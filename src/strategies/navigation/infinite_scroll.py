#!/usr/bin/env python3
"""
Infinite Scroll Strategy
Handle infinite scroll and dynamic content loading

Examples:
- Extract all posts from social media feeds
- Scrape complete product catalogs with lazy loading
- Handle dynamic search results that load on scroll
- Collect all items from infinite scroll lists
"""

import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.navigation.infinite_scroll")


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
