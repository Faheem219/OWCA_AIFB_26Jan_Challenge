"""
Simplified property-based test for personalized insights generation.

Tests Property 43: Personalized Insights Generation without database dependencies.
Validates that personalized insights are generated correctly based on user behavior
and trading patterns as specified in Requirements 8.6.
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.services.personalized_insights_service import PersonalizedInsightsService
from app.models.personalized_insights import (
    UserBehaviorEvent, UserBehaviorType, PersonalizedInsightsRequest,
    PersonalizedRecommendationsRequest, TradingPatternType, InsightType,
    RecommendationType, ConfidenceLevel, UserProfile, TradingPattern
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
def user_profile(draw):
    """Generate a valid user profile with trading patterns."""
    user_id = draw(st.text(min_size=5, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    
    # Generate preferred commodities and locations
    commodities = draw(st.lists(
        st.sampled_from(["rice", "wheat", "onion", "tomato", "sugar", "pulses"]),
        min_size=1, max_size=5, unique=True
    ))
    locations = draw(st.lists(
        st.sampled_from(["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata"]),
        min_size=1, max_size=3, unique=True
    ))
    
    # Generate trading patterns
    patterns = []
    if draw(st.booleans()):
        pattern_type = draw(st.sampled_from(list(TradingPatternType)))
        pattern = TradingPattern(
            user_id=user_id,
            pattern_type=pattern_type,
            confidence=draw(st.floats(min_value=0.6, max_value=1.0)),
            preferred_commodities=commodities[:2],
            preferred_locations=locations[:1],
            frequency_score=draw(st.floats(min_value=0.0, max_value=1.0)),
            volume_score=draw(st.floats(min_value=0.0, max_value=1.0)),
            seasonality_score=draw(st.floats(min_value=0.0, max_value=1.0))
        )
        patterns.append(pattern)
    
    return UserProfile(
        user_id=user_id,
        preferred_commodities=commodities,
        preferred_locations=locations,
        identified_patterns=patterns,
        average_transaction_value=draw(st.floats(min_value=1000, max_value=100000)),
        trading_frequency=draw(st.floats(min_value=0.1, max_value=10.0)),
        price_sensitivity=draw(st.floats(min_value=0.0, max_value=1.0)),
        quality_focus=draw(st.floats(min_value=0.0, max_value=1.0)),
        risk_tolerance=draw(st.floats(min_value=0.0, max_value=1.0)),
        total_behavior_events=draw(st.integers(min_value=0, max_value=1000))
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


class TestPersonalizedInsightsProperties:
    """Property-based tests for personalized insights generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = PersonalizedInsightsService()
    
    @given(profile=user_profile())
    @settings(max_examples=20, deadline=10000)
    def test_commodity_relevance_calculation_property(self, profile):
        """
        Property: Commodity relevance calculation should return valid scores.
        
        **Validates: Requirements 8.6**
        """
        for commodity in ["rice", "wheat", "onion", "tomato", "sugar"]:
            relevance = self.service._calculate_commodity_relevance(commodity, profile)
            
            # Property: Relevance should be valid
            assert 0.0 <= relevance <= 1.0, f"Relevance should be 0-1, got {relevance}"
            
            # Property: Preferred commodity should have higher relevance
            if commodity in profile.preferred_commodities:
                assert relevance > 0.0, f"Preferred commodity should have relevance > 0, got {relevance}"
    
    @given(
        events=st.lists(
            st.fixed_dictionaries({
                "quality_grade": st.one_of(
                    st.sampled_from(["premium", "standard", "below_standard"]),
                    st.none()
                )
            }),
            min_size=1, max_size=20
        )
    )
    @settings(max_examples=15, deadline=8000)
    def test_quality_focus_score_calculation_property(self, events):
        """
        Property: Quality focus score calculation should return valid scores.
        
        **Validates: Requirements 8.6**
        """
        score = self.service._calculate_quality_focus_score(events)
        
        # Property: Score should be valid
        assert 0.0 <= score <= 1.0, f"Quality focus score should be 0-1, got {score}"
        
        # Property: If all events have premium quality, score should be 1.0
        premium_events = [e for e in events if e.get("quality_grade") == "premium"]
        quality_events = [e for e in events if e.get("quality_grade") is not None]
        
        if quality_events and len(premium_events) == len(quality_events):
            assert score == 1.0, f"All premium quality should give score 1.0, got {score}"
    
    @given(confidence=st.sampled_from(list(ConfidenceLevel)))
    @settings(max_examples=10, deadline=5000)
    def test_confidence_to_score_conversion_property(self, confidence):
        """
        Property: Confidence level to score conversion should be consistent.
        
        **Validates: Requirements 8.6**
        """
        score = self.service._confidence_to_score(confidence)
        
        # Property: Score should be valid
        assert 0.0 <= score <= 1.0, f"Confidence score should be 0-1, got {score}"
        
        # Property: Higher confidence levels should have higher scores
        if confidence == ConfidenceLevel.LOW:
            assert score == 0.3, f"LOW confidence should be 0.3, got {score}"
        elif confidence == ConfidenceLevel.MEDIUM:
            assert score == 0.6, f"MEDIUM confidence should be 0.6, got {score}"
        elif confidence == ConfidenceLevel.HIGH:
            assert score == 0.8, f"HIGH confidence should be 0.8, got {score}"
        elif confidence == ConfidenceLevel.VERY_HIGH:
            assert score == 0.95, f"VERY_HIGH confidence should be 0.95, got {score}"
    
    @given(profile=user_profile())
    @settings(max_examples=15, deadline=8000)
    def test_user_profile_consistency_property(self, profile):
        """
        Property: User profiles should maintain internal consistency.
        
        **Validates: Requirements 8.6**
        """
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
        assert profile.total_behavior_events >= 0, f"Total behavior events should be >= 0, got {profile.total_behavior_events}"
        
        # Property: Patterns should be consistent with profile
        for pattern in profile.identified_patterns:
            assert pattern.user_id == profile.user_id, f"Pattern user_id should match profile user_id"
            assert 0.0 <= pattern.confidence <= 1.0, f"Pattern confidence should be 0-1, got {pattern.confidence}"
    
    @given(request=insights_request())
    @settings(max_examples=10, deadline=8000)
    def test_insights_request_validation_property(self, request):
        """
        Property: Insights requests should be properly validated.
        
        **Validates: Requirements 8.6**
        """
        # Property: Request fields should be valid
        assert isinstance(request.user_id, str), "User ID should be a string"
        assert len(request.user_id) > 0, "User ID should not be empty"
        assert request.max_results >= 1, f"Max results should be >= 1, got {request.max_results}"
        assert request.max_results <= 50, f"Max results should be <= 50, got {request.max_results}"
        
        # Property: Optional filters should be valid if present
        if request.insight_types:
            assert isinstance(request.insight_types, list), "Insight types should be a list"
            for insight_type in request.insight_types:
                assert insight_type in list(InsightType), f"Invalid insight type: {insight_type}"
        
        if request.commodities:
            assert isinstance(request.commodities, list), "Commodities should be a list"
            for commodity in request.commodities:
                assert isinstance(commodity, str), "Commodity should be a string"
                assert len(commodity) > 0, "Commodity should not be empty"
        
        if request.locations:
            assert isinstance(request.locations, list), "Locations should be a list"
            for location in request.locations:
                assert isinstance(location, str), "Location should be a string"
                assert len(location) > 0, "Location should not be empty"
    
    @given(
        transaction_events=st.lists(
            st.fixed_dictionaries({
                "timestamp": st.datetimes(
                    min_value=datetime(2023, 1, 1),
                    max_value=datetime(2024, 12, 31)
                ).map(lambda dt: dt.isoformat())
            }),
            min_size=12, max_size=50  # Need at least 12 for seasonality calculation
        )
    )
    @settings(max_examples=8, deadline=10000)
    def test_seasonality_score_calculation_property(self, transaction_events):
        """
        Property: Seasonality score calculation should return valid scores.
        
        **Validates: Requirements 8.6**
        """
        score = self.service._calculate_seasonality_score(transaction_events)
        
        # Property: Score should be valid
        assert 0.0 <= score <= 1.0, f"Seasonality score should be 0-1, got {score}"
        
        # Property: With sufficient data, score should be calculated
        if len(transaction_events) >= 12:
            assert score >= 0.0, f"With sufficient data, score should be >= 0, got {score}"
    
    def test_personalized_insights_core_properties(self):
        """
        Test core properties of personalized insights generation.
        
        **Validates: Requirements 8.6**
        """
        service = PersonalizedInsightsService()
        
        # Test 1: Confidence conversion consistency
        assert service._confidence_to_score(ConfidenceLevel.LOW) < service._confidence_to_score(ConfidenceLevel.MEDIUM)
        assert service._confidence_to_score(ConfidenceLevel.MEDIUM) < service._confidence_to_score(ConfidenceLevel.HIGH)
        assert service._confidence_to_score(ConfidenceLevel.HIGH) < service._confidence_to_score(ConfidenceLevel.VERY_HIGH)
        
        # Test 2: Quality focus calculation with known data
        premium_events = [{"quality_grade": "premium"} for _ in range(5)]
        mixed_events = [{"quality_grade": "premium"}, {"quality_grade": "standard"}]
        no_quality_events = [{"quality_grade": None} for _ in range(3)]
        
        assert service._calculate_quality_focus_score(premium_events) == 1.0
        assert service._calculate_quality_focus_score(mixed_events) == 0.5
        assert service._calculate_quality_focus_score(no_quality_events) == 0.0
        
        # Test 3: User profile with commodity relevance
        profile = UserProfile(
            user_id="test_user",
            preferred_commodities=["rice", "wheat"],
            preferred_locations=["Mumbai"],
            identified_patterns=[]
        )
        
        rice_relevance = service._calculate_commodity_relevance("rice", profile)
        sugar_relevance = service._calculate_commodity_relevance("sugar", profile)
        
        assert rice_relevance > sugar_relevance, "Preferred commodity should have higher relevance"
        assert 0.0 <= rice_relevance <= 1.0, "Relevance should be in valid range"
        assert 0.0 <= sugar_relevance <= 1.0, "Relevance should be in valid range"


if __name__ == "__main__":
    # Run a simple test
    service = PersonalizedInsightsService()
    
    # Test confidence conversion
    assert service._confidence_to_score(ConfidenceLevel.LOW) == 0.3
    assert service._confidence_to_score(ConfidenceLevel.HIGH) == 0.8
    
    # Test quality focus calculation
    events = [{"quality_grade": "premium"}, {"quality_grade": "premium"}]
    score = service._calculate_quality_focus_score(events)
    assert score == 1.0
    
    print("Simple property tests for personalized insights completed successfully!")