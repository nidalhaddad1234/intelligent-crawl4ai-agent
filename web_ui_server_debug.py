#!/usr/bin/env python3
"""
Enhanced Web UI Server with Debug Logging for AI Reasoning
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

# Enhanced logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Set specific loggers for AI components
logging.getLogger('ai_core').setLevel(logging.DEBUG)
logging.getLogger('ai_core.planner').setLevel(logging.DEBUG)
logging.getLogger('ai_core.registry').setLevel(logging.DEBUG)

print("🚀 STARTING ENHANCED WEB UI WITH DEBUG LOGGING")
print("=" * 60)

# Import AI-first components with enhanced error handling
try:
    print("📦 Importing AI Core Components...")
    from ai_core.planner import AIPlanner, PlanExecutor
    from ai_core.registry import tool_registry
    print("✅ AI Core components imported successfully")
    AI_AVAILABLE = True
except ImportError as e:
    print(f"❌ AI core components not available: {e}")
    AI_AVAILABLE = False
    AIPlanner = None
    PlanExecutor = None
    tool_registry = None

# Import tools to ensure they're registered
try:
    print("🔧 Loading AI Tools...")
    import ai_core.tools
    if tool_registry:
        tools = tool_registry.list_tools()
        print(f"✅ Loaded {len(tools)} tools: {tools}")
    else:
        print("⚠️ Tool registry not available")
except ImportError as e:
    print(f"⚠️ Some tools not available: {e}")

# URL parsing utilities
import re
def parse_message_with_urls(message):
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    urls = re.findall(url_pattern, message)
    cleaned = message
    for url in urls:
        cleaned = cleaned.replace(url, '')
    return cleaned.strip(), urls

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

# Session Management
class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, List[ChatMessage]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        
    def create_session(self) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        logger.debug(f"🆔 Created new session: {session_id}")
        return session_id
    
    def add_message(self, session_id: str, message: ChatMessage):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        self.sessions[session_id].append(message)
        logger.debug(f"💬 Added {message.role} message to session {session_id}")
    
    def get_messages(self, session_id: str) -> List[ChatMessage]:
        return self.sessions.get(session_id, [])

# Enhanced Intelligent Scraping Agent with Debug Logging
class EnhancedIntelligentAgent:
    def __init__(self):
        logger.info("🤖 Initializing Enhanced Intelligent Agent...")
        self._initialized = False
        self.ai_mode = False
        
        # Configuration
        self.config = {
            'ollama_url': os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            'ollama_model': os.getenv('OLLAMA_MODEL', 'deepseek-coder:1.3b'),
            'debug_mode': os.getenv('DEBUG', 'false').lower() == 'true'
        }
        
        logger.info(f"🔧 Configuration: {self.config}")
        
        # Initialize AI components if available
        if AI_AVAILABLE and AIPlanner and PlanExecutor:
            try:
                logger.info("🧠 Initializing AI Planner...")
                self.planner = AIPlanner(
                    local_model=self.config['ollama_model'],
                    local_ai_url=self.config['ollama_url']
                )
                
                logger.info("⚡ Initializing Plan Executor...")
                self.executor = PlanExecutor()
                
                self.ai_mode = True
                logger.info("✅ AI mode enabled successfully!")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize AI components: {e}")
                self.ai_mode = False
        else:
            logger.warning("⚠️ AI components not available - running in fallback mode")
            self.ai_mode = False
    
    async def initialize(self) -> bool:
        """Initialize agent with comprehensive health checks"""
        if self._initialized:
            return True
        
        try:
            logger.info("🚀 Starting Agent Initialization...")
            
            # Test Ollama connection
            if self.ai_mode:
                logger.info("🔌 Testing Ollama connection...")
                try:
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(f"{self.config['ollama_url']}/api/tags", timeout=5)
                        if response.status_code == 200:
                            models = response.json()
                            logger.info(f"✅ Ollama connected! Available models: {[m['name'] for m in models.get('models', [])]}")
                        else:
                            logger.error(f"❌ Ollama responded with status {response.status_code}")
                            self.ai_mode = False
                except Exception as e:
                    logger.error(f"❌ Cannot connect to Ollama: {e}")
                    self.ai_mode = False
            
            # Test tool registry
            if tool_registry:
                tools = tool_registry.list_tools()
                logger.info(f"🔧 Available tools: {tools}")
                
                # Log tool details
                manifest = tool_registry.get_tool_manifest()
                for tool in manifest.get('tools', []):
                    logger.debug(f"  📋 {tool['name']}: {tool['description']}")
            else:
                logger.warning("⚠️ Tool registry not available")
            
            self._initialized = True
            mode = "🧠 AI-First" if self.ai_mode else "🔄 Fallback"
            logger.info(f"🎉 Agent initialized successfully in {mode} mode!")
            return True
            
        except Exception as e:
            logger.error(f"💥 Agent initialization failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def process_chat_message(self, session_id: str, message: str, urls: Optional[List[str]] = None) -> str:
        """Process chat messages with detailed logging"""
        logger.info("=" * 80)
        logger.info(f"📨 PROCESSING MESSAGE IN SESSION {session_id}")
        logger.info(f"📝 Message: {message}")
        logger.info(f"🔗 URLs: {urls}")
        logger.info("=" * 80)
        
        try:
            # Extract URLs if not provided
            if not urls:
                cleaned_message, extracted_urls = parse_message_with_urls(message)
                urls = extracted_urls
                logger.debug(f"🔍 Extracted URLs from message: {urls}")
            
            if self.ai_mode:
                logger.info("🧠 Using AI mode for processing...")
                return await self._process_with_ai_debug(message, urls)
            else:
                logger.info("🔄 Using fallback mode for processing...")
                return await self._process_fallback_debug(message, urls)
                
        except Exception as e:
            logger.error(f"💥 Error processing message: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._handle_error(e)
    
    async def _process_with_ai_debug(self, message: str, urls: Optional[List[str]]) -> str:
        """AI processing with comprehensive debug logging"""
        logger.info("🤖 STARTING AI PROCESSING...")
        
        # Prepare context
        full_message = message
        if urls:
            url_context = f"\\n\\nURLs to process: {', '.join(urls)}"
            full_message += url_context
            logger.debug(f"📋 Full message with URLs: {full_message}")
        
        # Step 1: AI Planning
        logger.info("🧠 STEP 1: Creating AI execution plan...")
        try:
            plan = self.planner.create_plan(full_message)
            logger.info(f"📊 Plan created!")
            logger.info(f"  📈 Confidence: {plan.confidence:.1%}")
            logger.info(f"  📝 Description: {plan.description}")
            logger.info(f"  🔢 Steps: {len(plan.steps)}")
            
            # Log each step in detail
            for i, step in enumerate(plan.steps, 1):
                logger.info(f"  📋 Step {i}: {step.tool}")
                logger.info(f"    📝 Description: {step.description}")
                logger.info(f"    ⚙️ Parameters: {step.parameters}")
                logger.info(f"    🔗 Depends on: {step.depends_on}")
            
        except Exception as e:
            logger.error(f"💥 Plan creation failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Failed to create execution plan: {str(e)}"
        
        # Step 2: Plan Validation
        logger.info("🔍 STEP 2: Validating plan...")
        if not plan.steps:
            logger.warning("⚠️ No steps in plan")
            return self._handle_no_steps(message)
        
        if plan.confidence < 0.3:
            logger.warning(f"⚠️ Low confidence plan: {plan.confidence:.1%}")
            return self._handle_low_confidence(message, plan.confidence)
        
        # Step 3: Plan Execution
        logger.info("⚡ STEP 3: Executing plan...")
        try:
            logger.info("🚀 Starting plan execution...")
            executed_plan = await self.executor.execute_plan(plan)
            logger.info(f"✅ Plan execution completed with status: {executed_plan.status}")
            
            # Log execution results
            for i, step in enumerate(executed_plan.steps, 1):
                logger.info(f"📊 Step {i} Results:")
                logger.info(f"  ✅ Status: {step.status}")
                if step.result:
                    logger.info(f"  📄 Result type: {type(step.result)}")
                    logger.info(f"  📊 Result: {str(step.result)[:200]}...")
                if step.error:
                    logger.error(f"  ❌ Error: {step.error}")
            
        except Exception as e:
            logger.error(f"💥 Plan execution failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return f"❌ Failed to execute plan: {str(e)}"
        
        # Step 4: Format Response
        logger.info("📝 STEP 4: Formatting response...")
        response = self._format_plan_results_debug(executed_plan)
        logger.info(f"📤 Final response: {response[:200]}...")
        
        return response
    
    async def _process_fallback_debug(self, message: str, urls: Optional[List[str]]) -> str:
        """Fallback processing with debug logging"""
        logger.info("🔄 PROCESSING IN FALLBACK MODE...")
        
        if urls:
            logger.info(f"🔗 Processing {len(urls)} URLs in fallback mode")
            response = f"""🔄 **Fallback Mode Response**

