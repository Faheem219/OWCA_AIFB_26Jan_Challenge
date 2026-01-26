"""
Personalized Insights API endpoints.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse

from app.models.common import APIResponse, PaginationParams
from app.models.personalized_insights import (
    UserBehaviorEvent, PersonalizedInsight, PersonalizedRecommendation,
    UserProfile, RecommendationFeedback, BehaviorAnalysisResult,
    PersonalizedInsightsRequest, PersonalizedRecommendationsRequest,
    UserBehaviorType, InsightType, RecommendationType, ConfidenceLevel
)
from app.services.personalized_insights_service import personalized_insights_service
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/behavior/track", response_model=APIResponse)
async def track_user_behavior(
    behavior_event: UserBehaviorEvent,
    current_user: User = Depends(get_current_user)
):
    """
    Track user behavior event for personalized insights.
    
    Records user interactions and activities for behavior analysis
    and personalized recommendation generation.
    """
    try:
        # Ensure the behavior event is for the current user
        behavior_event.user_id = str(current_user.id)
        
        success = await personalized_insights_service.track_user_behavior(behavior_event)
        
        if success:
            return APIResponse(
                success=True,
                message="User behavior tracked successfully",
                data={"event_id": behavior_event.event_id}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to track user behavior"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error tracking user behavior: {str(e)}"
        )


@router.get("/insights", response_model=APIResponse)
async def get_personalized_insights(
    insight_types: Optional[List[InsightType]] = Query(None, description="Types of insights to generate"),
    commodities: Optional[List[str]] = Query(None, description="Specific commodities to focus on"),
    locations: Optional[List[str]] = Query(None, description="Specific locations to focus on"),
    max_results: int = Query(10, ge=1, le=50, description="Maximum number of insights to return"),
    min_confidence: Optional[ConfidenceLevel] = Query(None, description="Minimum confidence level"),
    include_historical: bool = Query(False, description="Include historical insights"),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized market insights for the current user.
    
    Generates insights based on user behavior, trading patterns,
    and current market conditions.
    **Validates: Requirements 8.6**
    """
    try:
        request = PersonalizedInsightsRequest(
            user_id=str(current_user.id),
            insight_types=insight_types,
            commodities=commodities,
            locations=locations,
            max_results=max_results,
            min_confidence=min_confidence,
            include_historical=include_historical
        )
        
        insights = await personalized_insights_service.generate_personalized_insights(request)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(insights)} personalized insights",
            data={
                "insights": [insight.dict() for insight in insights],
                "total_count": len(insights),
                "request_parameters": request.dict()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating personalized insights: {str(e)}"
        )


@router.get("/recommendations", response_model=APIResponse)
async def get_personalized_recommendations(
    recommendation_types: Optional[List[RecommendationType]] = Query(None, description="Types of recommendations to generate"),
    commodities: Optional[List[str]] = Query(None, description="Specific commodities to focus on"),
    locations: Optional[List[str]] = Query(None, description="Specific locations to focus on"),
    max_results: int = Query(5, ge=1, le=20, description="Maximum number of recommendations to return"),
    min_confidence: Optional[ConfidenceLevel] = Query(None, description="Minimum confidence level"),
    risk_tolerance: Optional[str] = Query(None, description="Risk tolerance level"),
    current_user: User = Depends(get_current_user)
):
    """
    Get personalized trading recommendations for the current user.
    
    Generates recommendations based on user behavior, market opportunities,
    and trading patterns.
    **Validates: Requirements 8.6**
    """
    try:
        request = PersonalizedRecommendationsRequest(
            user_id=str(current_user.id),
            recommendation_types=recommendation_types,
            commodities=commodities,
            locations=locations,
            max_results=max_results,
            min_confidence=min_confidence,
            risk_tolerance=risk_tolerance
        )
        
        recommendations = await personalized_insights_service.generate_personalized_recommendations(request)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(recommendations)} personalized recommendations",
            data={
                "recommendations": [rec.dict() for rec in recommendations],
                "total_count": len(recommendations),
                "request_parameters": request.dict()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating personalized recommendations: {str(e)}"
        )


