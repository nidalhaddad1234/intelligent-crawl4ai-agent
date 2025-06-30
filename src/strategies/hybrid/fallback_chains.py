#!/usr/bin/env python3
"""
Fallback Chains Strategy
Multi-strategy fallback system that tries multiple approaches until success
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

class FallbackStrategy(BaseExtractionStrategy):
    """
    Multi-strategy fallback system that tries multiple approaches until success
    
    Examples:
    - Try CSS first, then LLM if CSS fails
    - Handle edge cases and difficult websites
    - Ensure maximum success rate across different site types
    """
    
    def __init__(self, strategies: List[BaseExtractionStrategy], **kwargs):
        super().__init__(strategy_type=StrategyType.HYBRID, **kwargs)
        self.strategies = strategies
        self.success_tracking = {}
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        attempts = []
        final_result = None
        
        # Try each strategy in order until success
        for i, strategy in enumerate(self.strategies):
            try:
                result = await strategy.extract(url, html_content, purpose, context)
                attempts.append({
                    "strategy": strategy.__class__.__name__,
                    "success": result.success,
                    "confidence": result.confidence_score,
                    "data_fields": len(result.extracted_data) if result.extracted_data else 0,
                    "execution_time": result.execution_time
                })
                
                # Use this result if successful or if it's the last strategy
                if result.success or i == len(self.strategies) - 1:
                    final_result = result
                    final_result.fallback_used = i > 0  # Mark if fallback was used
                    break
                    
            except Exception as e:
                attempts.append({
                    "strategy": strategy.__class__.__name__,
                    "success": False,
                    "error": str(e),
                    "execution_time": 0
                })
                continue
        
        # Update metadata
        if final_result:
            final_result.execution_time = time.time() - start_time
            final_result.strategy_used = "FallbackStrategy"
            if not hasattr(final_result, 'metadata'):
                final_result.metadata = {}
            final_result.metadata.update({
                "attempts": attempts,
                "successful_strategy": attempts[-1]["strategy"] if attempts else "none",
                "fallback_depth": len(attempts) - 1,
                "total_attempts": len(attempts)
            })
        else:
            final_result = StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="FallbackStrategy",
                execution_time=time.time() - start_time,
                metadata={
                    "attempts": attempts, 
                    "all_strategies_failed": True,
                    "total_attempts": len(attempts)
                },
                error="All fallback strategies failed"
            )
        
        # Track success rates for optimization
        self._track_strategy_performance(attempts, url, purpose)
        
        return final_result
    
    def _track_strategy_performance(self, attempts: List[Dict[str, Any]], url: str, purpose: str):
        """Track strategy performance for future optimization"""
        
        # Create tracking key
        domain = self._extract_domain(url)
        tracking_key = f"{domain}_{purpose}"
        
        if tracking_key not in self.success_tracking:
            self.success_tracking[tracking_key] = {
                "attempts": 0,
                "strategy_performance": {}
            }
        
        # Update tracking data
        self.success_tracking[tracking_key]["attempts"] += 1
        
        for attempt in attempts:
            strategy_name = attempt["strategy"]
            success = attempt["success"]
            
            if strategy_name not in self.success_tracking[tracking_key]["strategy_performance"]:
                self.success_tracking[tracking_key]["strategy_performance"][strategy_name] = {
                    "successes": 0,
                    "failures": 0,
                    "total_attempts": 0
                }
            
            perf = self.success_tracking[tracking_key]["strategy_performance"][strategy_name]
            perf["total_attempts"] += 1
            
            if success:
                perf["successes"] += 1
            else:
                perf["failures"] += 1
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for tracking"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return "unknown"
    
    def get_strategy_performance(self, domain: str = None, purpose: str = None) -> Dict[str, Any]:
        """Get performance statistics for strategies"""
        
        if domain and purpose:
            tracking_key = f"{domain}_{purpose}"
            return self.success_tracking.get(tracking_key, {})
        
        # Return overall performance
        overall_performance = {}
        total_attempts = 0
        
        for tracking_key, data in self.success_tracking.items():
            total_attempts += data["attempts"]
            
            for strategy_name, perf in data["strategy_performance"].items():
                if strategy_name not in overall_performance:
                    overall_performance[strategy_name] = {
                        "successes": 0,
                        "failures": 0,
                        "total_attempts": 0
                    }
                
                overall_performance[strategy_name]["successes"] += perf["successes"]
                overall_performance[strategy_name]["failures"] += perf["failures"]
                overall_performance[strategy_name]["total_attempts"] += perf["total_attempts"]
        
        # Calculate success rates
        for strategy_name, perf in overall_performance.items():
            if perf["total_attempts"] > 0:
                perf["success_rate"] = perf["successes"] / perf["total_attempts"]
            else:
                perf["success_rate"] = 0.0
        
        return {
            "total_attempts": total_attempts,
            "strategy_performance": overall_performance
        }
    
    def optimize_strategy_order(self, domain: str = None, purpose: str = None) -> List[BaseExtractionStrategy]:
        """Optimize strategy order based on performance data"""
        
        performance_data = self.get_strategy_performance(domain, purpose)
        strategy_performance = performance_data.get("strategy_performance", {})
        
        if not strategy_performance:
            return self.strategies  # No data, return original order
        
        # Create mapping of strategy names to strategy objects
        strategy_map = {strategy.__class__.__name__: strategy for strategy in self.strategies}
        
        # Sort strategies by success rate (descending)
        sorted_strategies = sorted(
            strategy_performance.items(),
            key=lambda x: x[1]["success_rate"],
            reverse=True
        )
        
        # Rebuild strategy list in optimized order
        optimized_strategies = []
        used_strategies = set()
        
        # Add strategies with performance data first
        for strategy_name, perf in sorted_strategies:
            if strategy_name in strategy_map and strategy_name not in used_strategies:
                optimized_strategies.append(strategy_map[strategy_name])
                used_strategies.add(strategy_name)
        
        # Add remaining strategies that don't have performance data
        for strategy in self.strategies:
            strategy_name = strategy.__class__.__name__
            if strategy_name not in used_strategies:
                optimized_strategies.append(strategy)
        
        return optimized_strategies
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Fallback strategy confidence is based on constituent strategies"""
        if not self.strategies:
            return 0.0
        
        # Check if we have performance data for this domain/purpose
        domain = self._extract_domain(url)
        performance_data = self.get_strategy_performance(domain, purpose)
        
        if performance_data and "strategy_performance" in performance_data:
            # Use historical success rates
            strategy_performances = performance_data["strategy_performance"]
            success_rates = [
                perf.get("success_rate", 0.5) 
                for perf in strategy_performances.values()
            ]
            if success_rates:
                # Return the highest success rate among strategies
                return max(success_rates)
        
        # Fallback to average confidence of all strategies
        confidences = [
            strategy.get_confidence_score(url, html_content, purpose) 
            for strategy in self.strategies
        ]
        return max(confidences) if confidences else 0.0
    
    def supports_purpose(self, purpose: str) -> bool:
        """Supports purpose if any constituent strategy supports it"""
        return any(strategy.supports_purpose(purpose) for strategy in self.strategies)
    
    def add_strategy(self, strategy: BaseExtractionStrategy, position: int = None):
        """Add a new strategy to the fallback chain"""
        if position is None:
            self.strategies.append(strategy)
        else:
            self.strategies.insert(position, strategy)
    
    def remove_strategy(self, strategy_class_name: str) -> bool:
        """Remove a strategy from the fallback chain"""
        for i, strategy in enumerate(self.strategies):
            if strategy.__class__.__name__ == strategy_class_name:
                del self.strategies[i]
                return True
        return False
    
    def clear_performance_tracking(self):
        """Clear all performance tracking data"""
        self.success_tracking.clear()
    
    def get_strategy_chain_info(self) -> Dict[str, Any]:
        """Get information about the current strategy chain"""
        return {
            "total_strategies": len(self.strategies),
            "strategy_names": [strategy.__class__.__name__ for strategy in self.strategies],
            "performance_tracking_entries": len(self.success_tracking)
        }
