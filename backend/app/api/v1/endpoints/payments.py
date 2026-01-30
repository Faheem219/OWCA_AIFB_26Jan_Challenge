"""
Payment processing endpoints for secure transactions with mock payment gateway.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random
import hashlib
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.dependencies import get_current_user
from app.models.user import UserProfile

router = APIRouter()


def generate_transaction_id() -> str:
    """Generate a unique transaction ID."""
    timestamp = datetime.utcnow().isoformat()
    random_part = str(random.randint(1000, 9999))
    hash_input = f"{timestamp}-{random_part}".encode()
    return f"TXN{hashlib.md5(hash_input).hexdigest()[:12].upper()}"


def generate_payment_reference() -> str:
    """Generate a payment reference number."""
    return f"PAY{random.randint(100000, 999999)}"


@router.post("/create-payment-intent")
async def create_payment_intent(
    payment_data: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Create a payment intent for a transaction (Mock Implementation).
    
    Args:
        payment_data: Payment creation data with:
            - amount: float
            - currency: str (default: INR)
            - payment_method: str (upi/card/wallet)
            - description: str
            
    Returns:
        Payment intent information
    """
    try:
        amount = payment_data.get("amount")
        if not amount or amount <= 0:
            raise HTTPException(status_code=400, detail="Invalid amount")
        
        payment_method = payment_data.get("payment_method", "upi")
        currency = payment_data.get("currency", "INR")
        description = payment_data.get("description", "Product purchase")
        
        # Generate mock payment intent
        intent_id = f"PI_{generate_transaction_id()}"
        client_secret = f"SECRET_{hashlib.md5(intent_id.encode()).hexdigest()}"
        
        # Store payment intent in database
        payment_intent = {
            "_id": intent_id,
            "user_id": str(current_user.id),
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "description": description,
            "status": "pending",
            "client_secret": client_secret,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=30)
        }
        
        await db.payment_intents.insert_one(payment_intent)
        
        return {
            "intent_id": intent_id,
            "client_secret": client_secret,
            "amount": amount,
            "currency": currency,
            "payment_method": payment_method,
            "status": "pending",
            "message": "Payment intent created successfully (Mock)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create payment intent: {str(e)}"
        )


