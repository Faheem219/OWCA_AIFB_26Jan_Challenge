"""
Negotiation API endpoints with cultural guidance.
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.deps import get_database, get_current_user
from app.models.user import User
from app.models.negotiation import (
    NegotiationSession, NegotiationCreate, NegotiationUpdate,
    CulturalGuidance, PriceRecommendation, CounterOfferSuggestion,
    MarketContext, SeasonalFactor, MarketCondition
)
from app.services.negotiation_service import NegotiationAssistantService

router = APIRouter()


@router.post("/initiate", response_model=NegotiationSession)
async def initiate_negotiation(
    negotiation_data: NegotiationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Initiate a new negotiation session."""
    service = NegotiationAssistantService(db)
    return await service.initiate_negotiation(str(current_user.id), negotiation_data)


@router.get("/cultural-guidance")
async def get_cultural_guidance(
    buyer_region: str = Query(..., description="Buyer's region/state"),
    seller_region: str = Query(..., description="Seller's region/state"),
    commodity: Optional[str] = Query(None, description="Type of commodity"),
    seasonal_factor: Optional[SeasonalFactor] = Query(None, description="Current seasonal factor"),
    market_condition: Optional[MarketCondition] = Query(None, description="Current market condition"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> CulturalGuidance:
    """
    Get comprehensive cultural guidance for negotiation between regions.
    
    This endpoint provides detailed cultural guidance including:
    - Regional greeting customs and etiquette
    - Negotiation approach recommendations
    - Cultural sensitivities to be aware of
    - Recommended phrases in local languages
    - Topics to avoid during negotiation
    - Time orientation and relationship importance
    """
    service = NegotiationAssistantService(db)
    return await service.get_cultural_guidance(
        buyer_region=buyer_region,
        seller_region=seller_region,
        commodity=commodity,
        seasonal_factor=seasonal_factor,
        market_condition=market_condition
    )


@router.get("/cultural-sensitivity-indicators")
async def get_cultural_sensitivity_indicators(
    buyer_region: str = Query(..., description="Buyer's region/state"),
    seller_region: str = Query(..., description="Seller's region/state"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get cultural sensitivity indicators for negotiation.
    
    Returns:
    - Cultural distance and compatibility score
    - Potential friction points
    - Sensitivity level and recommendations
    - Success probability based on cultural factors
    - Adaptation strategies for both parties
    """
    service = NegotiationAssistantService(db)
    return await service.get_cultural_sensitivity_indicators(
        buyer_region=buyer_region,
        seller_region=seller_region
    )


@router.get("/region-specific-tips")
async def get_region_specific_tips(
    target_region: str = Query(..., description="Target region to get tips for"),
    user_role: str = Query(..., description="User role: buyer or seller"),
    commodity: Optional[str] = Query(None, description="Type of commodity"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get region-specific negotiation tips.
    
    Provides:
    - Role-specific tips for the target region
    - Communication preferences and styles
    - Timing recommendations
    - Do's and don'ts for the region
    - Success factors and common mistakes to avoid
    """
    if user_role not in ["buyer", "seller"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User role must be either 'buyer' or 'seller'"
        )
    
    service = NegotiationAssistantService(db)
    return await service.get_region_specific_negotiation_tips(
        target_region=target_region,
        user_role=user_role,
        commodity=commodity
    )


@router.get("/cultural-compatibility")
async def analyze_cultural_compatibility(
    buyer_region: str = Query(..., description="Buyer's region/state"),
    seller_region: str = Query(..., description="Seller's region/state"),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Analyze cultural compatibility between buyer and seller regions.
    
    Provides detailed analysis of:
    - Overall compatibility score
    - Communication style compatibility
    - Negotiation approach compatibility
    - Time orientation and hierarchy compatibility
    - Potential challenges and bridging strategies
    - Success predictors for the negotiation
    """
    service = NegotiationAssistantService(db)
    return await service.analyze_cultural_compatibility(
        buyer_region=buyer_region,
        seller_region=seller_region
    )


@router.get("/price-recommendation")
async def get_price_recommendation(
    commodity: str = Query(..., description="Commodity name"),
    quantity: float = Query(..., description="Quantity to negotiate"),
    quality_grade: str = Query("standard", description="Quality grade"),
    location: str = Query(..., description="Location/market"),
    user_role: str = Query("buyer", description="User role: buyer or seller"),
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> PriceRecommendation:
    """Get AI-powered price recommendation for negotiation."""
    if user_role not in ["buyer", "seller"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User role must be either 'buyer' or 'seller'"
        )
    
    service = NegotiationAssistantService(db)
    
    # Create market context
    market_context = MarketContext(
        commodity=commodity,
        location=location,
        current_market_price=100.0,  # This would be fetched from price service
        price_trend="stable",
        market_condition=MarketCondition.STABLE,
        supply_demand_ratio=1.0
    )
    
    return await service.get_price_recommendation(
        commodity=commodity,
        quantity=quantity,
        quality_grade=quality_grade,
        market_context=market_context,
        user_role=user_role
    )


@router.put("/{negotiation_id}")
async def update_negotiation(
    negotiation_id: str,
    update_data: NegotiationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> NegotiationSession:
    """Update negotiation with new step."""
    service = NegotiationAssistantService(db)
    return await service.update_negotiation(
        negotiation_id=negotiation_id,
        user_id=str(current_user.id),
        update_data=update_data
    )


@router.get("/supported-regions")
async def get_supported_regions() -> Dict[str, List[str]]:
    """
    Get list of supported regions and states for cultural guidance.
    
    Returns:
    - List of all supported states
    - States grouped by region (North, South, East, West, Central)
    - Regional characteristics and patterns
    """
    from app.data.cultural_negotiation_database import (
        get_all_supported_states,
        get_states_by_region,
        IndianRegion,
        REGIONAL_NEGOTIATION_PATTERNS
    )
    
    return {
        "all_states": get_all_supported_states(),
        "by_region": {
            region.value: get_states_by_region(region) 
            for region in IndianRegion
        },
        "regional_patterns": {
            region.value: patterns 
            for region, patterns in REGIONAL_NEGOTIATION_PATTERNS.items()
        }
    }


@router.get("/cultural-database-stats")
async def get_cultural_database_stats(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get statistics about the cultural negotiation database.
    
    Returns:
    - Number of supported states and regions
    - Cultural interaction statistics
    - Most common regional combinations
    - Success rates by cultural compatibility
    """
    from app.data.cultural_negotiation_database import (
        get_all_supported_states,
        IndianRegion
    )
    
    service = NegotiationAssistantService(db)
    
    try:
        # Get basic stats
        total_states = len(get_all_supported_states())
        total_regions = len(IndianRegion)
        
        # Get interaction stats from database
        cultural_interactions = await db["cultural_interactions"].count_documents({})
        
        # Get most common regional combinations
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "buyer_region": "$buyer_region",
                        "seller_region": "$seller_region"
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        common_combinations = await db["cultural_interactions"].aggregate(pipeline).to_list(10)
        
        return {
            "database_coverage": {
                "total_states": total_states,
                "total_regions": total_regions,
                "supported_languages": 13  # Based on our database
            },
            "interaction_stats": {
                "total_cultural_interactions": cultural_interactions,
                "most_common_combinations": common_combinations
            },
            "features": [
                "Regional negotiation etiquette database",
                "Cultural guidance recommendation engine", 
                "Region-specific negotiation tips",
                "Cultural sensitivity indicators",
                "Seasonal and market considerations",
                "Historical success pattern analysis"
            ]
        }
        
    except Exception as e:
        return {
            "database_coverage": {
                "total_states": total_states,
                "total_regions": total_regions
            },
            "error": f"Could not fetch interaction stats: {str(e)}"
        }