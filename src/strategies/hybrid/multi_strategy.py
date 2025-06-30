#!/usr/bin/env python3
"""
Multi-Strategy Coordinator
Advanced coordination system for running multiple extraction strategies in parallel,
with intelligent result merging and conflict resolution
"""

import asyncio
import time
import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import statistics

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType
from ai_core.core.hybrid_ai_service import HybridAIService

logger = logging.getLogger("multi_strategy")

class CoordinationMode(Enum):
    """Strategy coordination modes"""
    PARALLEL = "parallel"           # Run all strategies simultaneously
    COMPETITIVE = "competitive"     # Run strategies in competition, best wins
    COLLABORATIVE = "collaborative" # Strategies work together, merge results
    ADAPTIVE = "adaptive"          # Dynamically choose mode based on content

@dataclass
class StrategyWeight:
    """Weight configuration for strategy results"""
    strategy_name: str
    confidence_weight: float = 1.0
    data_quality_weight: float = 1.0
    speed_weight: float = 1.0
    reliability_weight: float = 1.0

@dataclass
class CoordinationConfig:
    """Configuration for multi-strategy coordination"""
    mode: CoordinationMode = CoordinationMode.COLLABORATIVE
    max_parallel_strategies: int = 5
    timeout_seconds: int = 30
    min_confidence_threshold: float = 0.3
    consensus_threshold: float = 0.7
    enable_conflict_resolution: bool = True
    strategy_weights: Dict[str, StrategyWeight] = None

