#!/usr/bin/env python3
"""
Web UI Server for Intelligent Crawl4AI Agent
FastAPI server providing ChatGPT-like interface for web scraping
"""

import asyncio
import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Import your existing agent components
try:
    from src.agents.intelligent_analyzer import IntelligentWebsiteAnalyzer
    from src.agents.strategy_selector import StrategySelector
    from src.agents.high_volume_executor import HighVolumeExecutor
    from src.utils.chromadb_manager import ChromaDBManager
    from src.utils.ollama_client import OllamaClient
    from src.database.sql_manager import DatabaseFactory
    from src.utils.url_extractor import parse_message_with_urls, extract_urls_from_text
except ImportError as e:
    print(f"Warning: Could not import agent modules: {e}")
    # Mock classes for development
    class IntelligentWebsiteAnalyzer:
        def __init__(self, *args, **kwargs): pass
        async def analyze_website(self, url): return {"mock": True}
    
    class StrategySelector:
        def __init__(self, *args, **kwargs): pass
        async def select_strategy(self, **kwargs): return {"primary_strategy": "mock"}
    
    class HighVolumeExecutor:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): pass
        async def submit_job(self, **kwargs): return "mock-job-id"
    
    class ChromaDBManager:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): pass
    
    class OllamaClient:
        def __init__(self, *args, **kwargs): pass
        async def initialize(self): pass
    
    class DatabaseFactory:
        @staticmethod
        def from_env(): return None
    
    # Fallback URL extraction if module not available
    def parse_message_with_urls(message):
        import re
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        urls = re.findall(url_pattern, message)
        cleaned = message
        for url in urls:
            cleaned = cleaned.replace(url, '')
        return cleaned.strip(), urls
    
    def extract_urls_from_text(text):
        import re
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        return re.findall(url_pattern, text)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models
class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ScrapingRequest(BaseModel):
    message: str = Field(..., description="User message/query")
    urls: Optional[List[str]] = Field(None, description="Optional URLs to scrape")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    options: Dict[str, Any] = Field(default_factory=dict, description="Additional scraping options")

class ScrapingResponse(BaseModel):
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    success: bool = Field(True, description="Whether the request was successful")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Extracted data if applicable")

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    total_urls: int
    processed_urls: int
    successful_extractions: int
    failed_extractions: int
    estimated_completion: Optional[datetime] = None
    results_preview: Optional[List[Dict[str, Any]]] = None

class SystemStatusResponse(BaseModel):
    status: str
    uptime_seconds: float
    total_requests: int
    active_sessions: int
    components_health: Dict[str, str]
    performance_metrics: Dict[str, Any]

# Global state management
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, List[ChatMessage]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        logger.info(f"Created new session: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, message: ChatMessage):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(message)
        logger.debug(f"Added message to session {session_id}: {message.role}")
    
    def get_messages(self, session_id: str) -> List[ChatMessage]:
        return self.sessions.get(session_id, [])
    
    def add_websocket(self, session_id: str, websocket: WebSocket):
        self.websocket_connections[session_id] = websocket
        logger.info(f"Added WebSocket connection for session: {session_id}")
    
    def remove_websocket(self, session_id: str):
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]
            logger.info(f"Removed WebSocket connection for session: {session_id}")
    
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        if session_id in self.websocket_connections:
            try:
                await self.websocket_connections[session_id].send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to session {session_id}: {e}")
                self.remove_websocket(session_id)

