"""
AI-Powered Content Understanding
Use AI to understand content semantics and context
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urlparse

from .models import ContentType, DataType, SchemaElement

logger = logging.getLogger(__name__)


class Entity:
    """Represents an extracted entity"""
    def __init__(self, text: str, entity_type: str, confidence: float = 0.0, context: str = ""):
        self.text = text
        self.entity_type = entity_type
        self.confidence = confidence
        self.context = context


class Relationship:
    """Represents a relationship between data elements"""
    def __init__(self, source: str, target: str, relationship_type: str, confidence: float = 0.0):
        self.source = source
        self.target = target
        self.relationship_type = relationship_type
        self.confidence = confidence


class ContentClassification:
    """Content classification result"""
    def __init__(self, content_type: ContentType, confidence: float, reasoning: str = ""):
        self.content_type = content_type
        self.confidence = confidence
        self.reasoning = reasoning


class AIContentAnalyzer:
    """Use AI to understand content semantics and context"""
    
    def __init__(self):
        self.content_indicators = self._initialize_content_indicators()
        self.entity_patterns = self._initialize_entity_patterns()
        self.relationship_types = self._initialize_relationship_types()
    
    def _initialize_content_indicators(self) -> Dict[ContentType, Dict[str, Any]]:
        """Initialize indicators for content type classification"""
        return {
            ContentType.ECOMMERCE_PRODUCT: {
                'keywords': ['price', 'buy', 'add to cart', 'product', 'purchase', 'shipping', 'reviews', 'rating'],
                'selectors': ['.price', '.buy-button', '.add-to-cart', '.product-details', '.reviews'],
                'url_patterns': [r'/product/', r'/item/', r'/p/', r'product-id', r'sku'],
                'confidence_boost': 0.3
            },
            ContentType.ECOMMERCE_LISTING: {
                'keywords': ['products', 'catalog', 'category', 'filter', 'sort', 'results', 'items found'],
                'selectors': ['.product-list', '.catalog', '.grid', '.results', '.filters'],
                'url_patterns': [r'/category/', r'/shop/', r'/products/', r'/catalog/'],
                'confidence_boost': 0.25
            },
            ContentType.NEWS_ARTICLE: {
                'keywords': ['published', 'author', 'breaking', 'news', 'reporter', 'source', 'updated'],
                'selectors': ['.article', '.news-content', '.byline', '.publish-date'],
                'url_patterns': [r'/news/', r'/article/', r'/story/', r'\d{4}/\d{2}/\d{2}'],
                'confidence_boost': 0.2
            },
            ContentType.BLOG_POST: {
                'keywords': ['posted by', 'blog', 'comments', 'tags', 'categories', 'share'],
                'selectors': ['.blog-post', '.entry', '.post-content', '.comments'],
                'url_patterns': [r'/blog/', r'/post/', r'/entry/'],
                'confidence_boost': 0.2
            },
            ContentType.CONTACT_PAGE: {
                'keywords': ['contact us', 'get in touch', 'address', 'phone', 'email', 'location'],
                'selectors': ['.contact-form', '.address', '.phone', '.email'],
                'url_patterns': [r'/contact', r'/contact-us', r'/get-in-touch'],
                'confidence_boost': 0.3
            },
            ContentType.PRICING_PAGE: {
                'keywords': ['pricing', 'plans', 'packages', 'subscription', 'tiers', 'features'],
                'selectors': ['.pricing-table', '.plans', '.packages', '.tiers'],
                'url_patterns': [r'/pricing', r'/plans', r'/packages'],
                'confidence_boost': 0.25
            }
        }
    
    def _initialize_entity_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for entity extraction"""
        return {
            'price': [
                r'\$[\d,]+\.?\d*',
                r'€[\d,]+\.?\d*',
                r'£[\d,]+\.?\d*',
                r'[\d,]+\.?\d*\s*(USD|EUR|GBP|dollars?|euros?|pounds?)',
                r'Price:?\s*[\d,]+\.?\d*'
            ],
            'email': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            'phone': [
                r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
                r'\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'
            ],
            'date': [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}'
            ],
            'url': [
                r'https?://[^\s<>"\']+',
                r'www\.[^\s<>"\']+',
                r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s<>"\']+'
            ],
            'company': [
                r'\b[A-Z][a-z]+\s+(Inc|LLC|Corp|Corporation|Ltd|Limited|Co|Company)\b',
                r'\b[A-Z][a-z]+\s+&\s+[A-Z][a-z]+\b'
            ],
            'person': [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'  # Simple first+last name pattern
            ]
        }
    
    def _initialize_relationship_types(self) -> List[str]:
        """Initialize types of relationships to detect"""
        return [
            'product_to_price',
            'product_to_category',
            'article_to_author',
            'article_to_date',
            'contact_to_company',
            'price_to_currency',
            'item_to_description',
            'parent_to_child',
            'category_to_subcategory'
        ]
    
    async def classify_content_type(self, content: str, url: str = "", title: str = "") -> ContentClassification:
        """Classify the type of content on the page"""
        try:
            scores = {}
            content_lower = content.lower()
            url_lower = url.lower()
            title_lower = title.lower()
            
            # Score each content type
            for content_type, indicators in self.content_indicators.items():
                score = 0.0
                
                # Keyword matching
                keyword_matches = sum(1 for keyword in indicators['keywords'] 
                                    if keyword in content_lower)
                if keyword_matches > 0:
                    score += (keyword_matches / len(indicators['keywords'])) * 0.4
                
                # URL pattern matching
                url_matches = sum(1 for pattern in indicators['url_patterns'] 
                                if re.search(pattern, url_lower))
                if url_matches > 0:
                    score += (url_matches / len(indicators['url_patterns'])) * 0.3
                
                # Title matching
                title_keyword_matches = sum(1 for keyword in indicators['keywords'] 
                                          if keyword in title_lower)
                if title_keyword_matches > 0:
                    score += (title_keyword_matches / len(indicators['keywords'])) * 0.2
                
                # Structural indicators (simplified - would need HTML analysis)
                if any(selector.replace('.', '').replace('#', '') in content_lower 
                      for selector in indicators.get('selectors', [])):
                    score += 0.1
                
                scores[content_type] = score
            
            # Find best match
            if scores:
                best_type = max(scores.keys(), key=lambda k: scores[k])
                best_score = scores[best_type]
                
                if best_score > 0.3:  # Minimum confidence threshold
                    reasoning = f"Detected {best_type.value} with score {best_score:.2f}"
                    return ContentClassification(best_type, best_score, reasoning)
            
            # Default classification
            return ContentClassification(
                ContentType.DIRECTORY_LISTING, 
                0.5, 
                "Default classification - no strong indicators found"
            )
            
        except Exception as e:
            logger.error(f"Content classification failed: {e}")
            return ContentClassification(ContentType.DIRECTORY_LISTING, 0.3, f"Error: {str(e)}")
    
    async def extract_entities(self, content: str) -> List[Entity]:
        """Extract entities from content"""
        try:
            entities = []
            
            # Extract entities using regex patterns
            for entity_type, patterns in self.entity_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        entity_text = match.group(0).strip()
                        if len(entity_text) > 2:  # Filter out very short matches
                            # Calculate confidence based on pattern quality and context
                            confidence = self._calculate_entity_confidence(entity_text, entity_type, content)
                            
                            # Get surrounding context
                            start_pos = max(0, match.start() - 50)
                            end_pos = min(len(content), match.end() + 50)
                            context = content[start_pos:end_pos].strip()
                            
                            entities.append(Entity(
                                text=entity_text,
                                entity_type=entity_type,
                                confidence=confidence,
                                context=context
                            ))
            
            # Remove duplicates and low-confidence entities
            entities = self._deduplicate_entities(entities)
            entities = [e for e in entities if e.confidence > 0.5]
            
            logger.info(f"Extracted {len(entities)} entities")
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return []
    
    async def detect_data_relationships(self, schema_elements: List[SchemaElement]) -> List[Relationship]:
        """Detect relationships between data elements"""
        try:
            relationships = []
            
            # Analyze spatial and semantic relationships
            for i, elem1 in enumerate(schema_elements):
                for j, elem2 in enumerate(schema_elements[i+1:], i+1):
                    relationship = self._analyze_element_relationship(elem1, elem2)
                    if relationship:
                        relationships.append(relationship)
            
            # Filter relationships by confidence
            relationships = [r for r in relationships if r.confidence > 0.6]
            
            logger.info(f"Detected {len(relationships)} data relationships")
            return relationships
            
        except Exception as e:
            logger.error(f"Relationship detection failed: {e}")
            return []
    
    async def suggest_extraction_rules(self, pattern_elements: List[SchemaElement]) -> Dict[str, Any]:
        """Suggest optimal extraction rules based on AI analysis"""
        try:
            suggestions = {
                'primary_selectors': [],
                'fallback_selectors': [],
                'data_transformations': [],
                'validation_rules': [],
                'confidence': 0.0
            }
            
            if not pattern_elements:
                return suggestions
            
            # Analyze element patterns
            element_analysis = self._analyze_element_patterns(pattern_elements)
            
            # Generate primary selectors
            suggestions['primary_selectors'] = self._generate_primary_selectors(pattern_elements)
            
            # Generate fallback selectors
            suggestions['fallback_selectors'] = self._generate_fallback_selectors(pattern_elements)
            
            # Suggest data transformations
            suggestions['data_transformations'] = self._suggest_transformations(pattern_elements)
            
            # Generate validation rules
            suggestions['validation_rules'] = self._generate_validation_rules(pattern_elements)
            
            # Calculate overall confidence
            suggestions['confidence'] = self._calculate_suggestion_confidence(element_analysis)
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Rule suggestion failed: {e}")
            return {'primary_selectors': [], 'fallback_selectors': [], 
                   'data_transformations': [], 'validation_rules': [], 'confidence': 0.0}
    
    def _calculate_entity_confidence(self, entity_text: str, entity_type: str, context: str) -> float:
        """Calculate confidence score for an extracted entity"""
        confidence = 0.7  # Base confidence
        
        # Type-specific confidence adjustments
        if entity_type == 'price':
            # Higher confidence for prices with currency symbols
            if any(symbol in entity_text for symbol in ['$', '€', '£']):
                confidence += 0.2
            # Lower confidence for numbers that might not be prices
            if entity_text.isdigit() and len(entity_text) > 6:
                confidence -= 0.3
        
        elif entity_type == 'email':
            # Very high confidence for email pattern matches
            confidence = 0.95
        
        elif entity_type == 'phone':
            # Higher confidence for formatted phone numbers
            if any(char in entity_text for char in ['-', '(', ')', ' ']):
                confidence += 0.1
        
        elif entity_type == 'date':
            # Higher confidence for specific date formats
            if re.match(r'\d{4}-\d{2}-\d{2}', entity_text):
                confidence += 0.2
        
        # Context-based adjustments
        context_lower = context.lower()
        if entity_type in context_lower:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Remove duplicate entities"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # Create a key for deduplication
            key = (entity.text.lower(), entity.entity_type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
            else:
                # If we've seen this entity before, keep the one with higher confidence
                for i, existing in enumerate(unique_entities):
                    if (existing.text.lower(), existing.entity_type) == key:
                        if entity.confidence > existing.confidence:
                            unique_entities[i] = entity
                        break
        
        return unique_entities
    
    def _analyze_element_relationship(self, elem1: SchemaElement, elem2: SchemaElement) -> Optional[Relationship]:
        """Analyze potential relationship between two elements"""
        try:
            # Check for common relationship patterns
            
            # Product-Price relationship
            if (elem1.data_type == DataType.TEXT and elem2.data_type == DataType.PRICE) or \
               (elem1.data_type == DataType.NAME and elem2.data_type == DataType.PRICE):
                return Relationship(
                    source=elem1.css_selector,
                    target=elem2.css_selector,
                    relationship_type='product_to_price',
                    confidence=0.8
                )
            
            # Article-Author relationship
            if elem1.data_type == DataType.TEXT and elem2.data_type == DataType.NAME:
                # Check if they appear close together
                if abs(len(elem1.text_content) - len(elem2.text_content)) < 100:
                    return Relationship(
                        source=elem1.css_selector,
                        target=elem2.css_selector,
                        relationship_type='article_to_author',
                        confidence=0.7
                    )
            
            # Image-Description relationship
            if elem1.data_type == DataType.IMAGE and elem2.data_type == DataType.TEXT:
                return Relationship(
                    source=elem1.css_selector,
                    target=elem2.css_selector,
                    relationship_type='image_to_description',
                    confidence=0.6
                )
            
            return None
            
        except Exception:
            return None
    
    def _analyze_element_patterns(self, elements: List[SchemaElement]) -> Dict[str, Any]:
        """Analyze patterns in schema elements"""
        analysis = {
            'common_classes': [],
            'common_tags': [],
            'data_types': [],
            'selector_patterns': [],
            'consistency_score': 0.0
        }
        
        if not elements:
            return analysis
        
        # Analyze common CSS classes
        all_classes = []
        for elem in elements:
            all_classes.extend(elem.css_classes)
        
        if all_classes:
            class_counts = {}
            for cls in all_classes:
                class_counts[cls] = class_counts.get(cls, 0) + 1
            
            # Find classes that appear in most elements
            threshold = len(elements) * 0.6  # 60% of elements
            analysis['common_classes'] = [cls for cls, count in class_counts.items() 
                                        if count >= threshold]
        
        # Analyze common tags
        tag_counts = {}
        for elem in elements:
            tag_counts[elem.tag_name] = tag_counts.get(elem.tag_name, 0) + 1
        
        analysis['common_tags'] = list(tag_counts.keys())
        
        # Analyze data types
        type_counts = {}
        for elem in elements:
            type_counts[elem.data_type.value] = type_counts.get(elem.data_type.value, 0) + 1
        
        analysis['data_types'] = list(type_counts.keys())
        
        # Calculate consistency score
        if len(elements) > 1:
            # Based on similarity of CSS classes and tag names
            class_consistency = len(analysis['common_classes']) / len(elements)
            tag_consistency = 1.0 if len(analysis['common_tags']) == 1 else 0.5
            analysis['consistency_score'] = (class_consistency + tag_consistency) / 2
        else:
            analysis['consistency_score'] = 1.0
        
        return analysis
    
    def _generate_primary_selectors(self, elements: List[SchemaElement]) -> List[str]:
        """Generate primary CSS selectors for extraction"""
        selectors = []
        
        if not elements:
            return selectors
        
        # Use most common classes and tags
        analysis = self._analyze_element_patterns(elements)
        
        # Generate class-based selectors
        for common_class in analysis['common_classes']:
            selectors.append(f".{common_class}")
        
        # Generate tag-based selectors
        for common_tag in analysis['common_tags']:
            selectors.append(common_tag)
        
        # Generate combined selectors
        if analysis['common_classes'] and analysis['common_tags']:
            for tag in analysis['common_tags']:
                for cls in analysis['common_classes']:
                    selectors.append(f"{tag}.{cls}")
        
        # Remove duplicates and return top 5
        unique_selectors = list(dict.fromkeys(selectors))
        return unique_selectors[:5]
    
    def _generate_fallback_selectors(self, elements: List[SchemaElement]) -> List[str]:
        """Generate fallback selectors"""
        fallback_selectors = []
        
        # Generate attribute-based selectors
        for elem in elements[:3]:  # Use first 3 elements
            if elem.attributes:
                for attr, value in elem.attributes.items():
                    if attr in ['data-testid', 'data-qa', 'data-cy']:
                        fallback_selectors.append(f"[{attr}='{value}']")
        
        # Generate XPath-based selectors (simplified)
        for elem in elements[:2]:
            if elem.xpath:
                fallback_selectors.append(elem.xpath)
        
        return fallback_selectors[:3]
    
    def _suggest_transformations(self, elements: List[SchemaElement]) -> List[str]:
        """Suggest data transformations"""
        transformations = []
        
        # Analyze data types and suggest appropriate transformations
        data_types = [elem.data_type for elem in elements]
        
        if DataType.PRICE in data_types:
            transformations.extend([
                "remove_currency_symbols",
                "convert_to_float",
                "normalize_decimal_separator"
            ])
        
        if DataType.DATE in data_types:
            transformations.extend([
                "parse_date_format",
                "convert_to_iso_format"
            ])
        
        if DataType.TEXT in data_types:
            transformations.extend([
                "trim_whitespace",
                "remove_extra_spaces",
                "normalize_unicode"
            ])
        
        if DataType.EMAIL in data_types:
            transformations.append("validate_email_format")
        
        if DataType.PHONE in data_types:
            transformations.extend([
                "normalize_phone_format",
                "extract_digits_only"
            ])
        
        return transformations
    
    def _generate_validation_rules(self, elements: List[SchemaElement]) -> List[str]:
        """Generate validation rules for extracted data"""
        rules = []
        
        # Basic validation rules
        rules.append("not_empty")
        rules.append("min_length_2")
        
        # Type-specific validation
        data_types = [elem.data_type for elem in elements]
        
        if DataType.PRICE in data_types:
            rules.extend([
                "is_numeric",
                "positive_value",
                "max_price_validation"
            ])
        
        if DataType.EMAIL in data_types:
            rules.append("valid_email_format")
        
        if DataType.PHONE in data_types:
            rules.extend([
                "valid_phone_format",
                "min_digits_10"
            ])
        
        if DataType.URL in data_types:
            rules.append("valid_url_format")
        
        if DataType.DATE in data_types:
            rules.extend([
                "valid_date_format",
                "reasonable_date_range"
            ])
        
        return rules
    
    def _calculate_suggestion_confidence(self, analysis: Dict[str, Any]) -> float:
        """Calculate confidence in the extraction suggestions"""
        confidence = 0.5  # Base confidence
        
        # Boost confidence based on consistency
        consistency_score = analysis.get('consistency_score', 0.0)
        confidence += consistency_score * 0.3
        
        # Boost confidence based on common patterns
        if analysis.get('common_classes'):
            confidence += 0.1
        
        if analysis.get('common_tags'):
            confidence += 0.1
        
        # Boost confidence based on data type diversity
        data_types = analysis.get('data_types', [])
        if len(data_types) > 1:
            confidence += 0.1
        
        return min(confidence, 1.0)
