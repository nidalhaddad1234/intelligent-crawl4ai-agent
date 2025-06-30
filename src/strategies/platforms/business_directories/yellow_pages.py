#!/usr/bin/env python3
"""
Yellow Pages Strategy
Specialized strategy for Yellow Pages business directory

Examples:
- Extract business listings from Yellow Pages search results
- Get detailed business information from business pages
- Scrape contact information and business hours
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.platforms.business_directories.yellow_pages")


class YellowPagesStrategy(BaseExtractionStrategy):
    """
    Specialized strategy for Yellow Pages business directory
    
    Examples:
    - Extract business listings from Yellow Pages search results
    - Get detailed business information from business pages
    - Scrape contact information and business hours
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.yellowpages_selectors = {
            "business_name": [
                ".business-name h3 a",
                ".listing-name",
                "h1.dockable"
            ],
            "phone": [
                ".phones.phone.primary",
                ".phone",
                "a[href^='tel:']"
            ],
            "address": [
                ".street-address",
                ".listing-address",
                ".address"
            ],
            "website": [
                ".track-visit-website",
                ".website-link a",
                "a[href*='http']"
            ],
            "categories": [
                ".categories a",
                ".business-categories",
                ".category"
            ],
            "rating": [
                ".rating .count",
                ".star-rating",
                ".result-rating"
            ],
            "years_in_business": [
                ".years-in-business",
                ".business-age"
            ],
            "hours": [
                ".hours-info",
                ".business-hours",
                ".opening-hours"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Determine if search results or business page
            if '/search/' in url or 'find_loc=' in url:
                extracted_data = await self._extract_search_results(soup, url)
            else:
                extracted_data = await self._extract_business_details(soup, url)
            
            confidence = self.calculate_confidence(extracted_data, ["business_name", "phone", "address"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="YellowPagesStrategy",
                execution_time=execution_time,
                metadata={
                    "page_type": "search" if "/search/" in url else "business"
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="YellowPagesStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _extract_search_results(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract Yellow Pages search results"""
        results = {"businesses": []}
        
        # Find business listing containers
        business_containers = soup.select(".result, .search-results .listing")
        
        for container in business_containers[:30]:  # Get first 30 results
            business = {}
            
            # Extract data using selectors
            for field, selectors in self.yellowpages_selectors.items():
                value = self._extract_yp_field(container, selectors, field)
                if value:
                    business[field] = value
            
            if business.get("business_name"):
                results["businesses"].append(business)
        
        return results
    
    async def _extract_business_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed business information"""
        business = {}
        
        # Extract all available fields
        for field, selectors in self.yellowpages_selectors.items():
            value = self._extract_yp_field(soup, selectors, field)
            if value:
                business[field] = value
        
        # Extract additional details
        business_details = self._extract_additional_details(soup)
        if business_details:
            business.update(business_details)
        
        return business
    
    def _extract_yp_field(self, container, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Yellow Pages specific logic"""
        for selector in selectors:
            elements = container.select(selector)
            for element in elements:
                if field_type == "phone":
                    return self._extract_yp_phone(element)
                elif field_type == "website":
                    return self._extract_yp_website(element)
                elif field_type == "rating":
                    return self._extract_yp_rating(element)
                else:
                    text = element.get_text(strip=True)
                    if text:
                        return text
        return None
    
    def _extract_yp_phone(self, element) -> Optional[str]:
        """Extract phone number from Yellow Pages element"""
        href = element.get('href', '')
        if href.startswith('tel:'):
            return href.replace('tel:', '')
        
        text = element.get_text(strip=True)
        # Clean phone number
        phone_match = re.search(r'(\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})', text)
        if phone_match:
            return phone_match.group(1)
        
        return text if text else None
    
    def _extract_yp_website(self, element) -> Optional[str]:
        """Extract website URL from Yellow Pages element"""
        href = element.get('href', '')
        if href and href.startswith('http'):
            return href
        return None
    
    def _extract_yp_rating(self, element) -> Optional[str]:
        """Extract rating from Yellow Pages element"""
        text = element.get_text(strip=True)
        rating_match = re.search(r'(\d+\.?\d*)', text)
        if rating_match:
            return rating_match.group(1)
        return None
    
    def _extract_additional_details(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional business details"""
        details = {}
        
        # Business description
        desc_elem = soup.select_one(".business-description, .about-business")
        if desc_elem:
            details["description"] = desc_elem.get_text(strip=True)
        
        # Payment methods
        payment_elem = soup.select_one(".payment-methods")
        if payment_elem:
            details["payment_methods"] = payment_elem.get_text(strip=True)
        
        # Services
        services_elems = soup.select(".services li, .business-services li")
        if services_elems:
            services = [elem.get_text(strip=True) for elem in services_elems]
            details["services"] = services
        
        return details
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Yellow Pages strategy confidence"""
        if 'yellowpages.com' in url:
            return 0.9
        return 0.1
    
    def supports_purpose(self, purpose: str) -> bool:
        """Yellow Pages supports business directory purposes"""
        supported_purposes = [
            "company_info", "business_listings", "contact_discovery",
            "local_business_data", "directory_mining"
        ]
        return purpose in supported_purposes
