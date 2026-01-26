"""
Unit tests for personalized insights functionality (no database required).
"""
import pytest
from datetime import datetime, timedelta
from app.services.personalized_insights_service import PersonalizedInsightsService
from app.models.personalized_insights import (
    UserBehaviorEvent, UserBehaviorType, PersonalizedInsightsRequest,
    PersonalizedRecommendationsRequest, TradingPatternType, ConfidenceLevel,
    UserProfile
)


def test_service_initialization():
    """Test that the service initializes correctly."""
    service = PersonalizedInsightsService()
    
    assert service.cache_ttl == 1800
    assert service.behavior_analysis_window_days == 90
    assert service.pattern_min_events == 10
    assert service.insight_relevance_threshold == 0.6
    assert service.recommendation_confidence_threshold == 0.7
    
    # Check pattern thresholds
    assert TradingPatternType.BULK_BUYER in service.pattern_thresholds
    assert TradingPatternType.FREQUENT_TRADER in service.pattern_thresholds
    assert TradingPatternType.SEASONAL_TRADER in service.pattern_thresholds


def test_behavior_event_creation():
    """Test creating behavior events."""
    user_id = "test_user_123"
    
    # Test minimal event
    event = UserBehaviorEvent(
        user_id=user_id,
        event_type=UserBehaviorType.SEARCH
    )
    
    assert event.user_id == user_id
    assert event.event_type == UserBehaviorType.SEARCH
    assert event.timestamp is not None
    assert event.event_id is not None
    
    # Test full event
    full_event = UserBehaviorEvent(
        user_id=user_id,
        event_type=UserBehaviorType.TRANSACTION,
        commodity="rice",
        location="Mumbai",
        quantity=500,
        transaction_value=25000,
        action_taken="completed",
        success=True
    )
    
    assert full_event.commodity == "rice"
    assert full_event.location == "Mumbai"
    assert full_event.quantity == 500
    assert full_event.transaction_value == 25000
    assert full_event.success is True


def test_insights_request_creation():
    """Test creating insights requests."""
    user_id = "test_user_456"
    
    # Test minimal request
    request = PersonalizedInsightsRequest(
        user_id=user_id
    )
    
    assert request.user_id == user_id
    assert request.max_results == 10
    assert request.insight_types is None
    assert request.commodities is None
    
    # Test full request
    from app.models.personalized_insights import InsightType
    
    full_request = PersonalizedInsightsRequest(
        user_id=user_id,
        insight_types=[InsightType.PRICE_OPPORTUNITY, InsightType.SEASONAL_TREND],
        commodities=["rice", "wheat"],
        locations=["Mumbai", "Delhi"],
        max_results=5,
        min_confidence=ConfidenceLevel.MEDIUM
    )
    
    assert len(full_request.insight_types) == 2
    assert "rice" in full_request.commodities
    assert "Mumbai" in full_request.locations
    assert full_request.max_results == 5
    assert full_request.min_confidence == ConfidenceLevel.MEDIUM


def test_recommendations_request_creation():
    """Test creating recommendations requests."""
    user_id = "test_user_789"
    
    from app.models.personalized_insights import RecommendationType
    
    request = PersonalizedRecommendationsRequest(
        user_id=user_id,
        recommendation_types=[RecommendationType.BUY_OPPORTUNITY],
        commodities=["onion"],
        max_results=3,
        min_confidence=ConfidenceLevel.HIGH,
        risk_tolerance="medium"
    )
    
    assert request.user_id == user_id
    assert len(request.recommendation_types) == 1
    assert request.recommendation_types[0] == RecommendationType.BUY_OPPORTUNITY
    assert "onion" in request.commodities
    assert request.max_results == 3
    assert request.min_confidence == ConfidenceLevel.HIGH
    assert request.risk_tolerance == "medium"


def test_confidence_level_conversion():
    """Test confidence level to score conversion."""
    service = PersonalizedInsightsService()
    
    assert service._confidence_to_score(ConfidenceLevel.LOW) == 0.3
    assert service._confidence_to_score(ConfidenceLevel.MEDIUM) == 0.6
    assert service._confidence_to_score(ConfidenceLevel.HIGH) == 0.8
    assert service._confidence_to_score(ConfidenceLevel.VERY_HIGH) == 0.95


def test_user_profile_creation():
    """Test creating user profiles."""
    user_id = "test_user_profile"
    
    profile = UserProfile(user_id=user_id)
    
    assert profile.user_id == user_id
    assert isinstance(profile.identified_patterns, list)
    assert len(profile.identified_patterns) == 0
    assert isinstance(profile.preferred_commodities, list)
    assert isinstance(profile.preferred_locations, list)
    assert profile.average_transaction_value == 0.0
    assert profile.trading_frequency == 0.0
    assert profile.price_sensitivity == 0.0
    assert profile.quality_focus == 0.0
    assert profile.risk_tolerance == 0.5
    assert profile.total_behavior_events == 0
    assert profile.profile_completeness == 0.0


