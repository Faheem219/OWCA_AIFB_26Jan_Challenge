"""
WebSocket manager for real-time chat communication.
"""
import json
import logging
from typing import Dict, List, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from app.db.redis import RedisCache
from app.models.chat import WebSocketMessage, TypingStatus
from app.models.translation import LanguageCode

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time chat."""
    
    def __init__(self, redis: RedisCache):
        """Initialize connection manager."""
        self.redis = redis
        # Active connections: user_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # User subscriptions: user_id -> set of conversation_ids
        self.user_subscriptions: Dict[str, Set[str]] = {}
        # Conversation subscribers: conversation_id -> set of user_ids
        self.conversation_subscribers: Dict[str, Set[str]] = {}
        
        # Redis pubsub for scaling across multiple instances
        self.pubsub = None
    
    async def connect(self, websocket: WebSocket, user_id: str, user_name: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        # Store connection
        self.active_connections[user_id] = websocket
        self.user_subscriptions[user_id] = set()
        
        # Mark user as online
        await self.redis.sadd("online_users", user_id)
        await self.redis.setex(f"user_online:{user_id}", 300, user_name)  # 5 min expiry
        
        logger.info(f"User {user_id} connected to WebSocket")
        
        # Start listening to Redis pubsub for this user
        await self._start_redis_listener(user_id)
    
    async def disconnect(self, user_id: str):
        """Handle WebSocket disconnection."""
        if user_id in self.active_connections:
            # Remove from all conversation subscriptions
            if user_id in self.user_subscriptions:
                for conv_id in self.user_subscriptions[user_id]:
                    if conv_id in self.conversation_subscribers:
                        self.conversation_subscribers[conv_id].discard(user_id)
                        if not self.conversation_subscribers[conv_id]:
                            del self.conversation_subscribers[conv_id]
                
                del self.user_subscriptions[user_id]
            
            # Remove connection
            del self.active_connections[user_id]
            
            # Mark user as offline
            await self.redis.srem("online_users", user_id)
            await self.redis.delete(f"user_online:{user_id}")
            
            logger.info(f"User {user_id} disconnected from WebSocket")
    
    async def subscribe_to_conversation(self, user_id: str, conversation_id: str):
        """Subscribe user to a conversation for real-time updates."""
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        self.user_subscriptions[user_id].add(conversation_id)
        
        if conversation_id not in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id] = set()
        
        self.conversation_subscribers[conversation_id].add(user_id)
        
        logger.debug(f"User {user_id} subscribed to conversation {conversation_id}")
    
    async def unsubscribe_from_conversation(self, user_id: str, conversation_id: str):
        """Unsubscribe user from a conversation."""
        if user_id in self.user_subscriptions:
            self.user_subscriptions[user_id].discard(conversation_id)
        
        if conversation_id in self.conversation_subscribers:
            self.conversation_subscribers[conversation_id].discard(user_id)
            if not self.conversation_subscribers[conversation_id]:
                del self.conversation_subscribers[conversation_id]
        
        logger.debug(f"User {user_id} unsubscribed from conversation {conversation_id}")
    
    async def send_personal_message(self, user_id: str, message: dict):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to user {user_id}: {e}")
                # Connection might be stale, remove it
                await self.disconnect(user_id)
    
    async def broadcast_to_conversation(self, conversation_id: str, message: dict, exclude_user: str = None):
        """Broadcast a message to all subscribers of a conversation."""
        if conversation_id not in self.conversation_subscribers:
            return
        
        subscribers = self.conversation_subscribers[conversation_id].copy()
        if exclude_user:
            subscribers.discard(exclude_user)
        
        # Send to all subscribers
        for user_id in subscribers:
            await self.send_personal_message(user_id, message)
    
    async def handle_message(self, user_id: str, message_data: dict):
        """Handle incoming WebSocket message from user."""
        try:
            message_type = message_data.get("type")
            conversation_id = message_data.get("conversation_id")
            
            if not conversation_id:
                await self.send_personal_message(user_id, {
                    "type": "error",
                    "message": "conversation_id is required"
                })
                return
            
            if message_type == "subscribe":
                await self.subscribe_to_conversation(user_id, conversation_id)
                await self.send_personal_message(user_id, {
                    "type": "subscribed",
                    "conversation_id": conversation_id
                })
            
            elif message_type == "unsubscribe":
                await self.unsubscribe_from_conversation(user_id, conversation_id)
                await self.send_personal_message(user_id, {
                    "type": "unsubscribed",
                    "conversation_id": conversation_id
                })
            
            elif message_type == "typing":
                status = message_data.get("status", "typing")
                await self._handle_typing_indicator(user_id, conversation_id, status)
            
            elif message_type == "read_receipt":
                message_id = message_data.get("message_id")
                if message_id:
                    await self._handle_read_receipt(user_id, conversation_id, message_id)
            
            else:
                logger.warning(f"Unknown message type: {message_type}")
        
        except Exception as e:
            logger.error(f"Error handling WebSocket message from {user_id}: {e}")
            await self.send_personal_message(user_id, {
                "type": "error",
                "message": "Failed to process message"
            })
    
    async def get_online_users(self) -> List[str]:
        """Get list of currently online users."""
        return await self.redis.smembers("online_users")
    
    async def is_user_online(self, user_id: str) -> bool:
        """Check if a user is currently online."""
        return await self.redis.sismember("online_users", user_id)
    
    async def _start_redis_listener(self, user_id: str):
        """Start listening to Redis pubsub for user's conversations."""
        # This would be implemented with Redis pubsub
        # For now, we'll handle it through direct method calls
        pass
    
    async def _handle_typing_indicator(self, user_id: str, conversation_id: str, status: str):
        """Handle typing indicator from user."""
        # Get user name from Redis cache
        user_name = await self.redis.get(f"user_online:{user_id}")
        if not user_name:
            user_name = f"User {user_id}"
        
        # Broadcast typing status to other conversation participants
        typing_message = {
            "type": "typing_indicator",
            "conversation_id": conversation_id,
            "user_id": user_id,
            "user_name": user_name,
            "status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_conversation(
            conversation_id, 
            typing_message, 
            exclude_user=user_id
        )
    
    async def _handle_read_receipt(self, user_id: str, conversation_id: str, message_id: str):
        """Handle read receipt from user."""
        # Broadcast read receipt to conversation participants
        read_receipt = {
            "type": "read_receipt",
            "conversation_id": conversation_id,
            "message_id": message_id,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.broadcast_to_conversation(
            conversation_id,
            read_receipt,
            exclude_user=user_id
        )


# Global connection manager instance
connection_manager = None


def get_connection_manager(redis: RedisCache) -> ConnectionManager:
    """Get or create connection manager instance."""
    global connection_manager
    if connection_manager is None:
        connection_manager = ConnectionManager(redis)
    return connection_manager


async def websocket_endpoint(websocket: WebSocket, user_id: str, user_name: str, redis: RedisCache):
    """WebSocket endpoint handler."""
    manager = get_connection_manager(redis)
    
    try:
        await manager.connect(websocket, user_id, user_name)
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle the message
            await manager.handle_message(user_id, message_data)
    
    except WebSocketDisconnect:
        await manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        await manager.disconnect(user_id)