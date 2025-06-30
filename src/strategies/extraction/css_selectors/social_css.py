#!/usr/bin/env python3
"""
Social Media CSS Strategy
Optimized for social media platforms and profile pages

Examples:
- Extract LinkedIn profile information
- Get Twitter/X profile data
- Scrape Facebook page details
"""

import time
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.extraction.css_selectors.social")


class SocialMediaCSSStrategy(BaseExtractionStrategy):
    """
    Optimized for social media platforms and profile pages
    
    Examples:
    - Extract LinkedIn profile information
    - Get Twitter/X profile data
    - Scrape Facebook page details
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        
        self.profile_selectors = {
            "name": [
                "h1, .name, .profile-name",
                "[data-testid*='name'], [data-name]",
                ".display-name, .full-name"
            ],
            "title": [
                ".title, .headline, .position",
                "[data-testid*='headline']",
                ".job-title, .professional-title"
            ],
            "company": [
                ".company, .organization, .workplace",
                "[data-testid*='company']",
                ".current-position"
            ],
            "location": [
                ".location, .geography, .address",
                "[data-testid*='location']",
                ".geo-location"
            ],
            "bio": [
                ".bio, .summary, .about",
                "[data-testid*='bio'], [data-testid*='summary']",
                ".description, .profile-description"
            ],
            "followers": [
                ".followers, .follower-count",
                "[data-testid*='followers']",
                ".connections"
            ],
            "avatar": [
                ".avatar img, .profile-photo img",
                "[data-testid*='avatar'] img",
                ".profile-image img"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract profile data
            profile_data = self._extract_profile_data(soup)
            
            # Platform-specific extraction
            platform = self._detect_platform(url)
            if platform:
                platform_data = self._extract_platform_specific(soup, platform)
                if platform_data:
                    profile_data.update(platform_data)
            
            extracted_data = profile_data if profile_data else {}
            
            confidence = self.calculate_confidence(
                extracted_data,
                ["name", "title", "company"]
            )
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="SocialMediaCSSStrategy",
                execution_time=execution_time,
                metadata={
                    "platform": platform,
                    "profile_completeness": len(extracted_data)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="SocialMediaCSSStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_profile_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract general profile data"""
        profile = {}
        
        for field, selectors in self.profile_selectors.items():
            if field == "avatar":
                value = self._extract_image_src(soup, selectors)
            else:
                value = self._extract_field_value(soup, selectors)
            
            if value:
                profile[field] = value
        
        return profile
    
    def _extract_field_value(self, container, selectors: List[str]) -> str:
        """Extract field value using multiple selector fallbacks"""
        for selector in selectors:
            try:
                elements = container.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and len(text) > 1:
                        return text
            except Exception:
                continue
        return None
    
    def _extract_image_src(self, container, selectors: List[str]) -> str:
        """Extract image source URL"""
        for selector in selectors:
            try:
                img_elements = container.select(selector)
                for img in img_elements:
                    src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                    if src and src.startswith(('http', '//')):
                        return src
            except Exception:
                continue
        return None
    
    def _detect_platform(self, url: str) -> str:
        """Detect social media platform from URL"""
        platforms = {
            "linkedin.com": "linkedin",
            "twitter.com": "twitter",
            "x.com": "twitter",
            "facebook.com": "facebook",
            "instagram.com": "instagram",
            "youtube.com": "youtube"
        }
        
        for domain, platform in platforms.items():
            if domain in url:
                return platform
        
        return None
    
    def _extract_platform_specific(self, soup: BeautifulSoup, platform: str) -> Dict[str, Any]:
        """Extract platform-specific data"""
        
        if platform == "linkedin":
            return self._extract_linkedin_specific(soup)
        elif platform == "twitter":
            return self._extract_twitter_specific(soup)
        elif platform == "facebook":
            return self._extract_facebook_specific(soup)
        
        return {}
    
    def _extract_linkedin_specific(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """LinkedIn-specific extraction"""
        data = {}
        
        # Connections count
        connections = soup.select(".member-connections, .connections-count")
        if connections:
            data["connections"] = connections[0].get_text(strip=True)
        
        # Experience section
        experience = soup.select(".experience-section, .pv-experience-section")
        if experience:
            data["has_experience"] = True
        
        return data
    
    def _extract_twitter_specific(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Twitter/X-specific extraction"""
        data = {}
        
        # Follower/following counts
        stats = soup.select("[data-testid='UserCell'] a")
        for stat in stats:
            text = stat.get_text(strip=True).lower()
            if "followers" in text:
                data["followers"] = text
            elif "following" in text:
                data["following"] = text
        
        return data
    
    def _extract_facebook_specific(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Facebook-specific extraction"""
        data = {}
        
        # Page likes
        likes = soup.select("[data-testid='page_likes']")
        if likes:
            data["page_likes"] = likes[0].get_text(strip=True)
        
        return data
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Estimate confidence for social media extraction"""
        
        # Check if it's a known social platform
        social_platforms = [
            "linkedin.com", "twitter.com", "x.com", "facebook.com",
            "instagram.com", "youtube.com"
        ]
        
        confidence = 0.3
        
        if any(platform in url for platform in social_platforms):
            confidence += 0.4
        
        # Check for profile indicators
        profile_indicators = [
            "profile", "bio", "followers", "connections", "about"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for indicator in profile_indicators 
                            if indicator in content_lower)
        confidence += min(indicator_count * 0.1, 0.3)
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Check if strategy supports the extraction purpose"""
        supported_purposes = [
            "profile_info", "social_media_analysis", "person_data",
            "professional_profiles", "social_intelligence"
        ]
        return purpose in supported_purposes
