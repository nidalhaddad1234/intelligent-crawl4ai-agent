#!/usr/bin/env python3
"""
XPath Extraction Strategy
XPath-based structured data extraction
"""

import time
from typing import Dict, Any, List, Optional
from lxml import html, etree

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

class JsonXPathExtractionStrategy(BaseExtractionStrategy):
    """
    XPath-based structured data extraction
    Matches Crawl4AI's JsonXPathExtractionStrategy functionality
    """
    
    def __init__(self, schema: Dict[str, Any], **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        self.schema = schema
        
        # Validate schema
        if not isinstance(schema, dict) or 'name' not in schema:
            raise ValueError("Schema must be a dictionary with 'name' field")
        
        self.base_xpath = schema.get('baseSelector', '//body')
        self.fields = schema.get('fields', [])
        
        # Validate fields
        for field in self.fields:
            if not isinstance(field, dict) or 'name' not in field:
                raise ValueError("Each field must be a dictionary with 'name' field")
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Parse HTML with lxml
            tree = html.fromstring(html_content)
            
            extracted_data = []
            
            # Find base elements using XPath
            base_elements = tree.xpath(self.base_xpath)
            
            if not base_elements:
                # Try alternative approach - extract from entire document
                base_elements = [tree]
            
            for element in base_elements:
                item_data = {}
                
                for field in self.fields:
                    field_name = field.get('name')
                    field_xpath = field.get('selector', field.get('xpath'))
                    field_type = field.get('type', 'text')
                    attribute = field.get('attribute')
                    
                    if not field_xpath:
                        continue
                    
                    try:
                        # Execute XPath query
                        field_elements = element.xpath(field_xpath)
                        
                        if field_elements:
                            if field_type == 'attribute' and attribute:
                                value = field_elements[0].get(attribute, '')
                            elif field_type == 'html':
                                value = etree.tostring(field_elements[0], encoding='unicode')
                            else:  # text
                                value = field_elements[0].text_content().strip()
                            
                            if value:
                                item_data[field_name] = value
                                
                    except Exception as e:
                        self.logger.warning(f"XPath extraction failed for field '{field_name}': {e}")
                
                if item_data:
                    extracted_data.append(item_data)
            
            # Format result based on schema structure
            result_data = {}
            if extracted_data:
                if len(extracted_data) == 1:
                    result_data = extracted_data[0]
                else:
                    result_data[self.schema['name'].lower().replace(' ', '_')] = extracted_data
            
            confidence = self._calculate_confidence(result_data, [f['name'] for f in self.fields])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(result_data),
                extracted_data=result_data,
                confidence_score=confidence,
                strategy_used="JsonXPathExtractionStrategy",
                execution_time=execution_time,
                metadata={
                    "base_xpath": self.base_xpath,
                    "fields_extracted": len(result_data),
                    "items_found": len(extracted_data),
                    "schema_name": self.schema['name']
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="JsonXPathExtractionStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _calculate_confidence(self, result_data: Dict[str, Any], expected_fields: List[str]) -> float:
        """Calculate confidence based on field completeness"""
        
        if not result_data:
            return 0.0
        
        if not expected_fields:
            return 0.5
        
        # Count how many expected fields were extracted
        if isinstance(result_data, dict):
            # Single item result
            extracted_fields = list(result_data.keys())
            field_coverage = len(extracted_fields) / len(expected_fields)
        else:
            # Multiple items result - use average coverage
            field_coverage = 0.5  # Default for multi-item results
        
        # Base confidence from field coverage
        confidence = 0.3 + (field_coverage * 0.6)
        
        # Bonus for rich data
        if isinstance(result_data, dict):
            data_richness = sum(1 for v in result_data.values() if v and len(str(v)) > 10)
            confidence += min(data_richness * 0.05, 0.1)
        
        return min(confidence, 1.0)
    
    def validate_xpath(self, xpath: str, html_content: str) -> bool:
        """Validate an XPath expression against HTML content"""
        try:
            tree = html.fromstring(html_content)
            elements = tree.xpath(xpath)
            return len(elements) > 0
        except Exception as e:
            self.logger.warning(f"XPath validation failed: {e}")
            return False
    
    def test_xpath(self, xpath: str, html_content: str) -> List[str]:
        """Test an XPath expression and return found text content"""
        try:
            tree = html.fromstring(html_content)
            elements = tree.xpath(xpath)
            return [elem.text_content().strip() for elem in elements if hasattr(elem, 'text_content')]
        except Exception as e:
            self.logger.warning(f"XPath test failed: {e}")
            return []
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get information about the current schema"""
        return {
            "name": self.schema.get('name'),
            "base_selector": self.base_xpath,
            "field_count": len(self.fields),
            "fields": [
                {
                    "name": field.get('name'),
                    "xpath": field.get('selector', field.get('xpath')),
                    "type": field.get('type', 'text'),
                    "attribute": field.get('attribute')
                }
                for field in self.fields
            ]
        }
    
    def update_schema(self, schema: Dict[str, Any]):
        """Update the extraction schema"""
        if not isinstance(schema, dict) or 'name' not in schema:
            raise ValueError("Schema must be a dictionary with 'name' field")
        
        self.schema = schema
        self.base_xpath = schema.get('baseSelector', '//body')
        self.fields = schema.get('fields', [])
        
        # Validate fields
        for field in self.fields:
            if not isinstance(field, dict) or 'name' not in field:
                raise ValueError("Each field must be a dictionary with 'name' field")
    
    def add_field(self, name: str, xpath: str, field_type: str = 'text', attribute: str = None):
        """Add a new field to the schema"""
        field = {
            'name': name,
            'selector': xpath,
            'type': field_type
        }
        
        if attribute:
            field['attribute'] = attribute
        
        self.fields.append(field)
    
    def remove_field(self, name: str):
        """Remove a field from the schema"""
        self.fields = [field for field in self.fields if field.get('name') != name]
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """XPath strategy confidence based on content structure"""
        try:
            tree = html.fromstring(html_content)
            base_elements = tree.xpath(self.base_xpath)
            
            if base_elements:
                # Test a few field XPaths to see if they work
                working_fields = 0
                for field in self.fields[:3]:  # Test first 3 fields
                    field_xpath = field.get('selector', field.get('xpath'))
                    if field_xpath:
                        try:
                            field_elements = base_elements[0].xpath(field_xpath)
                            if field_elements:
                                working_fields += 1
                        except:
                            pass
                
                if working_fields > 0:
                    return 0.7 + (working_fields * 0.1)
                else:
                    return 0.4
            else:
                return 0.2
        except:
            return 0.1
    
    def supports_purpose(self, purpose: str) -> bool:
        """XPath strategy supports structured data extraction"""
        supported_purposes = [
            "product_data", "news_content", "company_info",
            "structured_extraction", "xml_data", "html_parsing",
            "table_extraction", "list_extraction"
        ]
        return purpose in supported_purposes