class MultiStrategyCoordinator(BaseExtractionStrategy):
    """
    Advanced multi-strategy coordinator that can run multiple extraction
    strategies in various coordination modes with intelligent result merging
    """
    
    def __init__(self, strategies: List[BaseExtractionStrategy], 
                 llm_service: HybridAIService = None,
                 config: CoordinationConfig = None, **kwargs):
        super().__init__(strategy_type=StrategyType.HYBRID, **kwargs)
        self.strategies = strategies
        self.llm_service = llm_service
        self.config = config or CoordinationConfig()
        self.execution_history = []
        self.performance_stats = {}
        
        # Initialize strategy weights if not provided
        if not self.config.strategy_weights:
            self.config.strategy_weights = {
                strategy.__class__.__name__: StrategyWeight(strategy.__class__.__name__)
                for strategy in self.strategies
            }
    
    async def extract(self, url: str, html_content: str, purpose: str, 
                      context: Dict[str, Any] = None) -> StrategyResult:
        """Execute coordinated multi-strategy extraction"""
        
        start_time = time.time()
        context = context or {}
        
        try:
            # Select coordination mode
            coordination_mode = await self._select_coordination_mode(url, html_content, purpose)
            
            # Execute strategies based on mode
            strategy_results = await self._execute_coordinated_strategies(
                url, html_content, purpose, coordination_mode, context
            )
            
            # Merge and resolve conflicts
            final_data = await self._merge_and_resolve_results(
                strategy_results, purpose, coordination_mode
            )
            
            # Calculate overall confidence
            confidence = self._calculate_coordination_confidence(strategy_results, coordination_mode)
            
            # Record execution metrics
            execution_time = time.time() - start_time
            self._record_execution_metrics(url, purpose, strategy_results, execution_time)
            
            return StrategyResult(
                success=bool(final_data),
                extracted_data=final_data,
                confidence_score=confidence,
                strategy_used="MultiStrategyCoordinator",
                execution_time=execution_time,
                metadata={
                    "coordination_mode": coordination_mode.value,
                    "strategies_executed": len(strategy_results),
                    "successful_strategies": sum(1 for r in strategy_results.values() if r.success),
                    "consensus_achieved": confidence > self.config.consensus_threshold,
                    "strategy_results": {
                        name: {
                            "success": result.success,
                            "confidence": result.confidence_score,
                            "data_fields": len(result.extracted_data) if result.extracted_data else 0
                        }
                        for name, result in strategy_results.items()
                    }
                }
            )
            
        except Exception as e:
            logger.error(f"Multi-strategy coordination failed: {e}")
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="MultiStrategyCoordinator",
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _select_coordination_mode(self, url: str, html_content: str, 
                                       purpose: str) -> CoordinationMode:
        """Select optimal coordination mode based on content analysis"""
        
        if self.config.mode != CoordinationMode.ADAPTIVE:
            return self.config.mode
        
        # Use LLM to analyze content and recommend coordination mode
        if self.llm_service:
            try:
                analysis = await self.llm_service.analyze_website_content(url, html_content, purpose)
                
                complexity = analysis.get("website_type", "corporate")
                confidence = analysis.get("confidence", 0.5)
                
                # Decision logic for coordination mode
                if confidence > 0.8:
                    return CoordinationMode.COMPETITIVE  # High confidence, let best strategy win
                elif "ecommerce" in complexity or "directory" in complexity:
                    return CoordinationMode.COLLABORATIVE  # Complex sites benefit from collaboration
                else:
                    return CoordinationMode.PARALLEL  # Standard parallel execution
                    
            except Exception as e:
                logger.warning(f"Mode selection analysis failed: {e}")
        
        # Default fallback
        return CoordinationMode.COLLABORATIVE
    
    async def _execute_coordinated_strategies(self, url: str, html_content: str, 
                                            purpose: str, mode: CoordinationMode,
                                            context: Dict[str, Any]) -> Dict[str, StrategyResult]:
        """Execute strategies according to coordination mode"""
        
        if mode == CoordinationMode.PARALLEL:
            return await self._execute_parallel(url, html_content, purpose, context)
        elif mode == CoordinationMode.COMPETITIVE:
            return await self._execute_competitive(url, html_content, purpose, context)
        elif mode == CoordinationMode.COLLABORATIVE:
            return await self._execute_collaborative(url, html_content, purpose, context)
        else:
            # Fallback to parallel
            return await self._execute_parallel(url, html_content, purpose, context)
    
    async def _execute_parallel(self, url: str, html_content: str, purpose: str,
                               context: Dict[str, Any]) -> Dict[str, StrategyResult]:
        """Execute all strategies in parallel"""
        
        tasks = []
        strategy_names = []
        
        # Limit concurrent strategies
        strategies_to_run = self.strategies[:self.config.max_parallel_strategies]
        
        for strategy in strategies_to_run:
            task = asyncio.create_task(
                strategy.extract(url, html_content, purpose, context)
            )
            tasks.append(task)
            strategy_names.append(strategy.__class__.__name__)
        
        # Execute with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.timeout_seconds
            )
            
            strategy_results = {}
            for name, result in zip(strategy_names, results):
                if isinstance(result, Exception):
                    strategy_results[name] = StrategyResult(
                        success=False,
                        extracted_data={},
                        confidence_score=0.0,
                        strategy_used=name,
                        execution_time=0.0,
                        error=str(result)
                    )
                else:
                    strategy_results[name] = result
            
            return strategy_results
            
        except asyncio.TimeoutError:
            logger.warning(f"Parallel execution timeout after {self.config.timeout_seconds}s")
            # Cancel remaining tasks
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            return {}
    
    async def _execute_competitive(self, url: str, html_content: str, purpose: str,
                                  context: Dict[str, Any]) -> Dict[str, StrategyResult]:
        """Execute strategies competitively, return best result"""
        
        # First, run a quick confidence check
        confidence_tasks = []
        strategy_names = []
        
        for strategy in self.strategies:
            if hasattr(strategy, 'get_confidence_score'):
                confidence = strategy.get_confidence_score(url, html_content, purpose)
                confidence_tasks.append((strategy, confidence))
                strategy_names.append(strategy.__class__.__name__)
        
        # Sort by confidence and run top performers
        confidence_tasks.sort(key=lambda x: x[1], reverse=True)
        top_strategies = confidence_tasks[:3]  # Run top 3
        
        tasks = []
        names = []
        
        for strategy, _ in top_strategies:
            task = asyncio.create_task(
                strategy.extract(url, html_content, purpose, context)
            )
            tasks.append(task)
            names.append(strategy.__class__.__name__)
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.config.timeout_seconds
            )
            
            # Return the best result
            best_result = None
            best_name = None
            best_score = 0.0
            
            for name, result in zip(names, results):
                if isinstance(result, StrategyResult) and result.success:
                    score = self._calculate_strategy_score(result, name)
                    if score > best_score:
                        best_score = score
                        best_result = result
                        best_name = name
            
            if best_result:
                return {best_name: best_result}
            else:
                return {}
                
        except asyncio.TimeoutError:
            logger.warning("Competitive execution timeout")
            return {}
    
    async def _execute_collaborative(self, url: str, html_content: str, purpose: str,
                                    context: Dict[str, Any]) -> Dict[str, StrategyResult]:
        """Execute strategies collaboratively with shared context"""
        
        strategy_results = {}
        shared_context = context.copy()
        
        # Execute strategies in intelligent order
        ordered_strategies = self._order_strategies_for_collaboration(url, html_content, purpose)
        
        for strategy in ordered_strategies:
            try:
                # Add insights from previous strategies to context
                shared_context["previous_results"] = strategy_results
                
                result = await asyncio.wait_for(
                    strategy.extract(url, html_content, purpose, shared_context),
                    timeout=self.config.timeout_seconds / len(ordered_strategies)
                )
                
                strategy_name = strategy.__class__.__name__
                strategy_results[strategy_name] = result
                
                # Share successful extractions with subsequent strategies
                if result.success and result.extracted_data:
                    shared_context[f"{strategy_name}_data"] = result.extracted_data
                
            except asyncio.TimeoutError:
                logger.warning(f"Strategy {strategy.__class__.__name__} timed out in collaboration")
                continue
            except Exception as e:
                logger.warning(f"Strategy {strategy.__class__.__name__} failed: {e}")
                continue
        
        return strategy_results
    
    def _order_strategies_for_collaboration(self, url: str, html_content: str, 
                                           purpose: str) -> List[BaseExtractionStrategy]:
        """Order strategies for optimal collaboration"""
        
        # Order strategies by expected performance and complementarity
        strategy_scores = []
        
        for strategy in self.strategies:
            confidence = getattr(strategy, 'get_confidence_score', lambda *args: 0.5)(
                url, html_content, purpose
            )
            
            # Prefer faster strategies first for context building
            speed_bonus = 0.1 if 'CSS' in strategy.__class__.__name__ else 0.0
            
            score = confidence + speed_bonus
            strategy_scores.append((strategy, score))
        
        # Sort by score (highest first)
        strategy_scores.sort(key=lambda x: x[1], reverse=True)
        
        return [strategy for strategy, _ in strategy_scores]
    
    async def _merge_and_resolve_results(self, strategy_results: Dict[str, StrategyResult],
                                        purpose: str, mode: CoordinationMode) -> Dict[str, Any]:
        """Merge results from multiple strategies with conflict resolution"""
        
        if not strategy_results:
            return {}
        
        successful_results = {
            name: result for name, result in strategy_results.items() 
            if result.success and result.extracted_data
        }
        
        if not successful_results:
            return {}
        
        if len(successful_results) == 1:
            return next(iter(successful_results.values())).extracted_data
        
        # Merge multiple successful results
        merged_data = {}
        
        # Collect all unique fields
        all_fields = set()
        for result in successful_results.values():
            if result.extracted_data:
                all_fields.update(result.extracted_data.keys())
        
        # Resolve each field
        for field in all_fields:
            field_values = []
            field_weights = []
            
            for strategy_name, result in successful_results.items():
                if field in result.extracted_data:
                    value = result.extracted_data[field]
                    weight = self._calculate_field_weight(strategy_name, result, field)
                    field_values.append((value, weight, strategy_name))
                    field_weights.append(weight)
            
            # Resolve field value
            if self.config.enable_conflict_resolution and len(field_values) > 1:
                resolved_value = await self._resolve_field_conflict(
                    field, field_values, purpose
                )
            else:
                # Use highest weighted value
                field_values.sort(key=lambda x: x[1], reverse=True)
                resolved_value = field_values[0][0]
            
            if resolved_value:
                merged_data[field] = resolved_value
        
        return merged_data
    
    def _calculate_field_weight(self, strategy_name: str, result: StrategyResult, 
                               field: str) -> float:
        """Calculate weight for a specific field from a strategy result"""
        
        base_weight = 1.0
        
        # Strategy-specific weights
        if strategy_name in self.config.strategy_weights:
            weight_config = self.config.strategy_weights[strategy_name]
            base_weight = weight_config.confidence_weight
        
        # Confidence bonus
        confidence_bonus = result.confidence_score * 0.5
        
        # Data quality bonus (longer strings generally better)
        value = result.extracted_data.get(field, "")
        quality_bonus = min(len(str(value)) / 100, 0.3) if value else 0
        
        return base_weight + confidence_bonus + quality_bonus
    
    async def _resolve_field_conflict(self, field: str, field_values: List[Tuple[Any, float, str]],
                                     purpose: str) -> Any:
        """Resolve conflicts between different strategy values for the same field"""
        
        if not field_values:
            return None
        
        # If values are similar, use highest weighted
        unique_values = list(set(str(v[0]) for v in field_values))
        if len(unique_values) == 1:
            return field_values[0][0]  # All same value
        
        # Use LLM for intelligent conflict resolution
        if self.llm_service and len(field_values) > 1:
            try:
                conflict_prompt = f"""
Resolve conflict for field '{field}' in {purpose} extraction:

Values from different strategies:
{chr(10).join([f"- {v[2]}: {v[0]} (weight: {v[1]:.2f})" for v in field_values])}

Return the most accurate value, or combine them if appropriate.
Consider context and field type when deciding.
"""
                
                response = await self.llm_service.generate(conflict_prompt)
                if response.success:
                    return response.content.strip()
                    
            except Exception as e:
                logger.warning(f"LLM conflict resolution failed: {e}")
        
        # Fallback: use highest weighted value
        field_values.sort(key=lambda x: x[1], reverse=True)
        return field_values[0][0]
    
    def _calculate_coordination_confidence(self, strategy_results: Dict[str, StrategyResult],
                                          mode: CoordinationMode) -> float:
        """Calculate overall confidence for coordinated extraction"""
        
        if not strategy_results:
            return 0.0
        
        successful_results = [r for r in strategy_results.values() if r.success]
        if not successful_results:
            return 0.0
        
        # Base confidence from successful strategies
        confidences = [r.confidence_score for r in successful_results]
        
        if mode == CoordinationMode.COMPETITIVE:
            # Use highest confidence
            base_confidence = max(confidences)
        elif mode == CoordinationMode.COLLABORATIVE:
            # Use weighted average
            weights = [self._calculate_strategy_score(r, "") for r in successful_results]
            if sum(weights) > 0:
                base_confidence = sum(c * w for c, w in zip(confidences, weights)) / sum(weights)
            else:
                base_confidence = statistics.mean(confidences)
        else:  # PARALLEL
            # Use average confidence
            base_confidence = statistics.mean(confidences)
        
        # Consensus bonus
        if len(successful_results) > 1:
            consensus_bonus = min(len(successful_results) * 0.05, 0.2)
            base_confidence += consensus_bonus
        
        return min(base_confidence, 1.0)
    
    def _calculate_strategy_score(self, result: StrategyResult, strategy_name: str) -> float:
        """Calculate overall score for a strategy result"""
        
        if not result.success:
            return 0.0
        
        # Base score from confidence
        score = result.confidence_score
        
        # Data quality bonus
        data_fields = len(result.extracted_data) if result.extracted_data else 0
        quality_bonus = min(data_fields * 0.1, 0.3)
        score += quality_bonus
        
        # Speed bonus (faster is better)
        if result.execution_time > 0:
            speed_bonus = max(0, 0.2 - (result.execution_time / 10))
            score += speed_bonus
        
        return min(score, 1.0)
    
    def _record_execution_metrics(self, url: str, purpose: str, 
                                 strategy_results: Dict[str, StrategyResult],
                                 execution_time: float):
        """Record metrics for performance analysis"""
        
        execution_record = {
            "timestamp": time.time(),
            "url": url,
            "purpose": purpose,
            "total_execution_time": execution_time,
            "strategies_executed": len(strategy_results),
            "successful_strategies": sum(1 for r in strategy_results.values() if r.success),
            "strategy_performances": {
                name: {
                    "success": result.success,
                    "confidence": result.confidence_score,
                    "execution_time": result.execution_time,
                    "data_fields": len(result.extracted_data) if result.extracted_data else 0
                }
                for name, result in strategy_results.items()
            }
        }
        
        self.execution_history.append(execution_record)
        
        # Keep only recent history (last 100 executions)
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        
        if not self.execution_history:
            return {"message": "No execution history available"}
        
        total_executions = len(self.execution_history)
        successful_executions = sum(
            1 for record in self.execution_history 
            if record["successful_strategies"] > 0
        )
        
        # Calculate average performance per strategy
        strategy_stats = {}
        for record in self.execution_history:
            for strategy_name, perf in record["strategy_performances"].items():
                if strategy_name not in strategy_stats:
                    strategy_stats[strategy_name] = {
                        "executions": 0,
                        "successes": 0,
                        "total_confidence": 0.0,
                        "total_time": 0.0
                    }
                
                stats = strategy_stats[strategy_name]
                stats["executions"] += 1
                if perf["success"]:
                    stats["successes"] += 1
                stats["total_confidence"] += perf["confidence"]
                stats["total_time"] += perf["execution_time"]
        
        # Calculate averages
        for strategy_name, stats in strategy_stats.items():
            if stats["executions"] > 0:
                stats["success_rate"] = stats["successes"] / stats["executions"]
                stats["avg_confidence"] = stats["total_confidence"] / stats["executions"]
                stats["avg_execution_time"] = stats["total_time"] / stats["executions"]
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions,
            "avg_execution_time": statistics.mean([r["total_execution_time"] for r in self.execution_history]),
            "strategy_statistics": strategy_stats,
            "coordination_modes_used": len(set([
                r.get("coordination_mode", "unknown") for r in self.execution_history
            ]))
        }
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Multi-strategy coordinator has high confidence due to redundancy"""
        return 0.85  # High confidence due to multiple strategy redundancy
    
    def supports_purpose(self, purpose: str) -> bool:
        """Supports purpose if any constituent strategy supports it"""
        return any(strategy.supports_purpose(purpose) for strategy in self.strategies)
    
    def add_strategy(self, strategy: BaseExtractionStrategy, weight: StrategyWeight = None):
        """Add a new strategy to the coordinator"""
        self.strategies.append(strategy)
        
        if weight:
            self.config.strategy_weights[strategy.__class__.__name__] = weight
        else:
            self.config.strategy_weights[strategy.__class__.__name__] = StrategyWeight(
                strategy.__class__.__name__
            )
    
    def remove_strategy(self, strategy_class_name: str) -> bool:
        """Remove a strategy from the coordinator"""
        for i, strategy in enumerate(self.strategies):
            if strategy.__class__.__name__ == strategy_class_name:
                del self.strategies[i]
                if strategy_class_name in self.config.strategy_weights:
                    del self.config.strategy_weights[strategy_class_name]
                return True
        return False
    
    def update_strategy_weight(self, strategy_name: str, weight: StrategyWeight):
        """Update weight configuration for a strategy"""
        self.config.strategy_weights[strategy_name] = weight
    
    def clear_execution_history(self):
        """Clear execution history"""
        self.execution_history.clear()