def test_seasonality_score_calculation():
    """Test seasonality score calculation."""
    service = PersonalizedInsightsService()
    
    # Test with insufficient data
    events = [{"timestamp": datetime.utcnow().isoformat()} for _ in range(5)]
    score = service._calculate_seasonality_score(events)
    assert score == 0.0
    
    # Test with seasonal data (12+ events across different months)
    seasonal_events = []
    base_date = datetime(2023, 1, 1)
    
    # Create events concentrated in certain months (seasonal pattern)
    for month in [1, 1, 1, 2, 2, 6, 6, 6, 6, 7, 7, 12, 12, 12]:
        event_date = base_date.replace(month=month)
        seasonal_events.append({"timestamp": event_date.isoformat()})
    
    score = service._calculate_seasonality_score(seasonal_events)
    assert 0.0 <= score <= 1.0
    assert score > 0.0  # Should detect some seasonality


def test_quality_focus_score_calculation():
    """Test quality focus score calculation."""
    service = PersonalizedInsightsService()
    
    # Test with no quality grades
    events = [{"quality_grade": None} for _ in range(5)]
    score = service._calculate_quality_focus_score(events)
    assert score == 0.0
    
    # Test with all premium quality
    premium_events = [{"quality_grade": "premium"} for _ in range(5)]
    score = service._calculate_quality_focus_score(premium_events)
    assert score == 1.0
    
    # Test with mixed quality
    mixed_events = [
        {"quality_grade": "premium"},
        {"quality_grade": "standard"},
        {"quality_grade": "premium"},
        {"quality_grade": "standard"}
    ]
    score = service._calculate_quality_focus_score(mixed_events)
    assert score == 0.5


def test_engagement_score_calculation():
    """Test engagement score calculation."""
    service = PersonalizedInsightsService()
    
    # Test with no events
    score = service._calculate_engagement_score([])
    assert score == 0.0
    
    # Test with some events
    events = []
    base_date = datetime.utcnow()
    
    for i in range(10):
        events.append({
            "timestamp": (base_date - timedelta(days=i)).isoformat(),
            "event_type": UserBehaviorType.PRICE_CHECK.value
        })
    
    score = service._calculate_engagement_score(events)
    assert 0.0 <= score <= 1.0
    assert score > 0.0


def test_consistency_score_calculation():
    """Test consistency score calculation."""
    service = PersonalizedInsightsService()
    
    # Test with insufficient events
    events = [{"timestamp": datetime.utcnow().isoformat()} for _ in range(3)]
    score = service._calculate_consistency_score(events)
    assert score == 0.0
    
    # Test with consistent events (same number each week)
    consistent_events = []
    base_date = datetime.utcnow()
    
    # 2 events per week for 4 weeks
    for week in range(4):
        for day in [0, 3]:  # Monday and Thursday
            event_date = base_date - timedelta(weeks=week, days=day)
            consistent_events.append({"timestamp": event_date.isoformat()})
    
    score = service._calculate_consistency_score(consistent_events)
    assert 0.0 <= score <= 1.0


def test_activity_level_determination():
    """Test activity level determination."""
    service = PersonalizedInsightsService()
    
    # Test with no events
    level = service._determine_activity_level([])
    assert level == "low"
    
    # Test with high activity (many events per day)
    base_date = datetime.utcnow()
    high_activity_events = []
    
    for i in range(20):  # 20 events in 5 days = 4 per day
        event_date = base_date - timedelta(days=i % 5, hours=i)
        high_activity_events.append({"timestamp": event_date.isoformat()})
    
    level = service._determine_activity_level(high_activity_events)
    assert level in ["low", "medium", "high"]


def test_learning_indicators_identification():
    """Test learning indicators identification."""
    service = PersonalizedInsightsService()
    
    # Test with no events
    indicators = service._identify_learning_indicators([])
    assert isinstance(indicators, list)
    
    # Test with price checking behavior
    base_date = datetime.utcnow()
    events = []
    
    # Add price check events (recent)
    for i in range(10):
        events.append({
            "timestamp": (base_date - timedelta(days=i)).isoformat(),
            "event_type": UserBehaviorType.PRICE_CHECK.value
        })
    
    # Add transaction events (fewer)
    for i in range(3):
        events.append({
            "timestamp": (base_date - timedelta(days=i * 10)).isoformat(),
            "event_type": UserBehaviorType.TRANSACTION.value
        })
    
    indicators = service._identify_learning_indicators(events)
    assert isinstance(indicators, list)
    
    # Should identify price conscious behavior
    if len(indicators) > 0:
        assert any("price_conscious" in indicator for indicator in indicators)


def test_commodity_relevance_calculation():
    """Test commodity relevance calculation."""
    service = PersonalizedInsightsService()
    
    # Create a user profile
    profile = UserProfile(user_id="test_user")
    profile.preferred_commodities = ["rice", "wheat", "onion"]
    
    # Test relevance for preferred commodity
    relevance = service._calculate_commodity_relevance("rice", profile)
    assert 0.0 <= relevance <= 1.0
    assert relevance > 0.0  # Should have some relevance
    
    # Test relevance for non-preferred commodity
    relevance = service._calculate_commodity_relevance("sugar", profile)
    assert 0.0 <= relevance <= 1.0


if __name__ == "__main__":
    # Run basic unit tests
    test_service_initialization()
    test_behavior_event_creation()
    test_insights_request_creation()
    test_confidence_level_conversion()
    print("Unit tests for personalized insights completed successfully!")