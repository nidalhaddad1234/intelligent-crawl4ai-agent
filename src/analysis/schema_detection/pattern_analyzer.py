"""
Content Pattern Recognition and Analysis
Identify repeating content patterns and data structures
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter

from bs4 import BeautifulSoup, Tag
import difflib

from .models import (
    PatternType, DataType, ContentPattern, SchemaElement
)

logger = logging.getLogger(__name__)


class ContentPatternAnalyzer:
    """Identify repeating content patterns and data structures"""
    
    def __init__(self):
        self.pattern_indicators = self._initialize_pattern_indicators()
        self.min_pattern_repetition = 3
        self.similarity_threshold = 0.7
    
    def _initialize_pattern_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Initialize indicators for different pattern types"""
        return {
            'product_listing': {
                'selectors': ['.product', '.item', '.listing', '[data-product]', '.card'],
                'indicators': ['.price', '.name', '.title', '.image', '.rating', '.description'],
                'required_elements': ['price', 'name'],
                'confidence_boost': 0.3
            },
            'article_content': {
                'selectors': ['.article', '.post', '.entry', 'article'],
                'indicators': ['.title', '.author', '.date', '.content', '.excerpt'],
                'required_elements': ['title'],
                'confidence_boost': 0.2
            },
            'contact_info': {
                'selectors': ['.contact', '.info', '.details', '.address'],
                'indicators': ['.email', '.phone', '.address', 'a[href^="mailto"]', 'a[href^="tel"]'],
                'required_elements': ['email', 'phone'],
                'confidence_boost': 0.25
            },
            'pricing_data': {
                'selectors': ['.pricing', '.plan', '.package', '.tier'],
                'indicators': ['.price', '.cost', '.amount', '.features', '.name'],
                'required_elements': ['price'],
                'confidence_boost': 0.2
            },
            'navigation_menu': {
                'selectors': ['nav', '.nav', '.menu', '.navigation'],
                'indicators': ['a', '.link', '.nav-item', '.menu-item'],
                'required_elements': ['link'],
                'confidence_boost': 0.15
            }
        }
    
    async def find_repeating_patterns(self, html: str) -> List[ContentPattern]:
        """Find repeating content patterns on the page"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            patterns = []
            
            # Find patterns by structure similarity
            structural_patterns = await self._find_structural_patterns(soup)
            patterns.extend(structural_patterns)
            
            # Find patterns by known indicators
            indicator_patterns = await self._find_indicator_patterns(soup)
            patterns.extend(indicator_patterns)
            
            # Remove duplicates and merge similar patterns
            unique_patterns = self._deduplicate_patterns(patterns)
            
            logger.info(f"Found {len(unique_patterns)} unique content patterns")
            return unique_patterns
            
        except Exception as e:
            logger.error(f"Pattern analysis failed: {e}")
            return []
    
    async def detect_product_listings(self, html: str) -> List[ContentPattern]:
        """Detect product listing patterns"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for common product container patterns
            product_containers = []
            
            # Direct product selectors
            for selector in self.pattern_indicators['product_listing']['selectors']:
                elements = soup.select(selector)
                product_containers.extend(elements)
            
            # Find containers with price indicators
            price_elements = soup.find_all(class_=re.compile(r'price|cost|amount'))
            for price_elem in price_elements:
                # Find the likely product container (parent with multiple similar siblings)
                container = self._find_product_container(price_elem)
                if container:
                    product_containers.append(container)
            
            # Analyze for product patterns
            patterns = []
            for container in product_containers:
                pattern = await self._analyze_product_pattern(container, soup)
                if pattern and pattern.confidence > 0.6:
                    patterns.append(pattern)
            
            return self._deduplicate_patterns(patterns)
            
        except Exception as e:
            logger.error(f"Product listing detection failed: {e}")
            return []
    
    async def detect_article_content(self, html: str) -> ContentPattern:
        """Detect main article content pattern"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for article indicators
            article_elements = soup.find_all(['article', '[role="main"]'])
            article_elements.extend(soup.find_all(class_=re.compile(r'article|post|content|entry')))
            
            best_pattern = None
            best_confidence = 0.0
            
            for article_elem in article_elements:
                pattern = await self._analyze_article_pattern(article_elem)
                if pattern and pattern.confidence > best_confidence:
                    best_pattern = pattern
                    best_confidence = pattern.confidence
            
            return best_pattern
            
        except Exception as e:
            logger.error(f"Article content detection failed: {e}")
            return None
    
    async def detect_contact_info(self, html: str) -> ContentPattern:
        """Detect contact information pattern"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find contact indicators
            contact_elements = []
            
            # Email and phone links
            email_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            phone_links = soup.find_all('a', href=re.compile(r'^tel:'))
            contact_elements.extend(email_links + phone_links)
            
            # Contact-related class names
            contact_containers = soup.find_all(class_=re.compile(r'contact|address|info'))
            contact_elements.extend(contact_containers)
            
            if not contact_elements:
                return None
            
            # Find the most comprehensive contact pattern
            best_pattern = None
            best_score = 0
            
            for elem in contact_elements:
                pattern = await self._analyze_contact_pattern(elem)
                if pattern:
                    score = len(pattern.sample_elements) * pattern.confidence
                    if score > best_score:
                        best_pattern = pattern
                        best_score = score
            
            return best_pattern
            
        except Exception as e:
            logger.error(f"Contact info detection failed: {e}")
            return None
    
    async def detect_pricing_data(self, html: str) -> List[ContentPattern]:
        """Detect pricing/plan patterns"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find pricing containers
            pricing_elements = []
            
            # Direct pricing selectors
            for selector in self.pattern_indicators['pricing_data']['selectors']:
                elements = soup.select(selector)
                pricing_elements.extend(elements)
            
            # Find elements with price indicators
            price_elements = soup.find_all(class_=re.compile(r'price|plan|tier|package'))
            pricing_elements.extend(price_elements)
            
            patterns = []
            for elem in pricing_elements:
                pattern = await self._analyze_pricing_pattern(elem)
                if pattern and pattern.confidence > 0.5:
                    patterns.append(pattern)
            
            return self._deduplicate_patterns(patterns)
            
        except Exception as e:
            logger.error(f"Pricing data detection failed: {e}")
            return []
    
    async def _find_structural_patterns(self, soup: BeautifulSoup) -> List[ContentPattern]:
        """Find patterns based on structural similarity"""
        patterns = []
        
        # Find groups of sibling elements with similar structure
        all_containers = soup.find_all(['div', 'article', 'section', 'li'])
        
        for container in all_containers:
            siblings = container.find_next_siblings()
            if len(siblings) < self.min_pattern_repetition:
                continue
            
            # Check structural similarity among siblings
            similar_siblings = [container]
            for sibling in siblings:
                if self._calculate_structural_similarity(container, sibling) > self.similarity_threshold:
                    similar_siblings.append(sibling)
            
            if len(similar_siblings) >= self.min_pattern_repetition:
                pattern = await self._create_pattern_from_elements(similar_siblings, PatternType.REPEATING_ELEMENTS)
                if pattern:
                    patterns.append(pattern)
        
        return patterns
    
    async def _find_indicator_patterns(self, soup: BeautifulSoup) -> List[ContentPattern]:
        """Find patterns based on known indicators"""
        patterns = []
        
        for pattern_name, config in self.pattern_indicators.items():
            for selector in config['selectors']:
                try:
                    elements = soup.select(selector)
                    if len(elements) >= self.min_pattern_repetition:
                        pattern_type = PatternType(pattern_name.upper())
                        pattern = await self._create_pattern_from_elements(elements, pattern_type)
                        if pattern:
                            pattern.confidence += config['confidence_boost']
                            patterns.append(pattern)
                except Exception:
                    continue
        
        return patterns
    
    async def _analyze_product_pattern(self, container: Tag, soup: BeautifulSoup) -> Optional[ContentPattern]:
        """Analyze a potential product pattern"""
        try:
            # Find similar product containers
            similar_containers = self._find_similar_elements(container, soup)
            
            if len(similar_containers) < self.min_pattern_repetition:
                return None
            
            # Analyze product elements within containers
            elements = []
            confidence = 0.6  # Base confidence for products
            
            # Look for common product elements
            for product_container in similar_containers[:5]:  # Analyze first 5
                # Price
                price_elem = product_container.find(class_=re.compile(r'price|cost|amount'))
                if price_elem:
                    elements.append(SchemaElement(
                        tag_name=price_elem.name,
                        css_classes=price_elem.get('class', []),
                        text_content=price_elem.get_text(strip=True),
                        data_type=DataType.PRICE,
                        confidence=0.9
                    ))
                    confidence += 0.1
                
                # Name/Title
                name_elem = product_container.find(class_=re.compile(r'name|title|product-name'))
                if name_elem:
                    elements.append(SchemaElement(
                        tag_name=name_elem.name,
                        css_classes=name_elem.get('class', []),
                        text_content=name_elem.get_text(strip=True),
                        data_type=DataType.NAME,
                        confidence=0.8
                    ))
                    confidence += 0.1
                
                # Image
                img_elem = product_container.find('img')
                if img_elem:
                    elements.append(SchemaElement(
                        tag_name=img_elem.name,
                        css_classes=img_elem.get('class', []),
                        attributes={'src': img_elem.get('src', '')},
                        data_type=DataType.IMAGE,
                        confidence=0.7
                    ))
            
            pattern = ContentPattern(
                pattern_type=PatternType.PRODUCT_LISTING,
                confidence=min(confidence, 1.0),
                sample_elements=elements,
                css_selector=self._generate_css_selector(container),
                repeat_count=len(similar_containers),
                consistency_score=self._calculate_pattern_consistency(similar_containers),
                extraction_hint=f"Product listing with {len(similar_containers)} items"
            )
            
            return pattern
            
        except Exception as e:
            logger.warning(f"Product pattern analysis failed: {e}")
            return None
    
    async def _analyze_article_pattern(self, article_elem: Tag) -> Optional[ContentPattern]:
        """Analyze article content pattern"""
        try:
            elements = []
            confidence = 0.5
            
            # Title
            title_elem = article_elem.find(['h1', 'h2', '.title', '.headline'])
            if title_elem:
                elements.append(SchemaElement(
                    tag_name=title_elem.name,
                    css_classes=title_elem.get('class', []),
                    text_content=title_elem.get_text(strip=True),
                    data_type=DataType.TEXT,
                    confidence=0.9
                ))
                confidence += 0.2
            
            # Author
            author_elem = article_elem.find(class_=re.compile(r'author|byline|writer'))
            if author_elem:
                elements.append(SchemaElement(
                    tag_name=author_elem.name,
                    css_classes=author_elem.get('class', []),
                    text_content=author_elem.get_text(strip=True),
                    data_type=DataType.NAME,
                    confidence=0.8
                ))
                confidence += 0.1
            
            # Date
            date_elem = article_elem.find(class_=re.compile(r'date|time|published'))
            if date_elem:
                elements.append(SchemaElement(
                    tag_name=date_elem.name,
                    css_classes=date_elem.get('class', []),
                    text_content=date_elem.get_text(strip=True),
                    data_type=DataType.DATE,
                    confidence=0.8
                ))
                confidence += 0.1
            
            # Content
            content_elem = article_elem.find(class_=re.compile(r'content|body|text'))
            if content_elem:
                elements.append(SchemaElement(
                    tag_name=content_elem.name,
                    css_classes=content_elem.get('class', []),
                    text_content=content_elem.get_text(strip=True)[:500],  # First 500 chars
                    data_type=DataType.TEXT,
                    confidence=0.7
                ))
                confidence += 0.1
            
            if not elements:
                return None
            
            pattern = ContentPattern(
                pattern_type=PatternType.ARTICLE_CONTENT,
                confidence=min(confidence, 1.0),
                sample_elements=elements,
                css_selector=self._generate_css_selector(article_elem),
                repeat_count=1,
                consistency_score=1.0,
                extraction_hint="Main article content"
            )
            
            return pattern
            
        except Exception as e:
            logger.warning(f"Article pattern analysis failed: {e}")
            return None
    
    async def _analyze_contact_pattern(self, contact_elem: Tag) -> Optional[ContentPattern]:
        """Analyze contact information pattern"""
        try:
            elements = []
            confidence = 0.4
            
            # Email
            email_links = contact_elem.find_all('a', href=re.compile(r'^mailto:'))
            for email_link in email_links:
                email_text = email_link.get_text(strip=True) or email_link.get('href', '').replace('mailto:', '')
                elements.append(SchemaElement(
                    tag_name=email_link.name,
                    css_classes=email_link.get('class', []),
                    text_content=email_text,
                    data_type=DataType.EMAIL,
                    confidence=0.9,
                    attributes={'href': email_link.get('href', '')}
                ))
                confidence += 0.2
            
            # Phone
            phone_links = contact_elem.find_all('a', href=re.compile(r'^tel:'))
            for phone_link in phone_links:
                phone_text = phone_link.get_text(strip=True) or phone_link.get('href', '').replace('tel:', '')
                elements.append(SchemaElement(
                    tag_name=phone_link.name,
                    css_classes=phone_link.get('class', []),
                    text_content=phone_text,
                    data_type=DataType.PHONE,
                    confidence=0.9,
                    attributes={'href': phone_link.get('href', '')}
                ))
                confidence += 0.2
            
            # Address
            address_elem = contact_elem.find(class_=re.compile(r'address|location'))
            if address_elem:
                elements.append(SchemaElement(
                    tag_name=address_elem.name,
                    css_classes=address_elem.get('class', []),
                    text_content=address_elem.get_text(strip=True),
                    data_type=DataType.ADDRESS,
                    confidence=0.8
                ))
                confidence += 0.1
            
            if not elements:
                return None
            
            pattern = ContentPattern(
                pattern_type=PatternType.CONTACT_INFO,
                confidence=min(confidence, 1.0),
                sample_elements=elements,
                css_selector=self._generate_css_selector(contact_elem),
                repeat_count=1,
                consistency_score=1.0,
                extraction_hint="Contact information"
            )
            
            return pattern
            
        except Exception as e:
            logger.warning(f"Contact pattern analysis failed: {e}")
            return None
    
    async def _analyze_pricing_pattern(self, pricing_elem: Tag) -> Optional[ContentPattern]:
        """Analyze pricing pattern"""
        try:
            elements = []
            confidence = 0.5
            
            # Price
            price_elem = pricing_elem.find(class_=re.compile(r'price|cost|amount'))
            if price_elem:
                elements.append(SchemaElement(
                    tag_name=price_elem.name,
                    css_classes=price_elem.get('class', []),
                    text_content=price_elem.get_text(strip=True),
                    data_type=DataType.PRICE,
                    confidence=0.9
                ))
                confidence += 0.2
            
            # Plan name
            name_elem = pricing_elem.find(class_=re.compile(r'name|title|plan'))
            if name_elem:
                elements.append(SchemaElement(
                    tag_name=name_elem.name,
                    css_classes=name_elem.get('class', []),
                    text_content=name_elem.get_text(strip=True),
                    data_type=DataType.TEXT,
                    confidence=0.8
                ))
                confidence += 0.1
            
            # Features
            features_elem = pricing_elem.find(class_=re.compile(r'features|benefits|includes'))
            if features_elem:
                elements.append(SchemaElement(
                    tag_name=features_elem.name,
                    css_classes=features_elem.get('class', []),
                    text_content=features_elem.get_text(strip=True)[:300],  # First 300 chars
                    data_type=DataType.TEXT,
                    confidence=0.7
                ))
                confidence += 0.1
            
            if not elements:
                return None
            
            pattern = ContentPattern(
                pattern_type=PatternType.PRICING_DATA,
                confidence=min(confidence, 1.0),
                sample_elements=elements,
                css_selector=self._generate_css_selector(pricing_elem),
                repeat_count=1,
                consistency_score=1.0,
                extraction_hint="Pricing information"
            )
            
            return pattern
            
        except Exception as e:
            logger.warning(f"Pricing pattern analysis failed: {e}")
            return None
    
    def _find_product_container(self, price_element: Tag) -> Optional[Tag]:
        """Find the likely product container for a price element"""
        try:
            # Walk up the DOM to find a container with similar siblings
            current = price_element.parent
            
            while current and current.name != '[document]':
                siblings = current.find_next_siblings()
                
                # Check if siblings have similar price elements
                price_siblings = 0
                for sibling in siblings[:10]:  # Check first 10 siblings
                    if sibling.find(class_=re.compile(r'price|cost|amount')):
                        price_siblings += 1
                
                if price_siblings >= 2:  # Found container with multiple price siblings
                    return current
                
                current = current.parent
            
            return None
            
        except Exception:
            return None
    
    def _find_similar_elements(self, element: Tag, soup: BeautifulSoup) -> List[Tag]:
        """Find elements similar to the given element"""
        similar_elements = [element]
        
        # Find siblings with similar structure
        siblings = element.find_next_siblings()
        for sibling in siblings:
            if self._calculate_structural_similarity(element, sibling) > self.similarity_threshold:
                similar_elements.append(sibling)
        
        # Find elements with similar class names in the entire document
        if element.get('class'):
            class_name = element.get('class')[0]
            class_elements = soup.find_all(class_=class_name)
            for elem in class_elements:
                if elem not in similar_elements and self._calculate_structural_similarity(element, elem) > self.similarity_threshold:
                    similar_elements.append(elem)
                    if len(similar_elements) >= 10:  # Limit to 10 similar elements
                        break
        
        return similar_elements
    
    def _calculate_structural_similarity(self, elem1: Tag, elem2: Tag) -> float:
        """Calculate structural similarity between two elements"""
        try:
            if not elem1 or not elem2 or elem1.name != elem2.name:
                return 0.0
            
            scores = []
            
            # Tag name similarity (already checked above)
            scores.append(1.0)
            
            # Class similarity
            classes1 = set(elem1.get('class', []))
            classes2 = set(elem2.get('class', []))
            if classes1 or classes2:
                class_similarity = len(classes1.intersection(classes2)) / len(classes1.union(classes2))
                scores.append(class_similarity)
            
            # Child count similarity
            children1 = len(elem1.find_all())
            children2 = len(elem2.find_all())
            if children1 > 0 or children2 > 0:
                child_similarity = 1.0 - abs(children1 - children2) / max(children1, children2, 1)
                scores.append(child_similarity)
            
            # Text length similarity
            text1_len = len(elem1.get_text(strip=True))
            text2_len = len(elem2.get_text(strip=True))
            if text1_len > 0 or text2_len > 0:
                text_similarity = 1.0 - abs(text1_len - text2_len) / max(text1_len, text2_len, 1)
                scores.append(text_similarity)
            
            return sum(scores) / len(scores) if scores else 0.0
            
        except Exception:
            return 0.0
    
    def _calculate_pattern_consistency(self, elements: List[Tag]) -> float:
        """Calculate consistency score for a pattern"""
        if len(elements) < 2:
            return 1.0
        
        consistency_scores = []
        
        # Calculate pairwise similarities
        for i in range(min(5, len(elements))):  # Check first 5 elements
            for j in range(i + 1, min(5, len(elements))):
                similarity = self._calculate_structural_similarity(elements[i], elements[j])
                consistency_scores.append(similarity)
        
        return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0
    
    async def _create_pattern_from_elements(self, elements: List[Tag], pattern_type: PatternType) -> Optional[ContentPattern]:
        """Create a content pattern from a list of elements"""
        try:
            if not elements:
                return None
            
            # Create sample elements from the first few
            sample_elements = []
            for elem in elements[:3]:  # Use first 3 as samples
                sample_elements.append(SchemaElement(
                    tag_name=elem.name,
                    css_classes=elem.get('class', []),
                    element_id=elem.get('id'),
                    text_content=elem.get_text(strip=True)[:200],  # First 200 chars
                    data_type=DataType.TEXT,
                    confidence=0.7
                ))
            
            # Calculate pattern metrics
            consistency_score = self._calculate_pattern_consistency(elements)
            confidence = 0.5 + (consistency_score * 0.3) + (min(len(elements) / 10, 0.2))
            
            pattern = ContentPattern(
                pattern_type=pattern_type,
                confidence=min(confidence, 1.0),
                sample_elements=sample_elements,
                css_selector=self._generate_css_selector(elements[0]),
                repeat_count=len(elements),
                consistency_score=consistency_score,
                extraction_hint=f"Pattern with {len(elements)} similar elements"
            )
            
            return pattern
            
        except Exception as e:
            logger.warning(f"Pattern creation failed: {e}")
            return None
    
    def _deduplicate_patterns(self, patterns: List[ContentPattern]) -> List[ContentPattern]:
        """Remove duplicate and overlapping patterns"""
        if not patterns:
            return []
        
        unique_patterns = []
        
        for pattern in patterns:
            is_duplicate = False
            
            for existing in unique_patterns:
                # Check for CSS selector overlap
                if pattern.css_selector == existing.css_selector:
                    is_duplicate = True
                    # Keep the one with higher confidence
                    if pattern.confidence > existing.confidence:
                        unique_patterns.remove(existing)
                        unique_patterns.append(pattern)
                    break
                
                # Check for similar extraction hints
                if pattern.extraction_hint and existing.extraction_hint:
                    similarity = difflib.SequenceMatcher(None, pattern.extraction_hint, existing.extraction_hint).ratio()
                    if similarity > 0.8:
                        is_duplicate = True
                        if pattern.confidence > existing.confidence:
                            unique_patterns.remove(existing)
                            unique_patterns.append(pattern)
                        break
            
            if not is_duplicate:
                unique_patterns.append(pattern)
        
        # Sort by confidence
        unique_patterns.sort(key=lambda p: p.confidence, reverse=True)
        
        return unique_patterns
    
    def _generate_css_selector(self, element: Tag) -> str:
        """Generate CSS selector for an element"""
        try:
            selector_parts = []
            
            # Add tag name
            if element.name:
                selector_parts.append(element.name)
            
            # Add ID if present
            if element.get('id'):
                selector_parts.append(f"#{element.get('id')}")
                return ''.join(selector_parts)  # ID is unique, return early
            
            # Add classes if present
            classes = element.get('class', [])
            if classes:
                class_selector = '.' + '.'.join(classes)
                selector_parts.append(class_selector)
            
            return ''.join(selector_parts) if selector_parts else element.name or ''
            
        except Exception:
            return ''
