"""
Market Analytics API endpoints.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.common import APIResponse, PaginationParams
from app.models.market_analytics import (
    DemandForecast, WeatherImpactPrediction, SeasonalDemandAlert,
    ExportImportInfluence, MarketAnalytics, ForecastModel,
    WeatherCondition, AlertSeverity, AnalyticsConfiguration
)
from app.services.market_analytics_service import market_analytics_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/demand-forecast", response_model=APIResponse)
async def get_demand_forecast(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    forecast_days: int = Query(30, ge=1, le=365, description="Number of days to forecast"),
    model: ForecastModel = Query(ForecastModel.ENSEMBLE, description="Forecasting model to use")
):
    """
    Generate demand forecast for a commodity using machine learning algorithms.
    
    Implements demand forecasting based on historical data and market patterns.
    **Validates: Requirements 8.2**
    """
    try:
        forecast = await market_analytics_service.generate_demand_forecast(
            commodity=commodity,
            location=location,
            forecast_days=forecast_days,
            model=model
        )
        
        return APIResponse(
            success=True,
            message=f"Generated {forecast_days}-day demand forecast for {commodity}",
            data=forecast.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating demand forecast: {str(e)}"
        )


@router.get("/weather-impact", response_model=APIResponse)
async def predict_weather_impact(
    commodity: str = Query(..., description="Commodity name"),
    weather_condition: WeatherCondition = Query(..., description="Weather condition"),
    affected_regions: List[str] = Query(..., description="List of affected regions"),
    impact_duration_days: int = Query(7, ge=1, le=30, description="Duration of impact in days")
):
    """
    Predict weather impact on agricultural commodity prices.
    
    Creates weather impact prediction system for better market planning.
    **Validates: Requirements 8.3**
    """
    try:
        prediction = await market_analytics_service.predict_weather_impact(
            commodity=commodity,
            weather_condition=weather_condition,
            affected_regions=affected_regions,
            impact_duration_days=impact_duration_days
        )
        
        return APIResponse(
            success=True,
            message=f"Generated weather impact prediction for {commodity}",
            data=prediction.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error predicting weather impact: {str(e)}"
        )


@router.get("/seasonal-alerts", response_model=APIResponse)
async def get_seasonal_alerts(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    days_ahead: int = Query(30, ge=1, le=90, description="Number of days to look ahead"),
    severity_filter: Optional[AlertSeverity] = Query(None, description="Filter by alert severity")
):
    """
    Get seasonal and festival demand alerts for better planning.
    
    Provides seasonal and festival demand alerts for market planning.
    **Validates: Requirements 8.4**
    """
    try:
        alerts = await market_analytics_service.generate_seasonal_alerts(
            commodity=commodity,
            location=location,
            days_ahead=days_ahead
        )
        
        # Apply severity filter if specified
        if severity_filter:
            alerts = [alert for alert in alerts if alert.severity == severity_filter]
        
        # Sort by event start date
        alerts.sort(key=lambda x: x.event_start_date)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(alerts)} seasonal alerts for {commodity}",
            data={
                "alerts": [alert.dict() for alert in alerts],
                "total_count": len(alerts),
                "query": {
                    "commodity": commodity,
                    "location": location,
                    "days_ahead": days_ahead,
                    "severity_filter": severity_filter
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving seasonal alerts: {str(e)}"
        )


@router.get("/export-import-influence", response_model=APIResponse)
async def get_export_import_influence(
    commodity: str = Query(..., description="Commodity name"),
    analysis_period_days: int = Query(30, ge=7, le=365, description="Analysis period in days")
):
    """
    Analyze export-import price influence on domestic markets.
    
    Implements export-import price influence tracking for global market awareness.
    **Validates: Requirements 8.5**
    """
    try:
        influence = await market_analytics_service.analyze_export_import_influence(
            commodity=commodity,
            analysis_period_days=analysis_period_days
        )
        
        return APIResponse(
            success=True,
            message=f"Analyzed export-import influence for {commodity}",
            data=influence.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing export-import influence: {str(e)}"
        )


@router.get("/comprehensive-analytics", response_model=APIResponse)
async def get_comprehensive_analytics(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    analysis_period_days: int = Query(30, ge=7, le=365, description="Analysis period in days")
):
    """
    Generate comprehensive market analytics and forecasting report.
    
    Combines all analytics components for complete market intelligence.
    **Validates: Requirements 8.2, 8.3, 8.4, 8.5**
    """
    try:
        analytics = await market_analytics_service.generate_comprehensive_analytics(
            commodity=commodity,
            location=location,
            analysis_period_days=analysis_period_days
        )
        
        return APIResponse(
            success=True,
            message=f"Generated comprehensive analytics for {commodity}",
            data=analytics.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating comprehensive analytics: {str(e)}"
        )


@router.post("/alerts/subscribe", response_model=APIResponse)
async def subscribe_to_alerts(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    alert_types: List[str] = Query(..., description="Types of alerts to subscribe to"),
    severity_threshold: AlertSeverity = Query(AlertSeverity.MEDIUM, description="Minimum alert severity"),
    current_user: User = Depends(get_current_user)
):
    """
    Subscribe to market analytics alerts.
    
    Allows users to subscribe to various types of market alerts.
    """
    try:
        from app.db.mongodb import get_database
        from app.models.market_analytics import AlertSubscription
        
        db = await get_database()
        
        # Check if subscription already exists
        existing_subscription = await db.alert_subscriptions.find_one({
            "user_id": current_user.user_id,
            "commodity": {"$regex": commodity, "$options": "i"},
            "location": location
        })
        
        if existing_subscription:
            # Update existing subscription
            await db.alert_subscriptions.update_one(
                {"_id": existing_subscription["_id"]},
                {
                    "$set": {
                        "alert_types": alert_types,
                        "severity_threshold": severity_threshold.value,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            subscription_id = str(existing_subscription["_id"])
            action = "updated"
        else:
            # Create new subscription
            subscription = AlertSubscription(
                user_id=current_user.user_id,
                commodity=commodity,
                location=location,
                alert_types=alert_types,
                severity_threshold=severity_threshold
            )
            
            result = await db.alert_subscriptions.insert_one(subscription.dict())
            subscription_id = str(result.inserted_id)
            action = "created"
        
        return APIResponse(
            success=True,
            message=f"Alert subscription {action} successfully",
            data={
                "subscription_id": subscription_id,
                "commodity": commodity,
                "location": location,
                "alert_types": alert_types,
                "severity_threshold": severity_threshold.value
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error managing alert subscription: {str(e)}"
        )


@router.get("/alerts/subscriptions", response_model=APIResponse)
async def get_user_subscriptions(
    current_user: User = Depends(get_current_user),
    active_only: bool = Query(True, description="Return only active subscriptions")
):
    """
    Get user's alert subscriptions.
    """
    try:
        from app.db.mongodb import get_database
        
        db = await get_database()
        
        query = {"user_id": current_user.user_id}
        if active_only:
            query["is_active"] = True
        
        cursor = db.alert_subscriptions.find(query).sort("created_at", -1)
        subscriptions = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for subscription in subscriptions:
            subscription["_id"] = str(subscription["_id"])
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(subscriptions)} alert subscriptions",
            data={"subscriptions": subscriptions}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving alert subscriptions: {str(e)}"
        )


@router.delete("/alerts/subscriptions/{subscription_id}", response_model=APIResponse)
async def delete_alert_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Delete an alert subscription.
    """
    try:
        from app.db.mongodb import get_database
        from bson import ObjectId
        
        db = await get_database()
        
        result = await db.alert_subscriptions.delete_one({
            "_id": ObjectId(subscription_id),
            "user_id": current_user.user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Alert subscription not found"
            )
        
        return APIResponse(
            success=True,
            message="Alert subscription deleted successfully",
            data={"deleted_subscription_id": subscription_id}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting alert subscription: {str(e)}"
        )


@router.get("/analytics/historical", response_model=APIResponse)
async def get_historical_analytics(
    commodity: str = Query(..., description="Commodity name"),
    location: Optional[str] = Query(None, description="Location filter"),
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    pagination: PaginationParams = Depends()
):
    """
    Get historical market analytics data.
    
    Retrieves previously generated analytics for trend analysis.
    """
    try:
        from app.db.mongodb import get_database
        
        db = await get_database()
        
        # Build query
        query = {
            "commodity": {"$regex": commodity, "$options": "i"},
            "analysis_date": {
                "$gte": (date.today() - timedelta(days=days_back)).isoformat()
            }
        }
        
        if location:
            query["location"] = {"$regex": location, "$options": "i"}
        
        # Get total count
        total_count = await db.market_analytics.count_documents(query)
        
        # Get paginated results
        cursor = db.market_analytics.find(query).sort("analysis_date", -1)
        cursor = cursor.skip(pagination.skip).limit(pagination.size)
        
        analytics_docs = await cursor.to_list(length=pagination.size)
        
        # Convert ObjectId to string
        for doc in analytics_docs:
            doc["_id"] = str(doc["_id"])
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(analytics_docs)} historical analytics records",
            data={
                "analytics": analytics_docs,
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
            detail=f"Error retrieving historical analytics: {str(e)}"
        )


