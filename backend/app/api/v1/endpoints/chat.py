"""
Chat and messaging endpoints for real-time communication.
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import Dict, Any, List, Annotated
from datetime import datetime, timedelta
import uuid

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.user import UserProfile
from app.services.translation_service import translation_service
from app.services.ai_service import ai_service

router = APIRouter()


# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
    
    async def broadcast(self, message: Dict[str, Any], conversation_id: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str):
    """WebSocket endpoint for real-time chat."""
    await manager.connect(websocket, conversation_id)
    try:
        while True:
            data = await websocket.receive_json()
            message = {
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "sender_id": data.get("sender_id"),
                "content": data.get("content"),
                "type": data.get("type", "text"),
                "timestamp": datetime.utcnow().isoformat(),
                "translated": False
            }
            
            # Auto-translate if requested
            if data.get("translate") and data.get("target_language"):
                try:
                    result = await translation_service.translate_text(
                        text=data.get("content"),
                        source_language=data.get("source_language", "en"),
                        target_language=data.get("target_language")
                    )
                    message["translated_content"] = result.translated_text
                    message["translated"] = True
                except Exception:
                    pass
            
            await manager.broadcast(message, conversation_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, conversation_id)


@router.get("/conversations")
async def get_conversations(
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)]
) -> Dict[str, Any]:
    """Get user's chat conversations."""
    try:
        user_id = str(current_user.id)
        
        conversations = await db.conversations.find({
            "$or": [
                {"participant_1": user_id},
                {"participant_2": user_id}
            ]
        }).sort("updated_at", -1).to_list(length=50)
        
        formatted_conversations = []
        for conv in conversations:
            last_message = await db.messages.find_one(
                {"conversation_id": str(conv["_id"])},
                sort=[("created_at", -1)]
            )
            
            other_user_id = conv["participant_2"] if conv["participant_1"] == user_id else conv["participant_1"]
            other_user = await db.users.find_one({"_id": other_user_id})
            
            formatted_conversations.append({
                "id": str(conv["_id"]),
                "other_participant": {
                    "id": other_user_id,
                    "name": other_user.get("profile", {}).get("full_name", "Unknown") if other_user else "Unknown"
                },
                "product_id": conv.get("product_id"),
                "last_message": {
                    "content": last_message.get("content", "") if last_message else "",
                    "timestamp": last_message.get("created_at").isoformat() if last_message and last_message.get("created_at") else None
                },
                "unread_count": conv.get("unread_count", {}).get(user_id, 0),
                "updated_at": conv.get("updated_at").isoformat() if conv.get("updated_at") else None
            })
        
        return {"conversations": formatted_conversations, "total_count": len(formatted_conversations)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch conversations: {str(e)}")


@router.post("/conversations")
async def create_conversation(
    conversation_data: Dict[str, Any],
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)]
) -> Dict[str, Any]:
    """Create a new chat conversation."""
    try:
        user_id = str(current_user.id)
        other_participant_id = conversation_data.get("participant_id")
        product_id = conversation_data.get("product_id")
        
        if not other_participant_id:
            raise HTTPException(status_code=400, detail="Participant ID is required")
        
        existing = await db.conversations.find_one({
            "$or": [
                {"participant_1": user_id, "participant_2": other_participant_id},
                {"participant_1": other_participant_id, "participant_2": user_id}
            ],
            "product_id": product_id
        })
        
        if existing:
            return {"id": str(existing["_id"]), "message": "Conversation already exists", "existing": True}
        
        conversation_id = str(uuid.uuid4())
        conversation = {
            "_id": conversation_id,
            "participant_1": user_id,
            "participant_2": other_participant_id,
            "product_id": product_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "unread_count": {user_id: 0, other_participant_id: 0},
            "status": "active"
        }
        
        await db.conversations.insert_one(conversation)
        return {"id": conversation_id, "participant_id": other_participant_id, "product_id": product_id, "message": "Conversation created", "existing": False}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")


