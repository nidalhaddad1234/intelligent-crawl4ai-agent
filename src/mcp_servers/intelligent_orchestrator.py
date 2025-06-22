#!/usr/bin/env python3
"""
Intelligent Crawl4AI Orchestrator - Main MCP Server
Combines Claude's strategic planning with local AI execution
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional
from mcp.server import Server
from mcp.types import CallToolResult, ListToolsResult, Tool, TextContent

from ..agents.intelligent_analyzer import IntelligentWebsiteAnalyzer
from ..agents.strategy_selector import StrategySelector
from ..agents.high_volume_executor import HighVolumeExecutor
from ..utils.chromadb_manager import ChromaDBManager
from ..utils.ollama_client import OllamaClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("intelligent_orchestrator")

class IntelligentOrchestrator:
    """Main orchestrator that coordinates all AI agents"""
    
    def __init__(self):
        self.ollama_client = OllamaClient(
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434")
        )
        self.chromadb_manager = ChromaDBManager(
            host=os.getenv("CHROMADB_HOST", "localhost"),
            port=int(os.getenv("CHROMADB_PORT", "8000"))
        )
        self.website_analyzer = IntelligentWebsiteAnalyzer(self.ollama_client)
        self.strategy_selector = StrategySelector(self.ollama_client, self.chromadb_manager)
        self.high_volume_executor = HighVolumeExecutor()
        
    async def initialize(self):
        """Initialize all components"""
        await self.ollama_client.initialize()
        await self.chromadb_manager.initialize()
        await self.high_volume_executor.initialize()
        logger.info("Intelligent Orchestrator initialized successfully")

# Initialize the orchestrator
orchestrator = IntelligentOrchestrator()

# Create MCP server
server = Server("intelligent_crawl4ai_orchestrator")

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List all available tools for Claude Desktop"""
    return ListToolsResult(
        tools=[
            Tool(
                name="analyze_and_scrape",
                description="Analyze websites and execute intelligent scraping with optimal strategy selection",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of URLs to scrape"
                        },
                        "purpose": {
                            "type": "string",
                            "enum": ["company_info", "contact_discovery", "product_data", "profile_info", "news_content", "general_data"],
                            "description": "Type of data to extract"
                        },
                        "execution_mode": {
                            "type": "string",
                            "enum": ["intelligent_single", "high_volume", "authenticated"],
                            "default": "intelligent_single",
                            "description": "Processing mode"
                        },
                        "credentials": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "password": {"type": "string"},
                                "two_factor_code": {"type": "string"}
                            },
                            "description": "Optional credentials for authenticated sites"
                        },
                        "additional_context": {
                            "type": "string",
                            "description": "Additional context about what to extract"
                        }
                    },
                    "required": ["urls", "purpose"]
                }
            ),
            Tool(
                name="analyze_website_structure",
                description="Analyze website structure and recommend optimal extraction strategy",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "purpose": {"type": "string"}
                    },
                    "required": ["url", "purpose"]
                }
            ),
            Tool(
                name="submit_high_volume_job",
                description="Submit high-volume scraping job for massive URL processing",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {"type": "array", "items": {"type": "string"}},
                        "purpose": {"type": "string"},
                        "priority": {"type": "number", "default": 1},
                        "batch_size": {"type": "number", "default": 100},
                        "max_workers": {"type": "number", "default": 50}
                    },
                    "required": ["urls", "purpose"]
                }
            ),
            Tool(
                name="get_job_status",
                description="Get status and progress of high-volume scraping jobs",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string"}
                    },
                    "required": ["job_id"]
                }
            ),
            Tool(
                name="query_extracted_data",
                description="Query previously extracted data using semantic search",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "data_type": {"type": "string"},
                        "limit": {"type": "number", "default": 10}
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_system_stats",
                description="Get real-time system performance and worker statistics",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
        ]
    )

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls from Claude Desktop"""
    try:
        # Initialize orchestrator if not already done
        if not hasattr(orchestrator, '_initialized'):
            await orchestrator.initialize()
            orchestrator._initialized = True
        
        if name == "analyze_and_scrape":
            result = await analyze_and_scrape(arguments)
        elif name == "analyze_website_structure":
            result = await analyze_website_structure(arguments)
        elif name == "submit_high_volume_job":
            result = await submit_high_volume_job(arguments)
        elif name == "get_job_status":
            result = await get_job_status(arguments)
        elif name == "query_extracted_data":
            result = await query_extracted_data(arguments)
        elif name == "get_system_stats":
            result = await get_system_stats(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        return CallToolResult(content=[TextContent(type="text", text=json.dumps(result, indent=2))])
    
    except Exception as e:
        logger.error(f"Tool execution failed: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")],
            isError=True
        )

async def analyze_and_scrape(args: Dict[str, Any]) -> Dict[str, Any]:
    """Main intelligent scraping function"""
    urls = args["urls"]
    purpose = args["purpose"]
    execution_mode = args.get("execution_mode", "intelligent_single")
    credentials = args.get("credentials")
    additional_context = args.get("additional_context", "")
    
    logger.info(f"Starting {execution_mode} scraping of {len(urls)} URLs for {purpose}")
    
    if execution_mode == "high_volume":
        # Delegate to high-volume executor
        job_id = await orchestrator.high_volume_executor.submit_job(
            urls=urls,
            purpose=purpose,
            credentials=credentials
        )
        return {
            "execution_mode": "high_volume",
            "job_id": job_id,
            "status": "submitted",
            "urls_count": len(urls),
            "message": f"High-volume job submitted with ID: {job_id}"
        }
    
    else:
        # Intelligent single/batch processing
        results = []
        strategy_stats = {}
        
        for url in urls[:10]:  # Limit to first 10 for real-time processing
            try:
                # Step 1: Analyze website
                analysis = await orchestrator.website_analyzer.analyze_website(url)
                
                # Step 2: Select optimal strategy
                strategy = await orchestrator.strategy_selector.select_strategy(
                    analysis=analysis,
                    purpose=purpose,
                    additional_context=additional_context
                )
                
                # Step 3: Execute extraction
                if execution_mode == "authenticated" and credentials:
                    result = await orchestrator.website_analyzer.scrape_with_authentication(
                        url=url,
                        strategy=strategy,
                        credentials=credentials
                    )
                else:
                    result = await orchestrator.website_analyzer.execute_extraction(
                        url=url,
                        strategy=strategy
                    )
                
                # Step 4: Store in ChromaDB for learning
                await orchestrator.chromadb_manager.store_extraction_result(
                    url=url,
                    result=result,
                    strategy=strategy,
                    purpose=purpose
                )
                
                results.append(result)
                
                # Track strategy usage
                strategy_name = strategy.primary_strategy
                strategy_stats[strategy_name] = strategy_stats.get(strategy_name, 0) + 1
                
            except Exception as e:
                logger.error(f"Failed to process {url}: {e}")
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        # Summary statistics
        successful = sum(1 for r in results if r.get("success", False))
        
        return {
            "execution_mode": execution_mode,
            "total_urls": len(urls),
            "processed_urls": len(results),
            "successful_extractions": successful,
            "failed_extractions": len(results) - successful,
            "strategy_distribution": strategy_stats,
            "results": results,
            "purpose": purpose
        }

async def analyze_website_structure(args: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze website structure without extraction"""
    url = args["url"]
    purpose = args["purpose"]
    
    analysis = await orchestrator.website_analyzer.analyze_website(url)
    strategy = await orchestrator.strategy_selector.select_strategy(
        analysis=analysis,
        purpose=purpose
    )
    
    return {
        "url": url,
        "analysis": {
            "website_type": analysis.website_type.value,
            "complexity": analysis.estimated_complexity,
            "has_javascript": analysis.has_javascript,
            "has_forms": analysis.has_forms,
            "detected_frameworks": analysis.detected_frameworks,
            "anti_bot_measures": analysis.anti_bot_measures
        },
        "recommended_strategy": {
            "primary": strategy.primary_strategy,
            "fallbacks": strategy.fallback_strategies,
            "confidence": strategy.estimated_success_rate,
            "reasoning": strategy.reasoning
        },
        "extraction_plan": strategy.extraction_config
    }

