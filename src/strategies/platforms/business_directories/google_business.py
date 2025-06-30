#!/usr/bin/env python3
"""
Google Business Strategy
Strategy for Google Business listings and maps data

Examples:
- Extract business information from Google My Business listings
- Get reviews and ratings from Google Maps
- Scrape business hours and contact information
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.platforms.business_directories.google_business")


class GoogleBusinessStrategy(BaseExtractionStrategy):
    """
    Strategy for Google Business listings and maps data
    
    Examples:
    - Extract business information from Google My Business listings
    - Get reviews and ratings from Google Maps
    - Scrape business hours and contact information
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.google_selectors = {
            "business_name": [
                "h1[data-attrid='title']",
                ".SPZz6b",
                ".x3AX1-LfntMc-header-title-title"
            ],
            "rating": [
                "[data-attrid='kc:/location/location:rating']",
                ".yi40Hd.YrbPuc",
                ".Aq14fc"
            ],
            "review_count": [
                "[data-attrid='kc:/location/location:num_reviews']",
                ".hqzQac",
                ".RDApEe.YrbPuc"
            ],
            "address": [
                "[data-attrid='kc:/location/location:address']",
                ".LrzXr",
                ".T6pBCe"
            ],
            "phone": [
                "[data-attrid='kc:/location/location:phone']",
                ".LrzXr.zdqRlf.kno-fv",
                "a[href^='tel:']"
            ],
            "website": [
                "[data-attrid='kc:/location/location:website']",
                ".CL9Uqc.Ab5aWb",
                "a[data-dtype='d3website']"
            ],
            "hours": [
                "[data-attrid='kc:/location/location:hours']",
                ".t39EBf.GUrTXd",
                ".OqQkV"
            ],
            "category": [
                "[data-attrid='kc:/location/location:category']",
                ".YhemCb",
                ".mgr77e"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = {}
            
            # Extract business information
            for field, selectors in self.google_selectors.items():
                value = self._extract_google_field(soup, selectors, field)
                if value:
                    extracted_data[field] = value
            
            # Extract reviews if available
            reviews_data = self._extract_google_reviews(soup)
            if reviews_data:
                extracted_data["reviews"] = reviews_data
            
            confidence = self.calculate_confidence(extracted_data, ["business_name", "rating"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="GoogleBusinessStrategy",
                execution_time=execution_time,
                metadata={
                    "google_business": True
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="GoogleBusinessStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_google_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Google-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if field_type == "phone":
                    href = element.get('href', '')
                    if href.startswith('tel:'):
                        return href.replace('tel:', '')
                
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _extract_google_reviews(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract Google reviews"""
        reviews = []
        
        # Look for review elements
        review_elements = soup.select(".jftiEf, .review-item")
        
        for review_elem in review_elements[:5]:  # First 5 reviews
            review = {}
            
            # Reviewer name
            name_elem = review_elem.select_one(".X43Kjb, .reviewer-name")
            if name_elem:
                review["reviewer"] = name_elem.get_text(strip=True)
            
            # Review text
            text_elem = review_elem.select_one(".wiI7pd, .review-text")
            if text_elem:
                review["text"] = text_elem.get_text(strip=True)[:300]
            
            # Review rating
            rating_elem = review_elem.select_one(".kvMYJc, .review-rating")
            if rating_elem:
                rating_text = rating_elem.get('aria-label', '')
                rating_match = re.search(r'(\d+)', rating_text)
                if rating_match:
                    review["rating"] = rating_match.group(1)
            
            if review:
                reviews.append(review)
        
        return reviews
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Google Business strategy confidence"""
        if 'google.com' in url and ('maps' in url or 'business' in url):
            return 0.8
        return 0.2
    
    def supports_purpose(self, purpose: str) -> bool:
        """Google Business supports local business purposes"""
        supported_purposes = [
            "company_info", "business_listings", "contact_discovery",
            "local_business_data", "review_analysis"
        ]
        return purpose in supported_purposes
