"""
Property-based test for personalized insights generation.

Tests the property that personalized insights should be generated
based on user behavior and trading patterns.
"""
import pytest
import asyncio
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
from typing import List

from app.services.personalized_insights_service import personalized_insights_service
from app.models.personalized_insights import (
    UserBehaviorEvent, UserBehaviorType, PersonalizedInsightsRequest,
    PersonalizedRecommendationsRequest, TradingPatternType, InsightType,
    RecommendationType, ConfidenceLevel
)


# Test data generators
@st.composite
def user_behavior_event(draw):
    """Generate a valid user behavior event."""
    user_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    event_type = draw(st.sampled_from(list(UserBehaviorType)))
    
    # Optional fields based on event type
    commodity = None
    location = None
    quantity = None
    transaction_value = None
    
    if event_type in [UserBehaviorType.PRICE_CHECK, UserBehaviorType.VIEW_PRODUCT, UserBehaviorType.TRANSACTION]:
        commodity = draw(st.sampled_from(["rice", "wheat", "onion", "tomato", "sugar", "pulses"]))
        location = draw(st.sampled_from(["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune"]))
    
    if event_type == UserBehaviorType.TRANSACTION:
        quantity = draw(st.floats(min_value=10, max_value=10000))
        transaction_value = draw(st.floats(min_value=1000, max_value=1000000))
    
    return UserBehaviorEvent(
        user_id=user_id,
        event_type=event_type,
        commodity=commodity,
        location=location,
        quantity=quantity,
        transaction_value=transaction_value,
        timestamp=datetime.utcnow() - timedelta(days=draw(st.integers(min_value=0, max_value=90)))
    )


@st.composite
def insights_request(draw):
    """Generate a valid personalized insights request."""
    user_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    max_results = draw(st.integers(min_value=1, max_value=20))
    
    # Optional filters
    insight_types = None
    commodities = None
    locations = None
    
    if draw(st.booleans()):
        insight_types = draw(st.lists(st.sampled_from(list(InsightType)), min_size=1, max_size=3))
    
    if draw(st.booleans()):
        commodities = draw(st.lists(st.sampled_from(["rice", "wheat", "onion", "tomato"]), min_size=1, max_size=3))
    
    if draw(st.booleans()):
        locations = draw(st.lists(st.sampled_from(["Mumbai", "Delhi", "Bangalore"]), min_size=1, max_size=2))
    
    return PersonalizedInsightsRequest(
        user_id=user_id,
        insight_types=insight_types,
        commodities=commodities,
        locations=locations,
        max_results=max_results
    )


@st.composite
def recommendations_request(draw):
    """Generate a valid personalized recommendations request."""
    user_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    max_results = draw(st.integers(min_value=1, max_value=10))
    
    # Optional filters
    recommendation_types = None
    commodities = None
    
    if draw(st.booleans()):
        recommendation_types = draw(st.lists(st.sampled_from(list(RecommendationType)), min_size=1, max_size=2))
    
    if draw(st.booleans()):
        commodities = draw(st.lists(st.sampled_from(["rice", "wheat", "onion"]), min_size=1, max_size=2))
    
    return PersonalizedRecommendationsRequest(
        user_id=user_id,
        recommendation_types=recommendation_types,
        commodities=commodities,
        max_results=max_results
    )


@pytest.mark.asyncio
@given(behavior_event=user_behavior_event())
@settings(max_examples=20, deadline=30000)  # Reduced examples for faster testing
async def test_behavior_tracking_always_succeeds(behavior_event):
    """
    Property: User behavior tracking should always succeed for valid events.
    
    **Validates: Requirements 8.6**
    """
    # Track the behavior event
    success = await personalized_insights_service.track_user_behavior(behavior_event)
    
    # Property: Tracking should always succeed for valid events
    assert success is True, f"Behavior tracking failed for valid event: {behavior_event.dict()}"


