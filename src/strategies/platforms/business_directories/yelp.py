#!/usr/bin/env python3
"""
Yelp Strategy
Specialized strategy for Yelp business listings and reviews

Examples:
- Extract restaurant details from Yelp business pages
- Get review data and ratings
- Scrape business contact information and hours
"""

import json
import re
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.platforms.business_directories.yelp")


class YelpStrategy(BaseExtractionStrategy):
    """
    Specialized strategy for Yelp business listings and reviews
    
    Examples:
    - Extract restaurant details from Yelp business pages
    - Get review data and ratings
    - Scrape business contact information and hours
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.yelp_selectors = {
            "business_name": [
                "h1[data-testid='page-title']",
                ".biz-page-title",
                "h1.lemon--h1__373c0__2ZHSL"
            ],
            "rating": [
                "[aria-label*='star rating']",
                ".i-stars",
                "[data-testid='rating']"
            ],
            "review_count": [
                "[data-testid='review-count']",
                ".review-count",
                "a[href*='#reviews']"
            ],
            "price_range": [
                "[data-testid='price-range']",
                ".price-range",
                ".business-attribute-price-range"
            ],
            "categories": [
                "[data-testid='category']",
                ".category-str-list a",
                ".business-categories"
            ],
            "address": [
                "[data-testid='business-address']",
                ".street-address",
                "address"
            ],
            "phone": [
                "[data-testid='phone-number']",
                ".biz-phone",
                "a[href^='tel:']"
            ],
            "website": [
                "[data-testid='business-website-link']",
                ".biz-website a",
                "a[href*='biz_redir']"
            ],
            "hours": [
                "[data-testid='hours']",
                ".hours-table",
                ".business-hours"
            ],
            "photos": [
                "[data-testid='photo-box'] img",
                ".photo-box img",
                ".showcase-photos img"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Determine if this is a business page or search results
            if self._is_business_page(url):
                extracted_data = await self._extract_business_details(soup, url)
            else:
                extracted_data = await self._extract_search_results(soup, url)
            
            # Extract structured data if available
            structured_data = self._extract_yelp_structured_data(html_content)
            if structured_data:
                extracted_data.update(structured_data)
            
            confidence = self.calculate_confidence(extracted_data, ["business_name", "rating", "address"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="YelpStrategy",
                execution_time=execution_time,
                metadata={
                    "page_type": "business" if self._is_business_page(url) else "search",
                    "yelp_specific": True
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="YelpStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _is_business_page(self, url: str) -> bool:
        """Check if URL is a Yelp business page vs search results"""
        return '/biz/' in url
    
    async def _extract_business_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract details from a Yelp business page"""
        business = {}
        
        # Extract basic business information
        for field, selectors in self.yelp_selectors.items():
            value = self._extract_yelp_field(soup, selectors, field)
            if value:
                business[field] = value
        
        # Extract reviews data
        reviews_data = self._extract_reviews_data(soup)
        if reviews_data:
            business["reviews"] = reviews_data
        
        # Extract business attributes
        attributes = self._extract_business_attributes(soup)
        if attributes:
            business["attributes"] = attributes
        
        # Extract menu information if available
        menu_data = self._extract_menu_data(soup)
        if menu_data:
            business["menu"] = menu_data
        
        return business
    
    async def _extract_search_results(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract business listings from Yelp search results"""
        results = {"businesses": []}
        
        # Find business listing containers
        business_containers = soup.select(".businessName, .search-result, [data-testid='serp-ia-card']")
        
        for container in business_containers[:20]:  # Limit to first 20 results
            business = {}
            
            # Extract basic info from each listing
            name_elem = container.select_one("h3 a, .businessName a, [data-testid='business-name']")
            if name_elem:
                business["name"] = name_elem.get_text(strip=True)
                business["url"] = name_elem.get('href', '')
            
            # Rating and review count
            rating_elem = container.select_one("[aria-label*='star'], .i-stars")
            if rating_elem:
                business["rating"] = self._extract_rating_from_element(rating_elem)
            
            review_elem = container.select_one(".reviewCount, [data-testid='review-count']")
            if review_elem:
                business["review_count"] = review_elem.get_text(strip=True)
            
            # Categories
            category_elem = container.select_one(".category-str-list, .business-categories")
            if category_elem:
                business["categories"] = category_elem.get_text(strip=True)
            
            # Address
            address_elem = container.select_one(".address, .neighborhood-str-list")
            if address_elem:
                business["address"] = address_elem.get_text(strip=True)
            
            if business.get("name"):
                results["businesses"].append(business)
        
        return results
    
    def _extract_yelp_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Yelp-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if field_type == "rating":
                    return self._extract_rating_from_element(element)
                elif field_type == "photos":
                    return self._extract_photo_urls(elements)
                elif field_type == "website":
                    return self._extract_yelp_website(element)
                elif field_type == "phone":
                    return self._extract_phone_number(element)
                else:
                    text = element.get_text(strip=True)
                    if text:
                        return text
        return None
    
    def _extract_rating_from_element(self, element) -> Optional[str]:
        """Extract rating from Yelp rating element"""
        # Check aria-label first
        aria_label = element.get('aria-label', '')
        if 'star' in aria_label:
            # Extract number from "4.5 star rating"
            rating_match = re.search(r'(\d+\.?\d*)', aria_label)
            if rating_match:
                return rating_match.group(1)
        
        # Check for data attributes
        for attr in ['data-rating', 'data-star-rating']:
            if element.get(attr):
                return element.get(attr)
        
        # Check text content
        text = element.get_text(strip=True)
        rating_match = re.search(r'(\d+\.?\d*)', text)
        if rating_match:
            return rating_match.group(1)
        
        return None
    
    def _extract_photo_urls(self, elements) -> List[str]:
        """Extract photo URLs from elements"""
        photos = []
        for element in elements:
            src = element.get('src') or element.get('data-src')
            if src and src.startswith('http'):
                photos.append(src)
        return photos[:10]  # Limit to first 10 photos
    
    def _extract_yelp_website(self, element) -> Optional[str]:
        """Extract website URL from Yelp business link"""
        href = element.get('href', '')
        if 'biz_redir' in href:
            # Parse the redirect URL to get actual website
            try:
                parsed = urlparse(href)
                query_params = parse_qs(parsed.query)
                if 'url' in query_params:
                    return query_params['url'][0]
            except:
                pass
        return href if href.startswith('http') else None
    
    def _extract_phone_number(self, element) -> Optional[str]:
        """Extract phone number from element"""
        href = element.get('href', '')
        if href.startswith('tel:'):
            return href.replace('tel:', '')
        return element.get_text(strip=True)
    
    def _extract_reviews_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract review-related data"""
        reviews_data = {}
        
        # Total review count
        review_count_elem = soup.select_one("[data-testid='review-count'], .review-count")
        if review_count_elem:
            reviews_data["total_reviews"] = review_count_elem.get_text(strip=True)
        
        # Individual reviews
        review_elements = soup.select(".review, [data-testid='review']")
        if review_elements:
            reviews = []
            for review_elem in review_elements[:5]:  # First 5 reviews
                review = {}
                
                # Reviewer name
                name_elem = review_elem.select_one(".user-name, .reviewer-name")
                if name_elem:
                    review["reviewer"] = name_elem.get_text(strip=True)
                
                # Review rating
                rating_elem = review_elem.select_one("[aria-label*='star']")
                if rating_elem:
                    review["rating"] = self._extract_rating_from_element(rating_elem)
                
                # Review text
                text_elem = review_elem.select_one(".review-content, .comment")
                if text_elem:
                    review["text"] = text_elem.get_text(strip=True)[:500]  # Limit length
                
                if review:
                    reviews.append(review)
            
            reviews_data["recent_reviews"] = reviews
        
        return reviews_data
    
    def _extract_business_attributes(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract business attributes like amenities, parking, etc."""
        attributes = {}
        
        # Look for attributes section
        attr_sections = soup.select(".business-attributes, .amenities-info")
        
        for section in attr_sections:
            attr_items = section.select(".attribute-item, .amenity-item")
            for item in attr_items:
                key_elem = item.select_one(".attribute-key, .amenity-key")
                value_elem = item.select_one(".attribute-value, .amenity-value")
                
                if key_elem and value_elem:
                    key = key_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    attributes[key] = value
        
        return attributes
    
    def _extract_menu_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract menu information if available"""
        menu_data = {}
        
        # Look for menu sections
        menu_sections = soup.select(".menu-section, .menu-items")
        
        for section in menu_sections:
            section_name_elem = section.select_one(".section-header, .menu-section-header")
            section_name = section_name_elem.get_text(strip=True) if section_name_elem else "Menu"
            
            items = []
            menu_items = section.select(".menu-item")
            
            for item in menu_items[:10]:  # Limit items per section
                item_data = {}
                
                name_elem = item.select_one(".menu-item-name, .item-name")
                if name_elem:
                    item_data["name"] = name_elem.get_text(strip=True)
                
                price_elem = item.select_one(".menu-item-price, .item-price")
                if price_elem:
                    item_data["price"] = price_elem.get_text(strip=True)
                
                desc_elem = item.select_one(".menu-item-description, .item-description")
                if desc_elem:
                    item_data["description"] = desc_elem.get_text(strip=True)
                
                if item_data:
                    items.append(item_data)
            
            if items:
                menu_data[section_name] = items
        
        return menu_data
    
    def _extract_yelp_structured_data(self, html_content: str) -> Dict[str, Any]:
        """Extract Yelp-specific structured data"""
        structured = {}
        
        # Look for Yelp's JSON data in script tags
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tags = soup.find_all('script')
        
        for script in script_tags:
            script_text = script.get_text()
            if 'window.yelp' in script_text or 'bizDetails' in script_text:
                # Try to extract JSON data
                try:
                    # Look for JSON objects in the script
                    json_matches = re.findall(r'\{[^{}]*"bizId"[^{}]*\}', script_text)
                    for match in json_matches:
                        try:
                            data = json.loads(match)
                            if 'bizId' in data:
                                structured['yelp_internal_data'] = data
                                break
                        except json.JSONDecodeError:
                            continue
                except Exception:
                    continue
        
        return structured
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Yelp strategy has high confidence on Yelp URLs"""
        if 'yelp.com' in url:
            return 0.9
        return 0.1  # Very low confidence for non-Yelp URLs
    
    def supports_purpose(self, purpose: str) -> bool:
        """Yelp strategy supports business and review extraction"""
        supported_purposes = [
            "company_info", "business_listings", "contact_discovery",
            "review_analysis", "local_business_data"
        ]
        return purpose in supported_purposes
