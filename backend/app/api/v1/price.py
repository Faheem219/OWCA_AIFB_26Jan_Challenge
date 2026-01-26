"""
Price discovery API endpoints.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.common import APIResponse, PaginationParams, TimePeriod
from app.models.price import (
    PriceData, PriceQuery, PriceSearchResult, MarketTrend, PriceForecast,
    MarketComparison, MSPData, PriceAlert, QualityGrade, MarketType, Location
)
from app.services.price_discovery_service import price_discovery_service
from app.services.agmarknet_service import agmarknet_service
from app.services.scheduler_service import scheduler_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/current", response_model=APIResponse)
async def get_current_prices(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter (state/district/market)"),
    radius_km: int = Query(50, ge=1, le=500, description="Search radius in kilometers"),
    quality_grade: Optional[QualityGrade] = Query(None, description="Quality grade filter"),
    market_type: Optional[MarketType] = Query(None, description="Market type filter")
):
    """
    Get current market prices for a commodity.
    
    Returns prices within 5 minutes of the latest market update.
    """
    try:
        # Get current prices
        prices = await price_discovery_service.get_current_prices(
            commodity=commodity,
            location=location,
            radius_km=radius_km
        )
        
        # Apply additional filters
        if quality_grade:
            prices = [p for p in prices if p.quality_grade == quality_grade]
        
        if market_type:
            prices = [p for p in prices if p.market_type == market_type]
        
        # Calculate summary statistics
        if prices:
            price_values = [p.price_modal for p in prices]
            summary = {
                "total_markets": len(prices),
                "average_price": sum(price_values) / len(price_values),
                "min_price": min(price_values),
                "max_price": max(price_values),
                "price_spread": max(price_values) - min(price_values),
                "last_updated": max(p.updated_at for p in prices).isoformat()
            }
        else:
            summary = {
                "total_markets": 0,
                "average_price": 0,
                "min_price": 0,
                "max_price": 0,
                "price_spread": 0,
                "last_updated": None
            }
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(prices)} current prices for {commodity}",
            data={
                "prices": [p.dict() for p in prices],
                "summary": summary,
                "query": {
                    "commodity": commodity,
                    "location": location,
                    "radius_km": radius_km,
                    "quality_grade": quality_grade,
                    "market_type": market_type
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving current prices: {str(e)}"
        )


@router.get("/trends", response_model=APIResponse)
async def get_price_trends(
    commodity: str = Query(..., description="Commodity name"),
    period: TimePeriod = Query(TimePeriod.MONTHLY, description="Time period for trend analysis"),
    location: Optional[str] = Query(None, description="Location filter")
):
    """
    Get price trends for a commodity over a specified period.
    
    Provides historical price data with trend analysis and volatility metrics.
    """
    try:
        trend = await price_discovery_service.get_price_trends(
            commodity=commodity,
            period=period,
            location=location
        )
        
        return APIResponse(
            success=True,
            message=f"Retrieved price trends for {commodity}",
            data=trend.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving price trends: {str(e)}"
        )


@router.get("/forecast", response_model=APIResponse)
async def get_price_forecast(
    commodity: str = Query(..., description="Commodity name"),
    forecast_days: int = Query(30, ge=1, le=365, description="Number of days to forecast"),
    location: Optional[str] = Query(None, description="Location filter")
):
    """
    Get price forecast using machine learning models.
    
    Predicts seasonal price variations with confidence intervals.
    """
    try:
        forecast = await price_discovery_service.predict_seasonal_prices(
            commodity=commodity,
            forecast_days=forecast_days,
            location=location
        )
        
        return APIResponse(
            success=True,
            message=f"Generated {forecast_days}-day forecast for {commodity}",
            data=forecast.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating price forecast: {str(e)}"
        )


@router.get("/compare", response_model=APIResponse)
async def compare_market_prices(
    commodity: str = Query(..., description="Commodity name"),
    markets: List[str] = Query(..., description="List of market names to compare")
):
    """
    Compare prices across different markets.
    
    Provides price analysis and identifies the best market for buyers.
    """
    try:
        if len(markets) < 2:
            raise HTTPException(
                status_code=400,
                detail="At least 2 markets required for comparison"
            )
        
        comparison = await price_discovery_service.compare_market_prices(
            commodity=commodity,
            markets=markets
        )
        
        return APIResponse(
            success=True,
            message=f"Compared prices across {len(markets)} markets",
            data=comparison.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing market prices: {str(e)}"
        )


@router.get("/msp", response_model=APIResponse)
async def get_msp_data(
    commodity: str = Query(..., description="Commodity name")
):
    """
    Get Minimum Support Price (MSP) data for agricultural products.
    
    Returns current MSP and indicates if market prices are below MSP.
    """
    try:
        msp_data = await price_discovery_service.get_msp_data(commodity)
        
        if not msp_data:
            return APIResponse(
                success=False,
                message=f"No MSP data found for {commodity}",
                data=None
            )
        
        # Get current market price to compare with MSP
        current_prices = await price_discovery_service.get_current_prices(commodity)
        
        comparison_data = {
            "msp_data": msp_data.dict(),
            "market_comparison": None
        }
        
        if current_prices:
            avg_market_price = sum(p.price_modal for p in current_prices) / len(current_prices)
            is_below_msp, _ = await price_discovery_service.check_price_below_msp(
                commodity, avg_market_price
            )
            
            comparison_data["market_comparison"] = {
                "average_market_price": avg_market_price,
                "is_below_msp": is_below_msp,
                "price_difference": avg_market_price - msp_data.msp_price,
                "percentage_difference": ((avg_market_price - msp_data.msp_price) / msp_data.msp_price) * 100
            }
        
        return APIResponse(
            success=True,
            message=f"Retrieved MSP data for {commodity}",
            data=comparison_data
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving MSP data: {str(e)}"
        )


@router.post("/alerts", response_model=APIResponse)
async def create_price_alert(
    alert_data: PriceAlert,
    current_user: User = Depends(get_current_user)
):
    """
    Create a price alert for a commodity.
    
    Users will be notified when price conditions are met.
    """
    try:
        # Set user_id from authenticated user
        alert_data.user_id = current_user.user_id
        
        # Store alert in database
        from app.db.mongodb import get_database
        db = await get_database()
        
        result = await db.price_alerts.insert_one(alert_data.dict())
        
        return APIResponse(
            success=True,
            message="Price alert created successfully",
            data={
                "alert_id": str(result.inserted_id),
                "alert": alert_data.dict()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating price alert: {str(e)}"
        )


@router.get("/alerts", response_model=APIResponse)
async def get_user_price_alerts(
    current_user: User = Depends(get_current_user),
    active_only: bool = Query(True, description="Return only active alerts")
):
    """
    Get user's price alerts.
    """
    try:
        from app.db.mongodb import get_database
        db = await get_database()
        
        query = {"user_id": current_user.user_id}
        if active_only:
            query["is_active"] = True
        
        cursor = db.price_alerts.find(query).sort("created_at", -1)
        alerts = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for alert in alerts:
            alert["_id"] = str(alert["_id"])
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(alerts)} price alerts",
            data={"alerts": alerts}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving price alerts: {str(e)}"
        )


@router.delete("/alerts/{alert_id}", response_model=APIResponse)
async def delete_price_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete a price alert.
    """
    try:
        from app.db.mongodb import get_database
        from bson import ObjectId
        
        db = await get_database()
        
        result = await db.price_alerts.delete_one({
            "_id": ObjectId(alert_id),
            "user_id": current_user.user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Price alert not found"
            )
        
        return APIResponse(
            success=True,
            message="Price alert deleted successfully",
            data={"deleted_alert_id": alert_id}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting price alert: {str(e)}"
        )


@router.post("/refresh", response_model=APIResponse)
async def refresh_price_data(
    background_tasks: BackgroundTasks,
    commodity: Optional[str] = Query(None, description="Specific commodity to refresh"),
    force: bool = Query(False, description="Force refresh even if recent data exists")
):
    """
    Manually trigger price data refresh from AGMARKNET.
    
    Useful for getting the latest prices outside of scheduled updates.
    """
    try:
        async def refresh_task():
            if commodity:
                # Refresh specific commodity
                price_data = await agmarknet_service.fetch_daily_rates(commodity=commodity)
                if price_data:
                    await agmarknet_service.store_price_data(price_data)
            else:
                # Refresh major commodities
                major_commodities = ['Rice', 'Wheat', 'Onion', 'Potato', 'Tomato']
                for comm in major_commodities:
                    price_data = await agmarknet_service.fetch_daily_rates(commodity=comm)
                    if price_data:
                        await agmarknet_service.store_price_data(price_data)
        
        # Add refresh task to background
        background_tasks.add_task(refresh_task)
        
        return APIResponse(
            success=True,
            message="Price data refresh initiated",
            data={
                "commodity": commodity or "all_major",
                "force": force,
                "status": "background_task_started"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error initiating price refresh: {str(e)}"
        )


@router.get("/search", response_model=APIResponse)
async def search_prices(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    date_from: Optional[date] = Query(None, description="Start date for search"),
    date_to: Optional[date] = Query(None, description="End date for search"),
    quality_grade: Optional[QualityGrade] = Query(None, description="Quality grade filter"),
    market_type: Optional[MarketType] = Query(None, description="Market type filter"),
    radius_km: int = Query(50, ge=1, le=500, description="Search radius"),
    include_predictions: bool = Query(False, description="Include price predictions"),
    pagination: PaginationParams = Depends()
):
    """
    Advanced price search with multiple filters.
    
    Provides comprehensive price search across historical and current data.
    """
    try:
        # Build search query
        query = PriceQuery(
            commodity=commodity,
            location=location,
            radius_km=radius_km,
            date_from=date_from,
            date_to=date_to,
            quality_grade=quality_grade,
            market_type=market_type,
            include_predictions=include_predictions
        )
        
        # Execute search (implement in price_discovery_service)
        # For now, use current prices as base
        prices = await price_discovery_service.get_current_prices(
            commodity=commodity,
            location=location,
            radius_km=radius_km
        )
        
        # Apply filters
        if quality_grade:
            prices = [p for p in prices if p.quality_grade == quality_grade]
        
        if market_type:
            prices = [p for p in prices if p.market_type == market_type]
        
        # Apply pagination
        total_count = len(prices)
        start_idx = pagination.skip
        end_idx = start_idx + pagination.size
        paginated_prices = prices[start_idx:end_idx]
        
        # Calculate statistics
        price_range = None
        average_price = None
        
        if prices:
            price_values = [p.price_modal for p in prices]
            price_range = {"min": min(price_values), "max": max(price_values)}
            average_price = sum(price_values) / len(price_values)
        
        search_result = PriceSearchResult(
            query=query,
            results=paginated_prices,
            total_count=total_count,
            average_price=average_price,
            price_range=price_range,
            last_updated=datetime.utcnow(),
            cache_hit=False
        )
        
        return APIResponse(
            success=True,
            message=f"Found {total_count} price records",
            data={
                "search_result": search_result.dict(),
                "pagination": {
                    "page": pagination.page,
                    "size": pagination.size,
                    "total": total_count,
                    "pages": (total_count + pagination.size - 1) // pagination.size
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching prices: {str(e)}"
        )


@router.get("/scheduler/status", response_model=APIResponse)
async def get_scheduler_status():
    """
    Get status of scheduled price data fetching jobs.
    
    Provides information about background tasks and their execution status.
    """
    try:
        scheduler_info = scheduler_service.get_scheduler_info()
        job_status = scheduler_service.get_job_status()
        
        return APIResponse(
            success=True,
            message="Retrieved scheduler status",
            data={
                "scheduler": scheduler_info,
                "jobs": job_status
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving scheduler status: {str(e)}"
        )


@router.get("/analysis/advanced", response_model=APIResponse)
async def get_advanced_trend_analysis(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    analysis_period_days: int = Query(365, ge=30, le=1095, description="Analysis period in days")
):
    """
    Get advanced trend analysis with pattern recognition and anomaly detection.
    
    Provides comprehensive analysis including seasonal patterns, volatility metrics,
    support/resistance levels, and momentum indicators.
    """
    try:
        analysis = await price_discovery_service.get_advanced_trend_analysis(
            commodity=commodity,
            location=location,
            analysis_period_days=analysis_period_days
        )
        
        # Store analysis results for future reference
        if "error" not in analysis:
            analysis_id = await price_discovery_service.store_trend_analysis_results(
                commodity=commodity,
                location=location,
                analysis_results=analysis
            )
            analysis["analysis_id"] = analysis_id
        
        return APIResponse(
            success="error" not in analysis,
            message=f"Advanced trend analysis for {commodity}" + (f" in {location}" if location else ""),
            data=analysis
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing advanced trend analysis: {str(e)}"
        )


@router.get("/prediction/ensemble", response_model=APIResponse)
async def get_ensemble_price_prediction(
    commodity: str = Query(..., description="Commodity name"),
    forecast_days: int = Query(30, ge=1, le=365, description="Number of days to forecast"),
    location: Optional[str] = Query(None, description="Location filter")
):
    """
    Get ensemble price prediction using multiple machine learning models.
    
    Combines predictions from seasonal ARIMA, moving average, and linear trend models
    to provide more robust forecasting with confidence intervals.
    """
    try:
        prediction = await price_discovery_service.get_ensemble_price_prediction(
            commodity=commodity,
            forecast_days=forecast_days,
            location=location
        )
        
        return APIResponse(
            success="error" not in prediction,
            message=f"Ensemble prediction for {commodity} ({forecast_days} days)",
            data=prediction
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating ensemble prediction: {str(e)}"
        )


@router.get("/analysis/historical", response_model=APIResponse)
async def get_stored_trend_analysis(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back")
):
    """
    Get previously stored trend analysis results.
    
    Retrieves historical trend analysis data for comparison and tracking.
    """
    try:
        stored_analyses = await price_discovery_service.get_stored_trend_analysis(
            commodity=commodity,
            location=location,
            days_back=days_back
        )
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(stored_analyses)} stored analyses",
            data={
                "analyses": stored_analyses,
                "count": len(stored_analyses)
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving stored analyses: {str(e)}"
        )


@router.get("/patterns/seasonal", response_model=APIResponse)
async def get_seasonal_price_patterns(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    years_back: int = Query(3, ge=1, le=10, description="Number of years to analyze")
):
    """
    Get detailed seasonal price patterns for a commodity.
    
    Analyzes multi-year data to identify consistent seasonal trends and patterns.
    """
    try:
        # Get extended historical data for seasonal analysis
        end_date = date.today()
        start_date = end_date - timedelta(days=years_back * 365)
        
        price_points = await price_discovery_service._get_historical_prices(
            commodity, start_date, end_date, location
        )
        
        if len(price_points) < 365:  # Need at least 1 year of data
            return APIResponse(
                success=False,
                message="Insufficient data for seasonal analysis",
                data={"required_days": 365, "available_days": len(price_points)}
            )
        
        # Perform seasonal analysis
        seasonal_analysis = await price_discovery_service._detect_seasonal_patterns(price_points)
        
        # Add year-over-year comparison
        yearly_patterns = {}
        for pp in price_points:
            year = pp.date.year
            month = pp.date.month
            
            if year not in yearly_patterns:
                yearly_patterns[year] = {}
            if month not in yearly_patterns[year]:
                yearly_patterns[year][month] = []
            
            yearly_patterns[year][month].append(pp.price)
        
        # Calculate yearly averages
        yearly_monthly_averages = {}
        for year, months in yearly_patterns.items():
            yearly_monthly_averages[year] = {}
            for month, prices in months.items():
                yearly_monthly_averages[year][month] = statistics.mean(prices)
        
        seasonal_analysis["yearly_patterns"] = yearly_monthly_averages
        seasonal_analysis["analysis_period"] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "years_analyzed": years_back
        }
        
        return APIResponse(
            success=True,
            message=f"Seasonal patterns for {commodity}",
            data=seasonal_analysis
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing seasonal patterns: {str(e)}"
        )


@router.get("/volatility/analysis", response_model=APIResponse)
async def get_volatility_analysis(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    analysis_period_days: int = Query(180, ge=30, le=730, description="Analysis period in days")
):
    """
    Get detailed volatility analysis for a commodity.
    
    Provides comprehensive volatility metrics including rolling volatility,
    volatility clustering, and risk assessment.
    """
    try:
        # Get historical data
        end_date = date.today()
        start_date = end_date - timedelta(days=analysis_period_days)
        
        price_points = await price_discovery_service._get_historical_prices(
            commodity, start_date, end_date, location
        )
        
        if len(price_points) < 30:
            return APIResponse(
                success=False,
                message="Insufficient data for volatility analysis",
                data={"required_days": 30, "available_days": len(price_points)}
            )
        
        prices = [pp.price for pp in price_points]
        
        # Calculate comprehensive volatility metrics
        volatility_metrics = price_discovery_service._calculate_volatility_metrics(prices)
        
        # Add additional volatility analysis
        # Calculate daily returns
        returns = []
        for i in range(1, len(prices)):
            daily_return = (prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] > 0 else 0
            returns.append(daily_return)
        
        # Volatility clustering analysis
        volatility_clusters = []
        high_vol_threshold = statistics.stdev(returns) * 1.5 if len(returns) > 1 else 0
        
        cluster_start = None
        for i, ret in enumerate(returns):
            if abs(ret) > high_vol_threshold:
                if cluster_start is None:
                    cluster_start = i
            else:
                if cluster_start is not None:
                    volatility_clusters.append({
                        "start_index": cluster_start,
                        "end_index": i - 1,
                        "duration_days": i - cluster_start,
                        "start_date": price_points[cluster_start].date.isoformat(),
                        "end_date": price_points[i-1].date.isoformat()
                    })
                    cluster_start = None
        
        # Risk metrics
        if len(returns) > 1:
            var_95 = sorted(returns)[int(len(returns) * 0.05)]  # 5% VaR
            max_drawdown = min(returns)
            
            risk_metrics = {
                "value_at_risk_95": var_95,
                "maximum_drawdown": max_drawdown,
                "sharpe_ratio": statistics.mean(returns) / statistics.stdev(returns) if statistics.stdev(returns) > 0 else 0,
                "downside_volatility": statistics.stdev([r for r in returns if r < 0]) if any(r < 0 for r in returns) else 0
            }
        else:
            risk_metrics = {"error": "insufficient_data_for_risk_metrics"}
        
        volatility_analysis = {
            **volatility_metrics,
            "daily_returns_stats": {
                "mean": statistics.mean(returns) if returns else 0,
                "std_dev": statistics.stdev(returns) if len(returns) > 1 else 0,
                "min": min(returns) if returns else 0,
                "max": max(returns) if returns else 0
            },
            "volatility_clusters": volatility_clusters,
            "risk_metrics": risk_metrics,
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days_analyzed": analysis_period_days,
                "data_points": len(price_points)
            }
        }
        
        return APIResponse(
            success=True,
            message=f"Volatility analysis for {commodity}",
            data=volatility_analysis
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error performing volatility analysis: {str(e)}"
        )


@router.get("/geographic/radius", response_model=APIResponse)
async def get_prices_within_radius(
    commodity: str = Query(..., description="Commodity name"),
    center_lat: float = Query(..., description="Center latitude"),
    center_lon: float = Query(..., description="Center longitude"),
    center_state: str = Query(..., description="Center location state"),
    center_district: str = Query(..., description="Center location district"),
    center_market: str = Query(..., description="Center location market name"),
    radius_km: int = Query(50, ge=1, le=500, description="Search radius in kilometers"),
    quality_grades: Optional[List[QualityGrade]] = Query(None, description="Quality grade filters"),
    market_types: Optional[List[MarketType]] = Query(None, description="Market type filters"),
    include_msp: bool = Query(True, description="Include MSP comparison")
):
    """
    Get prices within a specified radius of a center location.
    
    Implements location-based price queries with coordinate/distance calculations.
    """
    try:
        # Create center location
        center_location = Location(
            state=center_state,
            district=center_district,
            market_name=center_market,
            latitude=center_lat,
            longitude=center_lon
        )
        
        # Get prices within radius
        result = await price_discovery_service.get_prices_within_radius(
            commodity=commodity,
            center_location=center_location,
            radius_km=radius_km,
            quality_grades=quality_grades,
            market_types=market_types,
            include_msp_comparison=include_msp
        )
        
        return APIResponse(
            success=True,
            message=f"Found {result.total_markets} markets within {radius_km}km radius",
            data=result.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting prices within radius: {str(e)}"
        )


@router.get("/geographic/compare", response_model=APIResponse)
async def compare_markets_within_radius(
    commodity: str = Query(..., description="Commodity name"),
    center_lat: float = Query(..., description="Center latitude"),
    center_lon: float = Query(..., description="Center longitude"),
    center_state: str = Query(..., description="Center location state"),
    center_district: str = Query(..., description="Center location district"),
    center_market: str = Query(..., description="Center location market name"),
    radius_km: int = Query(50, ge=1, le=500, description="Search radius in kilometers")
):
    """
    Compare markets within a specified radius.
    
    Provides market comparison with distance information and recommendations.
    """
    try:
        # Create center location
        center_location = Location(
            state=center_state,
            district=center_district,
            market_name=center_market,
            latitude=center_lat,
            longitude=center_lon
        )
        
        # Compare markets
        comparison = await price_discovery_service.compare_markets_within_radius(
            commodity=commodity,
            center_location=center_location,
            radius_km=radius_km
        )
        
        return APIResponse(
            success=True,
            message=f"Compared {len(comparison.markets)} markets within {radius_km}km",
            data=comparison.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing markets within radius: {str(e)}"
        )


@router.get("/quality/categorization", response_model=APIResponse)
async def get_quality_based_categorization(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    radius_km: int = Query(50, ge=1, le=500, description="Search radius if location provided")
):
    """
    Get quality-based price categorization for a commodity.
    
    Implements quality-based price categorization system with premium analysis.
    """
    try:
        categorization = await price_discovery_service.get_quality_based_price_categorization(
            commodity=commodity,
            location=location,
            radius_km=radius_km
        )
        
        return APIResponse(
            success=True,
            message=f"Quality categorization for {commodity}",
            data=categorization.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting quality categorization: {str(e)}"
        )


@router.get("/geographic/variations", response_model=APIResponse)
async def get_location_based_variations(
    commodity: str = Query(..., description="Commodity name"),
    center_lat: float = Query(..., description="Center latitude"),
    center_lon: float = Query(..., description="Center longitude"),
    center_state: str = Query(..., description="Center location state"),
    center_district: str = Query(..., description="Center location district"),
    center_market: str = Query(..., description="Center location market name"),
    radius_km: int = Query(50, ge=1, le=500, description="Analysis radius in kilometers")
):
    """
    Analyze location-based price variations (wholesale vs retail, urban vs rural).
    
    Provides comprehensive analysis of price variations across different location types.
    """
    try:
        from app.models.price import Location
        
        # Create center location
        center_location = Location(
            state=center_state,
            district=center_district,
            market_name=center_market,
            latitude=center_lat,
            longitude=center_lon
        )
        
        # Analyze variations
        variations = await price_discovery_service.get_location_based_price_variations(
            commodity=commodity,
            center_location=center_location,
            radius_km=radius_km
        )
        
        return APIResponse(
            success=True,
            message=f"Location-based price variations for {commodity}",
            data=variations
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing location-based variations: {str(e)}"
        )


@router.get("/msp/integration", response_model=APIResponse)
async def get_msp_integration_analysis(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    radius_km: int = Query(50, ge=1, le=500, description="Search radius")
):
    """
    Get comprehensive MSP integration and comparison analysis.
    
    Provides MSP data integration with current market prices and quality analysis.
    """
    try:
        # Get MSP data
        msp_data = await price_discovery_service.get_msp_data(commodity)
        
        if not msp_data:
            return APIResponse(
                success=False,
                message=f"No MSP data available for {commodity}",
                data=None
            )
        
        # Get current market prices
        current_prices = await price_discovery_service.get_current_prices(
            commodity=commodity,
            location=location,
            radius_km=radius_km
        )
        
        # Analyze MSP vs market prices
        msp_analysis = {
            "msp_data": msp_data.dict(),
            "market_analysis": {
                "total_markets": len(current_prices),
                "markets_below_msp": 0,
                "markets_above_msp": 0,
                "average_market_price": 0,
                "price_distribution": {
                    "below_msp": [],
                    "at_msp": [],
                    "above_msp": []
                }
            }
        }
        
        if current_prices:
            market_prices = [p.price_modal for p in current_prices]
            msp_analysis["market_analysis"]["average_market_price"] = statistics.mean(market_prices)
            
            # Categorize prices relative to MSP
            for price_data in current_prices:
                price = price_data.price_modal
                if price < msp_data.msp_price * 0.95:  # 5% tolerance
                    msp_analysis["market_analysis"]["markets_below_msp"] += 1
                    msp_analysis["market_analysis"]["price_distribution"]["below_msp"].append({
                        "market": price_data.market_name,
                        "price": price,
                        "difference": price - msp_data.msp_price,
                        "percentage_below": ((msp_data.msp_price - price) / msp_data.msp_price) * 100
                    })
                elif price > msp_data.msp_price * 1.05:  # 5% tolerance
                    msp_analysis["market_analysis"]["markets_above_msp"] += 1
                    msp_analysis["market_analysis"]["price_distribution"]["above_msp"].append({
                        "market": price_data.market_name,
                        "price": price,
                        "difference": price - msp_data.msp_price,
                        "percentage_above": ((price - msp_data.msp_price) / msp_data.msp_price) * 100
                    })
                else:
                    msp_analysis["market_analysis"]["price_distribution"]["at_msp"].append({
                        "market": price_data.market_name,
                        "price": price
                    })
            
            # Quality-based MSP analysis
            quality_msp_analysis = {}
            for quality_grade in [QualityGrade.PREMIUM, QualityGrade.STANDARD, QualityGrade.BELOW_STANDARD]:
                quality_prices = [p for p in current_prices if p.quality_grade == quality_grade]
                if quality_prices:
                    avg_quality_price = statistics.mean([p.price_modal for p in quality_prices])
                    quality_msp_analysis[quality_grade.value] = {
                        "average_price": avg_quality_price,
                        "vs_msp": {
                            "difference": avg_quality_price - msp_data.msp_price,
                            "percentage": ((avg_quality_price - msp_data.msp_price) / msp_data.msp_price) * 100
                        },
                        "market_count": len(quality_prices)
                    }
            
            msp_analysis["quality_based_msp_analysis"] = quality_msp_analysis
            
            # Recommendations
            recommendations = []
            below_msp_percentage = (msp_analysis["market_analysis"]["markets_below_msp"] / len(current_prices)) * 100
            
            if below_msp_percentage > 50:
                recommendations.append("Majority of markets trading below MSP - government intervention may be needed")
            elif below_msp_percentage > 25:
                recommendations.append("Significant number of markets below MSP - monitor closely")
            
            if msp_analysis["market_analysis"]["average_market_price"] > msp_data.msp_price * 1.2:
                recommendations.append("Market prices significantly above MSP - good for farmers")
            
            msp_analysis["recommendations"] = recommendations
        
        return APIResponse(
            success=True,
            message=f"MSP integration analysis for {commodity}",
            data=msp_analysis
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in MSP integration analysis: {str(e)}"
        )


@router.get("/health", response_model=APIResponse)
async def price_service_health():
    """
    Health check for price discovery service.
    
    Checks connectivity to AGMARKNET API and database.
    """
    try:
        health_status = {
            "service": "healthy",
            "agmarknet_api": "unknown",
            "database": "unknown",
            "cache": "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test AGMARKNET API
        try:
            test_data = await agmarknet_service.fetch_daily_rates(commodity="Rice")
            health_status["agmarknet_api"] = "healthy" if test_data else "degraded"
        except Exception:
            health_status["agmarknet_api"] = "unhealthy"
        
        # Test database
        try:
            from app.db.mongodb import get_database
            db = await get_database()
            await db.price_data.find_one()
            health_status["database"] = "healthy"
        except Exception:
            health_status["database"] = "unhealthy"
        
        # Test cache
        try:
            from app.db.redis import get_redis
            redis = await get_redis()
            await redis.ping()
            health_status["cache"] = "healthy"
        except Exception:
            health_status["cache"] = "unhealthy"
        
        # Determine overall health
        unhealthy_services = [k for k, v in health_status.items() 
                            if v == "unhealthy" and k != "service" and k != "timestamp"]
        
        if unhealthy_services:
            health_status["service"] = "degraded"
        
        return APIResponse(
            success=True,
            message="Price service health check completed",
            data=health_status
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Health check failed: {str(e)}",
            data={"service": "unhealthy", "error": str(e)}
        )