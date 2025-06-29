"""
Base Deep Crawling Strategy
Provides foundation for all deep crawling implementations
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urljoin, urlparse
import logging

logger = logging.getLogger("deep_crawling")

@dataclass 
class CrawlResult:
    """Result from crawling a single page"""
    url: str
    success: bool
    content: str = ""
    title: str = ""
    links: List[str] = None
    depth: int = 0
    parent_url: str = ""
    crawl_time: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.links is None:
            self.links = []
        if self.metadata is None:
            self.metadata = {}

@dataclass
class DeepCrawlConfig:
    """Configuration for deep crawling operations"""
    max_depth: int = 3
    max_pages: int = 100
    max_concurrent: int = 10
    delay_between_requests: float = 1.0
    respect_robots_txt: bool = True
    follow_redirects: bool = True
    timeout: int = 30
    include_patterns: List[str] = None
    exclude_patterns: List[str] = None
    allowed_domains: List[str] = None
    
    def __post_init__(self):
        if self.include_patterns is None:
            self.include_patterns = []
        if self.exclude_patterns is None:
            self.exclude_patterns = []
        if self.allowed_domains is None:
            self.allowed_domains = []

class DeepCrawlStrategy(ABC):
    """
    Abstract base class for deep crawling strategies
    """
    
    def __init__(self, config: DeepCrawlConfig = None):
        self.config = config or DeepCrawlConfig()
        self.visited_urls: Set[str] = set()
        self.crawled_pages: List[CrawlResult] = []
        self.url_queue: List[str] = []
        self.logger = logging.getLogger(f"deep_crawl.{self.__class__.__name__}")
        
    @abstractmethod
    async def crawl(self, starting_url: str) -> List[CrawlResult]:
        """
        Perform deep crawling starting from the given URL
        
        Args:
            starting_url: URL to start crawling from
            
        Returns:
            List of CrawlResult objects for all crawled pages
        """
        pass
    
    def _normalize_url(self, url: str, base_url: str = None) -> str:
        """Normalize URL for consistent handling"""
        if base_url and not url.startswith(('http://', 'https://')):
            url = urljoin(base_url, url)
        
        # Remove fragment
        if '#' in url:
            url = url.split('#')[0]
            
        # Remove trailing slash for consistency
        if url.endswith('/') and url != '/':
            url = url.rstrip('/')
            
        return url
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        return urlparse(url).netloc.lower()
    
    def _should_crawl_url(self, url: str, depth: int) -> bool:
        """
        Determine if a URL should be crawled based on configuration
        """
        # Check if already visited
        if url in self.visited_urls:
            return False
            
        # Check depth limit
        if depth > self.config.max_depth:
            return False
            
        # Check page limit
        if len(self.crawled_pages) >= self.config.max_pages:
            return False
            
        # Check domain restrictions
        if self.config.allowed_domains:
            url_domain = self._extract_domain(url)
            if not any(domain in url_domain for domain in self.config.allowed_domains):
                return False
        
        # Check include patterns
        if self.config.include_patterns:
            if not any(pattern in url for pattern in self.config.include_patterns):
                return False
        
        # Check exclude patterns  
        if self.config.exclude_patterns:
            if any(pattern in url for pattern in self.config.exclude_patterns):
                return False
                
        return True
    
    def _extract_links_from_content(self, content: str, base_url: str) -> List[str]:
        """
        Extract all links from HTML content
        """
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            links = []
            
            # Extract all href attributes from anchor tags
            for link_tag in soup.find_all('a', href=True):
                href = link_tag['href']
                normalized_url = self._normalize_url(href, base_url)
                
                # Only include HTTP/HTTPS links
                if normalized_url.startswith(('http://', 'https://')):
                    links.append(normalized_url)
            
            # Remove duplicates while preserving order
            return list(dict.fromkeys(links))
            
        except Exception as e:
            self.logger.warning(f"Failed to extract links from content: {e}")
            return []
    
    async def _crawl_single_page(self, url: str, depth: int, parent_url: str = "") -> CrawlResult:
        """
        Crawl a single page and return the result
        """
        start_time = time.time()
        
        try:
            # Import here to avoid circular imports
            from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
            
            browser_config = BrowserConfig(
                headless=True,
                verbose=False
            )
            
            run_config = CrawlerRunConfig(
                cache_mode="bypass",
                timeout=self.config.timeout * 1000,  # Convert to milliseconds
                wait_for="networkidle"
            )
            
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(url=url, config=run_config)
                
                if result.success:
                    # Extract links for further crawling
                    links = self._extract_links_from_content(result.html, url)
                    
                    crawl_result = CrawlResult(
                        url=url,
                        success=True,
                        content=result.cleaned_html or result.html,
                        title=result.metadata.get('title', ''),
                        links=links,
                        depth=depth,
                        parent_url=parent_url,
                        crawl_time=time.time() - start_time,
                        metadata={
                            'status_code': result.status_code,
                            'content_length': len(result.html) if result.html else 0,
                            'links_found': len(links)
                        }
                    )
                else:
                    crawl_result = CrawlResult(
                        url=url,
                        success=False,
                        depth=depth,
                        parent_url=parent_url,
                        crawl_time=time.time() - start_time,
                        error=result.error_message or "Unknown error"
                    )
                    
                return crawl_result
                
        except Exception as e:
            self.logger.error(f"Failed to crawl {url}: {e}")
            return CrawlResult(
                url=url,
                success=False,
                depth=depth,
                parent_url=parent_url,
                crawl_time=time.time() - start_time,
                error=str(e)
            )
    
    def get_crawl_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the crawling operation
        """
        successful_crawls = [r for r in self.crawled_pages if r.success]
        failed_crawls = [r for r in self.crawled_pages if not r.success]
        
        total_links = sum(len(r.links) for r in successful_crawls)
        avg_crawl_time = sum(r.crawl_time for r in self.crawled_pages) / len(self.crawled_pages) if self.crawled_pages else 0
        
        return {
            "total_pages_crawled": len(self.crawled_pages),
            "successful_crawls": len(successful_crawls),
            "failed_crawls": len(failed_crawls),
            "success_rate": len(successful_crawls) / len(self.crawled_pages) if self.crawled_pages else 0,
            "total_links_discovered": total_links,
            "average_crawl_time": avg_crawl_time,
            "unique_domains": len(set(self._extract_domain(r.url) for r in successful_crawls)),
            "max_depth_reached": max((r.depth for r in self.crawled_pages), default=0)
        }
