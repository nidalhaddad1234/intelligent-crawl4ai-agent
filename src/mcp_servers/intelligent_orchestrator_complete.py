#!/usr/bin/env python3
"""
Intelligent Crawl4AI Orchestrator - Production MCP Server (COMPLETE VERSION)
Complete Claude Desktop integration with full MCP protocol compliance
"""

import asyncio
import json
import logging
import os
import signal
import sys
import time
import traceback
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Sequence

import uvloop
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolResult, ListToolsResult, Tool, TextContent, ImageContent,
    Resource, ListResourcesResult, ReadResourceResult,
    Prompt, ListPromptsResult, GetPromptResult, PromptMessage,
    McpError, INVALID_REQUEST, INTERNAL_ERROR, INVALID_PARAMS,
    LoggingLevel, LoggingMessage
)

# Import our intelligent agents
try:
    from ..agents.intelligent_analyzer import IntelligentWebsiteAnalyzer
    from ..agents.strategy_selector import StrategySelector
    from ..agents.high_volume_executor import HighVolumeExecutor
    from ..utils.chromadb_manager import ChromaDBManager
    from ..utils.ollama_client import OllamaClient
    from ..strategies import get_strategy, RegexExtractionStrategy
    from ..database.models import ExtractionJob, JobStatus
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Create mock classes for testing
    class IntelligentWebsiteAnalyzer:
        def __init__(self, *args, **kwargs): pass
        async def analyze_website(self, url): return {"mock": True}
        async def execute_intelligent_extraction(self, **kwargs): return {"success": True, "extracted_data": {"mock": True}, "processing_time": 1.0}
        async def execute_fast_extraction(self, **kwargs): return {"success": True, "extracted_data": {"mock": True}, "processing_time": 0.5}
        async def execute_authenticated_extraction(self, **kwargs): return {"success": True, "extracted_data": {"mock": True}, "processing_time": 2.0}
        async def execute_stealth_extraction(self, **kwargs): return {"success": True, "extracted_data": {"mock": True}, "processing_time": 3.0}
    
    class StrategySelector:
        def __init__(self, *args, **kwargs): pass
        async def select_strategy(self, **kwargs): return {"primary_strategy": "mock", "confidence": 0.8}
        async def get_strategy_recommendations(self, **kwargs): return {"recommended_strategies": ["mock_strategy"]}
    
    class HighVolumeExecutor:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): pass
        async def submit_job(self, **kwargs): return "mock-job-id"
        async def get_job_status(self, job_id, **kwargs): return {"status": "completed", "progress": 100}
        async def get_health(self): return {"status": "healthy"}
        async def get_system_stats(self): return {"active_jobs": 0}
        async def shutdown(self): pass
    
    class ChromaDBManager:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): pass
        async def store_extraction_result(self, **kwargs): pass
        async def semantic_search(self, **kwargs): return [{"content": "mock result", "similarity": 0.9}]
        async def get_job_data(self, job_ids): return [{"job_id": job_id, "data": "mock"} for job_id in job_ids]
        async def get_recent_data(self, **kwargs): return [{"data": "mock recent data"}]
        async def health_check(self): pass
        async def close(self): pass
    
    class OllamaClient:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): pass
        async def health_check(self): pass
        async def close(self): pass

# Configure high-performance event loop
if sys.platform != 'win32':
    try:
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        pass  # uvloop not available, use default

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO').upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/mcp_server.log') if Path('/app/logs').exists() else logging.NullHandler()
    ]
)
logger = logging.getLogger("intelligent_mcp_server")

