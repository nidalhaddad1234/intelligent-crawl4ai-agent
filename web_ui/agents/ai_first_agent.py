"""
AI-First Agent
Main AI processing agent for intent analysis and response generation
"""

from typing import Optional
from ..core.models import ChatResponse, IntentAnalysis


class AIFirstAgent:
    """Main AI agent for processing user requests"""
    
    def __init__(self):
        self.ai_planner = None  # Will be initialized with actual AI core
    
    async def process_message(self, message: str, session_id: str) -> ChatResponse:
        """Process user message and generate response"""
        
        # Analyze intent
        intent = await self._analyze_intent(message)
        
        # Generate response
        response_text = await self._generate_response(message, intent)
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            metadata={"processed": True},
            intent_analysis=intent.__dict__ if intent else None
        )
    
    async def _analyze_intent(self, message: str) -> IntentAnalysis:
        """Analyze user intent"""
        # Simplified intent analysis
        return IntentAnalysis(
            primary_intent="information_request",
            confidence=0.8,
            targets=[],
            parameters={},
            needs_clarification=False,
            reasoning="Simple intent analysis"
        )
    
    async def _generate_response(self, message: str, intent: IntentAnalysis) -> str:
        """Generate AI response"""
        return f"I understand you want to: {intent.primary_intent}. Let me help you with that!"


# Singleton instance
_ai_agent: Optional[AIFirstAgent] = None


def get_ai_agent() -> AIFirstAgent:
    """Get AI agent instance"""
    global _ai_agent
    if _ai_agent is None:
        _ai_agent = AIFirstAgent()
    return _ai_agent