#!/usr/bin/env python3
"""
Directory CSS Strategy
Optimized for business directory websites like Yellow Pages, Yelp, etc.

Examples:
- Extract business listings from Yellow Pages
- Get restaurant info from Yelp
- Scrape real estate agents from Zillow
"""

import time
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.extraction.css_selectors.directory")


class DirectoryCSSStrategy(BaseExtractionStrategy):
    """
    Optimized for business directory websites like Yellow Pages, Yelp, etc.
    
    Examples:
    - Extract business listings from Yellow Pages
    - Get restaurant info from Yelp
    - Scrape real estate agents from Zillow
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        
        # Common CSS patterns for business directories
        self.business_selectors = {
            "name": [
                "h1, h2, h3",
                ".business-name, .company-name, .listing-name",
                "[data-business-name], [data-name]",
                ".name, .title",
                ".card-title, .listing-title"
            ],
            "address": [
                ".address, .location",
                "[itemprop='address'], [itemtype*='PostalAddress']",
                ".street-address, .postal-address",
                "[data-address], [data-location]",
                ".contact-address"
            ],
            "phone": [
                "a[href^='tel:']",
                ".phone, .telephone, .tel",
                "[itemprop='telephone']",
                "[data-phone], [data-tel]",
                ".contact-phone"
            ],
            "website": [
                "a[href^='http']:not([href*='yelp']):not([href*='google']):not([href*='facebook'])",
                ".website, .url",
                "[data-website], [data-url]",
                ".external-link"
            ],
            "email": [
                "a[href^='mailto:']",
                "[data-email]",
                ".email"
            ],
            "rating": [
                ".rating, .stars, .score",
                "[data-rating], [data-stars]",
                ".review-rating, .avg-rating"
            ],
            "category": [
                ".category, .business-type",
                "[data-category], [data-type]",
                ".tags, .categories"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = {}
            
            # Extract business listings
            listings = self._find_business_listings(soup)
            
            if listings:
                extracted_data["businesses"] = listings
                confidence = self.calculate_confidence(extracted_data, ["businesses"])
            else:
                # Try single business extraction
                business_data = self._extract_single_business(soup)
                if business_data:
                    extracted_data.update(business_data)
                    confidence = self.calculate_confidence(extracted_data, list(self.business_selectors.keys()))
                else:
                    confidence = 0.1
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="DirectoryCSSStrategy",
                execution_time=execution_time,
                metadata={
                    "listings_found": len(extracted_data.get("businesses", [])),
                    "selectors_used": self._get_successful_selectors(soup)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="DirectoryCSSStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _find_business_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find multiple business listings on directory pages"""
        
        # Common listing container patterns
        listing_containers = [
            ".listing, .business-listing",
            ".card, .business-card",
            ".result, .search-result",
            "[data-business], [data-listing]",
            ".item, .business-item"
        ]
        
        listings = []
        
        for container_selector in listing_containers:
            containers = soup.select(container_selector)
            
            if len(containers) > 1:  # Multiple listings found
                for container in containers[:50]:  # Limit to first 50
                    business_data = self._extract_business_from_container(container)
                    if business_data:
                        listings.append(business_data)
                
                if listings:
                    break
        
        return listings
    
    def _extract_business_from_container(self, container) -> Dict[str, Any]:
        """Extract business data from a single container element"""
        business = {}
        
        for field, selectors in self.business_selectors.items():
            value = self._extract_field_value(container, selectors)
            if value:
                business[field] = value
        
        # Only return if we have essential data
        if business.get("name") or business.get("phone") or business.get("address"):
            return business
        return None
    
    def _extract_single_business(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract single business data from entire page"""
        business = {}
        
        for field, selectors in self.business_selectors.items():
            value = self._extract_field_value(soup, selectors)
            if value:
                business[field] = value
        
        return business if business else None
    
    def _extract_field_value(self, container, selectors: List[str]) -> str:
        """Extract field value using multiple selector fallbacks"""
        for selector in selectors:
            try:
                elements = container.select(selector)
                for element in elements:
                    # Get text content
                    if selector.startswith("a[href"):
                        # For links, extract href attribute
                        href = element.get('href', '')
                        if href and ('tel:' in href or 'mailto:' in href or 'http' in href):
                            return href.replace('tel:', '').replace('mailto:', '')
                    
                    text = element.get_text(strip=True)
                    if text and len(text) > 1:
                        return text
                        
            except Exception:
                continue
        return None
    
    def _get_successful_selectors(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Track which selectors were successful for learning"""
        successful = {}
        
        for field, selectors in self.business_selectors.items():
            for selector in selectors:
                try:
                    if soup.select(selector):
                        successful[field] = selector
                        break
                except Exception:
                    continue
        
        return successful
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Estimate confidence for directory extraction"""
        
        # Check for directory indicators
        directory_indicators = [
            "listing", "business", "directory", "search-result",
            "card", "item", "result"
        ]
        
        confidence = 0.3  # Base confidence
        
        content_lower = html_content.lower()
        
        # Check for directory patterns
        indicator_count = sum(1 for indicator in directory_indicators 
                            if indicator in content_lower)
        confidence += min(indicator_count * 0.1, 0.4)
        
        # Check for multiple business names/phones (indicates listings)
        soup = BeautifulSoup(html_content, 'html.parser')
        business_names = soup.select("h1, h2, h3, .business-name, .company-name")
        phone_links = soup.select("a[href^='tel:']")
        
        if len(business_names) > 3:
            confidence += 0.2
        if len(phone_links) > 2:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Check if strategy supports the extraction purpose"""
        supported_purposes = [
            "company_info", "contact_discovery", "business_listings",
            "directory_mining", "lead_generation"
        ]
        return purpose in supported_purposes
