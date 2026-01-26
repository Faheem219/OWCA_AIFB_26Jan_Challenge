"""
Chat and conversation models for real-time communication.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from bson import ObjectId

from app.models.common import PyObjectId, MessageType
from app.models.translation import LanguageCode


class ConversationType(str, Enum):
    """Types of conversations."""
    DIRECT = "direct"  # One-on-one conversation
    GROUP = "group"    # Group negotiation
    BROADCAST = "broadcast"  # Broadcast message
    GROUP_NEGOTIATION = "group_negotiation"  # Group negotiation room


class MessageStatus(str, Enum):
    """Message delivery status."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class TypingStatus(str, Enum):
    """Typing indicator status."""
    TYPING = "typing"
    STOPPED = "stopped"


class ParticipantRole(str, Enum):
    """Participant roles in conversations."""
    OWNER = "owner"      # Conversation creator
    MEMBER = "member"    # Regular participant
    ADMIN = "admin"      # Group admin (for group chats)
    MODERATOR = "moderator"  # Group negotiation moderator
    BUYER = "buyer"      # Buyer in group negotiation
    SELLER = "seller"    # Seller in group negotiation


class MessageMetadata(BaseModel):
    """Additional metadata for messages."""
    reply_to: Optional[str] = None  # Message ID being replied to
    forwarded_from: Optional[str] = None  # Original message ID if forwarded
    edited: bool = False
    edited_at: Optional[datetime] = None
    attachments: List[str] = []  # File URLs
    location: Optional[Dict[str, float]] = None  # lat, lng
    offer_details: Optional[Dict[str, Any]] = None  # For offer messages


class Translation(BaseModel):
    """Translation of a message."""
    language: LanguageCode
    text: str
    confidence_score: float
    provider: str
    translated_at: datetime = Field(default_factory=datetime.utcnow)


class Message(BaseModel):
    """Chat message model."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    conversation_id: str
    sender_id: str
    sender_name: str  # Cached for performance
    message_type: MessageType = MessageType.TEXT
    original_text: str
    original_language: LanguageCode
    translations: Dict[str, Translation] = {}  # language_code -> Translation
    status: MessageStatus = MessageStatus.SENT
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[MessageMetadata] = None
    
    # Read receipts - user_id -> timestamp
    read_by: Dict[str, datetime] = {}
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class Participant(BaseModel):
    """Conversation participant."""
    user_id: str
    user_name: str  # Cached for performance
    role: ParticipantRole = ParticipantRole.MEMBER
    preferred_language: LanguageCode
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_read_message_id: Optional[str] = None
    last_read_at: Optional[datetime] = None
    is_active: bool = True  # For group conversations
    muted: bool = False


class ConversationSettings(BaseModel):
    """Conversation settings."""
    auto_translate: bool = True
    allow_voice_messages: bool = True
    allow_file_sharing: bool = True
    typing_indicators: bool = True
    read_receipts: bool = True
    message_retention_days: int = 365  # How long to keep messages


class Conversation(BaseModel):
    """Conversation model."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    type: ConversationType = ConversationType.DIRECT
    title: Optional[str] = None  # For group conversations
    description: Optional[str] = None
    participants: List[Participant] = []
    settings: ConversationSettings = ConversationSettings()
    created_by: str  # User ID who created the conversation
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None
    last_message_preview: Optional[str] = None  # For conversation list
    message_count: int = 0
    is_active: bool = True
    
    # For business context
    product_id: Optional[str] = None  # If conversation is about a specific product
    negotiation_id: Optional[str] = None  # If this is a negotiation conversation
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class TypingIndicator(BaseModel):
    """Typing indicator model."""
    conversation_id: str
    user_id: str
    user_name: str
    status: TypingStatus
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageCreateRequest(BaseModel):
    """Request to create a new message."""
    conversation_id: str
    message_type: MessageType = MessageType.TEXT
    text: str
    reply_to: Optional[str] = None
    attachments: List[str] = []
    offer_details: Optional[Dict[str, Any]] = None


class ConversationCreateRequest(BaseModel):
    """Request to create a new conversation."""
    type: ConversationType = ConversationType.DIRECT
    participant_ids: List[str]
    title: Optional[str] = None
    description: Optional[str] = None
    product_id: Optional[str] = None
    initial_message: Optional[str] = None


class ConversationListResponse(BaseModel):
    """Response for conversation list."""
    id: str
    type: ConversationType
    title: Optional[str] = None
    participants: List[Dict[str, str]]  # Simplified participant info
    last_message_preview: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int = 0
    is_active: bool = True


class MessageResponse(BaseModel):
    """Response model for messages."""
    id: str
    conversation_id: str
    sender_id: str
    sender_name: str
    message_type: MessageType
    original_text: str
    original_language: LanguageCode
    translated_text: Optional[str] = None  # Translation for requesting user's language
    status: MessageStatus
    timestamp: datetime
    metadata: Optional[MessageMetadata] = None
    is_read: bool = False


