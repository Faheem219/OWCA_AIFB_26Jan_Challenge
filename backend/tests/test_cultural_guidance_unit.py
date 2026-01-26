"""
Unit tests for cultural guidance provision.

**Validates: Requirements 3.3**
"""

import pytest
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.cultural_guidance_service import CulturalGuidanceService
from app.models.negotiation import CulturalGuidance, CulturalContext
from app.data.cultural_negotiation_database import get_all_supported_states


class TestCulturalGuidanceUnit:
    """Unit tests for cultural guidance provision."""
    
    @pytest_asyncio.fixture
    async def cultural_service(self, test_db):
        """Create cultural guidance service for testing."""
        db = await test_db.__anext__()
        return CulturalGuidanceService(db)
    
    @pytest.mark.asyncio
    async def test_cultural_guidance_provision_completeness(self, cultural_service: CulturalGuidanceService):
        """
        **Property 14: Cultural Guidance Provision**
        **Validates: Requirements 3.3**
        
        Test that cultural guidance is provided for regional combinations.
        """
        # Test with specific regions
        buyer_region = "Punjab"
        seller_region = "Tamil Nadu"
        
        guidance = await cultural_service.get_comprehensive_cultural_guidance(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # Verify guidance is provided
        assert guidance is not None, f"No cultural guidance provided for {buyer_region} - {seller_region}"
        assert isinstance(guidance, CulturalGuidance), "Guidance must be CulturalGuidance instance"
        
        # Verify essential guidance components are present
        assert guidance.buyer_region == buyer_region, "Buyer region must match input"
        assert guidance.seller_region == seller_region, "Seller region must match input"
        assert guidance.cultural_context is not None, "Cultural context must be provided"
        assert isinstance(guidance.cultural_context, CulturalContext), "Cultural context must be valid enum"
        
        # Verify greeting style guidance
        assert guidance.greeting_style is not None, "Greeting style guidance must be provided"
        assert len(guidance.greeting_style) > 0, "Greeting style must not be empty"
        assert isinstance(guidance.greeting_style, str), "Greeting style must be string"
        
        # Verify negotiation approach guidance
        assert guidance.negotiation_approach is not None, "Negotiation approach must be provided"
        assert len(guidance.negotiation_approach) > 0, "Negotiation approach must not be empty"
        assert isinstance(guidance.negotiation_approach, str), "Negotiation approach must be string"
        
        # Verify cultural sensitivities
        assert guidance.cultural_sensitivities is not None, "Cultural sensitivities must be provided"
        assert isinstance(guidance.cultural_sensitivities, list), "Cultural sensitivities must be list"
        assert len(guidance.cultural_sensitivities) > 0, "At least one cultural sensitivity must be provided"
        
        for sensitivity in guidance.cultural_sensitivities:
            assert isinstance(sensitivity, str), "Each sensitivity must be string"
            assert len(sensitivity) > 0, "Sensitivity descriptions must not be empty"
        
        # Verify recommended phrases
        assert guidance.recommended_phrases is not None, "Recommended phrases must be provided"
        assert isinstance(guidance.recommended_phrases, dict), "Recommended phrases must be dictionary"
        assert len(guidance.recommended_phrases) > 0, "At least one recommended phrase must be provided"
        
        # Verify at least English phrase is provided
        assert "en" in guidance.recommended_phrases, "English phrase must be provided"
        assert len(guidance.recommended_phrases["en"]) > 0, "English phrase must not be empty"
        
        # Verify taboo topics
        assert guidance.taboo_topics is not None, "Taboo topics must be provided"
        assert isinstance(guidance.taboo_topics, list), "Taboo topics must be list"
        assert len(guidance.taboo_topics) > 0, "At least one taboo topic must be provided"
        
        for topic in guidance.taboo_topics:
            assert isinstance(topic, str), "Each taboo topic must be string"
            assert len(topic) > 0, "Taboo topic descriptions must not be empty"
        
        # Verify time orientation
        assert guidance.time_orientation is not None, "Time orientation must be provided"
        assert guidance.time_orientation in ["punctual", "flexible", "moderately_flexible"], \
            f"Time orientation must be valid value, got: {guidance.time_orientation}"
        
        # Verify relationship importance
        assert guidance.relationship_importance is not None, "Relationship importance must be provided"
        assert guidance.relationship_importance in ["low", "moderate", "high", "very_high"], \
            f"Relationship importance must be valid value, got: {guidance.relationship_importance}"
    
    @pytest.mark.asyncio
    async def test_cultural_sensitivity_indicators_provision(self, cultural_service: CulturalGuidanceService):
        """
        Test that cultural sensitivity indicators are provided.
        """
        buyer_region = "Gujarat"
        seller_region = "West Bengal"
        
        indicators = await cultural_service.get_cultural_sensitivity_indicators(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # Verify essential indicators are provided
        assert "cultural_distance" in indicators, "Cultural distance must be provided"
        assert "compatibility_score" in indicators, "Compatibility score must be provided"
        assert "sensitivity_level" in indicators, "Sensitivity level must be provided"
        assert "recommendations" in indicators, "Recommendations must be provided"
        assert "success_probability" in indicators, "Success probability must be provided"
        
        # Verify data types and ranges
        cultural_distance = indicators["cultural_distance"]
        assert isinstance(cultural_distance, (int, float)), "Cultural distance must be numeric"
        assert 0.0 <= cultural_distance <= 1.0, f"Cultural distance must be 0-1, got: {cultural_distance}"
        
        compatibility_score = indicators["compatibility_score"]
        assert isinstance(compatibility_score, (int, float)), "Compatibility score must be numeric"
        assert 0.0 <= compatibility_score <= 1.0, f"Compatibility score must be 0-1, got: {compatibility_score}"
        
        sensitivity_level = indicators["sensitivity_level"]
        assert sensitivity_level in ["low", "moderate", "high"], \
            f"Sensitivity level must be valid, got: {sensitivity_level}"
        
        recommendations = indicators["recommendations"]
        assert isinstance(recommendations, list), "Recommendations must be list"
        assert len(recommendations) > 0, "At least one recommendation must be provided"
        
        success_probability = indicators["success_probability"]
        assert isinstance(success_probability, (int, float)), "Success probability must be numeric"
        assert 0.0 <= success_probability <= 1.0, f"Success probability must be 0-1, got: {success_probability}"
    
    @pytest.mark.asyncio
    async def test_region_specific_tips_provision(self, cultural_service: CulturalGuidanceService):
        """
        Test that region-specific tips are provided.
        """
        target_region = "Maharashtra"
        user_role = "buyer"
        
        tips = await cultural_service.get_region_specific_tips(
            target_region=target_region,
            user_role=user_role
        )
        
        # Verify essential tip components
        assert "region" in tips, "Region must be specified in tips"
        assert tips["region"] == target_region, "Region must match input"
        
        assert "role_specific_tips" in tips, "Role-specific tips must be provided"
        role_tips = tips["role_specific_tips"]
        assert isinstance(role_tips, list), "Role tips must be list"
        assert len(role_tips) > 0, "At least one role-specific tip must be provided"
        
        assert "communication_tips" in tips, "Communication tips must be provided"
        comm_tips = tips["communication_tips"]
        assert isinstance(comm_tips, list), "Communication tips must be list"
        assert len(comm_tips) > 0, "At least one communication tip must be provided"
        
        assert "success_factors" in tips, "Success factors must be provided"
        success_factors = tips["success_factors"]
        assert isinstance(success_factors, list), "Success factors must be list"
        assert len(success_factors) > 0, "At least one success factor must be provided"
        
        # Verify tip quality
        for tip_list in [role_tips, comm_tips, success_factors]:
            for tip in tip_list:
                assert isinstance(tip, str), "Each tip must be string"
                assert len(tip) > 0, "Tips must not be empty"
    
    @pytest.mark.asyncio
    async def test_cultural_compatibility_analysis_provision(self, cultural_service: CulturalGuidanceService):
        """
        Test that cultural compatibility analysis is provided.
        """
        buyer_region = "Karnataka"
        seller_region = "Haryana"
        
        analysis = await cultural_service.analyze_cultural_compatibility(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # Verify essential analysis components
        assert "overall_compatibility" in analysis, "Overall compatibility must be provided"
        overall_compat = analysis["overall_compatibility"]
        assert isinstance(overall_compat, (int, float)), "Overall compatibility must be numeric"
        assert 0.0 <= overall_compat <= 1.0, f"Overall compatibility must be 0-1, got: {overall_compat}"
        
        assert "potential_challenges" in analysis, "Potential challenges must be provided"
        challenges = analysis["potential_challenges"]
        assert isinstance(challenges, list), "Challenges must be list"
        assert len(challenges) > 0, "At least one potential challenge must be identified"
        
        assert "bridging_strategies" in analysis, "Bridging strategies must be provided"
        strategies = analysis["bridging_strategies"]
        assert isinstance(strategies, list), "Strategies must be list"
        assert len(strategies) > 0, "At least one bridging strategy must be provided"
        
        # Verify content quality
        for challenge in challenges:
            assert isinstance(challenge, str), "Each challenge must be string"
            assert len(challenge) > 0, "Challenges must not be empty"
        
        for strategy in strategies:
            assert isinstance(strategy, str), "Each strategy must be string"
            assert len(strategy) > 0, "Strategies must not be empty"
    
    @pytest.mark.asyncio
    async def test_same_region_guidance_consistency(self, cultural_service: CulturalGuidanceService):
        """
        Test that guidance for states within the same region shows consistency.
        """
        # Test with same region states
        buyer_region = "Punjab"
        seller_region = "Haryana"  # Both are North Indian states
        
        guidance = await cultural_service.get_comprehensive_cultural_guidance(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # For same region, cultural distance should be lower
        indicators = await cultural_service.get_cultural_sensitivity_indicators(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        cultural_distance = indicators["cultural_distance"]
        compatibility_score = indicators["compatibility_score"]
        
        # Same region should have higher compatibility
        assert compatibility_score >= 0.5, \
            f"Same region compatibility should be >= 0.5, got: {compatibility_score}"
        assert cultural_distance <= 0.5, \
            f"Same region cultural distance should be <= 0.5, got: {cultural_distance}"
    
    @pytest.mark.asyncio
    async def test_cross_regional_guidance_specificity(self, cultural_service: CulturalGuidanceService):
        """
        Test that cross-regional guidance addresses specific cultural differences.
        """
        # Test with different region states
        buyer_region = "Punjab"  # North
        seller_region = "Tamil Nadu"  # South
        
        guidance = await cultural_service.get_comprehensive_cultural_guidance(
            buyer_region=buyer_region,
            seller_region=seller_region
        )
        
        # For different regions, guidance should acknowledge differences
        guidance_text = (guidance.negotiation_approach + " " + 
                        " ".join(guidance.cultural_sensitivities)).lower()
        
        # Should contain cultural awareness keywords
        cultural_keywords = ["cultural", "regional", "tradition", "custom", "respect", "different", "sensitivity"]
        assert any(keyword in guidance_text for keyword in cultural_keywords), \
            "Cross-regional guidance should include cultural sensitivity keywords"
    
    def test_supported_states_coverage(self):
        """
        Test that the cultural database covers major Indian states.
        """
        supported_states = get_all_supported_states()
        
        # Verify we have good coverage of major Indian states
        assert len(supported_states) >= 8, f"Should support at least 8 states, got: {len(supported_states)}"
        
        # Check for major states
        major_states = ["Punjab", "Tamil Nadu", "Gujarat", "Maharashtra", "West Bengal", "Karnataka", "Haryana"]
        for state in major_states:
            assert state in supported_states, f"Major state {state} should be supported"