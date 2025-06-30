"""
Chat API endpoints
Handles pure chat interface and intent processing
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.websockets import WebSocket, WebSocketDisconnect

from ..core.models import PureChatRequest, ChatResponse
from ..services.session_manager import get_session_manager
from ..agents.ai_first_agent import get_ai_agent

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
async def send_message(
    request: PureChatRequest,
    session_manager=Depends(get_session_manager),
    ai_agent=Depends(get_ai_agent)
):
    """Process a pure chat message"""
    try:
        # Create session if needed
        if not request.session_id:
            request.session_id = session_manager.create_session()
        
        # Process with AI agent
        response = await ai_agent.process_message(request.message, request.session_id)
        
        return ChatResponse(
            response=response.response,
            session_id=request.session_id,
            metadata=response.metadata,
            intent_analysis=response.intent_analysis
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat"""
    session_manager = get_session_manager()
    
    await websocket.accept()
    session_manager.add_websocket_connection(session_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Process message and send response
            await websocket.send_text(f"Echo: {data}")
    
    except WebSocketDisconnect:
        session_manager.remove_websocket_connection(session_id)