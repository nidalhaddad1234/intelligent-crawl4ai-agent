#!/usr/bin/env python3
"""
Pagination Strategy
Handle paginated content extraction across multiple pages

Examples:
- Extract all products from multi-page catalogs
- Scrape all search results across pagination
- Collect complete datasets from paginated APIs
- Handle infinite scroll and load-more buttons
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.navigation.pagination")


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
