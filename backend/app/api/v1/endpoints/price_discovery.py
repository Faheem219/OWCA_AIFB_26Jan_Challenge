"""
Price discovery endpoints for AI-powered pricing insights.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import date
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.services.market_data_service import MarketDataService
from app.models.market_data import (
    MarketPriceRequest, MarketPriceResponse,
    PriceHistoryRequest, PriceHistoryResponse,
    DataSyncStatus
)

router = APIRouter()


async def get_market_data_service() -> MarketDataService:
    """Dependency to get market data service."""
    database = await get_database()
    service = MarketDataService(database)
    await service.initialize()
    return service


@router.get("/market-price/{commodity}", response_model=MarketPriceResponse)
async def get_market_price(
    commodity: str,
    state: Optional[str] = Query(None, description="State name filter"),
    market: Optional[str] = Query(None, description="Market name filter"),
    variety: Optional[str] = Query(None, description="Commodity variety filter"),
    date_from: Optional[date] = Query(None, description="Start date for price data"),
    date_to: Optional[date] = Query(None, description="End date for price data"),
    service: MarketDataService = Depends(get_market_data_service)
) -> MarketPriceResponse:
    """
    Get current market price for a commodity.
    
    Args:
        commodity: Commodity name
        state: State name filter (optional)
        market: Market name filter (optional)
        variety: Commodity variety filter (optional)
        date_from: Start date for price data (optional)
        date_to: End date for price data (optional)
        service: Market data service dependency
        
    Returns:
        Market price information with validation and caching
    """
    try:
        request = MarketPriceRequest(
            commodity=commodity,
            variety=variety,
            market=market,
            state=state,
            date_from=date_from,
            date_to=date_to
        )
        
        response = await service.get_market_price(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch market price data: {str(e)}"
        )


@router.get("/price-history/{commodity}", response_model=PriceHistoryResponse)
async def get_price_history(
    commodity: str,
    variety: Optional[str] = Query(None, description="Commodity variety filter"),
    market: Optional[str] = Query(None, description="Market name filter"),
    state: Optional[str] = Query(None, description="State name filter"),
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    include_predictions: bool = Query(False, description="Include price predictions"),
    service: MarketDataService = Depends(get_market_data_service)
) -> PriceHistoryResponse:
    """
    Get historical price trends for a commodity.
    
    Args:
        commodity: Commodity name
        variety: Commodity variety filter (optional)
        market: Market name filter (optional)
        state: State name filter (optional)
        days: Number of days of history (1-365)
        include_predictions: Include price predictions (optional)
        service: Market data service dependency
        
    Returns:
        Historical price data with trend analysis
    """
    try:
        request = PriceHistoryRequest(
            commodity=commodity,
            variety=variety,
            market=market,
            state=state,
            days=days,
            include_predictions=include_predictions
        )
        
        response = await service.get_price_history(request)
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch price history: {str(e)}"
        )


@router.post("/sync-data", response_model=DataSyncStatus)
async def sync_external_data(
    commodities: list[str],
    service: MarketDataService = Depends(get_market_data_service)
) -> DataSyncStatus:
    """
    Synchronize market data from external sources.
    
    Args:
        commodities: List of commodity names to sync
        service: Market data service dependency
        
    Returns:
        Data synchronization status and results
    """
    try:
        if not commodities:
            raise HTTPException(
                status_code=400,
                detail="At least one commodity must be specified"
            )
        
        if len(commodities) > 10:
            raise HTTPException(
                status_code=400,
                detail="Cannot sync more than 10 commodities at once"
            )
        
        sync_status = await service.sync_external_data(commodities)
        return sync_status
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to sync external data: {str(e)}"
        )


@router.get("/data-quality/{commodity}")
async def get_data_quality(
    commodity: str,
    service: MarketDataService = Depends(get_market_data_service)
) -> Dict[str, Any]:
    """
    Get data quality information for a commodity.
    
    Args:
        commodity: Commodity name
        service: Market data service dependency
        
    Returns:
        Data quality metrics and validation results
    """
    try:
        # Get recent market data
        request = MarketPriceRequest(commodity=commodity)
        response = await service.get_market_price(request)
        
        if not response.prices:
            return {
                "commodity": commodity,
                "data_quality": "no_data",
                "quality_score": 0.0,
                "total_records": 0,
                "validation_summary": "No data available"
            }
        
        # Calculate quality metrics
        quality_counts = {}
        total_records = len(response.prices)
        validated_records = sum(1 for price in response.prices if price.is_validated)
        
        for price in response.prices:
            quality = price.data_quality.value
            quality_counts[quality] = quality_counts.get(quality, 0) + 1
        
        # Calculate overall quality score
        quality_weights = {"high": 1.0, "medium": 0.7, "low": 0.4, "unverified": 0.0}
        weighted_score = sum(
            quality_counts.get(quality, 0) * weight 
            for quality, weight in quality_weights.items()
        )
        overall_score = weighted_score / total_records if total_records > 0 else 0.0
        
        return {
            "commodity": commodity,
            "data_quality": response.data_quality.value,
            "quality_score": round(overall_score, 2),
            "total_records": total_records,
            "validated_records": validated_records,
            "quality_distribution": quality_counts,
            "last_updated": response.last_updated.isoformat(),
            "validation_summary": f"{validated_records}/{total_records} records validated"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get data quality information: {str(e)}"
        )


@router.get("/price-prediction/{commodity}")
async def get_price_prediction(
    commodity: str,
    state: Optional[str] = None,
    market: Optional[str] = None,
    days_ahead: int = 7,
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get AI-powered price prediction for a commodity.
    
    Args:
        commodity: Commodity name
        state: State name (optional)
        market: Market name (optional)
        days_ahead: Number of days to predict ahead (default: 7)
        
    Returns:
        Price prediction information
    """
    try:
        from app.services.market_data_service import MarketDataService
        
        market_service = MarketDataService(db)
        await market_service.initialize()
        
        prediction = await market_service.predict_price(
            commodity=commodity,
            state=state,
            market=market,
            days_ahead=days_ahead
        )
        
        return prediction
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate price prediction: {str(e)}"
        )


@router.post("/suggest-price")
async def suggest_price(
    price_request: Dict[str, Any],
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> Dict[str, Any]:
    """
    Get AI-powered price suggestion for a product.
    
    Args:
        price_request: Price suggestion request data with:
            - commodity: str
            - state: Optional[str]
            - market: Optional[str]
            - quality: str (high/medium/low)
        
    Returns:
        Price suggestion with confidence and reasoning
    """
    try:
        from app.services.market_data_service import MarketDataService
        
        # Validate request
        commodity = price_request.get("commodity")
        if not commodity:
            raise HTTPException(status_code=400, detail="Commodity is required")
        
        market_service = MarketDataService(db)
        await market_service.initialize()
        
        suggestion = await market_service.suggest_price_for_product(
            commodity=commodity,
            state=price_request.get("state"),
            market=price_request.get("market"),
            quality=price_request.get("quality", "medium")
        )
        
        return suggestion
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate price suggestion: {str(e)}"
        )