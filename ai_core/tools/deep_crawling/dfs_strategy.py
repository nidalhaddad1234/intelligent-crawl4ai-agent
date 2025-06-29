"""
DFS (Depth-First Search) Deep Crawling Strategy
Explores websites by going deep into specific paths before exploring breadth
"""

import asyncio
from typing import List, Set, Dict, Any
from .base_strategy import DeepCrawlStrategy, CrawlResult, DeepCrawlConfig

class DFSDeepCrawlStrategy(DeepCrawlStrategy):
    """
    Depth-First Search deep crawling strategy
    
    Explores websites by diving deep into specific paths:
    - Follows first available link to maximum depth
    - Backtracks when depth limit reached or no more links
    - Explores alternative paths systematically
    
    This approach is ideal for:
    - Finding deeply nested content
    - Following specific content paths
    - Detailed exploration of site sections
    - When you want comprehensive coverage of specific areas
    """
    
    def __init__(self, config: DeepCrawlConfig = None):
        super().__init__(config)
        self.crawl_stack: List[Dict[str, Any]] = []  # Stack for DFS traversal
        self.path_history: List[str] = []  # Track current path
        
    async def crawl(self, starting_url: str) -> List[CrawlResult]:
        """
        Perform DFS crawling starting from the given URL
        
        Algorithm:
        1. Start with initial URL on stack
        2. Pop URL from stack and crawl it
        3. Add discovered links to stack (LIFO order)
        4. Continue until stack is empty or limits reached
        """
        
        self.logger.info(f"Starting DFS crawl from: {starting_url}")
        self.logger.info(f"Config - Max depth: {self.config.max_depth}, Max pages: {self.config.max_pages}")
        
        # Initialize with starting URL
        normalized_start_url = self._normalize_url(starting_url)
        self.crawl_stack.append({
            "url": normalized_start_url,
            "depth": 0,
            "parent_url": "",
            "path": [normalized_start_url]
        })
        self.visited_urls.add(normalized_start_url)
        
        # Process URLs using DFS (stack-based)
        while (self.crawl_stack and 
               len(self.crawled_pages) < self.config.max_pages):
            
            # Pop from stack (LIFO - most recently added first)
            current_item = self.crawl_stack.pop()
            current_url = current_item["url"]
            current_depth = current_item["depth"]
            current_parent = current_item["parent_url"]
            current_path = current_item["path"]
            
            self.logger.info(f"Crawling depth {current_depth}: {current_url}")
            self.path_history = current_path
            
            # Crawl current URL
            result = await self._crawl_single_page(current_url, current_depth, current_parent)
            self.crawled_pages.append(result)
            
            # If successful and not at max depth, add discovered links to stack
            if (result.success and 
                current_depth < self.config.max_depth and
                len(self.crawled_pages) < self.config.max_pages):
                
                # Add links to stack in reverse order (so first link is processed first)
                discovered_links = []
                for link in reversed(result.links):
                    if self._should_crawl_url(link, current_depth + 1):
                        # Check for cycles in current path
                        if link not in current_path:
                            discovered_links.append({
                                "url": link,
                                "depth": current_depth + 1,
                                "parent_url": current_url,
                                "path": current_path + [link]
                            })
                            self.visited_urls.add(link)
                
                # Add to stack (will be processed in LIFO order)
                self.crawl_stack.extend(discovered_links)
                
                # Limit stack size to prevent memory issues
                max_stack_size = self.config.max_pages * 2
                if len(self.crawl_stack) > max_stack_size:
                    self.crawl_stack = self.crawl_stack[-max_stack_size:]
                
                self.logger.info(f"Added {len(discovered_links)} URLs to stack. Stack size: {len(self.crawl_stack)}")
            
            # Add delay between requests if configured
            if self.config.delay_between_requests > 0:
                await asyncio.sleep(self.config.delay_between_requests)
        
        self.logger.info(f"DFS crawl complete. Crawled {len(self.crawled_pages)} pages")
        return self.crawled_pages
    
    def get_crawl_paths(self) -> List[Dict[str, Any]]:
        """
        Get the paths explored during DFS crawling
        
        Returns:
            List of path information showing how deep the crawler went
        """
        paths = {}
        
        for result in self.crawled_pages:
            if result.success:
                # Reconstruct path to this URL
                path_key = f"depth_{result.depth}"
                if path_key not in paths:
                    paths[path_key] = []
                
                paths[path_key].append({
                    "url": result.url,
                    "title": result.title,
                    "parent_url": result.parent_url,
                    "content_length": len(result.content),
                    "links_found": len(result.links)
                })
        
        return paths
    
    def get_deepest_paths(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the deepest paths discovered during crawling
        
        Args:
            limit: Maximum number of paths to return
            
        Returns:
            List of deepest paths with their metadata
        """
        # Sort by depth (deepest first)
        successful_results = [r for r in self.crawled_pages if r.success]
        deepest_results = sorted(successful_results, key=lambda x: x.depth, reverse=True)
        
        deepest_paths = []
        for result in deepest_results[:limit]:
            # Reconstruct full path
            path_chain = self._reconstruct_path_chain(result)
            
            deepest_paths.append({
                "final_url": result.url,
                "final_title": result.title,
                "depth_reached": result.depth,
                "path_chain": path_chain,
                "content_quality": len(result.content) / 1000,  # Simple quality metric
                "discovery_value": len(result.links)  # How many new links it provided
            })
        
        return deepest_paths
    
    def _reconstruct_path_chain(self, target_result: CrawlResult) -> List[Dict[str, str]]:
        """Reconstruct the full path chain to a specific result"""
        chain = []
        current = target_result
        
        # Build chain backwards from target to root
        while current:
            chain.insert(0, {
                "url": current.url,
                "title": current.title,
                "depth": current.depth
            })
            
            # Find parent
            if current.parent_url:
                parent = next((r for r in self.crawled_pages 
                             if r.url == current.parent_url), None)
                current = parent
            else:
                break
        
        return chain
    
    def get_dfs_statistics(self) -> Dict[str, Any]:
        """
        Get DFS-specific statistics
        """
        base_stats = self.get_crawl_statistics()
        
        # DFS-specific metrics
        successful_results = [r for r in self.crawled_pages if r.success]
        
        depth_distribution = {}
        for result in successful_results:
            depth = result.depth
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
        
        # Calculate path efficiency
        max_depth = max((r.depth for r in successful_results), default=0)
        avg_depth = sum(r.depth for r in successful_results) / len(successful_results) if successful_results else 0
        
        # Stack usage statistics
        max_stack_size = getattr(self, '_max_stack_size', 0)
        
        dfs_stats = {
            "depth_distribution": depth_distribution,
            "max_depth_reached": max_depth,
            "average_depth": avg_depth,
            "depth_efficiency": avg_depth / max_depth if max_depth > 0 else 0,
            "path_completion_rate": len([r for r in successful_results if r.depth == max_depth]) / len(successful_results) if successful_results else 0,
            "deepest_paths": self.get_deepest_paths(5),
            "stack_usage": {
                "max_stack_size": max_stack_size,
                "final_stack_size": len(self.crawl_stack)
            }
        }
        
        return {**base_stats, **dfs_stats}
    
    def get_content_depth_analysis(self) -> Dict[str, Any]:
        """
        Analyze content quality at different depths
        """
        successful_results = [r for r in self.crawled_pages if r.success]
        
        depth_analysis = {}
        for result in successful_results:
            depth = result.depth
            if depth not in depth_analysis:
                depth_analysis[depth] = {
                    "page_count": 0,
                    "total_content_length": 0,
                    "total_links_found": 0,
                    "pages": []
                }
            
            depth_info = depth_analysis[depth]
            depth_info["page_count"] += 1
            depth_info["total_content_length"] += len(result.content)
            depth_info["total_links_found"] += len(result.links)
            depth_info["pages"].append({
                "url": result.url,
                "title": result.title,
                "content_length": len(result.content),
                "links_count": len(result.links)
            })
        
        # Calculate averages and insights
        for depth, info in depth_analysis.items():
            info["avg_content_length"] = info["total_content_length"] / info["page_count"]
            info["avg_links_per_page"] = info["total_links_found"] / info["page_count"]
            info["content_richness"] = info["avg_content_length"] / 1000  # Simple richness metric
        
        return {
            "depth_analysis": depth_analysis,
            "insights": {
                "richest_depth": max(depth_analysis.keys(), 
                                   key=lambda d: depth_analysis[d]["content_richness"], 
                                   default=0),
                "most_connected_depth": max(depth_analysis.keys(), 
                                          key=lambda d: depth_analysis[d]["avg_links_per_page"], 
                                          default=0),
                "depth_quality_trend": self._analyze_depth_quality_trend(depth_analysis)
            }
        }
    
    def _analyze_depth_quality_trend(self, depth_analysis: Dict[int, Dict[str, Any]]) -> str:
        """Analyze if content quality improves or degrades with depth"""
        if len(depth_analysis) < 2:
            return "insufficient_data"
        
        depths = sorted(depth_analysis.keys())
        quality_scores = [depth_analysis[d]["content_richness"] for d in depths]
        
        # Simple trend analysis
        increasing_count = sum(1 for i in range(1, len(quality_scores)) 
                             if quality_scores[i] > quality_scores[i-1])
        decreasing_count = sum(1 for i in range(1, len(quality_scores)) 
                             if quality_scores[i] < quality_scores[i-1])
        
        if increasing_count > decreasing_count:
            return "improving_with_depth"
        elif decreasing_count > increasing_count:
            return "degrading_with_depth"
        else:
            return "stable_across_depths"
