"""
Health check API endpoints.
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.db.mongodb import get_database
from app.db.redis import get_redis, RedisCache
from app.models.common import HealthCheck, APIResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=APIResponse)
async def health_check(
    db: AsyncIOMotorDatabase = Depends(get_database),
    redis: RedisCache = Depends(get_redis)
):
    """Health check endpoint."""
    services = {}
    
    # Check MongoDB connection
    try:
        await db.command('ping')
        services["mongodb"] = "healthy"
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        services["mongodb"] = "unhealthy"
    
    # Check Redis connection
    try:
        if redis.redis_client:
            await redis.redis_client.ping()
            services["redis"] = "healthy"
        else:
            services["redis"] = "disabled"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services["redis"] = "unhealthy"
    
    # Overall status
    overall_status = "healthy" if (services["mongodb"] == "healthy" and 
                                  services["redis"] in ["healthy", "disabled"]) else "unhealthy"
    
    health_data = HealthCheck(
        status=overall_status,
        version=settings.VERSION,
        services=services
    )
    
    return APIResponse(
        success=overall_status == "healthy",
        message=f"System is {overall_status}",
        data=health_data.dict()
    )


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return {"message": "pong"}


@router.get("/version")
async def version():
    """Get application version."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "api_version": settings.API_V1_STR
    }