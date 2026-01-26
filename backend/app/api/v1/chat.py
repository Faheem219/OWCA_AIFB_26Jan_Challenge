"""
Chat API endpoints for real-time communication.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.security import HTTPBearer
import logging

from app.api.deps import get_current_user, get_database, get_redis, get_chat_service
from app.models.user import User
from app.models.chat import (
    ConversationCreateRequest, MessageCreateRequest, BroadcastMessageRequest,
    ConversationResponse, MessageResponse, ConversationListResponse,
    TypingStatus, ChatStats, GroupNegotiationCreateRequest, GroupNegotiationJoinRequest,
    GroupVoteRequest, GroupNegotiationResponse, BroadcastResponse, ParticipantManagementRequest,
    GroupNegotiationStatus, VoteType
)
from app.models.translation import LanguageCode
from app.services.chat_service import ChatService
from app.services.websocket_manager import websocket_endpoint
from app.db.redis import RedisCache

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a new conversation."""
    try:
        return await chat_service.create_conversation(
            request=request,
            creator_id=str(current_user.id),
            creator_name=current_user.full_name,
            creator_language=LanguageCode(current_user.preferred_language)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/conversations", response_model=List[ConversationListResponse])
async def get_conversations(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get user's conversations."""
    try:
        return await chat_service.get_conversations(
            user_id=str(current_user.id),
            page=page,
            size=size
        )
    except Exception as e:
        logger.error(f"Failed to get conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")


@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get messages from a conversation."""
    try:
        return await chat_service.get_conversation_messages(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            user_language=LanguageCode(current_user.preferred_language),
            page=page,
            size=size
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def send_message(
    conversation_id: str,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send a message in a conversation."""
    # Ensure conversation_id matches
    request.conversation_id = conversation_id
    
    try:
        return await chat_service.send_message(
            request=request,
            sender_id=str(current_user.id),
            sender_name=current_user.full_name,
            sender_language=LanguageCode(current_user.preferred_language)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


@router.post("/broadcast", response_model=BroadcastResponse)
async def send_broadcast_message(
    request: BroadcastMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Send broadcast message to multiple recipients."""
    try:
        return await chat_service.send_broadcast_message(
            request=request,
            sender_id=str(current_user.id),
            sender_name=current_user.full_name,
            sender_language=LanguageCode(current_user.preferred_language)
        )
    except Exception as e:
        logger.error(f"Failed to send broadcast: {e}")
        raise HTTPException(status_code=500, detail="Failed to send broadcast message")


@router.post("/conversations/{conversation_id}/typing")
async def set_typing_status(
    conversation_id: str,
    status: TypingStatus,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Set typing status for a user in a conversation."""
    try:
        await chat_service.set_typing_status(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            user_name=current_user.full_name,
            status=status
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to set typing status: {e}")
        raise HTTPException(status_code=500, detail="Failed to set typing status")


@router.get("/conversations/{conversation_id}/typing")
async def get_typing_users(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get users currently typing in a conversation."""
    try:
        return await chat_service.get_typing_users(conversation_id)
    except Exception as e:
        logger.error(f"Failed to get typing users: {e}")
        raise HTTPException(status_code=500, detail="Failed to get typing users")


@router.post("/messages/{message_id}/read")
async def mark_message_as_read(
    message_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Mark a message as read."""
    try:
        await chat_service.mark_message_as_read(
            message_id=message_id,
            user_id=str(current_user.id)
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to mark message as read: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark message as read")


@router.get("/stats", response_model=ChatStats)
async def get_chat_stats(
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get chat statistics for the current user."""
    try:
        return await chat_service.get_chat_stats(str(current_user.id))
    except Exception as e:
        logger.error(f"Failed to get chat stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat stats")


@router.websocket("/ws")
async def websocket_chat(
    websocket: WebSocket,
    token: str = Query(...),
    redis: RedisCache = Depends(get_redis)
):
    """WebSocket endpoint for real-time chat."""
    # Validate token and get user info
    try:
        from app.core.security import decode_access_token
        from app.db.mongodb import get_database
        from bson import ObjectId
        
        # Decode token to get user ID
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        
        # Get user info from database
        db = await get_database()
        user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        
        if not user_doc:
            await websocket.close(code=4002, reason="User not found")
            return
        
        user_name = user_doc.get("full_name", f"User {user_id}")
        
        # Handle WebSocket connection
        await websocket_endpoint(websocket, user_id, user_name, redis)
        
    except Exception as e:
        logger.error(f"WebSocket authentication error: {e}")
        await websocket.close(code=4003, reason="Authentication failed")


# Group Negotiation Endpoints

@router.post("/group-negotiations", response_model=GroupNegotiationResponse)
async def create_group_negotiation_room(
    request: GroupNegotiationCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a group negotiation room."""
    try:
        return await chat_service.create_group_negotiation_room(
            request=request,
            creator_id=str(current_user.id),
            creator_name=current_user.full_name,
            creator_language=LanguageCode(current_user.preferred_language)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create group negotiation room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create group negotiation room")


@router.post("/group-negotiations/{room_id}/join", response_model=GroupNegotiationResponse)
async def join_group_negotiation(
    room_id: str,
    request: GroupNegotiationJoinRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Join a group negotiation room."""
    request.room_id = room_id
    
    try:
        return await chat_service.join_group_negotiation(
            request=request,
            user_id=str(current_user.id),
            user_name=current_user.full_name,
            user_language=LanguageCode(current_user.preferred_language)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to join group negotiation: {e}")
        raise HTTPException(status_code=500, detail="Failed to join group negotiation")


@router.get("/group-negotiations", response_model=List[GroupNegotiationResponse])
async def get_group_negotiation_rooms(
    status: Optional[GroupNegotiationStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get group negotiation rooms for the current user."""
    try:
        return await chat_service.get_group_negotiation_rooms(
            user_id=str(current_user.id),
            status_filter=status
        )
    except Exception as e:
        logger.error(f"Failed to get group negotiation rooms: {e}")
        raise HTTPException(status_code=500, detail="Failed to get group negotiation rooms")


@router.post("/group-negotiations/{room_id}/decisions")
async def create_group_decision(
    room_id: str,
    decision_type: VoteType,
    description: str,
    deadline_hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Create a group decision for voting."""
    try:
        decision_id = await chat_service.create_group_decision(
            room_id=room_id,
            decision_type=decision_type,
            description=description,
            creator_id=str(current_user.id),
            deadline_hours=deadline_hours
        )
        return {"decision_id": decision_id, "status": "created"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create group decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to create group decision")


@router.post("/group-negotiations/vote")
async def vote_on_group_decision(
    request: GroupVoteRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Vote on a group decision."""
    try:
        is_complete = await chat_service.vote_on_decision(
            request=request,
            voter_id=str(current_user.id),
            voter_name=current_user.full_name
        )
        return {"status": "voted", "decision_complete": is_complete}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to vote on decision: {e}")
        raise HTTPException(status_code=500, detail="Failed to vote on decision")


@router.post("/group-negotiations/manage-participant")
async def manage_group_participant(
    request: ParticipantManagementRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Manage participants in group negotiation."""
    try:
        success = await chat_service.manage_participant(
            request=request,
            manager_id=str(current_user.id),
            manager_name=current_user.full_name
        )
        return {"status": "success" if success else "failed", "action": request.action}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to manage participant: {e}")
        raise HTTPException(status_code=500, detail="Failed to manage participant")