I can see you want to process {len(urls)} URLs:
{chr(10).join(f'• {url}' for url in urls[:5])}
{'...' if len(urls) > 5 else ''}

**In AI mode, I would:**
1. 🧠 Analyze your request: "{message}"
2. 🔍 Examine each website's structure  
3. 📊 Extract relevant data based on your needs
4. 📋 Process and organize the results
5. 📤 Provide structured output

**Current Status:**
- ❌ AI mode not available
- ⚠️ Ollama connection: {self.config['ollama_url']}
- 🔧 Tool registry: {'Available' if tool_registry else 'Not Available'}

**To enable AI features:**
- Ensure Ollama is running and accessible
- Verify AI core components are properly installed
- Check the logs for specific error details
"""
        else:
            logger.info("💬 Processing general query in fallback mode")
            response = f"""🔄 **Fallback Mode - General Help**

Your request: "{message}"

**I'm currently running in fallback mode.**

**To get started with web scraping:**
- Provide URLs you want to scrape
- Describe what data you want to extract
- Example: "Extract product prices from https://example.com"

**For full AI capabilities:**
- ✅ Ensure Ollama is running: {self.config['ollama_url']}
- ✅ Check AI components are loaded
- ✅ View console logs for detailed diagnostics

**System Status:**
- 🔧 Tool Registry: {'✅' if tool_registry else '❌'} 
- 🧠 AI Mode: {'✅' if self.ai_mode else '❌'}
- 🐛 Debug Mode: {'✅' if self.config['debug_mode'] else '❌'}
"""
        
        logger.debug(f"📤 Fallback response: {response[:100]}...")
        return response
    
    def _format_plan_results_debug(self, plan) -> str:
        """Format results with debug information"""
        logger.info("📝 Formatting plan results...")
        
        if plan.status.value == "completed":
            logger.info("✅ Plan completed successfully")
            results = [f"✅ **{plan.description}**\\n"]
            
            success_count = 0
            for step in plan.steps:
                if step.status.value == "completed":
                    success_count += 1
                    results.append(f"• ✅ {step.description}")
                    
                    if step.result and isinstance(step.result, dict):
                        if "data" in step.result:
                            data_count = len(step.result.get('data', []))
                            results.append(f"  📊 Found: {data_count} items")
                            logger.info(f"📊 Step {step.step_id} found {data_count} items")
                        
                        if "url" in step.result:
                            results.append(f"  🔗 Source: {step.result['url']}")
                            
                elif step.status.value == "failed":
                    results.append(f"• ❌ Failed: {step.description}")
                    if step.error:
                        results.append(f"  🔍 Error: {step.error}")
                        logger.error(f"❌ Step {step.step_id} failed: {step.error}")
            
            results.append(f"\\n📈 **Summary:** {success_count}/{len(plan.steps)} steps completed successfully")
            
            final_result = "\\n".join(results)
            logger.info(f"📋 Formatted {len(results)} result lines")
            return final_result
        else:
            logger.error(f"❌ Plan failed with status: {plan.status}")
            return f"❌ **Execution Failed**\\n\\n{plan.description}\\n\\nPlease try rephrasing your request or check the system status."
    
    def _handle_no_steps(self, message: str) -> str:
        """Handle case where no steps were generated"""
        logger.warning("⚠️ No steps generated by AI planner")
        return f"""⚠️ **Unable to Create Execution Plan**

