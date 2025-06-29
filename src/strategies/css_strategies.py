#!/usr/bin/env python3
"""
CSS-Based Extraction Strategies
High-performance CSS selector strategies for common website patterns
"""

import asyncio
import time
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from .base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType, ExtractionField

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

class NewsCSSStrategy(BaseExtractionStrategy):
    """
    Optimized for news websites and articles
    
    Examples:
    - Extract article content from news sites
    - Get headlines and summaries
    - Scrape publication metadata
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        
        self.article_selectors = {
            "headline": [
                "h1, .headline, .title",
                "[data-testid*='headline']",
                ".article-title, .post-title",
                ".entry-title"
            ],
            "author": [
                ".author, .byline, .writer",
                "[data-testid*='author']",
                ".article-author, .post-author",
                "[rel='author']"
            ],
            "publish_date": [
                "time, .date, .published",
                "[data-testid*='date']",
                ".publish-date, .article-date",
                "[datetime]"
            ],
            "content": [
                ".article-content, .post-content",
                "[data-testid*='article-body']",
                ".entry-content, .story-body",
                "article .content, .article .body"
            ],
            "summary": [
                ".summary, .excerpt, .lead",
                "[data-testid*='summary']",
                ".article-summary, .post-excerpt"
            ],
            "category": [
                ".category, .section, .topic",
                "[data-testid*='category']",
                ".article-category"
            ],
            "tags": [
                ".tags, .keywords",
                "[data-testid*='tags']",
                ".article-tags, .post-tags"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check for article listing vs single article
            articles = self._find_article_listings(soup)
            
            if articles:
                extracted_data = {"articles": articles}
            else:
                # Single article
                article_data = self._extract_single_article(soup)
                extracted_data = article_data if article_data else {}
            
            # Extract structured data for articles
            structured_data = self.extract_structured_data(html_content)
            if structured_data:
                extracted_data["structured_data"] = structured_data
            
            confidence = self.calculate_confidence(
                extracted_data,
                ["headline", "content"] if "articles" not in extracted_data else ["articles"]
            )
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="NewsCSSStrategy", 
                execution_time=execution_time,
                metadata={
                    "articles_found": len(extracted_data.get("articles", [])),
                    "has_structured_data": bool(structured_data)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="NewsCSSStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _find_article_listings(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Find multiple articles on news homepage/category pages"""
        
        article_containers = [
            "article, .article",
            ".post, .story",
            "[data-testid*='article']",
            ".news-item, .article-item",
            ".entry, .story-item"
        ]
        
        articles = []
        
        for container_selector in article_containers:
            containers = soup.select(container_selector)
            
            if len(containers) > 1:
                for container in containers[:20]:  # Limit to first 20
                    article_data = self._extract_article_from_container(container)
                    if article_data:
                        articles.append(article_data)
                
                if articles:
                    break
        
        return articles
    
    def _extract_article_from_container(self, container) -> Dict[str, Any]:
        """Extract article data from container"""
        article = {}
        
        for field, selectors in self.article_selectors.items():
            value = self._extract_field_value(container, selectors)
            if value:
                if field == "content":
                    # Clean up content
                    article[field] = self._clean_article_content(value)
                else:
                    article[field] = value
        
        # Must have headline to be valid
        if article.get("headline"):
            return article
        return None
    
    def _extract_single_article(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract single article from article page"""
        article = {}
        
        for field, selectors in self.article_selectors.items():
            value = self._extract_field_value(soup, selectors)
            if value:
                if field == "content":
                    article[field] = self._clean_article_content(value)
                else:
                    article[field] = value
        
        return article if article else None
    
    def _clean_article_content(self, content: str) -> str:
        """Clean and format article content"""
        # Remove extra whitespace
        content = ' '.join(content.split())
        
        # Basic cleanup
        content = content.replace('\n\n', '\n').strip()
        
        return content if len(content) > 50 else None  # Minimum content length
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Estimate confidence for news extraction"""
        
        news_indicators = [
            "article", "news", "story", "headline", "byline",
            "publish", "author", "content", "journalism"
        ]
        
        confidence = 0.2
        content_lower = html_content.lower()
        
        # Check for news indicators
        indicator_count = sum(1 for indicator in news_indicators 
                            if indicator in content_lower)
        confidence += min(indicator_count * 0.08, 0.4)
        
        # Check for article-specific elements
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Article structured data
        if 'Article' in html_content and 'application/ld+json' in html_content:
            confidence += 0.3
        
        # Time elements (common in news)
        time_elements = soup.select("time, [datetime]")
        if time_elements:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Check if strategy supports the extraction purpose"""
        supported_purposes = [
            "news_content", "article_extraction", "content_analysis",
            "media_monitoring", "publication_data"
        ]
        return purpose in supported_purposes

class ContactCSSStrategy(BaseExtractionStrategy):
    """
    Specialized for extracting contact information from any website
    
    Examples:
    - Find all emails, phones, addresses on company websites
    - Extract social media links
    - Get contact forms and support information
    """
    
    def __init__(self, **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        
        self.contact_selectors = {
            "emails": [
                "a[href^='mailto:']",
                "[data-email]",
                ".email, .e-mail"
            ],
            "phones": [
                "a[href^='tel:']",
                ".phone, .telephone, .tel",
                "[data-phone], [data-tel]"
            ],
            "addresses": [
                ".address, .location",
                "[itemprop='address']",
                ".contact-address, .office-address"
            ],
            "social_links": [
                "a[href*='facebook.com'], a[href*='twitter.com'], a[href*='linkedin.com']",
                "a[href*='instagram.com'], a[href*='youtube.com']",
                ".social-links a, .social a"
            ],
            "contact_forms": [
                "form[action*='contact'], form[id*='contact']",
                ".contact-form, .contact-us-form"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            extracted_data = {}
            
            # Extract all contact information
            for field, selectors in self.contact_selectors.items():
                values = self._extract_multiple_values(soup, selectors, field)
                if values:
                    extracted_data[field] = values
            
            # Text-based extraction for emails and phones
            text_contacts = self._extract_from_text(html_content)
            if text_contacts:
                for key, values in text_contacts.items():
                    if key in extracted_data:
                        # Merge and deduplicate
                        all_values = extracted_data[key] + values
                        extracted_data[key] = list(set(all_values))
                    else:
                        extracted_data[key] = values
            
            confidence = self.calculate_confidence(
                extracted_data,
                ["emails", "phones", "addresses"]
            )
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="ContactCSSStrategy",
                execution_time=execution_time,
                metadata={
                    "total_contacts_found": sum(len(v) for v in extracted_data.values()),
                    "contact_types": list(extracted_data.keys())
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="ContactCSSStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _extract_multiple_values(self, soup: BeautifulSoup, selectors: List[str], field_type: str) -> List[str]:
        """Extract multiple values for a field type"""
        values = []
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    if field_type == "emails":
                        href = element.get('href', '')
                        if href.startswith('mailto:'):
                            email = href.replace('mailto:', '').split('?')[0]
                            if '@' in email:
                                values.append(email)
                        else:
                            text = element.get_text(strip=True)
                            if '@' in text:
                                values.append(text)
                    
                    elif field_type == "phones":
                        href = element.get('href', '')
                        if href.startswith('tel:'):
                            phone = href.replace('tel:', '')
                            values.append(phone)
                        else:
                            text = element.get_text(strip=True)
                            if text:
                                values.append(text)
                    
                    elif field_type == "social_links":
                        href = element.get('href', '')
                        if href and any(platform in href for platform in 
                                      ['facebook.com', 'twitter.com', 'linkedin.com', 
                                       'instagram.com', 'youtube.com']):
                            values.append(href)
                    
                    else:
                        text = element.get_text(strip=True)
                        if text:
                            values.append(text)
                            
            except Exception:
                continue
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(values))
    
    def _extract_from_text(self, html_content: str) -> Dict[str, List[str]]:
        """Extract emails and phones from plain text using regex"""
        import re
        
        # Get text content only
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        
        contacts = {}
        
        # Email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contacts["emails"] = list(set(emails))
        
        # Phone regex (multiple formats)
        phone_patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',   # (123) 456-7890
            r'\+\d{1,3}[-.\s]?\d{3,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}'  # International
        ]
        
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        
        if phones:
            contacts["phones"] = list(set(phones))
        
        return contacts
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Estimate confidence for contact extraction"""
        
        # Contact extraction can work on any page
        confidence = 0.5
        
        # Check for contact-specific content
        contact_indicators = [
            "contact", "email", "phone", "address", "social"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for indicator in contact_indicators 
                            if indicator in content_lower)
        confidence += min(indicator_count * 0.1, 0.3)
        
        # Check for actual contact elements
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if soup.select("a[href^='mailto:']"):
            confidence += 0.1
        if soup.select("a[href^='tel:']"):
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Check if strategy supports the extraction purpose"""
        supported_purposes = [
            "contact_discovery", "lead_generation", "business_intelligence",
            "social_media_analysis", "communication_channels"
        ]
        return purpose in supported_purposes

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
