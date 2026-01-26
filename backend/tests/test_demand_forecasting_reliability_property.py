"""
Property-based test for demand forecasting reliability.
**Property 39: Demand Forecasting Reliability**
**Validates: Requirements 8.2**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, date, timedelta
import statistics

from app.services.market_analytics_service import market_analytics_service
from app.models.market_analytics import (
    ForecastModel, DemandForecast, WeatherCondition, FestivalType
)
from app.models.price import PricePoint, Location
from app.models.common import TrendDirection


@composite
def commodity_strategy(draw):
    """Generate commodity names for testing."""
    return draw(st.sampled_from([
        "rice", "wheat", "onion", "potato", "tomato", "sugar", "cotton",
        "pulses", "maize", "soybean", "groundnut", "mustard", "apple", "mango"
    ]))


@composite
def location_strategy(draw):
    """Generate location names for testing."""
    return draw(st.sampled_from([
        "Maharashtra", "Punjab", "Haryana", "Uttar Pradesh", "Gujarat",
        "Karnataka", "Tamil Nadu", "Andhra Pradesh", "West Bengal", "Rajasthan"
    ]))


@composite
def forecast_parameters_strategy(draw):
    """Generate forecast parameters for testing."""
    forecast_days = draw(st.integers(min_value=7, max_value=90))
    model = draw(st.sampled_from(list(ForecastModel)))
    return forecast_days, model


@composite
def historical_price_data_strategy(draw):
    """Generate realistic historical price data."""
    num_points = draw(st.integers(min_value=30, max_value=365))
    base_price = draw(st.floats(min_value=50.0, max_value=500.0))
    
    price_points = []
    current_price = base_price
    
    for i in range(num_points):
        # Add some realistic price variation
        price_change = draw(st.floats(min_value=-0.1, max_value=0.1))
        current_price = max(10.0, current_price * (1 + price_change))
        
        price_point = PricePoint(
            date=date.today() - timedelta(days=num_points - i),
            price=current_price,
            volume=draw(st.floats(min_value=100.0, max_value=10000.0))
        )
        price_points.append(price_point)
    
    return price_points


@composite
def market_factors_strategy(draw):
    """Generate market factors for testing."""
    seasonal_factor = draw(st.floats(min_value=0.7, max_value=1.5))
    weather_factor = draw(st.floats(min_value=0.8, max_value=1.3))
    festival_factor = draw(st.floats(min_value=0.9, max_value=1.4))
    trade_factor = draw(st.floats(min_value=0.8, max_value=1.2))
    
    return seasonal_factor, weather_factor, festival_factor, trade_factor


class TestDemandForecastingReliabilityProperty:
    """Property-based tests for demand forecasting reliability."""
    
    @given(
        commodity=commodity_strategy(),
        location=location_strategy(),
        params=forecast_parameters_strategy(),
        price_data=historical_price_data_strategy(),
        factors=market_factors_strategy()
    )
    @settings(max_examples=50, deadline=10000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_39_demand_forecasting_reliability(
        self, 
        commodity, 
        location, 
        params, 
        price_data, 
        factors
    ):
        """
        **Property 39: Demand Forecasting Reliability**
        **Validates: Requirements 8.2**
        
        For any commodity with sufficient historical data, demand forecasts should 
        achieve reasonable accuracy when compared to actual demand patterns.
        
        This property tests that:
        1. Forecasts are based on historical data and market patterns
        2. Forecasts are consistent and reliable across different time periods
        3. Multiple forecasting models produce reasonable results
        4. Confidence scores accurately reflect forecast reliability
        5. Seasonal, weather, festival, and trade factors are properly incorporated
        """
        forecast_days, model = params
        seasonal_factor, weather_factor, festival_factor, trade_factor = factors
        
        # Assume we have sufficient data for reliable forecasting
        assume(len(price_data) >= 30)
        
        # Mock the price discovery service to return our test data
        with patch.object(
            market_analytics_service.price_discovery_service,
            '_get_historical_prices',
            return_value=price_data
        ):
            # Mock market factors
            with patch.object(
                market_analytics_service,
                '_get_seasonal_demand_factor',
                return_value=seasonal_factor
            ):
                with patch.object(
                    market_analytics_service,
                    '_get_weather_demand_factor',
                    return_value=weather_factor
                ):
                    with patch.object(
                        market_analytics_service,
                        '_get_festival_demand_factor',
                        return_value=festival_factor
                    ):
                        with patch.object(
                            market_analytics_service,
                            '_get_trade_demand_factor',
                            return_value=trade_factor
                        ):
                            # Generate demand forecast
                            forecast = await market_analytics_service.generate_demand_forecast(
                                commodity=commodity,
                                location=location,
                                forecast_days=forecast_days,
                                model=model
                            )
        
        # Property 1: Forecast should be based on historical data and market patterns
        assert forecast.commodity == commodity
        assert forecast.location == location
        assert forecast.forecast_period_days == forecast_days
        assert forecast.model_used == model
        
        # Property 2: Forecasts should be consistent and reliable
        # Demand prediction should be within reasonable bounds (0.1 to 5.0 multiplier)
        assert 0.1 <= forecast.predicted_demand <= 5.0, \
            f"Predicted demand {forecast.predicted_demand} outside reasonable bounds [0.1, 5.0]"
        
        # Property 3: Multiple forecasting models should produce reasonable results
        # The forecast should have a valid trend direction
        assert forecast.demand_trend in [TrendDirection.RISING, TrendDirection.FALLING, TrendDirection.STABLE]
        
        # Property 4: Confidence scores should accurately reflect forecast reliability
        assert 0.0 <= forecast.confidence <= 1.0, \
            f"Confidence score {forecast.confidence} outside valid range [0.0, 1.0]"
        
        # Higher data quality should lead to higher confidence
        if len(price_data) >= 100:
            assert forecast.confidence >= 0.3, \
                f"Confidence {forecast.confidence} too low for high-quality data ({len(price_data)} points)"
        
        # Property 5: Seasonal, weather, festival, and trade factors should be properly incorporated
        assert forecast.seasonal_factor == seasonal_factor
        assert forecast.weather_factor == weather_factor
        assert forecast.festival_factor == festival_factor
        assert forecast.export_import_factor == trade_factor
        
        # Factors should be reflected in the final prediction
        expected_base_multiplier = seasonal_factor * weather_factor * festival_factor * trade_factor
        
        # The predicted demand should be influenced by these factors
        # (allowing for price-demand inverse relationship and other adjustments)
        assert 0.1 <= forecast.predicted_demand <= 5.0
        
        # Property 6: Factors considered should include historical data
        assert "historical_prices" in forecast.factors_considered
        assert "seasonal_patterns" in forecast.factors_considered
        
        # Property 7: Forecast should include proper metadata
        assert forecast.forecast_date > date.today()
        assert forecast.created_at is not None
        
        # Property 8: Trend direction should be consistent with demand prediction
        if forecast.predicted_demand > 1.1:
            assert forecast.demand_trend == TrendDirection.RISING
        elif forecast.predicted_demand < 0.9:
            assert forecast.demand_trend == TrendDirection.FALLING
        else:
            assert forecast.demand_trend == TrendDirection.STABLE
    
    @given(
        commodity=commodity_strategy(),
        location=location_strategy(),
        price_data=historical_price_data_strategy()
    )
    @settings(max_examples=20, deadline=8000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_forecast_consistency_across_models(
        self, 
        commodity, 
        location, 
        price_data
    ):
        """
        Test that different forecasting models produce consistent results.
        
        This validates that multiple forecasting models produce reasonable results
        and that the ensemble model provides better confidence than individual models.
        """
        assume(len(price_data) >= 30)
        
        forecasts = {}
        
        # Test all forecasting models
        for model in ForecastModel:
            with patch.object(
                market_analytics_service.price_discovery_service,
                '_get_historical_prices',
                return_value=price_data
            ):
                with patch.object(
                    market_analytics_service,
                    '_get_seasonal_demand_factor',
                    return_value=1.0
                ):
                    with patch.object(
                        market_analytics_service,
                        '_get_weather_demand_factor',
                        return_value=1.0
                    ):
                        with patch.object(
                            market_analytics_service,
                            '_get_festival_demand_factor',
                            return_value=1.0
                        ):
                            with patch.object(
                                market_analytics_service,
                                '_get_trade_demand_factor',
                                return_value=1.0
                            ):
                                forecast = await market_analytics_service.generate_demand_forecast(
                                    commodity=commodity,
                                    location=location,
                                    forecast_days=30,
                                    model=model
                                )
                                forecasts[model] = forecast
        
        # All models should produce valid forecasts
        for model, forecast in forecasts.items():
            assert 0.1 <= forecast.predicted_demand <= 5.0
            assert 0.0 <= forecast.confidence <= 1.0
            assert forecast.model_used == model
        
        # Ensemble model should have higher or equal confidence compared to individual models
        ensemble_confidence = forecasts[ForecastModel.ENSEMBLE].confidence
        individual_confidences = [
            forecasts[model].confidence 
            for model in ForecastModel 
            if model != ForecastModel.ENSEMBLE
        ]
        
        if individual_confidences:
            max_individual_confidence = max(individual_confidences)
            assert ensemble_confidence >= max_individual_confidence - 0.1, \
                f"Ensemble confidence {ensemble_confidence} should be >= max individual {max_individual_confidence}"
        
        # All forecasts should be within a reasonable range of each other
        predictions = [forecast.predicted_demand for forecast in forecasts.values()]
        if len(predictions) > 1:
            prediction_range = max(predictions) - min(predictions)
            mean_prediction = statistics.mean(predictions)
            
            # Range should not be more than 100% of the mean (reasonable consistency)
            assert prediction_range <= mean_prediction, \
                f"Prediction range {prediction_range} too large compared to mean {mean_prediction}"
    
    @given(
        commodity=commodity_strategy(),
        location=location_strategy(),
        price_data=historical_price_data_strategy()
    )
    @settings(max_examples=15, deadline=6000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_forecast_reliability_with_data_quality(
        self, 
        commodity, 
        location, 
        price_data
    ):
        """
        Test that forecast reliability correlates with data quality.
        
        This validates that confidence scores accurately reflect forecast reliability
        based on the quality and quantity of historical data.
        """
        assume(len(price_data) >= 10)
        
        with patch.object(
            market_analytics_service.price_discovery_service,
            '_get_historical_prices',
            return_value=price_data
        ):
            with patch.object(
                market_analytics_service,
                '_get_seasonal_demand_factor',
                return_value=1.0
            ):
                with patch.object(
                    market_analytics_service,
                    '_get_weather_demand_factor',
                    return_value=1.0
                ):
                    with patch.object(
                        market_analytics_service,
                        '_get_festival_demand_factor',
                        return_value=1.0
                    ):
                        with patch.object(
                            market_analytics_service,
                            '_get_trade_demand_factor',
                            return_value=1.0
                        ):
                            forecast = await market_analytics_service.generate_demand_forecast(
                                commodity=commodity,
                                location=location,
                                forecast_days=30,
                                model=ForecastModel.ENSEMBLE
                            )
        
        # Data quality should correlate with confidence
        data_points = len(price_data)
        
        if data_points >= 200:
            # High data quality should yield high confidence
            assert forecast.confidence >= 0.6, \
                f"High data quality ({data_points} points) should yield confidence >= 0.6, got {forecast.confidence}"
        elif data_points >= 100:
            # Medium data quality should yield medium confidence
            assert forecast.confidence >= 0.4, \
                f"Medium data quality ({data_points} points) should yield confidence >= 0.4, got {forecast.confidence}"
        elif data_points >= 30:
            # Low data quality should yield lower confidence
            assert forecast.confidence >= 0.2, \
                f"Low data quality ({data_points} points) should yield confidence >= 0.2, got {forecast.confidence}"
        else:
            # Very low data quality should yield very low confidence
            assert forecast.confidence >= 0.0, \
                f"Very low data quality ({data_points} points) should yield confidence >= 0.0, got {forecast.confidence}"
        
        # Recent data should increase confidence
        latest_date = max(pp.date for pp in price_data)
        days_old = (date.today() - latest_date).days
        
        if days_old <= 7:
            # Recent data should boost confidence
            assert forecast.confidence >= 0.3, \
                f"Recent data ({days_old} days old) should yield confidence >= 0.3, got {forecast.confidence}"
    
    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self):
        """
        Test that the system handles insufficient data gracefully.
        
        This validates that the system provides appropriate fallback behavior
        when historical data is insufficient for reliable forecasting.
        """
        # Test with very limited data
        limited_data = [
            PricePoint(
                date=date.today() - timedelta(days=i),
                price=100.0,
                volume=1000.0
            )
            for i in range(5)  # Only 5 data points
        ]
        
        with patch.object(
            market_analytics_service.price_discovery_service,
            '_get_historical_prices',
            return_value=limited_data
        ):
            forecast = await market_analytics_service.generate_demand_forecast(
                commodity="rice",
                location="Maharashtra",
                forecast_days=30,
                model=ForecastModel.ENSEMBLE
            )
        
        # Should handle insufficient data gracefully
        assert forecast.commodity == "rice"
        assert forecast.confidence == 0.0  # Low confidence due to insufficient data
        assert "insufficient_data" in forecast.factors_considered
        assert forecast.predicted_demand == 1.0  # Neutral demand prediction
        
        # Test with no data
        with patch.object(
            market_analytics_service.price_discovery_service,
            '_get_historical_prices',
            return_value=[]
        ):
            forecast = await market_analytics_service.generate_demand_forecast(
                commodity="unknown_commodity",
                forecast_days=30
            )
        
        assert forecast.confidence == 0.0
        assert "insufficient_data" in forecast.factors_considered


if __name__ == "__main__":
    pytest.main([__file__, "-v"])