I couldn't generate steps for your request: "{message}"

**Possible reasons:**
• Request might be too vague or unclear
• Required tools might not be available
• AI model needs more specific instructions

**Please try:**
• Being more specific about what data you want
• Including example URLs to process
• Using phrases like "extract", "analyze", or "scrape"

**Examples:**
• "Extract contact information from https://example.com"
• "Get product prices from these URLs: ..."
• "Analyze the main content of this webpage"
"""
    
    def _handle_low_confidence(self, message: str, confidence: float) -> str:
        """Handle low confidence scenarios"""
        logger.warning(f"⚠️ Low confidence plan: {confidence:.1%}")
        return f"""🤔 **Uncertain About Your Request**

Confidence Level: {confidence:.1%}

Your request: "{message}"

**I'm not fully confident about how to handle this request.**

**To improve accuracy, please:**
• Be more specific about the data you want
• Provide example URLs if applicable
• Use clearer action words like "extract", "scrape", "analyze"

**Good examples:**
• "Extract all email addresses from company pages"
• "Get product titles and prices from this e-commerce site"
• "Analyze the main content and headings from news articles"
"""
    
    def _handle_error(self, error: Exception) -> str:
        """Handle errors with detailed information"""
        error_id = str(uuid.uuid4())[:8]
        logger.error(f"💥 Error {error_id}: {str(error)}")
        
        return f"""❌ **Processing Error**