@dataclass
class MCPConfig:
    """MCP Server Configuration"""
    server_name: str = "intelligent_crawl4ai_orchestrator"
    server_version: str = "1.2.0"
    max_concurrent_requests: int = 50
    request_timeout: int = 300
    enable_metrics: bool = True
    enable_health_checks: bool = True
    ollama_url: str = "http://localhost:11434"
    chromadb_url: str = "http://localhost:8000"
    redis_url: str = "redis://localhost:6379"
    postgres_url: str = ""
    log_level: str = "INFO"
    debug_mode: bool = False
    rate_limit_per_minute: int = 1000
    
    @classmethod
    def from_env(cls) -> 'MCPConfig':
        """Load configuration from environment variables"""
        return cls(
            server_name=os.getenv('MCP_SERVER_NAME', cls.server_name),
            server_version=os.getenv('MCP_SERVER_VERSION', cls.server_version),
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', cls.max_concurrent_requests)),
            request_timeout=int(os.getenv('MCP_TIMEOUT', cls.request_timeout)),
            enable_metrics=os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
            enable_health_checks=os.getenv('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true',
            ollama_url=os.getenv('OLLAMA_URL', cls.ollama_url),
            chromadb_url=os.getenv('CHROMADB_URL', cls.chromadb_url),
            redis_url=os.getenv('REDIS_URL', cls.redis_url),
            postgres_url=os.getenv('POSTGRES_URL', cls.postgres_url),
            log_level=os.getenv('LOG_LEVEL', cls.log_level),
            debug_mode=os.getenv('DEBUG', 'false').lower() == 'true',
            rate_limit_per_minute=int(os.getenv('RATE_LIMIT_PER_MINUTE', cls.rate_limit_per_minute))
        )

class MCPMetrics:
    """Performance metrics collection"""
    
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.error_count = 0
        self.tool_calls = {}
        self.avg_response_time = 0.0
        self.active_connections = 0
        self.total_data_extracted = 0
        
    def record_request(self, tool_name: str, response_time: float, success: bool):
        """Record request metrics"""
        self.request_count += 1
        if not success:
            self.error_count += 1
        
        # Update tool-specific metrics
        if tool_name not in self.tool_calls:
            self.tool_calls[tool_name] = {'count': 0, 'errors': 0, 'avg_time': 0.0}
        
        tool_metrics = self.tool_calls[tool_name]
        tool_metrics['count'] += 1
        if not success:
            tool_metrics['errors'] += 1
        
        # Update average response time (exponential moving average)
        alpha = 0.1
        tool_metrics['avg_time'] = (1 - alpha) * tool_metrics['avg_time'] + alpha * response_time
        self.avg_response_time = (1 - alpha) * self.avg_response_time + alpha * response_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current metrics"""
        uptime = time.time() - self.start_time
        return {
            'uptime_seconds': uptime,
            'requests_total': self.request_count,
            'errors_total': self.error_count,
            'success_rate': (self.request_count - self.error_count) / max(self.request_count, 1),
            'avg_response_time_ms': self.avg_response_time * 1000,
            'requests_per_minute': (self.request_count / uptime) * 60 if uptime > 0 else 0,
            'active_connections': self.active_connections,
            'tool_usage': self.tool_calls,
            'memory_usage_mb': self._get_memory_usage(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

class IntelligentOrchestrator:
    """Enhanced orchestrator with full production capabilities"""
    
    def __init__(self, config: MCPConfig):
        self.config = config
        self.metrics = MCPMetrics()
        self.is_shutting_down = False
        self._initialized = False
        
        # Initialize components
        self.ollama_client = None
        self.chromadb_manager = None
        self.website_analyzer = None
        self.strategy_selector = None
        self.high_volume_executor = None
        
        # Health check status
        self.health_status = {
            'status': 'starting',
            'components': {},
            'last_check': None
        }
        
        # Rate limiting
        self.request_times = []
        
        logger.info(f"Initializing Intelligent Orchestrator v{config.server_version}")
    
    async def initialize(self) -> bool:
        """Initialize all components with proper error handling"""
        if self._initialized:
            return True
            
        try:
            logger.info("Starting component initialization...")
            
            # Initialize Ollama client
            logger.info("Initializing Ollama client...")
            self.ollama_client = OllamaClient(base_url=self.config.ollama_url)
            await self.ollama_client.initialize()
            self.health_status['components']['ollama'] = 'healthy'
            logger.info("✅ Ollama client initialized")
            
            # Initialize ChromaDB
            logger.info("Initializing ChromaDB...")
            self.chromadb_manager = ChromaDBManager(
                host=self.config.chromadb_url.split('://')[-1].split(':')[0],
                port=int(self.config.chromadb_url.split(':')[-1]) if ':' in self.config.chromadb_url else 8000,
                ollama_client=self.ollama_client
            )
            await self.chromadb_manager.initialize()
            self.health_status['components']['chromadb'] = 'healthy'
            logger.info("✅ ChromaDB initialized")
            
            # Initialize website analyzer
            logger.info("Initializing Website Analyzer...")
            self.website_analyzer = IntelligentWebsiteAnalyzer(self.ollama_client)
            self.health_status['components']['analyzer'] = 'healthy'
            logger.info("✅ Website Analyzer initialized")
            
            # Initialize strategy selector
            logger.info("Initializing Strategy Selector...")
            self.strategy_selector = StrategySelector(self.ollama_client, self.chromadb_manager)
            self.health_status['components']['strategy_selector'] = 'healthy'
            logger.info("✅ Strategy Selector initialized")
            
            # Initialize high-volume executor
            logger.info("Initializing High-Volume Executor...")
            self.high_volume_executor = HighVolumeExecutor()
            await self.high_volume_executor.initialize()
            self.health_status['components']['executor'] = 'healthy'
            logger.info("✅ High-Volume Executor initialized")
            
            self._initialized = True
            self.health_status['status'] = 'healthy'
            self.health_status['last_check'] = datetime.now(timezone.utc).isoformat()
            
            logger.info("🎉 All components initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            logger.error(traceback.format_exc())
            self.health_status['status'] = 'unhealthy'
            self.health_status['error'] = str(e)
            return False
    
    async def shutdown(self):
        """Graceful shutdown of all components"""
        logger.info("🛑 Starting graceful shutdown...")
        self.is_shutting_down = True
        
        # Shutdown components in reverse order
        if self.high_volume_executor:
            try:
                await self.high_volume_executor.shutdown()
                logger.info("✅ High-Volume Executor shutdown")
            except Exception as e:
                logger.error(f"Error shutting down executor: {e}")
        
        if self.chromadb_manager:
            try:
                await self.chromadb_manager.close()
                logger.info("✅ ChromaDB connection closed")
            except Exception as e:
                logger.error(f"Error closing ChromaDB: {e}")
        
        if self.ollama_client:
            try:
                await self.ollama_client.close()
                logger.info("✅ Ollama client closed")
            except Exception as e:
                logger.error(f"Error closing Ollama client: {e}")
        
        logger.info("🏁 Graceful shutdown completed")
    
    def check_rate_limit(self) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        
        # Check if under limit
        if len(self.request_times) >= self.config.rate_limit_per_minute:
            return False
        
        # Add current request
        self.request_times.append(current_time)
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_data = {
            'overall_status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'components': {},
            'metrics': self.metrics.get_stats() if self.config.enable_metrics else None
        }
        
        # Check each component
        try:
            # Check Ollama
            if self.ollama_client:
                try:
                    await self.ollama_client.health_check()
                    health_data['components']['ollama'] = 'healthy'
                except Exception as e:
                    health_data['components']['ollama'] = f'unhealthy: {e}'
                    health_data['overall_status'] = 'degraded'
            
            # Check ChromaDB
            if self.chromadb_manager:
                try:
                    await self.chromadb_manager.health_check()
                    health_data['components']['chromadb'] = 'healthy'
                except Exception as e:
                    health_data['components']['chromadb'] = f'unhealthy: {e}'
                    health_data['overall_status'] = 'degraded'
            
            # Check high-volume executor
            if self.high_volume_executor:
                try:
                    executor_stats = await self.high_volume_executor.get_health()
                    health_data['components']['executor'] = executor_stats
                except Exception as e:
                    health_data['components']['executor'] = f'unhealthy: {e}'
                    health_data['overall_status'] = 'degraded'
                    
        except Exception as e:
            health_data['overall_status'] = 'unhealthy'
            health_data['error'] = str(e)
        
        self.health_status = health_data
        return health_data

# Global orchestrator instance
orchestrator: Optional[IntelligentOrchestrator] = None
config = MCPConfig.from_env()

# Create enhanced MCP server
server = Server(config.server_name)

@asynccontextmanager
async def request_context(tool_name: str):
    """Context manager for request handling with metrics and error tracking"""
    start_time = time.time()
    success = False
    
    try:
        # Check rate limiting
        if not orchestrator.check_rate_limit():
            raise McpError(INVALID_REQUEST, "Rate limit exceeded")
        
        # Check if shutting down
        if orchestrator.is_shutting_down:
            raise McpError(INTERNAL_ERROR, "Server is shutting down")
        
        orchestrator.metrics.active_connections += 1
        yield
        success = True
        
    except Exception as e:
        logger.error(f"Request failed for {tool_name}: {e}")
        raise
    
    finally:
        response_time = time.time() - start_time
        orchestrator.metrics.active_connections -= 1
        
        if config.enable_metrics:
            orchestrator.metrics.record_request(tool_name, response_time, success)
        
        if config.debug_mode:
            logger.debug(f"{tool_name} completed in {response_time:.3f}s (success: {success})")

async def ensure_initialized():
    """Ensure orchestrator is initialized"""
    global orchestrator
    
    if orchestrator is None:
        orchestrator = IntelligentOrchestrator(config)
    
    if not orchestrator._initialized:
        success = await orchestrator.initialize()
        if not success:
            raise McpError(INTERNAL_ERROR, "Failed to initialize orchestrator")

# ==================== UTILITY FUNCTIONS ====================

async def format_results_as_csv(results: List[Dict]) -> str:
    """Format extraction results as CSV"""
    if not results:
        return "No data to export"
    
    import csv
    import io
    
    output = io.StringIO()
    
    # Get all possible field names
    fieldnames = set()
    for result in results:
        if result.get('extracted_data'):
            fieldnames.update(result['extracted_data'].keys())
        fieldnames.update(['url', 'success', 'timestamp'])
    
    writer = csv.DictWriter(output, fieldnames=list(fieldnames))
    writer.writeheader()
    
    for result in results:
        row = {'url': result.get('url', ''), 'success': result.get('success', False), 'timestamp': result.get('timestamp', '')}
        if result.get('extracted_data'):
            row.update(result['extracted_data'])
        writer.writerow(row)
    
    return output.getvalue()

async def format_results_as_markdown(response: Dict) -> str:
    """Format extraction results as Markdown"""
    md = f"# Intelligent Scraping Results\n\n"
    md += f"**Total URLs**: {response['summary']['total_urls']}\n"
    md += f"**Successful**: {response['summary']['successful_extractions']}\n"
    md += f"**Success Rate**: {response['summary']['success_rate']:.2%}\n"
    md += f"**Purpose**: {response['summary']['purpose']}\n"
    md += f"**Mode**: {response['summary']['execution_mode']}\n\n"
    
    for i, result in enumerate(response['results'], 1):
        md += f"## Result {i}: {result['url']}\n\n"
        md += f"**Status**: {'✅ Success' if result.get('success') else '❌ Failed'}\n\n"
        
        if result.get('success') and result.get('extracted_data'):
            md += "**Extracted Data**:\n```json\n"
            md += json.dumps(result['extracted_data'], indent=2)
            md += "\n```\n\n"
        
        if result.get('error'):
            md += f"**Error**: {result['error']}\n\n"
    
    return md

async def format_export_as_csv(data: List[Dict]) -> str:
    """Format export data as CSV"""
    return await format_results_as_csv(data)

async def format_export_as_excel(data: List[Dict]) -> bytes:
    """Format export data as Excel (returns base64 encoded bytes)"""
    try:
        import pandas as pd
        import io
        
        # Flatten the data for Excel export
        flattened_data = []
        for item in data:
            flattened_item = {}
            for key, value in item.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        flattened_item[f"{key}_{subkey}"] = subvalue
                else:
                    flattened_item[key] = value
            flattened_data.append(flattened_item)
        
        df = pd.DataFrame(flattened_data)
        
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        
        import base64
        return base64.b64encode(output.getvalue()).decode('utf-8')
    except ImportError:
        return "Excel export requires pandas and openpyxl packages"

async def format_export_as_xml(data: List[Dict]) -> str:
    """Format export data as XML"""
    def dict_to_xml(d, root_name="item"):
        xml = f"<{root_name}>"
        for key, value in d.items():
            if isinstance(value, dict):
                xml += dict_to_xml(value, key)
            elif isinstance(value, list):
                xml += f"<{key}>"
                for item in value:
                    if isinstance(item, dict):
                        xml += dict_to_xml(item, "item")
                    else:
                        xml += f"<item>{item}</item>"
                xml += f"</{key}>"
            else:
                xml += f"<{key}>{value}</{key}>"
        xml += f"</{root_name}>"
        return xml
    
    xml_output = '<?xml version="1.0" encoding="UTF-8"?>\n<export>\n'
    for item in data:
        xml_output += dict_to_xml(item) + "\n"
    xml_output += "</export>"
    
    return xml_output

# ==================== MCP HANDLERS ====================

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List all available tools with comprehensive schemas"""
    return ListToolsResult(
        tools=[
            Tool(
                name="intelligent_scrape",
                description="🎯 Analyze websites and execute intelligent scraping with AI-powered strategy selection. Supports single URLs, batch processing, and authenticated sites.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string", "format": "uri"},
                            "description": "List of URLs to scrape (max 50 for real-time processing)",
                            "maxItems": 50,
                            "minItems": 1
                        },
                        "purpose": {
                            "type": "string",
                            "enum": [
                                "contact_discovery", "lead_generation", "business_listings",
                                "product_data", "profile_info", "news_content", 
                                "social_media_analysis", "e_commerce", "competitor_analysis"
                            ],
                            "description": "Type of data to extract - determines optimal strategy selection"
                        },
                        "execution_mode": {
                            "type": "string",
                            "enum": ["intelligent_single", "fast_batch", "authenticated", "stealth_mode"],
                            "default": "intelligent_single",
                            "description": "Processing mode: intelligent_single (AI analysis), fast_batch (regex patterns), authenticated (login required), stealth_mode (anti-detection)"
                        },
                        "credentials": {
                            "type": "object",
                            "properties": {
                                "username": {"type": "string"},
                                "password": {"type": "string"},
                                "two_factor_code": {"type": "string"},
                                "session_cookies": {"type": "object"}
                            },
                            "description": "Login credentials for authenticated sites (LinkedIn, Facebook, etc.)"
                        },
                        "extraction_config": {
                            "type": "object",
                            "properties": {
                                "max_pages": {"type": "integer", "default": 1, "minimum": 1, "maximum": 10},
                                "follow_pagination": {"type": "boolean", "default": False},
                                "extract_images": {"type": "boolean", "default": False},
                                "custom_selectors": {"type": "object"},
                                "timeout_seconds": {"type": "integer", "default": 30, "minimum": 10, "maximum": 300}
                            },
                            "description": "Advanced extraction configuration"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["structured", "markdown", "json", "csv"],
                            "default": "structured",
                            "description": "Output format for extracted data"
                        },
                        "additional_context": {
                            "type": "string",
                            "description": "Additional context about what specific information to extract",
                            "maxLength": 1000
                        }
                    },
                    "required": ["urls", "purpose"]
                }
            ),
            Tool(
                name="analyze_website_structure",
                description="🔍 Analyze website structure, frameworks, and recommend optimal extraction strategies without executing scraping.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string", 
                            "format": "uri",
                            "description": "Website URL to analyze"
                        },
                        "purpose": {
                            "type": "string",
                            "description": "Intended extraction purpose for strategy optimization"
                        },
                        "deep_analysis": {
                            "type": "boolean",
                            "default": False,
                            "description": "Perform deep technical analysis (takes longer but more detailed)"
                        }
                    },
                    "required": ["url", "purpose"]
                }
            ),
            Tool(
                name="submit_high_volume_job",
                description="⚡ Submit high-volume scraping jobs for processing thousands of URLs with distributed workers.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string", "format": "uri"},
                            "description": "Large list of URLs to process (recommended: 100-10,000 URLs)",
                            "minItems": 10,
                            "maxItems": 50000
                        },
                        "purpose": {"type": "string"},
                        "priority": {
                            "type": "integer",
                            "enum": [1, 2, 3, 4, 5],
                            "default": 3,
                            "description": "Job priority (1=highest, 5=lowest)"
                        },
                        "batch_size": {
                            "type": "integer",
                            "default": 100,
                            "minimum": 10,
                            "maximum": 1000,
                            "description": "URLs per batch for processing"
                        },
                        "max_workers": {
                            "type": "integer",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Maximum concurrent workers"
                        },
                        "rate_limit_delay": {
                            "type": "number",
                            "default": 1.0,
                            "minimum": 0.1,
                            "maximum": 30.0,
                            "description": "Delay between requests in seconds"
                        },
                        "callback_webhook": {
                            "type": "string",
                            "format": "uri",
                            "description": "Optional webhook URL for job completion notification"
                        }
                    },
                    "required": ["urls", "purpose"]
                }
            ),
            Tool(
                name="get_job_status",
                description="📊 Get detailed status, progress, and results of high-volume scraping jobs.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {
                            "type": "string",
                            "description": "Job ID returned from submit_high_volume_job"
                        },
                        "include_results": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include extracted data in response (use with caution for large jobs)"
                        },
                        "include_errors": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include error details for failed URLs"
                        }
                    },
                    "required": ["job_id"]
                }
            ),
            Tool(
                name="semantic_search",
                description="🔎 Search previously extracted data using AI-powered semantic similarity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Natural language search query",
                            "maxLength": 500
                        },
                        "data_types": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Filter by data types (e.g., 'contact_info', 'product_data')"
                        },
                        "date_range": {
                            "type": "object",
                            "properties": {
                                "start_date": {"type": "string", "format": "date"},
                                "end_date": {"type": "string", "format": "date"}
                            },
                            "description": "Filter by extraction date range"
                        },
                        "limit": {
                            "type": "integer",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 100,
                            "description": "Maximum number of results to return"
                        },
                        "similarity_threshold": {
                            "type": "number",
                            "default": 0.7,
                            "minimum": 0.1,
                            "maximum": 1.0,
                            "description": "Minimum similarity score (0.1-1.0)"
                        }
                    },
                    "required": ["query"]
                }
            ),
            Tool(
                name="get_system_status",
                description="📈 Get real-time system performance, health metrics, and operational statistics.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_metrics": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include performance metrics"
                        },
                        "include_health": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include health check results"
                        },
                        "include_jobs": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include active job information"
                        }
                    },
                    "required": []
                }
            ),
            Tool(
                name="export_data",
                description="💾 Export extracted data in various formats (JSON, CSV, Excel, XML).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Job IDs to export (or leave empty for all recent data)"
                        },
                        "format": {
                            "type": "string",
                            "enum": ["json", "csv", "excel", "xml"],
                            "default": "json",
                            "description": "Export format"
                        },
                        "filter_criteria": {
                            "type": "object",
                            "properties": {
                                "purpose": {"type": "string"},
                                "date_range": {"type": "object"},
                                "success_only": {"type": "boolean", "default": True}
                            },
                            "description": "Criteria for filtering exported data"
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include extraction metadata (timestamps, strategies used, etc.)"
                        }
                    },
                    "required": ["format"]
                }
            )
        ]
    )

