#!/usr/bin/env python3
"""
Adaptive Learning Strategy
Learning hybrid strategy that adapts based on historical performance
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType
from .smart_hybrid import SmartHybridStrategy

class AdaptiveHybridStrategy(SmartHybridStrategy):
    """
    Learning hybrid strategy that adapts based on historical performance
    
    Examples:
    - Learn which strategies work best for different website types
    - Optimize strategy selection based on success rates
    - Improve over time with usage
    """
    
    def __init__(self, ollama_client, chromadb_manager=None, **kwargs):
        super().__init__(ollama_client, **kwargs)
        self.chromadb_manager = chromadb_manager
        self.performance_history = {}
        self.learning_enabled = chromadb_manager is not None
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Get historical performance for this URL pattern
            url_pattern = self._get_url_pattern(url)
            historical_performance = await self._get_historical_performance(url_pattern, purpose)
            
            # Adapt strategy plan based on historical data
            strategy_plan = await self._analyze_and_plan_extraction(url, html_content, purpose)
            if historical_performance:
                strategy_plan = self._adapt_strategy_plan(strategy_plan, historical_performance)
            
            # Execute with adapted plan
            extraction_results = await self._execute_strategy_plan(url, html_content, purpose, strategy_plan, context)
            final_data = self._merge_strategy_results(extraction_results, purpose)
            
            # Calculate confidence
            confidence = self._calculate_smart_hybrid_confidence(extraction_results, strategy_plan)
            
            # Create final result
            final_result = StrategyResult(
                success=bool(final_data),
                extracted_data=final_data,
                confidence_score=confidence,
                strategy_used="AdaptiveHybridStrategy",
                execution_time=time.time() - start_time,
                metadata={
                    "adapted_plan": strategy_plan,
                    "historical_data_used": bool(historical_performance),
                    "url_pattern": url_pattern,
                    "learning_enabled": self.learning_enabled
                }
            )
            
            # Learn from this execution
            if self.learning_enabled:
                await self._learn_from_execution(url, purpose, final_result, strategy_plan)
            
            return final_result
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="AdaptiveHybridStrategy",
                execution_time=time.time() - start_time,
                metadata={"learning_enabled": self.learning_enabled},
                error=str(e)
            )
    
    def _get_url_pattern(self, url: str) -> str:
        """Extract pattern from URL for learning purposes"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Create pattern based on domain and path structure
            path_parts = [part for part in parsed.path.split('/') if part]
            
            if not path_parts:
                return f"{domain}_homepage"
            elif len(path_parts) == 1:
                return f"{domain}_{path_parts[0]}"
            else:
                return f"{domain}_deep_page"
        except:
            return "unknown_pattern"
    
    async def _get_historical_performance(self, url_pattern: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get historical performance data for this pattern"""
        
        if not self.chromadb_manager:
            return self._get_local_historical_performance(url_pattern, purpose)
        
        try:
            # Query for similar URL patterns and purposes
            similar_results = await self.chromadb_manager.query_similar_strategies(
                query_text=f"{url_pattern} {purpose}",
                website_type="unknown",
                purpose=purpose,
                limit=5
            )
            
            if similar_results:
                # Aggregate performance data
                return self._aggregate_performance_data(similar_results)
            
        except Exception as e:
            self.logger.warning(f"Failed to get historical performance from ChromaDB: {e}")
            # Fallback to local performance history
            return self._get_local_historical_performance(url_pattern, purpose)
        
        return None
    
    def _get_local_historical_performance(self, url_pattern: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get historical performance from local storage"""
        
        key = f"{url_pattern}_{purpose}"
        if key in self.performance_history:
            history = self.performance_history[key]
            
            if history["total_attempts"] >= 3:  # Minimum sample size
                return {
                    "css_success_rate": history["css_successes"] / history["total_attempts"],
                    "llm_success_rate": history["llm_successes"] / history["total_attempts"],
                    "best_strategy": self._determine_best_strategy(history),
                    "avg_confidence": history["total_confidence"] / history["total_attempts"],
                    "sample_size": history["total_attempts"]
                }
        
        return None
    
    def _determine_best_strategy(self, history: Dict[str, Any]) -> str:
        """Determine best strategy from local history"""
        css_rate = history["css_successes"] / history["total_attempts"] if history["total_attempts"] > 0 else 0
        llm_rate = history["llm_successes"] / history["total_attempts"] if history["total_attempts"] > 0 else 0
        
        if css_rate > llm_rate + 0.1:
            return "css"
        elif llm_rate > css_rate + 0.1:
            return "llm"
        else:
            return "hybrid"
    
    def _aggregate_performance_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate historical performance data from ChromaDB"""
        
        aggregated = {
            "css_success_rate": 0.0,
            "llm_success_rate": 0.0,
            "best_strategy": "hybrid",
            "avg_confidence": 0.0,
            "sample_size": len(results)
        }
        
        css_successes = 0
        llm_successes = 0
        total_confidence = 0.0
        
        for result in results:
            strategy = result.get("strategy", "")
            success_rate = result.get("success_rate", 0)
            
            if "css" in strategy.lower():
                css_successes += success_rate
            elif "llm" in strategy.lower():
                llm_successes += success_rate
            
            total_confidence += success_rate
        
        if results:
            aggregated["css_success_rate"] = css_successes / len(results)
            aggregated["llm_success_rate"] = llm_successes / len(results)
            aggregated["avg_confidence"] = total_confidence / len(results)
            
            # Determine best strategy
            if aggregated["css_success_rate"] > aggregated["llm_success_rate"] + 0.1:
                aggregated["best_strategy"] = "css"
            elif aggregated["llm_success_rate"] > aggregated["css_success_rate"] + 0.1:
                aggregated["best_strategy"] = "llm"
        
        return aggregated
    
    def _adapt_strategy_plan(self, original_plan: Dict[str, Any], historical_data: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt strategy plan based on historical performance"""
        
        adapted_plan = original_plan.copy()
        
        # Adjust strategy recommendation based on historical success
        best_historical = historical_data.get("best_strategy", "hybrid")
        sample_size = historical_data.get("sample_size", 0)
        
        if best_historical != "hybrid" and sample_size >= 3:
            # Override primary strategy if we have strong historical evidence
            adapted_plan["recommended_strategies"]["primary"] = best_historical
            adapted_plan["reasoning"] += f" (Adapted: historical {best_historical} success rate)"
            
            # Adjust confidence based on historical data
            historical_confidence = historical_data.get("avg_confidence", 0.5)
            if historical_confidence > 0.7:
                adapted_plan["confidence"] = min(adapted_plan["confidence"] + 0.15, 1.0)
            elif historical_confidence > 0.5:
                adapted_plan["confidence"] = min(adapted_plan["confidence"] + 0.05, 1.0)
        
        return adapted_plan
    
    async def _learn_from_execution(self, url: str, purpose: str, result: StrategyResult, strategy_plan: Dict[str, Any]):
        """Learn from execution results for future improvement"""
        
        url_pattern = self._get_url_pattern(url)
        
        # Store in local performance history
        self._store_local_performance(url_pattern, purpose, result, strategy_plan)
        
        # Store in ChromaDB if available
        if self.chromadb_manager:
            await self._store_chromadb_performance(url, purpose, result, strategy_plan)
    
    def _store_local_performance(self, url_pattern: str, purpose: str, result: StrategyResult, strategy_plan: Dict[str, Any]):
        """Store performance data in local history"""
        
        key = f"{url_pattern}_{purpose}"
        
        if key not in self.performance_history:
            self.performance_history[key] = {
                "total_attempts": 0,
                "css_successes": 0,
                "llm_successes": 0,
                "total_confidence": 0.0
            }
        
        history = self.performance_history[key]
        history["total_attempts"] += 1
        history["total_confidence"] += result.confidence_score
        
        # Track strategy-specific successes
        primary_strategy = strategy_plan.get("recommended_strategies", {}).get("primary", "hybrid")
        
        if result.success:
            if primary_strategy == "css" or "css" in result.metadata.get("strategies_used", []):
                history["css_successes"] += 1
            if primary_strategy == "llm" or "llm" in result.metadata.get("strategies_used", []):
                history["llm_successes"] += 1
    
    async def _store_chromadb_performance(self, url: str, purpose: str, result: StrategyResult, strategy_plan: Dict[str, Any]):
        """Store performance data in ChromaDB for global learning"""
        
        learning_data = {
            "url_pattern": self._get_url_pattern(url),
            "purpose": purpose,
            "strategy_plan": strategy_plan,
            "success": result.success,
            "confidence": result.confidence_score,
            "data_quality": len(result.extracted_data) if result.extracted_data else 0,
            "timestamp": time.time(),
            "strategy": "AdaptiveHybridStrategy"
        }
        
        try:
            await self.chromadb_manager.store_strategy_learning(learning_data)
        except Exception as e:
            self.logger.warning(f"Failed to store learning data in ChromaDB: {e}")
    
    def get_learning_statistics(self) -> Dict[str, Any]:
        """Get learning and adaptation statistics"""
        
        total_patterns = len(self.performance_history)
        total_attempts = sum(h["total_attempts"] for h in self.performance_history.values())
        
        if total_attempts == 0:
            return {
                "total_patterns_learned": total_patterns,
                "total_attempts": 0,
                "learning_enabled": self.learning_enabled,
                "patterns": []
            }
        
        # Calculate per-pattern statistics
        pattern_stats = []
        for pattern, history in self.performance_history.items():
            if history["total_attempts"] > 0:
                css_rate = history["css_successes"] / history["total_attempts"]
                llm_rate = history["llm_successes"] / history["total_attempts"]
                avg_confidence = history["total_confidence"] / history["total_attempts"]
                
                pattern_stats.append({
                    "pattern": pattern,
                    "attempts": history["total_attempts"],
                    "css_success_rate": css_rate,
                    "llm_success_rate": llm_rate,
                    "avg_confidence": avg_confidence,
                    "best_strategy": self._determine_best_strategy(history)
                })
        
        # Sort by number of attempts (most learned patterns first)
        pattern_stats.sort(key=lambda x: x["attempts"], reverse=True)
        
        return {
            "total_patterns_learned": total_patterns,
            "total_attempts": total_attempts,
            "learning_enabled": self.learning_enabled,
            "chromadb_available": self.chromadb_manager is not None,
            "patterns": pattern_stats[:10]  # Top 10 most learned patterns
        }
    
    def reset_learning_data(self):
        """Reset all learning data"""
        self.performance_history.clear()
    
    def export_learning_data(self) -> Dict[str, Any]:
        """Export learning data for backup or analysis"""
        return {
            "performance_history": self.performance_history.copy(),
            "learning_enabled": self.learning_enabled,
            "export_timestamp": time.time()
        }
    
    def import_learning_data(self, learning_data: Dict[str, Any]):
        """Import learning data from backup"""
        if "performance_history" in learning_data:
            self.performance_history.update(learning_data["performance_history"])
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Adaptive strategy has highest confidence due to learning"""
        base_confidence = super().get_confidence_score(url, html_content, purpose)
        
        # Learning bonus based on historical data
        url_pattern = self._get_url_pattern(url)
        key = f"{url_pattern}_{purpose}"
        
        if key in self.performance_history:
            history = self.performance_history[key]
            if history["total_attempts"] >= 3:
                # Boost confidence based on historical success
                avg_confidence = history["total_confidence"] / history["total_attempts"]
                if avg_confidence > 0.7:
                    base_confidence = min(base_confidence + 0.15, 1.0)
                elif avg_confidence > 0.5:
                    base_confidence = min(base_confidence + 0.1, 1.0)
        
        return min(base_confidence + 0.05, 1.0)  # Base learning bonus