@pytest.mark.asyncio
@given(request=insights_request())
@settings(max_examples=15, deadline=30000)
async def test_insights_generation_returns_valid_results(request):
    """
    Property: Personalized insights generation should always return valid results.
    
    **Validates: Requirements 8.6**
    """
    # Generate insights
    insights = await personalized_insights_service.generate_personalized_insights(request)
    
    # Property: Should always return a list
    assert isinstance(insights, list), f"Insights should be a list, got {type(insights)}"
    
    # Property: Should not exceed max_results
    assert len(insights) <= request.max_results, f"Returned {len(insights)} insights, max was {request.max_results}"
    
    # Property: All insights should be valid
    for insight in insights:
        assert insight.user_id == request.user_id, f"Insight user_id mismatch: {insight.user_id} != {request.user_id}"
        assert insight.insight_type is not None, "Insight type should not be None"
        assert insight.title is not None and len(insight.title) > 0, "Insight title should not be empty"
        assert insight.description is not None and len(insight.description) > 0, "Insight description should not be empty"
        assert 0.0 <= insight.relevance_score <= 1.0, f"Relevance score should be 0-1, got {insight.relevance_score}"
        assert 1 <= insight.priority <= 5, f"Priority should be 1-5, got {insight.priority}"
        
        # Property: If commodity filter specified, insights should match
        if request.commodities and insight.commodity:
            assert insight.commodity in request.commodities, f"Insight commodity {insight.commodity} not in requested {request.commodities}"
        
        # Property: If insight type filter specified, insights should match
        if request.insight_types:
            assert insight.insight_type in request.insight_types, f"Insight type {insight.insight_type} not in requested {request.insight_types}"


@pytest.mark.asyncio
@given(request=recommendations_request())
@settings(max_examples=15, deadline=30000)
async def test_recommendations_generation_returns_valid_results(request):
    """
    Property: Personalized recommendations generation should always return valid results.
    
    **Validates: Requirements 8.6**
    """
    # Generate recommendations
    recommendations = await personalized_insights_service.generate_personalized_recommendations(request)
    
    # Property: Should always return a list
    assert isinstance(recommendations, list), f"Recommendations should be a list, got {type(recommendations)}"
    
    # Property: Should not exceed max_results
    assert len(recommendations) <= request.max_results, f"Returned {len(recommendations)} recommendations, max was {request.max_results}"
    
    # Property: All recommendations should be valid
    for rec in recommendations:
        assert rec.user_id == request.user_id, f"Recommendation user_id mismatch: {rec.user_id} != {request.user_id}"
        assert rec.recommendation_type is not None, "Recommendation type should not be None"
        assert rec.title is not None and len(rec.title) > 0, "Recommendation title should not be empty"
        assert rec.description is not None and len(rec.description) > 0, "Recommendation description should not be empty"
        assert 0.0 <= rec.relevance_score <= 1.0, f"Relevance score should be 0-1, got {rec.relevance_score}"
        assert 1 <= rec.priority <= 5, f"Priority should be 1-5, got {rec.priority}"
        
        # Property: If commodity filter specified, recommendations should match
        if request.commodities and rec.commodity:
            assert rec.commodity in request.commodities, f"Recommendation commodity {rec.commodity} not in requested {request.commodities}"
        
        # Property: If recommendation type filter specified, recommendations should match
        if request.recommendation_types:
            assert rec.recommendation_type in request.recommendation_types, f"Recommendation type {rec.recommendation_type} not in requested {request.recommendation_types}"
        
        # Property: Success probability should be valid if present
        if rec.success_probability is not None:
            assert 0.0 <= rec.success_probability <= 1.0, f"Success probability should be 0-1, got {rec.success_probability}"


