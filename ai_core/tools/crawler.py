"""
Crawler Tool - AI-discoverable web crawling capabilities

This tool wraps Crawl4AI functionality and makes it available to the AI planner.
"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, CSSExtractionStrategy

from ..registry import ai_tool, create_example, ToolExample
from .deep_crawling.bfs_strategy import BFSDeepCrawlStrategy
from .deep_crawling.dfs_strategy import DFSDeepCrawlStrategy
from .deep_crawling.best_first_strategy import BestFirstCrawlStrategy
from .deep_crawling.base_strategy import DeepCrawlConfig
from .deep_crawling.filters import URLPatternFilter, DomainFilter, CommonFilters, FilterChain
from .deep_crawling.scorers import CommonScorers, ScoringEngine
from .content_processing.filters import BM25ContentFilter, LLMContentFilter, PruningContentFilter, RelevantContentFilter, ContentFilterChain
from .content_processing.chunking import RegexChunking, SemanticChunking, HierarchicalChunking
from .content_processing.quality import ContentQualityAssessor, ContentEnhancer
from .performance.dispatchers import MemoryAdaptiveDispatcher, SemaphoreDispatcher
from .performance.rate_limiter import TokenBucketLimiter, AdaptiveRateLimiter
from .performance.proxy_manager import ProxyManager, RoundRobinProxyStrategy, WeightedProxyStrategy
from .performance.monitor import CrawlerMonitor


@ai_tool(
    name="crawl_web",
    description="Extract data from websites using various strategies including CSS selectors, LLM extraction, and smart detection",
    category="extraction",
    examples=[
        create_example(
            "Extract product prices from e-commerce site",
            url="https://example.com/products",
            strategy="css",
            css_selectors={"price": ".product-price", "title": ".product-title"}
        ),
        create_example(
            "Extract article content using AI",
            url="https://example.com/article",
            strategy="llm",
            extraction_prompt="Extract the main article content, author, and publication date"
        ),
        create_example(
            "Auto-detect and extract data",
            url="https://example.com",
            strategy="auto"
        )
    ],
    capabilities=[
        "Extract structured data from web pages",
        "Handle JavaScript-rendered content",
        "Use CSS selectors for precise extraction",
        "Apply AI/LLM for intelligent extraction",
        "Auto-detect content structure",
        "Handle pagination and infinite scroll",
        "Manage sessions and cookies",
        "Bypass anti-bot measures"
    ],
    performance={
        "speed": "medium",
        "reliability": "high",
        "cost": "low"
    }
)
async def crawl_web(
    url: str,
    strategy: str = "auto",
    css_selectors: Optional[Dict[str, str]] = None,
    extraction_prompt: Optional[str] = None,
    js_render: bool = True,
    wait_for: Optional[str] = None,
    screenshot: bool = False,
    proxy: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Crawl a web page and extract data using specified strategy
    
    Args:
        url: Target URL to crawl
        strategy: Extraction strategy - 'css', 'llm', 'auto', 'regex'
        css_selectors: CSS selectors for extraction (when strategy='css')
        extraction_prompt: Prompt for LLM extraction (when strategy='llm')
        js_render: Whether to render JavaScript
        wait_for: CSS selector to wait for before extraction
        screenshot: Whether to take a screenshot
        proxy: Proxy URL to use
        headers: Custom headers to send
        
    Returns:
        Dictionary containing extracted data, metadata, and status
    """
    try:
        # Configure browser
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        
        # Configure crawler
        crawler_config = CrawlerRunConfig(
            wait_for=wait_for,
            screenshot=screenshot,
            proxy=proxy,
            headers=headers,
            js_code="window.scrollTo(0, document.body.scrollHeight);" if js_render else None
        )
        
        # Select extraction strategy
        extraction_strategy = None
        
        if strategy == "css" and css_selectors:
            # Create CSS extraction strategy
            extraction_strategy = CSSExtractionStrategy(
                schema={
                    "name": f"Extract from {url}",
                    "baseSelector": "body",
                    "fields": [
                        {
                            "name": key,
                            "selector": selector,
                            "type": "text"
                        }
                        for key, selector in css_selectors.items()
                    ]
                }
            )
        elif strategy == "llm" and extraction_prompt:
            # Create LLM extraction strategy
            extraction_strategy = LLMExtractionStrategy(
                provider="ollama",
                api_token="",
                extraction_prompt=extraction_prompt,
                chunk_size=2000,
                overlap=100
            )
        
        # Perform crawl
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(
                url=url,
                config=crawler_config,
                extraction_strategy=extraction_strategy
            )
            
            # Process results
            extracted_data = {}
            
            if result.extracted_content:
                extracted_data = result.extracted_content
            elif strategy == "auto":
                # Auto extraction - get main content
                extracted_data = {
                    "content": result.markdown,
                    "title": result.metadata.get("title", ""),
                    "description": result.metadata.get("description", ""),
                    "links": result.links[:20] if result.links else []
                }
            
            return {
                "success": result.success,
                "url": url,
                "data": extracted_data,
                "metadata": {
                    "title": result.metadata.get("title"),
                    "description": result.metadata.get("description"),
                    "status_code": result.status_code,
                    "content_length": len(result.html) if result.html else 0,
                    "extraction_strategy": strategy
                },
                "screenshot": result.screenshot if screenshot else None,
                "error": result.error_message if not result.success else None
            }
            
    except Exception as e:
        return {
            "success": False,
            "url": url,
            "data": {},
            "metadata": {},
            "error": str(e)
        }


