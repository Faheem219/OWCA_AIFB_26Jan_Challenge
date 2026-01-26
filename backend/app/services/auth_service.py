"""
Authentication service for user management and JWT tokens.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    create_refresh_token,
    verify_refresh_token
)
from app.models.user import User, UserCreate, UserInDB, Token, UserResponse
from app.db.mongodb import Collections
from app.db.redis import RedisCache
import uuid
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""
    
    def __init__(self, db: AsyncIOMotorDatabase, redis: RedisCache):
        self.db = db
        self.redis = redis
        self.users_collection = db[Collections.USERS]
    
    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """Create a new user."""
        # Check if user already exists
        existing_user = await self.users_collection.find_one({
            "$or": [
                {"email": user_data.email},
                {"phone": user_data.phone}
            ]
        })
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or phone already exists"
            )
        
        # Hash password
        hashed_password = get_password_hash(user_data.password)
        
        # Create user document
        user_dict = user_data.dict(exclude={"password"})
        user_dict.update({
            "hashed_password": hashed_password,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        })
        
        # Insert user
        result = await self.users_collection.insert_one(user_dict)
        
        # Retrieve created user
        created_user = await self.users_collection.find_one({"_id": result.inserted_id})
        
        # Convert to response model
        user_response = UserResponse(
            id=str(created_user["_id"]),
            email=created_user["email"],
            phone=created_user["phone"],
            full_name=created_user["full_name"],
            preferred_language=created_user["preferred_language"],
            user_type=created_user["user_type"],
            is_active=created_user["is_active"],
            vendor_profile=created_user.get("vendor_profile"),
            buyer_profile=created_user.get("buyer_profile"),
            created_at=created_user["created_at"],
            last_active=created_user.get("last_active")
        )
        
        logger.info(f"Created new user: {user_response.email}")
        return user_response
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with email and password."""
        user = await self.users_collection.find_one({"email": email})
        
        if not user:
            return None
        
        if not verify_password(password, user["hashed_password"]):
            return None
        
        # Update last active
        await self.users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_active": datetime.utcnow()}}
        )
        
        return UserInDB(**user)
    
    async def login(self, email: str, password: str) -> Token:
        """Login user and return JWT tokens."""
        user = await self.authenticate_user(email, password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        # Create tokens
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Store session in Redis
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": str(user.id),
            "email": user.email,
            "user_type": user.user_type,
            "preferred_language": user.preferred_language
        }
        await self.redis.set_session(session_id, session_data)
        
        logger.info(f"User logged in: {user.email}")
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=1800  # 30 minutes
        )
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        payload = verify_refresh_token(refresh_token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Get user from database
        user = await self.get_user_by_id(user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Create new access token
        access_token_expires = timedelta(minutes=30)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep the same refresh token
            token_type="bearer",
            expires_in=1800
        )
    
    async def logout(self, session_id: str) -> bool:
        """Logout user and invalidate session."""
        return await self.redis.delete_session(session_id)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID."""
        try:
            from bson import ObjectId
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if user:
                return UserInDB(**user)
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email."""
        user = await self.users_collection.find_one({"email": email})
        if user:
            return UserInDB(**user)
        return None
    
    async def update_user_profile(self, user_id: str, update_data: dict) -> Optional[UserResponse]:
        """Update user profile."""
        try:
            from bson import ObjectId
            
            # Add updated timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            # Update user
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                return None
            
            # Get updated user
            updated_user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            
            return UserResponse(
                id=str(updated_user["_id"]),
                email=updated_user["email"],
                phone=updated_user["phone"],
                full_name=updated_user["full_name"],
                preferred_language=updated_user["preferred_language"],
                user_type=updated_user["user_type"],
                is_active=updated_user["is_active"],
                vendor_profile=updated_user.get("vendor_profile"),
                buyer_profile=updated_user.get("buyer_profile"),
                created_at=updated_user["created_at"],
                last_active=updated_user.get("last_active")
            )
            
        except Exception as e:
            logger.error(f"Error updating user profile {user_id}: {e}")
            return None
    
    async def verify_user_credentials(self, user_id: str, credentials: dict) -> bool:
        """Verify user credentials for vendor profile."""
        # This would integrate with government verification APIs
        # For now, we'll implement basic validation
        
        required_fields = ["type", "number", "issuing_authority"]
        if not all(field in credentials for field in required_fields):
            return False
        
        # TODO: Implement actual government API verification
        # For now, mark as verified if all required fields are present
        return True
    
    async def get_session_data(self, session_id: str) -> Optional[dict]:
        """Get session data from Redis."""
        return await self.redis.get_session(session_id)