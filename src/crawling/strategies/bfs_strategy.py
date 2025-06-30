"""
BFS (Breadth-First Search) Deep Crawling Strategy
Explores websites level by level, discovering site structure systematically
"""

import asyncio
from typing import List, Set
from .base_strategy import DeepCrawlStrategy, CrawlResult, DeepCrawlConfig

class BFSDeepCrawlStrategy(DeepCrawlStrategy):
    """
    Breadth-First Search deep crawling strategy
    
    Explores websites level by level:
    - Level 0: Starting URL
    - Level 1: All links from starting URL  
    - Level 2: All links from Level 1 pages
    - etc.
    
    This approach is ideal for:
    - Site structure discovery
    - Finding all pages at a specific depth
    - Systematic exploration
    """
    
    def __init__(self, config: DeepCrawlConfig = None):
        super().__init__(config)
        self.current_level_urls: List[str] = []
        self.next_level_urls: List[str] = []
        
    async def crawl(self, starting_url: str) -> List[CrawlResult]:
        """
        Perform BFS crawling starting from the given URL
        
        Algorithm:
        1. Start with initial URL at depth 0
        2. Crawl all URLs at current depth level in parallel
        3. Collect all links from crawled pages  
        4. Move to next depth level
        5. Repeat until max depth or max pages reached
        """
        
        self.logger.info(f"Starting BFS crawl from: {starting_url}")
        self.logger.info(f"Config - Max depth: {self.config.max_depth}, Max pages: {self.config.max_pages}")
        
        # Initialize with starting URL
        normalized_start_url = self._normalize_url(starting_url)
        self.current_level_urls = [normalized_start_url]
        self.visited_urls.add(normalized_start_url)
        
        current_depth = 0
        
        # Process each depth level
        while (self.current_level_urls and 
               current_depth <= self.config.max_depth and 
               len(self.crawled_pages) < self.config.max_pages):
            
            self.logger.info(f"Processing depth {current_depth} with {len(self.current_level_urls)} URLs")
            
            # Crawl all URLs at current depth in parallel
            level_results = await self._crawl_level(self.current_level_urls, current_depth)
            
            # Add results to our collection
            self.crawled_pages.extend(level_results)
            
            # Collect URLs for next level
            self.next_level_urls = []
            for result in level_results:
                if result.success:
                    # Add all discovered links for next level
                    for link in result.links:
                        if self._should_crawl_url(link, current_depth + 1):
                            self.next_level_urls.append(link)
                            self.visited_urls.add(link)
            
            # Remove duplicates from next level
            self.next_level_urls = list(dict.fromkeys(self.next_level_urls))
            
            # Limit next level size to respect max_pages limit
            remaining_pages = self.config.max_pages - len(self.crawled_pages)
            if len(self.next_level_urls) > remaining_pages:
                self.next_level_urls = self.next_level_urls[:remaining_pages]
            
            self.logger.info(f"Depth {current_depth} complete. Found {len(self.next_level_urls)} URLs for next level")
            
            # Move to next level
            self.current_level_urls = self.next_level_urls
            current_depth += 1
            
            # Add delay between levels if configured
            if self.config.delay_between_requests > 0 and self.current_level_urls:
                await asyncio.sleep(self.config.delay_between_requests)
        
        self.logger.info(f"BFS crawl complete. Crawled {len(self.crawled_pages)} pages")
        return self.crawled_pages
    
    async def _crawl_level(self, urls: List[str], depth: int) -> List[CrawlResult]:
        """
        Crawl all URLs at a specific depth level in parallel
        """
        if not urls:
            return []
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def crawl_with_semaphore(url: str) -> CrawlResult:
            async with semaphore:
                # Determine parent URL for tracking
                parent_url = ""
                if depth > 0 and self.crawled_pages:
                    # Find a parent from previous level that links to this URL
                    for prev_result in reversed(self.crawled_pages):
                        if url in prev_result.links:
                            parent_url = prev_result.url
                            break
                
                result = await self._crawl_single_page(url, depth, parent_url)
                
                # Add delay between individual requests if configured
                if self.config.delay_between_requests > 0:
                    await asyncio.sleep(self.config.delay_between_requests)
                
                return result
        
        # Create tasks for all URLs in this level
        tasks = [crawl_with_semaphore(url) for url in urls]
        
        # Execute all tasks in parallel
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and handle any exceptions
            level_results = []
            for url, result in zip(urls, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Exception crawling {url}: {result}")
                    # Create failed result
                    failed_result = CrawlResult(
                        url=url,
                        success=False,
                        depth=depth,
                        error=str(result)
                    )
                    level_results.append(failed_result)
                else:
                    level_results.append(result)
            
            return level_results
            
        except Exception as e:
            self.logger.error(f"Failed to crawl level {depth}: {e}")
            # Return failed results for all URLs in this level
            return [
                CrawlResult(url=url, success=False, depth=depth, error=str(e))
                for url in urls
            ]
    
    def get_site_map(self) -> dict:
        """
        Generate a site map showing the hierarchical structure discovered
        """
        site_map = {
            "root": {},
            "levels": {},
            "statistics": self.get_crawl_statistics()
        }
        
        # Group pages by depth level
        for result in self.crawled_pages:
            if result.depth not in site_map["levels"]:
                site_map["levels"][result.depth] = []
            
            page_info = {
                "url": result.url,
                "title": result.title,
                "success": result.success,
                "links_count": len(result.links) if result.success else 0,
                "parent_url": result.parent_url
            }
            
            site_map["levels"][result.depth].append(page_info)
        
        # Create root structure
        if self.crawled_pages:
            root_page = next((r for r in self.crawled_pages if r.depth == 0), None)
            if root_page:
                site_map["root"] = {
                    "url": root_page.url,
                    "title": root_page.title,
                    "total_pages_discovered": len(self.crawled_pages)
                }
        
        return site_map
    
    def get_crawl_summary(self) -> dict:
        """
        Get a comprehensive summary of the BFS crawl operation
        """
        stats = self.get_crawl_statistics()
        site_map = self.get_site_map()
        
        # Analyze URL patterns
        url_patterns = {}
        for result in self.crawled_pages:
            if result.success:
                # Extract path patterns
                from urllib.parse import urlparse
                parsed = urlparse(result.url)
                path_parts = [p for p in parsed.path.split('/') if p]
                
                if path_parts:
                    pattern = '/' + '/'.join(path_parts[:-1]) if len(path_parts) > 1 else '/'
                    url_patterns[pattern] = url_patterns.get(pattern, 0) + 1
        
        return {
            "crawl_statistics": stats,
            "site_structure": site_map,
            "url_patterns": url_patterns,
            "top_patterns": sorted(url_patterns.items(), key=lambda x: x[1], reverse=True)[:10],
            "discovery_insights": {
                "most_productive_depth": self._get_most_productive_depth(),
                "avg_links_per_page": stats["total_links_discovered"] / stats["successful_crawls"] if stats["successful_crawls"] > 0 else 0,
                "exploration_efficiency": stats["successful_crawls"] / len(self.visited_urls) if self.visited_urls else 0
            }
        }
    
    def _get_most_productive_depth(self) -> int:
        """Find which depth level discovered the most new URLs"""
        depth_productivity = {}
        
        for result in self.crawled_pages:
            if result.success:
                depth = result.depth
                links_count = len(result.links)
                depth_productivity[depth] = depth_productivity.get(depth, 0) + links_count
        
        if not depth_productivity:
            return 0
            
        return max(depth_productivity.items(), key=lambda x: x[1])[0]