@pytest.mark.asyncio
@given(
    user_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    events=st.lists(user_behavior_event(), min_size=1, max_size=10)
)
@settings(max_examples=10, deadline=45000)
async def test_behavior_analysis_consistency(user_id, events):
    """
    Property: Behavior analysis should be consistent and provide meaningful results.
    
    **Validates: Requirements 8.6**
    """
    # Ensure all events are for the same user
    for event in events:
        event.user_id = user_id
    
    # Track all behavior events
    for event in events:
        success = await personalized_insights_service.track_user_behavior(event)
        assert success, "All behavior tracking should succeed"
        await asyncio.sleep(0.01)  # Small delay for timestamp differences
    
    # Analyze behavior
    analysis = await personalized_insights_service.analyze_user_behavior(user_id)
    
    # Property: Analysis should be for the correct user
    assert analysis.user_id == user_id, f"Analysis user_id mismatch: {analysis.user_id} != {user_id}"
    
    # Property: Total events should be at least the number we tracked
    assert analysis.total_events >= len(events), f"Analysis shows {analysis.total_events} events, but we tracked {len(events)}"
    
    # Property: Engagement score should be valid
    assert 0.0 <= analysis.engagement_score <= 1.0, f"Engagement score should be 0-1, got {analysis.engagement_score}"
    
    # Property: Consistency score should be valid
    assert 0.0 <= analysis.consistency_score <= 1.0, f"Consistency score should be 0-1, got {analysis.consistency_score}"
    
    # Property: Confidence should be valid
    assert 0.0 <= analysis.confidence_in_analysis <= 1.0, f"Confidence should be 0-1, got {analysis.confidence_in_analysis}"
    
    # Property: Activity level should be valid
    assert analysis.activity_level in ["low", "medium", "high"], f"Invalid activity level: {analysis.activity_level}"
    
    # Property: Patterns should be valid if present
    for pattern in analysis.patterns:
        assert pattern.user_id == user_id, f"Pattern user_id mismatch: {pattern.user_id} != {user_id}"
        assert 0.0 <= pattern.confidence <= 1.0, f"Pattern confidence should be 0-1, got {pattern.confidence}"
        assert pattern.pattern_type in list(TradingPatternType), f"Invalid pattern type: {pattern.pattern_type}"


@pytest.mark.asyncio
@given(user_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
@settings(max_examples=10, deadline=20000)
async def test_user_profile_creation_and_retrieval(user_id):
    """
    Property: User profiles should be created and retrieved consistently.
    
    **Validates: Requirements 8.6**
    """
    # Get or create user profile
    profile = await personalized_insights_service._get_or_create_user_profile(user_id)
    
    # Property: Profile should exist and be valid
    assert profile is not None, "Profile should not be None"
    assert profile.user_id == user_id, f"Profile user_id mismatch: {profile.user_id} != {user_id}"
    
    # Property: Profile fields should be valid
    assert isinstance(profile.preferred_commodities, list), "Preferred commodities should be a list"
    assert isinstance(profile.preferred_locations, list), "Preferred locations should be a list"
    assert isinstance(profile.identified_patterns, list), "Identified patterns should be a list"
    
    # Property: Numeric fields should be valid
    assert profile.average_transaction_value >= 0, f"Average transaction value should be >= 0, got {profile.average_transaction_value}"
    assert profile.trading_frequency >= 0, f"Trading frequency should be >= 0, got {profile.trading_frequency}"
    assert 0.0 <= profile.price_sensitivity <= 1.0, f"Price sensitivity should be 0-1, got {profile.price_sensitivity}"
    assert 0.0 <= profile.quality_focus <= 1.0, f"Quality focus should be 0-1, got {profile.quality_focus}"
    assert 0.0 <= profile.risk_tolerance <= 1.0, f"Risk tolerance should be 0-1, got {profile.risk_tolerance}"
    assert 0.0 <= profile.profile_completeness <= 1.0, f"Profile completeness should be 0-1, got {profile.profile_completeness}"


@pytest.mark.asyncio
@given(
    commodity=st.sampled_from(["rice", "wheat", "onion", "tomato", "sugar"]),
    user_id=st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
)
@settings(max_examples=10, deadline=15000)
async def test_commodity_relevance_calculation(commodity, user_id):
    """
    Property: Commodity relevance calculation should return valid scores.
    
    **Validates: Requirements 8.6**
    """
    # Create a user profile with the commodity as preferred
    profile = await personalized_insights_service._get_or_create_user_profile(user_id)
    profile.preferred_commodities = [commodity]
    
    # Calculate relevance
    relevance = personalized_insights_service._calculate_commodity_relevance(commodity, profile)
    
    # Property: Relevance should be valid
    assert 0.0 <= relevance <= 1.0, f"Relevance should be 0-1, got {relevance}"
    
    # Property: Preferred commodity should have higher relevance
    assert relevance > 0.0, f"Preferred commodity should have relevance > 0, got {relevance}"


if __name__ == "__main__":
    # Run a simple test
    import asyncio
    
    async def run_simple_test():
        event = UserBehaviorEvent(
            user_id="test_user",
            event_type=UserBehaviorType.PRICE_CHECK,
            commodity="rice"
        )
        success = await personalized_insights_service.track_user_behavior(event)
        print(f"Simple test result: {success}")
    
    asyncio.run(run_simple_test())
    print("Property-based tests for personalized insights completed!")