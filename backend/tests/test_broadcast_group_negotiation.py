"""
Tests for broadcast messaging and group negotiation features.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from app.services.chat_service import ChatService
from app.models.chat import (
    BroadcastMessageRequest, GroupNegotiationCreateRequest, GroupNegotiationJoinRequest,
    GroupVoteRequest, ParticipantManagementRequest, MessageType, GroupNegotiationStatus,
    VoteType
)
from app.models.translation import LanguageCode


@pytest.fixture
def mock_db():
    """Mock database."""
    db = MagicMock()
    
    # Mock collections with proper async methods
    db.conversations = MagicMock()
    db.messages = MagicMock()
    db.users = MagicMock()
    db.group_negotiations = MagicMock()
    db.broadcast_messages = MagicMock()
    
    # Make find_one return AsyncMock
    db.group_negotiations.find_one = AsyncMock()
    db.conversations.update_one = AsyncMock()
    db.group_negotiations.update_one = AsyncMock()
    db.group_negotiations.insert_one = AsyncMock()
    db.broadcast_messages.insert_one = AsyncMock()
    
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis cache."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def mock_translation_service():
    """Mock translation service."""
    service = AsyncMock()
    return service


@pytest.fixture
def chat_service(mock_db, mock_redis, mock_translation_service):
    """Chat service with mocked dependencies."""
    return ChatService(mock_db, mock_redis, mock_translation_service)


class TestBroadcastMessaging:
    """Test broadcast messaging functionality."""
    
    @pytest.mark.asyncio
    async def test_send_broadcast_message_success(self, chat_service, mock_db):
        """Test successful broadcast message sending."""
        # Mock user data
        mock_users = [
            {"_id": ObjectId(), "full_name": "User 1"},
            {"_id": ObjectId(), "full_name": "User 2"}
        ]
        
        # Mock database responses
        mock_db.users.find.return_value.__aiter__ = AsyncMock(return_value=iter(mock_users))
        mock_db.broadcast_messages.insert_one.return_value = AsyncMock(inserted_id=ObjectId())
        
        # Mock conversation creation
        chat_service.create_conversation = AsyncMock()
        chat_service.create_conversation.return_value = MagicMock(id="conv_123")
        
        # Mock message sending
        chat_service.send_message = AsyncMock()
        
        # Create broadcast request
        request = BroadcastMessageRequest(
            recipient_ids=[str(user["_id"]) for user in mock_users],
            text="Test broadcast message",
            message_type=MessageType.TEXT
        )
        
        # Send broadcast
        result = await chat_service.send_broadcast_message(
            request=request,
            sender_id="sender_123",
            sender_name="Sender",
            sender_language=LanguageCode.ENGLISH
        )
        
        # Verify result
        assert result.total_recipients == 2
        assert result.delivered_count >= 0
        assert isinstance(result.conversation_ids, list)
    
    @pytest.mark.asyncio
    async def test_broadcast_message_partial_failure(self, chat_service, mock_db):
        """Test broadcast message with some failures."""
        # Mock user data
        mock_users = [
            {"_id": ObjectId(), "full_name": "User 1"},
            {"_id": ObjectId(), "full_name": "User 2"}
        ]
        
        # Mock database responses
        mock_db.users.find.return_value.__aiter__ = AsyncMock(return_value=iter(mock_users))
        mock_db.broadcast_messages.insert_one.return_value = AsyncMock(inserted_id=ObjectId())
        
        # Mock conversation creation - first succeeds, second fails
        chat_service.create_conversation = AsyncMock()
        chat_service.create_conversation.side_effect = [
            MagicMock(id="conv_123"),
            Exception("Failed to create conversation")
        ]
        
        # Mock message sending
        chat_service.send_message = AsyncMock()
        
        # Create broadcast request
        request = BroadcastMessageRequest(
            recipient_ids=[str(user["_id"]) for user in mock_users],
            text="Test broadcast message"
        )
        
        # Send broadcast
        result = await chat_service.send_broadcast_message(
            request=request,
            sender_id="sender_123",
            sender_name="Sender",
            sender_language=LanguageCode.ENGLISH
        )
        
        # Verify partial success
        assert result.total_recipients == 2
        assert result.failed_count > 0


class TestGroupNegotiation:
    """Test group negotiation functionality."""
    
    @pytest.mark.asyncio
    async def test_create_group_negotiation_room(self, chat_service, mock_db):
        """Test creating a group negotiation room."""
        # Mock conversation creation
        chat_service.create_conversation = AsyncMock()
        chat_service.create_conversation.return_value = MagicMock(id="conv_123")
        
        # Mock database insert
        mock_db.group_negotiations.insert_one.return_value = AsyncMock(inserted_id=ObjectId())
        
        # Create request
        request = GroupNegotiationCreateRequest(
            product_id="product_123",
            seller_id="seller_123",
            minimum_participants=2,
            maximum_participants=5,
            initial_message="Let's negotiate together!"
        )
        
        # Create room
        result = await chat_service.create_group_negotiation_room(
            request=request,
            creator_id="creator_123",
            creator_name="Creator",
            creator_language=LanguageCode.ENGLISH
        )
        
        # Verify result
        assert result.product_id == "product_123"
        assert result.seller_id == "seller_123"
        assert result.minimum_participants == 2
        assert result.maximum_participants == 5
        assert result.status == GroupNegotiationStatus.FORMING
        assert "creator_123" in result.buyer_ids
    
    @pytest.mark.asyncio
    async def test_join_group_negotiation(self, chat_service, mock_db):
        """Test joining a group negotiation room."""
        # Mock room data
        room_data = {
            "_id": ObjectId(),
            "conversation_id": "conv_123",
            "product_id": "product_123",
            "seller_id": "seller_123",
            "buyer_ids": ["creator_123"],
            "moderator_id": "creator_123",
            "status": GroupNegotiationStatus.FORMING.value,
            "minimum_participants": 2,
            "maximum_participants": 5,
            "negotiation_rules": {},
            "group_decisions": [],
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        # Mock database responses
        mock_db.group_negotiations.find_one.return_value = room_data
        mock_db.conversations.update_one.return_value = AsyncMock()
        mock_db.group_negotiations.update_one.return_value = AsyncMock()
        
        # Mock message sending
        chat_service.send_message = AsyncMock()
        
        # Create join request
        request = GroupNegotiationJoinRequest(
            room_id=str(room_data["_id"]),
            message="I want to join!"
        )
        
        # Join room
        result = await chat_service.join_group_negotiation(
            request=request,
            user_id="user_456",
            user_name="New User",
            user_language=LanguageCode.ENGLISH
        )
        
        # Verify result
        assert result.current_participants >= 2
        assert result.status == GroupNegotiationStatus.ACTIVE  # Should be active with 2+ participants
    
    @pytest.mark.asyncio
    async def test_create_group_decision(self, chat_service, mock_db):
        """Test creating a group decision."""
        # Mock room data
        room_data = {
            "_id": ObjectId(),
            "conversation_id": "conv_123",
            "product_id": "product_123",
            "seller_id": "seller_123",
            "buyer_ids": ["buyer_1", "buyer_2"],
            "moderator_id": "moderator_123",
            "status": GroupNegotiationStatus.ACTIVE.value,
            "group_decisions": [],
            "created_at": datetime.utcnow()
        }
        
        # Mock database responses
        mock_db.group_negotiations.find_one.return_value = room_data
        mock_db.group_negotiations.update_one.return_value = AsyncMock()
        
        # Mock message sending
        chat_service.send_message = AsyncMock()
        
        # Create decision
        decision_id = await chat_service.create_group_decision(
            room_id=str(room_data["_id"]),
            decision_type=VoteType.ACCEPT_OFFER,
            description="Accept the seller's offer of $100 per unit",
            creator_id="moderator_123",
            deadline_hours=24
        )
        
        # Verify decision created
        assert decision_id is not None
        assert isinstance(decision_id, str)
    
    @pytest.mark.asyncio
    async def test_vote_on_decision(self, chat_service, mock_db):
        """Test voting on a group decision."""
        # Mock decision data
        decision_data = {
            "decision_id": "decision_123",
            "decision_type": VoteType.ACCEPT_OFFER.value,
            "description": "Accept offer",
            "votes": {},
            "required_votes": 2,
            "current_votes": 0,
            "deadline": datetime.utcnow() + timedelta(hours=24),
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        
        # Mock room data
        room_data = {
            "_id": ObjectId(),
            "conversation_id": "conv_123",
            "buyer_ids": ["buyer_1", "buyer_2"],
            "group_decisions": [decision_data],
            "created_at": datetime.utcnow()
        }
        
        # Mock database responses
        mock_db.group_negotiations.find_one.return_value = room_data
        mock_db.group_negotiations.update_one.return_value = AsyncMock()
        
        # Mock message sending
        chat_service.send_message = AsyncMock()
        
        # Create vote request
        request = GroupVoteRequest(
            room_id=str(room_data["_id"]),
            decision_id="decision_123",
            vote=True,
            comment="I agree with this offer"
        )
        
        # Vote on decision
        is_complete = await chat_service.vote_on_decision(
            request=request,
            voter_id="buyer_1",
            voter_name="Buyer 1"
        )
        
        # Verify vote recorded (decision not complete yet with only 1 vote)
        assert is_complete is False
    
    @pytest.mark.asyncio
    async def test_manage_participant_remove(self, chat_service, mock_db):
        """Test removing a participant from group negotiation."""
        # Mock room data
        room_data = {
            "_id": ObjectId(),
            "conversation_id": "conv_123",
            "buyer_ids": ["buyer_1", "buyer_2", "buyer_3"],
            "moderator_id": "moderator_123",
            "created_at": datetime.utcnow()
        }
        
        # Mock database responses
        mock_db.group_negotiations.find_one.return_value = room_data
        mock_db.conversations.update_one.return_value = AsyncMock()
        mock_db.group_negotiations.update_one.return_value = AsyncMock()
        
        # Mock message sending
        chat_service.send_message = AsyncMock()
        
        # Create management request
        request = ParticipantManagementRequest(
            room_id=str(room_data["_id"]),
            action="remove",
            user_id="buyer_2",
            reason="Inactive participant"
        )
        
        # Remove participant
        success = await chat_service.manage_participant(
            request=request,
            manager_id="moderator_123",
            manager_name="Moderator"
        )
        
        # Verify success
        assert success is True


class TestGroupNegotiationEdgeCases:
    """Test edge cases for group negotiation."""
    
    @pytest.mark.asyncio
    async def test_join_full_room(self, chat_service, mock_db):
        """Test joining a room that's already full."""
        # Mock room data - already at maximum capacity
        room_data = {
            "_id": ObjectId(),
            "buyer_ids": ["buyer_1", "buyer_2"],  # At max capacity
            "status": GroupNegotiationStatus.ACTIVE.value,
            "minimum_participants": 2,
            "maximum_participants": 2,  # Full
            "created_at": datetime.utcnow()
        }
        
        mock_db.group_negotiations.find_one.return_value = room_data
        
        request = GroupNegotiationJoinRequest(
            room_id=str(room_data["_id"]),
            message="I want to join!"
        )
        
        # Should raise ValueError for full room
        with pytest.raises(ValueError, match="Room is full"):
            await chat_service.join_group_negotiation(
                request=request,
                user_id="user_456",
                user_name="New User",
                user_language=LanguageCode.ENGLISH
            )
    
    @pytest.mark.asyncio
    async def test_vote_after_deadline(self, chat_service, mock_db):
        """Test voting after deadline has passed."""
        # Mock decision data with past deadline
        decision_data = {
            "decision_id": "decision_123",
            "decision_type": VoteType.ACCEPT_OFFER.value,
            "description": "Accept offer",
            "votes": {},
            "required_votes": 2,
            "current_votes": 0,
            "deadline": datetime.utcnow() - timedelta(hours=1),  # Past deadline
            "status": "pending",
            "created_at": datetime.utcnow() - timedelta(hours=25)
        }
        
        room_data = {
            "_id": ObjectId(),
            "buyer_ids": ["buyer_1", "buyer_2"],
            "group_decisions": [decision_data],
            "created_at": datetime.utcnow()
        }
        
        mock_db.group_negotiations.find_one.return_value = room_data
        
        request = GroupVoteRequest(
            room_id=str(room_data["_id"]),
            decision_id="decision_123",
            vote=True
        )
        
        # Should raise ValueError for expired deadline
        with pytest.raises(ValueError, match="Voting deadline has passed"):
            await chat_service.vote_on_decision(
                request=request,
                voter_id="buyer_1",
                voter_name="Buyer 1"
            )