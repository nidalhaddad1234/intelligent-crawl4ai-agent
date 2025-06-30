"""
Web UI Integration - Replace hardcoded logic with AI planning

This module shows how to integrate the AI planner into the web UI server,
removing all hardcoded if/else logic.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..planner import UnifiedAIPlanner, PlanExecutor
from ..registry import tool_registry


logger = logging.getLogger(__name__)


class AIFirstScrapingAgent:
    """
    AI-First version of the scraping agent
    NO HARDCODED LOGIC - Everything goes through AI planning
    """
    
    def __init__(self):
        # Initialize AI components
        self.planner = UnifiedAIPlanner(
            local_ai_url="http://localhost:11434",
            local_model="deepseek-coder:1.3b",
            confidence_threshold=0.7
        )
        self.executor = PlanExecutor()
        
        # Components from original agent
        self.ollama_client = None
        self.chromadb_manager = None
        self.database = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the agent components"""
        try:
            # Initialize tools (they self-register)
            logger.info("Initializing AI-First Scraping Agent...")
            
            # Import tools to trigger registration
            from ..tools import crawler, database, analyzer, exporter
            
            logger.info(f"✅ Registered {len(tool_registry.list_tools())} tools")
            
            # Initialize other components as needed
            # ... (database, chromadb, etc.)
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def process_message(self, 
                            session_id: str, 
                            message: str, 
                            context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process any message using AI planning - NO HARDCODED LOGIC!
        
        Args:
            session_id: Session identifier
            message: User's natural language message
            context: Optional context (URLs, previous messages, etc.)
            
        Returns:
            Response string
        """
        try:
            # 1. Let AI create a plan from the message
            logger.info(f"Creating AI plan for: {message}")
            plan = self.planner.create_plan(message)
            
            # 2. Log the plan for transparency
            logger.info(f"AI Plan created with {len(plan.steps)} steps:")
            for step in plan.steps:
                logger.info(f"  - Step {step.step_id}: {step.tool}({step.parameters})")
            
            # 3. Execute the plan
            if plan.steps:
                executed_plan = await self.executor.execute_plan(plan)
                
                # 4. Format the results
                return self._format_plan_results(executed_plan)
            else:
                # AI couldn't create a plan - ask for clarification
                return self._handle_unclear_request(message)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._handle_error(e)
    
    def _format_plan_results(self, plan) -> str:
        """
        Format plan execution results into a user-friendly response
        NO HARDCODED TEMPLATES - Let AI format too!
        """
        # For now, simple formatting - this should also use AI
        if plan.status.value == "completed":
            results = []
            results.append(f"✅ Completed: {plan.description}")
            
            # Show what was done
            for step in plan.steps:
                if step.status.value == "completed":
                    results.append(f"\n• {step.description}")
                    if step.result and isinstance(step.result, dict):
                        if "data" in step.result:
                            results.append(f"  Found: {len(step.result.get('data', []))} items")
                elif step.status.value == "failed":
                    results.append(f"\n❌ Failed: {step.description}")
                    results.append(f"  Error: {step.error}")
            
            return "\n".join(results)
        else:
            return f"❌ Plan execution failed: {plan.description}"
    
    def _handle_unclear_request(self, message: str) -> str:
        """Handle cases where AI can't understand the request"""
        # Even this could use AI for better responses!
        return (
            "I'm having trouble understanding your request. "
            "Could you provide more details? For example:\n\n"
            "• 'Analyze https://example.com for contact information'\n"
            "• 'Extract product data from these URLs: ...'\n"
            "• 'Export my recent scraping results as CSV'"
        )
    
    def _handle_error(self, error: Exception) -> str:
        """Handle errors gracefully"""
        return (
            f"I encountered an error while processing your request: {str(error)}\n\n"
            "Please try rephrasing your request or check the system status."
        )


def create_ai_first_chat_handler():
    """
    Factory function to create the new chat handler
    This replaces the entire process_chat_message logic
    """
    agent = AIFirstScrapingAgent()
    
    async def handle_chat(session_id: str, 
                         message: str, 
                         urls: Optional[List[str]] = None) -> str:
        """
        New chat handler - NO HARDCODED LOGIC!
        Everything goes through AI planning
        """
        # Initialize if needed
        if not agent._initialized:
            await agent.initialize()
        
        # Create context from any provided data
        context = {}
        if urls:
            context["urls"] = urls
        
        # Let AI handle EVERYTHING
        return await agent.process_message(session_id, message, context)
    
    return handle_chat


# Example of how to modify web_ui_server.py:
"""
# REPLACE THIS:
async def process_chat_message(self, session_id: str, message: str, urls: Optional[List[str]] = None) -> str:
    # 300+ lines of if/elif/else logic...
    
# WITH THIS:
from ai_core.integrations.web_ui_integration import create_ai_first_chat_handler

class IntelligentScrapingAgent:
    def __init__(self):
        # ... existing init ...
        self.ai_chat_handler = create_ai_first_chat_handler()
    
    async def process_chat_message(self, session_id: str, message: str, urls: Optional[List[str]] = None) -> str:
        return await self.ai_chat_handler(session_id, message, urls)
"""


# Additional helper to update specific parts of the old agent
def transform_existing_methods():
    """
    Guide for transforming existing methods to use AI
    """
    transformations = {
        "_handle_analysis_request": """
        # OLD: Manual keyword checking
        # NEW: Let AI decide what type of analysis
        async def _handle_analysis_request(self, url: str, message: str) -> str:
            plan = self.planner.create_plan(f"analyze {url} based on: {message}")
            result = await self.executor.execute_plan(plan)
            return self._format_plan_results(result)
        """,
        
        "_handle_scraping_request": """
        # OLD: Manual URL counting and routing
        # NEW: AI decides high-volume vs regular
        async def _handle_scraping_request(self, session_id: str, message: str, urls: List[str]) -> str:
            context = {"urls": urls, "session_id": session_id}
            plan = self.planner.create_plan(message)
            result = await self.executor.execute_plan(plan)
            return self._format_plan_results(result)
        """,
        
        "_get_extraction_capabilities": """
        # OLD: Hardcoded capability detection
        # NEW: AI analyzes and describes capabilities
        async def _get_extraction_capabilities(self, analysis: Dict[str, Any]) -> str:
            plan = self.planner.create_plan(
                f"describe extraction capabilities from analysis: {analysis}"
            )
            result = await self.executor.execute_plan(plan)
            return result.get("description", "General extraction available")
        """
    }
    
    return transformations
