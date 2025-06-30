#!/usr/bin/env python3
"""
Adaptive Crawler Strategy
Self-adapting strategy that learns from website patterns and adjusts extraction
approach dynamically based on real-time analysis and historical performance
"""

import asyncio
import time
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import hashlib

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType
from ai_core.core.hybrid_ai_service import HybridAIService
from services.vector_service import VectorService
from .adaptive_crawler_helpers import AdaptiveCrawlerHelpers

logger = logging.getLogger("adaptive_crawler")

@dataclass
class WebsitePattern:
    """Represents a learned website pattern"""
    pattern_id: str
    url_pattern: str
    content_features: Dict[str, Any]
    optimal_strategy: str
    success_rate: float
    avg_confidence: float
    last_updated: float
    sample_count: int

@dataclass
class AdaptationConfig:
    """Configuration for adaptive behavior"""
    learning_rate: float = 0.1
    pattern_threshold: int = 3  # Minimum samples before trusting pattern
    adaptation_threshold: float = 0.7  # Confidence threshold for adaptation
    max_patterns: int = 1000
    pattern_expiry_days: int = 30
    enable_real_time_learning: bool = True
    enable_content_analysis: bool = True

class AdaptiveCrawlerStrategy(BaseExtractionStrategy):
    """
    Self-adapting strategy that learns from website patterns and continuously
    improves extraction effectiveness through machine learning and pattern recognition
    """
    
    def __init__(self, base_strategies: List[BaseExtractionStrategy],
                 llm_service: HybridAIService = None,
                 vector_service: VectorService = None,
                 config: AdaptationConfig = None, **kwargs):
        super().__init__(strategy_type=StrategyType.HYBRID, **kwargs)
        self.base_strategies = base_strategies
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.config = config or AdaptationConfig()
        
        # Learning storage
        self.website_patterns: Dict[str, WebsitePattern] = {}
        self.content_embeddings: Dict[str, List[float]] = {}
        self.adaptation_history = []
        
        # Performance tracking
        self.strategy_performance = {}
        self.real_time_metrics = {
            "adaptations_made": 0,
            "patterns_learned": 0,
            "successful_predictions": 0,
            "total_predictions": 0
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, 
                      context: Dict[str, Any] = None) -> StrategyResult:
        """Execute adaptive extraction with real-time learning"""
        
        start_time = time.time()
        context = context or {}
        
        try:
            # Step 1: Analyze current website
            website_analysis = await AdaptiveCrawlerHelpers.analyze_website_structure(
                url, html_content, purpose, self.llm_service, self.vector_service, self.config
            )
            
            # Step 2: Find similar patterns from history
            similar_patterns = await self._find_similar_patterns(website_analysis, purpose)
            
            # Step 3: Select optimal strategy based on patterns
            selected_strategy, prediction_confidence = await self._select_adaptive_strategy(
                website_analysis, similar_patterns, purpose
            )
            
            # Step 4: Execute selected strategy
            extraction_result = await self._execute_adaptive_extraction(
                selected_strategy, url, html_content, purpose, context
            )
            
            # Step 5: Learn from execution result
            if self.config.enable_real_time_learning:
                await self._learn_from_execution(
                    website_analysis, selected_strategy, extraction_result, purpose
                )
            
            # Step 6: Update performance metrics
            self._update_real_time_metrics(extraction_result, prediction_confidence)
            
            # Enhanced result with adaptation metadata
            execution_time = time.time() - start_time
            extraction_result.execution_time = execution_time
            extraction_result.strategy_used = "AdaptiveCrawlerStrategy"
            
            if not hasattr(extraction_result, 'metadata'):
                extraction_result.metadata = {}
            
            extraction_result.metadata.update({
                "selected_strategy": selected_strategy.__class__.__name__ if selected_strategy else "None",
                "prediction_confidence": prediction_confidence,
                "website_analysis": website_analysis,
                "similar_patterns_found": len(similar_patterns),
                "adaptation_applied": prediction_confidence > self.config.adaptation_threshold,
                "learning_enabled": self.config.enable_real_time_learning
            })
            
            return extraction_result
            
        except Exception as e:
            logger.error(f"Adaptive extraction failed: {e}")
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="AdaptiveCrawlerStrategy",
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _find_similar_patterns(self, website_analysis: Dict[str, Any], 
                                   purpose: str) -> List[WebsitePattern]:
        """Find similar website patterns from learning history"""
        
        similar_patterns = []
        current_features = website_analysis.get("content_features", {})
        current_embedding = website_analysis.get("content_embedding")
        
        # Vector similarity search if available
        if current_embedding and self.vector_service:
            try:
                similar_embeddings = await AdaptiveCrawlerHelpers.find_similar_embeddings(
                    self.vector_service, current_embedding
                )
                for pattern_id, similarity in similar_embeddings:
                    if pattern_id in self.website_patterns:
                        pattern = self.website_patterns[pattern_id]
                        if similarity > 0.7:  # High similarity threshold
                            similar_patterns.append(pattern)
            except Exception as e:
                logger.warning(f"Vector similarity search failed: {e}")
        
        # Feature-based similarity search
        for pattern_id, pattern in self.website_patterns.items():
            if pattern.sample_count < self.config.pattern_threshold:
                continue  # Not enough samples
                
            # Check if pattern is still fresh
            age_days = (time.time() - pattern.last_updated) / (24 * 3600)
            if age_days > self.config.pattern_expiry_days:
                continue
            
            # Calculate feature similarity
            similarity = AdaptiveCrawlerHelpers.calculate_feature_similarity(
                current_features, pattern.content_features
            )
            
            if similarity > 0.6:  # Similarity threshold
                similar_patterns.append(pattern)
        
        # Sort by success rate and confidence
        similar_patterns.sort(
            key=lambda p: (p.success_rate, p.avg_confidence, p.sample_count),
            reverse=True
        )
        
        return similar_patterns[:5]  # Top 5 similar patterns
    
    async def _select_adaptive_strategy(self, website_analysis: Dict[str, Any],
                                       similar_patterns: List[WebsitePattern],
                                       purpose: str) -> Tuple[Optional[BaseExtractionStrategy], float]:
        """Select optimal strategy based on analysis and patterns"""
        
        # If we have good similar patterns, use their recommendation
        if similar_patterns:
            best_pattern = similar_patterns[0]
            if (best_pattern.success_rate > 0.7 and 
                best_pattern.sample_count >= self.config.pattern_threshold):
                
                # Find the recommended strategy
                for strategy in self.base_strategies:
                    if strategy.__class__.__name__ == best_pattern.optimal_strategy:
                        confidence = min(best_pattern.success_rate, best_pattern.avg_confidence)
                        self.real_time_metrics["total_predictions"] += 1
                        return strategy, confidence
        
        # Fallback to LLM-based strategy selection
        if self.llm_service:
            try:
                strategy_recommendation = await AdaptiveCrawlerHelpers.get_llm_strategy_recommendation(
                    self.llm_service, website_analysis, purpose, 
                    [s.__class__.__name__ for s in self.base_strategies]
                )
                
                recommended_strategy_name = strategy_recommendation.get("strategy", "")
                confidence = strategy_recommendation.get("confidence", 0.5)
                
                for strategy in self.base_strategies:
                    if recommended_strategy_name.lower() in strategy.__class__.__name__.lower():
                        self.real_time_metrics["total_predictions"] += 1
                        return strategy, confidence
                        
            except Exception as e:
                logger.warning(f"LLM strategy recommendation failed: {e}")
        
        # Final fallback: use strategy with highest confidence
        best_strategy = None
        best_confidence = 0.0
        
        for strategy in self.base_strategies:
            if hasattr(strategy, 'get_confidence_score'):
                confidence = strategy.get_confidence_score(
                    website_analysis.get("url", ""), "", purpose
                )
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_strategy = strategy
        
        if best_strategy:
            self.real_time_metrics["total_predictions"] += 1
            return best_strategy, best_confidence
        
        # Ultimate fallback
        return self.base_strategies[0] if self.base_strategies else None, 0.3
    
    async def _execute_adaptive_extraction(self, strategy: BaseExtractionStrategy,
                                          url: str, html_content: str, purpose: str,
                                          context: Dict[str, Any]) -> StrategyResult:
        """Execute extraction with selected strategy"""
        
        if not strategy:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="None",
                execution_time=0.0,
                error="No strategy selected"
            )
        
        try:
            # Add adaptive context
            adaptive_context = context.copy()
            adaptive_context["adaptive_extraction"] = True
            adaptive_context["adaptation_timestamp"] = time.time()
            
            result = await strategy.extract(url, html_content, purpose, adaptive_context)
            return result
            
        except Exception as e:
            logger.error(f"Strategy execution failed: {e}")
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used=strategy.__class__.__name__,
                execution_time=0.0,
                error=str(e)
            )
    
    async def _learn_from_execution(self, website_analysis: Dict[str, Any],
                                   strategy: BaseExtractionStrategy,
                                   result: StrategyResult, purpose: str):
        """Learn from execution result to improve future predictions"""
        
        if not strategy:
            return
        
        # Generate pattern ID
        domain = website_analysis.get("domain", "unknown")
        features_hash = AdaptiveCrawlerHelpers.hash_features(website_analysis.get("content_features", {}))
        pattern_id = f"{domain}_{purpose}_{features_hash}"
        
        # Update or create pattern
        if pattern_id in self.website_patterns:
            pattern = self.website_patterns[pattern_id]
            
            # Update with new data using learning rate
            lr = self.config.learning_rate
            new_success = 1.0 if result.success else 0.0
            new_confidence = result.confidence_score
            
            # Exponential moving average
            pattern.success_rate = (1 - lr) * pattern.success_rate + lr * new_success
            pattern.avg_confidence = (1 - lr) * pattern.avg_confidence + lr * new_confidence
            pattern.sample_count += 1
            pattern.last_updated = time.time()
            
            # Update optimal strategy if this one performed better
            current_score = pattern.success_rate * pattern.avg_confidence
            new_score = new_success * new_confidence
            
            if new_score > current_score or pattern.sample_count <= 2:
                pattern.optimal_strategy = strategy.__class__.__name__
        else:
            # Create new pattern
            pattern = WebsitePattern(
                pattern_id=pattern_id,
                url_pattern=domain,
                content_features=website_analysis.get("content_features", {}),
                optimal_strategy=strategy.__class__.__name__,
                success_rate=1.0 if result.success else 0.0,
                avg_confidence=result.confidence_score,
                last_updated=time.time(),
                sample_count=1
            )
            
            self.website_patterns[pattern_id] = pattern
            self.real_time_metrics["patterns_learned"] += 1
        
        # Store content embedding for similarity search
        content_embedding = website_analysis.get("content_embedding")
        if content_embedding and self.vector_service:
            try:
                await self.vector_service.store_embedding(
                    embedding=content_embedding,
                    metadata={
                        "pattern_id": pattern_id,
                        "strategy": strategy.__class__.__name__,
                        "success_rate": pattern.success_rate,
                        "purpose": purpose
                    },
                    collection_name="website_patterns"
                )
            except Exception as e:
                logger.warning(f"Failed to store embedding: {e}")
        
        # Record adaptation history
        self.adaptation_history.append({
            "timestamp": time.time(),
            "pattern_id": pattern_id,
            "strategy_used": strategy.__class__.__name__,
            "success": result.success,
            "confidence": result.confidence_score,
            "purpose": purpose,
            "learning_applied": True
        })
        
        # Limit history size
        if len(self.adaptation_history) > 1000:
            self.adaptation_history = self.adaptation_history[-1000:]
        
        # Clean up old patterns
        await self._cleanup_old_patterns()
    
    async def _cleanup_old_patterns(self):
        """Remove old or low-quality patterns"""
        
        current_time = time.time()
        patterns_to_remove = []
        
        for pattern_id, pattern in self.website_patterns.items():
            # Remove old patterns
            age_days = (current_time - pattern.last_updated) / (24 * 3600)
            if age_days > self.config.pattern_expiry_days:
                patterns_to_remove.append(pattern_id)
                continue
            
            # Remove low-quality patterns with enough samples
            if (pattern.sample_count >= 10 and 
                pattern.success_rate < 0.3 and 
                pattern.avg_confidence < 0.4):
                patterns_to_remove.append(pattern_id)
        
        # Remove identified patterns
        for pattern_id in patterns_to_remove:
            del self.website_patterns[pattern_id]
        
        # Limit total patterns
        if len(self.website_patterns) > self.config.max_patterns:
            # Remove oldest patterns
            sorted_patterns = sorted(
                self.website_patterns.items(),
                key=lambda x: x[1].last_updated
            )
            
            excess_count = len(self.website_patterns) - self.config.max_patterns
            for pattern_id, _ in sorted_patterns[:excess_count]:
                del self.website_patterns[pattern_id]
    
    def _update_real_time_metrics(self, result: StrategyResult, prediction_confidence: float):
        """Update real-time performance metrics"""
        
        if result.success and prediction_confidence > self.config.adaptation_threshold:
            self.real_time_metrics["successful_predictions"] += 1
        
        if prediction_confidence > self.config.adaptation_threshold:
            self.real_time_metrics["adaptations_made"] += 1
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive adaptation and learning statistics"""
        
        total_predictions = self.real_time_metrics["total_predictions"]
        prediction_accuracy = 0.0
        
        if total_predictions > 0:
            prediction_accuracy = (
                self.real_time_metrics["successful_predictions"] / total_predictions
            )
        
        # Pattern quality statistics
        pattern_stats = {
            "high_quality": 0,
            "medium_quality": 0,
            "low_quality": 0
        }
        
        for pattern in self.website_patterns.values():
            if pattern.sample_count >= 5:
                quality_score = pattern.success_rate * pattern.avg_confidence
                if quality_score > 0.7:
                    pattern_stats["high_quality"] += 1
                elif quality_score > 0.4:
                    pattern_stats["medium_quality"] += 1
                else:
                    pattern_stats["low_quality"] += 1
        
        return {
            "learning_statistics": {
                "total_patterns_learned": len(self.website_patterns),
                "patterns_with_sufficient_data": sum(
                    1 for p in self.website_patterns.values() 
                    if p.sample_count >= self.config.pattern_threshold
                ),
                "pattern_quality_distribution": pattern_stats,
                "avg_pattern_confidence": sum(
                    p.avg_confidence for p in self.website_patterns.values()
                ) / max(len(self.website_patterns), 1)
            },
            "adaptation_performance": {
                "total_predictions": total_predictions,
                "successful_predictions": self.real_time_metrics["successful_predictions"],
                "prediction_accuracy": prediction_accuracy,
                "adaptations_made": self.real_time_metrics["adaptations_made"],
                "patterns_learned_session": self.real_time_metrics["patterns_learned"]
            },
            "configuration": {
                "learning_rate": self.config.learning_rate,
                "pattern_threshold": self.config.pattern_threshold,
                "adaptation_threshold": self.config.adaptation_threshold,
                "real_time_learning": self.config.enable_real_time_learning
            }
        }
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Adaptive strategy confidence increases with learning"""
        
        # Base confidence starts at 0.6
        base_confidence = 0.6
        
        # Learning bonus based on patterns learned
        pattern_count = len(self.website_patterns)
        learning_bonus = min(pattern_count * 0.01, 0.2)  # Up to 0.2 bonus
        
        # Accuracy bonus based on prediction success
        total_predictions = self.real_time_metrics["total_predictions"]
        if total_predictions > 10:
            accuracy = self.real_time_metrics["successful_predictions"] / total_predictions
            accuracy_bonus = accuracy * 0.15
        else:
            accuracy_bonus = 0.0
        
        return min(base_confidence + learning_bonus + accuracy_bonus, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Supports purpose if any base strategy supports it"""
        return any(strategy.supports_purpose(purpose) for strategy in self.base_strategies)
