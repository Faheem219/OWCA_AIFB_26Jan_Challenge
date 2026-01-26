"""
Main FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn

from app.core.config import settings
from app.db.mongodb import mongodb
from app.db.redis import redis_cache
from app.api.v1.api import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting up Multilingual Mandi API...")
    
    # Connect to databases
    await mongodb.connect_to_mongo()
    
    # Try to connect to Redis, but continue if it fails
    try:
        await redis_cache.connect_to_redis()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed, continuing without caching: {str(e)}")
        redis_cache.redis_client = None
    
    logger.info("Database connections established")
    
    # Start scheduler service
    from app.services.scheduler_service import scheduler_service
    await scheduler_service.start()
    logger.info("Scheduler service started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multilingual Mandi API...")
    
    # Stop scheduler service
    await scheduler_service.stop()
    logger.info("Scheduler service stopped")
    
    # Close database connections
    await mongodb.close_mongo_connection()
    await redis_cache.close_redis_connection()
    
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A real-time linguistic bridge platform for Indian vendors and buyers",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.DEBUG else ["localhost", "127.0.0.1"]
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Multilingual Mandi API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )