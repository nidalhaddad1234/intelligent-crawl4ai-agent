#!/usr/bin/env python3
"""
Adaptive Learning LLM Strategy
Self-adapting LLM strategy that improves extraction prompts based on results
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from collections import Counter

from .context_aware import ContextAwareLLMStrategy
from core.base_strategy import StrategyResult

class AdaptiveLLMStrategy(ContextAwareLLMStrategy):
    """
    Self-adapting LLM strategy that improves extraction prompts based on results
    
    Examples:
    - Automatically adjust extraction prompts based on success rates
    - Learn optimal prompt patterns for different website types
    - Adapt to new content patterns dynamically
    """
    
    def __init__(self, ollama_client, chromadb_manager=None, **kwargs):
        super().__init__(ollama_client, chromadb_manager, **kwargs)
        self.prompt_variations = {}
        self.success_metrics = {}
        self.adaptation_enabled = True
        self.min_attempts_for_adaptation = 3
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        # Get adaptive prompt based on historical performance
        adaptive_prompt_elements = await self._get_adaptive_prompt_elements(url, purpose)
        
        # Enhanced context with adaptive elements
        enhanced_context = context or {}
        enhanced_context.update(adaptive_prompt_elements)
        
        result = await super().extract(url, html_content, purpose, enhanced_context)
        
        # Track performance for adaptation
        await self._track_performance(url, purpose, result, adaptive_prompt_elements)
        
        # Update metadata with adaptation information
        if hasattr(result, 'metadata'):
            result.metadata.update({
                "adaptive_elements_used": bool(adaptive_prompt_elements),
                "adaptation_enabled": self.adaptation_enabled,
                "prompt_adapted": self._has_adapted_prompt(url, purpose)
            })
        
        return result
    
    async def _get_adaptive_prompt_elements(self, url: str, purpose: str) -> Dict[str, Any]:
        """Get adaptive prompt elements based on historical performance"""
        
        # Check if we have learned prompt patterns for this purpose
        prompt_key = f"{purpose}_{self._get_url_pattern(url)}"
        
        if prompt_key in self.prompt_variations:
            learned_elements = self.prompt_variations[prompt_key]
            
            # Validate that these elements have good performance
            if self._validate_prompt_elements(prompt_key, learned_elements):
                return learned_elements
        
        # Default adaptive elements
        return {
            "extraction_hints": self._get_purpose_specific_hints(purpose),
            "quality_indicators": self._get_quality_indicators(purpose),
            "adaptation_level": "default"
        }
    
    def _validate_prompt_elements(self, prompt_key: str, elements: Dict[str, Any]) -> bool:
        """Validate that prompt elements have good historical performance"""
        
        if prompt_key not in self.success_metrics:
            return False
        
        metrics = self.success_metrics[prompt_key]
        
        # Require minimum attempts and good success rate
        if (metrics.get("attempts", 0) >= self.min_attempts_for_adaptation and
            metrics.get("success_rate", 0) > 0.6):
            return True
        
        return False
    
    def _get_purpose_specific_hints(self, purpose: str) -> List[str]:
        """Get specific hints for different extraction purposes"""
        
        hints_map = {
            "company_info": [
                "Look for 'About Us' or 'Company' sections",
                "Check footer for contact information", 
                "Look for leadership team or executive information",
                "Find mission/vision statements",
                "Check for company history or founding information"
            ],
            "contact_discovery": [
                "Scan entire page for email addresses",
                "Look for 'Contact', 'Support', or 'Help' sections",
                "Check social media links and profiles",
                "Find physical addresses and phone numbers",
                "Look for contact forms and support channels"
            ],
            "product_data": [
                "Look for pricing information and cost details",
                "Find product specifications or technical features",
                "Check for customer reviews or ratings",
                "Look for product images and detailed descriptions",
                "Find availability and purchasing information"
            ],
            "news_content": [
                "Identify headline and subheadings clearly",
                "Find author information and publication date",
                "Extract main article content accurately",
                "Look for quotes and key statistics",
                "Identify sources and references"
            ],
            "profile_info": [
                "Look for professional titles and current positions",
                "Find work experience and career history",
                "Check for educational background",
                "Look for skills and expertise areas",
                "Find contact information and social profiles"
            ]
        }
        
        return hints_map.get(purpose, ["Extract all relevant information carefully and thoroughly"])
    
    def _get_quality_indicators(self, purpose: str) -> List[str]:
        """Get quality indicators for different purposes"""
        
        indicators_map = {
            "company_info": ["company_name", "description", "contact_email", "industry"],
            "contact_discovery": ["emails", "phones", "addresses", "social_media"],
            "product_data": ["name", "price", "description", "features"],
            "news_content": ["headline", "content", "author", "publish_date"],
            "profile_info": ["name", "title", "company", "experience"]
        }
        
        return indicators_map.get(purpose, ["title", "main_content"])
    
    def _get_url_pattern(self, url: str) -> str:
        """Extract URL pattern for categorization"""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Pattern recognition based on URL structure
            if any(word in path for word in ['about', 'company', 'who-we-are']):
                return "about_page"
            elif any(word in path for word in ['contact', 'support', 'help']):
                return "contact_page"
            elif any(word in path for word in ['product', 'service', 'solution']):
                return "product_page"
            elif any(word in path for word in ['news', 'blog', 'article', 'press']):
                return "content_page"
            elif any(word in path for word in ['profile', 'team', 'people', 'staff']):
                return "profile_page"
            elif path == '/' or not path:
                return "homepage"
            else:
                return "general_page"
        except:
            return "unknown_pattern"
    
    async def _track_performance(self, url: str, purpose: str, result: StrategyResult, prompt_elements: Dict[str, Any]):
        """Track performance for continuous adaptation"""
        
        prompt_key = f"{purpose}_{self._get_url_pattern(url)}"
        
        if prompt_key not in self.success_metrics:
            self.success_metrics[prompt_key] = {
                "attempts": 0,
                "successes": 0,
                "total_confidence": 0.0,
                "best_elements": prompt_elements,
                "recent_results": []
            }
        
        metrics = self.success_metrics[prompt_key]
        metrics["attempts"] += 1
        metrics["total_confidence"] += result.confidence_score
        
        # Track recent results (keep last 10)
        result_data = {
            "success": result.success,
            "confidence": result.confidence_score,
            "data_quality": len(result.extracted_data) if result.extracted_data else 0,
            "elements_used": prompt_elements,
            "timestamp": time.time()
        }
        
        metrics["recent_results"].append(result_data)
        if len(metrics["recent_results"]) > 10:
            metrics["recent_results"] = metrics["recent_results"][-10:]
        
        if result.success:
            metrics["successes"] += 1
            
            # Calculate current success rate
            success_rate = metrics["successes"] / metrics["attempts"]
            
            # Update best elements if this approach is performing well
            if (result.confidence_score > 0.7 and 
                success_rate > 0.6 and 
                metrics["attempts"] >= self.min_attempts_for_adaptation):
                
                # Adapt prompt elements based on successful patterns
                await self._adapt_prompt_elements(prompt_key, result, prompt_elements)
    
    async def _adapt_prompt_elements(self, prompt_key: str, result: StrategyResult, current_elements: Dict[str, Any]):
        """Adapt prompt elements based on successful results"""
        
        if not self.adaptation_enabled:
            return
        
        metrics = self.success_metrics[prompt_key]
        
        # Analyze recent successful results for patterns
        successful_results = [
            r for r in metrics["recent_results"]
            if r["success"] and r["confidence"] > 0.6
        ]
        
        if len(successful_results) >= 2:
            # Extract common elements from successful attempts
            adapted_elements = self._extract_successful_patterns(successful_results, current_elements)
            
            # Update prompt variations if we found good patterns
            if adapted_elements and adapted_elements != current_elements:
                self.prompt_variations[prompt_key] = adapted_elements
                self.logger.info(f"Adapted prompt elements for {prompt_key}")
    
    def _extract_successful_patterns(self, successful_results: List[Dict[str, Any]], current_elements: Dict[str, Any]) -> Dict[str, Any]:
        """Extract patterns from successful extraction results"""
        
        # Start with current elements
        adapted_elements = current_elements.copy()
        
        # Analyze what made these extractions successful
        high_quality_results = [r for r in successful_results if r["confidence"] > 0.8]
        
        if high_quality_results:
            # If we have high-quality results, enhance hints based on data quality
            avg_data_quality = sum(r["data_quality"] for r in high_quality_results) / len(high_quality_results)
            
            if avg_data_quality > 5:
                # Add emphasis on thoroughness
                if "extraction_hints" in adapted_elements:
                    adapted_elements["extraction_hints"].append("Be extra thorough in extraction")
                    adapted_elements["adaptation_level"] = "enhanced_thoroughness"
            
            # Enhance quality indicators based on successful extractions
            if "quality_indicators" in adapted_elements:
                # Count which fields were most commonly successful
                all_elements = []
                for result in high_quality_results:
                    elements_used = result.get("elements_used", {})
                    if "quality_indicators" in elements_used:
                        all_elements.extend(elements_used["quality_indicators"])
                
                if all_elements:
                    # Get most common quality indicators
                    common_indicators = [item for item, count in Counter(all_elements).most_common(5)]
                    adapted_elements["quality_indicators"] = common_indicators
                    adapted_elements["adaptation_level"] = "optimized_indicators"
        
        return adapted_elements
    
    def _has_adapted_prompt(self, url: str, purpose: str) -> bool:
        """Check if we have adapted prompts for this URL pattern and purpose"""
        prompt_key = f"{purpose}_{self._get_url_pattern(url)}"
        return prompt_key in self.prompt_variations
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Get statistics about adaptation and learning"""
        
        total_patterns = len(self.success_metrics)
        total_attempts = sum(metrics.get("attempts", 0) for metrics in self.success_metrics.values())
        total_adaptations = len(self.prompt_variations)
        
        # Calculate overall success rates
        pattern_stats = []
        for pattern, metrics in self.success_metrics.items():
            if metrics.get("attempts", 0) > 0:
                success_rate = metrics.get("successes", 0) / metrics["attempts"]
                avg_confidence = metrics.get("total_confidence", 0) / metrics["attempts"]
                
                pattern_stats.append({
                    "pattern": pattern,
                    "attempts": metrics["attempts"],
                    "success_rate": success_rate,
                    "avg_confidence": avg_confidence,
                    "has_adaptation": pattern in self.prompt_variations
                })
        
        # Sort by success rate
        pattern_stats.sort(key=lambda x: x["success_rate"], reverse=True)
        
        return {
            "total_patterns_tracked": total_patterns,
            "total_attempts": total_attempts,
            "total_adaptations": total_adaptations,
            "adaptation_enabled": self.adaptation_enabled,
            "min_attempts_threshold": self.min_attempts_for_adaptation,
            "top_performing_patterns": pattern_stats[:5]
        }
    
    def reset_adaptations(self, pattern: str = None):
        """Reset adaptation data"""
        
        if pattern:
            # Reset specific pattern
            if pattern in self.prompt_variations:
                del self.prompt_variations[pattern]
            if pattern in self.success_metrics:
                del self.success_metrics[pattern]
        else:
            # Reset all adaptations
            self.prompt_variations.clear()
            self.success_metrics.clear()
    
    def set_adaptation_enabled(self, enabled: bool):
        """Enable or disable adaptation"""
        self.adaptation_enabled = enabled
    
    def set_adaptation_threshold(self, min_attempts: int):
        """Set minimum attempts required before adaptation"""
        self.min_attempts_for_adaptation = max(1, min_attempts)
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Adaptive strategy confidence increases with learning"""
        
        base_confidence = super().get_confidence_score(url, html_content, purpose)
        
        # Check if we have adaptations for this pattern
        prompt_key = f"{purpose}_{self._get_url_pattern(url)}"
        
        if prompt_key in self.success_metrics:
            metrics = self.success_metrics[prompt_key]
            attempts = metrics.get("attempts", 0)
            
            if attempts >= self.min_attempts_for_adaptation:
                success_rate = metrics.get("successes", 0) / attempts
                
                # Boost confidence based on historical success
                if success_rate > 0.8:
                    base_confidence += 0.15
                elif success_rate > 0.6:
                    base_confidence += 0.1
                elif success_rate > 0.4:
                    base_confidence += 0.05
        
        return min(base_confidence, 1.0)