@ai_tool(
    name="process_content_intelligently",
    description="Advanced content processing with filtering, chunking, and quality enhancement",
    category="processing",
    examples=[
        create_example(
            "Filter and enhance content for quality",
            content="Raw scraped content...",
            processing_type="quality_enhancement",
            keywords=["contact", "information"] 
        ),
        create_example(
            "Chunk content for AI processing",
            content="Long document content...",
            processing_type="chunking",
            chunk_strategy="semantic"
        )
    ],
    capabilities=[
        "BM25-based content filtering",
        "LLM-powered quality assessment",
        "Noise and irrelevant content removal",
        "Semantic content chunking",
        "Hierarchical document structure",
        "Content quality enhancement",
        "Intelligent text processing"
    ],
    performance={
        "speed": "medium",
        "reliability": "high", 
        "cost": "low"
    }
)
async def process_content_intelligently(
    content: str,
    processing_type: str = "quality_enhancement",
    keywords: Optional[List[str]] = None,
    chunk_strategy: str = "regex",
    quality_threshold: float = 0.7,
    remove_noise: bool = True
) -> Dict[str, Any]:
    """
    Process content using advanced filtering, chunking, and quality enhancement
    
    Args:
        content: Raw content to process
        processing_type: Type of processing (quality_enhancement, filtering, chunking, enhancement)
        keywords: Keywords for relevance filtering
        chunk_strategy: Chunking strategy (regex, semantic, hierarchical)
        quality_threshold: Minimum quality threshold (0.0-1.0)
        remove_noise: Whether to remove noise and irrelevant content
        
    Returns:
        Dictionary with processed content and analysis
    """
    try:
        if not content or not content.strip():
            return {
                "success": False,
                "error": "Empty content provided",
                "processed_content": "",
                "analysis": {}
            }
        
        processed_content = content
        analysis = {"original_length": len(content)}
        
        if processing_type in ["quality_enhancement", "filtering"]:
            # Apply content filtering
            filters = []
            
            if remove_noise:
                filters.append(PruningContentFilter(remove_noise=True))
            
            if keywords:
                filters.append(RelevantContentFilter(keywords=keywords))
                filters.append(BM25ContentFilter(keywords=keywords, relevance_threshold=quality_threshold))
            
            # Apply LLM quality filtering
            filters.append(LLMContentFilter(quality_threshold=quality_threshold))
            
            if filters:
                filter_chain = ContentFilterChain(filters, logic="AND")
                filter_result = filter_chain.filter(processed_content, {"keywords": keywords})
                
                processed_content = filter_result.content
                analysis["filtering"] = {
                    "filters_applied": len(filters),
                    "quality_score": filter_result.score,
                    "filtered_sections": len(filter_result.filtered_sections),
                    "reduction_ratio": 1 - (len(processed_content) / len(content)) if content else 0
                }
        
        if processing_type in ["quality_enhancement", "enhancement"]:
            # Assess and enhance quality
            quality_assessor = ContentQualityAssessor()
            quality_metrics = quality_assessor.assess_quality(processed_content, {"keywords": keywords})
            
            enhancer = ContentEnhancer()
            enhanced_content, enhancement_summary = enhancer.enhance(processed_content, quality_metrics)
            
            processed_content = enhanced_content
            analysis["quality_assessment"] = {
                "overall_score": quality_metrics.overall_score,
                "readability_score": quality_metrics.readability_score,
                "information_density": quality_metrics.information_density,
                "coherence_score": quality_metrics.coherence_score,
                "completeness_score": quality_metrics.completeness_score,
                "linguistic_quality": quality_metrics.linguistic_quality
            }
            analysis["enhancement"] = enhancement_summary
        
        if processing_type == "chunking":
            # Apply content chunking
            if chunk_strategy == "semantic":
                chunker = SemanticChunking(target_chunk_size=1000, similarity_threshold=0.7)
            elif chunk_strategy == "hierarchical":
                chunker = HierarchicalChunking(chunk_sizes=[2000, 1000, 500])
            else:  # regex
                chunker = RegexChunking(chunk_size=1000, overlap=100)
            
            chunks = chunker.chunk(processed_content)
            
            analysis["chunking"] = {
                "strategy": chunk_strategy,
                "total_chunks": len(chunks),
                "chunks": [
                    {
                        "id": chunk.chunk_id,
                        "size": len(chunk.content),
                        "start_position": chunk.start_position,
                        "end_position": chunk.end_position,
                        "metadata": chunk.metadata
                    }
                    for chunk in chunks
                ]
            }
            
            # Return chunks as processed content
            processed_content = "\n\n---CHUNK---\n\n".join(chunk.content for chunk in chunks)
        
        analysis["processed_length"] = len(processed_content)
        analysis["processing_type"] = processing_type
        
        return {
            "success": True,
            "processed_content": processed_content,
            "analysis": analysis,
            "metadata": {
                "original_length": len(content),
                "processed_length": len(processed_content),
                "processing_type": processing_type,
                "quality_threshold": quality_threshold,
                "keywords_used": keywords or []
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "processed_content": content,
            "analysis": {}
        }


@ai_tool(
    name="crawl_enterprise_scale",
    description="Enterprise-scale crawling with adaptive performance and resource management",
    category="scaling",
    examples=[
        create_example(
            "Crawl 1000+ URLs with enterprise performance",
            urls=["https://example1.com", "https://example2.com"],
            processing_strategy="adaptive",
            max_concurrent=20,
            rate_limit=10.0
        ),
        create_example(
            "High-volume crawling with proxy rotation",
            urls=["https://shop1.com", "https://shop2.com"],
            processing_strategy="high_volume",
            use_proxies=True,
            proxy_rotation="weighted"
        )
    ],
    capabilities=[
        "Memory-adaptive concurrency scaling",
        "Intelligent rate limiting",
        "Proxy rotation and management",
        "Real-time performance monitoring",
        "Resource usage optimization",
        "Enterprise-grade reliability",
        "Automatic error recovery"
    ],
    performance={
        "speed": "very_high",
        "reliability": "very_high",
        "cost": "medium"
    }
)
async def crawl_enterprise_scale(
    urls: List[str],
    processing_strategy: str = "adaptive",
    max_concurrent: int = 20,
    rate_limit: float = 10.0,
    use_proxies: bool = False,
    proxy_rotation: str = "round_robin",
    monitoring_enabled: bool = True,
    extraction_strategy: str = "auto",
    css_selectors: Optional[Dict[str, str]] = None,
    extraction_prompt: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform enterprise-scale crawling with advanced performance management
    
    Args:
        urls: List of URLs to crawl (supports 1000+ URLs)
        processing_strategy: Strategy (adaptive, high_volume, balanced, quality_focused)
        max_concurrent: Maximum concurrent requests
        rate_limit: Requests per second limit
        use_proxies: Whether to use proxy rotation
        proxy_rotation: Proxy strategy (round_robin, weighted, failover)
        monitoring_enabled: Enable real-time monitoring
        extraction_strategy: Content extraction method
        css_selectors: CSS selectors for extraction
        extraction_prompt: LLM extraction prompt
        
    Returns:
        Dictionary with enterprise crawling results and analytics
    """
    try:
        if not urls:
            return {
                "success": False,
                "error": "No URLs provided",
                "results": {},
                "analytics": {}
            }
        
        start_time = time.time()
        
        # Configure strategy-specific settings
        if processing_strategy == "adaptive":
            dispatcher = MemoryAdaptiveDispatcher()
            rate_limiter = AdaptiveRateLimiter()
        elif processing_strategy == "high_volume":
            dispatcher = SemaphoreDispatcher()
            rate_limiter = TokenBucketLimiter()
            max_concurrent = min(max_concurrent * 2, 50)  # Increase for high volume
        else:  # balanced, quality_focused
            dispatcher = SemaphoreDispatcher()
            rate_limiter = TokenBucketLimiter()
        
        # Initialize monitoring if enabled
        monitor = None
        if monitoring_enabled:
            monitor = CrawlerMonitor()
            await monitor.start()
        
        # Initialize proxy manager if needed
        proxy_manager = None
        if use_proxies:
            # Mock proxy configuration - in production, load from config
            from .performance.proxy_manager import ProxyConfig
            mock_proxies = [
                ProxyConfig(host="proxy1.example.com", port=8080),
                ProxyConfig(host="proxy2.example.com", port=8080),
                ProxyConfig(host="proxy3.example.com", port=8080)
            ]
            
            strategy_map = {
                "round_robin": RoundRobinProxyStrategy(),
                "weighted": WeightedProxyStrategy(),
                "failover": RoundRobinProxyStrategy()  # Simplified
            }
            
            proxy_manager = ProxyManager(
                proxies=mock_proxies,
                strategy=strategy_map.get(proxy_rotation, RoundRobinProxyStrategy())
            )
            await proxy_manager.start()
        
        # Create crawling tasks
        async def crawl_with_enterprise_features(url: str):
            task_start = time.time()
            
            try:
                # Rate limiting
                await rate_limiter.wait_for_tokens(1)
                
                # Get proxy if available
                proxy = None
                if proxy_manager:
                    proxy_config = proxy_manager.get_proxy()
                    if proxy_config:
                        proxy = proxy_config.url
                
                # Record crawler start
                if monitor:
                    monitor.record_crawler_start()
                
                # Perform crawl
                result = await crawl_web(
                    url=url,
                    strategy=extraction_strategy,
                    css_selectors=css_selectors,
                    extraction_prompt=extraction_prompt,
                    proxy=proxy
                )
                
                task_time = time.time() - task_start
                
                # Record results
                if monitor:
                    monitor.record_request(
                        success=result.get("success", False),
                        response_time=task_time,
                        bytes_downloaded=result.get("metadata", {}).get("content_length", 0)
                    )
                    monitor.record_page_processed()
                    monitor.record_crawler_stop()
                
                # Record proxy usage
                if proxy_manager and proxy_config:
                    proxy_manager.record_usage(
                        proxy_config,
                        result.get("success", False),
                        task_time
                    )
                
                # Record rate limiter result
                if hasattr(rate_limiter, 'record_success'):
                    rate_limiter.record_success(result.get("success", False))
                
                return result
                
            except Exception as e:
                task_time = time.time() - task_start
                
                if monitor:
                    monitor.record_request(False, task_time, 0)
                    monitor.record_crawler_stop()
                
                if proxy_manager and proxy_config:
                    proxy_manager.record_usage(proxy_config, False, task_time)
                
                return {
                    "success": False,
                    "url": url,
                    "error": str(e),
                    "metadata": {"task_time": task_time}
                }
        
        # Create task functions
        tasks = [lambda u=url: crawl_with_enterprise_features(u) for url in urls]
        
        # Execute with dispatcher
        results = await dispatcher.dispatch(tasks)
        
        execution_time = time.time() - start_time
        
        # Organize results
        successful_results = [r for r in results if isinstance(r, dict) and r.get("success", False)]
        failed_results = [r for r in results if isinstance(r, dict) and not r.get("success", False)]
        error_results = [r for r in results if isinstance(r, Exception)]
        
        # Collect analytics
        analytics = {
            "execution_time": execution_time,
            "total_urls": len(urls),
            "successful_crawls": len(successful_results),
            "failed_crawls": len(failed_results) + len(error_results),
            "success_rate": len(successful_results) / len(urls) if urls else 0,
            "avg_requests_per_second": len(urls) / execution_time if execution_time > 0 else 0,
            "processing_strategy": processing_strategy,
            "dispatcher_stats": dispatcher.get_statistics(),
            "rate_limiter_stats": rate_limiter.get_statistics()
        }
        
        if proxy_manager:
            analytics["proxy_stats"] = proxy_manager.get_statistics()
            await proxy_manager.stop()
        
        if monitor:
            analytics["monitoring_data"] = monitor.get_dashboard_data()
            await monitor.stop()
        
        # Format results for return
        results_dict = {}
        for i, (url, result) in enumerate(zip(urls, results)):
            if isinstance(result, Exception):
                results_dict[url] = {
                    "success": False,
                    "error": str(result)
                }
            else:
                results_dict[url] = result
        
        return {
            "success": len(successful_results) > 0,
            "results": results_dict,
            "analytics": analytics,
            "performance_insights": {
                "optimal_concurrency": analytics["dispatcher_stats"].get("current_concurrency", max_concurrent),
                "rate_limit_effectiveness": analytics["rate_limiter_stats"].get("success_rate", 1.0),
                "recommended_batch_size": min(len(urls), max_concurrent * 5),
                "scaling_recommendation": "increase_concurrency" if analytics["success_rate"] > 0.95 else "optimize_reliability"
            },
            "metadata": {
                "processing_strategy": processing_strategy,
                "max_concurrent": max_concurrent,
                "rate_limit": rate_limit,
                "proxy_rotation": proxy_rotation if use_proxies else None,
                "monitoring_enabled": monitoring_enabled
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": {},
            "analytics": {}
        }


# NEW: Deep Crawling Capabilities

@ai_tool(
    name="deep_crawl_bfs",
    description="Discover and crawl entire websites using intelligent site exploration",
    category="discovery",
    examples=[
        create_example(
            "Discover all contact pages from company website",
            starting_url="https://company.com",
            purpose="contact_discovery",
            max_depth=3,
            max_pages=50
        ),
        create_example(
            "Find all product pages from e-commerce site",
            starting_url="https://shop.com",
            purpose="product_discovery",
            include_patterns=["*/product*", "*/shop*"],
            max_depth=4
        )
    ],
    capabilities=[
        "Automatically discover site structure",
        "Intelligent URL filtering and prioritization",
        "Breadth-first systematic exploration",
        "Configurable depth and page limits",
        "Pattern-based URL filtering",
        "Domain restriction support",
        "Performance monitoring and statistics"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "medium"
    }
)
async def deep_crawl_bfs(
    starting_url: str,
    purpose: str = "comprehensive_discovery",
    max_depth: int = 3,
    max_pages: int = 100,
    max_concurrent: int = 10,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    allowed_domains: Optional[List[str]] = None,
    delay_between_requests: float = 1.0
) -> Dict[str, Any]:
    """
    Perform deep crawling using BFS strategy to discover and explore websites
    
    Args:
        starting_url: URL to start crawling from
        purpose: Crawling purpose (contact_discovery, product_discovery, news_content, comprehensive_discovery)
        max_depth: Maximum depth to crawl (0 = starting page only)
        max_pages: Maximum total pages to crawl
        max_concurrent: Maximum concurrent requests
        include_patterns: URL patterns to include (e.g., ["*/contact*", "*/about*"])
        exclude_patterns: URL patterns to exclude (e.g., ["*/admin*", "*/api/*"])
        allowed_domains: Restrict crawling to specific domains
        delay_between_requests: Delay between requests in seconds
        
    Returns:
        Dictionary with discovered pages, site map, and crawling statistics
    """
    try:
        # Configure deep crawling
        config = DeepCrawlConfig(
            max_depth=max_depth,
            max_pages=max_pages,
            max_concurrent=max_concurrent,
            delay_between_requests=delay_between_requests,
            include_patterns=include_patterns or [],
            exclude_patterns=exclude_patterns or [],
            allowed_domains=allowed_domains or []
        )
        
        # Set up URL filtering based on purpose
        if purpose == "contact_discovery":
            url_filter = CommonFilters.contact_discovery()
        elif purpose == "product_discovery":
            url_filter = CommonFilters.product_discovery()
        elif purpose == "news_content":
            url_filter = CommonFilters.news_content()
        else:
            url_filter = CommonFilters.comprehensive_discovery()
        
        # Add custom patterns if provided
        if include_patterns or exclude_patterns or allowed_domains:
            custom_filters = []
            if include_patterns or exclude_patterns:
                custom_filters.append(URLPatternFilter(
                    include=include_patterns,
                    exclude=exclude_patterns
                ))
            if allowed_domains:
                custom_filters.append(DomainFilter(allowed_domains=allowed_domains))
            
            # Combine with purpose-based filter
            if custom_filters:
                all_filters = [url_filter] + custom_filters
                url_filter = FilterChain(all_filters, logic="AND")
        
        # Initialize BFS crawler
        crawler = BFSDeepCrawlStrategy(config)
        
        # Override URL filtering in crawler
        original_should_crawl = crawler._should_crawl_url
        def enhanced_should_crawl(url: str, depth: int) -> bool:
            # First check base criteria
            if not original_should_crawl(url, depth):
                return False
            # Then apply purpose-based filtering
            return url_filter.should_crawl(url, {"depth": depth})
        
        crawler._should_crawl_url = enhanced_should_crawl
        
        # Perform deep crawling
        crawl_results = await crawler.crawl(starting_url)
        
        # Generate comprehensive results
        site_map = crawler.get_site_map()
        crawl_summary = crawler.get_crawl_summary()
        statistics = crawler.get_crawl_statistics()
        
        # Organize results by success/failure
        successful_pages = [r for r in crawl_results if r.success]
        failed_pages = [r for r in crawl_results if not r.success]
        
        # Extract key insights
        discovered_urls = [r.url for r in successful_pages]
        total_links_found = sum(len(r.links) for r in successful_pages)
        
        return {
            "success": len(successful_pages) > 0,
            "starting_url": starting_url,
            "purpose": purpose,
            "discovered_pages": {
                "successful": [
                    {
                        "url": r.url,
                        "title": r.title,
                        "depth": r.depth,
                        "parent_url": r.parent_url,
                        "links_count": len(r.links),
                        "crawl_time": r.crawl_time,
                        "content_length": len(r.content)
                    }
                    for r in successful_pages
                ],
                "failed": [
                    {
                        "url": r.url,
                        "depth": r.depth,
                        "error": r.error
                    }
                    for r in failed_pages
                ]
            },
            "site_structure": site_map,
            "crawl_summary": crawl_summary,
            "statistics": statistics,
            "insights": {
                "total_pages_discovered": len(discovered_urls),
                "total_links_found": total_links_found,
                "average_links_per_page": total_links_found / len(successful_pages) if successful_pages else 0,
                "deepest_page_reached": max((r.depth for r in successful_pages), default=0),
                "most_productive_depth": crawl_summary.get("discovery_insights", {}).get("most_productive_depth", 0),
                "exploration_efficiency": statistics.get("success_rate", 0),
                "filter_configuration": url_filter.get_filter_info() if hasattr(url_filter, 'get_filter_info') else {"type": "simple"}
            },
            "discovered_urls": discovered_urls[:50],  # Return first 50 URLs for reference
            "metadata": {
                "config_used": {
                    "max_depth": max_depth,
                    "max_pages": max_pages,
                    "max_concurrent": max_concurrent,
                    "purpose": purpose
                },
                "execution_time": sum(r.crawl_time for r in crawl_results),
                "total_requests": len(crawl_results)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "starting_url": starting_url,
            "error": str(e),
            "purpose": purpose
        }


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
    name="crawl_multiple",
    description="Crawl multiple URLs in parallel for efficient bulk extraction",
    category="extraction",
    examples=[
        create_example(
            "Extract data from multiple product pages",
            urls=["https://example.com/product1", "https://example.com/product2"],
            strategy="css",
            css_selectors={"price": ".price", "title": ".title"}
        )
    ],
    capabilities=[
        "Parallel crawling of multiple URLs",
        "Batch processing for efficiency",
        "Consistent extraction across pages",
        "Progress tracking"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "medium"
    }
)
async def crawl_multiple(
    urls: List[str],
    strategy: str = "auto",
    css_selectors: Optional[Dict[str, str]] = None,
    extraction_prompt: Optional[str] = None,
    max_concurrent: int = 5
) -> Dict[str, Any]:
    """
    Crawl multiple URLs in parallel
    
    Args:
        urls: List of URLs to crawl
        strategy: Extraction strategy to use
        css_selectors: CSS selectors for extraction
        extraction_prompt: Prompt for LLM extraction
        max_concurrent: Maximum concurrent crawls
        
    Returns:
        Dictionary with results for each URL
    """
    results = {}
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def crawl_with_semaphore(url: str):
        async with semaphore:
            return await crawl_web(
                url=url,
                strategy=strategy,
                css_selectors=css_selectors,
                extraction_prompt=extraction_prompt
            )
    
    # Create tasks for all URLs
    tasks = [crawl_with_semaphore(url) for url in urls]
    
    # Execute in parallel
    crawl_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Organize results
    for url, result in zip(urls, crawl_results):
        if isinstance(result, Exception):
            results[url] = {
                "success": False,
                "error": str(result)
            }
        else:
            results[url] = result
    
    # Summary statistics
    successful = sum(1 for r in results.values() if r.get("success", False))
    
    return {
        "total_urls": len(urls),
        "successful": successful,
        "failed": len(urls) - successful,
        "results": results
    }


@ai_tool(
    name="crawl_paginated",
    description="Crawl paginated content by following next page links",
    category="extraction",
    examples=[
        create_example(
            "Extract all products from paginated listing",
            url="https://example.com/products?page=1",
            next_page_selector="a.next-page",
            data_selectors={"products": ".product-item"},
            max_pages=10
        )
    ],
    capabilities=[
        "Follow pagination links automatically",
        "Extract data from multiple pages",
        "Stop at maximum page limit",
        "Detect end of pagination"
    ],
    performance={
        "speed": "medium",
        "reliability": "high",
        "cost": "medium"
    }
)
async def crawl_paginated(
    url: str,
    next_page_selector: str,
    data_selectors: Dict[str, str],
    max_pages: int = 10,
    delay_between_pages: float = 1.0
) -> Dict[str, Any]:
    """
    Crawl paginated content
    
    Args:
        url: Starting URL
        next_page_selector: CSS selector for next page link
        data_selectors: CSS selectors for data extraction
        max_pages: Maximum number of pages to crawl
        delay_between_pages: Delay between page requests (seconds)
        
    Returns:
        Dictionary with aggregated data from all pages
    """
    all_data = []
    current_url = url
    pages_crawled = 0
    
    browser_config = BrowserConfig(headless=True)
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        while current_url and pages_crawled < max_pages:
            # Crawl current page
            result = await crawler.arun(url=current_url)
            
            if not result.success:
                break
            
            # Extract data using CSS selectors
            page_data = {}
            for key, selector in data_selectors.items():
                elements = result.select(selector)
                page_data[key] = [elem.text for elem in elements]
            
            all_data.append({
                "page": pages_crawled + 1,
                "url": current_url,
                "data": page_data
            })
            
            # Find next page link
            next_links = result.select(next_page_selector)
            if next_links and next_links[0].get("href"):
                next_url = next_links[0]["href"]
                # Handle relative URLs
                if not next_url.startswith("http"):
                    from urllib.parse import urljoin
                    next_url = urljoin(current_url, next_url)
                current_url = next_url
            else:
                break
            
            pages_crawled += 1
            
            # Delay between pages
            if pages_crawled < max_pages:
                await asyncio.sleep(delay_between_pages)
    
    return {
        "pages_crawled": pages_crawled,
        "data": all_data,
        "success": pages_crawled > 0
    }


# NEW: Deep Crawling Capabilities

@ai_tool(
    name="deep_crawl_bfs",
    description="Discover and crawl entire websites using intelligent site exploration",
    category="discovery",
    examples=[
        create_example(
            "Discover all contact pages from company website",
            starting_url="https://company.com",
            purpose="contact_discovery",
            max_depth=3,
            max_pages=50
        ),
        create_example(
            "Find all product pages from e-commerce site",
            starting_url="https://shop.com",
            purpose="product_discovery",
            include_patterns=["*/product*", "*/shop*"],
            max_depth=4
        )
    ],
    capabilities=[
        "Automatically discover site structure",
        "Intelligent URL filtering and prioritization",
        "Breadth-first systematic exploration",
        "Configurable depth and page limits",
        "Pattern-based URL filtering",
        "Domain restriction support",
        "Performance monitoring and statistics"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "medium"
    }
)
async def deep_crawl_bfs(
    starting_url: str,
    purpose: str = "comprehensive_discovery",
    max_depth: int = 3,
    max_pages: int = 100,
    max_concurrent: int = 10,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    allowed_domains: Optional[List[str]] = None,
    delay_between_requests: float = 1.0
) -> Dict[str, Any]:
    """
    Perform deep crawling using BFS strategy to discover and explore websites
    
    Args:
        starting_url: URL to start crawling from
        purpose: Crawling purpose (contact_discovery, product_discovery, news_content, comprehensive_discovery)
        max_depth: Maximum depth to crawl (0 = starting page only)
        max_pages: Maximum total pages to crawl
        max_concurrent: Maximum concurrent requests
        include_patterns: URL patterns to include (e.g., ["*/contact*", "*/about*"])
        exclude_patterns: URL patterns to exclude (e.g., ["*/admin*", "*/api/*"])
        allowed_domains: Restrict crawling to specific domains
        delay_between_requests: Delay between requests in seconds
        
    Returns:
        Dictionary with discovered pages, site map, and crawling statistics
    """
    try:
        # Configure deep crawling
        config = DeepCrawlConfig(
            max_depth=max_depth,
            max_pages=max_pages,
            max_concurrent=max_concurrent,
            delay_between_requests=delay_between_requests,
            include_patterns=include_patterns or [],
            exclude_patterns=exclude_patterns or [],
            allowed_domains=allowed_domains or []
        )
        
        # Set up URL filtering based on purpose
        if purpose == "contact_discovery":
            url_filter = CommonFilters.contact_discovery()
        elif purpose == "product_discovery":
            url_filter = CommonFilters.product_discovery()
        elif purpose == "news_content":
            url_filter = CommonFilters.news_content()
        else:
            url_filter = CommonFilters.comprehensive_discovery()
        
        # Add custom patterns if provided
        if include_patterns or exclude_patterns or allowed_domains:
            custom_filters = []
            if include_patterns or exclude_patterns:
                custom_filters.append(URLPatternFilter(
                    include=include_patterns,
                    exclude=exclude_patterns
                ))
            if allowed_domains:
                custom_filters.append(DomainFilter(allowed_domains=allowed_domains))
            
            # Combine with purpose-based filter
            if custom_filters:
                all_filters = [url_filter] + custom_filters
                url_filter = FilterChain(all_filters, logic="AND")
        
        # Initialize BFS crawler
        crawler = BFSDeepCrawlStrategy(config)
        
        # Override URL filtering in crawler
        original_should_crawl = crawler._should_crawl_url
        def enhanced_should_crawl(url: str, depth: int) -> bool:
            # First check base criteria
            if not original_should_crawl(url, depth):
                return False
            # Then apply purpose-based filtering
            return url_filter.should_crawl(url, {"depth": depth})
        
        crawler._should_crawl_url = enhanced_should_crawl
        
        # Perform deep crawling
        crawl_results = await crawler.crawl(starting_url)
        
        # Generate comprehensive results
        site_map = crawler.get_site_map()
        crawl_summary = crawler.get_crawl_summary()
        statistics = crawler.get_crawl_statistics()
        
        # Organize results by success/failure
        successful_pages = [r for r in crawl_results if r.success]
        failed_pages = [r for r in crawl_results if not r.success]
        
        # Extract key insights
        discovered_urls = [r.url for r in successful_pages]
        total_links_found = sum(len(r.links) for r in successful_pages)
        
        return {
            "success": len(successful_pages) > 0,
            "starting_url": starting_url,
            "purpose": purpose,
            "discovered_pages": {
                "successful": [
                    {
                        "url": r.url,
                        "title": r.title,
                        "depth": r.depth,
                        "parent_url": r.parent_url,
                        "links_count": len(r.links),
                        "crawl_time": r.crawl_time,
                        "content_length": len(r.content)
                    }
                    for r in successful_pages
                ],
                "failed": [
                    {
                        "url": r.url,
                        "depth": r.depth,
                        "error": r.error
                    }
                    for r in failed_pages
                ]
            },
            "site_structure": site_map,
            "crawl_summary": crawl_summary,
            "statistics": statistics,
            "insights": {
                "total_pages_discovered": len(discovered_urls),
                "total_links_found": total_links_found,
                "average_links_per_page": total_links_found / len(successful_pages) if successful_pages else 0,
                "deepest_page_reached": max((r.depth for r in successful_pages), default=0),
                "most_productive_depth": crawl_summary.get("discovery_insights", {}).get("most_productive_depth", 0),
                "exploration_efficiency": statistics.get("success_rate", 0),
                "filter_configuration": url_filter.get_filter_info() if hasattr(url_filter, 'get_filter_info') else {"type": "simple"}
            },
            "discovered_urls": discovered_urls[:50],  # Return first 50 URLs for reference
            "metadata": {
                "config_used": {
                    "max_depth": max_depth,
                    "max_pages": max_pages,
                    "max_concurrent": max_concurrent,
                    "purpose": purpose
                },
                "execution_time": sum(r.crawl_time for r in crawl_results),
                "total_requests": len(crawl_results)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "starting_url": starting_url,
            "error": str(e),
            "purpose": purpose
        }


@ai_tool(
    name="intelligent_site_discovery",
    description="AI-powered site discovery that automatically finds relevant pages based on your goals",
    category="intelligence",
    examples=[
        create_example(
            "Find all ways to contact this company",
            company_url="https://company.com",
            discovery_goal="contact_information"
        ),
        create_example(
            "Discover all product offerings from this business",
            company_url="https://business.com",
            discovery_goal="product_catalog"
        )
    ],
    capabilities=[
        "AI-powered goal understanding",
        "Automatic strategy selection",
        "Intelligent URL prioritization",
        "Comprehensive site analysis",
        "Quality-focused discovery"
    ],
    performance={
        "speed": "medium",
        "reliability": "very_high",
        "cost": "medium"
    }
)
async def intelligent_site_discovery(
    company_url: str,
    discovery_goal: str = "comprehensive_analysis",
    quality_threshold: float = 0.7,
    max_pages: int = 50,
    focus_depth: int = 3
) -> Dict[str, Any]:
    """
    Intelligent site discovery with AI-powered goal understanding
    
    Args:
        company_url: Company website to explore
        discovery_goal: What you want to discover (contact_information, product_catalog, 
                       company_information, news_content, comprehensive_analysis)
        quality_threshold: Minimum quality score for pages (0.0-1.0)
        max_pages: Maximum pages to crawl
        focus_depth: How deep to explore for high-quality content
        
    Returns:
        Dictionary with intelligently discovered and prioritized content
    """
    try:
        # Map discovery goals to crawling strategies
        goal_mapping = {
            "contact_information": {
                "purpose": "contact_discovery",
                "scorer": CommonScorers.contact_discovery(),
                "include_patterns": ["*/contact*", "*/about*", "*/team*", "*/location*"],
                "keywords": ["contact", "phone", "email", "address", "office"]
            },
            "product_catalog": {
                "purpose": "product_discovery",
                "scorer": CommonScorers.product_discovery(),
                "include_patterns": ["*/product*", "*/service*", "*/solution*", "*/catalog*"],
                "keywords": ["product", "service", "solution", "offering", "feature"]
            },
            "company_information": {
                "purpose": "comprehensive_discovery",
                "scorer": CommonScorers.comprehensive_discovery(),
                "include_patterns": ["*/about*", "*/company*", "*/history*", "*/mission*"],
                "keywords": ["about", "company", "history", "mission", "vision", "values"]
            },
            "news_content": {
                "purpose": "news_content",
                "scorer": CommonScorers.news_content(),
                "include_patterns": ["*/news*", "*/blog*", "*/press*", "*/announcement*"],
                "keywords": ["news", "blog", "article", "press", "announcement"]
            },
            "comprehensive_analysis": {
                "purpose": "comprehensive_discovery",
                "scorer": CommonScorers.quality_focused(),
                "include_patterns": [],
                "keywords": ["about", "contact", "product", "service", "news"]
            }
        }
        
        strategy = goal_mapping.get(discovery_goal, goal_mapping["comprehensive_analysis"])
        
        # Perform initial discovery
        discovery_result = await deep_crawl_bfs(
            starting_url=company_url,
            purpose=strategy["purpose"],
            max_depth=focus_depth,
            max_pages=max_pages,
            include_patterns=strategy["include_patterns"] if strategy["include_patterns"] else None
        )
        
        if not discovery_result["success"]:
            return discovery_result
        
        # Score and prioritize discovered pages
        successful_pages = discovery_result["discovered_pages"]["successful"]
        urls = [page["url"] for page in successful_pages]
        
        scoring_engine = ScoringEngine(strategy["scorer"])
        prioritized_urls = scoring_engine.get_prioritized_urls(urls)
        
        # Filter by quality threshold
        high_quality_pages = [
            (url, score) for url, score in prioritized_urls 
            if score >= quality_threshold
        ]
        
        # Enhance results with scoring insights
        enhanced_pages = []
        for page in successful_pages:
            page_url = page["url"]
            score = next((score for url, score in prioritized_urls if url == page_url), 0.0)
            
            enhanced_page = page.copy()
            enhanced_page["quality_score"] = score
            enhanced_page["meets_quality_threshold"] = score >= quality_threshold
            enhanced_pages.append(enhanced_page)
        
        # Sort by quality score
        enhanced_pages.sort(key=lambda x: x["quality_score"], reverse=True)
        
        return {
            "success": True,
            "company_url": company_url,
            "discovery_goal": discovery_goal,
            "quality_threshold": quality_threshold,
            "discovered_pages": enhanced_pages,
            "high_quality_pages": [
                {
                    "url": url,
                    "quality_score": score,
                    "page_info": next((p for p in enhanced_pages if p["url"] == url), {})
                }
                for url, score in high_quality_pages[:20]  # Top 20 high-quality pages
            ],
            "discovery_insights": {
                "total_pages_found": len(successful_pages),
                "high_quality_pages_count": len(high_quality_pages),
                "quality_rate": len(high_quality_pages) / len(successful_pages) if successful_pages else 0,
                "average_quality_score": sum(p["quality_score"] for p in enhanced_pages) / len(enhanced_pages) if enhanced_pages else 0,
                "top_scoring_page": enhanced_pages[0] if enhanced_pages else None,
                "goal_strategy_used": strategy["purpose"],
                "keywords_targeted": strategy["keywords"]
            },
            "scoring_statistics": scoring_engine.get_scoring_statistics(),
            "original_discovery": discovery_result["statistics"],
            "recommendations": {
                "best_pages_for_goal": [page["url"] for page in enhanced_pages[:5]],
                "quality_distribution": {
                    "excellent (0.9+)": len([p for p in enhanced_pages if p["quality_score"] >= 0.9]),
                    "good (0.7-0.9)": len([p for p in enhanced_pages if 0.7 <= p["quality_score"] < 0.9]),
                    "fair (0.5-0.7)": len([p for p in enhanced_pages if 0.5 <= p["quality_score"] < 0.7]),
                    "poor (0.0-0.5)": len([p for p in enhanced_pages if p["quality_score"] < 0.5])
                },
                "suggested_next_actions": [
                    f"Extract detailed information from top {min(5, len(high_quality_pages))} pages",
                    f"Focus on pages with scores above {quality_threshold:.1f}",
                    f"Consider exploring {strategy['purpose']} patterns further"
                ]
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "company_url": company_url,
            "discovery_goal": discovery_goal,
            "error": str(e)
        }
