
# Additional Deep Crawling Tools - Week 2 Completion

@ai_tool(
    name="deep_crawl_dfs",
    description="Deep exploration using depth-first strategy for comprehensive content discovery",
    category="discovery",
    examples=[
        create_example(
            "Explore deep product catalog structure",
            starting_url="https://ecommerce.com",
            purpose="product_discovery",
            max_depth=5,
            focus_strategy="depth"
        ),
        create_example(
            "Find detailed company information in nested pages",
            starting_url="https://company.com/about",
            purpose="company_information",
            max_depth=4
        )
    ],
    capabilities=[
        "Deep path exploration",
        "Comprehensive content discovery",
        "Nested structure analysis",
        "Path tracking and analysis",
        "Content depth optimization"
    ],
    performance={
        "speed": "medium",
        "reliability": "high",
        "cost": "medium"
    }
)
async def deep_crawl_dfs(
    starting_url: str,
    purpose: str = "comprehensive_discovery",
    max_depth: int = 4,
    max_pages: int = 80,
    max_concurrent: int = 8,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    focus_strategy: str = "depth"  # "depth" or "quality"
) -> Dict[str, Any]:
    """
    Perform deep crawling using DFS strategy for thorough exploration
    
    Args:
        starting_url: URL to start crawling from
        purpose: Crawling purpose (same as BFS options)
        max_depth: Maximum depth to explore (higher than BFS for deep exploration)
        max_pages: Maximum total pages to crawl
        max_concurrent: Maximum concurrent requests
        include_patterns: URL patterns to include
        exclude_patterns: URL patterns to exclude
        focus_strategy: "depth" for maximum depth, "quality" for balanced approach
        
    Returns:
        Dictionary with deep exploration results and path analysis
    """
    try:
        # Configure for deep exploration
        if focus_strategy == "depth":
            config = DeepCrawlConfig(
                max_depth=max_depth,
                max_pages=max_pages,
                max_concurrent=max_concurrent,
                delay_between_requests=0.8,  # Slightly faster for deep exploration
                include_patterns=include_patterns or [],
                exclude_patterns=exclude_patterns or []
            )
        else:  # quality focus
            config = DeepCrawlConfig(
                max_depth=max(max_depth - 1, 2),  # Slightly less depth
                max_pages=max_pages,
                max_concurrent=max_concurrent + 2,  # More concurrent for efficiency
                delay_between_requests=1.0,
                include_patterns=include_patterns or [],
                exclude_patterns=exclude_patterns or []
            )
        
        # Set up filtering based on purpose
        if purpose == "contact_discovery":
            url_filter = CommonFilters.contact_discovery()
        elif purpose == "product_discovery":
            url_filter = CommonFilters.product_discovery()
        elif purpose == "news_content":
            url_filter = CommonFilters.news_content()
        else:
            url_filter = CommonFilters.comprehensive_discovery()
        
        # Initialize DFS crawler
        crawler = DFSDeepCrawlStrategy(config)
        
        # Override URL filtering
        original_should_crawl = crawler._should_crawl_url
        def enhanced_should_crawl(url: str, depth: int) -> bool:
            if not original_should_crawl(url, depth):
                return False
            return url_filter.should_crawl(url, {"depth": depth})
        
        crawler._should_crawl_url = enhanced_should_crawl
        
        # Perform deep crawling
        crawl_results = await crawler.crawl(starting_url)
        
        # Get DFS-specific analysis
        dfs_statistics = crawler.get_dfs_statistics()
        content_depth_analysis = crawler.get_content_depth_analysis()
        crawl_paths = crawler.get_crawl_paths()
        deepest_paths = crawler.get_deepest_paths(10)
        
        # Organize results
        successful_pages = [r for r in crawl_results if r.success]
        failed_pages = [r for r in crawl_results if not r.success]
        
        return {
            "success": len(successful_pages) > 0,
            "starting_url": starting_url,
            "purpose": purpose,
            "strategy": "depth_first_search",
            "focus_strategy": focus_strategy,
            "discovered_pages": {
                "successful": [
                    {
                        "url": r.url,
                        "title": r.title,
                        "depth": r.depth,
                        "parent_url": r.parent_url,
                        "content_length": len(r.content),
                        "links_count": len(r.links),
                        "crawl_time": r.crawl_time
                    }
                    for r in successful_pages
                ],
                "failed": [
                    {"url": r.url, "depth": r.depth, "error": r.error}
                    for r in failed_pages
                ]
            },
            "exploration_analysis": {
                "deepest_paths": deepest_paths,
                "crawl_paths": crawl_paths,
                "depth_distribution": dfs_statistics.get("depth_distribution", {}),
                "max_depth_reached": dfs_statistics.get("max_depth_reached", 0),
                "average_depth": dfs_statistics.get("average_depth", 0),
                "path_efficiency": dfs_statistics.get("depth_efficiency", 0)
            },
            "content_analysis": content_depth_analysis,
            "statistics": dfs_statistics,
            "insights": {
                "total_pages_discovered": len(successful_pages),
                "exploration_strategy": "Depth-first exploration prioritizes deep content discovery",
                "best_depth_for_content": content_depth_analysis.get("insights", {}).get("richest_depth", 0),
                "content_quality_trend": content_depth_analysis.get("insights", {}).get("depth_quality_trend", "unknown"),
                "deepest_valuable_path": deepest_paths[0] if deepest_paths else None
            },
            "recommendations": {
                "optimal_depth_range": f"0-{min(max_depth, dfs_statistics.get('max_depth_reached', 0) + 1)}",
                "content_strategy": "Focus on depths with highest content richness",
                "next_exploration": "Consider BFS for broader discovery or Best-First for quality focus"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "starting_url": starting_url,
            "error": str(e),
            "strategy": "depth_first_search"
        }


@ai_tool(
    name="smart_priority_crawl",
    description="AI-powered priority crawling that finds the best content first using intelligent scoring",
    category="intelligence",
    examples=[
        create_example(
            "Find the most important company pages efficiently",
            starting_url="https://company.com",
            crawl_goal="contact_information",
            quality_focus=True
        ),
        create_example(
            "Discover top product pages with limited resources",
            starting_url="https://store.com",
            crawl_goal="product_catalog",
            max_pages=30,
            efficiency_mode=True
        )
    ],
    capabilities=[
        "Intelligent URL prioritization",
        "Quality-first exploration",
        "Adaptive scoring algorithms",
        "Resource-efficient crawling",
        "Goal-oriented discovery"
    ],
    performance={
        "speed": "high",
        "reliability": "very_high",
        "cost": "low"
    }
)
async def smart_priority_crawl(
    starting_url: str,
    crawl_goal: str = "comprehensive_analysis",
    max_pages: int = 50,
    quality_focus: bool = True,
    efficiency_mode: bool = False,
    custom_scorer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Intelligent priority-based crawling for optimal resource utilization
    
    Args:
        starting_url: URL to start crawling from
        crawl_goal: Goal for crawling (contact_information, product_catalog, 
                   company_information, news_content, comprehensive_analysis)
        max_pages: Maximum pages to crawl (enforced strictly for efficiency)
        quality_focus: Whether to prioritize content quality over quantity
        efficiency_mode: Optimize for speed and resource usage
        custom_scorer: Custom scoring strategy name
        
    Returns:
        Dictionary with prioritized results and adaptation insights
    """
    try:
        # Configure for priority-based crawling
        if efficiency_mode:
            config = DeepCrawlConfig(
                max_depth=3,  # Limit depth for efficiency
                max_pages=max_pages,
                max_concurrent=12,  # Higher concurrency
                delay_between_requests=0.5,  # Faster requests
                include_patterns=[],
                exclude_patterns=[]
            )
        else:
            config = DeepCrawlConfig(
                max_depth=4,
                max_pages=max_pages,
                max_concurrent=8,
                delay_between_requests=1.0,
                include_patterns=[],
                exclude_patterns=[]
            )
        
        # Select scorer based on goal and preferences
        if custom_scorer:
            if custom_scorer == "contact_focused":
                scorer = CommonScorers.contact_discovery()
            elif custom_scorer == "product_focused":
                scorer = CommonScorers.product_discovery()
            elif custom_scorer == "news_focused":
                scorer = CommonScorers.news_content()
            elif custom_scorer == "quality_focused":
                scorer = CommonScorers.quality_focused()
            else:
                scorer = CommonScorers.comprehensive_discovery()
        else:
            # Auto-select based on goal
            goal_scorer_map = {
                "contact_information": CommonScorers.contact_discovery(),
                "product_catalog": CommonScorers.product_discovery(),
                "company_information": CommonScorers.comprehensive_discovery(),
                "news_content": CommonScorers.news_content(),
                "comprehensive_analysis": CommonScorers.quality_focused() if quality_focus else CommonScorers.comprehensive_discovery()
            }
            scorer = goal_scorer_map.get(crawl_goal, CommonScorers.comprehensive_discovery())
        
        # Set up filtering
        goal_filter_map = {
            "contact_information": CommonFilters.contact_discovery(),
            "product_catalog": CommonFilters.product_discovery(),
            "news_content": CommonFilters.news_content(),
            "comprehensive_analysis": CommonFilters.comprehensive_discovery(),
            "company_information": CommonFilters.comprehensive_discovery()
        }
        url_filter = goal_filter_map.get(crawl_goal, CommonFilters.comprehensive_discovery())
        
        # Initialize Best-First crawler
        crawler = BestFirstCrawlStrategy(config, scorer)
        
        # Override URL filtering
        original_should_crawl = crawler._should_crawl_url
        def enhanced_should_crawl(url: str, depth: int) -> bool:
            if not original_should_crawl(url, depth):
                return False
            return url_filter.should_crawl(url, {"depth": depth})
        
        crawler._should_crawl_url = enhanced_should_crawl
        
        # Perform priority crawling
        crawl_results = await crawler.crawl(starting_url)
        
        # Get priority-specific insights
        priority_insights = crawler.get_priority_insights()
        adaptive_insights = crawler.get_adaptive_insights()
        
        # Organize and analyze results
        successful_pages = [r for r in crawl_results if r.success]
        failed_pages = [r for r in crawl_results if not r.success]
        
        # Sort by quality scores
        scored_pages = []
        for page in successful_pages:
            score = crawler.url_scores.get(page.url, 0.0)
            scored_pages.append({
                "url": page.url,
                "title": page.title,
                "quality_score": score,
                "depth": page.depth,
                "content_length": len(page.content),
                "links_count": len(page.links),
                "crawl_time": page.crawl_time
            })
        
        scored_pages.sort(key=lambda x: x["quality_score"], reverse=True)
        
        return {
            "success": len(successful_pages) > 0,
            "starting_url": starting_url,
            "crawl_goal": crawl_goal,
            "strategy": "best_first_priority",
            "configuration": {
                "quality_focus": quality_focus,
                "efficiency_mode": efficiency_mode,
                "scorer_used": scorer.get_scorer_name(),
                "max_pages": max_pages
            },
            "prioritized_results": {
                "top_quality_pages": scored_pages[:10],  # Top 10 highest quality
                "all_pages": scored_pages,
                "failed_attempts": [
                    {"url": r.url, "error": r.error} for r in failed_pages
                ]
            },
            "priority_analysis": priority_insights,
            "adaptation_insights": adaptive_insights,
            "efficiency_metrics": {
                "pages_per_minute": len(successful_pages) / max(sum(r.crawl_time for r in crawl_results) / 60, 0.1),
                "quality_hit_rate": len([p for p in scored_pages if p["quality_score"] > 0.7]) / len(scored_pages) if scored_pages else 0,
                "resource_utilization": len(successful_pages) / max_pages,
                "average_quality_score": sum(p["quality_score"] for p in scored_pages) / len(scored_pages) if scored_pages else 0
            },
            "strategic_insights": {
                "best_discovery": scored_pages[0] if scored_pages else None,
                "quality_distribution": {
                    "excellent (0.9+)": len([p for p in scored_pages if p["quality_score"] >= 0.9]),
                    "good (0.7-0.9)": len([p for p in scored_pages if 0.7 <= p["quality_score"] < 0.9]),
                    "fair (0.5-0.7)": len([p for p in scored_pages if 0.5 <= p["quality_score"] < 0.7]),
                    "poor (0.0-0.5)": len([p for p in scored_pages if p["quality_score"] < 0.5])
                },
                "strategy_effectiveness": adaptive_insights.get("strategy_effectiveness", {}),
                "recommendations": adaptive_insights.get("recommendations", [])
            },
            "next_actions": {
                "high_value_targets": [p["url"] for p in scored_pages[:5]],
                "suggested_extractions": f"Focus on top {min(5, len(scored_pages))} pages for detailed data extraction",
                "optimization_suggestions": [
                    "Adjust quality threshold based on results",
                    "Consider expanding search if high-quality pages found",
                    "Use discovered patterns to refine future crawls"
                ]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "starting_url": starting_url,
            "crawl_goal": crawl_goal,
            "strategy": "best_first_priority",
            "error": str(e)
        }
