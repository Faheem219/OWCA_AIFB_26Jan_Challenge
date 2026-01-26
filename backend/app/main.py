"""
Main FastAPI application for Multilingual Mandi Marketplace Platform.

This module sets up the FastAPI application with all necessary middleware,
routers, and configurations for the multilingual marketplace platform.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.redis import connect_to_redis, close_redis_connection
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.services.elasticsearch_service import elasticsearch_service
from app.core.exceptions import (
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    ExternalServiceException,
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting up Multilingual Mandi Marketplace API")
    
    # Connect to databases
    await connect_to_mongo()
    await connect_to_redis()
    
    # Initialize Elasticsearch
    try:
        await elasticsearch_service.initialize()
        logger.info("Elasticsearch connection established")
    except Exception as e:
        logger.warning(f"Failed to initialize Elasticsearch: {e}")
        logger.info("Application will continue with MongoDB fallback for search")
    
    logger.info("Database connections established")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Multilingual Mandi Marketplace API")
    
    # Close database connections
    await close_mongo_connection()
    await close_redis_connection()
    
    # Close Elasticsearch connection
    try:
        await elasticsearch_service.close()
        logger.info("Elasticsearch connection closed")
    except Exception as e:
        logger.warning(f"Error closing Elasticsearch connection: {e}")
    
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="Multilingual Mandi Marketplace API",
    description="AI-powered multilingual marketplace for Indian local markets",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.get_allowed_hosts(),
)


# Custom exception handlers
@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": str(exc),
            "details": exc.details if hasattr(exc, 'details') else None,
        },
    )


@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    return JSONResponse(
        status_code=401,
        content={
            "error": "authentication_error",
            "message": str(exc),
        },
    )


@app.exception_handler(AuthorizationException)
async def authorization_exception_handler(request: Request, exc: AuthorizationException):
    return JSONResponse(
        status_code=403,
        content={
            "error": "authorization_error",
            "message": str(exc),
        },
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "not_found",
            "message": str(exc),
        },
    )


@app.exception_handler(ExternalServiceException)
async def external_service_exception_handler(request: Request, exc: ExternalServiceException):
    return JSONResponse(
        status_code=503,
        content={
            "error": "external_service_error",
            "message": str(exc),
            "service": exc.service if hasattr(exc, 'service') else None,
        },
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Serve static files (for uploaded images, etc.)
if settings.DEBUG:
    import os
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests for monitoring and debugging."""
    import time
    start_time = time.time()
    
    # Log request
    logger.info(
        "Request started",
        extra={
            "method": request.method,
            "url": str(request.url),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
    )
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "url": str(request.url),
            "status_code": response.status_code,
            "process_time": process_time,
        }
    )
    
    # Add process time header
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower(),
    )