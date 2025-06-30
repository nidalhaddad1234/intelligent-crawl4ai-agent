#!/usr/bin/env python3
"""
Amazon Strategy
Specialized strategy for Amazon product pages and search results

Examples:
- Extract product details, pricing, and reviews
- Get seller information and shipping details
- Scrape product specifications and images
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.platforms.ecommerce.amazon")


class AmazonStrategy(BaseExtractionStrategy):
    """
    Specialized strategy for Amazon product pages and search results
    
    Examples:
    - Extract product details, pricing, and reviews
    - Get seller information and shipping details
    - Scrape product specifications and images
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.PLATFORM_SPECIFIC, **kwargs)
        
        self.amazon_selectors = {
            "product_title": [
                "#productTitle",
                ".product-title",
                "h1.a-size-large"
            ],
            "price": [
                ".a-price-whole",
                "#price_inside_buybox",
                ".a-price.a-text-price.a-size-medium.apexPriceToPay"
            ],
            "rating": [
                ".a-icon-alt",
                "[data-hook='average-star-rating']",
                ".acrPopover"
            ],
            "review_count": [
                "#acrCustomerReviewText",
                "[data-hook='total-review-count']"
            ],
            "availability": [
                "#availability span",
                ".a-color-success",
                ".a-color-state"
            ],
            "brand": [
                "#bylineInfo",
                ".a-brand",
                "[data-brand]"
            ],
            "description": [
                "#feature-bullets ul",
                ".a-unordered-list.a-vertical",
                "#productDescription"
            ],
            "images": [
                "#landingImage",
                ".a-dynamic-image",
                "#altImages img"
            ],
            "specifications": [
                "#productDetails_detailBullets_sections1",
                ".a-keyvalue",
                "#prodDetails"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Determine if this is a product page or search results
            if '/dp/' in url or '/gp/product/' in url:
                extracted_data = await self._extract_product_details(soup, url)
            elif '/s?' in url:
                extracted_data = await self._extract_search_results(soup, url)
            else:
                extracted_data = await self._extract_general_amazon_data(soup, url)
            
            confidence = self.calculate_confidence(extracted_data, ["product_title", "price"])
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="AmazonStrategy",
                execution_time=execution_time,
                metadata={
                    "page_type": self._detect_amazon_page_type(url),
                    "amazon_specific": True
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="AmazonStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _extract_product_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract Amazon product details"""
        product = {}
        
        # Extract basic product information
        for field, selectors in self.amazon_selectors.items():
            value = self._extract_amazon_field(soup, selectors, field)
            if value:
                product[field] = value
        
        # Extract seller information
        seller_data = self._extract_seller_info(soup)
        if seller_data:
            product["seller"] = seller_data
        
        # Extract shipping information
        shipping_data = self._extract_shipping_info(soup)
        if shipping_data:
            product["shipping"] = shipping_data
        
        # Extract variant information (size, color, etc.)
        variants_data = self._extract_variants_info(soup)
        if variants_data:
            product["variants"] = variants_data
        
        return product
    
    async def _extract_search_results(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract Amazon search results"""
        results = {"products": []}
        
        # Find product containers in search results
        product_containers = soup.select("[data-component-type='s-search-result']")
        
        for container in product_containers[:20]:  # Limit to first 20 results
            product = {}
            
            # Product title and link
            title_elem = container.select_one("h2 a span, .s-size-mini span")
            if title_elem:
                product["title"] = title_elem.get_text(strip=True)
            
            link_elem = container.select_one("h2 a")
            if link_elem:
                product["url"] = link_elem.get('href', '')
            
            # Price
            price_elem = container.select_one(".a-price-whole, .a-price")
            if price_elem:
                product["price"] = price_elem.get_text(strip=True)
            
            # Rating
            rating_elem = container.select_one(".a-icon-alt")
            if rating_elem:
                product["rating"] = self._extract_amazon_rating(rating_elem)
            
            # Image
            img_elem = container.select_one("img.s-image")
            if img_elem:
                product["image"] = img_elem.get('src', '')
            
            if product.get("title"):
                results["products"].append(product)
        
        return results
    
    async def _extract_general_amazon_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract general Amazon data for unclear page types"""
        data = {}
        
        # Try product extraction first
        product_data = await self._extract_product_details(soup, url)
        if product_data:
            data.update(product_data)
        
        # Try search results extraction
        search_data = await self._extract_search_results(soup, url)
        if search_data and search_data.get("products"):
            data.update(search_data)
        
        return data
    
    def _extract_amazon_field(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> Optional[str]:
        """Extract field using Amazon-specific logic"""
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                if field_type == "rating":
                    return self._extract_amazon_rating(element)
                elif field_type == "price":
                    return self._extract_amazon_price(element)
                elif field_type == "images":
                    return self._extract_amazon_images(elements)
                elif field_type == "description":
                    return self._extract_amazon_description(element)
                else:
                    text = element.get_text(strip=True)
                    if text:
                        return text
        return None
    
    def _extract_amazon_rating(self, element) -> Optional[str]:
        """Extract rating from Amazon rating element"""
        # Check alt text for rating
        alt_text = element.get('alt', '')
        if 'out of 5 stars' in alt_text:
            rating_match = re.search(r'(\d+\.?\d*)', alt_text)
            if rating_match:
                return rating_match.group(1)
        
        # Check text content
        text = element.get_text(strip=True)
        rating_match = re.search(r'(\d+\.?\d*)', text)
        if rating_match:
            return rating_match.group(1)
        
        return None
    
    def _extract_amazon_price(self, element) -> Optional[str]:
        """Extract price from Amazon price element"""
        # Try to get the full price
        price_text = element.get_text(strip=True)
        
        # Clean up price text
        price_text = re.sub(r'[^\d.,]', '', price_text)
        
        if price_text:
            return price_text
        
        return None
    
    def _extract_amazon_images(self, elements) -> List[str]:
        """Extract product images from Amazon"""
        images = []
        
        for element in elements:
            src = element.get('src') or element.get('data-src')
            if src and src.startswith('http'):
                images.append(src)
        
        return images[:5]  # Limit to first 5 images
    
    def _extract_amazon_description(self, element) -> Optional[str]:
        """Extract product description from Amazon"""
        # For bullet points, join them
        if element.name == 'ul':
            bullets = element.select('li')
            descriptions = [li.get_text(strip=True) for li in bullets]
            return ' | '.join(descriptions)
        else:
            return element.get_text(strip=True)
    
    def _extract_seller_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract seller information"""
        seller_data = {}
        
        # Seller name
        seller_elem = soup.select_one("#sellerProfileTriggerId, .a-link-normal")
        if seller_elem:
            seller_data["name"] = seller_elem.get_text(strip=True)
        
        # Fulfilled by Amazon
        fulfillment_elem = soup.select_one("#merchant-info")
        if fulfillment_elem and "amazon" in fulfillment_elem.get_text().lower():
            seller_data["fulfilled_by_amazon"] = True
        
        return seller_data
    
    def _extract_shipping_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract shipping information"""
        shipping_data = {}
        
        # Delivery date
        delivery_elem = soup.select_one("#mir-layout-DELIVERY_BLOCK")
        if delivery_elem:
            shipping_data["delivery_info"] = delivery_elem.get_text(strip=True)
        
        # Shipping cost
        shipping_elem = soup.select_one(".a-color-secondary.a-text-bold")
        if shipping_elem and "shipping" in shipping_elem.get_text().lower():
            shipping_data["cost"] = shipping_elem.get_text(strip=True)
        
        return shipping_data
    
    def _extract_variants_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract product variants (size, color, etc.)"""
        variants = {}
        
        # Size variants
        size_elements = soup.select("#variation_size_name .selection")
        if size_elements:
            sizes = [elem.get_text(strip=True) for elem in size_elements]
            variants["sizes"] = sizes
        
        # Color variants
        color_elements = soup.select("#variation_color_name .selection")
        if color_elements:
            colors = [elem.get_text(strip=True) for elem in color_elements]
            variants["colors"] = colors
        
        return variants
    
    def _detect_amazon_page_type(self, url: str) -> str:
        """Detect Amazon page type from URL"""
        if '/dp/' in url or '/gp/product/' in url:
            return "product"
        elif '/s?' in url:
            return "search"
        elif '/stores/' in url:
            return "store"
        else:
            return "unknown"
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Amazon strategy has high confidence on Amazon URLs"""
        if 'amazon.com' in url or 'amazon.' in url:
            return 0.9
        return 0.1
    
    def supports_purpose(self, purpose: str) -> bool:
        """Amazon strategy supports product and e-commerce data"""
        supported_purposes = [
            "product_data", "price_monitoring", "ecommerce_analysis",
            "competitive_intelligence", "review_analysis"
        ]
        return purpose in supported_purposes
