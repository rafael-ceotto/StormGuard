"""
Chat Router for StormGuard API
==============================
Real-time chat endpoints with RAG-powered disaster prediction
"""

from fastapi import APIRouter, HTTPException, status, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from api.utils.auth import get_current_user
from api.utils.db import get_db
from api.services.rag_service import get_rag_service, RAGService
from data_pipeline.db_models import ChatMessage, User
from datetime import datetime
import uuid
import json
import logging


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["chat"]
)


# ===== Pydantic Models =====

class ChatRequest(BaseModel):
    """Chat message request"""
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat message response"""
    id: str
    user_id: str
    user_message: str
    assistant_response: str
    sources: List[dict]
    session_id: str
    tokens_used: int
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    session_id: str
    messages: List[ChatResponse]
    created_at: datetime
    updated_at: datetime


# ===== HTTP Endpoints =====

@router.post(
    "/message",
    response_model=ChatResponse,
    summary="Send message to chat",
    description="Send a message to the RAG-powered disaster prediction chat"
)
async def chat_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service)
) -> ChatResponse:
    """
    Send a message to the RAG chat system
    
    **Request Body:**
    - message: str - User's question or message
    - session_id: Optional[str] - Conversation session ID (creates new if not provided)
    
    **Security:**
    - Requires valid JWT token
    
    **Returns:**
    - ChatResponse with AI response and context sources
    """
    
    # Get user data
    user_id = current_user.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Create session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    try:
        # Query RAG service
        rag_result = await rag_service.query_rag(
            user_message=request.message,
            user_location=(user.latitude, user.longitude),
            session_id=session_id
        )
        
        # Create chat message record
        chat_message_id = str(uuid.uuid4())
        chat_message = ChatMessage(
            id=chat_message_id,
            user_id=user_id,
            user_message=request.message,
            assistant_response=rag_result["response"],
            sources=json.dumps(rag_result["sources"]),
            session_id=session_id,
            tokens_used=rag_result["tokens_used"],
            created_at=datetime.utcnow()
        )
        
        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)
        
        # Parse sources back to list
        sources = json.loads(chat_message.sources) if chat_message.sources else []
        
        return ChatResponse(
            id=chat_message.id,
            user_id=chat_message.user_id,
            user_message=chat_message.user_message,
            assistant_response=chat_message.assistant_response,
            sources=sources,
            session_id=chat_message.session_id,
            tokens_used=chat_message.tokens_used,
            created_at=chat_message.created_at
        )
    
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing chat message: {str(e)}"
        )


@router.get(
    "/history/{session_id}",
    response_model=ChatHistoryResponse,
    summary="Get chat history",
    description="Retrieve chat history for a conversation session"
)
async def get_chat_history(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> ChatHistoryResponse:
    """
    Get chat history for a session
    
    **Path Parameters:**
    - session_id: str - Conversation session ID
    
    **Security:**
    - Requires valid JWT token
    - Can only access own chat history
    
    **Returns:**
    - ChatHistoryResponse with all messages in session
    """
    
    user_id = current_user.get("sub")
    
    # Get messages for this session
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.user_id == user_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No messages found for session {session_id}"
        )
    
    # Convert to response format
    message_responses = []
    for msg in messages:
        sources = json.loads(msg.sources) if msg.sources else []
        message_responses.append(
            ChatResponse(
                id=msg.id,
                user_id=msg.user_id,
                user_message=msg.user_message,
                assistant_response=msg.assistant_response,
                sources=sources,
                session_id=msg.session_id,
                tokens_used=msg.tokens_used,
                created_at=msg.created_at
            )
        )
    
    return ChatHistoryResponse(
        session_id=session_id,
        messages=message_responses,
        created_at=messages[0].created_at if messages else datetime.utcnow(),
        updated_at=messages[-1].created_at if messages else datetime.utcnow()
    )


@router.get(
    "/sessions",
    response_model=List[dict],
    summary="Get all chat sessions",
    description="Retrieve all conversation sessions for current user"
)
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
) -> List[dict]:
    """
    Get all chat sessions for current user
    
    **Security:**
    - Requires valid JWT token
    
    **Returns:**
    - List of session summaries
    """
    
    user_id = current_user.get("sub")
    
    # Get unique session IDs and their metadata
    sessions = db.query(ChatMessage).filter(
        ChatMessage.user_id == user_id
    ).distinct(ChatMessage.session_id).order_by(
        ChatMessage.session_id,
        ChatMessage.created_at.desc()
    ).all()
    
    session_list = []
    seen_sessions = set()
    
    for message in sessions:
        if message.session_id not in seen_sessions:
            seen_sessions.add(message.session_id)
            session_list.append({
                "session_id": message.session_id,
                "first_message": message.user_message[:100],
                "created_at": message.created_at,
                "message_count": db.query(ChatMessage).filter(
                    ChatMessage.session_id == message.session_id
                ).count()
            })
    
    return session_list


@router.delete(
    "/sessions/{session_id}",
    summary="Delete chat session",
    description="Delete a chat session and all its messages"
)
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a chat session
    
    **Path Parameters:**
    - session_id: str - Session ID to delete
    
    **Security:**
    - Requires valid JWT token
    - Can only delete own sessions
    """
    
    user_id = current_user.get("sub")
    
    # Delete all messages in the session
    deleted = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id,
        ChatMessage.user_id == user_id
    ).delete()
    
    db.commit()
    
    return {
        "deleted": deleted,
        "session_id": session_id,
        "message": f"Deleted {deleted} messages from session {session_id}"
    }


# ===== WebSocket Endpoint (Phase 4) =====

class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: dict = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, session_id: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        key = f"{user_id}:{session_id}"
        self.active_connections[key] = websocket
    
    def disconnect(self, user_id: str, session_id: str):
        """Remove WebSocket connection"""
        key = f"{user_id}:{session_id}"
        self.active_connections.pop(key, None)
    
    async def send_personal(self, message: str, user_id: str, session_id: str):
        """Send message to specific user session"""
        key = f"{user_id}:{session_id}"
        if key in self.active_connections:
            await self.active_connections[key].send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{user_id}/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    user_id: str,
    session_id: str,
    db: Session = Depends(get_db),
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    WebSocket endpoint for real-time chat
    
    **WebSocket Parameters:**
    - user_id: User ID
    - session_id: Chat session ID
    
    **Message Format:**
    ```json
    {
        "message": "User question here"
    }
    ```
    """
    
    await manager.connect(websocket, user_id, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse message
            try:
                payload = json.loads(data)
                user_message = payload.get("message", "")
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "error": "Invalid JSON format"
                }))
                continue
            
            # Get user for location
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                await websocket.send_text(json.dumps({
                    "error": "User not found"
                }))
                continue
            
            # Query RAG
            try:
                rag_result = await rag_service.query_rag(
                    user_message=user_message,
                    user_location=(user.latitude, user.longitude),
                    session_id=session_id
                )
                
                # Send streaming response
                await websocket.send_text(json.dumps({
                    "type": "response",
                    "response": rag_result["response"],
                    "sources": rag_result["sources"],
                    "tokens_used": rag_result["tokens_used"]
                }))
            
            except Exception as e:
                logger.error(f"RAG error: {e}")
                await websocket.send_text(json.dumps({
                    "error": str(e)
                }))
    
    except WebSocketDisconnect:
        manager.disconnect(user_id, session_id)
        logger.info(f"WebSocket disconnected: {user_id}:{session_id}")
