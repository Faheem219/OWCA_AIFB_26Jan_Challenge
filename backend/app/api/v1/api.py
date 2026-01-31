"""
Main API router for version 1 of the Multilingual Mandi Marketplace API.

This module aggregates all API routes and provides the main router
for the FastAPI application.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    products,
    chat,
    translation,
    price_discovery,
    payments,
    health,
    orders,
)

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"]
)

api_router.include_router(
    products.router,
    prefix="/products",
    tags=["products"]
)

api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

api_router.include_router(
    translation.router,
    prefix="/translation",
    tags=["translation"]
)

api_router.include_router(
    price_discovery.router,
    prefix="/price-discovery",
    tags=["price-discovery"]
)

api_router.include_router(
    payments.router,
    prefix="/payments",
    tags=["payments"]
)

api_router.include_router(
    orders.router,
    prefix="/orders",
    tags=["orders"]
)