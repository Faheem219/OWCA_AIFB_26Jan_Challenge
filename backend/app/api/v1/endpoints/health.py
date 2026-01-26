"""
Health check endpoints for monitoring and load balancer health checks.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.core.database import check_database_health
from app.core.redis import check_redis_health
from app.core.config import settings

router = APIRouter()


@router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    
    Returns:
        Health status information
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "service": "multilingual-mandi-marketplace-api"
    }


@router.get("/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    Detailed health check including database and cache status.
    
    Returns:
        Detailed health status information
    """
    # Check database health
    db_healthy = await check_database_health()
    
    # Check Redis health
    redis_healthy = await check_redis_health()
    
    # Overall health status
    overall_healthy = db_healthy and redis_healthy
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "service": "multilingual-mandi-marketplace-api",
        "components": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "type": "mongodb"
            },
            "cache": {
                "status": "healthy" if redis_healthy else "unhealthy",
                "type": "redis"
            }
        },
        "features": {
            "voice_messages": settings.ENABLE_VOICE_MESSAGES,
            "ai_moderation": settings.ENABLE_AI_MODERATION,
            "price_prediction": settings.ENABLE_PRICE_PREDICTION,
            "offline_mode": settings.ENABLE_OFFLINE_MODE
        }
    }


@router.get("/ready")
async def readiness_check() -> Dict[str, str]:
    """
    Kubernetes readiness probe endpoint.
    
    Returns:
        Readiness status
    """
    # Check if all critical services are ready
    db_healthy = await check_database_health()
    redis_healthy = await check_redis_health()
    
    if db_healthy and redis_healthy:
        return {"status": "ready"}
    else:
        return {"status": "not_ready"}


@router.get("/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    Returns:
        Liveness status
    """
    return {"status": "alive"}