@router.get("/profile", response_model=APIResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get user's behavioral profile with trading patterns and preferences.
    
    Returns comprehensive user profile including identified trading patterns,
    preferences, and behavioral insights.
    """
    try:
        profile = await personalized_insights_service.get_user_profile(str(current_user.id))
        
        if not profile:
            # Create a basic profile if none exists
            profile = await personalized_insights_service.update_user_profile(str(current_user.id))
        
        return APIResponse(
            success=True,
            message="Retrieved user behavioral profile",
            data=profile.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving user profile: {str(e)}"
        )


@router.post("/profile/update", response_model=APIResponse)
async def update_user_profile(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """
    Update user profile based on recent behavior analysis.
    
    Triggers analysis of recent user behavior and updates the profile
    with new patterns and preferences.
    """
    try:
        async def update_task():
            try:
                await personalized_insights_service.update_user_profile(str(current_user.id))
            except Exception as e:
                logger.error(f"Error in profile update task: {str(e)}")
        
        # Add update task to background
        background_tasks.add_task(update_task)
        
        return APIResponse(
            success=True,
            message="Profile update initiated",
            data={"status": "background_task_started"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error initiating profile update: {str(e)}"
        )


@router.get("/behavior/analysis", response_model=APIResponse)
async def analyze_user_behavior(
    current_user: User = Depends(get_current_user)
):
    """
    Analyze user behavior and identify trading patterns.
    
    Performs comprehensive analysis of user behavior to identify
    trading patterns, preferences, and behavioral insights.
    """
    try:
        analysis = await personalized_insights_service.analyze_user_behavior(str(current_user.id))
        
        return APIResponse(
            success=True,
            message="Completed user behavior analysis",
            data=analysis.dict()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing user behavior: {str(e)}"
        )


@router.post("/recommendations/{recommendation_id}/feedback", response_model=APIResponse)
async def submit_recommendation_feedback(
    recommendation_id: str,
    rating: int = Query(..., ge=1, le=5, description="Overall rating (1-5)"),
    usefulness: int = Query(..., ge=1, le=5, description="Usefulness rating (1-5)"),
    accuracy: int = Query(..., ge=1, le=5, description="Accuracy rating (1-5)"),
    timeliness: int = Query(..., ge=1, le=5, description="Timeliness rating (1-5)"),
    comment: Optional[str] = Query(None, description="Optional feedback comment"),
    followed_recommendation: bool = Query(False, description="Whether you followed the recommendation"),
    outcome_successful: Optional[bool] = Query(None, description="Whether the outcome was successful"),
    actual_savings: Optional[float] = Query(None, description="Actual savings achieved"),
    actual_profit: Optional[float] = Query(None, description="Actual profit achieved"),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback on a recommendation for learning and improvement.
    
    Collects user feedback on recommendations to improve future
    recommendation quality and personalization.
    """
    try:
        # Get the recommendation to verify ownership and get creation time
        from app.db.mongodb import get_database
        db = await get_database()
        
        recommendation_doc = await db.personalized_recommendations.find_one({
            "recommendation_id": recommendation_id,
            "user_id": str(current_user.id)
        })
        
        if not recommendation_doc:
            raise HTTPException(
                status_code=404,
                detail="Recommendation not found"
            )
        
        feedback = RecommendationFeedback(
            user_id=str(current_user.id),
            recommendation_id=recommendation_id,
            rating=rating,
            usefulness=usefulness,
            accuracy=accuracy,
            timeliness=timeliness,
            comment=comment,
            followed_recommendation=followed_recommendation,
            outcome_successful=outcome_successful,
            actual_savings=actual_savings,
            actual_profit=actual_profit,
            recommendation_created_at=datetime.fromisoformat(recommendation_doc["created_at"])
        )
        
        success = await personalized_insights_service.record_recommendation_feedback(feedback)
        
        if success:
            return APIResponse(
                success=True,
                message="Recommendation feedback recorded successfully",
                data={"feedback_id": feedback.feedback_id}
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to record recommendation feedback"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error submitting recommendation feedback: {str(e)}"
        )


@router.get("/insights/history", response_model=APIResponse)
async def get_insights_history(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    insight_types: Optional[List[InsightType]] = Query(None, description="Filter by insight types"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical personalized insights for the user.
    
    Retrieves previously generated insights for trend analysis
    and insight effectiveness tracking.
    """
    try:
        from app.db.mongodb import get_database
        
        db = await get_database()
        
        # Build query
        query = {
            "user_id": str(current_user.id),
            "created_at": {
                "$gte": (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            }
        }
        
        if insight_types:
            query["insight_type"] = {"$in": [it.value for it in insight_types]}
        
        # Get total count
        total_count = await db.personalized_insights.count_documents(query)
        
        # Get paginated results
        cursor = db.personalized_insights.find(query).sort("created_at", -1)
        cursor = cursor.skip(pagination.skip).limit(pagination.size)
        
        insights_docs = await cursor.to_list(length=pagination.size)
        
        # Convert ObjectId to string
        for doc in insights_docs:
            doc["_id"] = str(doc["_id"])
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(insights_docs)} historical insights",
            data={
                "insights": insights_docs,
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
            detail=f"Error retrieving insights history: {str(e)}"
        )


@router.get("/recommendations/history", response_model=APIResponse)
async def get_recommendations_history(
    days_back: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    recommendation_types: Optional[List[RecommendationType]] = Query(None, description="Filter by recommendation types"),
    include_feedback: bool = Query(True, description="Include feedback data"),
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user)
):
    """
    Get historical personalized recommendations for the user.
    
    Retrieves previously generated recommendations with optional
    feedback data for effectiveness analysis.
    """
    try:
        from app.db.mongodb import get_database
        
        db = await get_database()
        
        # Build query
        query = {
            "user_id": str(current_user.id),
            "created_at": {
                "$gte": (datetime.utcnow() - timedelta(days=days_back)).isoformat()
            }
        }
        
        if recommendation_types:
            query["recommendation_type"] = {"$in": [rt.value for rt in recommendation_types]}
        
        # Get total count
        total_count = await db.personalized_recommendations.count_documents(query)
        
        # Get paginated results
        cursor = db.personalized_recommendations.find(query).sort("created_at", -1)
        cursor = cursor.skip(pagination.skip).limit(pagination.size)
        
        recommendations_docs = await cursor.to_list(length=pagination.size)
        
        # Add feedback data if requested
        if include_feedback:
            for doc in recommendations_docs:
                feedback_doc = await db.recommendation_feedback.find_one({
                    "recommendation_id": doc["recommendation_id"]
                })
                doc["feedback"] = feedback_doc
        
        # Convert ObjectId to string
        for doc in recommendations_docs:
            doc["_id"] = str(doc["_id"])
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(recommendations_docs)} historical recommendations",
            data={
                "recommendations": recommendations_docs,
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
            detail=f"Error retrieving recommendations history: {str(e)}"
        )


@router.get("/insights/{insight_id}/mark-viewed", response_model=APIResponse)
async def mark_insight_viewed(
    insight_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Mark an insight as viewed by the user.
    
    Updates the insight record to track user engagement
    and improve future insight relevance.
    """
    try:
        from app.db.mongodb import get_database
        
        db = await get_database()
        
        result = await db.personalized_insights.update_one(
            {
                "insight_id": insight_id,
                "user_id": str(current_user.id)
            },
            {
                "$set": {
                    "viewed": True,
                    "viewed_at": datetime.utcnow().isoformat()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=404,
                detail="Insight not found"
            )
        
        return APIResponse(
            success=True,
            message="Insight marked as viewed",
            data={"insight_id": insight_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error marking insight as viewed: {str(e)}"
        )


@router.get("/health", response_model=APIResponse)
async def personalized_insights_health():
    """
    Health check for personalized insights service.
    
    Checks service connectivity and data availability.
    """
    try:
        health_status = {
            "service": "healthy",
            "database": "unknown",
            "cache": "unknown",
            "behavior_tracking": "unknown",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Test database
        try:
            from app.db.mongodb import get_database
            db = await get_database()
            await db.user_behavior_events.find_one()
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
        
        # Test behavior tracking
        try:
            db = await get_database()
            recent_events = await db.user_behavior_events.count_documents({
                "timestamp": {"$gte": (datetime.utcnow() - timedelta(hours=24)).isoformat()}
            })
            health_status["behavior_tracking"] = "healthy" if recent_events > 0 else "no_recent_data"
        except Exception:
            health_status["behavior_tracking"] = "unhealthy"
        
        # Determine overall health
        unhealthy_services = [k for k, v in health_status.items() 
                            if v == "unhealthy" and k not in ["service", "timestamp"]]
        
        if unhealthy_services:
            health_status["service"] = "degraded"
        
        return APIResponse(
            success=True,
            message="Personalized insights service health check completed",
            data=health_status
        )
        
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Health check failed: {str(e)}",
            data={"service": "unhealthy", "error": str(e)}
        )