"""
MongoDB database connection and utilities.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB connection manager."""
    
    def __init__(self):
        self.client: AsyncIOMotorClient = None
        self.database: AsyncIOMotorDatabase = None
    
    async def connect_to_mongo(self):
        """Create database connection."""
        logger.info("Connecting to MongoDB...")
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.database = self.client[settings.MONGODB_DATABASE]
        
        # Test the connection
        try:
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close_mongo_connection(self):
        """Close database connection."""
        logger.info("Closing MongoDB connection...")
        if self.client:
            self.client.close()
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        return self.database


# Global database instance
mongodb = MongoDB()


async def get_database() -> AsyncIOMotorDatabase:
    """Dependency to get database instance."""
    return mongodb.get_database()


# Collection names
class Collections:
    """Database collection names."""
    USERS = "users"
    VENDORS = "vendors"
    PRODUCTS = "products"
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"
    TRANSACTIONS = "transactions"
    MARKET_DATA = "market_data"
    NEGOTIATIONS = "negotiations"
    TRANSLATIONS_CACHE = "translations_cache"
    TRANSLATION_STATS = "translation_stats"
    AUDIO_FILES = "audio_files"
    VOICE_STATS = "voice_stats"
    REVIEWS = "reviews"
    NOTIFICATIONS = "notifications"
    CULTURAL_INTERACTIONS = "cultural_interactions"