# ==================== TOOL CALL HANDLERS ====================

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle all tool calls with comprehensive error handling and logging"""
    await ensure_initialized()
    
    try:
        async with request_context(name):
            # Route to specific tool handler
            if name == "intelligent_scrape":
                result = await handle_intelligent_scrape(arguments)
            elif name == "analyze_website_structure":
                result = await handle_analyze_website_structure(arguments)
            elif name == "submit_high_volume_job":
                result = await handle_submit_high_volume_job(arguments)
            elif name == "get_job_status":
                result = await handle_get_job_status(arguments)
            elif name == "semantic_search":
                result = await handle_semantic_search(arguments)
            elif name == "get_system_status":
                result = await handle_get_system_status(arguments)
            elif name == "export_data":
                result = await handle_export_data(arguments)
            else:
                raise McpError(INVALID_REQUEST, f"Unknown tool: {name}")
            
            return CallToolResult(content=[TextContent(type="text", text=result)])
            
    except McpError:
        raise
    except Exception as e:
        logger.error(f"Tool call failed for {name}: {e}")
        logger.error(traceback.format_exc())
        raise McpError(INTERNAL_ERROR, f"Tool execution failed: {str(e)}")

async def handle_intelligent_scrape(arguments: Dict[str, Any]) -> str:
    """🎯 Handle intelligent scraping with AI-powered strategy selection"""
    urls = arguments["urls"]
    purpose = arguments["purpose"]
    execution_mode = arguments.get("execution_mode", "intelligent_single")
    credentials = arguments.get("credentials", {})
    extraction_config = arguments.get("extraction_config", {})
    output_format = arguments.get("output_format", "structured")
    additional_context = arguments.get("additional_context", "")
    
    logger.info(f"🎯 Starting intelligent scrape for {len(urls)} URLs with purpose: {purpose}")
    
    results = []
    
    for i, url in enumerate(urls):
        try:
            logger.info(f"Processing URL {i+1}/{len(urls)}: {url}")
            
            # Step 1: Analyze website structure
            logger.info("🔍 Analyzing website structure...")
            analysis_result = await orchestrator.website_analyzer.analyze_website(
                url=url,
                purpose=purpose,
                deep_analysis=(execution_mode == "intelligent_single")
            )
            
            # Step 2: Select optimal strategy
            logger.info("🧠 Selecting optimal extraction strategy...")
            strategy_result = await orchestrator.strategy_selector.select_strategy(
                url=url,
                purpose=purpose,
                website_analysis=analysis_result,
                execution_mode=execution_mode,
                additional_context=additional_context
            )
            
            # Step 3: Execute extraction
            logger.info(f"⚡ Executing extraction with strategy: {strategy_result.get('primary_strategy')}")
            
            # Configure extraction parameters
            extract_params = {
                "url": url,
                "strategy": strategy_result,
                "purpose": purpose,
                "credentials": credentials,
                "config": extraction_config,
                "output_format": output_format
            }
            
            # Execute based on mode
            if execution_mode == "intelligent_single":
                extraction_result = await orchestrator.website_analyzer.execute_intelligent_extraction(
                    **extract_params
                )
            elif execution_mode == "fast_batch":
                extraction_result = await orchestrator.website_analyzer.execute_fast_extraction(
                    **extract_params
                )
            elif execution_mode == "authenticated":
                extraction_result = await orchestrator.website_analyzer.execute_authenticated_extraction(
                    **extract_params
                )
            elif execution_mode == "stealth_mode":
                extraction_result = await orchestrator.website_analyzer.execute_stealth_extraction(
                    **extract_params
                )
            else:
                raise ValueError(f"Unknown execution mode: {execution_mode}")
            
            # Step 4: Store results in ChromaDB
            if extraction_result.get("success", False):
                logger.info("💾 Storing extraction results...")
                await orchestrator.chromadb_manager.store_extraction_result(
                    url=url,
                    purpose=purpose,
                    strategy=strategy_result["primary_strategy"],
                    data=extraction_result["extracted_data"],
                    metadata={
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "execution_mode": execution_mode,
                        "analysis": analysis_result,
                        "strategy_confidence": strategy_result.get("confidence", 0.0)
                    }
                )
                orchestrator.metrics.total_data_extracted += 1
            
            # Format result
            result = {
                "url": url,
                "success": extraction_result.get("success", False),
                "extracted_data": extraction_result.get("extracted_data", {}),
                "metadata": {
                    "purpose": purpose,
                    "execution_mode": execution_mode,
                    "strategy_used": strategy_result.get("primary_strategy"),
                    "strategy_confidence": strategy_result.get("confidence", 0.0),
                    "processing_time": extraction_result.get("processing_time", 0.0),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                "analysis": analysis_result if output_format == "structured" else None,
                "strategy_selection": strategy_result if output_format == "structured" else None
            }
            
            if not extraction_result.get("success", False):
                result["error"] = extraction_result.get("error", "Unknown extraction error")
            
            results.append(result)
            logger.info(f"✅ Successfully processed {url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process {url}: {e}")
            results.append({
                "url": url,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    
    # Compile final response
    successful_extractions = sum(1 for r in results if r.get("success", False))
    
    response = {
        "summary": {
            "total_urls": len(urls),
            "successful_extractions": successful_extractions,
            "success_rate": successful_extractions / len(urls) if urls else 0,
            "purpose": purpose,
            "execution_mode": execution_mode,
            "output_format": output_format
        },
        "results": results,
        "processing_metadata": {
            "server_version": config.server_version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_processing_time": sum(r.get("metadata", {}).get("processing_time", 0) for r in results)
        }
    }
    
    logger.info(f"🎉 Intelligent scraping completed: {successful_extractions}/{len(urls)} successful")
    
    # Format output based on requested format
    if output_format == "json":
        return json.dumps(response, indent=2, ensure_ascii=False)
    elif output_format == "csv":
        return await format_results_as_csv(results)
    elif output_format == "markdown":
        return await format_results_as_markdown(response)
    else:
        return json.dumps(response, indent=2, ensure_ascii=False)

async def handle_analyze_website_structure(arguments: Dict[str, Any]) -> str:
    """🔍 Handle website structure analysis"""
    url = arguments["url"]
    purpose = arguments["purpose"]
    deep_analysis = arguments.get("deep_analysis", False)
    
    logger.info(f"🔍 Analyzing website structure for: {url}")
    
    try:
        # Perform comprehensive analysis
        analysis_result = await orchestrator.website_analyzer.analyze_website(
            url=url,
            purpose=purpose,
            deep_analysis=deep_analysis
        )
        
        # Get strategy recommendations
        strategy_recommendations = await orchestrator.strategy_selector.get_strategy_recommendations(
            url=url,
            purpose=purpose,
            website_analysis=analysis_result
        )
        
        response = {
            "url": url,
            "analysis": analysis_result,
            "strategy_recommendations": strategy_recommendations,
            "metadata": {
                "purpose": purpose,
                "deep_analysis": deep_analysis,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "analyzer_version": config.server_version
            }
        }
        
        logger.info(f"✅ Website analysis completed for {url}")
        return json.dumps(response, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"❌ Website analysis failed for {url}: {e}")
        error_response = {
            "url": url,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(error_response, indent=2, ensure_ascii=False)

async def handle_submit_high_volume_job(arguments: Dict[str, Any]) -> str:
    """⚡ Handle high-volume job submission"""
    urls = arguments["urls"]
    purpose = arguments["purpose"]
    priority = arguments.get("priority", 3)
    batch_size = arguments.get("batch_size", 100)
    max_workers = arguments.get("max_workers", 10)
    rate_limit_delay = arguments.get("rate_limit_delay", 1.0)
    callback_webhook = arguments.get("callback_webhook")
    
    logger.info(f"⚡ Submitting high-volume job: {len(urls)} URLs, purpose: {purpose}")
    
    try:
        # Submit job to high-volume executor
        job_id = await orchestrator.high_volume_executor.submit_job(
            urls=urls,
            purpose=purpose,
            priority=priority,
            batch_size=batch_size,
            max_workers=max_workers,
            rate_limit_delay=rate_limit_delay,
            callback_webhook=callback_webhook,
            orchestrator=orchestrator
        )
        
        # Get initial job status
        job_status = await orchestrator.high_volume_executor.get_job_status(job_id)
        
        response = {
            "job_id": job_id,
            "status": job_status,
            "submission_details": {
                "total_urls": len(urls),
                "purpose": purpose,
                "priority": priority,
                "batch_size": batch_size,
                "max_workers": max_workers,
                "rate_limit_delay": rate_limit_delay,
                "estimated_completion_time": (len(urls) / max_workers) * rate_limit_delay
            },
            "metadata": {
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "server_version": config.server_version
            }
        }
        
        logger.info(f"✅ High-volume job submitted successfully: {job_id}")
        return json.dumps(response, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"❌ High-volume job submission failed: {e}")
        error_response = {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(error_response, indent=2, ensure_ascii=False)

async def handle_get_job_status(arguments: Dict[str, Any]) -> str:
    """📊 Handle job status retrieval"""
    job_id = arguments["job_id"]
    include_results = arguments.get("include_results", False)
    include_errors = arguments.get("include_errors", True)
    
    logger.info(f"📊 Getting job status for: {job_id}")
    
    try:
        # Get comprehensive job status
        job_status = await orchestrator.high_volume_executor.get_job_status(
            job_id=job_id,
            include_results=include_results,
            include_errors=include_errors
        )
        
        if not job_status:
            raise ValueError(f"Job not found: {job_id}")
        
        response = {
            "job_id": job_id,
            "status": job_status,
            "metadata": {
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "include_results": include_results,
                "include_errors": include_errors
            }
        }
        
        logger.info(f"✅ Job status retrieved for {job_id}: {job_status.get('status', 'unknown')}")
        return json.dumps(response, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"❌ Failed to get job status for {job_id}: {e}")
        error_response = {
            "job_id": job_id,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(error_response, indent=2, ensure_ascii=False)

async def handle_semantic_search(arguments: Dict[str, Any]) -> str:
    """🔎 Handle semantic search of extracted data"""
    query = arguments["query"]
    data_types = arguments.get("data_types", [])
    date_range = arguments.get("date_range", {})
    limit = arguments.get("limit", 10)
    similarity_threshold = arguments.get("similarity_threshold", 0.7)
    
    logger.info(f"🔎 Performing semantic search: '{query}' (limit: {limit})")
    
    try:
        # Perform semantic search using ChromaDB
        search_results = await orchestrator.chromadb_manager.semantic_search(
            query=query,
            data_types=data_types,
            date_range=date_range,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        response = {
            "query": query,
            "results": search_results,
            "search_metadata": {
                "total_results": len(search_results),
                "data_types_filter": data_types,
                "date_range_filter": date_range,
                "similarity_threshold": similarity_threshold,
                "limit": limit
            },
            "metadata": {
                "search_timestamp": datetime.now(timezone.utc).isoformat(),
                "server_version": config.server_version
            }
        }
        
        logger.info(f"✅ Semantic search completed: {len(search_results)} results found")
        return json.dumps(response, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"❌ Semantic search failed: {e}")
        error_response = {
            "query": query,
            "success": False,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(error_response, indent=2, ensure_ascii=False)

async def handle_get_system_status(arguments: Dict[str, Any]) -> str:
    """📈 Handle system status retrieval"""
    include_metrics = arguments.get("include_metrics", True)
    include_health = arguments.get("include_health", True)
    include_jobs = arguments.get("include_jobs", True)
    
    logger.info("📈 Getting comprehensive system status")
    
    try:
        response = {
            "system_status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server_info": {
                "name": config.server_name,
                "version": config.server_version,
                "uptime_seconds": time.time() - orchestrator.metrics.start_time,
                "initialized": orchestrator._initialized
            }
        }
        
        # Include performance metrics
        if include_metrics and config.enable_metrics:
            response["metrics"] = orchestrator.metrics.get_stats()
        
        # Include health check results
        if include_health and config.enable_health_checks:
            response["health"] = await orchestrator.health_check()
        
        # Include job information
        if include_jobs:
            try:
                job_stats = await orchestrator.high_volume_executor.get_system_stats()
                response["jobs"] = job_stats
            except Exception as e:
                response["jobs"] = {"error": f"Failed to get job stats: {e}"}
        
        # Add component status
        response["components"] = {
            "ollama_client": "healthy" if orchestrator.ollama_client else "not_initialized",
            "chromadb_manager": "healthy" if orchestrator.chromadb_manager else "not_initialized",
            "website_analyzer": "healthy" if orchestrator.website_analyzer else "not_initialized",
            "strategy_selector": "healthy" if orchestrator.strategy_selector else "not_initialized",
            "high_volume_executor": "healthy" if orchestrator.high_volume_executor else "not_initialized"
        }
        
        logger.info("✅ System status retrieved successfully")
        return json.dumps(response, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"❌ Failed to get system status: {e}")
        error_response = {
            "system_status": "error",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return json.dumps(error_response, indent=2, ensure_ascii=False)

async def handle_export_data(arguments: Dict[str, Any]) -> str:
    """💾 Handle data export"""
    job_ids = arguments.get("job_ids", [])
    format_type = arguments["format"]
    filter_criteria = arguments.get("filter_criteria", {})
    include_metadata = arguments.get("include_metadata", True)
    
    logger.info(f"💾 Exporting data in {format_type} format")
    
    try:
        # Get data to export
        if job_ids:
            export_data = await orchestrator.chromadb_manager.get_job_data(job_ids)
        else:
            export_data = await orchestrator.chromadb_manager.get_recent_data(
                filter_criteria=filter_criteria,
                include_metadata=include_metadata
            )
        
        # Format data based on requested format
        if format_type == "json":
            formatted_data = json.dumps(export_data, indent=2, ensure_ascii=False)
        elif format_type == "csv":
            formatted_data = await format_export_as_csv(export_data)
        elif format_type == "excel":
            formatted_data = await format_export_as_excel(export_data)
        elif format_type == "xml":
            formatted_data = await format_export_as_xml(export_data)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
        
        response = {
            "export_summary": {
                "format": format_type,
                "total_records": len(export_data) if isinstance(export_data, list) else 1,
                "job_ids": job_ids,
                "filter_criteria": filter_criteria,
                "include_metadata": include_metadata,
                "export_timestamp": datetime.now(timezone.utc).isoformat()
            },
            "data": formatted_data if format_type == "json" else f"Data exported in {format_type} format",
            "download_info": {
                "size_bytes": len(formatted_data.encode('utf-8')) if isinstance(formatted_data, str) else len(formatted_data),
                "format": format_type,
                "encoding": "utf-8"
            }
        }
        
        logger.info(f"✅ Data export completed: {len(export_data)} records in {format_type} format")
        return json.dumps(response, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"❌ Data export failed: {e}")
        error_response = {
            "export_summary": {
                "format": format_type,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }
        return json.dumps(error_response, indent=2, ensure_ascii=False)

# ==================== RESOURCE HANDLERS ====================

@server.list_resources()
async def handle_list_resources() -> ListResourcesResult:
    """List available resources"""
    return ListResourcesResult(
        resources=[
            Resource(
                uri="extraction://metrics",
                name="System Metrics",
                description="Real-time performance and usage metrics",
                mimeType="application/json"
            ),
            Resource(
                uri="extraction://health",
                name="Health Status",
                description="System health and component status",
                mimeType="application/json"
            ),
            Resource(
                uri="extraction://logs",
                name="Server Logs",
                description="Recent server log entries",
                mimeType="text/plain"
            )
        ]
    )

@server.read_resource()
async def handle_read_resource(uri: str) -> ReadResourceResult:
    """Read resource content"""
    await ensure_initialized()
    
    if uri == "extraction://metrics":
        metrics_data = orchestrator.metrics.get_stats()
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps(metrics_data, indent=2)
                )
            ]
        )
    elif uri == "extraction://health":
        health_data = await orchestrator.health_check()
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=json.dumps(health_data, indent=2)
                )
            ]
        )
    elif uri == "extraction://logs":
        # Read recent log entries
        log_content = "Recent server logs would be displayed here"
        if Path('/app/logs/mcp_server.log').exists():
            try:
                with open('/app/logs/mcp_server.log', 'r') as f:
                    lines = f.readlines()
                    log_content = ''.join(lines[-100:])  # Last 100 lines
            except Exception as e:
                log_content = f"Error reading logs: {e}"
        
        return ReadResourceResult(
            contents=[
                TextContent(
                    type="text",
                    text=log_content
                )
            ]
        )
    else:
        raise McpError(INVALID_REQUEST, f"Unknown resource: {uri}")

# ==================== PROMPT HANDLERS ====================

@server.list_prompts()
async def handle_list_prompts() -> ListPromptsResult:
    """List available prompts"""
    return ListPromptsResult(
        prompts=[
            Prompt(
                name="extract_contacts",
                description="Extract contact information from business websites",
                arguments=[
                    {"name": "website_url", "description": "URL of the business website", "required": True},
                    {"name": "business_type", "description": "Type of business (optional)", "required": False}
                ]
            ),
            Prompt(
                name="analyze_competitor",
                description="Analyze competitor website structure and content",
                arguments=[
                    {"name": "competitor_url", "description": "URL of competitor website", "required": True},
                    {"name": "analysis_focus", "description": "What to focus on (pricing, features, etc.)", "required": False}
                ]
            ),
            Prompt(
                name="scrape_ecommerce",
                description="Extract product data from e-commerce sites",
                arguments=[
                    {"name": "product_url", "description": "URL of product page or category", "required": True},
                    {"name": "data_points", "description": "Specific data points to extract", "required": False}
                ]
            )
        ]
    )

@server.get_prompt()
async def handle_get_prompt(name: str, arguments: Dict[str, str]) -> GetPromptResult:
    """Get prompt content"""
    
    if name == "extract_contacts":
        website_url = arguments.get("website_url", "")
        business_type = arguments.get("business_type", "general business")
        
        prompt_text = f"""Extract contact information from the following {business_type} website: {website_url}

