"""
Dynamic Extraction Rule Generation
Automatically generate extraction rules from detected patterns
"""

import logging
import re
from typing import List, Dict, Any, Optional
from collections import Counter

from .models import (
    DataType, ExtractionRule, ContentPattern, DetectedSchema, SchemaElement
)

logger = logging.getLogger(__name__)


class RuleGenerator:
    """Automatically generate extraction rules from detected patterns"""
    
    def __init__(self):
        self.selector_priority = {
            'id': 10,
            'class': 8,
            'tag': 6,
            'attribute': 7,
            'xpath': 5
        }
        self.extraction_methods = self._initialize_extraction_methods()
        self.validation_patterns = self._initialize_validation_patterns()
    
    def _initialize_extraction_methods(self) -> Dict[DataType, List[str]]:
        """Initialize extraction methods for different data types"""
        return {
            DataType.TEXT: ['text()', 'innerText', 'textContent'],
            DataType.PRICE: ['text()', 'data-price', '@data-value'],
            DataType.EMAIL: ['text()', '@href', 'data-email'],
            DataType.PHONE: ['text()', '@href', 'data-phone'],
            DataType.URL: ['@href', '@src', 'data-url'],
            DataType.IMAGE: ['@src', '@data-src', '@data-lazy-src'],
            DataType.DATE: ['text()', '@datetime', 'data-date'],
            DataType.RATING: ['text()', '@data-rating', 'data-score'],
            DataType.NAME: ['text()', '@alt', '@title'],
            DataType.ADDRESS: ['text()', 'data-address'],
            DataType.NUMBER: ['text()', '@data-value', 'data-number'],
            DataType.CURRENCY: ['text()', 'data-currency'],
            DataType.PERCENTAGE: ['text()', 'data-percentage']
        }
    
    def _initialize_validation_patterns(self) -> Dict[DataType, List[str]]:
        """Initialize validation patterns for different data types"""
        return {
            DataType.PRICE: [
                r'^\$?[\d,]+\.?\d*$',
                r'^€?[\d,]+\.?\d*$',
                r'^£?[\d,]+\.?\d*$'
            ],
            DataType.EMAIL: [
                r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
            ],
            DataType.PHONE: [
                r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',
                r'^\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}$'
            ],
            DataType.URL: [
                r'^https?://[^\s<>"\']+$',
                r'^www\.[^\s<>"\']+$'
            ],
            DataType.DATE: [
                r'^\d{1,2}[/-]\d{1,2}[/-]\d{2,4}$',
                r'^\d{4}[/-]\d{1,2}[/-]\d{1,2}$'
            ],
            DataType.RATING: [
                r'^\d+\.?\d*/5$',
                r'^\d+\.?\d*\s*stars?$'
            ],
            DataType.PERCENTAGE: [
                r'^\d+\.?\d*%$'
            ]
        }
    
    async def generate_css_selectors(self, pattern: ContentPattern) -> List[str]:
        """Generate CSS selectors from content patterns"""
        try:
            selectors = []
            
            # Primary selector from pattern
            if pattern.css_selector:
                selectors.append(pattern.css_selector)
            
            # Generate selectors from sample elements
            if pattern.sample_elements:
                element_selectors = self._extract_selectors_from_elements(pattern.sample_elements)
                selectors.extend(element_selectors)
            
            # Generate fallback selectors
            fallback_selectors = self._generate_fallback_selectors(pattern)
            selectors.extend(fallback_selectors)
            
            # Optimize and deduplicate
            optimized_selectors = await self.optimize_selectors(selectors)
            
            logger.info(f"Generated {len(optimized_selectors)} CSS selectors for pattern {pattern.id}")
            return optimized_selectors
            
        except Exception as e:
            logger.error(f"CSS selector generation failed: {e}")
            return []
    
    async def generate_xpath_expressions(self, pattern: ContentPattern) -> List[str]:
        """Generate XPath expressions from content patterns"""
        try:
            xpaths = []
            
            # Primary XPath from pattern
            if pattern.xpath:
                xpaths.append(pattern.xpath)
            
            # Generate XPaths from sample elements
            if pattern.sample_elements:
                for element in pattern.sample_elements:
                    if element.xpath:
                        xpaths.append(element.xpath)
            
            # Generate semantic XPaths
            semantic_xpaths = self._generate_semantic_xpaths(pattern)
            xpaths.extend(semantic_xpaths)
            
            # Remove duplicates
            unique_xpaths = list(dict.fromkeys(xpaths))
            
            logger.info(f"Generated {len(unique_xpaths)} XPath expressions for pattern {pattern.id}")
            return unique_xpaths[:5]  # Return top 5
            
        except Exception as e:
            logger.error(f"XPath generation failed: {e}")
            return []
    
    async def generate_extraction_pipeline(self, schemas: List[DetectedSchema]) -> Dict[str, Any]:
        """Generate complete extraction pipeline from detected schemas"""
        try:
            pipeline = {
                'extraction_rules': [],
                'data_structure': {},
                'validation_rules': [],
                'post_processing': [],
                'confidence': 0.0
            }
            
            if not schemas:
                return pipeline
            
            # Generate rules for each schema
            all_rules = []
            for schema in schemas:
                schema_rules = await self._generate_schema_rules(schema)
                all_rules.extend(schema_rules)
            
            pipeline['extraction_rules'] = all_rules
            
            # Define data structure
            pipeline['data_structure'] = self._define_data_structure(schemas)
            
            # Generate validation rules
            pipeline['validation_rules'] = self._generate_pipeline_validation(schemas)
            
            # Define post-processing steps
            pipeline['post_processing'] = self._generate_post_processing_steps(schemas)
            
            # Calculate pipeline confidence
            pipeline['confidence'] = self._calculate_pipeline_confidence(schemas, all_rules)
            
            logger.info(f"Generated extraction pipeline with {len(all_rules)} rules")
            return pipeline
            
        except Exception as e:
            logger.error(f"Pipeline generation failed: {e}")
            return {
                'extraction_rules': [],
                'data_structure': {},
                'validation_rules': [],
                'post_processing': [],
                'confidence': 0.0
            }
    
    async def optimize_selectors(self, selectors: List[str]) -> List[str]:
        """Optimize and rank selectors by reliability and specificity"""
        try:
            if not selectors:
                return []
            
            # Score each selector
            scored_selectors = []
            for selector in selectors:
                score = self._calculate_selector_score(selector)
                scored_selectors.append((selector, score))
            
            # Sort by score (highest first)
            scored_selectors.sort(key=lambda x: x[1], reverse=True)
            
            # Remove duplicates while preserving order
            seen = set()
            optimized = []
            for selector, score in scored_selectors:
                if selector not in seen:
                    seen.add(selector)
                    optimized.append(selector)
            
            return optimized[:5]  # Return top 5 selectors
            
        except Exception as e:
            logger.error(f"Selector optimization failed: {e}")
            return selectors[:5]  # Return first 5 if optimization fails
    
    def _extract_selectors_from_elements(self, elements: List[SchemaElement]) -> List[str]:
        """Extract CSS selectors from schema elements"""
        selectors = []
        
        # Collect existing selectors
        for element in elements:
            if element.css_selector:
                selectors.append(element.css_selector)
        
        # Generate selectors based on common patterns
        if len(elements) > 1:
            # Find common classes
            all_classes = []
            for element in elements:
                all_classes.extend(element.css_classes)
            
            if all_classes:
                class_counts = Counter(all_classes)
                # Use classes that appear in at least 50% of elements
                threshold = len(elements) * 0.5
                common_classes = [cls for cls, count in class_counts.items() 
                                if count >= threshold]
                
                for cls in common_classes:
                    selectors.append(f".{cls}")
            
            # Find common tags
            tag_counts = Counter(element.tag_name for element in elements)
            common_tags = [tag for tag, count in tag_counts.items() 
                          if count >= len(elements) * 0.5]
            
            selectors.extend(common_tags)
            
            # Generate combined selectors
            for tag in common_tags:
                for cls in common_classes:
                    selectors.append(f"{tag}.{cls}")
        
        return selectors
    
    def _generate_fallback_selectors(self, pattern: ContentPattern) -> List[str]:
        """Generate fallback selectors for robustness"""
        fallback_selectors = []
        
        # Attribute-based selectors
        if pattern.sample_elements:
            for element in pattern.sample_elements[:2]:  # Use first 2 elements
                # Data attributes
                for attr, value in element.attributes.items():
                    if attr.startswith('data-'):
                        fallback_selectors.append(f"[{attr}]")
                        if len(value) < 50:  # Avoid very long attribute values
                            fallback_selectors.append(f"[{attr}='{value}']")
                
                # ID-based selectors
                if element.element_id:
                    fallback_selectors.append(f"#{element.element_id}")
        
        # Content-based selectors (for specific text)
        if pattern.pattern_type.value in ['contact_info', 'pricing_data']:
            # Generate selectors based on text content patterns
            fallback_selectors.extend([
                "[class*='contact']",
                "[class*='price']",
                "[class*='email']",
                "[class*='phone']"
            ])
        
        return fallback_selectors
    
    def _generate_semantic_xpaths(self, pattern: ContentPattern) -> List[str]:
        """Generate semantic XPath expressions"""
        xpaths = []
        
        # Pattern-specific XPaths
        if pattern.pattern_type.value == 'product_listing':
            xpaths.extend([
                "//div[contains(@class, 'product')]",
                "//article[contains(@class, 'item')]",
                "//*[contains(@class, 'price')]/ancestor::*[1]"
            ])
        
        elif pattern.pattern_type.value == 'article_content':
            xpaths.extend([
                "//article",
                "//main",
                "//*[contains(@class, 'content')]"
            ])
        
        elif pattern.pattern_type.value == 'contact_info':
            xpaths.extend([
                "//a[starts-with(@href, 'mailto:')]",
                "//a[starts-with(@href, 'tel:')]",
                "//*[contains(@class, 'contact')]"
            ])
        
        elif pattern.pattern_type.value == 'pricing_data':
            xpaths.extend([
                "//*[contains(@class, 'price')]",
                "//*[contains(@class, 'plan')]",
                "//*[contains(text(), '$')]"
            ])
        
        # Generic structural XPaths
        if pattern.sample_elements:
            first_element = pattern.sample_elements[0]
            if first_element.tag_name:
                xpaths.append(f"//{first_element.tag_name}")
                
                if first_element.css_classes:
                    for cls in first_element.css_classes[:2]:  # Use first 2 classes
                        xpaths.append(f"//{first_element.tag_name}[contains(@class, '{cls}')]")
        
        return xpaths
    
    async def _generate_schema_rules(self, schema: DetectedSchema) -> List[ExtractionRule]:
        """Generate extraction rules for a specific schema"""
        rules = []
        
        try:
            # Generate rule for the schema as a whole
            main_rule = ExtractionRule(
                target_selector=schema.selector_path,
                data_type=DataType.TEXT,  # Default, will be refined
                extraction_method="text()",
                confidence=schema.confidence
            )
            
            # Add validation rules based on schema type
            if schema.schema_type.value == 'table':
                main_rule.validation_rules = ['not_empty', 'is_table_structure']
                main_rule.extraction_method = "table_extraction"
            
            elif schema.schema_type.value == 'form':
                main_rule.validation_rules = ['not_empty', 'is_form_structure']
                main_rule.extraction_method = "form_extraction"
            
            elif schema.schema_type.value == 'product':
                main_rule.validation_rules = ['not_empty', 'has_price_or_name']
                main_rule.data_type = DataType.TEXT
            
            # Add fallback selectors
            main_rule.fallback_selectors = [schema.xpath_path] if schema.xpath_path else []
            
            rules.append(main_rule)
            
            # Generate rules for individual elements
            for element in schema.elements[:5]:  # Limit to first 5 elements
                if element.css_selector:
                    element_rule = ExtractionRule(
                        target_selector=element.css_selector,
                        data_type=element.data_type,
                        extraction_method=self._get_extraction_method(element.data_type),
                        confidence=element.confidence,
                        validation_rules=self._get_validation_rules(element.data_type)
                    )
                    
                    # Add transformation rules
                    element_rule.transformation_rules = self._get_transformation_rules(element.data_type)
                    
                    rules.append(element_rule)
            
        except Exception as e:
            logger.warning(f"Failed to generate rules for schema {schema.id}: {e}")
        
        return rules
    
    def _define_data_structure(self, schemas: List[DetectedSchema]) -> Dict[str, Any]:
        """Define the expected data structure from schemas"""
        structure = {
            'type': 'object',
            'properties': {},
            'relationships': []
        }
        
        for schema in schemas:
            schema_name = f"{schema.schema_type.value}_{schema.id[:8]}"
            
            if schema.schema_type.value == 'table':
                structure['properties'][schema_name] = {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': self._extract_table_properties(schema)
                    }
                }
            
            elif schema.schema_type.value == 'list':
                structure['properties'][schema_name] = {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': self._extract_list_properties(schema)
                    }
                }
            
            elif schema.schema_type.value in ['product', 'article', 'contact']:
                structure['properties'][schema_name] = {
                    'type': 'object',
                    'properties': self._extract_object_properties(schema)
                }
            
            else:
                structure['properties'][schema_name] = {
                    'type': 'string',
                    'description': f"Content from {schema.schema_type.value}"
                }
        
        return structure
    
    def _generate_pipeline_validation(self, schemas: List[DetectedSchema]) -> List[str]:
        """Generate validation rules for the entire pipeline"""
        validation_rules = [
            'validate_required_schemas',
            'check_data_completeness',
            'validate_data_types'
        ]
        
        # Schema-specific validations
        schema_types = [schema.schema_type.value for schema in schemas]
        
        if 'table' in schema_types:
            validation_rules.append('validate_table_structure')
        
        if 'product' in schema_types:
            validation_rules.extend(['validate_product_data', 'check_price_format'])
        
        if 'contact' in schema_types:
            validation_rules.extend(['validate_contact_info', 'verify_email_format'])
        
        return validation_rules
    
    def _generate_post_processing_steps(self, schemas: List[DetectedSchema]) -> List[str]:
        """Generate post-processing steps"""
        steps = [
            'clean_whitespace',
            'remove_duplicates',
            'normalize_data_types'
        ]
        
        # Schema-specific post-processing
        schema_types = [schema.schema_type.value for schema in schemas]
        
        if 'product' in schema_types:
            steps.extend([
                'normalize_prices',
                'standardize_product_names'
            ])
        
        if 'table' in schema_types:
            steps.extend([
                'convert_table_to_records',
                'handle_merged_cells'
            ])
        
        if 'contact' in schema_types:
            steps.extend([
                'format_phone_numbers',
                'normalize_email_addresses'
            ])
        
        return steps
    
    def _calculate_pipeline_confidence(self, schemas: List[DetectedSchema], rules: List[ExtractionRule]) -> float:
        """Calculate overall confidence for the extraction pipeline"""
        if not schemas or not rules:
            return 0.0
        
        # Average schema confidence
        schema_confidence = sum(schema.confidence for schema in schemas) / len(schemas)
        
        # Average rule confidence
        rule_confidence = sum(rule.confidence for rule in rules) / len(rules)
        
        # Adjust based on schema diversity
        schema_types = set(schema.schema_type.value for schema in schemas)
        diversity_bonus = min(len(schema_types) * 0.1, 0.2)
        
        # Adjust based on rule completeness
        completeness_bonus = min(len(rules) * 0.02, 0.1)
        
        total_confidence = (schema_confidence + rule_confidence) / 2 + diversity_bonus + completeness_bonus
        
        return min(total_confidence, 1.0)
    
    def _calculate_selector_score(self, selector: str) -> float:
        """Calculate reliability score for a CSS selector"""
        score = 0.0
        
        # ID selectors are most reliable
        if selector.startswith('#'):
            score += 10
        
        # Class selectors are reliable
        elif '.' in selector:
            score += 8
            # Multiple classes are more specific
            class_count = selector.count('.')
            score += min(class_count * 0.5, 2)
        
        # Attribute selectors are moderately reliable
        elif '[' in selector and ']' in selector:
            score += 7
            # Data attributes are preferred
            if 'data-' in selector:
                score += 1
        
        # Tag selectors are less reliable but still useful
        elif re.match(r'^[a-zA-Z]+$', selector):
            score += 6
        
        # Combined selectors can be more specific
        if ' ' in selector or '>' in selector:
            score += 1
        
        # Penalize overly complex selectors
        if len(selector) > 100:
            score -= 2
        
        # Penalize selectors with numbers (might be dynamic)
        if re.search(r'\d+', selector):
            score -= 1
        
        return max(score, 0)
    
    def _get_extraction_method(self, data_type: DataType) -> str:
        """Get the best extraction method for a data type"""
        methods = self.extraction_methods.get(data_type, ['text()'])
        return methods[0]  # Return the primary method
    
    def _get_validation_rules(self, data_type: DataType) -> List[str]:
        """Get validation rules for a data type"""
        base_rules = ['not_empty']
        
        if data_type == DataType.PRICE:
            base_rules.extend(['is_numeric', 'positive_value'])
        elif data_type == DataType.EMAIL:
            base_rules.append('valid_email_format')
        elif data_type == DataType.PHONE:
            base_rules.append('valid_phone_format')
        elif data_type == DataType.URL:
            base_rules.append('valid_url_format')
        elif data_type == DataType.DATE:
            base_rules.append('valid_date_format')
        
        return base_rules
    
    def _get_transformation_rules(self, data_type: DataType) -> List[str]:
        """Get transformation rules for a data type"""
        rules = ['trim_whitespace']
        
        if data_type == DataType.PRICE:
            rules.extend(['remove_currency_symbols', 'convert_to_float'])
        elif data_type == DataType.PHONE:
            rules.append('normalize_phone_format')
        elif data_type == DataType.DATE:
            rules.append('parse_date_format')
        elif data_type == DataType.TEXT:
            rules.append('normalize_unicode')
        
        return rules
    
    def _extract_table_properties(self, schema: DetectedSchema) -> Dict[str, Any]:
        """Extract properties from a table schema"""
        properties = {}
        
        # Extract column information from table attributes
        if 'column_count' in schema.attributes:
            for i in range(schema.attributes['column_count']):
                properties[f'column_{i}'] = {'type': 'string'}
        
        # If we have sample elements, use their data types
        for i, element in enumerate(schema.elements[:10]):  # Max 10 columns
            col_name = f'column_{i}' if not element.text_content else element.text_content.lower().replace(' ', '_')
            properties[col_name] = {
                'type': self._data_type_to_json_type(element.data_type),
                'description': element.text_content
            }
        
        return properties
    
    def _extract_list_properties(self, schema: DetectedSchema) -> Dict[str, Any]:
        """Extract properties from a list schema"""
        properties = {}
        
        # Analyze list items to determine structure
        if schema.elements:
            # Find common properties across list items
            common_properties = {}
            for element in schema.elements:
                if element.data_type != DataType.TEXT:
                    prop_name = element.data_type.value
                    common_properties[prop_name] = {
                        'type': self._data_type_to_json_type(element.data_type)
                    }
            
            properties.update(common_properties)
        
        # Default list item structure
        if not properties:
            properties = {
                'text': {'type': 'string'},
                'link': {'type': 'string', 'format': 'uri'}
            }
        
        return properties
    
    def _extract_object_properties(self, schema: DetectedSchema) -> Dict[str, Any]:
        """Extract properties from an object schema"""
        properties = {}
        
        for element in schema.elements:
            prop_name = element.data_type.value
            if element.text_content and len(element.text_content) < 50:
                prop_name = element.text_content.lower().replace(' ', '_')
            
            properties[prop_name] = {
                'type': self._data_type_to_json_type(element.data_type),
                'selector': element.css_selector
            }
        
        return properties
    
    def _data_type_to_json_type(self, data_type: DataType) -> str:
        """Convert DataType to JSON schema type"""
        mapping = {
            DataType.TEXT: 'string',
            DataType.PRICE: 'number',
            DataType.NUMBER: 'number',
            DataType.BOOLEAN: 'boolean',
            DataType.DATE: 'string',
            DataType.EMAIL: 'string',
            DataType.PHONE: 'string',
            DataType.URL: 'string',
            DataType.IMAGE: 'string',
            DataType.ADDRESS: 'string',
            DataType.NAME: 'string',
            DataType.RATING: 'number',
            DataType.CURRENCY: 'string',
            DataType.PERCENTAGE: 'number'
        }
        
        return mapping.get(data_type, 'string')