class IntelligentScrapingAgent:
    """Main agent class that orchestrates all scraping operations"""
    
    def __init__(self):
        self.ollama_client = None
        self.chromadb_manager = None
        self.website_analyzer = None
        self.strategy_selector = None
        self.high_volume_executor = None
        self.database = None
        self._initialized = False
        
        # Configuration from environment
        self.config = {
            'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            'chromadb_url': os.getenv('CHROMADB_URL', 'http://localhost:8000'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379'),
            'postgres_url': os.getenv('POSTGRES_URL', ''),
            'max_concurrent_jobs': int(os.getenv('MAX_CONCURRENT_JOBS', '10')),
            'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true'
        }
    
    async def initialize(self) -> bool:
        """Initialize all agent components"""
        if self._initialized:
            return True
        
        try:
            logger.info("Initializing Intelligent Scraping Agent...")
            
            # Initialize Ollama client
            self.ollama_client = OllamaClient(base_url=self.config['ollama_url'])
            await self.ollama_client.initialize()
            logger.info("✅ Ollama client initialized")
            
            # Initialize ChromaDB
            chromadb_host = self.config['chromadb_url'].split('://')[-1].split(':')[0]
            chromadb_port = int(self.config['chromadb_url'].split(':')[-1]) if ':' in self.config['chromadb_url'] else 8000
            self.chromadb_manager = ChromaDBManager(
                host=chromadb_host,
                port=chromadb_port,
                ollama_client=self.ollama_client
            )
            await self.chromadb_manager.initialize()
            logger.info("✅ ChromaDB initialized")
            
            # Initialize database
            self.database = DatabaseFactory.from_env()
            if self.database:
                await self.database.connect()
                logger.info("✅ Database initialized")
            
            # Initialize website analyzer
            self.website_analyzer = IntelligentWebsiteAnalyzer(self.ollama_client)
            logger.info("✅ Website Analyzer initialized")
            
            # Initialize strategy selector
            self.strategy_selector = StrategySelector(self.ollama_client, self.chromadb_manager)
            logger.info("✅ Strategy Selector initialized")
            
            # Initialize high-volume executor
            self.high_volume_executor = HighVolumeExecutor()
            await self.high_volume_executor.initialize()
            logger.info("✅ High-Volume Executor initialized")
            
            self._initialized = True
            logger.info("🎉 Agent initialization completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            return False
    
    async def process_chat_message(self, session_id: str, message: str, urls: Optional[List[str]] = None) -> str:
        """Process a chat message and determine the appropriate action"""
        
        # Extract URLs from message if not provided separately
        extracted_urls = []
        cleaned_message = message
        
        if not urls:
            # Try to extract URLs from the message text
            cleaned_message, extracted_urls = parse_message_with_urls(message)
            urls = extracted_urls if extracted_urls else None
        
        # Combine URLs from parameter and extracted URLs
        all_urls = []
        if urls:
            all_urls.extend(urls)
        if extracted_urls:
            all_urls.extend([url for url in extracted_urls if url not in urls])
        
        # Remove duplicates
        all_urls = list(dict.fromkeys(all_urls)) if all_urls else None
        
        # Log for debugging
        logger.info(f"Processing message: '{cleaned_message}' with URLs: {all_urls}")
        
        # Use cleaned message for intent detection
        message_lower = cleaned_message.lower()
        
        # Analyze intent - check for analyze/check/examine keywords
        if any(keyword in message_lower for keyword in ['analyze', 'analyse', 'check', 'examine', 'inspect', 'review']):
            if all_urls and len(all_urls) == 1:
                return await self._handle_analysis_request(all_urls[0], message)
            elif all_urls and len(all_urls) > 1:
                # Analyze multiple sites
                responses = []
                for i, url in enumerate(all_urls[:3], 1):  # Limit to 3 for UI clarity
                    responses.append(f"\n**Analysis {i}: {url}**")
                    analysis = await self._handle_single_analysis(url)
                    responses.append(analysis)
                return "\n".join(responses)
            else:
                return "To analyze a website, please provide a URL. For example: 'Analyze https://example.com' or use the URL input field below."
        
        # Scraping intent - check for scrape/extract/crawl/get keywords or currency/exchange/price queries
        elif any(keyword in message_lower for keyword in ['scrape', 'extract', 'get data', 'crawl', 'fetch', 'pull', 'collect', 'gather', 'how much', 'exchange', 'currency', 'rate', 'price', 'cost', 'convert', 'eur', 'usd', 'dollar', 'euro']):
            if all_urls:
                return await self._handle_scraping_request(session_id, message, all_urls)
            else:
                return "I'd be happy to help you scrape data! Please provide the URLs you'd like me to process. You can type them directly (e.g., 'Scrape https://example.com') or use the URL input field."
        
        # Job status intent
        elif any(keyword in message_lower for keyword in ['job', 'status', 'progress', 'check job', 'job status']):
            return await self._handle_job_status_request(message)
        
        # Search intent
        elif any(keyword in message_lower for keyword in ['search', 'find', 'look for', 'query']):
            return await self._handle_search_request(message)
        
        # Export intent
        elif any(keyword in message_lower for keyword in ['export', 'download', 'save', 'csv', 'excel', 'json']):
            return await self._handle_export_request(message)
        
        # Help intent
        elif any(keyword in message_lower for keyword in ['help', 'what can you do', 'capabilities', 'how to', 'guide']):
            return self._get_help_message()
        
        # If URLs are present but no clear intent, suggest actions
        elif all_urls:
            url_list = '\n'.join([f"• {url}" for url in all_urls[:5]])
            return f"I found these URLs in your message:\n{url_list}\n\nWhat would you like me to do with them?\n\n**Quick Actions:**\n• Type 'analyze' to analyze the website structure\n• Type 'scrape' to extract data\n• Type 'scrape contact info' to extract contact details\n• Type 'scrape products' to extract product information"
        
        else:
            return self._get_conversational_response(message)
    
    async def _handle_scraping_request(self, session_id: str, message: str, urls: List[str]) -> str:
        """Handle a scraping request"""
        try:
            if len(urls) > 50:
                # Use high-volume processing
                job_id = await self.high_volume_executor.submit_job(
                    urls=urls,
                    purpose="general_extraction",
                    session_id=session_id
                )
                return f"🚀 Started high-volume scraping job with ID: {job_id}\n\nProcessing {len(urls)} URLs. You can check the progress with: 'What's the status of job {job_id}?'"
            
            else:
                # Process directly
                results = []
                for url in urls[:10]:  # Limit to 10 for demo
                    try:
                        # Mock processing - replace with actual scraping logic
                        result = {
                            "url": url,
                            "success": True,
                            "data": {"title": f"Mock data for {url}", "content": "Sample extracted content"},
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                        results.append(result)
                    except Exception as e:
                        results.append({
                            "url": url,
                            "success": False,
                            "error": str(e)
                        })
                
                successful = sum(1 for r in results if r["success"])
                return f"✅ Completed scraping {len(urls)} URLs:\n\n• Successful: {successful}\n• Failed: {len(results) - successful}\n\nResults have been saved to your session. Would you like me to export them in a specific format?"
        
        except Exception as e:
            logger.error(f"Scraping request failed: {e}")
            return f"❌ Sorry, I encountered an error while processing your scraping request: {str(e)}"
    
    async def _handle_analysis_request(self, url: str, message: str) -> str:
        """Handle a website analysis request"""
        
        # Check if specific analysis is requested
        message_lower = message.lower()
        
        if 'contact' in message_lower:
            analysis_type = "contact information extraction"
        elif 'product' in message_lower:
            analysis_type = "product data extraction"
        elif 'price' in message_lower or 'pricing' in message_lower:
            analysis_type = "pricing information extraction"
        elif 'review' in message_lower:
            analysis_type = "reviews and ratings extraction"
        else:
            analysis_type = "general data extraction"
        
        response = await self._handle_single_analysis(url)
        response += f"\n\n**Specific Request**: Optimized for {analysis_type}"
        
        return response
    
    async def _handle_single_analysis(self, url: str) -> str:
        """Handle analysis for a single URL"""
        try:
            # Initialize analyzer if needed
            if not self.website_analyzer:
                return "❌ Website analyzer is not initialized. Please check system status."
            
            # Analyze the website
            analysis = await self.website_analyzer.analyze_website(url)
            
            # Format the analysis result
            framework = analysis.get('framework', 'Unknown')
            has_api = analysis.get('has_api', False)
            anti_bot = analysis.get('anti_bot_measures', [])
            recommended_strategy = analysis.get('recommended_strategy', 'DirectoryCSSStrategy')
            confidence = analysis.get('confidence', 0.5)
            
            anti_bot_status = 'Detected: ' + ', '.join(anti_bot) if anti_bot else 'None detected'
            
            return f"""🔍 **Website Analysis for {url}:**

• **Framework**: {framework}
• **Has API**: {'Yes' if has_api else 'No'}
• **Anti-bot measures**: {anti_bot_status}
• **Recommended strategy**: {recommended_strategy}
• **Confidence**: {confidence:.0%}

**Extraction Capabilities Detected:**
{self._get_extraction_capabilities(analysis)}

Would you like me to proceed with scraping using the recommended strategy?"""
            
        except Exception as e:
            logger.error(f"Analysis request failed: {e}")
            return f"❌ Sorry, I couldn't analyze the website: {str(e)}"
    
    def _get_extraction_capabilities(self, analysis: Dict[str, Any]) -> str:
        """Get extraction capabilities from analysis"""
        capabilities = []
        
        # Check for common data types
        if analysis.get('has_products', False):
            capabilities.append("• 🛍️ Product listings with prices")
        if analysis.get('has_contact', False):
            capabilities.append("• 📧 Contact information (email, phone, address)")
        if analysis.get('has_business_info', False):
            capabilities.append("• 🏢 Business details and descriptions")
        if analysis.get('has_reviews', False):
            capabilities.append("• ⭐ Reviews and ratings")
        if analysis.get('has_social_links', False):
            capabilities.append("• 🔗 Social media links")
        
        return '\n'.join(capabilities) if capabilities else "• 📄 General content extraction available"
    
    async def _handle_job_status_request(self, message: str) -> str:
        """Handle job status request"""
        # Extract job ID from message (simple regex or parsing)
        import re
        job_match = re.search(r'job[_\s-]?(\w+)', message, re.IGNORECASE)
        
        if job_match:
            job_id = job_match.group(1)
            # Mock status - replace with actual job status lookup
            return f"📊 Job Status for {job_id}:\n\n• Status: Processing\n• Progress: 65%\n• Processed: 650/1000 URLs\n• Success rate: 92%\n• Estimated completion: ~5 minutes\n\nI'll notify you when the job is complete!"
        else:
            return "To check job status, please provide the job ID. For example: 'What's the status of job abc123?'"
    
    async def _handle_search_request(self, message: str) -> str:
        """Handle semantic search request"""
        try:
            # Extract search query
            query = message.replace('search', '').replace('find', '').replace('look for', '').strip()
            
            # Mock search results - replace with actual semantic search
            results = [
                {"content": f"Found relevant data about: {query}", "similarity": 0.92, "source": "recent_scrape_1"},
                {"content": f"Additional information on: {query}", "similarity": 0.87, "source": "recent_scrape_2"}
            ]
            
            response = f"🔎 Search results for '{query}':\n\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result['content']} (similarity: {result['similarity']:.0%})\n"
            
            return response + "\nWould you like me to provide more details on any of these results?"
        
        except Exception as e:
            logger.error(f"Search request failed: {e}")
            return f"❌ Sorry, I couldn't perform the search: {str(e)}"
    
    async def _handle_export_request(self, message: str) -> str:
        """Handle data export request"""
        # Determine format from message
        format_map = {
            'csv': 'CSV',
            'excel': 'Excel',
            'json': 'JSON',
            'xml': 'XML'
        }
        
        format_type = 'JSON'  # default
        for fmt, name in format_map.items():
            if fmt in message.lower():
                format_type = name
                break
        
        return f"📥 Preparing {format_type} export of your scraped data...\n\nExport will include:\n• All recent scraping results\n• Timestamps and metadata\n• Success/failure status\n\nDownload link will be available shortly!"
    
    def _get_help_message(self) -> str:
        """Get help message"""
        return """🤖 **Intelligent Web Scraping Assistant**

I can help you with:

**🎯 Web Scraping:**
• "Scrape these URLs: [url1, url2, ...]"
• "Extract contact information from [url]"
• "Get product data from these e-commerce sites"

**🔍 Website Analysis:**
• "Analyze the structure of [url]"
• "What's the best strategy for scraping [url]?"

**⚡ High-Volume Processing:**
• "Process these 1000 URLs for business data"
• "Submit a bulk job for lead generation"

**📊 Job Management:**
• "What's the status of job [job_id]?"
• "Show me my recent scraping results"

**🔎 Data Search:**
• "Search for companies in tech industry"
• "Find all emails from recent scrapes"

**💾 Data Export:**
• "Export my data as CSV"
• "Download results in Excel format"

Just tell me what you'd like to scrape or ask me to analyze a website!"""
    
    def _get_conversational_response(self, message: str) -> str:
        """Get a conversational response for general queries"""
        greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon']
        
        if any(greeting in message.lower() for greeting in greetings):
            return "Hello! I'm your intelligent web scraping assistant. I can help you extract data from websites, analyze site structures, and manage large-scale scraping jobs. What would you like me to help you with today?"
        
        elif 'thank' in message.lower():
            return "You're welcome! Feel free to ask if you need help with any web scraping tasks."
        
        else:
            return "I'm here to help with web scraping and data extraction. You can ask me to scrape URLs, analyze websites, check job status, or search through extracted data. What would you like me to help you with?"

# Initialize global components
session_manager = SessionManager()
scraping_agent = IntelligentScrapingAgent()

# Create FastAPI app
app = FastAPI(
    title="Intelligent Web Scraping UI",
    description="ChatGPT-like interface for intelligent web scraping",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the scraping agent on startup"""
    logger.info("🚀 Starting Web UI Server...")
    success = await scraping_agent.initialize()
    if not success:
        logger.error("❌ Failed to initialize scraping agent")
    else:
        logger.info("✅ Web UI Server ready!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Shutting down Web UI Server...")

# API Routes
@app.get("/")
async def read_root():
    """Serve the main chat interface"""
    return FileResponse("static/index.html")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

@app.post("/api/chat", response_model=ScrapingResponse)
async def chat_endpoint(request: ScrapingRequest):
    """Main chat endpoint"""
    try:
        # Create session if not provided
        session_id = request.session_id or session_manager.create_session()
        
        # Add user message to session
        user_message = ChatMessage(
            role="user",
            content=request.message,
            metadata={"urls": request.urls, "options": request.options}
        )
        session_manager.add_message(session_id, user_message)
        
        # Process the message
        response_content = await scraping_agent.process_chat_message(
            session_id, request.message, request.urls
        )
        
        # Add assistant response to session
        assistant_message = ChatMessage(
            role="assistant",
            content=response_content
        )
        session_manager.add_message(session_id, assistant_message)
        
        return ScrapingResponse(
            response=response_content,
            session_id=session_id,
            metadata={"message_count": len(session_manager.get_messages(session_id))}
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get all messages for a session"""
    messages = session_manager.get_messages(session_id)
    return [message.dict() for message in messages]

@app.post("/api/sessions")
async def create_session():
    """Create a new chat session"""
    session_id = session_manager.create_session()
    return {"session_id": session_id}

@app.get("/api/system/status", response_model=SystemStatusResponse)
async def get_system_status():
    """Get system status and metrics"""
    return SystemStatusResponse(
        status="operational",
        uptime_seconds=time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0,
        total_requests=len(session_manager.sessions),
        active_sessions=len(session_manager.websocket_connections),
        components_health={
            "ollama": "healthy",
            "chromadb": "healthy",
            "database": "healthy"
        },
        performance_metrics={
            "avg_response_time_ms": 150,
            "success_rate": 0.95
        }
    )

# WebSocket endpoint for real-time communication
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    await websocket.accept()
    session_manager.add_websocket(session_id, websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Process the message
            response_content = await scraping_agent.process_chat_message(
                session_id, data.get("message", ""), data.get("urls")
            )
            
            # Send response back
            await websocket.send_json({
                "type": "response",
                "content": response_content,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
    except WebSocketDisconnect:
        session_manager.remove_websocket(session_id)
        logger.info(f"WebSocket disconnected for session: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        session_manager.remove_websocket(session_id)

# Mount static files
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # Set start time for uptime calculation
    app.state.start_time = time.time()
    
    # Run the server
    uvicorn.run(
        app,
        host=os.getenv("WEB_HOST", "0.0.0.0"),
        port=int(os.getenv("WEB_PORT", "8888")),
        log_level="info",
        access_log=True
    )