#!/usr/bin/env python3
"""
JSON-CSS Hybrid Strategy
Combines JSON-LD structured data extraction with CSS fallbacks
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

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
