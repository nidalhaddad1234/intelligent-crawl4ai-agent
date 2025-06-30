#!/usr/bin/env python3
"""
News CSS Strategy
Optimized for news websites and articles

Examples:
- Extract article content from news sites
- Get headlines and summaries
- Scrape publication metadata
"""

import time
import logging
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.extraction.css_selectors.news")


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
    
    def _extract_field_value(self, container, selectors: List[str]) -> str:
        """Extract field value using multiple selector fallbacks"""
        for selector in selectors:
            try:
                elements = container.select(selector)
                for element in elements:
                    # Special handling for datetime
                    if element.get('datetime'):
                        return element.get('datetime')
                    
                    text = element.get_text(strip=True)
                    if text and len(text) > 1:
                        return text
            except Exception:
                continue
        return None
    
    def _clean_article_content(self, content: str) -> str:
        """Clean and format article content"""
        # Remove extra whitespace
        content = ' '.join(content.split())
        
        # Basic cleanup
        content = content.replace('\n\n', '\n').strip()
        
        return content if len(content) > 50 else None  # Minimum content length
    
    def extract_structured_data(self, html_content: str) -> Dict[str, Any]:
        """Extract JSON-LD structured data for articles"""
        import json
        import re
        
        # Find JSON-LD scripts
        json_ld_pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(json_ld_pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        structured_data = {}
        
        for match in matches:
            try:
                data = json.loads(match.strip())
                
                # Check if it's article data
                if isinstance(data, dict):
                    if data.get('@type') in ['Article', 'NewsArticle']:
                        structured_data['article'] = data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') in ['Article', 'NewsArticle']:
                            structured_data['article'] = item
                            break
            except json.JSONDecodeError:
                continue
        
        return structured_data
    
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