@router.post("/confirm-payment")
async def confirm_payment(
    payment_confirmation: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Confirm and process a payment (Mock Implementation).
    
    Args:
        payment_confirmation: Payment confirmation data with:
            - intent_id: str
            - payment_details: Dict (method-specific details)
            
    Returns:
        Payment confirmation result
    """
    try:
        intent_id = payment_confirmation.get("intent_id")
        if not intent_id:
            raise HTTPException(status_code=400, detail="Payment intent ID required")
        
        # Retrieve payment intent
        intent = await db.payment_intents.find_one({"_id": intent_id})
        if not intent:
            raise HTTPException(status_code=404, detail="Payment intent not found")
        
        if intent["status"] != "pending":
            raise HTTPException(status_code=400, detail=f"Payment already {intent['status']}")
        
        # Check expiration
        if datetime.utcnow() > intent["expires_at"]:
            await db.payment_intents.update_one(
                {"_id": intent_id},
                {"$set": {"status": "expired"}}
            )
            raise HTTPException(status_code=400, detail="Payment intent expired")
        
        # Mock payment processing - 95% success rate
        payment_successful = random.random() < 0.95
        
        if payment_successful:
            transaction_id = generate_transaction_id()
            payment_reference = generate_payment_reference()
            
            # Create transaction record
            transaction = {
                "_id": transaction_id,
                "user_id": str(current_user.id),
                "intent_id": intent_id,
                "amount": intent["amount"],
                "currency": intent["currency"],
                "payment_method": intent["payment_method"],
                "payment_reference": payment_reference,
                "description": intent["description"],
                "status": "completed",
                "completed_at": datetime.utcnow(),
                "metadata": payment_confirmation.get("payment_details", {})
            }
            
            await db.transactions.insert_one(transaction)
            
            # Update payment intent
            await db.payment_intents.update_one(
                {"_id": intent_id},
                {
                    "$set": {
                        "status": "succeeded",
                        "transaction_id": transaction_id,
                        "completed_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "status": "succeeded",
                "transaction_id": transaction_id,
                "payment_reference": payment_reference,
                "amount": intent["amount"],
                "currency": intent["currency"],
                "payment_method": intent["payment_method"],
                "message": "Payment processed successfully (Mock)",
                "receipt_url": f"/api/v1/payments/receipt/{transaction_id}"
            }
        else:
            # Mock payment failure
            await db.payment_intents.update_one(
                {"_id": intent_id},
                {
                    "$set": {
                        "status": "failed",
                        "error": "Payment declined by mock gateway",
                        "failed_at": datetime.utcnow()
                    }
                }
            )
            
            raise HTTPException(
                status_code=402,
                detail="Payment declined - insufficient funds or authentication failure (Mock)"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm payment: {str(e)}"
        )


@router.get("/transactions")
async def get_transactions(
    limit: int = 20,
    offset: int = 0,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get user's transaction history.
    
    Args:
        limit: Maximum number of transactions to return
        offset: Number of transactions to skip
        
    Returns:
        List of transactions
    """
    try:
        # Query transactions
        transactions_cursor = db.transactions.find(
            {"user_id": str(current_user.id)}
        ).sort("completed_at", -1).skip(offset).limit(limit)
        
        transactions = await transactions_cursor.to_list(length=limit)
        total_count = await db.transactions.count_documents({"user_id": str(current_user.id)})
        
        # Format transactions
        formatted_transactions = []
        for txn in transactions:
            formatted_transactions.append({
                "transaction_id": txn["_id"],
                "amount": txn["amount"],
                "currency": txn["currency"],
                "payment_method": txn["payment_method"],
                "payment_reference": txn.get("payment_reference"),
                "description": txn.get("description"),
                "status": txn["status"],
                "completed_at": txn["completed_at"].isoformat() if txn.get("completed_at") else None
            })
        
        return {
            "transactions": formatted_transactions,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transactions: {str(e)}"
        )


@router.get("/transactions/{transaction_id}")
async def get_transaction_detail(
    transaction_id: str,
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get detailed information about a specific transaction.
    
    Args:
        transaction_id: Transaction identifier
        
    Returns:
        Detailed transaction information
    """
    try:
        transaction = await db.transactions.find_one({"_id": transaction_id})
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Unauthorized access to transaction")
        
        return {
            "transaction_id": transaction["_id"],
            "amount": transaction["amount"],
            "currency": transaction["currency"],
            "payment_method": transaction["payment_method"],
            "payment_reference": transaction.get("payment_reference"),
            "description": transaction.get("description"),
            "status": transaction["status"],
            "completed_at": transaction["completed_at"].isoformat() if transaction.get("completed_at") else None,
            "metadata": transaction.get("metadata", {}),
            "intent_id": transaction.get("intent_id"),
            "refund_status": transaction.get("refund_status"),
            "refunded_at": transaction["refunded_at"].isoformat() if transaction.get("refunded_at") else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transaction: {str(e)}"
        )


@router.post("/refund")
async def process_refund(
    refund_data: Dict[str, Any],
    current_user: UserProfile = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Process a refund for a transaction (Mock Implementation).
    
    Args:
        refund_data: Refund request data with:
            - transaction_id: str
            - reason: str
            - amount: Optional[float] (partial refund)
            
    Returns:
        Refund processing result
    """
    try:
        transaction_id = refund_data.get("transaction_id")
        reason = refund_data.get("reason", "Customer request")
        
        if not transaction_id:
            raise HTTPException(status_code=400, detail="Transaction ID required")
        
        # Retrieve transaction
        transaction = await db.transactions.find_one({"_id": transaction_id})
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction["user_id"] != str(current_user.id):
            raise HTTPException(status_code=403, detail="Unauthorized")
        
        if transaction["status"] != "completed":
            raise HTTPException(status_code=400, detail="Only completed transactions can be refunded")
        
        if transaction.get("refund_status") == "refunded":
            raise HTTPException(status_code=400, detail="Transaction already refunded")
        
        # Process refund amount
        refund_amount = refund_data.get("amount", transaction["amount"])
        if refund_amount > transaction["amount"]:
            raise HTTPException(status_code=400, detail="Refund amount exceeds transaction amount")
        
        # Mock refund processing - 98% success rate
        refund_successful = random.random() < 0.98
        
        if refund_successful:
            refund_id = f"RFD_{generate_transaction_id()}"
            
            # Update transaction with refund info
            await db.transactions.update_one(
                {"_id": transaction_id},
                {
                    "$set": {
                        "refund_status": "refunded" if refund_amount == transaction["amount"] else "partial_refund",
                        "refund_amount": refund_amount,
                        "refund_reason": reason,
                        "refund_id": refund_id,
                        "refunded_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "status": "success",
                "refund_id": refund_id,
                "transaction_id": transaction_id,
                "refund_amount": refund_amount,
                "currency": transaction["currency"],
                "refund_method": transaction["payment_method"],
                "estimated_arrival": "3-5 business days (Mock)",
                "message": "Refund processed successfully"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Refund processing failed - please contact support (Mock)"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process refund: {str(e)}"
        )