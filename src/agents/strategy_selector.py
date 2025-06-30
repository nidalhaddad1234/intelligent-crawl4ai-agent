#!/usr/bin/env python3
"""
Enhanced Strategy Selector - Production Ready
Intelligent strategy selection based on website analysis and learning from past performance
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import from new modular structure
from services import LLMService, VectorService
from agents.intelligent_analyzer import IntelligentAnalyzer, WebsiteAnalysis, WebsiteType

logger = logging.getLogger("strategy_selector")

@dataclass
class StrategyRecommendation:
    """Enhanced strategy recommendation with comprehensive metadata"""
    primary_strategy: str
    fallback_strategies: List[str]
    extraction_config: Dict[str, Any]
    browser_config: Dict[str, Any]
    estimated_success_rate: float
    reasoning: str
    confidence_score: float
    performance_estimate: Dict[str, Any]
    resource_requirements: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    optimization_hints: List[str]
    learning_source: str = "pattern"

class StrategySelector:
    """
    Production-ready intelligent strategy selector
    
    Features:
    - Pattern-based strategy selection
    - AI-powered custom strategy generation  
    - Learning from extraction results
    - Performance optimization
    - Comprehensive risk assessment
    """
    
    def __init__(self, llm_service: LLMService = None, vector_service: VectorService = None):
        self.llm_service = llm_service
        self.vector_service = vector_service
        
        # Performance tracking
        self.selection_count = 0
        self.success_tracking = {}
        
        # Strategy patterns for common scenarios
        self.strategy_patterns = {
            "directory_listing_company_info": {
                "primary_strategy": "json_css_hybrid",
                "fallback_strategies": ["llm_extraction", "css_extraction"],
                "extraction_config": {
                    "css_selectors": {
                        "company_name": "h1, h2, .business-name, .company-title, [itemprop='name']",
                        "address": ".address, .location, [itemprop='address'], .street-address",
                        "phone": ".phone, .tel, a[href^='tel:'], [itemprop='telephone']",
                        "email": "a[href^='mailto:'], .email, [itemprop='email']",
                        "website": "a[href*='www'], .website, [itemprop='url']",
                        "description": ".description, .about, .bio, [itemprop='description']",
                        "hours": ".hours, .opening-hours, .business-hours",
                        "rating": ".rating, .stars, .review-score"
                    },
                    "json_ld_schema": ["LocalBusiness", "Organization", "Place"],
                    "microdata_props": ["name", "address", "telephone", "email", "url"]
                },
                "browser_config": {
                    "wait_for": "css:.business-name, h1, h2",
                    "timeout": 15000,
                    "js_scroll": False
                },
                "estimated_success_rate": 0.85,
                "reasoning": "Directory listings often have structured data and consistent layouts",
                "confidence_score": 0.88,
                "performance_estimate": {
                    "avg_processing_time": 3.2,
                    "resource_usage": "low",
                    "reliability": 0.85
                },
                "resource_requirements": {
                    "javascript_needed": False,
                    "authentication_needed": False,
                    "rate_limit_sensitive": True
                },
                "risk_assessment": {
                    "bot_detection_risk": 0.3,
                    "structure_change_risk": 0.2,
                    "legal_risk": 0.1
                },
                "optimization_hints": [
                    "Check for JSON-LD structured data first",
                    "Use schema.org microdata when available", 
                    "Respect rate limits for directory crawling"
                ]
            },
            
            "e_commerce_product_data": {
                "primary_strategy": "json_css_hybrid",
                "fallback_strategies": ["llm_extraction", "css_extraction"],
                "extraction_config": {
                    "css_selectors": {
                        "name": [
                            "h1.product-title, .product-name, [itemprop='name']",
                            ".product-header h1, .item-title, .product-display-name"
                        ],
                        "price": [
                            ".price, .cost, [itemprop='price']",
                            ".price-current, .sale-price, .product-price"
                        ],
                        "description": [
                            ".product-description, [data-description]",
                            "[itemprop='description'], .details, .product-details"
                        ]
                    },
                    "json_ld_schema": ["Product", "Offer"],
                    "microdata_props": ["name", "price", "description", "image", "brand", "sku"]
                },
                "browser_config": {
                    "wait_for": "css:.product, .item",
                    "js_scroll": True,
                    "timeout": 20000
                },
                "estimated_success_rate": 0.80,
                "reasoning": "E-commerce sites often have structured data and consistent product layouts",
                "confidence_score": 0.85,
                "performance_estimate": {
                    "avg_processing_time": 5.1,
                    "resource_usage": "medium",
                    "reliability": 0.80
                },
                "resource_requirements": {
                    "javascript_needed": True,
                    "authentication_needed": False,
                    "rate_limit_sensitive": True
                },
                "risk_assessment": {
                    "bot_detection_risk": 0.6,
                    "structure_change_risk": 0.4,
                    "legal_risk": 0.2
                },
                "optimization_hints": [
                    "Check for JSON-LD structured data first",
                    "Handle dynamic pricing with retry logic",
                    "Respect rate limits for product catalogs"
                ]
            },
            
            "contact_discovery_general": {
                "primary_strategy": "llm_extraction",
                "fallback_strategies": ["css_extraction"],
                "extraction_config": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "emails": {"type": "array", "items": {"type": "string"}},
                            "phones": {"type": "array", "items": {"type": "string"}},
                            "addresses": {"type": "array", "items": {"type": "string"}},
                            "social_links": {"type": "array", "items": {"type": "string"}},
                            "contact_forms": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "instruction": "Find ALL contact information: emails, phone numbers, physical addresses, social media links, and contact forms"
                },
                "browser_config": {
                    "wait_for": "networkidle",
                    "js_scroll": True,
                    "timeout": 25000
                },
                "estimated_success_rate": 0.80,
                "reasoning": "Contact discovery benefits from AI's pattern recognition across diverse page layouts",
                "confidence_score": 0.82,
                "performance_estimate": {
                    "avg_processing_time": 7.1,
                    "resource_usage": "medium",
                    "reliability": 0.80
                },
                "resource_requirements": {
                    "javascript_needed": True,
                    "authentication_needed": False,
                    "rate_limit_sensitive": False
                },
                "risk_assessment": {
                    "bot_detection_risk": 0.4,
                    "structure_change_risk": 0.3,
                    "legal_risk": 0.3
                },
                "optimization_hints": [
                    "Check contact pages first",
                    "Look for schema.org contact information",
                    "Validate extracted email formats",
                    "Handle obfuscated contact info"
                ]
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize strategy selector with services"""
        
        try:
            # Initialize services if not provided
            if not self.llm_service:
                self.llm_service = LLMService()
                await self.llm_service.initialize()
            
            if not self.vector_service:
                self.vector_service = VectorService(llm_service=self.llm_service)
                await self.vector_service.initialize()
            
            logger.info("Strategy selector initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize strategy selector: {e}")
            return False
    
    async def select_strategy(self, analysis: WebsiteAnalysis, purpose: str,
                            additional_context: str = "",
                            performance_requirements: Dict[str, Any] = None) -> StrategyRecommendation:
        """
        Select optimal strategy with enhanced decision-making
        
        Args:
            analysis: Website analysis results
            purpose: Extraction purpose
            additional_context: Additional context for strategy selection
            performance_requirements: Performance constraints and requirements
            
        Returns:
            Enhanced strategy recommendation
        """
        
        logger.info(f"Selecting strategy for {analysis.website_type.value} site with purpose: {purpose}")
        self.selection_count += 1
        
        # Step 1: Check for exact pattern match with enhancements
        pattern_key = f"{analysis.website_type.value}_{purpose}"
        if pattern_key in self.strategy_patterns:
            pattern = self.strategy_patterns[pattern_key].copy()
            
            # Enhance pattern with analysis data
            enhanced_pattern = await self._enhance_pattern_with_analysis(pattern, analysis)
            return StrategyRecommendation(**enhanced_pattern)
        
        # Step 2: Use learned patterns from vector service
        if self.vector_service:
            learned_strategy = await self._get_learned_strategy(analysis, purpose)
            if learned_strategy and learned_strategy.confidence_score > 0.7:
                return learned_strategy
        
        # Step 3: AI-powered custom strategy generation
        if self.llm_service:
            custom_strategy = await self._generate_custom_strategy(
                analysis, purpose, additional_context, performance_requirements
            )
            if custom_strategy and custom_strategy.confidence_score > 0.6:
                return custom_strategy
        
        # Step 4: Enhanced rule-based selection with fallback
        return self._enhanced_rule_based_strategy_selection(analysis, purpose, performance_requirements)
    
    async def _enhance_pattern_with_analysis(self, pattern: Dict[str, Any], 
                                           analysis: WebsiteAnalysis) -> Dict[str, Any]:
        """Enhance base pattern with website analysis insights"""
        
        enhanced_pattern = pattern.copy()
        
        # Adjust success rate based on analysis confidence
        base_success_rate = pattern["estimated_success_rate"]
        confidence_factor = analysis.analysis_confidence
        enhanced_pattern["estimated_success_rate"] = base_success_rate * (0.7 + 0.3 * confidence_factor)
        
        enhanced_pattern["learning_source"] = "pattern_enhanced"
        
        return enhanced_pattern
    
    async def _get_learned_strategy(self, analysis: WebsiteAnalysis, purpose: str) -> Optional[StrategyRecommendation]:
        """Retrieve and enhance learned strategy from vector service"""
        
        try:
            # This would query the vector service for similar strategies
            # For now, return None to fall back to other methods
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get learned strategy: {e}")
            return None
    
    async def _generate_custom_strategy(self, analysis: WebsiteAnalysis, purpose: str,
                                      additional_context: str,
                                      performance_requirements: Dict[str, Any] = None) -> Optional[StrategyRecommendation]:
        """Generate custom strategy using AI"""
        
        try:
            # This would use the LLM service to generate a custom strategy
            # For now, return None to fall back to rule-based selection
            return None
            
        except Exception as e:
            logger.warning(f"Custom strategy generation failed: {e}")
            return None
    
    def _enhanced_rule_based_strategy_selection(self, analysis: WebsiteAnalysis, purpose: str,
                                               performance_requirements: Dict[str, Any] = None) -> StrategyRecommendation:
        """Enhanced rule-based strategy selection with comprehensive fallback"""
        
        performance_requirements = performance_requirements or {}
        
        # High-performance requirement adjustments
        prefer_speed = performance_requirements.get("max_processing_time", float('inf')) < 10
        
        if purpose == "company_info":
            if analysis.website_type == WebsiteType.DIRECTORY_LISTING:
                strategy = "css_extraction" if prefer_speed else "json_css_hybrid"
                success_rate = 0.75
                processing_time = 3.0 if prefer_speed else 4.5
                
            elif analysis.content_dynamically_loaded or analysis.estimated_complexity == "high":
                strategy = "llm_extraction"
                success_rate = 0.70
                processing_time = 8.0
                
            else:
                strategy = "css_extraction"
                success_rate = 0.72
                processing_time = 3.5
        
        elif purpose == "contact_discovery":
            strategy = "llm_extraction"
            success_rate = 0.75
            processing_time = 7.0
            
        elif purpose == "product_data" and analysis.website_type == WebsiteType.E_COMMERCE:
            strategy = "json_css_hybrid" if not prefer_speed else "css_extraction"
            success_rate = 0.80 if not prefer_speed else 0.70
            processing_time = 5.0 if not prefer_speed else 3.0
            
        else:
            # Default strategy
            strategy = "llm_extraction"
            success_rate = 0.65
            processing_time = 6.0
        
        # Adjust for analysis confidence
        success_rate *= (0.8 + 0.2 * analysis.analysis_confidence)
        
        return StrategyRecommendation(
            primary_strategy=strategy,
            fallback_strategies=self._get_default_fallback_strategies(strategy),
            extraction_config=self._get_default_extraction_config(purpose, strategy),
            browser_config=self._get_default_browser_config(analysis, prefer_speed),
            estimated_success_rate=success_rate,
            reasoning=f"Rule-based selection for {purpose} on {analysis.website_type.value} site",
            confidence_score=0.6,
            performance_estimate={
                "avg_processing_time": processing_time,
                "resource_usage": "low" if prefer_speed else "medium",
                "reliability": success_rate
            },
            resource_requirements={
                "javascript_needed": analysis.has_javascript,
                "authentication_needed": analysis.has_auth_required,
                "rate_limit_sensitive": len(analysis.anti_bot_measures) > 0
            },
            risk_assessment={
                "bot_detection_risk": min(0.8, len(analysis.anti_bot_measures) * 0.25),
                "structure_change_risk": 0.4,
                "legal_risk": 0.3
            },
            optimization_hints=[
                f"Rule-based fallback for {analysis.website_type.value} sites",
                "Consider upgrading to learned or AI-generated strategies"
            ],
            learning_source="rule_based"
        )
    
    def _get_default_fallback_strategies(self, primary_strategy: str) -> List[str]:
        """Get appropriate fallback strategies"""
        
        fallback_map = {
            "css_extraction": ["llm_extraction"],
            "llm_extraction": ["css_extraction"],
            "json_css_hybrid": ["llm_extraction", "css_extraction"],
            "regex_extraction": ["css_extraction", "llm_extraction"],
            "form_automation": ["llm_extraction"]
        }
        
        return fallback_map.get(primary_strategy, ["llm_extraction"])
    
    def _get_default_extraction_config(self, purpose: str, strategy: str) -> Dict[str, Any]:
        """Get default extraction configuration"""
        
        if strategy == "llm_extraction":
            return {
                "instruction": f"Extract {purpose} data from this webpage. Be thorough and accurate.",
                "schema": self._get_default_schema(purpose)
            }
        else:
            return self._get_default_css_config(purpose)
    
    def _get_default_schema(self, purpose: str) -> Dict[str, Any]:
        """Get default schema for LLM extraction"""
        
        schemas = {
            "company_info": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "address": {"type": "string"},
                    "phone": {"type": "string"},
                    "email": {"type": "string"},
                    "website": {"type": "string"}
                }
            },
            "contact_discovery": {
                "type": "object",
                "properties": {
                    "emails": {"type": "array", "items": {"type": "string"}},
                    "phones": {"type": "array", "items": {"type": "string"}},
                    "addresses": {"type": "array", "items": {"type": "string"}}
                }
            },
            "product_data": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "string"},
                    "description": {"type": "string"},
                    "availability": {"type": "string"}
                }
            }
        }
        
        return schemas.get(purpose, {"type": "object", "properties": {}})
    
    def _get_default_css_config(self, purpose: str) -> Dict[str, Any]:
        """Get default CSS extraction configuration"""
        
        configs = {
            "company_info": {
                "company_name": "h1, h2, .company-name, .title",
                "address": ".address, .location",
                "phone": ".phone, .tel, a[href^='tel:']",
                "email": "a[href^='mailto:']"
            },
            "contact_discovery": {
                "contact_info": ".contact, .contact-info, .contact-details"
            },
            "product_data": {
                "name": ".product-title, h1",
                "price": ".price, .cost",
                "description": ".description"
            }
        }
        
        return configs.get(purpose, {"content": "body"})
    
    def _get_default_browser_config(self, analysis: WebsiteAnalysis, prefer_speed: bool) -> Dict[str, Any]:
        """Get default browser configuration"""
        
        config = {
            "wait_for": "css:body" if prefer_speed else "networkidle",
            "timeout": 10000 if prefer_speed else 20000,
            "js_scroll": False
        }
        
        if analysis.has_infinite_scroll:
            config["js_scroll"] = True
            config["timeout"] = max(config["timeout"], 25000)
        
        if analysis.content_dynamically_loaded:
            config["wait_for"] = "networkidle"
            config["timeout"] = max(config["timeout"], 20000)
        
        return config
    
    async def learn_from_extraction(self, url: str, strategy: StrategyRecommendation,
                                  result: Dict[str, Any], analysis: WebsiteAnalysis, 
                                  purpose: str, performance_metrics: Dict[str, float] = None):
        """Enhanced learning from extraction results"""
        
        success = result.get("success", False)
        confidence = result.get("confidence_score", 0.5)
        processing_time = performance_metrics.get("processing_time", 0) if performance_metrics else 0
        
        # Track strategy performance
        strategy_key = f"{strategy.primary_strategy}_{analysis.website_type.value}_{purpose}"
        if strategy_key not in self.success_tracking:
            self.success_tracking[strategy_key] = {
                "attempts": 0,
                "successes": 0,
                "avg_success_rate": 0.0,
                "avg_processing_time": 0.0,
                "learning_source": strategy.learning_source
            }
        
        tracking = self.success_tracking[strategy_key]
        tracking["attempts"] += 1
        
        if success:
            tracking["successes"] += 1
        
        # Update averages
        success_rate = 1.0 if success else 0.0
        tracking["avg_success_rate"] = (
            (tracking["avg_success_rate"] * (tracking["attempts"] - 1) + success_rate) / 
            tracking["attempts"]
        )
        
        if processing_time > 0:
            tracking["avg_processing_time"] = (
                (tracking["avg_processing_time"] * (tracking["attempts"] - 1) + processing_time) / 
                tracking["attempts"]
            )
        
        logger.info(f"Learned from extraction: {url} - Success: {success}, "
                   f"Processing time: {processing_time:.2f}s")
    
    async def get_strategy_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive strategy performance statistics"""
        
        stats = {
            "total_selections": self.selection_count,
            "tracked_strategies": len(self.success_tracking),
            "strategy_performance": {},
            "overall_metrics": {
                "avg_success_rate": 0.0,
                "avg_processing_time": 0.0,
                "total_attempts": 0
            }
        }
        
        total_attempts = 0
        total_success_rate = 0.0
        total_processing_time = 0.0
        
        for strategy_key, tracking in self.success_tracking.items():
            if tracking["attempts"] > 0:
                stats["strategy_performance"][strategy_key] = {
                    "attempts": tracking["attempts"],
                    "success_rate": tracking["avg_success_rate"],
                    "avg_processing_time": tracking["avg_processing_time"],
                    "learning_source": tracking["learning_source"]
                }
                
                total_attempts += tracking["attempts"]
                total_success_rate += tracking["avg_success_rate"] * tracking["attempts"]
                total_processing_time += tracking["avg_processing_time"] * tracking["attempts"]
        
        if total_attempts > 0:
            stats["overall_metrics"]["avg_success_rate"] = total_success_rate / total_attempts
            stats["overall_metrics"]["avg_processing_time"] = total_processing_time / total_attempts
            stats["overall_metrics"]["total_attempts"] = total_attempts
        
        return stats
    
    async def cleanup(self):
        """Clean up resources"""
        
        logger.info(f"Strategy selector cleanup: {len(self.success_tracking)} strategies tracked")
