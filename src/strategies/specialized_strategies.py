#!/usr/bin/env python3
"""
Specialized Extraction Strategies
Advanced strategies for handling complex scenarios like forms, authentication, pagination
"""

import asyncio
import json
import time
import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from .base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

class RegexExtractionStrategy(BaseExtractionStrategy):
    """
    High-performance regex-based extraction for common patterns
    
    Provides 20x speed boost for extracting:
    - Email addresses
    - Phone numbers (US/International)
    - URLs and links
    - Social media handles
    - Business identifiers (Tax IDs, Registration numbers)
    - Addresses and postal codes
    
    Best for: Contact discovery, lead generation, data mining
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        
        # Compiled regex patterns for maximum performance
        self.patterns = {
            "emails": {
                "pattern": re.compile(
                    r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                    re.IGNORECASE
                ),
                "cleaner": lambda x: x.lower().strip()
            },
            "phones": {
                "pattern": re.compile(
                    r'(?:\+?1[-\s.]?)?(?:\(?[0-9]{3}\)?[-\s.]?)?[0-9]{3}[-\s.]?[0-9]{4}|'
                    r'(?:\+[1-9]\d{0,3}[-\s.]?)?(?:\(?\d{1,4}\)?[-\s.]?)?\d{1,4}[-\s.]?\d{1,4}[-\s.]?\d{1,9}'
                ),
                "cleaner": lambda x: re.sub(r'[^\d+]', '', x) if len(re.sub(r'[^\d]', '', x)) >= 7 else None
            },
            "urls": {
                "pattern": re.compile(
                    r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?',
                    re.IGNORECASE
                ),
                "cleaner": lambda x: x.strip()
            },
            "social_handles": {
                "pattern": re.compile(
                    r'@([A-Za-z0-9_]{1,15})(?=\s|$|[^A-Za-z0-9_])'
                ),
                "cleaner": lambda x: x.strip('@')
            },
            "linkedin_profiles": {
                "pattern": re.compile(
                    r'linkedin\.com/in/([a-zA-Z0-9\-]+)',
                    re.IGNORECASE
                ),
                "cleaner": lambda x: f"https://linkedin.com/in/{x.split('/')[-1]}"
            },
            "addresses": {
                "pattern": re.compile(
                    r'\d+\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd|Way|Place|Pl)\s*,?\s*[A-Za-z\s]+,?\s*[A-Z]{2}\s*\d{5}(?:-\d{4})?',
                    re.IGNORECASE
                ),
                "cleaner": lambda x: ' '.join(x.split())
            },
            "zip_codes": {
                "pattern": re.compile(
                    r'\b\d{5}(?:-\d{4})?\b'
                ),
                "cleaner": lambda x: x.strip()
            },
            "business_hours": {
                "pattern": re.compile(
                    r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s*-?\s*(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)?[a-z]*:?\s*\d{1,2}:?\d{0,2}\s*(?:AM|PM|am|pm)?\s*-\s*\d{1,2}:?\d{0,2}\s*(?:AM|PM|am|pm)?',
                    re.IGNORECASE
                ),
                "cleaner": lambda x: ' '.join(x.split())
            },
            "prices": {
                "pattern": re.compile(
                    r'\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*(?:USD|dollars?)'
                ),
                "cleaner": lambda x: re.sub(r'[^\d.]', '', x) if '.' in x else re.sub(r'[^\d]', '', x)
            }
        }
        
        # Context-aware pattern priorities
        self.purpose_patterns = {
            "contact_discovery": ["emails", "phones", "addresses", "business_hours"],
            "lead_generation": ["emails", "phones", "linkedin_profiles", "social_handles"],
            "business_listings": ["emails", "phones", "addresses", "business_hours", "urls"],
            "social_media_analysis": ["social_handles", "emails", "urls"],
            "e_commerce": ["prices", "emails", "phones", "addresses"],
            "default": ["emails", "phones", "urls"]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Get text content from HTML (faster than BeautifulSoup for regex)
            text_content = self._extract_text_content(html_content)
            
            # Select patterns based on purpose
            target_patterns = self.purpose_patterns.get(purpose, self.purpose_patterns["default"])
            
            # Extract using selected patterns
            extracted_data = {}
            total_matches = 0
            
            for pattern_name in target_patterns:
                if pattern_name in self.patterns:
                    matches = self._extract_pattern(text_content, pattern_name)
                    if matches:
                        extracted_data[pattern_name] = matches
                        total_matches += len(matches)
            
            # Add metadata and confidence scoring
            metadata = {
                "text_length": len(text_content),
                "patterns_used": target_patterns,
                "total_matches": total_matches,
                "extraction_mode": "regex_fast"
            }
            
            # Calculate confidence based on match quality and quantity
            confidence = self._calculate_pattern_confidence(extracted_data, purpose)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="RegexExtractionStrategy",
                execution_time=execution_time,
                metadata=metadata
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="RegexExtractionStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_text_content(self, html_content: str) -> str:
        """
        Fast text extraction from HTML without full DOM parsing
        Much faster than BeautifulSoup for regex operations
        """
        # Remove script and style content
        text = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags but keep text content
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        return text.strip()
    
    def _extract_pattern(self, text: str, pattern_name: str) -> List[str]:
        """
        Extract and clean matches for a specific pattern
        """
        pattern_config = self.patterns[pattern_name]
        pattern = pattern_config["pattern"]
        cleaner = pattern_config["cleaner"]
        
        # Find all matches
        if pattern_name == "social_handles":
            # Special handling for social handles to extract group
            matches = [match.group(1) for match in pattern.finditer(text)]
        elif pattern_name == "linkedin_profiles":
            # Special handling for LinkedIn profiles
            matches = [match.group(0) for match in pattern.finditer(text)]
        else:
            matches = pattern.findall(text)
        
        # Clean and deduplicate matches
        cleaned_matches = []
        seen = set()
        
        for match in matches:
            cleaned = cleaner(match)
            if cleaned and cleaned not in seen and self._is_valid_match(cleaned, pattern_name):
                cleaned_matches.append(cleaned)
                seen.add(cleaned)
        
        return cleaned_matches[:50]  # Limit to prevent excessive matches
    
    def _is_valid_match(self, match: str, pattern_type: str) -> bool:
        """
        Validate extracted matches to reduce false positives
        """
        if pattern_type == "emails":
            # Filter out common false positives
            invalid_domains = ['example.com', 'test.com', 'localhost']
            if any(domain in match for domain in invalid_domains):
                return False
            # Must have valid domain structure
            return '.' in match.split('@')[1] if '@' in match else False
        
        elif pattern_type == "phones":
            # Must have minimum length after cleaning
            digits_only = re.sub(r'[^\d]', '', match)
            return len(digits_only) >= 7
        
        elif pattern_type == "urls":
            # Must be valid HTTP/HTTPS URL
            return match.startswith(('http://', 'https://'))
        
        elif pattern_type == "prices":
            # Must be reasonable price range
            try:
                price_value = float(re.sub(r'[^\d.]', '', match))
                return 0.01 <= price_value <= 1000000  # Reasonable price range
            except ValueError:
                return False
        
        elif pattern_type == "zip_codes":
            # US ZIP code validation
            return re.match(r'^\d{5}(-\d{4})?
    """
    Automated form detection, completion, and submission
    
    Examples:
    - Automatically fill out contact forms for lead generation
    - Submit search forms to access hidden content
    - Complete registration forms for data access
    - Handle multi-step form wizards
    """
    
    def __init__(self, form_data: Dict[str, Any] = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.form_data = form_data or {}
        
        # Common form field patterns
        self.field_patterns = {
            "email": [
                "email", "e-mail", "mail", "user_email", "contact_email"
            ],
            "name": [
                "name", "full_name", "first_name", "last_name", "username", "contact_name"
            ],
            "phone": [
                "phone", "telephone", "mobile", "contact_phone", "phone_number"
            ],
            "company": [
                "company", "organization", "business", "company_name"
            ],
            "message": [
                "message", "comment", "inquiry", "question", "description"
            ],
            "subject": [
                "subject", "topic", "title", "regarding"
            ]
        }
        
        # Default form data
        self.default_data = {
            "email": "contact@example.com",
            "name": "John Smith",
            "phone": "555-123-4567",
            "company": "Example Corp",
            "message": "I am interested in learning more about your services.",
            "subject": "Business Inquiry"
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect and analyze forms
            forms_data = self._analyze_forms(soup, url)
            
            # Determine which forms to fill
            target_forms = self._select_target_forms(forms_data, purpose)
            
            # Create form completion plan
            completion_plan = self._create_completion_plan(target_forms, context)
            
            extracted_data = {
                "forms_detected": len(forms_data),
                "target_forms": len(target_forms),
                "completion_plan": completion_plan,
                "forms_analysis": forms_data
            }
            
            # If this is just analysis, return the plan
            if context and context.get("analyze_only", True):
                extracted_data["action_required"] = "Form completion requires browser automation"
            
            confidence = 0.8 if target_forms else 0.3
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(target_forms),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="FormAutoStrategy",
                execution_time=execution_time,
                metadata={
                    "forms_found": len(forms_data),
                    "actionable_forms": len(target_forms)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="FormAutoStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _analyze_forms(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Analyze all forms on the page"""
        forms_data = []
        
        forms = soup.find_all('form')
        
        for i, form in enumerate(forms):
            form_info = {
                "form_id": form.get('id', f'form_{i}'),
                "action": form.get('action', ''),
                "method": form.get('method', 'GET').upper(),
                "fields": [],
                "submit_buttons": [],
                "form_type": "unknown"
            }
            
            # Make action URL absolute
            if form_info["action"]:
                form_info["action"] = urljoin(base_url, form_info["action"])
            
            # Analyze form fields
            fields = form.find_all(['input', 'textarea', 'select'])
            for field in fields:
                field_info = self._analyze_form_field(field)
                if field_info:
                    form_info["fields"].append(field_info)
            
            # Find submit buttons
            submit_buttons = form.find_all(['input', 'button'], type=['submit', 'button'])
            for button in submit_buttons:
                button_info = {
                    "type": button.get('type', 'button'),
                    "name": button.get('name', ''),
                    "value": button.get('value', ''),
                    "text": button.get_text(strip=True)
                }
                form_info["submit_buttons"].append(button_info)
            
            # Determine form type
            form_info["form_type"] = self._classify_form(form_info)
            
            forms_data.append(form_info)
        
        return forms_data
    
    def _analyze_form_field(self, field) -> Optional[Dict[str, Any]]:
        """Analyze individual form field"""
        field_type = field.get('type', 'text')
        
        # Skip hidden and submit fields
        if field_type in ['hidden', 'submit', 'button']:
            return None
        
        field_info = {
            "tag": field.name,
            "type": field_type,
            "name": field.get('name', ''),
            "id": field.get('id', ''),
            "placeholder": field.get('placeholder', ''),
            "required": field.has_attr('required'),
            "value": field.get('value', ''),
            "label": self._find_field_label(field),
            "field_purpose": "unknown"
        }
        
        # Determine field purpose
        field_info["field_purpose"] = self._classify_field_purpose(field_info)
        
        return field_info
    
    def _find_field_label(self, field) -> str:
        """Find label associated with form field"""
        # Check for label tag
        field_id = field.get('id')
        if field_id:
            label = field.find_parent().find('label', attrs={'for': field_id})
            if label:
                return label.get_text(strip=True)
        
        # Check for wrapping label
        label_parent = field.find_parent('label')
        if label_parent:
            return label_parent.get_text(strip=True).replace(field.get('value', ''), '').strip()
        
        # Check for adjacent text
        previous = field.find_previous_sibling(string=True)
        if previous:
            text = previous.strip()
            if text and len(text) < 50:
                return text
        
        return ""
    
    def _classify_field_purpose(self, field_info: Dict[str, Any]) -> str:
        """Classify the purpose of a form field"""
        
        # Combine all text sources for analysis
        text_sources = [
            field_info.get("name", "").lower(),
            field_info.get("id", "").lower(),
            field_info.get("placeholder", "").lower(),
            field_info.get("label", "").lower()
        ]
        
        combined_text = " ".join(text_sources)
        
        # Check against known patterns
        for purpose, patterns in self.field_patterns.items():
            if any(pattern in combined_text for pattern in patterns):
                return purpose
        
        # Special cases based on field type
        field_type = field_info.get("type", "")
        if field_type == "email":
            return "email"
        elif field_type == "tel":
            return "phone"
        elif field_type == "password":
            return "password"
        elif field_info.get("tag") == "textarea":
            return "message"
        
        return "unknown"
    
    def _classify_form(self, form_info: Dict[str, Any]) -> str:
        """Classify the type of form"""
        
        # Analyze field purposes
        field_purposes = [field["field_purpose"] for field in form_info["fields"]]
        
        # Contact forms
        if "email" in field_purposes and ("message" in field_purposes or "name" in field_purposes):
            return "contact_form"
        
        # Search forms
        if any("search" in field.get("name", "").lower() for field in form_info["fields"]):
            return "search_form"
        
        # Login forms
        if "password" in field_purposes and ("email" in field_purposes or "name" in field_purposes):
            return "login_form"
        
        # Registration forms
        if field_purposes.count("email") >= 1 and len(field_purposes) > 3:
            return "registration_form"
        
        # Newsletter forms
        if "email" in field_purposes and len(field_purposes) <= 2:
            return "newsletter_form"
        
        return "unknown"
    
    def _select_target_forms(self, forms_data: List[Dict[str, Any]], purpose: str) -> List[Dict[str, Any]]:
        """Select forms that match the extraction purpose"""
        
        target_forms = []
        
        for form in forms_data:
            form_type = form["form_type"]
            
            # Select forms based on purpose
            if purpose == "contact_discovery" and form_type in ["contact_form", "newsletter_form"]:
                target_forms.append(form)
            elif purpose == "lead_generation" and form_type in ["contact_form", "registration_form"]:
                target_forms.append(form)
            elif purpose == "data_access" and form_type in ["search_form", "registration_form"]:
                target_forms.append(form)
            elif purpose == "form_automation":
                target_forms.append(form)  # Include all forms
        
        return target_forms
    
    def _create_completion_plan(self, target_forms: List[Dict[str, Any]], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create plan for completing target forms"""
        
        completion_plan = []
        
        # Get form data from context or use defaults
        form_data = context.get("form_data", {}) if context else {}
        combined_data = {**self.default_data, **self.form_data, **form_data}
        
        for form in target_forms:
            plan = {
                "form_id": form["form_id"],
                "form_type": form["form_type"],
                "action": form["action"],
                "method": form["method"],
                "completion_steps": []
            }
            
            # Create completion steps for each field
            for field in form["fields"]:
                field_purpose = field["field_purpose"]
                
                if field_purpose in combined_data:
                    step = {
                        "action": "fill_field",
                        "selector": self._create_field_selector(field),
                        "value": combined_data[field_purpose],
                        "field_name": field["name"],
                        "field_type": field["type"]
                    }
                    plan["completion_steps"].append(step)
            
            # Add submit step
            if form["submit_buttons"]:
                submit_button = form["submit_buttons"][0]  # Use first submit button
                plan["completion_steps"].append({
                    "action": "submit_form",
                    "button_text": submit_button["text"],
                    "button_type": submit_button["type"]
                })
            
            completion_plan.append(plan)
        
        return completion_plan
    
    def _create_field_selector(self, field: Dict[str, Any]) -> str:
        """Create CSS selector for form field"""
        
        if field["id"]:
            return f"#{field['id']}"
        elif field["name"]:
            return f"[name='{field['name']}']"
        else:
            # Fallback selector
            return f"{field['tag']}[type='{field['type']}']"
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Form strategy confidence based on form presence"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        forms = soup.find_all('form')
        
        if not forms:
            return 0.1
        
        # Higher confidence for relevant purposes
        if purpose in ["contact_discovery", "lead_generation", "form_automation"]:
            return 0.8
        
        return 0.5
    
    def supports_purpose(self, purpose: str) -> bool:
        """Form strategy supports automation purposes"""
        supported_purposes = [
            "contact_discovery", "lead_generation", "form_automation",
            "data_access", "registration_automation"
        ]
        return purpose in supported_purposes

class PaginationStrategy(BaseExtractionStrategy):
    """
    Handle paginated content extraction across multiple pages
    
    Examples:
    - Extract all products from multi-page catalogs
    - Scrape all search results across pagination
    - Collect complete datasets from paginated APIs
    - Handle infinite scroll and load-more buttons
    """
    
    def __init__(self, max_pages: int = 10, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.max_pages = max_pages
        
        # Common pagination patterns
        self.pagination_selectors = {
            "next_button": [
                "a[rel='next']",
                ".next, .next-page",
                "[aria-label*='next']",
                ".pagination .next",
                "a:contains('Next')",
                ".pager-next a"
            ],
            "page_numbers": [
                ".pagination a",
                ".page-numbers a",
                ".pager a",
                "[aria-label*='page']"
            ],
            "current_page": [
                ".pagination .current",
                ".page-numbers .current",
                ".active",
                "[aria-current='page']"
            ],
            "load_more": [
                ".load-more",
                "[data-testid*='load-more']",
                "button:contains('Load More')",
                ".show-more"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Analyze pagination structure
            pagination_info = self._analyze_pagination(soup, url)
            
            # Extract data from current page
            current_page_data = self._extract_current_page_data(soup, purpose)
            
            # Create pagination plan
            pagination_plan = self._create_pagination_plan(pagination_info, url, purpose)
            
            extracted_data = {
                "current_page_data": current_page_data,
                "pagination_info": pagination_info,
                "pagination_plan": pagination_plan,
                "total_estimated_pages": pagination_info.get("total_pages", 1)
            }
            
            # If context requests full extraction, note it requires automation
            if context and context.get("extract_all_pages", False):
                extracted_data["automation_required"] = "Full pagination extraction requires browser automation"
            
            confidence = 0.8 if pagination_info.get("has_pagination") else 0.3
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(current_page_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="PaginationStrategy",
                execution_time=execution_time,
                metadata={
                    "has_pagination": pagination_info.get("has_pagination", False),
                    "pagination_type": pagination_info.get("type", "none")
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="PaginationStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _analyze_pagination(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Analyze pagination structure on the page"""
        
        pagination_info = {
            "has_pagination": False,
            "type": "none",
            "next_url": None,
            "page_urls": [],
            "current_page": 1,
            "total_pages": 1
        }
        
        # Check for next button
        next_button = self._find_pagination_element(soup, "next_button")
        if next_button:
            pagination_info["has_pagination"] = True
            pagination_info["type"] = "next_button"
            
            next_href = next_button.get('href')
            if next_href:
                pagination_info["next_url"] = urljoin(base_url, next_href)
        
        # Check for page numbers
        page_elements = self._find_pagination_elements(soup, "page_numbers")
        if page_elements:
            pagination_info["has_pagination"] = True
            if pagination_info["type"] == "none":
                pagination_info["type"] = "numbered_pages"
            
            page_urls = []
            for elem in page_elements:
                href = elem.get('href')
                if href:
                    page_urls.append(urljoin(base_url, href))
            
            pagination_info["page_urls"] = page_urls
            pagination_info["total_pages"] = len(page_urls)
        
        # Check current page
        current_elem = self._find_pagination_element(soup, "current_page")
        if current_elem:
            current_text = current_elem.get_text(strip=True)
            try:
                pagination_info["current_page"] = int(current_text)
            except ValueError:
                pass
        
        # Check for load more button
        load_more = self._find_pagination_element(soup, "load_more")
        if load_more:
            pagination_info["has_pagination"] = True
            pagination_info["type"] = "load_more"
            pagination_info["load_more_present"] = True
        
        # Try to extract total pages from pagination text
        pagination_text = self._get_pagination_text(soup)
        if pagination_text:
            total_match = re.search(r'of (\d+)', pagination_text)
            if total_match:
                pagination_info["total_pages"] = int(total_match.group(1))
        
        return pagination_info
    
    def _find_pagination_element(self, soup: BeautifulSoup, element_type: str):
        """Find pagination element using multiple selectors"""
        selectors = self.pagination_selectors.get(element_type, [])
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element
        
        return None
    
    def _find_pagination_elements(self, soup: BeautifulSoup, element_type: str):
        """Find multiple pagination elements"""
        selectors = self.pagination_selectors.get(element_type, [])
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return elements
        
        return []
    
    def _get_pagination_text(self, soup: BeautifulSoup) -> str:
        """Get pagination text for analysis"""
        pagination_containers = soup.select(".pagination, .pager, .page-info")
        
        for container in pagination_containers:
            text = container.get_text(strip=True)
            if text:
                return text
        
        return ""
    
    def _extract_current_page_data(self, soup: BeautifulSoup, purpose: str) -> Dict[str, Any]:
        """Extract data from current page"""
        
        # This is a simplified extraction - in practice, would use appropriate strategy
        data = {"items": []}
        
        # Look for common item containers
        item_selectors = [
            ".item, .result, .product",
            ".listing, .card",
            "[data-testid*='item'], [data-testid*='result']"
        ]
        
        for selector in item_selectors:
            items = soup.select(selector)
            if items:
                for item in items[:50]:  # Limit per page
                    item_data = self._extract_item_data(item)
                    if item_data:
                        data["items"].append(item_data)
                break
        
        data["items_count"] = len(data["items"])
        return data
    
    def _extract_item_data(self, item_element) -> Dict[str, Any]:
        """Extract basic data from item element"""
        
        item_data = {}
        
        # Title
        title_elem = item_element.select_one("h1, h2, h3, .title, .name")
        if title_elem:
            item_data["title"] = title_elem.get_text(strip=True)
        
        # Link
        link_elem = item_element.select_one("a")
        if link_elem:
            item_data["link"] = link_elem.get('href', '')
        
        # Price
        price_elem = item_element.select_one(".price, .cost, .amount")
        if price_elem:
            item_data["price"] = price_elem.get_text(strip=True)
        
        # Description
        desc_elem = item_element.select_one(".description, .summary")
        if desc_elem:
            item_data["description"] = desc_elem.get_text(strip=True)[:200]
        
        return item_data if item_data else None
    
    def _create_pagination_plan(self, pagination_info: Dict[str, Any], base_url: str, purpose: str) -> Dict[str, Any]:
        """Create plan for paginated extraction"""
        
        plan = {
            "strategy": "none",
            "estimated_pages": pagination_info.get("total_pages", 1),
            "urls_to_process": [],
            "automation_steps": []
        }
        
        if not pagination_info.get("has_pagination"):
            return plan
        
        pagination_type = pagination_info.get("type")
        
        if pagination_type == "numbered_pages":
            plan["strategy"] = "url_based"
            plan["urls_to_process"] = pagination_info.get("page_urls", [])[:self.max_pages]
        
        elif pagination_type == "next_button":
            plan["strategy"] = "sequential_navigation"
            plan["automation_steps"] = [
                {
                    "action": "click_next",
                    "selector": self.pagination_selectors["next_button"][0],
                    "repeat": min(self.max_pages - 1, 10)
                }
            ]
        
        elif pagination_type == "load_more":
            plan["strategy"] = "load_more_clicks"
            plan["automation_steps"] = [
                {
                    "action": "click_load_more",
                    "selector": self.pagination_selectors["load_more"][0],
                    "repeat": min(self.max_pages - 1, 20),
                    "wait_between": 2000  # 2 second wait
                }
            ]
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Pagination strategy confidence"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for pagination indicators
        pagination_indicators = [
            ".pagination", ".pager", ".page-numbers",
            "a[rel='next']", ".next", ".load-more"
        ]
        
        has_pagination = any(soup.select(indicator) for indicator in pagination_indicators)
        
        if has_pagination:
            return 0.9
        
        # Check for multiple items (suggests possible pagination)
        item_containers = soup.select(".item, .result, .product, .listing")
        if len(item_containers) > 10:
            return 0.6
        
        return 0.2
    
    def supports_purpose(self, purpose: str) -> bool:
        """Pagination supports data collection purposes"""
        supported_purposes = [
            "business_listings", "product_data", "search_results",
            "directory_mining", "catalog_extraction", "data_collection"
        ]
        return purpose in supported_purposes

class InfiniteScrollStrategy(BaseExtractionStrategy):
    """
    Handle infinite scroll and dynamic content loading
    
    Examples:
    - Extract all posts from social media feeds
    - Scrape complete product catalogs with lazy loading
    - Handle dynamic search results that load on scroll
    - Collect all items from infinite scroll lists
    """
    
    def __init__(self, max_scrolls: int = 20, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.max_scrolls = max_scrolls
        
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect infinite scroll indicators
            scroll_info = self._detect_infinite_scroll(soup, html_content)
            
            # Extract current visible content
            current_data = self._extract_visible_content(soup, purpose)
            
            # Create scroll automation plan
            scroll_plan = self._create_scroll_plan(scroll_info, purpose)
            
            extracted_data = {
                "current_data": current_data,
                "scroll_detected": scroll_info.get("has_infinite_scroll", False),
                "scroll_plan": scroll_plan,
                "automation_required": "Infinite scroll extraction requires browser automation"
            }
            
            confidence = 0.8 if scroll_info.get("has_infinite_scroll") else 0.3
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(current_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="InfiniteScrollStrategy",
                execution_time=execution_time,
                metadata={
                    "infinite_scroll_detected": scroll_info.get("has_infinite_scroll", False),
                    "loading_indicators": scroll_info.get("loading_indicators", [])
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="InfiniteScrollStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _detect_infinite_scroll(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
        """Detect infinite scroll patterns"""
        
        scroll_info = {
            "has_infinite_scroll": False,
            "loading_indicators": [],
            "scroll_triggers": [],
            "container_selectors": []
        }
        
        # Check for loading indicators
        loading_selectors = [
            ".loading", ".spinner", ".loader",
            "[data-testid*='loading']", "[data-testid*='spinner']",
            ".infinite-loading", ".load-indicator"
        ]
        
        for selector in loading_selectors:
            elements = soup.select(selector)
            if elements:
                scroll_info["loading_indicators"].append(selector)
                scroll_info["has_infinite_scroll"] = True
        
        # Check JavaScript for infinite scroll patterns
        if any(pattern in html_content for pattern in [
            "infinite", "scroll", "lazy", "load-more",
            "IntersectionObserver", "onscroll"
        ]):
            scroll_info["has_infinite_scroll"] = True
        
        # Look for common infinite scroll containers
        container_patterns = [
            ".feed", ".timeline", ".infinite-scroll",
            ".results-container", ".items-container",
            "[data-testid*='feed']", "[data-testid*='timeline']"
        ]
        
        for pattern in container_patterns:
            if soup.select(pattern):
                scroll_info["container_selectors"].append(pattern)
        
        # Check for scroll trigger elements
        trigger_patterns = [
            ".load-more-trigger", ".scroll-trigger",
            "[data-scroll-trigger]", ".infinite-trigger"
        ]
        
        for pattern in trigger_patterns:
            if soup.select(pattern):
                scroll_info["scroll_triggers"].append(pattern)
        
        return scroll_info
    
    def _extract_visible_content(self, soup: BeautifulSoup, purpose: str) -> Dict[str, Any]:
        """Extract currently visible content"""
        
        data = {"items": [], "containers_found": []}
        
        # Common content item patterns
        item_patterns = [
            ".post, .item, .card",
            ".result, .listing",
            "[data-testid*='post'], [data-testid*='item']",
            ".feed-item, .timeline-item"
        ]
        
        for pattern in item_patterns:
            items = soup.select(pattern)
            if items:
                data["containers_found"].append(pattern)
                
                for item in items:
                    item_data = self._extract_scroll_item(item)
                    if item_data:
                        data["items"].append(item_data)
                
                break  # Use first successful pattern
        
        data["items_count"] = len(data["items"])
        return data
    
    def _extract_scroll_item(self, item_element) -> Dict[str, Any]:
        """Extract data from scroll item"""
        
        item_data = {}
        
        # Text content
        text_elem = item_element.select_one(".content, .text, .description, p")
        if text_elem:
            item_data["text"] = text_elem.get_text(strip=True)[:500]
        
        # Title/header
        title_elem = item_element.select_one("h1, h2, h3, .title, .header")
        if title_elem:
            item_data["title"] = title_elem.get_text(strip=True)
        
        # Author/source
        author_elem = item_element.select_one(".author, .user, .source")
        if author_elem:
            item_data["author"] = author_elem.get_text(strip=True)
        
        # Timestamp
        time_elem = item_element.select_one("time, .timestamp, .date")
        if time_elem:
            item_data["timestamp"] = time_elem.get_text(strip=True)
        
        # Image
        img_elem = item_element.select_one("img")
        if img_elem:
            item_data["image"] = img_elem.get('src', '')
        
        # Link
        link_elem = item_element.select_one("a")
        if link_elem:
            item_data["link"] = link_elem.get('href', '')
        
        return item_data if item_data else None
    
    def _create_scroll_plan(self, scroll_info: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Create infinite scroll automation plan"""
        
        plan = {
            "automation_steps": [],
            "estimated_scrolls": self.max_scrolls,
            "wait_between_scrolls": 2000,  # 2 seconds
            "success_indicators": []
        }
        
        if not scroll_info.get("has_infinite_scroll"):
            return plan
        
        # Basic scroll strategy
        plan["automation_steps"] = [
            {
                "action": "scroll_to_bottom",
                "repeat": self.max_scrolls,
                "wait_for_loading": True,
                "loading_selectors": scroll_info.get("loading_indicators", [])
            }
        ]
        
        # If load triggers exist, click them instead
        if scroll_info.get("scroll_triggers"):
            plan["automation_steps"] = [
                {
                    "action": "click_triggers",
                    "selectors": scroll_info["scroll_triggers"],
                    "repeat": self.max_scrolls,
                    "wait_between": 2000
                }
            ]
        
        # Define success indicators
        plan["success_indicators"] = [
            "no_new_content_loaded",
            "end_of_feed_message",
            "max_scrolls_reached"
        ]
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Infinite scroll strategy confidence"""
        
        # Check for infinite scroll indicators
        scroll_indicators = [
            "infinite", "scroll", "lazy", "feed", "timeline"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for indicator in scroll_indicators if indicator in content_lower)
        
        confidence = 0.3 + (indicator_count * 0.1)
        
        # Higher confidence for social media and feed-based sites
        if any(pattern in url for pattern in ["twitter", "facebook", "instagram", "linkedin", "feed"]):
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Infinite scroll supports content collection purposes"""
        supported_purposes = [
            "social_media_analysis", "content_collection", "feed_monitoring",
            "news_content", "product_data", "user_generated_content"
        ]
        return purpose in supported_purposes

class AuthenticationStrategy(BaseExtractionStrategy):
    """
    Handle login and authentication workflows
    
    Examples:
    - Login to LinkedIn for profile access
    - Authenticate with Google/Facebook OAuth
    - Handle two-factor authentication
    - Maintain session across multiple requests
    - Handle subscription-based content access
    """
    
    def __init__(self, credentials: Dict[str, str] = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.credentials = credentials or {}
        
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect authentication requirements
            auth_info = self._detect_authentication_requirements(soup, html_content, url)
            
            # Create authentication plan
            auth_plan = self._create_authentication_plan(auth_info, url, context)
            
            extracted_data = {
                "authentication_required": auth_info.get("requires_auth", False),
                "auth_type": auth_info.get("auth_type", "none"),
                "auth_plan": auth_plan,
                "login_form_detected": auth_info.get("has_login_form", False),
                "oauth_providers": auth_info.get("oauth_providers", [])
            }
            
            confidence = 0.9 if auth_info.get("requires_auth") else 0.2
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=True,  # Always successful at detecting auth requirements
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="AuthenticationStrategy",
                execution_time=execution_time,
                metadata={
                    "auth_detected": auth_info.get("requires_auth", False),
                    "auth_complexity": auth_info.get("complexity", "simple")
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="AuthenticationStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _detect_authentication_requirements(self, soup: BeautifulSoup, html_content: str, url: str) -> Dict[str, Any]:
        """Detect authentication requirements and methods"""
        
        auth_info = {
            "requires_auth": False,
            "auth_type": "none",
            "has_login_form": False,
            "oauth_providers": [],
            "complexity": "simple"
        }
        
        # Check for login indicators
        login_indicators = [
            "login", "sign in", "log in", "authentication",
            "please sign in", "access denied", "unauthorized"
        ]
        
        page_text = html_content.lower()
        if any(indicator in page_text for indicator in login_indicators):
            auth_info["requires_auth"] = True
        
        # Check for login forms
        login_forms = soup.select("form:has([type='password']), .login-form, .signin-form")
        if login_forms:
            auth_info["has_login_form"] = True
            auth_info["requires_auth"] = True
            auth_info["auth_type"] = "form_login"
        
        # Check for OAuth providers
        oauth_patterns = {
            "google": ["google", "gmail"],
            "facebook": ["facebook", "fb"],
            "twitter": ["twitter"],
            "linkedin": ["linkedin"],
            "microsoft": ["microsoft", "outlook"],
            "github": ["github"]
        }
        
        for provider, patterns in oauth_patterns.items():
            if any(pattern in page_text for pattern in patterns):
                if any(oauth_term in page_text for oauth_term in ["oauth", "sign in with", "continue with"]):
                    auth_info["oauth_providers"].append(provider)
                    auth_info["auth_type"] = "oauth"
                    auth_info["requires_auth"] = True
        
        # Check for 2FA indicators
        tfa_indicators = ["two-factor", "2fa", "verification code", "authenticator"]
        if any(indicator in page_text for indicator in tfa_indicators):
            auth_info["complexity"] = "two_factor"
        
        # Check for subscription walls
        subscription_indicators = ["subscribe", "premium", "upgrade", "paywall"]
        if any(indicator in page_text for indicator in subscription_indicators):
            auth_info["auth_type"] = "subscription"
            auth_info["complexity"] = "subscription_required"
        
        # Platform-specific detection
        auth_info.update(self._detect_platform_specific_auth(url, soup))
        
        return auth_info
    
    def _detect_platform_specific_auth(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect platform-specific authentication patterns"""
        
        platform_info = {}
        
        if "linkedin.com" in url:
            if soup.select(".authwall, .guest-homepage"):
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "linkedin_login",
                    "complexity": "professional_network"
                })
        
        elif "facebook.com" in url:
            if "login" in soup.get_text().lower():
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "facebook_login",
                    "complexity": "social_network"
                })
        
        elif "twitter.com" in url or "x.com" in url:
            if soup.select(".login-form, .signin-form"):
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "twitter_login",
                    "complexity": "social_network"
                })
        
        return platform_info
    
    def _create_authentication_plan(self, auth_info: Dict[str, Any], url: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create authentication execution plan"""
        
        plan = {
            "steps": [],
            "estimated_time": 30,  # seconds
            "success_indicators": [],
            "failure_indicators": []
        }
        
        if not auth_info.get("requires_auth"):
            return plan
        
        auth_type = auth_info.get("auth_type")
        credentials = context.get("credentials", {}) if context else {}
        combined_creds = {**self.credentials, **credentials}
        
        if auth_type == "form_login":
            plan["steps"] = [
                {
                    "action": "fill_username",
                    "selector": "[name='username'], [name='email'], [type='email']",
                    "value": combined_creds.get("username", "")
                },
                {
                    "action": "fill_password",
                    "selector": "[name='password'], [type='password']",
                    "value": combined_creds.get("password", "")
                },
                {
                    "action": "submit_form",
                    "selector": "[type='submit'], .login-button, .signin-button"
                }
            ]
        
        elif auth_type == "oauth":
            provider = auth_info.get("oauth_providers", ["google"])[0]
            plan["steps"] = [
                {
                    "action": "click_oauth_button",
                    "selector": f".{provider}-login, [data-provider='{provider}']",
                    "provider": provider
                },
                {
                    "action": "handle_oauth_redirect",
                    "wait_for_redirect": True,
                    "timeout": 30000
                }
            ]
        
        # Add 2FA handling if needed
        if auth_info.get("complexity") == "two_factor":
            plan["steps"].append({
                "action": "handle_2fa",
                "selector": "[name='code'], [name='verification_code']",
                "wait_for_prompt": True,
                "code_source": combined_creds.get("2fa_method", "manual")
            })
        
        # Define success/failure indicators
        plan["success_indicators"] = [
            "dashboard", "profile", "logged in", "welcome",
            ".user-menu", ".logout", ".account-menu"
        ]
        
        plan["failure_indicators"] = [
            "invalid", "incorrect", "failed", "error",
            ".error-message", ".login-error"
        ]
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Authentication strategy confidence"""
        
        # Check for authentication indicators
        auth_indicators = [
            "login", "sign in", "authentication", "password",
            "access denied", "unauthorized"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for indicator in auth_indicators if indicator in content_lower)
        
        confidence = min(indicator_count * 0.2, 0.9)
        
        # Higher confidence for known platforms requiring auth
        protected_domains = ["linkedin.com", "facebook.com", "twitter.com"]
        if any(domain in url for domain in protected_domains):
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Authentication supports access-controlled purposes"""
        supported_purposes = [
            "profile_info", "social_media_analysis", "premium_content",
            "subscription_data", "protected_resources", "member_content"
        ]
        return purpose in supported_purposes

class CaptchaStrategy(BaseExtractionStrategy):
    """
    Handle CAPTCHA detection and solving
    
    Examples:
    - Detect reCAPTCHA and hCaptcha challenges
    - Integrate with CAPTCHA solving services
    - Handle image-based CAPTCHAs
    - Manage CAPTCHA retry logic
    """
    
    def __init__(self, captcha_service_key: str = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.captcha_service_key = captcha_service_key
        
        # CAPTCHA detection patterns
        self.captcha_indicators = {
            "recaptcha": [
                ".g-recaptcha", "[data-sitekey]", 
                "iframe[src*='recaptcha']", "#recaptcha"
            ],
            "hcaptcha": [
                ".h-captcha", "[data-sitekey*='hcaptcha']",
                "iframe[src*='hcaptcha']"
            ],
            "image_captcha": [
                ".captcha-image", "[src*='captcha']",
                ".verification-image", "[alt*='captcha']"
            ],
            "text_captcha": [
                "[name*='captcha']", ".captcha-input",
                "[placeholder*='captcha']"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect CAPTCHA types
            captcha_info = self._detect_captcha_types(soup, html_content)
            
            # Create solving plan
            solving_plan = self._create_captcha_solving_plan(captcha_info, context)
            
            extracted_data = {
                "captcha_detected": captcha_info.get("has_captcha", False),
                "captcha_types": captcha_info.get("types", []),
                "solving_plan": solving_plan,
                "service_required": captcha_info.get("has_captcha", False)
            }
            
            confidence = 0.9 if captcha_info.get("has_captcha") else 0.1
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=True,  # Always successful at detection
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="CaptchaStrategy",
                execution_time=execution_time,
                metadata={
                    "captcha_present": captcha_info.get("has_captcha", False),
                    "complexity": captcha_info.get("complexity", "none")
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="CaptchaStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _detect_captcha_types(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
        """Detect CAPTCHA types and characteristics"""
        
        captcha_info = {
            "has_captcha": False,
            "types": [],
            "complexity": "none",
            "site_keys": {},
            "elements": {}
        }
        
        # Check each CAPTCHA type
        for captcha_type, selectors in self.captcha_indicators.items():
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    captcha_info["has_captcha"] = True
                    captcha_info["types"].append(captcha_type)
                    captcha_info["elements"][captcha_type] = selector
                    
                    # Extract site keys for reCAPTCHA/hCaptcha
                    if captcha_type in ["recaptcha", "hcaptcha"]:
                        site_key = self._extract_site_key(elements[0], captcha_type)
                        if site_key:
                            captcha_info["site_keys"][captcha_type] = site_key
                    
                    break
        
        # Determine complexity
        if "recaptcha" in captcha_info["types"]:
            captcha_info["complexity"] = "recaptcha_v2_or_v3"
        elif "hcaptcha" in captcha_info["types"]:
            captcha_info["complexity"] = "hcaptcha"
        elif "image_captcha" in captcha_info["types"]:
            captcha_info["complexity"] = "image_recognition"
        elif "text_captcha" in captcha_info["types"]:
            captcha_info["complexity"] = "text_input"
        
        return captcha_info
    
    def _extract_site_key(self, element, captcha_type: str) -> Optional[str]:
        """Extract site key from CAPTCHA element"""
        
        # Check data-sitekey attribute
        site_key = element.get('data-sitekey')
        if site_key:
            return site_key
        
        # Check parent elements
        parent = element.find_parent()
        if parent:
            site_key = parent.get('data-sitekey')
            if site_key:
                return site_key
        
        # Check iframe src for embedded CAPTCHAs
        if element.name == 'iframe':
            src = element.get('src', '')
            if 'sitekey=' in src:
                import re
                match = re.search(r'sitekey=([^&]+)', src)
                if match:
                    return match.group(1)
        
        return None
    
    def _create_captcha_solving_plan(self, captcha_info: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create CAPTCHA solving plan"""
        
        plan = {
            "solving_method": "none",
            "steps": [],
            "estimated_time": 0,
            "service_config": {}
        }
        
        if not captcha_info.get("has_captcha"):
            return plan
        
        captcha_types = captcha_info.get("types", [])
        complexity = captcha_info.get("complexity", "none")
        
        if "recaptcha" in captcha_types:
            plan["solving_method"] = "2captcha_recaptcha"
            plan["estimated_time"] = 30  # seconds
            plan["steps"] = [
                {
                    "action": "submit_to_service",
                    "service": "2captcha",
                    "captcha_type": "recaptcha_v2",
                    "site_key": captcha_info.get("site_keys", {}).get("recaptcha"),
                    "page_url": context.get("url") if context else None
                },
                {
                    "action": "wait_for_solution",
                    "timeout": 120  # 2 minutes max
                },
                {
                    "action": "submit_solution",
                    "selector": "[name='g-recaptcha-response']"
                }
            ]
        
        elif "hcaptcha" in captcha_types:
            plan["solving_method"] = "2captcha_hcaptcha"
            plan["estimated_time"] = 30
            plan["steps"] = [
                {
                    "action": "submit_to_service",
                    "service": "2captcha",
                    "captcha_type": "hcaptcha",
                    "site_key": captcha_info.get("site_keys", {}).get("hcaptcha"),
                    "page_url": context.get("url") if context else None
                },
                {
                    "action": "wait_for_solution",
                    "timeout": 120
                },
                {
                    "action": "submit_solution",
                    "selector": "[name='h-captcha-response']"
                }
            ]
        
        elif "image_captcha" in captcha_types:
            plan["solving_method"] = "image_recognition"
            plan["estimated_time"] = 20
            plan["steps"] = [
                {
                    "action": "capture_image",
                    "selector": captcha_info.get("elements", {}).get("image_captcha")
                },
                {
                    "action": "solve_image",
                    "service": "2captcha_image"
                },
                {
                    "action": "input_solution",
                    "selector": "[name*='captcha'], .captcha-input"
                }
            ]
        
        elif "text_captcha" in captcha_types:
            plan["solving_method"] = "text_recognition"
            plan["estimated_time"] = 10
            plan["steps"] = [
                {
                    "action": "extract_question",
                    "selector": ".captcha-question, .captcha-text"
                },
                {
                    "action": "solve_text",
                    "method": "simple_math_or_lookup"
                },
                {
                    "action": "input_solution",
                    "selector": "[name*='captcha'], .captcha-input"
                }
            ]
        
        # Add service configuration
        if self.captcha_service_key:
            plan["service_config"] = {
                "api_key": self.captcha_service_key,
                "service_url": "http://2captcha.com/in.php",
                "result_url": "http://2captcha.com/res.php"
            }
        else:
            plan["service_config"] = {
                "note": "CAPTCHA service API key required for automated solving"
            }
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """CAPTCHA strategy confidence"""
        
        # Check for CAPTCHA indicators
        captcha_terms = [
            "captcha", "recaptcha", "hcaptcha", "verification",
            "prove you're human", "security check"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for term in captcha_terms if term in content_lower)
        
        confidence = min(indicator_count * 0.3, 0.9)
        
        # Check for actual CAPTCHA elements
        soup = BeautifulSoup(html_content, 'html.parser')
        if soup.select(".g-recaptcha, .h-captcha"):
            confidence = 0.95
        
        return confidence
    
    def supports_purpose(self, purpose: str) -> bool:
        """CAPTCHA strategy supports access purposes"""
        supported_purposes = [
            "form_automation", "data_access", "protected_content",
            "anti_bot_circumvention", "verification_handling"
        ]
        return purpose in supported_purposes
, match) is not None
        
        return True  # Default: accept the match
    
    def _calculate_pattern_confidence(self, extracted_data: Dict[str, Any], purpose: str) -> float:
        """
        Calculate confidence based on pattern match quality and relevance
        """
        if not extracted_data:
            return 0.1
        
        base_confidence = 0.3
        pattern_scores = {
            "emails": 0.25,
            "phones": 0.20,
            "urls": 0.15,
            "addresses": 0.20,
            "social_handles": 0.10,
            "linkedin_profiles": 0.15,
            "business_hours": 0.10,
            "prices": 0.15,
            "zip_codes": 0.05
        }
        
        # Calculate weighted score based on found patterns
        weighted_score = 0
        for pattern_name, matches in extracted_data.items():
            if pattern_name in pattern_scores:
                # Score based on pattern value and match count
                pattern_value = pattern_scores[pattern_name]
                match_bonus = min(len(matches) * 0.1, 0.3)  # Up to 30% bonus for multiple matches
                weighted_score += pattern_value + match_bonus
        
        # Purpose-specific bonuses
        purpose_bonuses = {
            "contact_discovery": 0.2 if "emails" in extracted_data or "phones" in extracted_data else 0,
            "lead_generation": 0.25 if "emails" in extracted_data and "phones" in extracted_data else 0,
            "business_listings": 0.2 if len(extracted_data) >= 3 else 0
        }
        
        purpose_bonus = purpose_bonuses.get(purpose, 0)
        
        final_confidence = min(base_confidence + weighted_score + purpose_bonus, 0.95)
        return final_confidence
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """
        Quick confidence estimation without full extraction
        """
        # Fast text sample for pattern detection
        text_sample = self._extract_text_content(html_content[:5000])  # First 5KB
        
        # Quick pattern checks
        pattern_indicators = {
            "emails": bool(re.search(r'@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text_sample)),
            "phones": bool(re.search(r'\(?\d{3}\)?[-\s.]?\d{3}[-\s.]?\d{4}', text_sample)),
            "urls": bool(re.search(r'https?://', text_sample))
        }
        
        # Calculate confidence based on pattern presence
        found_patterns = sum(pattern_indicators.values())
        
        if found_patterns >= 2:
            return 0.8  # High confidence
        elif found_patterns == 1:
            return 0.6  # Medium confidence
        else:
            # Check for business-like content
            business_indicators = ['contact', 'phone', 'email', 'address', 'location']
            if any(indicator in text_sample.lower() for indicator in business_indicators):
                return 0.4  # Low-medium confidence
            return 0.2  # Low confidence
    
    def supports_purpose(self, purpose: str) -> bool:
        """
        Regex strategy supports data extraction purposes
        """
        supported_purposes = [
            "contact_discovery", "lead_generation", "business_listings",
            "social_media_analysis", "e_commerce", "data_mining",
            "directory_scraping", "competitor_analysis"
        ]
        return purpose in supported_purposes or purpose == "default"
    
    def get_extraction_summary(self, result: StrategyResult) -> Dict[str, Any]:
        """
        Generate extraction summary for monitoring and optimization
        """
        extracted_data = result.extracted_data or {}
        
        summary = {
            "total_patterns_found": len(extracted_data),
            "total_matches": sum(len(matches) for matches in extracted_data.values()),
            "pattern_breakdown": {k: len(v) for k, v in extracted_data.items()},
            "execution_time_ms": round(result.execution_time * 1000, 2),
            "performance_category": "high_speed_regex"
        }
        
        # Performance rating
        if result.execution_time < 0.1:
            summary["performance_rating"] = "excellent"
        elif result.execution_time < 0.5:
            summary["performance_rating"] = "good"
        else:
            summary["performance_rating"] = "slow"
        
        return summary

class FormAutoStrategy(BaseExtractionStrategy):
    """
    Automated form detection, completion, and submission
    
    Examples:
    - Automatically fill out contact forms for lead generation
    - Submit search forms to access hidden content
    - Complete registration forms for data access
    - Handle multi-step form wizards
    """
    
    def __init__(self, form_data: Dict[str, Any] = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.form_data = form_data or {}
        
        # Common form field patterns
        self.field_patterns = {
            "email": [
                "email", "e-mail", "mail", "user_email", "contact_email"
            ],
            "name": [
                "name", "full_name", "first_name", "last_name", "username", "contact_name"
            ],
            "phone": [
                "phone", "telephone", "mobile", "contact_phone", "phone_number"
            ],
            "company": [
                "company", "organization", "business", "company_name"
            ],
            "message": [
                "message", "comment", "inquiry", "question", "description"
            ],
            "subject": [
                "subject", "topic", "title", "regarding"
            ]
        }
        
        # Default form data
        self.default_data = {
            "email": "contact@example.com",
            "name": "John Smith",
            "phone": "555-123-4567",
            "company": "Example Corp",
            "message": "I am interested in learning more about your services.",
            "subject": "Business Inquiry"
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect and analyze forms
            forms_data = self._analyze_forms(soup, url)
            
            # Determine which forms to fill
            target_forms = self._select_target_forms(forms_data, purpose)
            
            # Create form completion plan
            completion_plan = self._create_completion_plan(target_forms, context)
            
            extracted_data = {
                "forms_detected": len(forms_data),
                "target_forms": len(target_forms),
                "completion_plan": completion_plan,
                "forms_analysis": forms_data
            }
            
            # If this is just analysis, return the plan
            if context and context.get("analyze_only", True):
                extracted_data["action_required"] = "Form completion requires browser automation"
            
            confidence = 0.8 if target_forms else 0.3
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(target_forms),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="FormAutoStrategy",
                execution_time=execution_time,
                metadata={
                    "forms_found": len(forms_data),
                    "actionable_forms": len(target_forms)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="FormAutoStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _analyze_forms(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Analyze all forms on the page"""
        forms_data = []
        
        forms = soup.find_all('form')
        
        for i, form in enumerate(forms):
            form_info = {
                "form_id": form.get('id', f'form_{i}'),
                "action": form.get('action', ''),
                "method": form.get('method', 'GET').upper(),
                "fields": [],
                "submit_buttons": [],
                "form_type": "unknown"
            }
            
            # Make action URL absolute
            if form_info["action"]:
                form_info["action"] = urljoin(base_url, form_info["action"])
            
            # Analyze form fields
            fields = form.find_all(['input', 'textarea', 'select'])
            for field in fields:
                field_info = self._analyze_form_field(field)
                if field_info:
                    form_info["fields"].append(field_info)
            
            # Find submit buttons
            submit_buttons = form.find_all(['input', 'button'], type=['submit', 'button'])
            for button in submit_buttons:
                button_info = {
                    "type": button.get('type', 'button'),
                    "name": button.get('name', ''),
                    "value": button.get('value', ''),
                    "text": button.get_text(strip=True)
                }
                form_info["submit_buttons"].append(button_info)
            
            # Determine form type
            form_info["form_type"] = self._classify_form(form_info)
            
            forms_data.append(form_info)
        
        return forms_data
    
    def _analyze_form_field(self, field) -> Optional[Dict[str, Any]]:
        """Analyze individual form field"""
        field_type = field.get('type', 'text')
        
        # Skip hidden and submit fields
        if field_type in ['hidden', 'submit', 'button']:
            return None
        
        field_info = {
            "tag": field.name,
            "type": field_type,
            "name": field.get('name', ''),
            "id": field.get('id', ''),
            "placeholder": field.get('placeholder', ''),
            "required": field.has_attr('required'),
            "value": field.get('value', ''),
            "label": self._find_field_label(field),
            "field_purpose": "unknown"
        }
        
        # Determine field purpose
        field_info["field_purpose"] = self._classify_field_purpose(field_info)
        
        return field_info
    
    def _find_field_label(self, field) -> str:
        """Find label associated with form field"""
        # Check for label tag
        field_id = field.get('id')
        if field_id:
            label = field.find_parent().find('label', attrs={'for': field_id})
            if label:
                return label.get_text(strip=True)
        
        # Check for wrapping label
        label_parent = field.find_parent('label')
        if label_parent:
            return label_parent.get_text(strip=True).replace(field.get('value', ''), '').strip()
        
        # Check for adjacent text
        previous = field.find_previous_sibling(string=True)
        if previous:
            text = previous.strip()
            if text and len(text) < 50:
                return text
        
        return ""
    
    def _classify_field_purpose(self, field_info: Dict[str, Any]) -> str:
        """Classify the purpose of a form field"""
        
        # Combine all text sources for analysis
        text_sources = [
            field_info.get("name", "").lower(),
            field_info.get("id", "").lower(),
            field_info.get("placeholder", "").lower(),
            field_info.get("label", "").lower()
        ]
        
        combined_text = " ".join(text_sources)
        
        # Check against known patterns
        for purpose, patterns in self.field_patterns.items():
            if any(pattern in combined_text for pattern in patterns):
                return purpose
        
        # Special cases based on field type
        field_type = field_info.get("type", "")
        if field_type == "email":
            return "email"
        elif field_type == "tel":
            return "phone"
        elif field_type == "password":
            return "password"
        elif field_info.get("tag") == "textarea":
            return "message"
        
        return "unknown"
    
    def _classify_form(self, form_info: Dict[str, Any]) -> str:
        """Classify the type of form"""
        
        # Analyze field purposes
        field_purposes = [field["field_purpose"] for field in form_info["fields"]]
        
        # Contact forms
        if "email" in field_purposes and ("message" in field_purposes or "name" in field_purposes):
            return "contact_form"
        
        # Search forms
        if any("search" in field.get("name", "").lower() for field in form_info["fields"]):
            return "search_form"
        
        # Login forms
        if "password" in field_purposes and ("email" in field_purposes or "name" in field_purposes):
            return "login_form"
        
        # Registration forms
        if field_purposes.count("email") >= 1 and len(field_purposes) > 3:
            return "registration_form"
        
        # Newsletter forms
        if "email" in field_purposes and len(field_purposes) <= 2:
            return "newsletter_form"
        
        return "unknown"
    
    def _select_target_forms(self, forms_data: List[Dict[str, Any]], purpose: str) -> List[Dict[str, Any]]:
        """Select forms that match the extraction purpose"""
        
        target_forms = []
        
        for form in forms_data:
            form_type = form["form_type"]
            
            # Select forms based on purpose
            if purpose == "contact_discovery" and form_type in ["contact_form", "newsletter_form"]:
                target_forms.append(form)
            elif purpose == "lead_generation" and form_type in ["contact_form", "registration_form"]:
                target_forms.append(form)
            elif purpose == "data_access" and form_type in ["search_form", "registration_form"]:
                target_forms.append(form)
            elif purpose == "form_automation":
                target_forms.append(form)  # Include all forms
        
        return target_forms
    
    def _create_completion_plan(self, target_forms: List[Dict[str, Any]], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create plan for completing target forms"""
        
        completion_plan = []
        
        # Get form data from context or use defaults
        form_data = context.get("form_data", {}) if context else {}
        combined_data = {**self.default_data, **self.form_data, **form_data}
        
        for form in target_forms:
            plan = {
                "form_id": form["form_id"],
                "form_type": form["form_type"],
                "action": form["action"],
                "method": form["method"],
                "completion_steps": []
            }
            
            # Create completion steps for each field
            for field in form["fields"]:
                field_purpose = field["field_purpose"]
                
                if field_purpose in combined_data:
                    step = {
                        "action": "fill_field",
                        "selector": self._create_field_selector(field),
                        "value": combined_data[field_purpose],
                        "field_name": field["name"],
                        "field_type": field["type"]
                    }
                    plan["completion_steps"].append(step)
            
            # Add submit step
            if form["submit_buttons"]:
                submit_button = form["submit_buttons"][0]  # Use first submit button
                plan["completion_steps"].append({
                    "action": "submit_form",
                    "button_text": submit_button["text"],
                    "button_type": submit_button["type"]
                })
            
            completion_plan.append(plan)
        
        return completion_plan
    
    def _create_field_selector(self, field: Dict[str, Any]) -> str:
        """Create CSS selector for form field"""
        
        if field["id"]:
            return f"#{field['id']}"
        elif field["name"]:
            return f"[name='{field['name']}']"
        else:
            # Fallback selector
            return f"{field['tag']}[type='{field['type']}']"
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Form strategy confidence based on form presence"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        forms = soup.find_all('form')
        
        if not forms:
            return 0.1
        
        # Higher confidence for relevant purposes
        if purpose in ["contact_discovery", "lead_generation", "form_automation"]:
            return 0.8
        
        return 0.5
    
    def supports_purpose(self, purpose: str) -> bool:
        """Form strategy supports automation purposes"""
        supported_purposes = [
            "contact_discovery", "lead_generation", "form_automation",
            "data_access", "registration_automation"
        ]
        return purpose in supported_purposes

class PaginationStrategy(BaseExtractionStrategy):
    """
    Handle paginated content extraction across multiple pages
    
    Examples:
    - Extract all products from multi-page catalogs
    - Scrape all search results across pagination
    - Collect complete datasets from paginated APIs
    - Handle infinite scroll and load-more buttons
    """
    
    def __init__(self, max_pages: int = 10, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.max_pages = max_pages
        
        # Common pagination patterns
        self.pagination_selectors = {
            "next_button": [
                "a[rel='next']",
                ".next, .next-page",
                "[aria-label*='next']",
                ".pagination .next",
                "a:contains('Next')",
                ".pager-next a"
            ],
            "page_numbers": [
                ".pagination a",
                ".page-numbers a",
                ".pager a",
                "[aria-label*='page']"
            ],
            "current_page": [
                ".pagination .current",
                ".page-numbers .current",
                ".active",
                "[aria-current='page']"
            ],
            "load_more": [
                ".load-more",
                "[data-testid*='load-more']",
                "button:contains('Load More')",
                ".show-more"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Analyze pagination structure
            pagination_info = self._analyze_pagination(soup, url)
            
            # Extract data from current page
            current_page_data = self._extract_current_page_data(soup, purpose)
            
            # Create pagination plan
            pagination_plan = self._create_pagination_plan(pagination_info, url, purpose)
            
            extracted_data = {
                "current_page_data": current_page_data,
                "pagination_info": pagination_info,
                "pagination_plan": pagination_plan,
                "total_estimated_pages": pagination_info.get("total_pages", 1)
            }
            
            # If context requests full extraction, note it requires automation
            if context and context.get("extract_all_pages", False):
                extracted_data["automation_required"] = "Full pagination extraction requires browser automation"
            
            confidence = 0.8 if pagination_info.get("has_pagination") else 0.3
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(current_page_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="PaginationStrategy",
                execution_time=execution_time,
                metadata={
                    "has_pagination": pagination_info.get("has_pagination", False),
                    "pagination_type": pagination_info.get("type", "none")
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="PaginationStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _analyze_pagination(self, soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
        """Analyze pagination structure on the page"""
        
        pagination_info = {
            "has_pagination": False,
            "type": "none",
            "next_url": None,
            "page_urls": [],
            "current_page": 1,
            "total_pages": 1
        }
        
        # Check for next button
        next_button = self._find_pagination_element(soup, "next_button")
        if next_button:
            pagination_info["has_pagination"] = True
            pagination_info["type"] = "next_button"
            
            next_href = next_button.get('href')
            if next_href:
                pagination_info["next_url"] = urljoin(base_url, next_href)
        
        # Check for page numbers
        page_elements = self._find_pagination_elements(soup, "page_numbers")
        if page_elements:
            pagination_info["has_pagination"] = True
            if pagination_info["type"] == "none":
                pagination_info["type"] = "numbered_pages"
            
            page_urls = []
            for elem in page_elements:
                href = elem.get('href')
                if href:
                    page_urls.append(urljoin(base_url, href))
            
            pagination_info["page_urls"] = page_urls
            pagination_info["total_pages"] = len(page_urls)
        
        # Check current page
        current_elem = self._find_pagination_element(soup, "current_page")
        if current_elem:
            current_text = current_elem.get_text(strip=True)
            try:
                pagination_info["current_page"] = int(current_text)
            except ValueError:
                pass
        
        # Check for load more button
        load_more = self._find_pagination_element(soup, "load_more")
        if load_more:
            pagination_info["has_pagination"] = True
            pagination_info["type"] = "load_more"
            pagination_info["load_more_present"] = True
        
        # Try to extract total pages from pagination text
        pagination_text = self._get_pagination_text(soup)
        if pagination_text:
            total_match = re.search(r'of (\d+)', pagination_text)
            if total_match:
                pagination_info["total_pages"] = int(total_match.group(1))
        
        return pagination_info
    
    def _find_pagination_element(self, soup: BeautifulSoup, element_type: str):
        """Find pagination element using multiple selectors"""
        selectors = self.pagination_selectors.get(element_type, [])
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element
        
        return None
    
    def _find_pagination_elements(self, soup: BeautifulSoup, element_type: str):
        """Find multiple pagination elements"""
        selectors = self.pagination_selectors.get(element_type, [])
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                return elements
        
        return []
    
    def _get_pagination_text(self, soup: BeautifulSoup) -> str:
        """Get pagination text for analysis"""
        pagination_containers = soup.select(".pagination, .pager, .page-info")
        
        for container in pagination_containers:
            text = container.get_text(strip=True)
            if text:
                return text
        
        return ""
    
    def _extract_current_page_data(self, soup: BeautifulSoup, purpose: str) -> Dict[str, Any]:
        """Extract data from current page"""
        
        # This is a simplified extraction - in practice, would use appropriate strategy
        data = {"items": []}
        
        # Look for common item containers
        item_selectors = [
            ".item, .result, .product",
            ".listing, .card",
            "[data-testid*='item'], [data-testid*='result']"
        ]
        
        for selector in item_selectors:
            items = soup.select(selector)
            if items:
                for item in items[:50]:  # Limit per page
                    item_data = self._extract_item_data(item)
                    if item_data:
                        data["items"].append(item_data)
                break
        
        data["items_count"] = len(data["items"])
        return data
    
    def _extract_item_data(self, item_element) -> Dict[str, Any]:
        """Extract basic data from item element"""
        
        item_data = {}
        
        # Title
        title_elem = item_element.select_one("h1, h2, h3, .title, .name")
        if title_elem:
            item_data["title"] = title_elem.get_text(strip=True)
        
        # Link
        link_elem = item_element.select_one("a")
        if link_elem:
            item_data["link"] = link_elem.get('href', '')
        
        # Price
        price_elem = item_element.select_one(".price, .cost, .amount")
        if price_elem:
            item_data["price"] = price_elem.get_text(strip=True)
        
        # Description
        desc_elem = item_element.select_one(".description, .summary")
        if desc_elem:
            item_data["description"] = desc_elem.get_text(strip=True)[:200]
        
        return item_data if item_data else None
    
    def _create_pagination_plan(self, pagination_info: Dict[str, Any], base_url: str, purpose: str) -> Dict[str, Any]:
        """Create plan for paginated extraction"""
        
        plan = {
            "strategy": "none",
            "estimated_pages": pagination_info.get("total_pages", 1),
            "urls_to_process": [],
            "automation_steps": []
        }
        
        if not pagination_info.get("has_pagination"):
            return plan
        
        pagination_type = pagination_info.get("type")
        
        if pagination_type == "numbered_pages":
            plan["strategy"] = "url_based"
            plan["urls_to_process"] = pagination_info.get("page_urls", [])[:self.max_pages]
        
        elif pagination_type == "next_button":
            plan["strategy"] = "sequential_navigation"
            plan["automation_steps"] = [
                {
                    "action": "click_next",
                    "selector": self.pagination_selectors["next_button"][0],
                    "repeat": min(self.max_pages - 1, 10)
                }
            ]
        
        elif pagination_type == "load_more":
            plan["strategy"] = "load_more_clicks"
            plan["automation_steps"] = [
                {
                    "action": "click_load_more",
                    "selector": self.pagination_selectors["load_more"][0],
                    "repeat": min(self.max_pages - 1, 20),
                    "wait_between": 2000  # 2 second wait
                }
            ]
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Pagination strategy confidence"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check for pagination indicators
        pagination_indicators = [
            ".pagination", ".pager", ".page-numbers",
            "a[rel='next']", ".next", ".load-more"
        ]
        
        has_pagination = any(soup.select(indicator) for indicator in pagination_indicators)
        
        if has_pagination:
            return 0.9
        
        # Check for multiple items (suggests possible pagination)
        item_containers = soup.select(".item, .result, .product, .listing")
        if len(item_containers) > 10:
            return 0.6
        
        return 0.2
    
    def supports_purpose(self, purpose: str) -> bool:
        """Pagination supports data collection purposes"""
        supported_purposes = [
            "business_listings", "product_data", "search_results",
            "directory_mining", "catalog_extraction", "data_collection"
        ]
        return purpose in supported_purposes

class InfiniteScrollStrategy(BaseExtractionStrategy):
    """
    Handle infinite scroll and dynamic content loading
    
    Examples:
    - Extract all posts from social media feeds
    - Scrape complete product catalogs with lazy loading
    - Handle dynamic search results that load on scroll
    - Collect all items from infinite scroll lists
    """
    
    def __init__(self, max_scrolls: int = 20, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.max_scrolls = max_scrolls
        
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect infinite scroll indicators
            scroll_info = self._detect_infinite_scroll(soup, html_content)
            
            # Extract current visible content
            current_data = self._extract_visible_content(soup, purpose)
            
            # Create scroll automation plan
            scroll_plan = self._create_scroll_plan(scroll_info, purpose)
            
            extracted_data = {
                "current_data": current_data,
                "scroll_detected": scroll_info.get("has_infinite_scroll", False),
                "scroll_plan": scroll_plan,
                "automation_required": "Infinite scroll extraction requires browser automation"
            }
            
            confidence = 0.8 if scroll_info.get("has_infinite_scroll") else 0.3
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(current_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="InfiniteScrollStrategy",
                execution_time=execution_time,
                metadata={
                    "infinite_scroll_detected": scroll_info.get("has_infinite_scroll", False),
                    "loading_indicators": scroll_info.get("loading_indicators", [])
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="InfiniteScrollStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _detect_infinite_scroll(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
        """Detect infinite scroll patterns"""
        
        scroll_info = {
            "has_infinite_scroll": False,
            "loading_indicators": [],
            "scroll_triggers": [],
            "container_selectors": []
        }
        
        # Check for loading indicators
        loading_selectors = [
            ".loading", ".spinner", ".loader",
            "[data-testid*='loading']", "[data-testid*='spinner']",
            ".infinite-loading", ".load-indicator"
        ]
        
        for selector in loading_selectors:
            elements = soup.select(selector)
            if elements:
                scroll_info["loading_indicators"].append(selector)
                scroll_info["has_infinite_scroll"] = True
        
        # Check JavaScript for infinite scroll patterns
        if any(pattern in html_content for pattern in [
            "infinite", "scroll", "lazy", "load-more",
            "IntersectionObserver", "onscroll"
        ]):
            scroll_info["has_infinite_scroll"] = True
        
        # Look for common infinite scroll containers
        container_patterns = [
            ".feed", ".timeline", ".infinite-scroll",
            ".results-container", ".items-container",
            "[data-testid*='feed']", "[data-testid*='timeline']"
        ]
        
        for pattern in container_patterns:
            if soup.select(pattern):
                scroll_info["container_selectors"].append(pattern)
        
        # Check for scroll trigger elements
        trigger_patterns = [
            ".load-more-trigger", ".scroll-trigger",
            "[data-scroll-trigger]", ".infinite-trigger"
        ]
        
        for pattern in trigger_patterns:
            if soup.select(pattern):
                scroll_info["scroll_triggers"].append(pattern)
        
        return scroll_info
    
    def _extract_visible_content(self, soup: BeautifulSoup, purpose: str) -> Dict[str, Any]:
        """Extract currently visible content"""
        
        data = {"items": [], "containers_found": []}
        
        # Common content item patterns
        item_patterns = [
            ".post, .item, .card",
            ".result, .listing",
            "[data-testid*='post'], [data-testid*='item']",
            ".feed-item, .timeline-item"
        ]
        
        for pattern in item_patterns:
            items = soup.select(pattern)
            if items:
                data["containers_found"].append(pattern)
                
                for item in items:
                    item_data = self._extract_scroll_item(item)
                    if item_data:
                        data["items"].append(item_data)
                
                break  # Use first successful pattern
        
        data["items_count"] = len(data["items"])
        return data
    
    def _extract_scroll_item(self, item_element) -> Dict[str, Any]:
        """Extract data from scroll item"""
        
        item_data = {}
        
        # Text content
        text_elem = item_element.select_one(".content, .text, .description, p")
        if text_elem:
            item_data["text"] = text_elem.get_text(strip=True)[:500]
        
        # Title/header
        title_elem = item_element.select_one("h1, h2, h3, .title, .header")
        if title_elem:
            item_data["title"] = title_elem.get_text(strip=True)
        
        # Author/source
        author_elem = item_element.select_one(".author, .user, .source")
        if author_elem:
            item_data["author"] = author_elem.get_text(strip=True)
        
        # Timestamp
        time_elem = item_element.select_one("time, .timestamp, .date")
        if time_elem:
            item_data["timestamp"] = time_elem.get_text(strip=True)
        
        # Image
        img_elem = item_element.select_one("img")
        if img_elem:
            item_data["image"] = img_elem.get('src', '')
        
        # Link
        link_elem = item_element.select_one("a")
        if link_elem:
            item_data["link"] = link_elem.get('href', '')
        
        return item_data if item_data else None
    
    def _create_scroll_plan(self, scroll_info: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Create infinite scroll automation plan"""
        
        plan = {
            "automation_steps": [],
            "estimated_scrolls": self.max_scrolls,
            "wait_between_scrolls": 2000,  # 2 seconds
            "success_indicators": []
        }
        
        if not scroll_info.get("has_infinite_scroll"):
            return plan
        
        # Basic scroll strategy
        plan["automation_steps"] = [
            {
                "action": "scroll_to_bottom",
                "repeat": self.max_scrolls,
                "wait_for_loading": True,
                "loading_selectors": scroll_info.get("loading_indicators", [])
            }
        ]
        
        # If load triggers exist, click them instead
        if scroll_info.get("scroll_triggers"):
            plan["automation_steps"] = [
                {
                    "action": "click_triggers",
                    "selectors": scroll_info["scroll_triggers"],
                    "repeat": self.max_scrolls,
                    "wait_between": 2000
                }
            ]
        
        # Define success indicators
        plan["success_indicators"] = [
            "no_new_content_loaded",
            "end_of_feed_message",
            "max_scrolls_reached"
        ]
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Infinite scroll strategy confidence"""
        
        # Check for infinite scroll indicators
        scroll_indicators = [
            "infinite", "scroll", "lazy", "feed", "timeline"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for indicator in scroll_indicators if indicator in content_lower)
        
        confidence = 0.3 + (indicator_count * 0.1)
        
        # Higher confidence for social media and feed-based sites
        if any(pattern in url for pattern in ["twitter", "facebook", "instagram", "linkedin", "feed"]):
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Infinite scroll supports content collection purposes"""
        supported_purposes = [
            "social_media_analysis", "content_collection", "feed_monitoring",
            "news_content", "product_data", "user_generated_content"
        ]
        return purpose in supported_purposes

class AuthenticationStrategy(BaseExtractionStrategy):
    """
    Handle login and authentication workflows
    
    Examples:
    - Login to LinkedIn for profile access
    - Authenticate with Google/Facebook OAuth
    - Handle two-factor authentication
    - Maintain session across multiple requests
    - Handle subscription-based content access
    """
    
    def __init__(self, credentials: Dict[str, str] = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.credentials = credentials or {}
        
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect authentication requirements
            auth_info = self._detect_authentication_requirements(soup, html_content, url)
            
            # Create authentication plan
            auth_plan = self._create_authentication_plan(auth_info, url, context)
            
            extracted_data = {
                "authentication_required": auth_info.get("requires_auth", False),
                "auth_type": auth_info.get("auth_type", "none"),
                "auth_plan": auth_plan,
                "login_form_detected": auth_info.get("has_login_form", False),
                "oauth_providers": auth_info.get("oauth_providers", [])
            }
            
            confidence = 0.9 if auth_info.get("requires_auth") else 0.2
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=True,  # Always successful at detecting auth requirements
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="AuthenticationStrategy",
                execution_time=execution_time,
                metadata={
                    "auth_detected": auth_info.get("requires_auth", False),
                    "auth_complexity": auth_info.get("complexity", "simple")
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="AuthenticationStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _detect_authentication_requirements(self, soup: BeautifulSoup, html_content: str, url: str) -> Dict[str, Any]:
        """Detect authentication requirements and methods"""
        
        auth_info = {
            "requires_auth": False,
            "auth_type": "none",
            "has_login_form": False,
            "oauth_providers": [],
            "complexity": "simple"
        }
        
        # Check for login indicators
        login_indicators = [
            "login", "sign in", "log in", "authentication",
            "please sign in", "access denied", "unauthorized"
        ]
        
        page_text = html_content.lower()
        if any(indicator in page_text for indicator in login_indicators):
            auth_info["requires_auth"] = True
        
        # Check for login forms
        login_forms = soup.select("form:has([type='password']), .login-form, .signin-form")
        if login_forms:
            auth_info["has_login_form"] = True
            auth_info["requires_auth"] = True
            auth_info["auth_type"] = "form_login"
        
        # Check for OAuth providers
        oauth_patterns = {
            "google": ["google", "gmail"],
            "facebook": ["facebook", "fb"],
            "twitter": ["twitter"],
            "linkedin": ["linkedin"],
            "microsoft": ["microsoft", "outlook"],
            "github": ["github"]
        }
        
        for provider, patterns in oauth_patterns.items():
            if any(pattern in page_text for pattern in patterns):
                if any(oauth_term in page_text for oauth_term in ["oauth", "sign in with", "continue with"]):
                    auth_info["oauth_providers"].append(provider)
                    auth_info["auth_type"] = "oauth"
                    auth_info["requires_auth"] = True
        
        # Check for 2FA indicators
        tfa_indicators = ["two-factor", "2fa", "verification code", "authenticator"]
        if any(indicator in page_text for indicator in tfa_indicators):
            auth_info["complexity"] = "two_factor"
        
        # Check for subscription walls
        subscription_indicators = ["subscribe", "premium", "upgrade", "paywall"]
        if any(indicator in page_text for indicator in subscription_indicators):
            auth_info["auth_type"] = "subscription"
            auth_info["complexity"] = "subscription_required"
        
        # Platform-specific detection
        auth_info.update(self._detect_platform_specific_auth(url, soup))
        
        return auth_info
    
    def _detect_platform_specific_auth(self, url: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Detect platform-specific authentication patterns"""
        
        platform_info = {}
        
        if "linkedin.com" in url:
            if soup.select(".authwall, .guest-homepage"):
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "linkedin_login",
                    "complexity": "professional_network"
                })
        
        elif "facebook.com" in url:
            if "login" in soup.get_text().lower():
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "facebook_login",
                    "complexity": "social_network"
                })
        
        elif "twitter.com" in url or "x.com" in url:
            if soup.select(".login-form, .signin-form"):
                platform_info.update({
                    "requires_auth": True,
                    "auth_type": "twitter_login",
                    "complexity": "social_network"
                })
        
        return platform_info
    
    def _create_authentication_plan(self, auth_info: Dict[str, Any], url: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create authentication execution plan"""
        
        plan = {
            "steps": [],
            "estimated_time": 30,  # seconds
            "success_indicators": [],
            "failure_indicators": []
        }
        
        if not auth_info.get("requires_auth"):
            return plan
        
        auth_type = auth_info.get("auth_type")
        credentials = context.get("credentials", {}) if context else {}
        combined_creds = {**self.credentials, **credentials}
        
        if auth_type == "form_login":
            plan["steps"] = [
                {
                    "action": "fill_username",
                    "selector": "[name='username'], [name='email'], [type='email']",
                    "value": combined_creds.get("username", "")
                },
                {
                    "action": "fill_password",
                    "selector": "[name='password'], [type='password']",
                    "value": combined_creds.get("password", "")
                },
                {
                    "action": "submit_form",
                    "selector": "[type='submit'], .login-button, .signin-button"
                }
            ]
        
        elif auth_type == "oauth":
            provider = auth_info.get("oauth_providers", ["google"])[0]
            plan["steps"] = [
                {
                    "action": "click_oauth_button",
                    "selector": f".{provider}-login, [data-provider='{provider}']",
                    "provider": provider
                },
                {
                    "action": "handle_oauth_redirect",
                    "wait_for_redirect": True,
                    "timeout": 30000
                }
            ]
        
        # Add 2FA handling if needed
        if auth_info.get("complexity") == "two_factor":
            plan["steps"].append({
                "action": "handle_2fa",
                "selector": "[name='code'], [name='verification_code']",
                "wait_for_prompt": True,
                "code_source": combined_creds.get("2fa_method", "manual")
            })
        
        # Define success/failure indicators
        plan["success_indicators"] = [
            "dashboard", "profile", "logged in", "welcome",
            ".user-menu", ".logout", ".account-menu"
        ]
        
        plan["failure_indicators"] = [
            "invalid", "incorrect", "failed", "error",
            ".error-message", ".login-error"
        ]
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Authentication strategy confidence"""
        
        # Check for authentication indicators
        auth_indicators = [
            "login", "sign in", "authentication", "password",
            "access denied", "unauthorized"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for indicator in auth_indicators if indicator in content_lower)
        
        confidence = min(indicator_count * 0.2, 0.9)
        
        # Higher confidence for known platforms requiring auth
        protected_domains = ["linkedin.com", "facebook.com", "twitter.com"]
        if any(domain in url for domain in protected_domains):
            confidence += 0.3
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Authentication supports access-controlled purposes"""
        supported_purposes = [
            "profile_info", "social_media_analysis", "premium_content",
            "subscription_data", "protected_resources", "member_content"
        ]
        return purpose in supported_purposes

class CaptchaStrategy(BaseExtractionStrategy):
    """
    Handle CAPTCHA detection and solving
    
    Examples:
    - Detect reCAPTCHA and hCaptcha challenges
    - Integrate with CAPTCHA solving services
    - Handle image-based CAPTCHAs
    - Manage CAPTCHA retry logic
    """
    
    def __init__(self, captcha_service_key: str = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.captcha_service_key = captcha_service_key
        
        # CAPTCHA detection patterns
        self.captcha_indicators = {
            "recaptcha": [
                ".g-recaptcha", "[data-sitekey]", 
                "iframe[src*='recaptcha']", "#recaptcha"
            ],
            "hcaptcha": [
                ".h-captcha", "[data-sitekey*='hcaptcha']",
                "iframe[src*='hcaptcha']"
            ],
            "image_captcha": [
                ".captcha-image", "[src*='captcha']",
                ".verification-image", "[alt*='captcha']"
            ],
            "text_captcha": [
                "[name*='captcha']", ".captcha-input",
                "[placeholder*='captcha']"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect CAPTCHA types
            captcha_info = self._detect_captcha_types(soup, html_content)
            
            # Create solving plan
            solving_plan = self._create_captcha_solving_plan(captcha_info, context)
            
            extracted_data = {
                "captcha_detected": captcha_info.get("has_captcha", False),
                "captcha_types": captcha_info.get("types", []),
                "solving_plan": solving_plan,
                "service_required": captcha_info.get("has_captcha", False)
            }
            
            confidence = 0.9 if captcha_info.get("has_captcha") else 0.1
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=True,  # Always successful at detection
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="CaptchaStrategy",
                execution_time=execution_time,
                metadata={
                    "captcha_present": captcha_info.get("has_captcha", False),
                    "complexity": captcha_info.get("complexity", "none")
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="CaptchaStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _detect_captcha_types(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
        """Detect CAPTCHA types and characteristics"""
        
        captcha_info = {
            "has_captcha": False,
            "types": [],
            "complexity": "none",
            "site_keys": {},
            "elements": {}
        }
        
        # Check each CAPTCHA type
        for captcha_type, selectors in self.captcha_indicators.items():
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    captcha_info["has_captcha"] = True
                    captcha_info["types"].append(captcha_type)
                    captcha_info["elements"][captcha_type] = selector
                    
                    # Extract site keys for reCAPTCHA/hCaptcha
                    if captcha_type in ["recaptcha", "hcaptcha"]:
                        site_key = self._extract_site_key(elements[0], captcha_type)
                        if site_key:
                            captcha_info["site_keys"][captcha_type] = site_key
                    
                    break
        
        # Determine complexity
        if "recaptcha" in captcha_info["types"]:
            captcha_info["complexity"] = "recaptcha_v2_or_v3"
        elif "hcaptcha" in captcha_info["types"]:
            captcha_info["complexity"] = "hcaptcha"
        elif "image_captcha" in captcha_info["types"]:
            captcha_info["complexity"] = "image_recognition"
        elif "text_captcha" in captcha_info["types"]:
            captcha_info["complexity"] = "text_input"
        
        return captcha_info
    
    def _extract_site_key(self, element, captcha_type: str) -> Optional[str]:
        """Extract site key from CAPTCHA element"""
        
        # Check data-sitekey attribute
        site_key = element.get('data-sitekey')
        if site_key:
            return site_key
        
        # Check parent elements
        parent = element.find_parent()
        if parent:
            site_key = parent.get('data-sitekey')
            if site_key:
                return site_key
        
        # Check iframe src for embedded CAPTCHAs
        if element.name == 'iframe':
            src = element.get('src', '')
            if 'sitekey=' in src:
                import re
                match = re.search(r'sitekey=([^&]+)', src)
                if match:
                    return match.group(1)
        
        return None
    
    def _create_captcha_solving_plan(self, captcha_info: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create CAPTCHA solving plan"""
        
        plan = {
            "solving_method": "none",
            "steps": [],
            "estimated_time": 0,
            "service_config": {}
        }
        
        if not captcha_info.get("has_captcha"):
            return plan
        
        captcha_types = captcha_info.get("types", [])
        complexity = captcha_info.get("complexity", "none")
        
        if "recaptcha" in captcha_types:
            plan["solving_method"] = "2captcha_recaptcha"
            plan["estimated_time"] = 30  # seconds
            plan["steps"] = [
                {
                    "action": "submit_to_service",
                    "service": "2captcha",
                    "captcha_type": "recaptcha_v2",
                    "site_key": captcha_info.get("site_keys", {}).get("recaptcha"),
                    "page_url": context.get("url") if context else None
                },
                {
                    "action": "wait_for_solution",
                    "timeout": 120  # 2 minutes max
                },
                {
                    "action": "submit_solution",
                    "selector": "[name='g-recaptcha-response']"
                }
            ]
        
        elif "hcaptcha" in captcha_types:
            plan["solving_method"] = "2captcha_hcaptcha"
            plan["estimated_time"] = 30
            plan["steps"] = [
                {
                    "action": "submit_to_service",
                    "service": "2captcha",
                    "captcha_type": "hcaptcha",
                    "site_key": captcha_info.get("site_keys", {}).get("hcaptcha"),
                    "page_url": context.get("url") if context else None
                },
                {
                    "action": "wait_for_solution",
                    "timeout": 120
                },
                {
                    "action": "submit_solution",
                    "selector": "[name='h-captcha-response']"
                }
            ]
        
        elif "image_captcha" in captcha_types:
            plan["solving_method"] = "image_recognition"
            plan["estimated_time"] = 20
            plan["steps"] = [
                {
                    "action": "capture_image",
                    "selector": captcha_info.get("elements", {}).get("image_captcha")
                },
                {
                    "action": "solve_image",
                    "service": "2captcha_image"
                },
                {
                    "action": "input_solution",
                    "selector": "[name*='captcha'], .captcha-input"
                }
            ]
        
        elif "text_captcha" in captcha_types:
            plan["solving_method"] = "text_recognition"
            plan["estimated_time"] = 10
            plan["steps"] = [
                {
                    "action": "extract_question",
                    "selector": ".captcha-question, .captcha-text"
                },
                {
                    "action": "solve_text",
                    "method": "simple_math_or_lookup"
                },
                {
                    "action": "input_solution",
                    "selector": "[name*='captcha'], .captcha-input"
                }
            ]
        
        # Add service configuration
        if self.captcha_service_key:
            plan["service_config"] = {
                "api_key": self.captcha_service_key,
                "service_url": "http://2captcha.com/in.php",
                "result_url": "http://2captcha.com/res.php"
            }
        else:
            plan["service_config"] = {
                "note": "CAPTCHA service API key required for automated solving"
            }
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """CAPTCHA strategy confidence"""
        
        # Check for CAPTCHA indicators
        captcha_terms = [
            "captcha", "recaptcha", "hcaptcha", "verification",
            "prove you're human", "security check"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for term in captcha_terms if term in content_lower)
        
        confidence = min(indicator_count * 0.3, 0.9)
        
        # Check for actual CAPTCHA elements
        soup = BeautifulSoup(html_content, 'html.parser')
        if soup.select(".g-recaptcha, .h-captcha"):
            confidence = 0.95
        
        return confidence
    
    def supports_purpose(self, purpose: str) -> bool:
        """CAPTCHA strategy supports access purposes"""
        supported_purposes = [
            "form_automation", "data_access", "protected_content",
            "anti_bot_circumvention", "verification_handling"
        ]
        return purpose in supported_purposes