class ConversationResponse(BaseModel):
    """Response model for conversation details."""
    id: str
    type: ConversationType
    title: Optional[str] = None
    description: Optional[str] = None
    participants: List[Participant]
    settings: ConversationSettings
    created_at: datetime
    message_count: int
    product_id: Optional[str] = None
    negotiation_id: Optional[str] = None


class GroupNegotiationStatus(str, Enum):
    """Status of group negotiation."""
    FORMING = "forming"      # Gathering participants
    ACTIVE = "active"        # Negotiation in progress
    VOTING = "voting"        # Participants voting on decision
    AGREED = "agreed"        # Agreement reached
    REJECTED = "rejected"    # Offer rejected
    EXPIRED = "expired"      # Negotiation expired
    CANCELLED = "cancelled"  # Negotiation cancelled


class VoteType(str, Enum):
    """Types of votes in group negotiation."""
    ACCEPT_OFFER = "accept_offer"
    REJECT_OFFER = "reject_offer"
    COUNTER_OFFER = "counter_offer"
    EXTEND_DEADLINE = "extend_deadline"
    LEAVE_GROUP = "leave_group"


class GroupDecision(BaseModel):
    """Group decision tracking."""
    decision_id: str = Field(default_factory=lambda: str(ObjectId()))
    decision_type: VoteType
    description: str
    votes: Dict[str, bool] = {}  # user_id -> vote (True/False)
    required_votes: int
    current_votes: int = 0
    deadline: datetime
    status: str = "pending"  # pending, approved, rejected, expired
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class GroupNegotiationRoom(BaseModel):
    """Group negotiation room model."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    conversation_id: str  # Associated conversation
    product_id: str
    seller_id: str
    buyer_ids: List[str] = []
    moderator_id: Optional[str] = None
    status: GroupNegotiationStatus = GroupNegotiationStatus.FORMING
    minimum_participants: int = 2
    maximum_participants: int = 10
    current_offer: Optional[Dict[str, Any]] = None
    group_decisions: List[GroupDecision] = []
    negotiation_rules: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class BroadcastRecipient(BaseModel):
    """Broadcast message recipient tracking."""
    user_id: str
    user_name: str
    conversation_id: Optional[str] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    status: str = "pending"  # pending, delivered, read, failed


class BroadcastMessage(BaseModel):
    """Broadcast message tracking."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    sender_id: str
    sender_name: str
    message_text: str
    message_type: MessageType = MessageType.TEXT
    recipients: List[BroadcastRecipient] = []
    total_recipients: int = 0
    delivered_count: int = 0
    read_count: int = 0
    failed_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class WebSocketMessage(BaseModel):
    """WebSocket message format."""
    type: str  # "message", "typing", "read_receipt", "user_joined", "user_left"
    conversation_id: str
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ChatStats(BaseModel):
    """Chat statistics."""
    total_conversations: int = 0
    total_messages: int = 0
    active_conversations: int = 0
    messages_today: int = 0
    average_response_time_minutes: float = 0.0
    translation_usage: Dict[str, int] = {}  # language_pair -> count
    most_active_users: List[Dict[str, Any]] = []


class BroadcastMessageRequest(BaseModel):
    """Request to send broadcast message."""
    recipient_ids: List[str]
    message_type: MessageType = MessageType.TEXT
    text: str
    title: Optional[str] = None
    attachments: List[str] = []


class GroupNegotiationCreateRequest(BaseModel):
    """Request to create group negotiation room."""
    product_id: str
    seller_id: str
    minimum_participants: int = 2
    maximum_participants: int = 10
    initial_message: Optional[str] = None
    negotiation_rules: Dict[str, Any] = {}
    expires_in_hours: int = 24


class GroupNegotiationJoinRequest(BaseModel):
    """Request to join group negotiation."""
    room_id: str
    message: Optional[str] = None


class GroupVoteRequest(BaseModel):
    """Request to vote in group negotiation."""
    room_id: str
    decision_id: str
    vote: bool  # True for yes, False for no
    comment: Optional[str] = None


class GroupNegotiationResponse(BaseModel):
    """Response for group negotiation room."""
    id: str
    conversation_id: str
    product_id: str
    seller_id: str
    buyer_ids: List[str]
    status: GroupNegotiationStatus
    minimum_participants: int
    maximum_participants: int
    current_participants: int
    current_offer: Optional[Dict[str, Any]] = None
    active_decisions: List[GroupDecision] = []
    created_at: datetime
    expires_at: Optional[datetime] = None


class BroadcastResponse(BaseModel):
    """Response for broadcast message."""
    id: str
    total_recipients: int
    delivered_count: int
    failed_count: int
    conversation_ids: List[str] = []
    created_at: datetime


class ParticipantManagementRequest(BaseModel):
    """Request for participant management."""
    room_id: str
    action: str  # "add", "remove", "promote", "demote"
    user_id: str
    reason: Optional[str] = None