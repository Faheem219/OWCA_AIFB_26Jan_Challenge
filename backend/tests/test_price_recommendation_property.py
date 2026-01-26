"""
Property-based test for market-based price recommendations.
**Property 12: Market-Based Price Recommendations**
**Validates: Requirements 3.1**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.negotiation_service import NegotiationAssistantService
from app.models.negotiation import MarketContext, MarketCondition, SeasonalFactor
from app.models.price import PriceData, Location


def create_mock_price_data(market_context, quality_grade="standard"):
    """Helper function to create mock price data with proper Location object."""
    mock_location = Location(
        state="Maharashtra",
        district="Mumbai",
        market_name=f"{market_context.location} Market"
    )
    
    return PriceData(
        commodity=market_context.commodity,
        market_name=f"{market_context.location} Market",
        location=mock_location,
        price_min=market_context.current_market_price * 0.9,
        price_max=market_context.current_market_price * 1.1,
        price_modal=market_context.current_market_price,
        quality_grade=quality_grade,
        date=datetime.now().date(),
        source="test"
    )


@composite
def market_context_strategy(draw):
    """Generate market context for testing."""
    commodity = draw(st.sampled_from([
        "rice", "wheat", "onion", "potato", "tomato", "apple", "mango"
    ]))
    
    location = draw(st.sampled_from([
        "Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune"
    ]))
    
    current_market_price = draw(st.floats(min_value=10.0, max_value=500.0))
    
    price_trend = draw(st.sampled_from(["rising", "falling", "stable"]))
    
    seasonal_factor = draw(st.sampled_from(list(SeasonalFactor)))
    
    market_condition = draw(st.sampled_from(list(MarketCondition)))
    
    supply_demand_ratio = draw(st.floats(min_value=0.5, max_value=2.0))
    
    msp_price = draw(st.one_of(
        st.none(),
        st.floats(min_value=current_market_price * 0.7, max_value=current_market_price * 1.2)
    ))
    
    return MarketContext(
        commodity=commodity,
        location=location,
        current_market_price=current_market_price,
        price_trend=price_trend,
        seasonal_factor=seasonal_factor,
        market_condition=market_condition,
        supply_demand_ratio=supply_demand_ratio,
        msp_price=msp_price
    )


@composite
def negotiation_parameters_strategy(draw):
    """Generate negotiation parameters."""
    quantity = draw(st.floats(min_value=1.0, max_value=1000.0))
    quality_grade = draw(st.sampled_from(["premium", "standard", "below_standard"]))
    user_role = draw(st.sampled_from(["buyer", "seller"]))
    
    return quantity, quality_grade, user_role


@pytest.fixture
def mock_db():
    """Mock database."""
    db = MagicMock()
    db.negotiations = AsyncMock()
    db.products = AsyncMock()
    db.users = AsyncMock()
    db.market_data = AsyncMock()
    return db


@pytest.fixture
def negotiation_service(mock_db):
    """Negotiation assistant service instance."""
    return NegotiationAssistantService(mock_db)


class TestPriceRecommendationProperties:
    """Property-based tests for market-based price recommendations."""
    
    @given(
        market_context=market_context_strategy(),
        params=negotiation_parameters_strategy()
    )
    @settings(max_examples=20, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_12_market_based_price_recommendations(
        self, 
        market_context, 
        params, 
        negotiation_service
    ):
        """
        **Property 12: Market-Based Price Recommendations**
        **Validates: Requirements 3.1**
        
        For any negotiation scenario, the Negotiation_Assistant should provide 
        price recommendations that fall within the current market range for the 
        specific commodity, quality, and location.
        """
        quantity, quality_grade, user_role = params
        
        # Mock price service to return consistent data
        mock_prices = [create_mock_price_data(market_context, quality_grade)]
        negotiation_service.price_service.get_current_prices.return_value = mock_prices
        
        # Get price recommendation
        recommendation = await negotiation_service.get_price_recommendation(
            market_context.commodity,
            quantity,
            quality_grade,
            market_context,
            user_role
        )
        
        # Test: Recommendation should be within reasonable market range
        market_price = market_context.current_market_price
        recommended_price = recommendation.recommended_price
        
        # Allow for quality adjustments and market factors (±50% range)
        min_acceptable = market_price * 0.5
        max_acceptable = market_price * 1.5
        
        assert min_acceptable <= recommended_price <= max_acceptable, \
            f"Recommended price {recommended_price} outside acceptable range [{min_acceptable}, {max_acceptable}]"
        
        # Test: Price range should be logical
        assert recommendation.price_range_min <= recommendation.recommended_price <= recommendation.price_range_max
        
        # Test: Confidence score should be valid
        assert 0.0 <= recommendation.confidence_score <= 1.0
        
        # Test: Success probability should be valid
        assert 0.0 <= recommendation.success_probability <= 1.0
        
        # Test: Factors considered should not be empty
        assert len(recommendation.factors_considered) > 0
        
        # Test: Reasoning should be provided
        assert len(recommendation.reasoning) > 0
        
        # Test: Market comparison should include current market price
        assert "current_market" in recommendation.market_comparison
        assert recommendation.market_comparison["current_market"] == market_price


if __name__ == "__main__":
    pytest.main([__file__, "-v"])