Error ID: {error_id}
Error: {str(error)}

**This error has been logged for debugging.**

**Please try:**
• Rephrasing your request
• Checking if the URLs are accessible
• Using simpler language in your request

**If the problem persists:**
• Check the console logs for detailed error information
• Verify system components are running properly
• Contact support with Error ID: {error_id}
"""

# Initialize global components
session_manager = SessionManager()
scraping_agent = EnhancedIntelligentAgent()

# Create FastAPI app
app = FastAPI(
    title="Enhanced Intelligent Web Scraping UI",
    description="ChatGPT-like interface with comprehensive debugging",
    version="2.0.0",
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
    logger.info("🚀 STARTING ENHANCED WEB UI SERVER...")
    success = await scraping_agent.initialize()
    if not success:
        logger.error("❌ Failed to initialize scraping agent")
    else:
        logger.info("✅ Enhanced Web UI Server ready!")

# Main routes
@app.get("/")
async def read_root():
    """Enhanced main page"""
    return HTMLResponse(f"""
<!DOCTYPE html>
<html>
<head>
    <title>Enhanced Intelligent Crawl4AI Agent</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; text-align: center; }}
        .status {{ background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #27ae60; }}
        .mode {{ font-weight: bold; color: #2980b9; }}
        .endpoint {{ background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 3px solid #3498db; }}
        .debug {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #ffc107; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: 'Courier New', monospace; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Enhanced Intelligent Crawl4AI Agent</h1>
        
        <div class="status">
            <h3>🔧 System Status</h3>
            <p><strong>Mode:</strong> <span class="mode">{'🧠 AI-First' if scraping_agent.ai_mode else '🔄 Fallback'}</span></p>
            <p><strong>Debug:</strong> <span class="mode">{'✅ Enabled' if scraping_agent.config['debug_mode'] else '❌ Disabled'}</span></p>
            <p><strong>Tools:</strong> <span class="mode">{len(tool_registry.list_tools()) if tool_registry else 0} available</span></p>
            <p><strong>Ollama:</strong> <span class="mode">{scraping_agent.config['ollama_url']}</span></p>
        </div>

        <div class="debug">
            <h3>🐛 Debug Information</h3>
            <p>This enhanced version provides comprehensive logging of AI reasoning processes.</p>
            <p><strong>Check the console logs</strong> to see detailed information about:</p>
            <ul>
                <li>🧠 AI planning steps</li>
                <li>🔧 Tool selection and execution</li>
                <li>📊 Results processing</li>
                <li>❌ Error handling and debugging</li>
            </ul>
        </div>

        <div class="endpoint">
            <h3>🚀 Quick Test</h3>
            <p>Use this curl command to test the enhanced agent:</p>
            <code>
curl -X POST http://localhost:8888/api/chat \\<br>
  -H "Content-Type: application/json" \\<br>
  -d '{{"message": "Extract the title from https://example.com"}}'
            </code>
        </div>

        <div class="endpoint">
            <h3>📋 API Documentation</h3>
            <p><strong>Interactive Docs:</strong> <a href="/api/docs">/api/docs</a></p>
            <p><strong>Health Check:</strong> <a href="/health">/health</a></p>
            <p><strong>System Status:</strong> <a href="/api/system/status">/api/system/status</a></p>
        </div>
    </div>
</body>
</html>
    """)

@app.get("/health")
async def health_check():
    """Enhanced health check with detailed information"""
    return {
        "status": "healthy",
        "mode": "ai" if scraping_agent.ai_mode else "fallback",
        "debug_enabled": scraping_agent.config['debug_mode'],
        "ollama_url": scraping_agent.config['ollama_url'],
        "tools_available": len(tool_registry.list_tools()) if tool_registry else 0,
        "timestamp": datetime.now(timezone.utc)
    }

@app.post("/api/chat", response_model=ScrapingResponse)
async def enhanced_chat_endpoint(request: ScrapingRequest):
    """Enhanced chat endpoint with comprehensive logging"""
    logger.info("=" * 100)
    logger.info("🎯 NEW CHAT REQUEST RECEIVED")
    logger.info(f"📨 Message: {request.message}")
    logger.info(f"🔗 URLs: {request.urls}")
    logger.info(f"🆔 Session: {request.session_id}")
    logger.info("=" * 100)
    
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
        
        # Process the message with enhanced logging
        response_content = await scraping_agent.process_chat_message(
            session_id, request.message, request.urls
        )
        
        # Add assistant response to session
        assistant_message = ChatMessage(
            role="assistant",
            content=response_content
        )
        session_manager.add_message(session_id, assistant_message)
        
        logger.info("✅ Chat request processed successfully")
        logger.info("=" * 100)
        
        return ScrapingResponse(
            response=response_content,
            session_id=session_id,
            metadata={
                "message_count": len(session_manager.get_messages(session_id)),
                "ai_mode": scraping_agent.ai_mode,
                "debug_enabled": scraping_agent.config['debug_mode']
            }
        )
        
    except Exception as e:
        logger.error(f"💥 Chat endpoint error: {e}")
        import traceback
        logger.error(traceback.format_exc())
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

@app.get("/api/system/status")
async def get_enhanced_system_status():
    """Enhanced system status with detailed debugging info"""
    tool_count = len(tool_registry.list_tools()) if tool_registry else 0
    
    return {
        "status": "operational",
        "mode": "ai" if scraping_agent.ai_mode else "fallback",
        "debug_enabled": scraping_agent.config['debug_mode'],
        "components": {
            "ai_planner": "available" if scraping_agent.ai_mode else "unavailable",
            "tool_registry": "available" if tool_registry else "unavailable",
            "ollama": scraping_agent.config['ollama_url'],
            "tools_count": tool_count
        },
        "sessions": {
            "total": len(session_manager.sessions),
            "active": len(session_manager.websocket_connections)
        },
        "timestamp": datetime.now(timezone.utc)
    }

if __name__ == "__main__":
    # Set start time for uptime calculation
    app.state.start_time = time.time()
    
    print("🌟 ENHANCED WEB UI SERVER STARTING...")
    print(f"🔧 Debug Mode: {os.getenv('DEBUG', 'false').lower() == 'true'}")
    print(f"🧠 AI Mode: {AI_AVAILABLE}")
    print(f"🛠️ Tools Available: {len(tool_registry.list_tools()) if tool_registry else 0}")
    print("=" * 60)
    
    # Run the server
    uvicorn.run(
        app,
        host=os.getenv("WEB_HOST", "0.0.0.0"),
        port=int(os.getenv("WEB_PORT", "8888")),
        log_level="debug",
        access_log=True
    )
