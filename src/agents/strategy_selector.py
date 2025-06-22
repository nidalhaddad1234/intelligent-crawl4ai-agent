#!/usr/bin/env python3
"""
Strategy Selector
Selects optimal extraction strategies based on website analysis and purpose
"""

import json
import logging
from typing import Dict, Any, List
from dataclasses import dataclass

from .intelligent_analyzer import WebsiteAnalysis, WebsiteType, ExtractionPurpose

logger = logging.getLogger("strategy_selector")

@dataclass
class StrategyRecommendation:
    primary_strategy: str
    fallback_strategies: List[str]
    extraction_config: Dict[str, Any]
    browser_config: Dict[str, Any]
    estimated_success_rate: float
    reasoning: str

class StrategySelector:
    """Selects optimal extraction strategies based on AI analysis"""
    
    def __init__(self, ollama_client, chromadb_manager):
        self.ollama_client = ollama_client
        self.chromadb_manager = chromadb_manager
        
        # Pre-defined strategy patterns for common scenarios
        self.strategy_patterns = self._initialize_strategy_patterns()
    
    def _initialize_strategy_patterns(self) -> Dict[str, Dict]:
        """Initialize common strategy patterns"""
        return {
            "directory_listing_company_info": {
                "primary_strategy": "css_extraction",
                "fallback_strategies": ["llm_extraction"],
                "extraction_config": {
                    "company_name": "h2, h3, .company-name, .business-name, [data-business-name]",
                    "address": ".address, .location, [itemprop='address'], .street-address",
                    "phone": ".phone, .tel, a[href^='tel:'], [itemprop='telephone']",
                    "website": "a[href^='http']:not([href*='google']):not([href*='yelp']):not([href*='facebook'])",
                    "email": "a[href^='mailto:'], [data-email]",
                    "rating": ".rating, .stars, [data-rating]",
                    "category": ".category, .business-type, [data-category]"
                },
                "browser_config": {"wait_for": "css:.listing, .business, .company"},
                "estimated_success_rate": 0.85,
                "reasoning": "Directory sites typically have predictable CSS patterns for business listings"
            },
            
            "e_commerce_product_data": {
                "primary_strategy": "json_css_extraction",
                "fallback_strategies": ["llm_extraction", "css_extraction"],
                "extraction_config": {
                    "product_name": ".product-title, h1, [data-product-title]",
                    "price": ".price, .cost, [data-price], .product-price",
                    "description": ".description, .product-description, [data-description]",
                    "images": "img[src*='product'], .product-image img",
                    "rating": ".rating, .stars, [data-rating]",
                    "availability": ".stock, .availability, [data-stock]"
                },
                "browser_config": {"wait_for": "css:.product, .item", "js_scroll": True},
                "estimated_success_rate": 0.80,
                "reasoning": "E-commerce sites often have structured data and consistent product layouts"
            },
            
            "social_media_profile_info": {
                "primary_strategy": "llm_extraction",
                "fallback_strategies": ["css_extraction"],
                "extraction_config": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "title": {"type": "string"},
                            "company": {"type": "string"},
                            "location": {"type": "string"},
                            "bio": {"type": "string"},
                            "connections": {"type": "number"},
                            "contact_info": {"type": "object"}
                        }
                    },
                    "instruction": "Extract profile information including name, professional title, company, location, and bio"
                },
                "browser_config": {"wait_for": "networkidle", "timeout": 30000},
                "estimated_success_rate": 0.75,
                "reasoning": "Social media profiles require AI to understand context and relationships"
            },
            
            "news_article_content": {
                "primary_strategy": "llm_extraction",
                "fallback_strategies": ["css_extraction"],
                "extraction_config": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "headline": {"type": "string"},
                            "author": {"type": "string"},
                            "publish_date": {"type": "string"},
                            "content": {"type": "string"},
                            "summary": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "instruction": "Extract article headline, author, publish date, full content, and summary"
                },
                "browser_config": {"wait_for": "css:article, .article, .content"},
                "estimated_success_rate": 0.90,
                "reasoning": "News articles have consistent structure that AI can reliably extract"
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
                            "contact_forms": {"type": "array", "items": {"type": "string"}},
                            "key_personnel": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "instruction": "Find ALL contact information: emails, phone numbers, addresses, social media links, contact forms, and key personnel names"
                },
                "browser_config": {"wait_for": "networkidle", "js_scroll": True},
                "estimated_success_rate": 0.80,
                "reasoning": "Contact discovery benefits from AI's pattern recognition across diverse page layouts"
            }
        }
    
    async def select_strategy(self, analysis: WebsiteAnalysis, purpose: str, 
                            additional_context: str = "") -> StrategyRecommendation:
        """Select optimal strategy based on analysis and purpose"""
        
        logger.info(f"Selecting strategy for {analysis.website_type.value} site with purpose: {purpose}")
        
        # Step 1: Check for exact pattern match
        pattern_key = f"{analysis.website_type.value}_{purpose}"
        if pattern_key in self.strategy_patterns:
            pattern = self.strategy_patterns[pattern_key]
            return StrategyRecommendation(**pattern)
        
        # Step 2: Use AI to generate custom strategy
        custom_strategy = await self._generate_custom_strategy(analysis, purpose, additional_context)
        if custom_strategy:
            return custom_strategy
        
        # Step 3: Use learned patterns from ChromaDB
        learned_strategy = await self._get_learned_strategy(analysis, purpose)
        if learned_strategy:
            return learned_strategy
        
        # Step 4: Fallback to rule-based selection
        return self._rule_based_strategy_selection(analysis, purpose)
    
    async def _generate_custom_strategy(self, analysis: WebsiteAnalysis, purpose: str, 
                                      additional_context: str) -> StrategyRecommendation:
        """Use AI to generate custom extraction strategy"""
        
        prompt = f"""
        You are an expert web scraping strategist. Analyze this website and create an optimal extraction strategy.
        
        Website Analysis:
        - URL: {analysis.url}
        - Type: {analysis.website_type.value}
        - Complexity: {analysis.estimated_complexity}
        - Has JavaScript: {analysis.has_javascript}
        - Frameworks: {analysis.detected_frameworks}
        - Anti-bot measures: {analysis.anti_bot_measures}
        - Content patterns: {analysis.content_patterns}
        
        Extraction Purpose: {purpose}
        Additional Context: {additional_context}
        
        Choose the best extraction strategy and provide configuration:
        
        Available strategies:
        1. css_extraction - Fast, reliable for static content with predictable selectors
        2. llm_extraction - Intelligent, handles complex content and context
        3. json_css_extraction - Best for structured data with JSON-LD or microdata
        
        Respond in JSON format:
        {{
            "primary_strategy": "css_extraction",
            "fallback_strategies": ["llm_extraction"],
            "extraction_config": {{
                "field_name": "css_selector_or_schema"
            }},
            "browser_config": {{
                "wait_for": "css:selector",
                "timeout": 30000,
                "js_scroll": false
            }},
            "estimated_success_rate": 0.85,
            "reasoning": "Detailed explanation of why this strategy is optimal"
        }}
        """
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=prompt,
                format="json"
            )
            
            strategy_data = json.loads(response)
            return StrategyRecommendation(**strategy_data)
            
        except Exception as e:
            logger.warning(f"Custom strategy generation failed: {e}")
            return None
    
    async def _get_learned_strategy(self, analysis: WebsiteAnalysis, purpose: str) -> StrategyRecommendation:
        """Retrieve learned strategy from ChromaDB based on similar sites"""
        
        try:
            # Query similar successful extractions
            query_text = f"{analysis.website_type.value} {purpose} {' '.join(analysis.content_patterns)}"
            
            similar_extractions = await self.chromadb_manager.query_similar_strategies(
                query_text=query_text,
                website_type=analysis.website_type.value,
                purpose=purpose,
                limit=3
            )
            
            if similar_extractions:
                # Use the most successful strategy
                best_strategy = max(similar_extractions, key=lambda x: x.get("success_rate", 0))
                
                return StrategyRecommendation(
                    primary_strategy=best_strategy["strategy"],
                    fallback_strategies=best_strategy.get("fallback_strategies", ["llm_extraction"]),
                    extraction_config=best_strategy.get("extraction_config", {}),
                    browser_config=best_strategy.get("browser_config", {"wait_for": "networkidle"}),
                    estimated_success_rate=best_strategy.get("success_rate", 0.70),
                    reasoning=f"Based on successful extraction from similar {analysis.website_type.value} sites"
                )
                
        except Exception as e:
            logger.warning(f"Learned strategy retrieval failed: {e}")
        
        return None
    
    def _rule_based_strategy_selection(self, analysis: WebsiteAnalysis, purpose: str) -> StrategyRecommendation:
        """Fallback rule-based strategy selection"""
        
        # General rules based on website characteristics and purpose
        
        if purpose == "company_info":
            if analysis.website_type == WebsiteType.DIRECTORY_LISTING:
                return StrategyRecommendation(
                    primary_strategy="css_extraction",
                    fallback_strategies=["llm_extraction"],
                    extraction_config={
                        "company_name": "h2, h3, .company-name, .business-name",
                        "address": ".address, .location",
                        "phone": ".phone, .tel, a[href^='tel:']",
                        "website": "a[href^='http']"
                    },
                    browser_config={"wait_for": "css:body"},
                    estimated_success_rate=0.75,
                    reasoning="Rule-based: Directory listings typically have predictable patterns"
                )
            
            elif analysis.content_dynamically_loaded or analysis.estimated_complexity == "high":
                return StrategyRecommendation(
                    primary_strategy="llm_extraction",
                    fallback_strategies=["css_extraction"],
                    extraction_config={
                        "schema": {
                            "type": "object",
                            "properties": {
                                "company_name": {"type": "string"},
                                "address": {"type": "string"},
                                "phone": {"type": "string"},
                                "email": {"type": "string"},
                                "website": {"type": "string"}
                            }
                        },
                        "instruction": "Extract company information including name, address, and contact details"
                    },
                    browser_config={"wait_for": "networkidle", "js_scroll": True},
                    estimated_success_rate=0.70,
                    reasoning="Rule-based: Dynamic content requires AI-powered extraction"
                )
        
        elif purpose == "contact_discovery":
            return StrategyRecommendation(
                primary_strategy="llm_extraction",
                fallback_strategies=["css_extraction"],
                extraction_config={
                    "schema": {
                        "type": "object",
                        "properties": {
                            "emails": {"type": "array", "items": {"type": "string"}},
                            "phones": {"type": "array", "items": {"type": "string"}},
                            "social_links": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "instruction": "Find all contact information: emails, phone numbers, and social media links"
                },
                browser_config={"wait_for": "networkidle"},
                estimated_success_rate=0.75,
                reasoning="Rule-based: Contact discovery benefits from AI pattern recognition"
            )
        
        elif purpose == "product_data" and analysis.website_type == WebsiteType.E_COMMERCE:
            return StrategyRecommendation(
                primary_strategy="json_css_extraction",
                fallback_strategies=["llm_extraction", "css_extraction"],
                extraction_config={
                    "name": ".product-title, h1",
                    "price": ".price, .cost",
                    "description": ".description",
                    "image": ".product-image img"
                },
                browser_config={"wait_for": "css:.product", "js_scroll": True},
                estimated_success_rate=0.80,
                reasoning="Rule-based: E-commerce sites have structured product data"
            )
        
        # Default fallback for any unmatched scenario
        return StrategyRecommendation(
            primary_strategy="llm_extraction",
            fallback_strategies=["css_extraction"],
            extraction_config={
                "instruction": f"Extract {purpose} data from this webpage. Be thorough and accurate."
            },
            browser_config={"wait_for": "networkidle"},
            estimated_success_rate=0.65,
            reasoning="Rule-based: Default AI extraction for unrecognized patterns"
        )
    
    async def learn_from_extraction(self, url: str, strategy: StrategyRecommendation, 
                                  result: Dict[str, Any], analysis: WebsiteAnalysis, purpose: str):
        """Learn from extraction results to improve future strategy selection"""
        
        success_rate = 1.0 if result.get("success", False) else 0.0
        
        # Enhance success rate based on data quality
        if result.get("success", False):
            extracted_data = result.get("extracted_data", {})
            if isinstance(extracted_data, dict):
                # Check data completeness
                non_empty_fields = sum(1 for v in extracted_data.values() if v and str(v).strip())
                total_fields = len(extracted_data)
                
                if total_fields > 0:
                    completeness_score = non_empty_fields / total_fields
                    success_rate = success_rate * 0.7 + completeness_score * 0.3
        
        # Store learning data in ChromaDB
        learning_data = {
            "url": url,
            "website_type": analysis.website_type.value,
            "purpose": purpose,
            "strategy": strategy.primary_strategy,
            "fallback_strategies": strategy.fallback_strategies,
            "extraction_config": strategy.extraction_config,
            "browser_config": strategy.browser_config,
            "success_rate": success_rate,
            "frameworks": analysis.detected_frameworks,
            "complexity": analysis.estimated_complexity,
            "anti_bot_measures": analysis.anti_bot_measures,
            "content_patterns": analysis.content_patterns
        }
        
        await self.chromadb_manager.store_strategy_learning(learning_data)
        
        logger.info(f"Learned from extraction: {url} - Success rate: {success_rate:.2f}")