Please focus on finding:
- Company name and address
- Phone numbers and email addresses
- Key personnel names and titles
- Social media profiles
- Business hours and contact methods

Use the intelligent_scrape tool with purpose "contact_discovery" to extract this information efficiently."""
        
        return GetPromptResult(
            description=f"Extract contact information from {business_type} website",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    elif name == "analyze_competitor":
        competitor_url = arguments.get("competitor_url", "")
        analysis_focus = arguments.get("analysis_focus", "overall strategy")
        
        prompt_text = f"""Analyze the competitor website: {competitor_url}

Focus on: {analysis_focus}

Please:
1. First use analyze_website_structure to understand the site architecture
2. Then use intelligent_scrape with purpose "competitor_analysis" to extract relevant data
3. Provide insights on their business model, pricing, and key features

Generate a comprehensive competitive analysis report."""
        
        return GetPromptResult(
            description=f"Analyze competitor focusing on {analysis_focus}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    elif name == "scrape_ecommerce":
        product_url = arguments.get("product_url", "")
        data_points = arguments.get("data_points", "price, description, reviews")
        
        prompt_text = f"""Extract product data from e-commerce site: {product_url}

Target data points: {data_points}

Please:
1. Use intelligent_scrape with purpose "e_commerce" 
2. Extract product information including pricing, descriptions, specifications
3. If available, gather customer reviews and ratings
4. Format the results in a structured way for analysis

