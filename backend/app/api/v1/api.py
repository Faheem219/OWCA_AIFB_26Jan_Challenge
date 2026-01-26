"""
API v1 router configuration.
"""
from fastapi import APIRouter
from app.api.v1 import auth, health, translation, voice, price, vendor, reviews, products, negotiation, chat, webrtc, payment, transaction, market_analytics, personalized_insights

api_router = APIRouter()

# Include routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(translation.router, prefix="/translation", tags=["translation"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(price.router, prefix="/price", tags=["price-discovery"])
api_router.include_router(vendor.router, prefix="/vendor", tags=["vendor-verification"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(products.router, prefix="/products", tags=["product-catalog"])
api_router.include_router(negotiation.router, prefix="/negotiation", tags=["negotiation-assistant"])
api_router.include_router(chat.router, prefix="/chat", tags=["real-time-chat"])
api_router.include_router(webrtc.router, prefix="/webrtc", tags=["webrtc-communication"])
api_router.include_router(payment.router, prefix="/payment", tags=["payment-system"])
api_router.include_router(transaction.router, prefix="/transaction", tags=["transaction-management"])
api_router.include_router(market_analytics.router, prefix="/market-analytics", tags=["market-analytics"])
api_router.include_router(personalized_insights.router, prefix="/personalized-insights", tags=["personalized-insights"])