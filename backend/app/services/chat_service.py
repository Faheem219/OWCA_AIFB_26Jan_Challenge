"""
Chat service for real-time communication with translation support.
"""
import logging
from datetime import datetime, timedelta, timedelta
from typing import Optional, List, Dict, Any
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.mongodb import Collections
from app.db.redis import RedisCache
from app.models.chat import (
    Conversation, Message, Participant, TypingIndicator,
    ConversationCreateRequest, MessageCreateRequest, BroadcastMessageRequest,
    ConversationResponse, MessageResponse, ConversationListResponse,
    ConversationType, MessageType, MessageStatus, ParticipantRole,
    Translation, MessageMetadata, TypingStatus, WebSocketMessage, ChatStats,
    GroupNegotiationCreateRequest, GroupNegotiationJoinRequest, GroupVoteRequest,
    GroupNegotiationResponse, BroadcastResponse, ParticipantManagementRequest,
    GroupNegotiationRoom, GroupNegotiationStatus, BroadcastMessage, BroadcastRecipient,
    GroupDecision, VoteType
)
from app.models.translation import TranslationRequest, LanguageCode
from app.services.translation_service import TranslationService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations and messages."""
    
    def __init__(self, db: AsyncIOMotorDatabase, redis: RedisCache, translation_service: TranslationService):
        """Initialize chat service."""
        self.db = db
        self.redis = redis
        self.translation_service = translation_service
        self.conversations_collection = db[Collections.CONVERSATIONS]
        self.messages_collection = db[Collections.MESSAGES]
        self.group_negotiations_collection = db["group_negotiations"]
        self.broadcast_messages_collection = db["broadcast_messages"]
        
        # Redis keys for real-time features
        self.typing_key_prefix = "typing:"
        self.online_users_key = "online_users"
        self.conversation_subscribers_prefix = "conv_subscribers:"
    
    async def create_conversation(
        self, 
        request: ConversationCreateRequest, 
        creator_id: str,
        creator_name: str,
        creator_language: LanguageCode
    ) -> ConversationResponse:
        """Create a new conversation."""
        # Validate participants
        if creator_id not in request.participant_ids:
            request.participant_ids.append(creator_id)
        
        if len(request.participant_ids) < 2:
            raise ValueError("Conversation must have at least 2 participants")
        
        # Check if direct conversation already exists
        if request.type == ConversationType.DIRECT and len(request.participant_ids) == 2:
            existing = await self._find_existing_direct_conversation(request.participant_ids)
            if existing:
                return await self._conversation_to_response(existing)
        
        # Get participant details from user collection
        participants = []
        user_cursor = self.db[Collections.USERS].find(
            {"_id": {"$in": [ObjectId(uid) for uid in request.participant_ids]}}
        )
        
        async for user in user_cursor:
            role = ParticipantRole.OWNER if str(user["_id"]) == creator_id else ParticipantRole.MEMBER
            participant = Participant(
                user_id=str(user["_id"]),
                user_name=user["full_name"],
                role=role,
                preferred_language=LanguageCode(user.get("preferred_language", "en"))
            )
            participants.append(participant)
        
        # Create conversation
        conversation = Conversation(
            type=request.type,
            title=request.title,
            description=request.description,
            participants=participants,
            created_by=creator_id,
            product_id=request.product_id
        )
        
        # Insert into database
        result = await self.conversations_collection.insert_one(conversation.dict(by_alias=True))
        conversation.id = result.inserted_id
        
        # Send initial message if provided
        if request.initial_message:
            await self.send_message(
                MessageCreateRequest(
                    conversation_id=str(conversation.id),
                    text=request.initial_message
                ),
                creator_id,
                creator_name,
                creator_language
            )
        
        logger.info(f"Created conversation {conversation.id} with {len(participants)} participants")
        return await self._conversation_to_response(conversation)
    
    async def send_message(
        self,
        request: MessageCreateRequest,
        sender_id: str,
        sender_name: str,
        sender_language: LanguageCode
    ) -> MessageResponse:
        """Send a message in a conversation."""
        # Get conversation
        conversation = await self.conversations_collection.find_one(
            {"_id": ObjectId(request.conversation_id)}
        )
        if not conversation:
            raise ValueError("Conversation not found")
        
        # Verify sender is participant
        participant_ids = [p["user_id"] for p in conversation["participants"]]
        if sender_id not in participant_ids:
            raise ValueError("User is not a participant in this conversation")
        
        # Create message metadata
        metadata = None
        if request.reply_to or request.attachments or request.offer_details:
            metadata = MessageMetadata(
                reply_to=request.reply_to,
                attachments=request.attachments,
                offer_details=request.offer_details
            )
        
        # Create message
        message = Message(
            conversation_id=request.conversation_id,
            sender_id=sender_id,
            sender_name=sender_name,
            message_type=request.message_type,
            original_text=request.text,
            original_language=sender_language,
            metadata=metadata
        )
        
        # Translate message for all participants
        await self._translate_message_for_participants(message, conversation["participants"])
        
        # Insert message into database
        result = await self.messages_collection.insert_one(message.dict(by_alias=True))
        message.id = result.inserted_id
        
        # Update conversation last message info
        await self.conversations_collection.update_one(
            {"_id": ObjectId(request.conversation_id)},
            {
                "$set": {
                    "last_message_at": message.timestamp,
                    "last_message_preview": request.text[:100],
                    "updated_at": datetime.utcnow()
                },
                "$inc": {"message_count": 1}
            }
        )
        
        # Broadcast message to conversation subscribers via WebSocket
        await self._broadcast_message_to_subscribers(request.conversation_id, message)
        
        logger.info(f"Message sent in conversation {request.conversation_id} by {sender_id}")
        return await self._message_to_response(message, sender_language)
    
    async def get_conversations(
        self, 
        user_id: str, 
        page: int = 1, 
        size: int = 20
    ) -> List[ConversationListResponse]:
        """Get user's conversations."""
        skip = (page - 1) * size
        
        cursor = self.conversations_collection.find(
            {
                "participants.user_id": user_id,
                "is_active": True
            }
        ).sort("last_message_at", -1).skip(skip).limit(size)
        
        conversations = []
        async for conv_doc in cursor:
            # Calculate unread count
            unread_count = await self._get_unread_count(str(conv_doc["_id"]), user_id)
            
            # Get participant info (excluding current user)
            participants = [
                {"user_id": p["user_id"], "user_name": p["user_name"]}
                for p in conv_doc["participants"]
                if p["user_id"] != user_id
            ]
            
            conversations.append(ConversationListResponse(
                id=str(conv_doc["_id"]),
                type=conv_doc["type"],
                title=conv_doc.get("title"),
                participants=participants,
                last_message_preview=conv_doc.get("last_message_preview"),
                last_message_at=conv_doc.get("last_message_at"),
                unread_count=unread_count,
                is_active=conv_doc["is_active"]
            ))
        
        return conversations
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        user_id: str,
        user_language: LanguageCode,
        page: int = 1,
        size: int = 50
    ) -> List[MessageResponse]:
        """Get messages from a conversation."""
        # Verify user is participant
        conversation = await self.conversations_collection.find_one(
            {
                "_id": ObjectId(conversation_id),
                "participants.user_id": user_id
            }
        )
        if not conversation:
            raise ValueError("Conversation not found or user not authorized")
        
        skip = (page - 1) * size
        
        cursor = self.messages_collection.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", -1).skip(skip).limit(size)
        
        messages = []
        async for msg_doc in cursor:
            message = Message(**msg_doc)
            response = await self._message_to_response(message, user_language)
            messages.append(response)
        
        # Mark messages as read
        await self._mark_messages_as_read(conversation_id, user_id)
        
        return list(reversed(messages))  # Return in chronological order
    
    async def send_broadcast_message(
        self,
        request: BroadcastMessageRequest,
        sender_id: str,
        sender_name: str,
        sender_language: LanguageCode
    ) -> BroadcastResponse:
        """Send broadcast message to multiple recipients with tracking."""
        # Create broadcast message record
        recipients = []
        conversation_ids = []
        
        # Get recipient details
        user_cursor = self.db[Collections.USERS].find(
            {"_id": {"$in": [ObjectId(uid) for uid in request.recipient_ids]}}
        )
        
        recipient_users = {}
        async for user in user_cursor:
            recipient_users[str(user["_id"])] = user["full_name"]
        
        # Create broadcast message tracking
        broadcast_message = BroadcastMessage(
            sender_id=sender_id,
            sender_name=sender_name,
            message_text=request.text,
            message_type=request.message_type,
            total_recipients=len(request.recipient_ids)
        )
        
        # Send to each recipient
        for recipient_id in request.recipient_ids:
            if recipient_id == sender_id:
                continue  # Don't send to self
                
            recipient_name = recipient_users.get(recipient_id, f"User {recipient_id}")
            
            try:
                # Create or get direct conversation
                conv_request = ConversationCreateRequest(
                    type=ConversationType.DIRECT,
                    participant_ids=[sender_id, recipient_id],
                    title=request.title
                )
                
                conversation = await self.create_conversation(
                    conv_request, sender_id, sender_name, sender_language
                )
                
                # Send message in conversation
                msg_request = MessageCreateRequest(
                    conversation_id=conversation.id,
                    text=request.text,
                    message_type=request.message_type,
                    attachments=request.attachments
                )
                
                await self.send_message(
                    msg_request, sender_id, sender_name, sender_language
                )
                
                # Track successful delivery
                recipient = BroadcastRecipient(
                    user_id=recipient_id,
                    user_name=recipient_name,
                    conversation_id=conversation.id,
                    delivered_at=datetime.utcnow(),
                    status="delivered"
                )
                recipients.append(recipient)
                conversation_ids.append(conversation.id)
                broadcast_message.delivered_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send broadcast to {recipient_id}: {e}")
                # Track failed delivery
                recipient = BroadcastRecipient(
                    user_id=recipient_id,
                    user_name=recipient_name,
                    status="failed"
                )
                recipients.append(recipient)
                broadcast_message.failed_count += 1
        
        # Update broadcast message with recipients
        broadcast_message.recipients = recipients
        
        # Save broadcast message record
        result = await self.broadcast_messages_collection.insert_one(
            broadcast_message.dict(by_alias=True)
        )
        broadcast_message.id = result.inserted_id
        
        logger.info(f"Broadcast message sent to {broadcast_message.delivered_count}/{broadcast_message.total_recipients} recipients")
        
        return BroadcastResponse(
            id=str(broadcast_message.id),
            total_recipients=broadcast_message.total_recipients,
            delivered_count=broadcast_message.delivered_count,
            failed_count=broadcast_message.failed_count,
            conversation_ids=conversation_ids,
            created_at=broadcast_message.created_at
        )
    
    async def set_typing_status(
        self,
        conversation_id: str,
        user_id: str,
        user_name: str,
        status: TypingStatus
    ):
        """Set typing status for a user in a conversation."""
        typing_key = f"{self.typing_key_prefix}{conversation_id}:{user_id}"
        
        if status == TypingStatus.TYPING:
            # Set typing status with expiration
            await self.redis.setex(typing_key, 10, user_name)  # Expires in 10 seconds
        else:
            # Remove typing status
            await self.redis.delete(typing_key)
        
        # Broadcast typing status to conversation subscribers
        typing_indicator = TypingIndicator(
            conversation_id=conversation_id,
            user_id=user_id,
            user_name=user_name,
            status=status
        )
        
        await self._broadcast_typing_to_subscribers(conversation_id, typing_indicator)
    
    async def get_typing_users(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get users currently typing in a conversation."""
        pattern = f"{self.typing_key_prefix}{conversation_id}:*"
        keys = await self.redis.keys(pattern)
        
        typing_users = []
        for key in keys:
            user_id = key.split(":")[-1]
            user_name = await self.redis.get(key)
            if user_name:
                typing_users.append({"user_id": user_id, "user_name": user_name})
        
        return typing_users
    
    async def mark_message_as_read(
        self,
        message_id: str,
        user_id: str
    ):
        """Mark a specific message as read by a user."""
        await self.messages_collection.update_one(
            {"_id": ObjectId(message_id)},
            {
                "$set": {
                    f"read_by.{user_id}": datetime.utcnow()
                }
            }
        )
    
    async def get_chat_stats(self, user_id: str) -> ChatStats:
        """Get chat statistics for a user."""
        # Count user's conversations
        total_conversations = await self.conversations_collection.count_documents(
            {"participants.user_id": user_id, "is_active": True}
        )
        
        # Count user's messages
        total_messages = await self.messages_collection.count_documents(
            {"sender_id": user_id}
        )
        
        # Count active conversations (with messages in last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_conversations = await self.conversations_collection.count_documents(
            {
                "participants.user_id": user_id,
                "last_message_at": {"$gte": week_ago},
                "is_active": True
            }
        )
        
        # Count messages today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        messages_today = await self.messages_collection.count_documents(
            {
                "sender_id": user_id,
                "timestamp": {"$gte": today_start}
            }
        )
        
        return ChatStats(
            total_conversations=total_conversations,
            total_messages=total_messages,
            active_conversations=active_conversations,
            messages_today=messages_today
        )
    
    async def _translate_message_for_participants(
        self, 
        message: Message, 
        participants: List[Dict[str, Any]]
    ):
        """Translate message for all participants who need it."""
        unique_languages = set()
        for participant in participants:
            lang = participant.get("preferred_language", "en")
            if lang != message.original_language.value:
                unique_languages.add(lang)
        
        # Translate to each required language
        for target_lang in unique_languages:
            try:
                translation_request = TranslationRequest(
                    text=message.original_text,
                    source_language=message.original_language,
                    target_language=LanguageCode(target_lang),
                    context="chat_message"
                )
                
                result = await self.translation_service.translate_text(translation_request)
                
                message.translations[target_lang] = Translation(
                    language=LanguageCode(target_lang),
                    text=result.translated_text,
                    confidence_score=result.confidence_score,
                    provider=result.provider
                )
                
            except Exception as e:
                logger.error(f"Translation failed for {target_lang}: {e}")
                # Store original text as fallback
                message.translations[target_lang] = Translation(
                    language=LanguageCode(target_lang),
                    text=message.original_text,
                    confidence_score=0.0,
                    provider="fallback"
                )
    
    async def _find_existing_direct_conversation(
        self, 
        participant_ids: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Find existing direct conversation between two users."""
        return await self.conversations_collection.find_one({
            "type": ConversationType.DIRECT,
            "participants.user_id": {"$all": participant_ids},
            "participants": {"$size": len(participant_ids)},
            "is_active": True
        })
    
    async def _get_unread_count(self, conversation_id: str, user_id: str) -> int:
        """Get unread message count for a user in a conversation."""
        # Get user's last read message timestamp
        conversation = await self.conversations_collection.find_one(
            {"_id": ObjectId(conversation_id)}
        )
        
        if not conversation:
            return 0
        
        # Find user's participant record
        user_participant = None
        for p in conversation["participants"]:
            if p["user_id"] == user_id:
                user_participant = p
                break
        
        if not user_participant:
            return 0
        
        last_read_at = user_participant.get("last_read_at")
        if not last_read_at:
            # Count all messages if never read
            return await self.messages_collection.count_documents({
                "conversation_id": conversation_id,
                "sender_id": {"$ne": user_id}  # Don't count own messages
            })
        
        # Count messages after last read timestamp
        return await self.messages_collection.count_documents({
            "conversation_id": conversation_id,
            "sender_id": {"$ne": user_id},
            "timestamp": {"$gt": last_read_at}
        })
    
    async def _mark_messages_as_read(self, conversation_id: str, user_id: str):
        """Mark all messages in conversation as read by user."""
        now = datetime.utcnow()
        
        # Update user's last read timestamp in conversation
        await self.conversations_collection.update_one(
            {
                "_id": ObjectId(conversation_id),
                "participants.user_id": user_id
            },
            {
                "$set": {
                    "participants.$.last_read_at": now
                }
            }
        )
    
    async def _conversation_to_response(self, conversation: Conversation) -> ConversationResponse:
        """Convert conversation model to response."""
        return ConversationResponse(
            id=str(conversation.id),
            type=conversation.type,
            title=conversation.title,
            description=conversation.description,
            participants=conversation.participants,
            settings=conversation.settings,
            created_at=conversation.created_at,
            message_count=conversation.message_count,
            product_id=conversation.product_id,
            negotiation_id=conversation.negotiation_id
        )
    
    async def _message_to_response(
        self, 
        message: Message, 
        user_language: LanguageCode
    ) -> MessageResponse:
        """Convert message model to response with appropriate translation."""
        # Get translated text for user's language
        translated_text = None
        if user_language.value in message.translations:
            translated_text = message.translations[user_language.value].text
        elif user_language != message.original_language:
            translated_text = message.original_text  # Fallback to original
        
        return MessageResponse(
            id=str(message.id),
            conversation_id=message.conversation_id,
            sender_id=message.sender_id,
            sender_name=message.sender_name,
            message_type=message.message_type,
            original_text=message.original_text,
            original_language=message.original_language,
            translated_text=translated_text,
            status=message.status,
            timestamp=message.timestamp,
            metadata=message.metadata
        )
    
    async def _broadcast_message_to_subscribers(
        self, 
        conversation_id: str, 
        message: Message
    ):
        """Broadcast new message to WebSocket subscribers."""
        # This will be implemented with WebSocket manager
        websocket_message = WebSocketMessage(
            type="new_message",
            conversation_id=conversation_id,
            data={
                "message_id": str(message.id),
                "sender_id": message.sender_id,
                "sender_name": message.sender_name,
                "text": message.original_text,
                "timestamp": message.timestamp.isoformat(),
                "message_type": message.message_type.value
            }
        )
        
        # Store in Redis for WebSocket manager to pick up
        await self.redis.publish(
            f"chat:{conversation_id}",
            websocket_message.json()
        )
    
    async def _broadcast_typing_to_subscribers(
        self, 
        conversation_id: str, 
        typing_indicator: TypingIndicator
    ):
        """Broadcast typing indicator to WebSocket subscribers."""
        websocket_message = WebSocketMessage(
            type="typing_indicator",
            conversation_id=conversation_id,
            data={
                "user_id": typing_indicator.user_id,
                "user_name": typing_indicator.user_name,
                "status": typing_indicator.status.value
            }
        )
        
        await self.redis.publish(
            f"chat:{conversation_id}",
            websocket_message.json()
        )
    async def create_group_negotiation_room(
        self,
        request: GroupNegotiationCreateRequest,
        creator_id: str,
        creator_name: str,
        creator_language: LanguageCode
    ) -> GroupNegotiationResponse:
        """Create a group negotiation room."""
        # Create conversation for the group negotiation
        conv_request = ConversationCreateRequest(
            type=ConversationType.GROUP_NEGOTIATION,
            participant_ids=[creator_id, request.seller_id],
            title=f"Group Negotiation - Product {request.product_id}",
            description="Group negotiation room for bulk purchase",
            product_id=request.product_id,
            initial_message=request.initial_message
        )
        
        conversation = await self.create_conversation(
            conv_request, creator_id, creator_name, creator_language
        )
        
        # Create group negotiation room
        expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)
        
        room = GroupNegotiationRoom(
            conversation_id=conversation.id,
            product_id=request.product_id,
            seller_id=request.seller_id,
            buyer_ids=[creator_id],
            moderator_id=creator_id,
            minimum_participants=request.minimum_participants,
            maximum_participants=request.maximum_participants,
            negotiation_rules=request.negotiation_rules,
            expires_at=expires_at
        )
        
        # Save to database
        result = await self.group_negotiations_collection.insert_one(room.dict(by_alias=True))
        room.id = result.inserted_id
        
        logger.info(f"Created group negotiation room {room.id} for product {request.product_id}")
        
        return GroupNegotiationResponse(
            id=str(room.id),
            conversation_id=conversation.id,
            product_id=room.product_id,
            seller_id=room.seller_id,
            buyer_ids=room.buyer_ids,
            status=room.status,
            minimum_participants=room.minimum_participants,
            maximum_participants=room.maximum_participants,
            current_participants=len(room.buyer_ids),
            current_offer=room.current_offer,
            active_decisions=room.group_decisions,
            created_at=room.created_at,
            expires_at=room.expires_at
        )
    
    async def join_group_negotiation(
        self,
        request: GroupNegotiationJoinRequest,
        user_id: str,
        user_name: str,
        user_language: LanguageCode
    ) -> GroupNegotiationResponse:
        """Join a group negotiation room."""
        # Get room
        room_doc = await self.group_negotiations_collection.find_one(
            {"_id": ObjectId(request.room_id)}
        )
        if not room_doc:
            raise ValueError("Group negotiation room not found")
        
        room = GroupNegotiationRoom(**room_doc)
        
        # Check if room is still accepting participants
        if room.status not in [GroupNegotiationStatus.FORMING, GroupNegotiationStatus.ACTIVE]:
            raise ValueError("Room is not accepting new participants")
        
        if len(room.buyer_ids) >= room.maximum_participants:
            raise ValueError("Room is full")
        
        if user_id in room.buyer_ids:
            raise ValueError("User already in room")
        
        # Add user to room
        room.buyer_ids.append(user_id)
        
        # Add user to conversation
        await self.conversations_collection.update_one(
            {"_id": ObjectId(room.conversation_id)},
            {
                "$push": {
                    "participants": {
                        "user_id": user_id,
                        "user_name": user_name,
                        "role": ParticipantRole.BUYER.value,
                        "preferred_language": user_language.value,
                        "joined_at": datetime.utcnow(),
                        "is_active": True,
                        "muted": False
                    }
                }
            }
        )
        
        # Update room status if minimum participants reached
        if len(room.buyer_ids) >= room.minimum_participants and room.status == GroupNegotiationStatus.FORMING:
            room.status = GroupNegotiationStatus.ACTIVE
        
        # Update room in database
        await self.group_negotiations_collection.update_one(
            {"_id": ObjectId(request.room_id)},
            {
                "$set": {
                    "buyer_ids": room.buyer_ids,
                    "status": room.status.value,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Send join message if provided
        if request.message:
            msg_request = MessageCreateRequest(
                conversation_id=room.conversation_id,
                text=request.message
            )
            await self.send_message(
                msg_request, user_id, user_name, user_language
            )
        
        # Notify other participants
        join_message = f"{user_name} joined the group negotiation"
        system_msg = MessageCreateRequest(
            conversation_id=room.conversation_id,
            text=join_message,
            message_type=MessageType.SYSTEM
        )
        await self.send_message(
            system_msg, "system", "System", LanguageCode.EN
        )
        
        logger.info(f"User {user_id} joined group negotiation room {request.room_id}")
        
        return GroupNegotiationResponse(
            id=str(room.id),
            conversation_id=room.conversation_id,
            product_id=room.product_id,
            seller_id=room.seller_id,
            buyer_ids=room.buyer_ids,
            status=room.status,
            minimum_participants=room.minimum_participants,
            maximum_participants=room.maximum_participants,
            current_participants=len(room.buyer_ids),
            current_offer=room.current_offer,
            active_decisions=room.group_decisions,
            created_at=room.created_at,
            expires_at=room.expires_at
        )
    
    async def create_group_decision(
        self,
        room_id: str,
        decision_type: VoteType,
        description: str,
        creator_id: str,
        deadline_hours: int = 24
    ) -> str:
        """Create a group decision for voting."""
        # Get room
        room_doc = await self.group_negotiations_collection.find_one(
            {"_id": ObjectId(room_id)}
        )
        if not room_doc:
            raise ValueError("Group negotiation room not found")
        
        room = GroupNegotiationRoom(**room_doc)
        
        # Check if user can create decisions (moderator or seller)
        if creator_id not in [room.moderator_id, room.seller_id]:
            raise ValueError("Only moderator or seller can create decisions")
        
        # Create decision
        deadline = datetime.utcnow() + timedelta(hours=deadline_hours)
        required_votes = len(room.buyer_ids)  # All buyers must vote
        
        decision = GroupDecision(
            decision_type=decision_type,
            description=description,
            required_votes=required_votes,
            deadline=deadline
        )
        
        # Add to room
        room.group_decisions.append(decision)
        
        # Update room in database
        await self.group_negotiations_collection.update_one(
            {"_id": ObjectId(room_id)},
            {
                "$push": {"group_decisions": decision.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Notify participants about new decision
        decision_message = f"New group decision: {description}. Please vote by {deadline.strftime('%Y-%m-%d %H:%M UTC')}"
        system_msg = MessageCreateRequest(
            conversation_id=room.conversation_id,
            text=decision_message,
            message_type=MessageType.SYSTEM
        )
        await self.send_message(
            system_msg, "system", "System", LanguageCode.EN
        )
        
        logger.info(f"Created group decision {decision.decision_id} in room {room_id}")
        return decision.decision_id
    
    async def vote_on_decision(
        self,
        request: GroupVoteRequest,
        voter_id: str,
        voter_name: str
    ) -> bool:
        """Vote on a group decision."""
        # Get room
        room_doc = await self.group_negotiations_collection.find_one(
            {"_id": ObjectId(request.room_id)}
        )
        if not room_doc:
            raise ValueError("Group negotiation room not found")
        
        room = GroupNegotiationRoom(**room_doc)
        
        # Check if user is participant
        if voter_id not in room.buyer_ids:
            raise ValueError("Only participants can vote")
        
        # Find decision
        decision = None
        decision_index = None
        for i, d in enumerate(room.group_decisions):
            if d.decision_id == request.decision_id:
                decision = GroupDecision(**d)
                decision_index = i
                break
        
        if not decision:
            raise ValueError("Decision not found")
        
        # Check if decision is still active
        if decision.status != "pending":
            raise ValueError("Decision is no longer active")
        
        if datetime.utcnow() > decision.deadline:
            raise ValueError("Voting deadline has passed")
        
        # Check if user already voted
        if voter_id in decision.votes:
            raise ValueError("User has already voted")
        
        # Record vote
        decision.votes[voter_id] = request.vote
        decision.current_votes += 1
        
        # Check if decision is complete
        if decision.current_votes >= decision.required_votes:
            # Count votes
            yes_votes = sum(1 for vote in decision.votes.values() if vote)
            no_votes = decision.current_votes - yes_votes
            
            if yes_votes > no_votes:
                decision.status = "approved"
            else:
                decision.status = "rejected"
            
            decision.completed_at = datetime.utcnow()
        
        # Update room in database
        await self.group_negotiations_collection.update_one(
            {"_id": ObjectId(request.room_id)},
            {
                "$set": {
                    f"group_decisions.{decision_index}": decision.dict(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Notify about vote
        vote_text = "yes" if request.vote else "no"
        vote_message = f"{voter_name} voted {vote_text} on: {decision.description}"
        if request.comment:
            vote_message += f" - Comment: {request.comment}"
        
        system_msg = MessageCreateRequest(
            conversation_id=room.conversation_id,
            text=vote_message,
            message_type=MessageType.SYSTEM
        )
        await self.send_message(
            system_msg, "system", "System", LanguageCode.EN
        )
        
        # If decision is complete, notify about result
        if decision.status in ["approved", "rejected"]:
            result_message = f"Decision '{decision.description}' has been {decision.status}"
            system_msg = MessageCreateRequest(
                conversation_id=room.conversation_id,
                text=result_message,
                message_type=MessageType.SYSTEM
            )
            await self.send_message(
                system_msg, "system", "System", LanguageCode.EN
            )
        
        logger.info(f"User {voter_id} voted {vote_text} on decision {request.decision_id}")
        return decision.status != "pending"
    
    async def manage_participant(
        self,
        request: ParticipantManagementRequest,
        manager_id: str,
        manager_name: str
    ) -> bool:
        """Manage participants in group negotiation."""
        # Get room
        room_doc = await self.group_negotiations_collection.find_one(
            {"_id": ObjectId(request.room_id)}
        )
        if not room_doc:
            raise ValueError("Group negotiation room not found")
        
        room = GroupNegotiationRoom(**room_doc)
        
        # Check if user can manage participants (moderator only)
        if manager_id != room.moderator_id:
            raise ValueError("Only moderator can manage participants")
        
        success = False
        message = ""
        
        if request.action == "remove":
            if request.user_id in room.buyer_ids:
                room.buyer_ids.remove(request.user_id)
                
                # Remove from conversation
                await self.conversations_collection.update_one(
                    {"_id": ObjectId(room.conversation_id)},
                    {"$pull": {"participants": {"user_id": request.user_id}}}
                )
                
                message = f"User {request.user_id} was removed from the group negotiation"
                if request.reason:
                    message += f" - Reason: {request.reason}"
                success = True
        
        elif request.action == "add":
            if request.user_id not in room.buyer_ids and len(room.buyer_ids) < room.maximum_participants:
                # Get user details
                user_doc = await self.db[Collections.USERS].find_one(
                    {"_id": ObjectId(request.user_id)}
                )
                if user_doc:
                    room.buyer_ids.append(request.user_id)
                    
                    # Add to conversation
                    await self.conversations_collection.update_one(
                        {"_id": ObjectId(room.conversation_id)},
                        {
                            "$push": {
                                "participants": {
                                    "user_id": request.user_id,
                                    "user_name": user_doc["full_name"],
                                    "role": ParticipantRole.BUYER.value,
                                    "preferred_language": user_doc.get("preferred_language", "en"),
                                    "joined_at": datetime.utcnow(),
                                    "is_active": True,
                                    "muted": False
                                }
                            }
                        }
                    )
                    
                    message = f"User {user_doc['full_name']} was added to the group negotiation"
                    success = True
        
        if success:
            # Update room in database
            await self.group_negotiations_collection.update_one(
                {"_id": ObjectId(request.room_id)},
                {
                    "$set": {
                        "buyer_ids": room.buyer_ids,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Send notification message
            system_msg = MessageCreateRequest(
                conversation_id=room.conversation_id,
                text=message,
                message_type=MessageType.SYSTEM
            )
            await self.send_message(
                system_msg, "system", "System", LanguageCode.EN
            )
        
        logger.info(f"Participant management action '{request.action}' by {manager_id}: {success}")
        return success
    
    async def get_group_negotiation_rooms(
        self,
        user_id: str,
        status_filter: Optional[GroupNegotiationStatus] = None
    ) -> List[GroupNegotiationResponse]:
        """Get group negotiation rooms for a user."""
        query = {
            "$or": [
                {"buyer_ids": user_id},
                {"seller_id": user_id},
                {"moderator_id": user_id}
            ]
        }
        
        if status_filter:
            query["status"] = status_filter.value
        
        cursor = self.group_negotiations_collection.find(query).sort("created_at", -1)
        
        rooms = []
        async for room_doc in cursor:
            room = GroupNegotiationRoom(**room_doc)
            rooms.append(GroupNegotiationResponse(
                id=str(room.id),
                conversation_id=room.conversation_id,
                product_id=room.product_id,
                seller_id=room.seller_id,
                buyer_ids=room.buyer_ids,
                status=room.status,
                minimum_participants=room.minimum_participants,
                maximum_participants=room.maximum_participants,
                current_participants=len(room.buyer_ids),
                current_offer=room.current_offer,
                active_decisions=[d for d in room.group_decisions if d.status == "pending"],
                created_at=room.created_at,
                expires_at=room.expires_at
            ))
        
        return rooms