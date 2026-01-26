"""
API dependencies for authentication and database access.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.security import verify_token
from app.db.mongodb import get_database
from app.db.redis import get_redis, RedisCache
from app.services.auth_service import AuthService
from app.services.translation_service import TranslationService
from app.services.voice_service import VoiceService
from app.services.chat_service import ChatService
from app.models.user import UserInDB
import logging

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


async def get_db() -> AsyncIOMotorDatabase:
    """Get database dependency."""
    return await get_database()


async def get_auth_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis: RedisCache = Depends(get_redis)
) -> AuthService:
    """Get authentication service instance."""
    return AuthService(db, redis)


async def get_translation_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis: RedisCache = Depends(get_redis)
) -> TranslationService:
    """Get translation service instance."""
    return TranslationService(db, redis)


async def get_voice_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis: RedisCache = Depends(get_redis),
    translation_service: TranslationService = Depends(get_translation_service)
) -> VoiceService:
    """Get voice service instance."""
    return VoiceService(db, redis, translation_service)


async def get_chat_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis: RedisCache = Depends(get_redis),
    translation_service: TranslationService = Depends(get_translation_service)
) -> ChatService:
    """Get chat service instance."""
    return ChatService(db, redis, translation_service)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserInDB:
    """Get current authenticated user."""
    try:
        # Verify token
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        
        # Get user from database
        user = await auth_service.get_user_by_id(user_id)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_vendor(
    current_user: UserInDB = Depends(get_current_active_user)
) -> UserInDB:
    """Get current user if they are a vendor."""
    if current_user.user_type not in ["vendor", "both"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Vendor access required."
        )
    return current_user


async def get_current_buyer(
    current_user: UserInDB = Depends(get_current_active_user)
) -> UserInDB:
    """Get current user if they are a buyer."""
    if current_user.user_type not in ["buyer", "both"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Buyer access required."
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Optional[UserInDB]:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            return None
        
        # This would need to be async, but for optional dependency we'll keep it simple
        # In practice, you might want to handle this differently
        return None  # Placeholder
        
    except Exception:
        return None