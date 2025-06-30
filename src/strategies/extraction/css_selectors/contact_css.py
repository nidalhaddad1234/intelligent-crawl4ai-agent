#!/usr/bin/env python3
"""
Contact CSS Strategy
Specialized for extracting contact information from any website

Examples:
- Find all emails, phones, addresses on company websites
- Extract social media links
- Get contact forms and support information
"""

import re
import time
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.extraction.css_selectors.contact")


class ContactCSSStrategy(BaseExtractionStrategy):
    """
    Specialized for extracting contact information from any website
    
    Examples:
    - Find all emails, phones, addresses on company websites
    - Extract social media links
    - Get contact forms and support information
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        
        self.contact_selectors = {
            "emails": [
                "a[href^='mailto:']",
                "[data-email]",
                ".email, .e-mail"
            ],
            "phones": [
                "a[href^='tel:']",
                ".phone, .telephone, .tel",
                "[data-phone], [data-tel]"
            ],
            "addresses": [
                ".address, .location",
                "[itemprop='address']",
                ".contact-address, .office-address"
            ],
            "social_links": [
                "a[href*='facebook.com'], a[href*='twitter.com'], a[href*='linkedin.com']",
                "a[href*='instagram.com'], a[href*='youtube.com']",
                ".social-links a, .social a"
            ],
            "contact_forms": [
                "form[action*='contact'], form[id*='contact']",
                ".contact-form, .contact-us-form"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = {}
            
            # Extract all contact information
            for field, selectors in self.contact_selectors.items():
                values = self._extract_multiple_values(soup, selectors, field)
                if values:
                    extracted_data[field] = values
            
            # Text-based extraction for emails and phones
            text_contacts = self._extract_from_text(html_content)
            if text_contacts:
                for key, values in text_contacts.items():
                    if key in extracted_data:
                        # Merge and deduplicate
                        all_values = extracted_data[key] + values
                        extracted_data[key] = list(set(all_values))
                    else:
                        extracted_data[key] = values
            
            confidence = self.calculate_confidence(
                extracted_data,
                ["emails", "phones", "addresses"]
            )
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="ContactCSSStrategy",
                execution_time=execution_time,
                metadata={
                    "total_contacts_found": sum(len(v) for v in extracted_data.values()),
                    "contact_types": list(extracted_data.keys())
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="ContactCSSStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_multiple_values(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> List[str]:
        """Extract multiple values for a field type"""
        values = []
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    if field_type == "emails":
                        href = element.get('href', '')
                        if href.startswith('mailto:'):
                            email = href.replace('mailto:', '').split('?')[0]
                            if '@' in email:
                                values.append(email)
                        else:
                            text = element.get_text(strip=True)
                            if '@' in text:
                                values.append(text)
                    
                    elif field_type == "phones":
                        href = element.get('href', '')
                        if href.startswith('tel:'):
                            phone = href.replace('tel:', '')
                            values.append(phone)
                        else:
                            text = element.get_text(strip=True)
                            if text:
                                values.append(text)
                    
                    elif field_type == "social_links":
                        href = element.get('href', '')
                        if href and any(platform in href for platform in 
                                      ['facebook.com', 'twitter.com', 'linkedin.com', 
                                       'instagram.com', 'youtube.com']):
                            values.append(href)
                    
                    else:
                        text = element.get_text(strip=True)
                        if text:
                            values.append(text)
                            
            except Exception:
                continue
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(values))
    
    def _extract_from_text(self, html_content: str) -> Dict[str, List[str]]:
        """Extract emails and phones from plain text using regex"""
        
        # Get text content only
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        
        contacts = {}
        
        # Email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contacts["emails"] = list(set(emails))
        
        # Phone regex (multiple formats)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',   # (123) 456-7890
            r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'  # International
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        if phones:
            contacts["phones"] = list(set(phones))
        
        return contacts
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Estimate confidence for contact extraction"""
        
        # Contact extraction can work on any page
        confidence = 0.5
        
        # Check for contact-specific content
        contact_indicators = [
            "contact", "email", "phone", "address", "social"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for indicator in contact_indicators 
                            if indicator in content_lower)
        confidence += min(indicator_count * 0.1, 0.3)
        
        # Check for actual contact elements
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if soup.select("a[href^='mailto:']"):
            confidence += 0.1
        if soup.select("a[href^='tel:']"):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Check if strategy supports the extraction purpose"""
        supported_purposes = [
            "contact_discovery", "lead_generation", "business_intelligence",
            "social_media_analysis", "communication_channels"
        ]
        return purpose in supported_purposes
