"""
Database connection and configuration for MongoDB.

This module handles MongoDB connection setup, database initialization,
and provides database access utilities for the application.
"""

import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global database client and database instances
mongo_client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """
    Create database connection and initialize MongoDB.
    """
    global mongo_client, database
    
    try:
        logger.info("Connecting to MongoDB...")
        
        # Create MongoDB client
        mongo_client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=10,
            minPoolSize=1,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
        )
        
        # Test the connection
        await mongo_client.admin.command('ping')
        
        # Get database instance
        database = mongo_client[settings.MONGODB_DATABASE]
        
        # Create indexes for optimal performance
        await create_indexes()
        
        logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DATABASE}")
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """
    Close database connection.
    """
    global mongo_client
    
    if mongo_client:
        logger.info("Closing MongoDB connection...")
        mongo_client.close()
        mongo_client = None
        logger.info("MongoDB connection closed")


async def get_database() -> AsyncIOMotorDatabase:
    """
    Get database instance.
    
    Returns:
        AsyncIOMotorDatabase: The database instance
        
    Raises:
        RuntimeError: If database is not connected
    """
    if database is None:
        raise RuntimeError("Database is not connected. Call connect_to_mongo() first.")
    return database


async def create_indexes() -> None:
    """
    Create database indexes for optimal query performance.
    """
    if database is None:
        logger.warning("Database not connected, skipping index creation")
        return
    
    try:
        logger.info("Creating database indexes...")
        
        # User collection indexes
        users_collection = database.users
        await users_collection.create_index("email", unique=True)
        await users_collection.create_index("phone", unique=True, sparse=True)
        await users_collection.create_index("role")
        await users_collection.create_index([("location.coordinates", "2dsphere")])
        
        # Product collection indexes
        products_collection = database.products
        await products_collection.create_index("vendor_id")
        await products_collection.create_index("category")
        await products_collection.create_index("status")
        await products_collection.create_index([("location.coordinates", "2dsphere")])
        await products_collection.create_index([
            ("name.original_text", "text"),
            ("description.original_text", "text")
        ])
        await products_collection.create_index("base_price")
        await products_collection.create_index([("created_at", -1)])
        
        # Conversation collection indexes
        conversations_collection = database.conversations
        await conversations_collection.create_index("participants")
        await conversations_collection.create_index([("last_activity", -1)])
        
        # Message collection indexes
        messages_collection = database.messages
        await messages_collection.create_index([
            ("conversation_id", 1),
            ("timestamp", -1)
        ])
        await messages_collection.create_index("sender_id")
        
        # Transaction collection indexes
        transactions_collection = database.transactions
        await transactions_collection.create_index("buyer_id")
        await transactions_collection.create_index("vendor_id")
        await transactions_collection.create_index("product_id")
        await transactions_collection.create_index([("created_at", -1)])
        await transactions_collection.create_index("payment_status")
        
        # Market price collection indexes
        market_prices_collection = database.market_prices
        await market_prices_collection.create_index([
            ("commodity", 1),
            ("market", 1),
            ("date", -1)
        ])
        await market_prices_collection.create_index([("date", -1)])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        # Don't raise here as the application can still function without indexes
        # though performance may be degraded


async def check_database_health() -> bool:
    """
    Check if database connection is healthy.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        if mongo_client is None:
            return False
        
        # Ping the database
        await mongo_client.admin.command('ping')
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Database utility functions
async def get_collection(collection_name: str):
    """
    Get a collection from the database.
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        Collection instance
    """
    db = await get_database()
    return db[collection_name]


async def create_collection_with_validation(collection_name: str, validator: dict):
    """
    Create a collection with JSON schema validation.
    
    Args:
        collection_name: Name of the collection
        validator: JSON schema validator
    """
    db = await get_database()
    
    try:
        await db.create_collection(
            collection_name,
            validator=validator
        )
        logger.info(f"Created collection '{collection_name}' with validation")
    except Exception as e:
        if "already exists" in str(e):
            logger.info(f"Collection '{collection_name}' already exists")
        else:
            logger.error(f"Error creating collection '{collection_name}': {e}")
            raise