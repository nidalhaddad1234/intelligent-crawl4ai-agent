#!/usr/bin/env python3
"""
E-commerce CSS Strategy
Optimized for e-commerce websites like Amazon, eBay, Shopify stores

Examples:
- Extract product details from Amazon
- Get pricing from online stores
- Scrape product catalogs
"""

import time
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.extraction.css_selectors.ecommerce")


class EcommerceCSSStrategy(BaseExtractionStrategy):
    """
    Optimized for e-commerce websites like Amazon, eBay, Shopify stores
    
    Examples:
    - Extract product details from Amazon
    - Get pricing from online stores
    - Scrape product catalogs
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        
        self.product_selectors = {
            "name": [
                "h1, .product-title, .product-name",
                "[data-testid*='product-title']",
                ".title, .name",
                "#product-title, #productTitle"
            ],
            "price": [
                ".price, .cost, .amount",
                "[data-testid*='price']",
                ".price-current, .current-price",
                ".sale-price, .regular-price",
                "[class*='price'], [id*='price']"
            ],
            "description": [
                ".description, .product-description",
                "[data-testid*='description']",
                ".details, .product-details",
                ".summary, .product-summary"
            ],
            "image": [
                ".product-image img, .main-image img",
                "[data-testid*='image'] img",
                ".gallery img, .product-gallery img",
                "img[src*='product']"
            ],
            "rating": [
                ".rating, .stars, .review-score",
                "[data-testid*='rating']",
                ".avg-rating, .average-rating"
            ],
            "availability": [
                ".stock, .availability, .in-stock",
                "[data-testid*='stock']",
                ".inventory-status"
            ],
            "brand": [
                ".brand, .manufacturer",
                "[data-testid*='brand']",
                ".product-brand"
            ],
            "sku": [
                ".sku, .product-id",
                "[data-sku], [data-product-id]"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check if it's a product listing page or single product
            products = self._find_product_listings(soup)
            
            if products:
                extracted_data = {"products": products}
            else:
                # Single product page
                product_data = self._extract_single_product(soup)
                extracted_data = product_data if product_data else {}
            
            # Extract structured data (JSON-LD for products)
            structured_data = self.extract_structured_data(html_content)
            if structured_data:
                extracted_data["structured_data"] = structured_data
            
            confidence = self.calculate_confidence(
                extracted_data, 
                ["name", "price"] if "products" not in extracted_data else ["products"]
            )
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="EcommerceCSSStrategy",
                execution_time=execution_time,
                metadata={
                    "products_found": len(extracted_data.get("products", [])),
                    "has_structured_data": bool(structured_data)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="EcommerceCSSStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _find_product_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find multiple products on category/search pages"""
        
        listing_containers = [
            ".product, .product-item",
            ".item, .search-item",
            "[data-testid*='product']",
            ".card, .product-card",
            ".result, .search-result"
        ]
        
        products = []
        
        for container_selector in listing_containers:
            containers = soup.select(container_selector)
            
            if len(containers) > 1:
                for container in containers[:30]:  # Limit to first 30
                    product_data = self._extract_product_from_container(container)
                    if product_data:
                        products.append(product_data)
                
                if products:
                    break
        
        return products
    
    def _extract_product_from_container(self, container) -> Dict[str, Any]:
        """Extract product data from container"""
        product = {}
        
        for field, selectors in self.product_selectors.items():
            if field == "image":
                # Special handling for images
                value = self._extract_image_src(container, selectors)
            else:
                value = self._extract_field_value(container, selectors)
            
            if value:
                product[field] = value
        
        # Must have name or price to be valid
        if product.get("name") or product.get("price"):
            return product
        return None
    
    def _extract_single_product(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract single product from product detail page"""
        product = {}
        
        for field, selectors in self.product_selectors.items():
            if field == "image":
                value = self._extract_image_src(soup, selectors)
            else:
                value = self._extract_field_value(soup, selectors)
            
            if value:
                product[field] = value
        
        return product if product else None
    
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
    
    def extract_structured_data(self, html_content: str) -> Dict[str, Any]:
        """Extract JSON-LD structured data for products"""
        import json
        import re
        
        # Find JSON-LD scripts
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        structured_data = {}
        
        for match in matches:
            try:
                data = json.loads(match.strip())
                
                # Check if it's product data
                if isinstance(data, dict):
                    if data.get('@type') == 'Product':
                        structured_data['product'] = data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') == 'Product':
                            structured_data['product'] = item
                            break
            except json.JSONDecodeError:
                continue
        
        return structured_data
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Estimate confidence for e-commerce extraction"""
        
        ecommerce_indicators = [
            "product", "price", "cart", "buy", "shop", "store",
            "catalog", "category", "checkout"
        ]
        
        confidence = 0.2
        content_lower = html_content.lower()
        
        # Check for e-commerce indicators
        indicator_count = sum(1 for indicator in ecommerce_indicators 
                            if indicator in content_lower)
        confidence += min(indicator_count * 0.1, 0.5)
        
        # Check for product-specific elements
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Price indicators
        price_elements = soup.select(".price, [class*='price'], [data-price]")
        if price_elements:
            confidence += 0.2
        
        # Product structured data
        if 'application/ld+json' in html_content and 'Product' in html_content:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Check if strategy supports the extraction purpose"""
        supported_purposes = [
            "product_data", "price_monitoring", "catalog_extraction",
            "ecommerce_analysis", "competitive_intelligence"
        ]
        return purpose in supported_purposes
