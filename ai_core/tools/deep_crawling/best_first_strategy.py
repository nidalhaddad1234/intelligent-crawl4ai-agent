"""
Best-First Crawling Strategy
Prioritizes URLs based on quality scores and strategic importance
"""

import asyncio
import heapq
from typing import List, Set, Dict, Any, Optional
from .base_strategy import DeepCrawlStrategy, CrawlResult, DeepCrawlConfig
from .scorers import URLScorer, CommonScorers, ScoringEngine

class BestFirstCrawlStrategy(DeepCrawlStrategy):
    """
    Best-First Search crawling strategy
    
    Prioritizes URLs based on scoring algorithms:
    - Maintains a priority queue of URLs to crawl
    - Always crawls the highest-scoring URL next
    - Adapts scoring based on discoveries
    - Optimizes for finding high-value content quickly
    
    This approach is ideal for:
    - Finding specific types of content efficiently
    - Quality-focused crawling with limited resources
    - Adaptive exploration based on discoveries
    - Goal-oriented crawling (contacts, products, etc.)
    """
    
    def __init__(self, config: DeepCrawlConfig = None, scorer: URLScorer = None):
        super().__init__(config)
        self.scorer = scorer or CommonScorers.comprehensive_discovery()
        self.scoring_engine = ScoringEngine(self.scorer)
        
        # Priority queue: (negative_score, url, depth, parent_url, context)
        # Using negative score because heapq is a min-heap
        self.priority_queue: List[tuple] = []
        self.url_scores: Dict[str, float] = {}
        self.discovery_context: Dict[str, Any] = {}
        
    async def crawl(self, starting_url: str) -> List[CrawlResult]:
        """
        Perform Best-First crawling starting from the given URL
        
        Algorithm:
        1. Score and add starting URL to priority queue
        2. Pop highest-scoring URL from queue
        3. Crawl the URL and score discovered links
        4. Add high-scoring links to queue
        5. Repeat until queue empty or limits reached
        """
        
        self.logger.info(f"Starting Best-First crawl from: {starting_url}")
        self.logger.info(f"Scorer: {self.scorer.get_scorer_name()}")
        
        # Initialize with starting URL
        normalized_start_url = self._normalize_url(starting_url)
        start_score = self.scorer.score_url(normalized_start_url, {"depth": 0})
        
        heapq.heappush(self.priority_queue, (
            -start_score,  # Negative for max-heap behavior
            normalized_start_url,
            0,  # depth
            "",  # parent_url
            {"is_starting_url": True}
        ))
        
        self.visited_urls.add(normalized_start_url)
        self.url_scores[normalized_start_url] = start_score
        
        crawl_iteration = 0
        
        # Process URLs by priority
        while (self.priority_queue and 
               len(self.crawled_pages) < self.config.max_pages):
            
            # Pop highest-priority URL
            neg_score, current_url, current_depth, parent_url, context = heapq.heappop(self.priority_queue)
            current_score = -neg_score
            
            self.logger.info(f"Iteration {crawl_iteration}: Crawling {current_url} (score: {current_score:.3f}, depth: {current_depth})")
            
            # Crawl current URL
            result = await self._crawl_single_page(current_url, current_depth, parent_url)
            self.crawled_pages.append(result)
            crawl_iteration += 1
            
            # Update discovery context based on results
            self._update_discovery_context(result, context)
            
            # If successful and within depth limit, score and queue discovered links
            if (result.success and 
                current_depth < self.config.max_depth and
                len(self.crawled_pages) < self.config.max_pages):
                
                # Score discovered links
                discovered_links = [link for link in result.links 
                                  if self._should_crawl_url(link, current_depth + 1)]
                
                if discovered_links:
                    # Create context for scoring
                    scoring_context = {
                        "depth": current_depth + 1,
                        "parent_url": current_url,
                        "parent_score": current_score,
                        "discovery_context": self.discovery_context,
                        "crawl_iteration": crawl_iteration
                    }
                    
                    # Score all discovered links
                    link_scores = self.scoring_engine.score_urls(discovered_links, scoring_context)
                    
                    # Add high-scoring links to priority queue
                    added_count = 0
                    for link, score in link_scores.items():
                        if link not in self.visited_urls:
                            # Apply score boost based on parent quality
                            boosted_score = self._apply_score_boost(score, current_score, scoring_context)
                            
                            heapq.heappush(self.priority_queue, (
                                -boosted_score,
                                link,
                                current_depth + 1,
                                current_url,
                                {"parent_score": current_score, "original_score": score}
                            ))
                            
                            self.visited_urls.add(link)
                            self.url_scores[link] = boosted_score
                            added_count += 1
                    
                    self.logger.info(f"Added {added_count} high-scoring URLs to queue. Queue size: {len(self.priority_queue)}")
                    
                    # Prune queue if it gets too large
                    await self._prune_queue_if_needed()
            
            # Add delay between requests if configured
            if self.config.delay_between_requests > 0:
                await asyncio.sleep(self.config.delay_between_requests)
        
        self.logger.info(f"Best-First crawl complete. Crawled {len(self.crawled_pages)} pages")
        return self.crawled_pages
    
    def _update_discovery_context(self, result: CrawlResult, context: Dict[str, Any]):
        """Update discovery context based on crawl results"""
        if not result.success:
            return
        
        # Track content types discovered
        if "content_types" not in self.discovery_context:
            self.discovery_context["content_types"] = set()
        
        # Simple content type detection
        if "contact" in result.url.lower() or "contact" in result.title.lower():
            self.discovery_context["content_types"].add("contact")
        if "product" in result.url.lower() or "product" in result.title.lower():
            self.discovery_context["content_types"].add("product")
        if "about" in result.url.lower() or "about" in result.title.lower():
            self.discovery_context["content_types"].add("about")
        if "news" in result.url.lower() or "blog" in result.url.lower():
            self.discovery_context["content_types"].add("news")
        
        # Track quality trends
        if "quality_scores" not in self.discovery_context:
            self.discovery_context["quality_scores"] = []
        
        content_quality = len(result.content) / 1000  # Simple quality metric
        self.discovery_context["quality_scores"].append(content_quality)
        
        # Track link density
        if "link_densities" not in self.discovery_context:
            self.discovery_context["link_densities"] = []
        
        link_density = len(result.links) / max(len(result.content), 1) * 1000
        self.discovery_context["link_densities"].append(link_density)
        
    def _apply_score_boost(self, base_score: float, parent_score: float, context: Dict[str, Any]) -> float:
        """Apply score boost based on parent quality and discovery context"""
        boosted_score = base_score
        
        # Boost based on parent quality
        if parent_score > 0.8:
            boosted_score *= 1.2  # 20% boost for high-quality parents
        elif parent_score > 0.6:
            boosted_score *= 1.1  # 10% boost for good parents
        
        # Boost based on discovery trends
        if "quality_scores" in self.discovery_context:
            recent_quality = self.discovery_context["quality_scores"][-5:]  # Last 5 pages
            if recent_quality and sum(recent_quality) / len(recent_quality) > 2.0:
                boosted_score *= 1.15  # Boost if we're finding good content
        
        # Boost for diversification (finding new content types)
        content_types_found = len(self.discovery_context.get("content_types", set()))
        if content_types_found < 3:  # Encourage diversity early on
            boosted_score *= 1.1
        
        return min(boosted_score, 1.0)  # Cap at 1.0
    
    async def _prune_queue_if_needed(self):
        """Prune priority queue if it becomes too large"""
        max_queue_size = self.config.max_pages
        
        if len(self.priority_queue) > max_queue_size:
            # Keep only the highest-scoring URLs
            self.priority_queue = heapq.nsmallest(max_queue_size, self.priority_queue)
            heapq.heapify(self.priority_queue)
            self.logger.info(f"Pruned queue to {len(self.priority_queue)} URLs")
    
    def get_priority_insights(self) -> Dict[str, Any]:
        """Get insights about the prioritization process"""
        successful_results = [r for r in self.crawled_pages if r.success]
        
        if not successful_results:
            return {"message": "No successful crawls to analyze"}
        
        # Analyze score vs. order correlation
        crawl_order_scores = []
        for i, result in enumerate(successful_results):
            score = self.url_scores.get(result.url, 0.0)
            crawl_order_scores.append((i, score))
        
        # Calculate if higher scores were generally crawled first
        score_order_correlation = self._calculate_score_order_correlation(crawl_order_scores)
        
        # Analyze score distribution
        all_scores = list(self.url_scores.values())
        score_stats = {
            "mean": sum(all_scores) / len(all_scores),
            "max": max(all_scores),
            "min": min(all_scores),
            "high_quality_count": len([s for s in all_scores if s > 0.8]),
            "medium_quality_count": len([s for s in all_scores if 0.5 <= s <= 0.8]),
            "low_quality_count": len([s for s in all_scores if s < 0.5])
        }
        
        # Find best discoveries
        best_pages = sorted(successful_results, 
                          key=lambda r: self.url_scores.get(r.url, 0.0), 
                          reverse=True)[:5]
        
        return {
            "prioritization_effectiveness": score_order_correlation,
            "score_statistics": score_stats,
            "discovery_context": self.discovery_context,
            "best_discoveries": [
                {
                    "url": r.url,
                    "title": r.title,
                    "score": self.url_scores.get(r.url, 0.0),
                    "content_length": len(r.content),
                    "links_found": len(r.links)
                }
                for r in best_pages
            ],
            "scoring_engine_stats": self.scoring_engine.get_scoring_statistics(),
            "queue_efficiency": {
                "max_queue_size": len(self.priority_queue) + len(self.crawled_pages),
                "final_queue_size": len(self.priority_queue),
                "utilization_rate": len(self.crawled_pages) / (len(self.priority_queue) + len(self.crawled_pages))
            }
        }
    
    def _calculate_score_order_correlation(self, crawl_order_scores: List[tuple]) -> float:
        """Calculate correlation between scores and crawl order"""
        if len(crawl_order_scores) < 2:
            return 0.0
        
        # Simple correlation: higher scores should have lower order numbers (crawled earlier)
        score_order_pairs = [(score, order) for order, score in crawl_order_scores]
        score_order_pairs.sort(key=lambda x: x[0], reverse=True)  # Sort by score descending
        
        # Calculate how well the order follows the score ranking
        perfect_order_score = 0
        for i, (score, actual_order) in enumerate(score_order_pairs):
            expected_order = i
            order_deviation = abs(actual_order - expected_order)
            perfect_order_score += 1.0 / (1.0 + order_deviation)
        
        # Normalize to 0-1 scale
        return perfect_order_score / len(score_order_pairs)
    
    def get_adaptive_insights(self) -> Dict[str, Any]:
        """Get insights about how the strategy adapted during crawling"""
        
        # Analyze score evolution over time
        crawl_timeline = []
        for i, result in enumerate(self.crawled_pages):
            if result.success:
                score = self.url_scores.get(result.url, 0.0)
                crawl_timeline.append({
                    "iteration": i,
                    "url": result.url,
                    "score": score,
                    "depth": result.depth,
                    "content_quality": len(result.content) / 1000
                })
        
        # Analyze adaptation patterns
        adaptation_patterns = {
            "score_trend": self._analyze_score_trend(crawl_timeline),
            "depth_strategy": self._analyze_depth_strategy(crawl_timeline),
            "quality_improvement": self._analyze_quality_improvement(crawl_timeline),
            "discovery_efficiency": self._analyze_discovery_efficiency()
        }
        
        return {
            "crawl_timeline": crawl_timeline[-10:],  # Last 10 for brevity
            "adaptation_patterns": adaptation_patterns,
            "strategy_effectiveness": self._calculate_strategy_effectiveness(),
            "recommendations": self._generate_strategy_recommendations()
        }
    
    def _analyze_score_trend(self, timeline: List[Dict[str, Any]]) -> str:
        """Analyze if scores improved over time"""
        if len(timeline) < 5:
            return "insufficient_data"
        
        early_scores = [item["score"] for item in timeline[:len(timeline)//3]]
        late_scores = [item["score"] for item in timeline[-len(timeline)//3:]]
        
        early_avg = sum(early_scores) / len(early_scores)
        late_avg = sum(late_scores) / len(late_scores)
        
        if late_avg > early_avg * 1.1:
            return "improving"
        elif late_avg < early_avg * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _analyze_depth_strategy(self, timeline: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze depth exploration patterns"""
        depth_distribution = {}
        for item in timeline:
            depth = item["depth"]
            depth_distribution[depth] = depth_distribution.get(depth, 0) + 1
        
        return {
            "depth_distribution": depth_distribution,
            "preferred_depth": max(depth_distribution.keys(), 
                                 key=depth_distribution.get, 
                                 default=0),
            "depth_diversity": len(depth_distribution)
        }
    
    def _analyze_quality_improvement(self, timeline: List[Dict[str, Any]]) -> float:
        """Calculate quality improvement rate"""
        if len(timeline) < 3:
            return 0.0
        
        qualities = [item["content_quality"] for item in timeline]
        
        # Simple linear trend
        n = len(qualities)
        sum_x = sum(range(n))
        sum_y = sum(qualities)
        sum_xy = sum(i * qualities[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0.0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        return slope
    
    def _analyze_discovery_efficiency(self) -> float:
        """Calculate how efficiently the strategy discovered valuable content"""
        successful_results = [r for r in self.crawled_pages if r.success]
        
        if not successful_results:
            return 0.0
        
        # Calculate efficiency as high-quality pages per crawl
        high_quality_pages = len([r for r in successful_results 
                                if self.url_scores.get(r.url, 0.0) > 0.7])
        
        return high_quality_pages / len(successful_results)
    
    def _calculate_strategy_effectiveness(self) -> Dict[str, float]:
        """Calculate overall strategy effectiveness metrics"""
        return {
            "quality_focus": self._analyze_discovery_efficiency(),
            "resource_efficiency": len([r for r in self.crawled_pages if r.success]) / len(self.crawled_pages) if self.crawled_pages else 0,
            "goal_achievement": len(self.discovery_context.get("content_types", set())) / 4.0,  # Assuming 4 main content types
            "prioritization_accuracy": self.get_priority_insights().get("prioritization_effectiveness", 0.0)
        }
    
    def _generate_strategy_recommendations(self) -> List[str]:
        """Generate recommendations for improving the strategy"""
        recommendations = []
        
        effectiveness = self._calculate_strategy_effectiveness()
        
        if effectiveness["quality_focus"] < 0.3:
            recommendations.append("Consider adjusting scoring weights to better identify high-quality content")
        
        if effectiveness["resource_efficiency"] < 0.8:
            recommendations.append("Review URL filtering to reduce failed crawl attempts")
        
        if effectiveness["goal_achievement"] < 0.5:
            recommendations.append("Adjust discovery goals or scoring criteria to find more diverse content types")
        
        if effectiveness["prioritization_accuracy"] < 0.6:
            recommendations.append("Fine-tune scoring algorithm to better predict page value")
        
        if not recommendations:
            recommendations.append("Strategy is performing well - consider expanding scope or depth")
        
        return recommendations