@router.post("/analytics/refresh", response_model=APIResponse)
async def refresh_analytics(
    background_tasks: BackgroundTasks,
    commodity: str = Query(..., description="Commodity to refresh analytics for"),
    location: Optional[str] = Query(None, description="Location filter"),
    force: bool = Query(False, description="Force refresh even if recent data exists")
):
    """
    Manually trigger analytics refresh.
    
    Useful for getting the latest analytics outside of scheduled updates.
    """
    try:
        async def refresh_task():
            try:
                # Generate fresh analytics
                analytics = await market_analytics_service.generate_comprehensive_analytics(
                    commodity=commodity,
                    location=location,
                    analysis_period_days=30
                )
                
                # Store in database
                from app.db.mongodb import get_database
                db = await get_database()
                
                await db.market_analytics.insert_one(analytics.dict())
                logger.info(f"Refreshed analytics for {commodity}")
                
            except Exception as e:
                logger.error(f"Error in analytics refresh task: {str(e)}")
        
        # Add refresh task to background
        background_tasks.add_task(refresh_task)
        
        return APIResponse(
            success=True,
            message="Analytics refresh initiated",
            data={
                "commodity": commodity,
                "location": location,
                "force": force,
                "status": "background_task_started"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error initiating analytics refresh: {str(e)}"
        )


@router.get("/models/accuracy", response_model=APIResponse)
async def get_model_accuracy(
    model: Optional[ForecastModel] = Query(None, description="Specific model to check"),
    commodity: Optional[str] = Query(None, description="Commodity filter"),
    location: Optional[str] = Query(None, description="Location filter")
):
    """
    Get forecasting model accuracy metrics.
    
    Provides historical accuracy data for different forecasting models.
    """
    try:
        from app.db.mongodb import get_database
        
        db = await get_database()
        
        # Build query
        query = {}
        if model:
            query["model_name"] = model.value
        if commodity:
            query["commodity"] = {"$regex": commodity, "$options": "i"}
        if location:
            query["location"] = {"$regex": location, "$options": "i"}
        
        cursor = db.model_accuracy.find(query).sort("last_updated", -1)
        accuracy_docs = await cursor.to_list(length=50)
        
        # Convert ObjectId to string
        for doc in accuracy_docs:
            doc["_id"] = str(doc["_id"])
        
        # Calculate summary statistics
        if accuracy_docs:
            accuracies = [doc["accuracy_percentage"] for doc in accuracy_docs]
            summary = {
                "total_models": len(accuracy_docs),
                "average_accuracy": statistics.mean(accuracies),
                "best_accuracy": max(accuracies),
                "worst_accuracy": min(accuracies),
                "accuracy_std_dev": statistics.stdev(accuracies) if len(accuracies) > 1 else 0
            }
        else:
            summary = {
                "total_models": 0,
                "average_accuracy": 0,
                "best_accuracy": 0,
                "worst_accuracy": 0,
                "accuracy_std_dev": 0
            }
        
        return APIResponse(
            success=True,
            message=f"Retrieved accuracy data for {len(accuracy_docs)} model evaluations",
            data={
                "accuracy_records": accuracy_docs,
                "summary": summary
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving model accuracy: {str(e)}"
        )


@router.get("/health", response_model=APIResponse)
async def market_analytics_health():
    """
    Health check for market analytics service.
    
    Checks connectivity to required services and data availability.
    """
    try:
        health_status = {
            "service": "healthy",
            "database": "unknown",
            "cache": "unknown",
            "data_availability": "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test database
        try:
            from app.db.mongodb import get_database
            db = await get_database()
            await db.market_analytics.find_one()
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
        
        # Test data availability
        try:
            db = await get_database()
            
            # Check for recent price data
            recent_date = (date.today() - timedelta(days=7)).isoformat()
            price_count = await db.price_data.count_documents({
                "date": {"$gte": recent_date}
            })
            
            # Check for seasonal factors
            seasonal_count = await db.seasonal_factors.count_documents({})
            
            if price_count > 0 and seasonal_count > 0:
                health_status["data_availability"] = "healthy"
            else:
                health_status["data_availability"] = "degraded"
                
        except Exception:
            health_status["data_availability"] = "unhealthy"
        
        # Determine overall health
        unhealthy_services = [k for k, v in health_status.items() 
                            if v == "unhealthy" and k not in ["service", "timestamp"]]
        
        if unhealthy_services:
            health_status["service"] = "degraded"
        
        return APIResponse(
            success=True,
            message="Market analytics service health check completed",
            data=health_status
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Health check failed: {str(e)}",
            data={"service": "unhealthy", "error": str(e)}
        )