async def submit_high_volume_job(args: Dict[str, Any]) -> Dict[str, Any]:
    """Submit high-volume job"""
    job_id = await orchestrator.high_volume_executor.submit_job(
        urls=args["urls"],
        purpose=args["purpose"],
        priority=args.get("priority", 1),
        batch_size=args.get("batch_size", 100),
        max_workers=args.get("max_workers", 50)
    )
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "urls_count": len(args["urls"]),
        "batch_size": args.get("batch_size", 100),
        "estimated_batches": len(args["urls"]) // args.get("batch_size", 100) + 1
    }

async def get_job_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get job status and progress"""
    return await orchestrator.high_volume_executor.get_job_status(args["job_id"])

async def query_extracted_data(args: Dict[str, Any]) -> Dict[str, Any]:
    """Query extracted data using semantic search"""
    return await orchestrator.chromadb_manager.semantic_search(
        query=args["query"],
        data_type=args.get("data_type"),
        limit=args.get("limit", 10)
    )

async def get_system_stats(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get system performance statistics"""
    return await orchestrator.high_volume_executor.get_system_stats()

async def main():
    """Main entry point for MCP server"""
    from mcp.server.stdio import stdio_server
    from mcp.server.models import InitializationOptions
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="intelligent_crawl4ai_orchestrator",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
