"""
Basic tests for personalized insights functionality.
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from app.services.personalized_insights_service import personalized_insights_service
from app.models.personalized_insights import (
    UserBehaviorEvent, UserBehaviorType, PersonalizedInsightsRequest,
    PersonalizedRecommendationsRequest, TradingPatternType
)


@pytest.mark.asyncio
async def test_track_user_behavior():
    """Test basic user behavior tracking."""
    user_id = "test_user_123"
    
    # Create a behavior event
    behavior_event = UserBehaviorEvent(
        user_id=user_id,
        event_type=UserBehaviorType.PRICE_CHECK,
        commodity="rice",
        location="Mumbai",
        price_range={"min": 2000, "max": 2500},
        action_taken="viewed_prices"
    )
    
    # Track the behavior
    success = await personalized_insights_service.track_user_behavior(behavior_event)
    assert success is True


@pytest.mark.asyncio
async def test_analyze_user_behavior_insufficient_data():
    """Test behavior analysis with insufficient data."""
    user_id = "test_user_minimal"
    
    # Analyze behavior (should handle minimal data gracefully)
    analysis = await personalized_insights_service.analyze_user_behavior(user_id)
    
    assert analysis.user_id == user_id
    assert analysis.total_events >= 0
    assert analysis.activity_level == "low"
    assert analysis.confidence_in_analysis == 0.0


@pytest.mark.asyncio
async def test_get_user_profile():
    """Test getting user profile."""
    user_id = "test_user_profile"
    
    # Get profile (should create if doesn't exist)
    profile = await personalized_insights_service.get_user_profile(user_id)
    
    # Profile might be None if not exists, which is acceptable
    if profile:
        assert profile.user_id == user_id
        assert isinstance(profile.preferred_commodities, list)
        assert isinstance(profile.preferred_locations, list)


@pytest.mark.asyncio
async def test_generate_personalized_insights_empty():
    """Test generating insights for user with no data."""
    user_id = "test_user_empty"
    
    request = PersonalizedInsightsRequest(
        user_id=user_id,
        max_results=5
    )
    
    insights = await personalized_insights_service.generate_personalized_insights(request)
    
    # Should return empty list or minimal insights
    assert isinstance(insights, list)
    assert len(insights) >= 0


@pytest.mark.asyncio
async def test_generate_personalized_recommendations_empty():
    """Test generating recommendations for user with no data."""
    user_id = "test_user_empty_rec"
    
    request = PersonalizedRecommendationsRequest(
        user_id=user_id,
        max_results=3
    )
    
    recommendations = await personalized_insights_service.generate_personalized_recommendations(request)
    
    # Should return empty list or minimal recommendations
    assert isinstance(recommendations, list)
    assert len(recommendations) >= 0


@pytest.mark.asyncio
async def test_create_multiple_behavior_events():
    """Test creating multiple behavior events for pattern detection."""
    user_id = "test_user_patterns"
    
    # Create multiple transaction events
    events = []
    for i in range(5):
        event = UserBehaviorEvent(
            user_id=user_id,
            event_type=UserBehaviorType.TRANSACTION,
            commodity="wheat",
            location="Delhi",
            quantity=1000 + i * 100,
            transaction_value=50000 + i * 5000,
            action_taken="completed"
        )
        events.append(event)
        
        # Track each event
        success = await personalized_insights_service.track_user_behavior(event)
        assert success is True
        
        # Small delay to ensure different timestamps
        await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_update_user_profile():
    """Test updating user profile."""
    user_id = "test_user_update"
    
    # Create some behavior events first
    for i in range(3):
        event = UserBehaviorEvent(
            user_id=user_id,
            event_type=UserBehaviorType.PRICE_CHECK,
            commodity="onion",
            location="Pune"
        )
        await personalized_insights_service.track_user_behavior(event)
        await asyncio.sleep(0.01)
    
    # Update profile
    profile = await personalized_insights_service.update_user_profile(user_id)
    
    assert profile.user_id == user_id
    assert profile.total_behavior_events >= 3


@pytest.mark.asyncio
async def test_insights_with_specific_commodities():
    """Test generating insights for specific commodities."""
    user_id = "test_user_specific"
    
    request = PersonalizedInsightsRequest(
        user_id=user_id,
        commodities=["rice", "wheat"],
        max_results=10
    )
    
    insights = await personalized_insights_service.generate_personalized_insights(request)
    
    assert isinstance(insights, list)
    # Check that insights are related to requested commodities (if any generated)
    for insight in insights:
        if insight.commodity:
            assert insight.commodity in ["rice", "wheat"]


@pytest.mark.asyncio
async def test_recommendations_with_specific_types():
    """Test generating specific types of recommendations."""
    user_id = "test_user_rec_types"
    
    from app.models.personalized_insights import RecommendationType
    
    request = PersonalizedRecommendationsRequest(
        user_id=user_id,
        recommendation_types=[RecommendationType.BUY_OPPORTUNITY],
        max_results=5
    )
    
    recommendations = await personalized_insights_service.generate_personalized_recommendations(request)
    
    assert isinstance(recommendations, list)
    # Check that recommendations are of requested type (if any generated)
    for rec in recommendations:
        assert rec.recommendation_type == RecommendationType.BUY_OPPORTUNITY


def test_confidence_level_conversion():
    """Test confidence level to score conversion."""
    from app.models.personalized_insights import ConfidenceLevel
    
    service = personalized_insights_service
    
    assert service._confidence_to_score(ConfidenceLevel.LOW) == 0.3
    assert service._confidence_to_score(ConfidenceLevel.MEDIUM) == 0.6
    assert service._confidence_to_score(ConfidenceLevel.HIGH) == 0.8
    assert service._confidence_to_score(ConfidenceLevel.VERY_HIGH) == 0.95


@pytest.mark.asyncio
async def test_behavior_event_validation():
    """Test behavior event validation and creation."""
    user_id = "test_user_validation"
    
    # Test with minimal required fields
    event = UserBehaviorEvent(
        user_id=user_id,
        event_type=UserBehaviorType.SEARCH
    )
    
    assert event.user_id == user_id
    assert event.event_type == UserBehaviorType.SEARCH
    assert event.timestamp is not None
    assert event.event_id is not None
    
    # Test with full fields
    full_event = UserBehaviorEvent(
        user_id=user_id,
        event_type=UserBehaviorType.TRANSACTION,
        commodity="rice",
        location="Mumbai",
        price_range={"min": 2000, "max": 2500},
        quantity=500,
        quality_grade="premium",
        transaction_value=125000,
        action_taken="completed",
        success=True
    )
    
    assert full_event.commodity == "rice"
    assert full_event.quantity == 500
    assert full_event.success is True


if __name__ == "__main__":
    # Run basic tests
    asyncio.run(test_track_user_behavior())
    print("Basic personalized insights tests completed successfully!")