"""
Session Management Service
Handles user sessions, WebSocket connections, and state management
"""

import uuid
from typing import Dict, List, Optional, Any
from fastapi import WebSocket

from ..core.models import ChatMessage


class SessionManager:
    """Manages user sessions and WebSocket connections"""
    
    def __init__(self):
        self.sessions: Dict[str, List[ChatMessage]] = {}
        self.websocket_connections: Dict[str, WebSocket] = {}
        self.active_jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self) -> str:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = []
        return session_id
    
    def add_message(self, session_id: str, message: ChatMessage):
        """Add message to session"""
        if session_id in self.sessions:
            self.sessions[session_id].append(message)
    
    def get_session_messages(self, session_id: str) -> List[ChatMessage]:
        """Get all messages for a session"""
        return self.sessions.get(session_id, [])
    
    def add_websocket_connection(self, session_id: str, websocket: WebSocket):
        """Add WebSocket connection"""
        self.websocket_connections[session_id] = websocket
    
    def remove_websocket_connection(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.websocket_connections:
            del self.websocket_connections[session_id]


# Singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get session manager instance"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager