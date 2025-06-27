"""
Crawler Tool - AI-discoverable web crawling capabilities

This tool wraps Crawl4AI functionality and makes it available to the AI planner.
"""

import asyncio
from typing import Dict, Any, Optional, List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, CSSExtractionStrategy

from ..registry import ai_tool, create_example, ToolExample


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
