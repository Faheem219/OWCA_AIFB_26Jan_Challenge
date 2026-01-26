"""
Property-based test for cultural guidance provision.
**Property 14: Cultural Guidance Provision**
**Validates: Requirements 3.3**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.cultural_guidance_service import CulturalGuidanceService
from app.models.negotiation import (
    CulturalGuidance, CulturalContext, SeasonalFactor, MarketCondition
)
from app.data.cultural_negotiation_database import (
    get_all_supported_states, get_cultural_data, IndianRegion
)


@composite
def regional_combination_strategy(draw):
    """Generate regional combinations for testing."""
    supported_states = get_all_supported_states()
    
    buyer_region = draw(st.sampled_from(supported_states))
    seller_region = draw(st.sampled_from(supported_states))
    
    # Ensure we test different regional combinations
    assume(buyer_region != seller_region or len(supported_states) == 1)
    
    return buyer_region, seller_region


@composite
def negotiation_context_strategy(draw):
    """Generate negotiation context for testing."""
    commodity = draw(st.one_of(
        st.none(),
        st.sampled_from([
            "rice", "wheat", "onion", "potato", "tomato", "apple", "mango",
            "cotton", "sugarcane", "tea", "coffee", "spices"
        ])
    ))
    
    seasonal_factor = draw(st.one_of(
        st.none(),
        st.sampled_from(list(SeasonalFactor))
    ))
    
    market_condition = draw(st.one_of(
        st.none(),
        st.sampled_from(list(MarketCondition))
    ))
    
    negotiation_history = draw(st.one_of(
        st.none(),
        st.lists(
            st.dictionaries(
                st.sampled_from(["step", "action", "outcome"]),
                st.text(min_size=1, max_size=50),
                min_size=1, max_size=3
            ),
            min_size=0, max_size=5
        )
    ))
    
    return commodity, seasonal_factor, market_condition, negotiation_history


@pytest.fixture
def mock_db():
    """Mock database for testing."""
    db = MagicMock()
    db.cultural_interactions = AsyncMock()
    db.negotiations = AsyncMock()
    
    # Mock successful database operations
    db.cultural_interactions.insert_one = AsyncMock()
    db.negotiations.aggregate = AsyncMock()
    db.negotiations.aggregate.return_value.to_list = AsyncMock(return_value=[])
    
    return db


@pytest.fixture
def cultural_service(mock_db):
    """Cultural guidance service instance."""
    return CulturalGuidanceService(mock_db)


class TestCulturalGuidanceProperties:
    """Property-based tests for cultural guidance provision."""
    
    @given(
        regions=regional_combination_strategy(),
        context=negotiation_context_strategy()
    )
    @settings(max_examples=50, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_14_cultural_guidance_provision(
        self, 
        regions, 
        context, 
        cultural_service
    ):
        """
        **Property 14: Cultural Guidance Provision**
        **Validates: Requirements 3.3**
        
        For any negotiation between parties from different regions, the 
        Negotiation_Assistant should provide appropriate cultural etiquette 
        guidance specific to the regional combination.
        """
        buyer_region, seller_region = regions
        commodity, seasonal_factor, market_condition, negotiation_history = context
        
        # Get comprehensive cultural guidance
        guidance = await cultural_service.get_comprehensive_cultural_guidance(
            buyer_region=buyer_region,
            seller_region=seller_region,
            commodity=commodity,
            seasonal_factor=seasonal_factor,
            market_condition=market_condition,
            negotiation_history=negotiation_history
        )
        
        # Property: Cultural guidance must always be provided
        assert guidance is not None, \
            f"Cultural guidance must be provided for {buyer_region} - {seller_region}"
        
        assert isinstance(guidance, CulturalGuidance), \
            "Guidance must be CulturalGuidance instance"
        
        # Property: Regional information must be preserved
        assert guidance.buyer_region == buyer_region, \
            f"Buyer region mismatch: expected {buyer_region}, got {guidance.buyer_region}"
        
        assert guidance.seller_region == seller_region, \
            f"Seller region mismatch: expected {seller_region}, got {guidance.seller_region}"
        
        # Property: Cultural context must be appropriate
        assert guidance.cultural_context is not None, \
            "Cultural context must be provided"
        
        assert isinstance(guidance.cultural_context, CulturalContext), \
            f"Cultural context must be valid enum, got {type(guidance.cultural_context)}"
        
        # Property: Essential guidance components must be present and non-empty
        essential_components = [
            ("greeting_style", guidance.greeting_style),
            ("negotiation_approach", guidance.negotiation_approach),
        ]
        
        for component_name, component_value in essential_components:
            assert component_value is not None, \
                f"{component_name} must be provided"
            assert isinstance(component_value, str), \
                f"{component_name} must be string, got {type(component_value)}"
            assert len(component_value.strip()) > 0, \
                f"{component_name} must not be empty"
        
        # Property: Cultural sensitivities must be provided as non-empty list
        assert guidance.cultural_sensitivities is not None, \
            "Cultural sensitivities must be provided"
        assert isinstance(guidance.cultural_sensitivities, list), \
            "Cultural sensitivities must be list"
        assert len(guidance.cultural_sensitivities) > 0, \
            "At least one cultural sensitivity must be provided"
        
        for sensitivity in guidance.cultural_sensitivities:
            assert isinstance(sensitivity, str), \
                f"Each sensitivity must be string, got {type(sensitivity)}"
            assert len(sensitivity.strip()) > 0, \
                "Sensitivity descriptions must not be empty"
        
        # Property: Recommended phrases must include at least English
        assert guidance.recommended_phrases is not None, \
            "Recommended phrases must be provided"
        assert isinstance(guidance.recommended_phrases, dict), \
            "Recommended phrases must be dictionary"
        assert len(guidance.recommended_phrases) > 0, \
            "At least one recommended phrase must be provided"
        assert "en" in guidance.recommended_phrases, \
            "English phrase must always be provided"
        assert len(guidance.recommended_phrases["en"].strip()) > 0, \
            "English phrase must not be empty"
        
        # Property: Taboo topics must be provided
        assert guidance.taboo_topics is not None, \
            "Taboo topics must be provided"
        assert isinstance(guidance.taboo_topics, list), \
            "Taboo topics must be list"
        assert len(guidance.taboo_topics) > 0, \
            "At least one taboo topic must be provided"
        
        for topic in guidance.taboo_topics:
            assert isinstance(topic, str), \
                f"Each taboo topic must be string, got {type(topic)}"
            assert len(topic.strip()) > 0, \
                "Taboo topic descriptions must not be empty"
        
        # Property: Time orientation must be valid
        assert guidance.time_orientation is not None, \
            "Time orientation must be provided"
        valid_time_orientations = ["punctual", "flexible", "moderately_flexible"]
        assert guidance.time_orientation in valid_time_orientations, \
            f"Time orientation must be valid: {valid_time_orientations}, got {guidance.time_orientation}"
        
        # Property: Relationship importance must be valid
        assert guidance.relationship_importance is not None, \
            "Relationship importance must be provided"
        valid_relationship_levels = ["low", "moderate", "high", "very_high"]
        assert guidance.relationship_importance in valid_relationship_levels, \
            f"Relationship importance must be valid: {valid_relationship_levels}, got {guidance.relationship_importance}"
    
    @given(
        regions=regional_combination_strategy()
    )
    @settings(max_examples=30, deadline=8000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_cultural_sensitivity_indicators_provision(
        self, 
        regions, 
        cultural_service
    ):
        """
        Test that cultural sensitivity indicators are provided for any regional combination.
        """
        buyer_region, seller_region = regions
        
        indicators = await cultural_service.get_cultural_sensitivity_indicators(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # Property: Essential indicators must be provided
        required_indicators = [
            "cultural_distance", "compatibility_score", "sensitivity_level",
            "recommendations", "success_probability"
        ]
        
        for indicator in required_indicators:
            assert indicator in indicators, \
                f"Required indicator '{indicator}' must be provided"
        
        # Property: Numeric indicators must be in valid ranges
        cultural_distance = indicators["cultural_distance"]
        assert isinstance(cultural_distance, (int, float)), \
            f"Cultural distance must be numeric, got {type(cultural_distance)}"
        assert 0.0 <= cultural_distance <= 1.0, \
            f"Cultural distance must be 0-1, got {cultural_distance}"
        
        compatibility_score = indicators["compatibility_score"]
        assert isinstance(compatibility_score, (int, float)), \
            f"Compatibility score must be numeric, got {type(compatibility_score)}"
        assert 0.0 <= compatibility_score <= 1.0, \
            f"Compatibility score must be 0-1, got {compatibility_score}"
        
        success_probability = indicators["success_probability"]
        assert isinstance(success_probability, (int, float)), \
            f"Success probability must be numeric, got {type(success_probability)}"
        assert 0.0 <= success_probability <= 1.0, \
            f"Success probability must be 0-1, got {success_probability}"
        
        # Property: Sensitivity level must be valid
        sensitivity_level = indicators["sensitivity_level"]
        valid_levels = ["low", "moderate", "high"]
        assert sensitivity_level in valid_levels, \
            f"Sensitivity level must be valid: {valid_levels}, got {sensitivity_level}"
        
        # Property: Recommendations must be provided
        recommendations = indicators["recommendations"]
        assert isinstance(recommendations, list), \
            "Recommendations must be list"
        assert len(recommendations) > 0, \
            "At least one recommendation must be provided"
        
        for rec in recommendations:
            assert isinstance(rec, str), \
                f"Each recommendation must be string, got {type(rec)}"
            assert len(rec.strip()) > 0, \
                "Recommendations must not be empty"
    
    @given(
        regions=regional_combination_strategy()
    )
    @settings(max_examples=25, deadline=6000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_region_specific_guidance_provision(
        self, 
        regions, 
        cultural_service
    ):
        """
        Test that region-specific guidance is provided for any region.
        """
        buyer_region, seller_region = regions
        
        # Test buyer-specific tips
        buyer_tips = await cultural_service.get_region_specific_tips(
            target_region=seller_region,  # Buyer gets tips about seller's region
            user_role="buyer"
        )
        
        # Property: Essential tip components must be provided
        required_components = [
            "region", "role_specific_tips", "communication_tips", "success_factors"
        ]
        
        for component in required_components:
            assert component in buyer_tips, \
                f"Required component '{component}' must be provided for buyer tips"
        
        assert buyer_tips["region"] == seller_region, \
            f"Region must match target region: expected {seller_region}, got {buyer_tips['region']}"
        
        # Property: Tips must be non-empty lists with string content
        tip_lists = ["role_specific_tips", "communication_tips", "success_factors"]
        
        for tip_list_name in tip_lists:
            tip_list = buyer_tips[tip_list_name]
            assert isinstance(tip_list, list), \
                f"{tip_list_name} must be list"
            assert len(tip_list) > 0, \
                f"{tip_list_name} must contain at least one tip"
            
            for tip in tip_list:
                assert isinstance(tip, str), \
                    f"Each tip in {tip_list_name} must be string, got {type(tip)}"
                assert len(tip.strip()) > 0, \
                    f"Tips in {tip_list_name} must not be empty"
        
        # Test seller-specific tips
        seller_tips = await cultural_service.get_region_specific_tips(
            target_region=buyer_region,  # Seller gets tips about buyer's region
            user_role="seller"
        )
        
        # Same validation for seller tips
        for component in required_components:
            assert component in seller_tips, \
                f"Required component '{component}' must be provided for seller tips"
        
        assert seller_tips["region"] == buyer_region, \
            f"Region must match target region: expected {buyer_region}, got {seller_tips['region']}"
    
    @given(
        regions=regional_combination_strategy()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_cultural_compatibility_analysis_provision(
        self, 
        regions, 
        cultural_service
    ):
        """
        Test that cultural compatibility analysis is provided for any regional combination.
        """
        buyer_region, seller_region = regions
        
        analysis = await cultural_service.analyze_cultural_compatibility(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # Property: Essential analysis components must be provided
        required_components = [
            "overall_compatibility", "potential_challenges", "bridging_strategies"
        ]
        
        for component in required_components:
            assert component in analysis, \
                f"Required component '{component}' must be provided in compatibility analysis"
        
        # Property: Overall compatibility must be valid numeric score
        overall_compat = analysis["overall_compatibility"]
        assert isinstance(overall_compat, (int, float)), \
            f"Overall compatibility must be numeric, got {type(overall_compat)}"
        assert 0.0 <= overall_compat <= 1.0, \
            f"Overall compatibility must be 0-1, got {overall_compat}"
        
        # Property: Challenges and strategies must be non-empty lists
        challenges = analysis["potential_challenges"]
        assert isinstance(challenges, list), \
            "Potential challenges must be list"
        assert len(challenges) > 0, \
            "At least one potential challenge must be identified"
        
        strategies = analysis["bridging_strategies"]
        assert isinstance(strategies, list), \
            "Bridging strategies must be list"
        assert len(strategies) > 0, \
            "At least one bridging strategy must be provided"
        
        # Property: Content quality validation
        for challenge in challenges:
            assert isinstance(challenge, str), \
                f"Each challenge must be string, got {type(challenge)}"
            assert len(challenge.strip()) > 0, \
                "Challenges must not be empty"
        
        for strategy in strategies:
            assert isinstance(strategy, str), \
                f"Each strategy must be string, got {type(strategy)}"
            assert len(strategy.strip()) > 0, \
                "Strategies must not be empty"
    
    @given(
        regions=regional_combination_strategy()
    )
    @settings(max_examples=15, deadline=4000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_cross_regional_guidance_specificity(
        self, 
        regions, 
        cultural_service
    ):
        """
        Test that cross-regional guidance addresses specific cultural differences.
        """
        buyer_region, seller_region = regions
        
        # Skip if same region (different property)
        assume(buyer_region != seller_region)
        
        guidance = await cultural_service.get_comprehensive_cultural_guidance(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # Property: Cross-regional guidance should acknowledge cultural differences
        guidance_text = (
            guidance.negotiation_approach + " " + 
            " ".join(guidance.cultural_sensitivities) + " " +
            " ".join(guidance.taboo_topics)
        ).lower()
        
        # Should contain cultural awareness keywords
        cultural_keywords = [
            "cultural", "regional", "tradition", "custom", "respect", 
            "different", "sensitivity", "adapt", "understand", "regional"
        ]
        
        has_cultural_awareness = any(keyword in guidance_text for keyword in cultural_keywords)
        assert has_cultural_awareness, \
            f"Cross-regional guidance should include cultural sensitivity keywords. " \
            f"Guidance text: {guidance_text[:200]}..."
        
        # Property: Different regions should have different cultural contexts when appropriate
        buyer_data = get_cultural_data(buyer_region)
        seller_data = get_cultural_data(seller_region)
        
        if buyer_data and seller_data:
            buyer_region_type = buyer_data.get("region")
            seller_region_type = seller_data.get("region")
            
            # If regions are from different Indian regions, cultural context should reflect this
            if buyer_region_type != seller_region_type:
                # Cultural context should not be TRADITIONAL (which implies same region)
                assert guidance.cultural_context != CulturalContext.TRADITIONAL, \
                    f"Different regional types should not have TRADITIONAL context: " \
                    f"{buyer_region_type} vs {seller_region_type}"
    
    @pytest.mark.asyncio
    async def test_supported_states_coverage(self, cultural_service):
        """
        Test that the cultural guidance system covers major Indian states.
        """
        supported_states = get_all_supported_states()
        
        # Property: Must support major Indian states
        assert len(supported_states) >= 8, \
            f"Should support at least 8 states for comprehensive coverage, got: {len(supported_states)}"
        
        # Property: Major states must be supported
        major_states = [
            "Punjab", "Tamil Nadu", "Gujarat", "Maharashtra", 
            "West Bengal", "Karnataka", "Haryana", "Madhya Pradesh"
        ]
        
        for state in major_states:
            assert state in supported_states, \
                f"Major state {state} should be supported. Supported states: {supported_states}"
        
        # Property: Each supported state should have cultural data
        for state in supported_states:
            cultural_data = get_cultural_data(state)
            assert cultural_data is not None, \
                f"Cultural data must be available for supported state: {state}"
            assert len(cultural_data) > 0, \
                f"Cultural data must not be empty for state: {state}"
    
    @given(
        regions=regional_combination_strategy()
    )
    @settings(max_examples=10, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_guidance_consistency_across_calls(
        self, 
        regions, 
        cultural_service
    ):
        """
        Test that cultural guidance is consistent across multiple calls with same parameters.
        """
        buyer_region, seller_region = regions
        
        # Get guidance twice with same parameters
        guidance1 = await cultural_service.get_comprehensive_cultural_guidance(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        guidance2 = await cultural_service.get_comprehensive_cultural_guidance(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # Property: Core guidance should be consistent
        assert guidance1.buyer_region == guidance2.buyer_region
        assert guidance1.seller_region == guidance2.seller_region
        assert guidance1.cultural_context == guidance2.cultural_context
        assert guidance1.greeting_style == guidance2.greeting_style
        assert guidance1.negotiation_approach == guidance2.negotiation_approach
        assert guidance1.time_orientation == guidance2.time_orientation
        assert guidance1.relationship_importance == guidance2.relationship_importance
        
        # Property: Lists should have same content (order may vary)
        assert set(guidance1.cultural_sensitivities) == set(guidance2.cultural_sensitivities)
        assert set(guidance1.taboo_topics) == set(guidance2.taboo_topics)
        assert guidance1.recommended_phrases == guidance2.recommended_phrases


if __name__ == "__main__":
    pytest.main([__file__, "-v"])