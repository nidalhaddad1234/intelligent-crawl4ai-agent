#!/usr/bin/env python3
"""
Hybrid Extraction Strategies
Combines CSS selectors with LLM intelligence for optimal extraction
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from bs4 import BeautifulSoup

from .base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType
from .css_strategies import DirectoryCSSStrategy, EcommerceCSSStrategy, NewsCSSStrategy
from .llm_strategies import IntelligentLLMStrategy

class JSONCSSHybridStrategy(BaseExtractionStrategy):
    """
    Combines JSON-LD structured data extraction with CSS fallbacks
    
    Examples:
    - Extract product data from e-commerce sites with schema.org markup
    - Get business information from sites with structured data
    - Handle sites with partial structured data coverage
    """
    
    def __init__(self, ollama_client=None, **kwargs):
        super().__init__(strategy_type=StrategyType.HYBRID, **kwargs)
        self.ollama_client = ollama_client
        
        # Mapping of structured data types to CSS fallbacks
        self.structured_fallbacks = {
            "Product": {
                "name": [".product-title, .product-name, h1"],
                "price": [".price, .cost, .amount"],
                "description": [".description, .product-description"],
                "image": [".product-image img, .main-image img"],
                "brand": [".brand, .manufacturer"],
                "sku": [".sku, .product-id"]
            },
            "Organization": {
                "name": [".company-name, .organization-name, h1"],
                "description": [".description, .about, .company-description"],
                "address": [".address, .location"],
                "telephone": [".phone, .tel, a[href^='tel:']"],
                "email": ["a[href^='mailto:']"],
                "url": [".website, .url"]
            },
            "LocalBusiness": {
                "name": [".business-name, .company-name, h1"],
                "address": [".address, .location"],
                "telephone": [".phone, .tel, a[href^='tel:']"],
                "openingHours": [".hours, .opening-hours"],
                "priceRange": [".price-range, .pricing"]
            },
            "Article": {
                "headline": ["h1, .headline, .title"],
                "author": [".author, .byline"],
                "datePublished": ["time, .date, .published"],
                "articleBody": [".content, .article-content, .post-content"]
            }
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Phase 1: Extract structured data (JSON-LD, microdata)
            structured_data = self._extract_all_structured_data(html_content)
            
            # Phase 2: CSS fallback for missing fields
            css_data = self._extract_css_fallbacks(html_content, structured_data, purpose)
            
            # Phase 3: Merge and validate data
            final_data = self._merge_data_sources(structured_data, css_data, purpose)
            
            # Phase 4: LLM enhancement if available and needed
            if self.ollama_client and self._needs_llm_enhancement(final_data, purpose):
                enhanced_data = await self._llm_enhance_data(url, html_content, final_data, purpose)
                if enhanced_data:
                    final_data = self._merge_data_sources(final_data, enhanced_data, purpose)
            
            confidence = self._calculate_hybrid_confidence(structured_data, css_data, final_data)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(final_data),
                extracted_data=final_data,
                confidence_score=confidence,
                strategy_used="JSONCSSHybridStrategy",
                execution_time=execution_time,
                metadata={
                    "structured_data_found": bool(structured_data),
                    "css_fallbacks_used": bool(css_data),
                    "llm_enhancement_used": hasattr(self, '_llm_enhanced'),
                    "data_sources": self._get_data_source_breakdown(structured_data, css_data)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="JSONCSSHybridStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_all_structured_data(self, html_content: str) -> Dict[str, Any]:
        """Extract all structured data from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        structured_data = {}
        
        # Extract JSON-LD
        json_ld_data = self._extract_json_ld(soup)
        if json_ld_data:
            structured_data.update(json_ld_data)
        
        # Extract microdata
        microdata = self._extract_microdata(soup)
        if microdata:
            structured_data.update(microdata)
        
        # Extract RDFa
        rdfa_data = self._extract_rdfa(soup)
        if rdfa_data:
            structured_data.update(rdfa_data)
        
        return structured_data
    
    def _extract_json_ld(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract JSON-LD structured data"""
        data = {}
        
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            try:
                json_data = json.loads(script.string)
                
                if isinstance(json_data, list):
                    for item in json_data:
                        if isinstance(item, dict) and '@type' in item:
                            data_type = item['@type']
                            data[f"json_ld_{data_type}"] = item
                elif isinstance(json_data, dict) and '@type' in json_data:
                    data_type = json_data['@type']
                    data[f"json_ld_{data_type}"] = json_data
                    
            except (json.JSONDecodeError, KeyError):
                continue
        
        return data
    
    def _extract_microdata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract microdata structured data"""
        data = {}
        
        items = soup.find_all(attrs={"itemtype": True})
        for item in items:
            item_type = item.get('itemtype', '').split('/')[-1]  # Get type name
            
            props = {}
            prop_elements = item.find_all(attrs={"itemprop": True})
            
            for prop_el in prop_elements:
                prop_name = prop_el.get('itemprop')
                prop_value = (prop_el.get('content') or 
                            prop_el.get('href') or 
                            prop_el.get_text(strip=True))
                
                if prop_name and prop_value:
                    props[prop_name] = prop_value
            
            if props:
                data[f"microdata_{item_type}"] = props
        
        return data
    
    def _extract_rdfa(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract RDFa structured data"""
        data = {}
        
        # Look for elements with typeof attribute
        rdfa_elements = soup.find_all(attrs={"typeof": True})
        
        for element in rdfa_elements:
            element_type = element.get('typeof', '').split('/')[-1]
            
            props = {}
            # Look for property attributes in child elements
            prop_elements = element.find_all(attrs={"property": True})
            
            for prop_el in prop_elements:
                prop_name = prop_el.get('property')
                prop_value = (prop_el.get('content') or 
                            prop_el.get_text(strip=True))
                
                if prop_name and prop_value:
                    props[prop_name] = prop_value
            
            if props:
                data[f"rdfa_{element_type}"] = props
        
        return data
    
    def _extract_css_fallbacks(self, html_content: str, structured_data: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Extract data using CSS selectors as fallbacks"""
        soup = BeautifulSoup(html_content, 'html.parser')
        css_data = {}
        
        # Determine which structured data types are relevant
        relevant_types = self._get_relevant_structured_types(purpose)
        
        for struct_type in relevant_types:
            if struct_type in self.structured_fallbacks:
                fallback_selectors = self.structured_fallbacks[struct_type]
                
                # Check which fields are missing from structured data
                missing_fields = self._get_missing_fields(structured_data, struct_type, fallback_selectors)
                
                # Extract missing fields using CSS
                for field in missing_fields:
                    selectors = fallback_selectors[field]
                    value = self._extract_with_css_selectors(soup, selectors)
                    if value:
                        css_data[field] = value
        
        return css_data
    
    def _get_relevant_structured_types(self, purpose: str) -> List[str]:
        """Get relevant structured data types for extraction purpose"""
        type_mapping = {
            "product_data": ["Product"],
            "company_info": ["Organization", "LocalBusiness"],
            "news_content": ["Article"],
            "contact_discovery": ["Organization", "LocalBusiness"],
            "business_listings": ["LocalBusiness", "Organization"]
        }
        
        return type_mapping.get(purpose, ["Product", "Organization", "Article"])
    
    def _get_missing_fields(self, structured_data: Dict[str, Any], struct_type: str, fallback_selectors: Dict[str, List[str]]) -> List[str]:
        """Identify fields missing from structured data"""
        missing = []
        
        # Check if we have this type of structured data
        type_keys = [key for key in structured_data.keys() if struct_type in key]
        
        if not type_keys:
            # No structured data of this type, need all fields
            return list(fallback_selectors.keys())
        
        # Check which fields are missing from existing structured data
        for type_key in type_keys:
            data = structured_data[type_key]
            if isinstance(data, dict):
                for field in fallback_selectors.keys():
                    # Check various field name variations
                    field_variations = [field, field.lower(), field.replace('_', '')]
                    if not any(var in data for var in field_variations):
                        missing.append(field)
        
        return missing
    
    def _extract_with_css_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract value using CSS selectors with fallbacks"""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    # Handle different element types
                    if element.name == 'img':
                        value = element.get('src') or element.get('data-src')
                    elif element.name == 'a':
                        href = element.get('href', '')
                        if href.startswith(('tel:', 'mailto:')):
                            value = href.replace('tel:', '').replace('mailto:', '')
                        else:
                            value = element.get_text(strip=True)
                    else:
                        value = element.get_text(strip=True)
                    
                    if value and len(value) > 1:
                        return value
                        
            except Exception:
                continue
        
        return None
    
    def _merge_data_sources(self, source1: Dict[str, Any], source2: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Merge data from multiple sources with priority handling"""
        merged = {}
        
        # Priority: structured data > CSS > LLM
        # Start with structured data (highest quality)
        for key, value in source1.items():
            if isinstance(value, dict):
                # Flatten structured data for easier use
                for sub_key, sub_value in value.items():
                    if sub_value and str(sub_value).strip():
                        clean_key = self._normalize_field_name(sub_key)
                        merged[clean_key] = sub_value
            else:
                merged[key] = value
        
        # Add CSS data for missing fields
        for key, value in source2.items():
            clean_key = self._normalize_field_name(key)
            if clean_key not in merged and value and str(value).strip():
                merged[clean_key] = value
        
        return merged
    
    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field names for consistency"""
        # Convert common variations to standard names
        field_mapping = {
            'headline': 'title',
            'name': 'title',
            'articleBody': 'content',
            'datePublished': 'publish_date',
            'telephone': 'phone',
            'priceRange': 'price_range',
            'openingHours': 'hours'
        }
        
        normalized = field_mapping.get(field_name, field_name)
        return normalized.lower().replace(' ', '_')
    
    def _needs_llm_enhancement(self, data: Dict[str, Any], purpose: str) -> bool:
        """Determine if LLM enhancement is needed"""
        # Check if we have minimal required fields for the purpose
        required_fields = {
            "product_data": ["title", "price"],
            "company_info": ["title", "description"],
            "news_content": ["title", "content"],
            "contact_discovery": ["phone", "email", "address"]
        }
        
        purpose_requirements = required_fields.get(purpose, ["title"])
        found_requirements = sum(1 for req in purpose_requirements if req in data)
        
        # Need enhancement if we have less than 60% of required fields
        return found_requirements / len(purpose_requirements) < 0.6
    
    async def _llm_enhance_data(self, url: str, html_content: str, existing_data: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Use LLM to enhance incomplete data"""
        if not self.ollama_client:
            return {}
        
        self._llm_enhanced = True  # Mark for metadata
        
        # Create enhancement prompt
        prompt = f"""
Enhance this partially extracted data with additional information from the webpage.

URL: {url}
Purpose: {purpose}
Current Data: {json.dumps(existing_data, indent=2)}

HTML Content (relevant sections):
{self._get_relevant_content_sections(html_content, existing_data)[:4000]}

INSTRUCTIONS:
1. Fill in missing information that would be valuable for: {purpose}
2. DO NOT modify existing data - only add new fields
3. Focus on finding information not captured by structured data extraction
4. Ensure all added information is factually present in the content
5. Use consistent field naming

Return JSON with ONLY the additional fields to add:
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=prompt,
                format="json",
                temperature=0.3
            )
            
            enhancement_data = json.loads(response)
            return enhancement_data if isinstance(enhancement_data, dict) else {}
            
        except Exception as e:
            self.logger.warning(f"LLM enhancement failed: {e}")
            return {}
    
    def _get_relevant_content_sections(self, html_content: str, existing_data: Dict[str, Any]) -> str:
        """Get relevant content sections for LLM enhancement"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove already processed structured data scripts
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Basic content filtering based on existing data
        lines = text.split('\n')
        relevant_lines = []
        
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:  # Filter out very short lines
                # Include lines that might contain additional info
                relevant_lines.append(line)
        
        return '\n'.join(relevant_lines)
    
    def _calculate_hybrid_confidence(self, structured_data: Dict[str, Any], css_data: Dict[str, Any], final_data: Dict[str, Any]) -> float:
        """Calculate confidence based on data source quality"""
        confidence = 0.3  # Base confidence
        
        # Structured data provides highest confidence
        if structured_data:
            structured_score = min(len(structured_data) * 0.15, 0.4)
            confidence += structured_score
        
        # CSS data provides medium confidence
        if css_data:
            css_score = min(len(css_data) * 0.1, 0.3)
            confidence += css_score
        
        # Final data completeness
        if final_data:
            completeness_score = min(len(final_data) * 0.05, 0.2)
            confidence += completeness_score
        
        # Hybrid approach bonus
        if structured_data and css_data:
            confidence += 0.1  # Multiple source validation
        
        return min(confidence, 1.0)
    
    def _get_data_source_breakdown(self, structured_data: Dict[str, Any], css_data: Dict[str, Any]) -> Dict[str, int]:
        """Get breakdown of data sources for metadata"""
        return {
            "structured_fields": len(structured_data),
            "css_fields": len(css_data),
            "total_sources": (1 if structured_data else 0) + (1 if css_data else 0)
        }
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Estimate confidence for hybrid extraction"""
        confidence = 0.5  # Base confidence for hybrid approach
        
        # Check for structured data presence
        if 'application/ld+json' in html_content:
            confidence += 0.2
        if 'itemtype' in html_content:
            confidence += 0.1
        if 'typeof' in html_content:
            confidence += 0.1
        
        # Purpose-specific adjustments
        if purpose in ["product_data", "company_info", "news_content"]:
            confidence += 0.1  # These purposes work well with structured data
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Hybrid strategy supports most purposes"""
        supported_purposes = [
            "product_data", "company_info", "news_content",
            "contact_discovery", "business_listings", "general_data"
        ]
        return purpose in supported_purposes

class SmartHybridStrategy(BaseExtractionStrategy):
    """
    Intelligent hybrid that dynamically chooses the best combination of CSS and LLM
    
    Examples:
    - Analyze page structure to determine optimal extraction approach
    - Use CSS for structured sections, LLM for complex content
    - Automatically adapt strategy based on content type
    """
    
    def __init__(self, ollama_client, **kwargs):
        super().__init__(strategy_type=StrategyType.HYBRID, **kwargs)
        self.ollama_client = ollama_client
        
        # Initialize component strategies
        self.css_strategies = {
            "directory": DirectoryCSSStrategy(),
            "ecommerce": EcommerceCSSStrategy(),
            "news": NewsCSSStrategy()
        }
        self.llm_strategy = IntelligentLLMStrategy(ollama_client)
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Phase 1: Analyze content to determine optimal strategy mix
            strategy_plan = await self._analyze_and_plan_extraction(url, html_content, purpose)
            
            # Phase 2: Execute planned extraction
            extraction_results = await self._execute_strategy_plan(url, html_content, purpose, strategy_plan, context)
            
            # Phase 3: Merge and validate results
            final_data = self._merge_strategy_results(extraction_results, purpose)
            
            confidence = self._calculate_smart_hybrid_confidence(extraction_results, strategy_plan)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(final_data),
                extracted_data=final_data,
                confidence_score=confidence,
                strategy_used="SmartHybridStrategy",
                execution_time=execution_time,
                metadata={
                    "strategy_plan": strategy_plan,
                    "strategies_used": list(extraction_results.keys()),
                    "plan_confidence": strategy_plan.get("confidence", 0.5)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="SmartHybridStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _analyze_and_plan_extraction(self, url: str, html_content: str, purpose: str) -> Dict[str, Any]:
        """Analyze content and create extraction strategy plan"""
        
        analysis_prompt = f"""
Analyze this webpage and create an optimal extraction strategy plan.

URL: {url}
Purpose: {purpose}

Content Analysis (first 3000 chars):
{html_content[:3000]}

Determine:
1. Content structure type (directory, e-commerce, news, corporate, etc.)
2. Best extraction approach for each section
3. Whether to use CSS selectors, LLM extraction, or both
4. Confidence in recommended approach

Return JSON plan:
{{
    "content_type": "directory|ecommerce|news|corporate|social|other",
    "complexity": "low|medium|high",
    "recommended_strategies": {{
        "primary": "css|llm|hybrid",
        "secondary": "css|llm|none",
        "css_areas": ["area1", "area2"],
        "llm_areas": ["area1", "area2"]
    }},
    "confidence": 0.8,
    "reasoning": "explanation of strategy choice"
}}
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=analysis_prompt,
                format="json",
                temperature=0.2
            )
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Strategy planning failed: {e}")
            # Return default plan
            return {
                "content_type": "corporate",
                "complexity": "medium",
                "recommended_strategies": {
                    "primary": "hybrid",
                    "secondary": "llm",
                    "css_areas": ["contact", "basic_info"],
                    "llm_areas": ["content", "complex_info"]
                },
                "confidence": 0.5,
                "reasoning": "Default hybrid approach due to analysis failure"
            }
    
    async def _execute_strategy_plan(self, url: str, html_content: str, purpose: str, 
                                   strategy_plan: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the planned extraction strategies"""
        
        results = {}
        recommended = strategy_plan.get("recommended_strategies", {})
        content_type = strategy_plan.get("content_type", "corporate")
        
        # Execute primary strategy
        primary_strategy = recommended.get("primary", "hybrid")
        
        if primary_strategy == "css" or primary_strategy == "hybrid":
            # Execute appropriate CSS strategy
            css_result = await self._execute_css_strategy(url, html_content, purpose, content_type)
            if css_result.success:
                results["css"] = css_result.extracted_data
        
        if primary_strategy == "llm" or primary_strategy == "hybrid":
            # Execute LLM strategy
            llm_result = await self.llm_strategy.extract(url, html_content, purpose, context)
            if llm_result.success:
                results["llm"] = llm_result.extracted_data
        
        # Execute secondary strategy if primary didn't provide enough data
        if len(results) == 0 or self._needs_secondary_strategy(results, purpose):
            secondary_strategy = recommended.get("secondary", "none")
            
            if secondary_strategy == "css" and "css" not in results:
                css_result = await self._execute_css_strategy(url, html_content, purpose, content_type)
                if css_result.success:
                    results["css_secondary"] = css_result.extracted_data
            
            elif secondary_strategy == "llm" and "llm" not in results:
                llm_result = await self.llm_strategy.extract(url, html_content, purpose, context)
                if llm_result.success:
                    results["llm_secondary"] = llm_result.extracted_data
        
        return results
    
    async def _execute_css_strategy(self, url: str, html_content: str, purpose: str, content_type: str) -> StrategyResult:
        """Execute appropriate CSS strategy based on content type"""
        
        # Select CSS strategy based on content type
        if content_type == "directory" and "directory" in self.css_strategies:
            strategy = self.css_strategies["directory"]
        elif content_type == "ecommerce" and "ecommerce" in self.css_strategies:
            strategy = self.css_strategies["ecommerce"]
        elif content_type == "news" and "news" in self.css_strategies:
            strategy = self.css_strategies["news"]
        else:
            # Default to directory strategy for general business content
            strategy = self.css_strategies["directory"]
        
        return await strategy.extract(url, html_content, purpose)
    
    def _needs_secondary_strategy(self, results: Dict[str, Any], purpose: str) -> bool:
        """Determine if secondary strategy is needed"""
        
        # Check if we have sufficient data for the purpose
        min_fields = {
            "company_info": 3,
            "contact_discovery": 2,
            "product_data": 2,
            "news_content": 2
        }
        
        required_fields = min_fields.get(purpose, 2)
        
        for strategy_result in results.values():
            if isinstance(strategy_result, dict) and len(strategy_result) >= required_fields:
                return False  # We have sufficient data
        
        return True  # Need more data
    
    def _merge_strategy_results(self, results: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Merge results from multiple strategies"""
        
        merged = {}
        
        # Priority order: CSS (most reliable) -> LLM (most comprehensive)
        strategy_priority = ["css", "llm", "css_secondary", "llm_secondary"]
        
        for strategy in strategy_priority:
            if strategy in results:
                data = results[strategy]
                if isinstance(data, dict):
                    # Merge data, giving priority to existing values
                    for key, value in data.items():
                        if key not in merged and value and str(value).strip():
                            merged[key] = value
        
        return merged
    
    def _calculate_smart_hybrid_confidence(self, results: Dict[str, Any], strategy_plan: Dict[str, Any]) -> float:
        """Calculate confidence based on strategy plan execution"""
        
        base_confidence = strategy_plan.get("confidence", 0.5)
        
        # Execution bonus
        if len(results) > 1:
            base_confidence += 0.15  # Multiple strategies provide validation
        elif len(results) == 1:
            base_confidence += 0.05
        
        # Data quality bonus
        total_fields = sum(len(data) if isinstance(data, dict) else 0 for data in results.values())
        if total_fields > 5:
            base_confidence += 0.1
        elif total_fields > 3:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Smart hybrid has high confidence due to adaptive approach"""
        return 0.8  # High confidence due to intelligent adaptation
    
    def supports_purpose(self, purpose: str) -> bool:
        """Smart hybrid supports all purposes"""
        return True

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
                    "data_fields": len(result.extracted_data) if result.extracted_data else 0
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
                    "error": str(e)
                })
                continue
        
        # Update metadata
        if final_result:
            final_result.execution_time = time.time() - start_time
            final_result.strategy_used = "FallbackStrategy"
            final_result.metadata.update({
                "attempts": attempts,
                "successful_strategy": attempts[-1]["strategy"] if attempts else "none",
                "fallback_depth": len(attempts) - 1
            })
        else:
            final_result = StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="FallbackStrategy",
                execution_time=time.time() - start_time,
                metadata={"attempts": attempts, "all_strategies_failed": True},
                error="All fallback strategies failed"
            )
        
        return final_result
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Fallback strategy confidence is based on constituent strategies"""
        if not self.strategies:
            return 0.0
        
        # Average confidence of all strategies
        confidences = [strategy.get_confidence_score(url, html_content, purpose) 
                      for strategy in self.strategies]
        return sum(confidences) / len(confidences)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Supports purpose if any constituent strategy supports it"""
        return any(strategy.supports_purpose(purpose) for strategy in self.strategies)

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
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        # Get historical performance for this URL pattern
        url_pattern = self._get_url_pattern(url)
        historical_performance = await self._get_historical_performance(url_pattern, purpose)
        
        # Adapt strategy plan based on historical data
        strategy_plan = await self._analyze_and_plan_extraction(url, html_content, purpose)
        if historical_performance:
            strategy_plan = self._adapt_strategy_plan(strategy_plan, historical_performance)
        
        # Execute with adapted plan
        result = await self._execute_strategy_plan(url, html_content, purpose, strategy_plan, context)
        final_data = self._merge_strategy_results(result, purpose)
        
        # Create final result
        final_result = StrategyResult(
            success=bool(final_data),
            extracted_data=final_data,
            confidence_score=self._calculate_smart_hybrid_confidence(result, strategy_plan),
            strategy_used="AdaptiveHybridStrategy",
            execution_time=0,  # Will be set by parent
            metadata={
                "adapted_plan": strategy_plan,
                "historical_data_used": bool(historical_performance)
            }
        )
        
        # Learn from this execution
        await self._learn_from_execution(url, purpose, final_result, strategy_plan)
        
        return final_result
    
    def _get_url_pattern(self, url: str) -> str:
        """Extract pattern from URL for learning purposes"""
        from urllib.parse import urlparse
        
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
    
    async def _get_historical_performance(self, url_pattern: str, purpose: str) -> Optional[Dict[str, Any]]:
        """Get historical performance data for this pattern"""
        
        if not self.chromadb_manager:
            return None
        
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
            self.logger.warning(f"Failed to get historical performance: {e}")
        
        return None
    
    def _aggregate_performance_data(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate historical performance data"""
        
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
        
        if best_historical != "hybrid":
            # Override primary strategy if we have strong historical evidence
            if historical_data.get("sample_size", 0) >= 3:  # Minimum sample size
                adapted_plan["recommended_strategies"]["primary"] = best_historical
                adapted_plan["reasoning"] += f" (Adapted based on historical {best_historical} success)"
        
        # Boost confidence if historical data is positive
        historical_confidence = historical_data.get("avg_confidence", 0.5)
        if historical_confidence > 0.7:
            adapted_plan["confidence"] = min(adapted_plan["confidence"] + 0.1, 1.0)
        
        return adapted_plan
    
    async def _learn_from_execution(self, url: str, purpose: str, result: StrategyResult, strategy_plan: Dict[str, Any]):
        """Learn from execution results for future improvement"""
        
        if not self.chromadb_manager:
            return
        
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
            self.logger.warning(f"Failed to store learning data: {e}")
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Adaptive strategy has highest confidence due to learning"""
        base_confidence = super().get_confidence_score(url, html_content, purpose)
        return min(base_confidence + 0.1, 1.0)  # Learning bonus
