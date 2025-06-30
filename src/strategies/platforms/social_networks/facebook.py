#!/usr/bin/env python3
"""
Facebook Strategy
Strategy for Facebook pages and business profiles

Examples:
- Extract Facebook page information
- Get business details from Facebook pages
- Scrape posts and engagement data
"""

import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.platforms.social_networks.facebook")


class FacebookStrategy(BaseExtractionStrategy):
    """
    Strategy for Facebook pages and business profiles
    
    Examples:
    - Extract Facebook page information
    - Get business details from Facebook pages
    - Scrape posts and engagement data
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.facebook_selectors = {
            "page_name": [
                "h1[data-testid='page_title']",
                ".x1heor9g.x1qlqyl8.x1pd3egz.x1a2a7pz",
                ".page-title"
            ],
            "page_category": [
                "[data-testid='page_subtitle']",
                ".x193iq5w.xeuugli.x13faqbe",
                ".page-category"
            ],
            "page_likes": [
                "[data-testid='page_likes']",
                ".page-likes-count"
            ],
            "page_followers": [
                "[data-testid='page_followers']",
                ".page-followers-count"
            ],
            "about_info": [
                "[data-testid='page_about_description']",
                ".page-about",
                ".about-section"
            ],
            "contact_info": [
                ".contact-info",
                ".page-contact"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = {}
            
            # Extract page information
            for field, selectors in self.facebook_selectors.items():
                value = self._extract_facebook_field(soup, selectors, field)
                if value:
                    extracted_data[field] = value
            
            # Check for login requirement
            if self._requires_facebook_login(soup):
                extracted_data["requires_authentication"] = True
            
            confidence = self.calculate_confidence(extracted_data, ["page_name"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="FacebookStrategy",
                execution_time=execution_time,
                metadata={
                    "facebook_page": True,
                    "requires_auth": extracted_data.get("requires_authentication", False)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="FacebookStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_facebook_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Facebook-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text:
                    return text
        return None
    
    def _requires_facebook_login(self, soup: BeautifulSoup) -> bool:
        """Check if Facebook login is required"""
        login_indicators = [
            "Log in to Facebook",
            "Create Account",
            "login_form"
        ]
        
        page_text = soup.get_text()
        return any(indicator in page_text for indicator in login_indicators)
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Facebook strategy confidence"""
        if 'facebook.com' in url:
            return 0.7
        return 0.1
    
    def supports_purpose(self, purpose: str) -> bool:
        """Facebook supports social media and business purposes"""
        supported_purposes = [
            "company_info", "social_media_analysis", "business_intelligence",
            "contact_discovery", "brand_monitoring"
        ]
        return purpose in supported_purposes