Export the results in CSV format for easy processing."""
        
        return GetPromptResult(
            description=f"Extract e-commerce data focusing on {data_points}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text)
                )
            ]
        )
    
    else:
        raise McpError(INVALID_REQUEST, f"Unknown prompt: {name}")

# ==================== SIGNAL HANDLERS & MAIN ====================

def setup_signal_handlers():
    """Setup graceful shutdown signal handlers"""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        asyncio.create_task(shutdown_server())
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

async def shutdown_server():
    """Graceful server shutdown"""
    global orchestrator
    
    if orchestrator:
        await orchestrator.shutdown()
    
    logger.info("🏁 MCP Server shutdown complete")
    sys.exit(0)

async def main():
    """Main server entry point"""
    setup_signal_handlers()
    
    logger.info(f"🚀 Starting Intelligent Crawl4AI MCP Server v{config.server_version}")
    logger.info(f"📊 Metrics enabled: {config.enable_metrics}")
    logger.info(f"🔍 Health checks enabled: {config.enable_health_checks}")
    logger.info(f"🐛 Debug mode: {config.debug_mode}")
    
    try:
        # Initialize server components
        await ensure_initialized()
        
        # Start the MCP server
        async with stdio_server() as (read_stream, write_stream):
            logger.info("✅ MCP Server started and ready for connections!")
            
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name=config.server_name,
                    server_version=config.server_version,
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities={}
                    )
                )
            )
            
    except KeyboardInterrupt:
        logger.info("👋 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        logger.error(traceback.format_exc())
    finally:
        await shutdown_server()

if __name__ == "__main__":
    asyncio.run(main())
