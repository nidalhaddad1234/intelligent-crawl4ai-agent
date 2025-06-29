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

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import AI-first components
try:
    # from ai_core.enhanced_adaptive_planner import EnhancedAdaptivePlanner
    from ai_core.planner import AIPlanner as EnhancedAdaptivePlanner
    from ai_core.planner import PlanExecutor
    from ai_core.registry import tool_registry
except ImportError as e:
    logger.warning(f"AI core components not available: {e}")
    # Fallback mode
    EnhancedAdaptivePlanner = None
    PlanExecutor = None
    tool_registry = None

# Import tools to ensure they're registered
try:
    # Try to import tools but don't fail if specific imports are missing
    import ai_core.tools
except ImportError as e:
    logger.warning(f"Some tools not available: {e}")

# Keep URL extraction utilities
import re
def parse_message_with_urls(message):
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    urls = re.findall(url_pattern, message)
    cleaned = message
    for url in urls:
        cleaned = cleaned.replace(url, '')
    return cleaned.strip(), urls

def extract_urls_from_text(text):
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    return re.findall(url_pattern, text)

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
    """AI-First agent with fallback mode"""
    
    def __init__(self):
        self._initialized = False
        self.ai_mode = False
        
        # Configuration from environment
        self.config = {
            'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true'
        }
        
        # Try to initialize AI components
        if EnhancedAdaptivePlanner and PlanExecutor:
            try:
                self.planner = EnhancedAdaptivePlanner(
                    local_model=os.getenv('AI_MODEL', 'deepseek-coder:1.3b'),
                    local_ai_url=self.config['ollama_url']
                )
                self.executor = PlanExecutor()
                self.ai_mode = True
                logger.info("AI mode enabled")
            except Exception as e:
                logger.error(f"Failed to initialize AI components: {e}")
                self.ai_mode = False
        else:
            logger.warning("AI components not available - running in fallback mode")
            self.ai_mode = False
    
    async def initialize(self) -> bool:
        """Initialize agent components"""
        if self._initialized:
            return True
        
        try:
            logger.info("Initializing Intelligent Scraping Agent...")
            
            if self.ai_mode:
                # Verify AI is available
                import httpx
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.config['ollama_url']}/api/tags", timeout=2)
                        if response.status_code == 200:
                            logger.info("✅ Ollama AI is running")
                        else:
                            logger.error("❌ Ollama AI is not available")
                            self.ai_mode = False
                except Exception as e:
                    logger.error(f"❌ Cannot connect to Ollama: {e}")
                    self.ai_mode = False
            
            # Log available tools
            if tool_registry:
                tools = tool_registry.list_tools()
                logger.info(f"✅ Registered {len(tools)} tools: {tools}")
            else:
                logger.warning("Tool registry not available")
            
            self._initialized = True
            mode = "AI-First" if self.ai_mode else "Fallback"
            logger.info(f"🎉 Agent initialized in {mode} mode!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Agent initialization failed: {e}")
            return False
    
    async def process_chat_message(self, session_id: str, message: str, urls: Optional[List[str]] = None) -> str:
        """Process messages with AI or fallback mode"""
        try:
            # Extract URLs from message if not provided
            if not urls:
                _, urls = parse_message_with_urls(message)
            
            if self.ai_mode:
                # AI mode - use planner
                return await self._process_with_ai(message, urls)
            else:
                # Fallback mode - simple responses
                return await self._process_fallback(message, urls)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._handle_error(e)
    
    async def _process_with_ai(self, message: str, urls: Optional[List[str]]) -> str:
        """Process using AI planning"""
        # Add context about URLs if provided
        full_message = message
        if urls:
            url_context = f"\n\nURLs provided: {', '.join(urls)}"
            full_message += url_context
        
        # Let AI create the plan
        logger.info(f"Creating AI plan for: {message}")
        plan = self.planner.create_plan(full_message)
        
        # Log the plan for transparency
        logger.info(f"AI Plan created with {len(plan.steps)} steps, confidence: {plan.confidence:.0%}")
        for step in plan.steps:
            logger.info(f"  - Step {step.step_id}: {step.tool}({step.parameters})")
        
        # Execute the plan if confident enough
        if plan.steps and plan.confidence > 0.3:
            executed_plan = await self.executor.execute_plan(plan)
            return self._format_plan_results(executed_plan)
        else:
            return self._handle_unclear_request(message, plan.confidence)
    
    async def _process_fallback(self, message: str, urls: Optional[List[str]]) -> str:
        """Simple fallback processing without AI"""
        if urls:
            return f"""I can see you want to process {len(urls)} URLs.

In AI mode, I would:
1. Analyze each website's structure
2. Extract relevant data based on your request
3. Process and organize the results

Currently running in fallback mode. To enable AI features:
- Ensure Ollama is running: http://localhost:11434
- The AI core components need to be properly installed

URLs detected: {', '.join(urls[:3])}{'...' if len(urls) > 3 else ''}"""
        else:
            return """I'm running in fallback mode (AI components not available).

To get started:
- Provide URLs you want to scrape
- Describe what data you want to extract
- I'll help guide you through the process

Example: "Extract product prices from https://example.com"

For full AI capabilities, ensure all components are properly installed."""
    
    def _format_plan_results(self, plan) -> str:
        """Format plan execution results into user-friendly response"""
        if plan.status.value == "completed":
            results = []
            results.append(f"✅ {plan.description}")
            
            for step in plan.steps:
                if step.status.value == "completed":
                    results.append(f"\n• {step.description}")
                    if step.result and isinstance(step.result, dict):
                        if "data" in step.result:
                            results.append(f"  Found: {len(step.result.get('data', []))} items")
                elif step.status.value == "failed":
                    results.append(f"\n❌ Failed: {step.description}")
                    if step.error:
                        results.append(f"  Error: {step.error}")
            
            return "\n".join(results)
        else:
            return f"❌ Plan execution failed: {plan.description}\n\nPlease try rephrasing your request."
    
    def _handle_unclear_request(self, message: str, confidence: float) -> str:
        """Handle cases where AI can't understand the request"""
        return (
            f"I'm having trouble understanding your request (confidence: {confidence:.0%}).\n\n"
            "Could you provide more details? For example:\n\n"
            "• 'Analyze https://example.com for contact information'\n"
            "• 'Extract product data from these URLs: ...'\n"
            "• 'Export my recent scraping results as CSV'\n"
            "• 'Compare prices from multiple websites'"
        )
    
    def _handle_error(self, error: Exception) -> str:
        """Handle errors gracefully"""
        return (
            f"I encountered an error while processing your request: {str(error)}\n\n"
            "Please try rephrasing your request or check the system status."
        )

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
    static_path = Path("static/index.html")
    if static_path.exists():
        return FileResponse("static/index.html")
    else:
        # Fallback HTML if static file doesn't exist
        return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Intelligent Crawl4AI Agent</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .status { background: #f0f0f0; padding: 10px; border-radius: 5px; }
        .mode { font-weight: bold; color: #0066cc; }
    </style>
</head>
<body>
    <h1>🚀 Intelligent Crawl4AI Agent</h1>
    <div class="status">
        <p>Status: <span class="mode">Web UI is running!</span></p>
        <p>Mode: <span class="mode">{mode}</span></p>
        <p>API Docs: <a href="/api/docs">/api/docs</a></p>
        <p>Health Check: <a href="/health">/health</a></p>
    </div>
    <h2>Quick Start</h2>
    <p>Use the API endpoint <code>POST /api/chat</code> to interact with the agent.</p>
    <pre>
{
    "message": "Extract product data from https://example.com",
    "urls": ["https://example.com"]
}
    </pre>
</body>
</html>
        """.format(mode="AI-First" if scraping_agent.ai_mode else "Fallback"))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mode": "ai" if scraping_agent.ai_mode else "fallback",
        "timestamp": datetime.now(timezone.utc)
    }

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
            "ollama": "healthy" if scraping_agent.ai_mode else "not_available",
            "chromadb": "unknown",
            "database": "unknown"
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

# Mount static files if they exist
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    logger.warning("Static directory not found - static files won't be served")

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