@router.get("/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)],
    limit: int = 50,
    skip: int = 0
) -> Dict[str, Any]:
    """Get messages from a conversation."""
    try:
        conversation = await db.conversations.find_one({"_id": conversation_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        user_id = str(current_user.id)
        if user_id not in [conversation.get("participant_1"), conversation.get("participant_2")]:
            raise HTTPException(status_code=403, detail="Not a participant")
        
        messages = await db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        
        await db.conversations.update_one({"_id": conversation_id}, {"$set": {f"unread_count.{user_id}": 0}})
        
        formatted_messages = []
        for msg in reversed(messages):
            formatted_messages.append({
                "id": str(msg["_id"]),
                "sender_id": msg.get("sender_id"),
                "content": msg.get("content"),
                "translated_content": msg.get("translated_content"),
                "type": msg.get("type", "text"),
                "created_at": msg.get("created_at").isoformat() if msg.get("created_at") else None
            })
        
        total = await db.messages.count_documents({"conversation_id": conversation_id})
        return {"messages": formatted_messages, "total_count": total, "has_more": skip + limit < total}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch messages: {str(e)}")


@router.post("/conversations/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    message_data: Dict[str, Any],
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)]
) -> Dict[str, Any]:
    """Send a message in a conversation."""
    try:
        conversation = await db.conversations.find_one({"_id": conversation_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        user_id = str(current_user.id)
        if user_id not in [conversation.get("participant_1"), conversation.get("participant_2")]:
            raise HTTPException(status_code=403, detail="Not a participant")
        
        content = message_data.get("content")
        if not content:
            raise HTTPException(status_code=400, detail="Message content required")
        
        message_id = str(uuid.uuid4())
        message = {
            "_id": message_id,
            "conversation_id": conversation_id,
            "sender_id": user_id,
            "content": content,
            "type": message_data.get("type", "text"),
            "created_at": datetime.utcnow()
        }
        
        translate_to = message_data.get("translate_to")
        if translate_to:
            try:
                result = await translation_service.translate_text(
                    text=content,
                    source_language=message_data.get("source_language", "en"),
                    target_language=translate_to
                )
                message["translated_content"] = result.translated_text
            except Exception:
                pass
        
        await db.messages.insert_one(message)
        
        other_participant = conversation.get("participant_2") if conversation.get("participant_1") == user_id else conversation.get("participant_1")
        await db.conversations.update_one(
            {"_id": conversation_id},
            {"$set": {"updated_at": datetime.utcnow()}, "$inc": {f"unread_count.{other_participant}": 1}}
        )
        
        return {
            "id": message_id,
            "content": content,
            "translated_content": message.get("translated_content"),
            "type": message.get("type"),
            "sender_id": user_id,
            "created_at": message["created_at"].isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.post("/conversations/{conversation_id}/offers")
async def make_offer(
    conversation_id: str,
    offer_data: Dict[str, Any],
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)]
) -> Dict[str, Any]:
    """Make a price offer in a conversation."""
    try:
        conversation = await db.conversations.find_one({"_id": conversation_id})
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        user_id = str(current_user.id)
        if user_id not in [conversation.get("participant_1"), conversation.get("participant_2")]:
            raise HTTPException(status_code=403, detail="Not a participant")
        
        price = offer_data.get("price")
        quantity = offer_data.get("quantity", 1)
        product_id = offer_data.get("product_id")
        
        if not product_id or not price:
            raise HTTPException(status_code=400, detail="Product ID and price required")
        
        offer_id = str(uuid.uuid4())
        offer = {
            "_id": offer_id,
            "conversation_id": conversation_id,
            "product_id": product_id,
            "buyer_id": user_id,
            "seller_id": conversation.get("participant_2") if conversation.get("participant_1") == user_id else conversation.get("participant_1"),
            "price": price,
            "quantity": quantity,
            "total_amount": price * quantity,
            "status": "pending",
            "message": offer_data.get("message"),
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        }
        
        await db.offers.insert_one(offer)
        
        message = {
            "_id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "sender_id": user_id,
            "content": f"Made an offer: ₹{price} x {quantity} = ₹{price * quantity}",
            "type": "offer",
            "offer_id": offer_id,
            "created_at": datetime.utcnow()
        }
        await db.messages.insert_one(message)
        
        return {"id": offer_id, "product_id": product_id, "price": price, "quantity": quantity, "total_amount": price * quantity, "status": "pending"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to make offer: {str(e)}")


@router.put("/offers/{offer_id}")
async def respond_to_offer(
    offer_id: str,
    response_data: Dict[str, Any],
    current_user: Annotated[UserProfile, Depends(get_current_user)],
    db: Annotated[Any, Depends(get_database)]
) -> Dict[str, Any]:
    """Accept, reject, or counter an offer."""
    try:
        offer = await db.offers.find_one({"_id": offer_id})
        if not offer:
            raise HTTPException(status_code=404, detail="Offer not found")
        
        user_id = str(current_user.id)
        if user_id != offer.get("seller_id"):
            raise HTTPException(status_code=403, detail="Only seller can respond")
        
        action = response_data.get("action")
        if action not in ["accept", "reject", "counter"]:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        if action == "accept":
            await db.offers.update_one({"_id": offer_id}, {"$set": {"status": "accepted", "responded_at": datetime.utcnow()}})
            status_message = "Offer accepted"
        elif action == "reject":
            await db.offers.update_one({"_id": offer_id}, {"$set": {"status": "rejected", "responded_at": datetime.utcnow()}})
            status_message = "Offer rejected"
        else:
            counter_price = response_data.get("counter_price")
            if not counter_price:
                raise HTTPException(status_code=400, detail="Counter price required")
            await db.offers.update_one({"_id": offer_id}, {"$set": {"status": "countered", "counter_price": counter_price, "responded_at": datetime.utcnow()}})
            status_message = f"Counter offer: ₹{counter_price}"
        
        message = {
            "_id": str(uuid.uuid4()),
            "conversation_id": offer["conversation_id"],
            "sender_id": user_id,
            "content": status_message,
            "type": "offer_response",
            "offer_id": offer_id,
            "created_at": datetime.utcnow()
        }
        await db.messages.insert_one(message)
        
        return {"id": offer_id, "status": action + "ed" if action != "counter" else "countered", "message": status_message}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to respond to offer: {str(e)}")


@router.post("/conversations/{conversation_id}/ai-suggestion")
async def get_negotiation_suggestion(
    conversation_id: str,
    context_data: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get AI-powered negotiation suggestions."""
    try:
        suggestion = await ai_service.generate_negotiation_suggestion(context_data)
        return suggestion
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get suggestion: {str(e)}")
