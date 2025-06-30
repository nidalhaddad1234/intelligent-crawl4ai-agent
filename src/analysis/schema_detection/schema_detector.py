"""
Smart Schema Detection Engine
Automatically detect data schemas on webpages
"""

import re
import logging
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from collections import Counter

from .models import (
    SchemaType, DataType, DetectedSchema, SchemaElement
)

logger = logging.getLogger(__name__)


class SchemaDetector:
    """Automatically detect data schemas on webpages"""
    
    def __init__(self):
        self.known_patterns = self._initialize_known_patterns()
        self.confidence_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        self.data_type_patterns = self._initialize_data_type_patterns()
    
    def _initialize_known_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize patterns for different schema types"""
        return {
            'table': {
                'selectors': ['table', '[role="table"]', '.table', '.data-table'],
                'indicators': ['thead', 'tbody', 'tr', 'td', 'th'],
                'confidence_boost': 0.2
            },
            'form': {
                'selectors': ['form', '.form', '.contact-form', '.search-form'],
                'indicators': ['input', 'select', 'textarea', 'button[type="submit"]'],
                'confidence_boost': 0.15
            },
            'product': {
                'selectors': ['.product', '.item', '.listing', '[data-product]'],
                'indicators': ['.price', '.title', '.name', '.description', '.rating'],
                'confidence_boost': 0.2
            },
            'article': {
                'selectors': ['article', '.article', '.post', '.content', 'main'],
                'indicators': ['h1', 'h2', '.title', '.author', '.date', 'p'],
                'confidence_boost': 0.15
            },
            'contact': {
                'selectors': ['.contact', '.contact-info', '.address', '.location'],
                'indicators': ['.email', '.phone', '.address', 'a[href^="mailto"]', 'a[href^="tel"]'],
                'confidence_boost': 0.25
            },
            'navigation': {
                'selectors': ['nav', '.nav', '.menu', '.navigation', 'header ul'],
                'indicators': ['a', 'li', '.nav-item', '.menu-item'],
                'confidence_boost': 0.1
            }
        }
    
    def _initialize_data_type_patterns(self) -> Dict[DataType, List[str]]:
        """Initialize regex patterns for data type detection"""
        return {
            DataType.PRICE: [
                r'\$[\d,]+\.?\d*',
                r'€[\d,]+\.?\d*',
                r'£[\d,]+\.?\d*',
                r'[\d,]+\.?\d*\s*(USD|EUR|GBP)',
                r'Price:?\s*[\d,]+\.?\d*'
            ],
            DataType.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ],
            DataType.PHONE: [
                r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',
                r'\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'
            ],
            DataType.DATE: [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',
                r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}'
            ],
            DataType.URL: [
                r'https?://[^\s<>"\']+',
                r'www\.[^\s<>"\']+',
                r'[a-zA-Z0-9-]+\.[a-zA-Z]{2,}[^\s<>"\']+'
            ],
            DataType.RATING: [
                r'\d+\.?\d*/5',
                r'\d+\.?\d*\s*stars?',
                r'Rating:?\s*\d+\.?\d*'
            ],
            DataType.PERCENTAGE: [
                r'\d+\.?\d*%',
                r'\d+\.?\d*\s*percent'
            ]
        }
    
    async def detect_schemas(self, html_content: str, url: str) -> List[DetectedSchema]:
        """Main method to detect all schemas on a webpage"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            detected_schemas = []
            
            # Detect different types of schemas
            tables = await self.detect_tables(soup)
            lists = await self.detect_lists(soup)
            forms = await self.detect_forms(soup)
            navigation = await self.detect_navigation(soup)
            
            detected_schemas.extend(tables)
            detected_schemas.extend(lists)
            detected_schemas.extend(forms)
            detected_schemas.extend(navigation)
            
            # Filter by confidence threshold
            high_confidence_schemas = [
                schema for schema in detected_schemas 
                if schema.confidence >= self.confidence_thresholds['medium']
            ]
            
            logger.info(f"Detected {len(high_confidence_schemas)} schemas on {url}")
            return high_confidence_schemas
            
        except Exception as e:
            logger.error(f"Schema detection failed: {e}")
            return []
    
    async def analyze_structured_data(self, html: str) -> Dict[str, Any]:
        """Analyze JSON-LD, microdata, and other structured data"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            structured_data = {}
            
            # JSON-LD detection
            json_scripts = soup.find_all('script', type='application/ld+json')
            if json_scripts:
                import json
                json_data = []
                for script in json_scripts:
                    try:
                        data = json.loads(script.string)
                        json_data.append(data)
                    except json.JSONDecodeError:
                        continue
                structured_data['json_ld'] = json_data
            
            # Microdata detection
            microdata_items = soup.find_all(attrs={'itemscope': True})
            if microdata_items:
                microdata = []
                for item in microdata_items:
                    item_type = item.get('itemtype', '')
                    properties = {}
                    prop_elements = item.find_all(attrs={'itemprop': True})
                    for prop in prop_elements:
                        prop_name = prop.get('itemprop')
                        prop_value = prop.get('content') or prop.get_text(strip=True)
                        properties[prop_name] = prop_value
                    
                    microdata.append({
                        'type': item_type,
                        'properties': properties
                    })
                structured_data['microdata'] = microdata
            
            # Open Graph detection
            og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
            if og_tags:
                og_data = {}
                for tag in og_tags:
                    property_name = tag.get('property', '').replace('og:', '')
                    content = tag.get('content', '')
                    og_data[property_name] = content
                structured_data['open_graph'] = og_data
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Structured data analysis failed: {e}")
            return {}
    
    async def detect_tables(self, soup: BeautifulSoup) -> List[DetectedSchema]:
        """Detect table schemas"""
        schemas = []
        tables = soup.find_all(['table', '[role="table"]'])
        
        for i, table in enumerate(tables):
            try:
                # Analyze table structure
                headers = table.find_all(['th', '[role="columnheader"]'])
                rows = table.find_all('tr')
                cells = table.find_all(['td', '[role="cell"]'])
                
                if len(rows) < 2 or len(cells) < 4:  # Minimum table requirements
                    continue
                
                # Calculate confidence based on structure
                confidence = 0.5  # Base confidence
                
                if headers:
                    confidence += 0.2  # Has headers
                if len(rows) > 5:
                    confidence += 0.1  # Substantial data
                if table.get('class') and any('table' in cls.lower() for cls in table.get('class')):
                    confidence += 0.1  # Proper CSS classes
                
                # Extract table elements
                elements = []
                
                # Header elements
                for header in headers:
                    elements.append(SchemaElement(
                        tag_name=header.name,
                        css_classes=header.get('class', []),
                        element_id=header.get('id'),
                        text_content=header.get_text(strip=True),
                        xpath=self._generate_xpath(header),
                        css_selector=self._generate_css_selector(header),
                        data_type=DataType.TEXT,
                        confidence=0.9
                    ))
                
                # Sample data rows
                sample_rows = rows[1:4] if len(rows) > 1 else rows  # Skip header row
                for row in sample_rows:
                    row_cells = row.find_all(['td', '[role="cell"]'])
                    for cell in row_cells:
                        cell_text = cell.get_text(strip=True)
                        data_type = self._detect_data_type(cell_text)
                        
                        elements.append(SchemaElement(
                            tag_name=cell.name,
                            css_classes=cell.get('class', []),
                            text_content=cell_text,
                            xpath=self._generate_xpath(cell),
                            css_selector=self._generate_css_selector(cell),
                            data_type=data_type,
                            confidence=0.8
                        ))
                
                # Create schema
                schema = DetectedSchema(
                    schema_type=SchemaType.TABLE,
                    confidence=min(confidence, 1.0),
                    elements=elements,
                    selector_path=self._generate_css_selector(table),
                    xpath_path=self._generate_xpath(table),
                    attributes={
                        'row_count': len(rows),
                        'column_count': len(headers) if headers else len(rows[0].find_all(['td', 'th'])) if rows else 0,
                        'has_headers': bool(headers),
                        'table_id': table.get('id', f'table_{i}')
                    },
                    metadata={
                        'detection_method': 'table_structure_analysis',
                        'element_count': len(elements)
                    }
                )
                
                schemas.append(schema)
                
            except Exception as e:
                logger.warning(f"Failed to analyze table {i}: {e}")
                continue
        
        return schemas
    
    async def detect_lists(self, soup: BeautifulSoup) -> List[DetectedSchema]:
        """Detect list schemas (ul, ol, structured divs)"""
        schemas = []
        
        # Find HTML lists
        lists = soup.find_all(['ul', 'ol'])
        
        # Find div-based lists (common pattern)
        div_lists = soup.find_all('div', class_=re.compile(r'list|items|grid|catalog'))
        
        all_lists = lists + div_lists
        
        for i, list_elem in enumerate(all_lists):
            try:
                # Get list items
                if list_elem.name in ['ul', 'ol']:
                    items = list_elem.find_all('li', recursive=False)
                else:
                    # For div-based lists, find child items
                    items = list_elem.find_all(['div', 'article', 'section'], recursive=False)
                    if len(items) < 3:  # Need at least 3 items to be considered a list
                        continue
                
                if len(items) < 2:
                    continue
                
                # Analyze list structure
                confidence = 0.4  # Base confidence
                
                if len(items) >= 5:
                    confidence += 0.2  # Substantial list
                if list_elem.get('class') and any(cls in ['list', 'items', 'grid'] for cls in list_elem.get('class')):
                    confidence += 0.1  # Proper CSS classes
                
                # Check for consistent structure in items
                consistency_score = self._calculate_list_consistency(items)
                confidence += consistency_score * 0.2
                
                # Extract elements
                elements = []
                sample_items = items[:5]  # Analyze first 5 items
                
                for item in sample_items:
                    item_text = item.get_text(strip=True)
                    
                    # Detect sub-elements within list items
                    links = item.find_all('a')
                    images = item.find_all('img')
                    prices = item.find_all(class_=re.compile(r'price|cost|amount'))
                    
                    elements.append(SchemaElement(
                        tag_name=item.name,
                        css_classes=item.get('class', []),
                        element_id=item.get('id'),
                        text_content=item_text[:200],  # Limit text length
                        xpath=self._generate_xpath(item),
                        css_selector=self._generate_css_selector(item),
                        data_type=DataType.TEXT,
                        confidence=0.7,
                        attributes={
                            'has_links': len(links) > 0,
                            'has_images': len(images) > 0,
                            'has_prices': len(prices) > 0
                        }
                    ))
                
                schema = DetectedSchema(
                    schema_type=SchemaType.LIST,
                    confidence=min(confidence, 1.0),
                    elements=elements,
                    selector_path=self._generate_css_selector(list_elem),
                    xpath_path=self._generate_xpath(list_elem),
                    attributes={
                        'item_count': len(items),
                        'list_type': list_elem.name,
                        'consistency_score': consistency_score,
                        'list_id': list_elem.get('id', f'list_{i}')
                    },
                    metadata={
                        'detection_method': 'list_structure_analysis',
                        'element_count': len(elements)
                    }
                )
                
                schemas.append(schema)
                
            except Exception as e:
                logger.warning(f"Failed to analyze list {i}: {e}")
                continue
        
        return schemas
    
    async def detect_forms(self, soup: BeautifulSoup) -> List[DetectedSchema]:
        """Detect form schemas"""
        schemas = []
        forms = soup.find_all('form')
        
        for i, form in enumerate(forms):
            try:
                # Get form elements
                inputs = form.find_all(['input', 'select', 'textarea'])
                buttons = form.find_all(['button', 'input[type="submit"]'])
                labels = form.find_all('label')
                
                if len(inputs) < 2:  # Minimum form requirements
                    continue
                
                confidence = 0.6  # Base confidence for forms
                
                if labels:
                    confidence += 0.2  # Has labels
                if buttons:
                    confidence += 0.1  # Has submit buttons
                if form.get('action'):
                    confidence += 0.1  # Has action URL
                
                elements = []
                
                # Analyze form inputs
                for input_elem in inputs:
                    input_type = input_elem.get('type', 'text')
                    input_name = input_elem.get('name', '')
                    input_id = input_elem.get('id', '')
                    
                    # Determine data type based on input type and name
                    data_type = self._detect_form_field_type(input_type, input_name, input_id)
                    
                    elements.append(SchemaElement(
                        tag_name=input_elem.name,
                        css_classes=input_elem.get('class', []),
                        element_id=input_id,
                        text_content=input_elem.get('placeholder', ''),
                        xpath=self._generate_xpath(input_elem),
                        css_selector=self._generate_css_selector(input_elem),
                        data_type=data_type,
                        confidence=0.8,
                        attributes={
                            'input_type': input_type,
                            'name': input_name,
                            'required': input_elem.get('required') is not None
                        }
                    ))
                
                schema = DetectedSchema(
                    schema_type=SchemaType.FORM,
                    confidence=min(confidence, 1.0),
                    elements=elements,
                    selector_path=self._generate_css_selector(form),
                    xpath_path=self._generate_xpath(form),
                    attributes={
                        'input_count': len(inputs),
                        'has_labels': len(labels) > 0,
                        'has_submit': len(buttons) > 0,
                        'action_url': form.get('action', ''),
                        'method': form.get('method', 'GET').upper()
                    },
                    metadata={
                        'detection_method': 'form_analysis',
                        'element_count': len(elements)
                    }
                )
                
                schemas.append(schema)
                
            except Exception as e:
                logger.warning(f"Failed to analyze form {i}: {e}")
                continue
        
        return schemas
    
    async def detect_navigation(self, soup: BeautifulSoup) -> List[DetectedSchema]:
        """Detect navigation schemas"""
        schemas = []
        
        # Find navigation elements
        nav_elements = soup.find_all(['nav', '[role="navigation"]'])
        nav_elements.extend(soup.find_all(class_=re.compile(r'nav|menu|navigation')))
        
        for i, nav in enumerate(nav_elements):
            try:
                # Get navigation links
                links = nav.find_all('a')
                list_items = nav.find_all('li')
                
                if len(links) < 3:  # Minimum navigation requirements
                    continue
                
                confidence = 0.5  # Base confidence
                
                if nav.name == 'nav' or nav.get('role') == 'navigation':
                    confidence += 0.2  # Semantic HTML
                if len(links) >= 5:
                    confidence += 0.1  # Substantial navigation
                
                elements = []
                
                for link in links[:10]:  # Analyze first 10 links
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)
                    
                    elements.append(SchemaElement(
                        tag_name=link.name,
                        css_classes=link.get('class', []),
                        element_id=link.get('id'),
                        text_content=link_text,
                        xpath=self._generate_xpath(link),
                        css_selector=self._generate_css_selector(link),
                        data_type=DataType.URL,
                        confidence=0.7,
                        attributes={
                            'href': href,
                            'is_external': href.startswith('http') and 'http' in href,
                            'has_text': bool(link_text)
                        }
                    ))
                
                schema = DetectedSchema(
                    schema_type=SchemaType.NAVIGATION,
                    confidence=min(confidence, 1.0),
                    elements=elements,
                    selector_path=self._generate_css_selector(nav),
                    xpath_path=self._generate_xpath(nav),
                    attributes={
                        'link_count': len(links),
                        'has_list_items': len(list_items) > 0,
                        'nav_type': nav.name,
                        'nav_id': nav.get('id', f'nav_{i}')
                    },
                    metadata={
                        'detection_method': 'navigation_analysis',
                        'element_count': len(elements)
                    }
                )
                
                schemas.append(schema)
                
            except Exception as e:
                logger.warning(f"Failed to analyze navigation {i}: {e}")
                continue
        
        return schemas
    
    def _detect_data_type(self, text: str) -> DataType:
        """Detect data type based on text content"""
        if not text:
            return DataType.TEXT
        
        text = text.strip()
        
        # Check each data type pattern
        for data_type, patterns in self.data_type_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return data_type
        
        # Additional heuristics
        if text.replace('.', '').replace(',', '').isdigit():
            return DataType.NUMBER
        
        if text.lower() in ['true', 'false', 'yes', 'no']:
            return DataType.BOOLEAN
        
        return DataType.TEXT
    
    def _detect_form_field_type(self, input_type: str, name: str, element_id: str) -> DataType:
        """Detect form field data type"""
        # Direct type mapping
        type_mapping = {
            'email': DataType.EMAIL,
            'tel': DataType.PHONE,
            'url': DataType.URL,
            'number': DataType.NUMBER,
            'date': DataType.DATE,
            'password': DataType.TEXT,
            'checkbox': DataType.BOOLEAN,
            'radio': DataType.BOOLEAN
        }
        
        if input_type in type_mapping:
            return type_mapping[input_type]
        
        # Name-based detection
        name_lower = (name + ' ' + element_id).lower()
        
        if any(keyword in name_lower for keyword in ['email', 'mail']):
            return DataType.EMAIL
        elif any(keyword in name_lower for keyword in ['phone', 'tel', 'mobile']):
            return DataType.PHONE
        elif any(keyword in name_lower for keyword in ['url', 'website', 'link']):
            return DataType.URL
        elif any(keyword in name_lower for keyword in ['date', 'birth', 'dob']):
            return DataType.DATE
        elif any(keyword in name_lower for keyword in ['price', 'cost', 'amount']):
            return DataType.PRICE
        elif any(keyword in name_lower for keyword in ['name', 'first', 'last', 'full']):
            return DataType.NAME
        elif any(keyword in name_lower for keyword in ['address', 'street', 'city', 'zip']):
            return DataType.ADDRESS
        
        return DataType.TEXT
    
    def _calculate_list_consistency(self, items: List[Tag]) -> float:
        """Calculate consistency score for list items"""
        if len(items) < 2:
            return 0.0
        
        # Analyze structure consistency
        structures = []
        for item in items[:10]:  # Check first 10 items
            structure = {
                'tag_count': len(item.find_all()),
                'has_links': len(item.find_all('a')) > 0,
                'has_images': len(item.find_all('img')) > 0,
                'class_pattern': ' '.join(item.get('class', [])),
                'text_length_range': len(item.get_text(strip=True)) // 50  # Group by text length
            }
            structures.append(structure)
        
        # Calculate consistency
        consistency_scores = []
        
        # Tag count consistency
        tag_counts = [s['tag_count'] for s in structures]
        tag_consistency = 1.0 - (max(tag_counts) - min(tag_counts)) / max(max(tag_counts), 1)
        consistency_scores.append(tag_consistency)
        
        # Link presence consistency
        link_presence = [s['has_links'] for s in structures]
        link_consistency = 1.0 if len(set(link_presence)) == 1 else 0.5
        consistency_scores.append(link_consistency)
        
        # Image presence consistency
        image_presence = [s['has_images'] for s in structures]
        image_consistency = 1.0 if len(set(image_presence)) == 1 else 0.5
        consistency_scores.append(image_consistency)
        
        return sum(consistency_scores) / len(consistency_scores)
    
    def _generate_xpath(self, element: Tag) -> str:
        """Generate XPath for an element"""
        try:
            components = []
            child = element if element.name else element.parent
            
            for parent in child.parents:
                if parent.name == '[document]':
                    break
                
                siblings = parent.find_all(child.name, recursive=False)
                if len(siblings) > 1:
                    index = siblings.index(child) + 1
                    components.append(f'{child.name}[{index}]')
                else:
                    components.append(child.name)
                child = parent
            
            components.reverse()
            return '/' + '/'.join(components) if components else ''
            
        except Exception:
            return ''
    
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
