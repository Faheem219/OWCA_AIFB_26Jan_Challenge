"""
Property-based tests for price analysis and trending system.
**Validates: Requirements 2.3, 2.4**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import date, datetime, timedelta
import statistics
from typing import List

from app.services.price_discovery_service import price_discovery_service
from app.models.price import PricePoint, PriceForecast
from app.models.common import TrendDirection


# Custom strategies for generating test data
@st.composite
def price_point_list(draw, min_size=10, max_size=100):
    """Generate a list of realistic price points."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    base_date = date.today() - timedelta(days=size)
    base_price = draw(st.floats(min_value=500, max_value=5000))
    
    price_points = []
    for i in range(size):
        # Add some realistic variation
        price_variation = draw(st.floats(min_value=-0.1, max_value=0.1))
        price = max(100, base_price * (1 + price_variation))
        
        price_points.append(PricePoint(
            date=base_date + timedelta(days=i),
            price=price,
            volume=draw(st.floats(min_value=10, max_value=1000))
        ))
        
        # Update base price for next iteration (random walk)
        base_price = price
    
    return price_points


@st.composite
def commodity_name(draw):
    """Generate realistic commodity names."""
    commodities = ["Rice", "Wheat", "Onion", "Potato", "Tomato", "Cotton", "Sugar", "Turmeric"]
    return draw(st.sampled_from(commodities))


class TestPriceAnalysisProperties:
    """Property-based tests for price analysis system."""
    
    @given(price_points=price_point_list(min_size=30))
    @settings(max_examples=50, deadline=5000)
    def test_trend_direction_consistency(self, price_points: List[PricePoint]):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any list of price points, trend direction calculation should be consistent
        and return a valid TrendDirection enum value.
        """
        assume(len(price_points) >= 2)
        
        trend_direction = price_discovery_service._calculate_trend_direction(price_points)
        
        # Property: Result should always be a valid TrendDirection
        assert isinstance(trend_direction, TrendDirection)
        assert trend_direction in [TrendDirection.RISING, TrendDirection.FALLING, 
                                 TrendDirection.STABLE, TrendDirection.VOLATILE]
        
        # Property: Same input should produce same output (deterministic)
        trend_direction_2 = price_discovery_service._calculate_trend_direction(price_points)
        assert trend_direction == trend_direction_2
    
    @given(price_points=price_point_list(min_size=10))
    @settings(max_examples=50, deadline=5000)
    def test_volatility_bounds(self, price_points: List[PricePoint]):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        For any price data, volatility index should always be between 0 and 1.
        """
        assume(len(price_points) >= 2)
        
        volatility = price_discovery_service._calculate_volatility(price_points)
        
        # Property: Volatility should be bounded between 0 and 1
        assert 0 <= volatility <= 1
        
        # Property: Identical prices should have zero volatility
        identical_prices = [PricePoint(date=date.today() - timedelta(days=i), price=1000) 
                           for i in range(10)]
        zero_volatility = price_discovery_service._calculate_volatility(identical_prices)
        assert zero_volatility == 0.0
    
    @given(
        price_points=price_point_list(min_size=30),
        commodity=commodity_name(),
        forecast_days=st.integers(min_value=1, max_value=365)
    )
    @settings(max_examples=30, deadline=10000)
    async def test_prediction_model_properties(self, price_points: List[PricePoint], 
                                             commodity: str, forecast_days: int):
        """
        **Property 11: Seasonal Price Prediction**
        **Validates: Requirements 2.4**
        
        For any valid historical data, prediction models should produce valid forecasts
        with positive prices and bounded confidence intervals.
        """
        assume(len(price_points) >= 30)
        assume(all(pp.price > 0 for pp in price_points))
        
        try:
            # Test seasonal ARIMA prediction
            arima_forecast = await price_discovery_service._seasonal_arima_predict(
                price_points, forecast_days, commodity
            )
            
            # Property: Predicted price should be positive
            assert arima_forecast.predicted_price > 0
            
            # Property: Confidence should be between 0 and 1
            assert 0 <= arima_forecast.confidence <= 1
            
            # Property: Confidence interval should be valid
            assert arima_forecast.confidence_interval_lower <= arima_forecast.predicted_price
            assert arima_forecast.predicted_price <= arima_forecast.confidence_interval_upper
            assert arima_forecast.confidence_interval_lower >= 0
            
            # Property: Forecast should have correct metadata
            assert arima_forecast.commodity == commodity
            assert arima_forecast.model_used == "seasonal_arima"
            assert len(arima_forecast.factors_considered) > 0
            
        except ValueError as e:
            # Expected for insufficient data
            assert "Insufficient data" in str(e)
    
    @given(
        price_points=price_point_list(min_size=10),
        commodity=commodity_name(),
        forecast_days=st.integers(min_value=1, max_value=90)
    )
    @settings(max_examples=30, deadline=10000)
    async def test_moving_average_prediction_properties(self, price_points: List[PricePoint],
                                                       commodity: str, forecast_days: int):
        """
        **Property 11: Seasonal Price Prediction**
        **Validates: Requirements 2.4**
        
        Moving average predictions should be reasonable relative to recent prices.
        """
        assume(len(price_points) >= 5)
        assume(all(pp.price > 0 for pp in price_points))
        
        try:
            ma_forecast = await price_discovery_service._moving_average_predict(
                price_points, forecast_days, commodity
            )
            
            # Property: Prediction should be reasonably close to recent prices
            recent_prices = [pp.price for pp in price_points[-10:]]
            recent_avg = statistics.mean(recent_prices)
            
            # Prediction shouldn't be more than 50% different from recent average
            price_ratio = ma_forecast.predicted_price / recent_avg
            assert 0.5 <= price_ratio <= 2.0
            
            # Property: Model metadata should be correct
            assert ma_forecast.model_used == "moving_average"
            assert "moving_average" in ma_forecast.factors_considered
            
        except ValueError as e:
            assert "Insufficient data" in str(e)
    
    @given(price_points=price_point_list(min_size=20))
    @settings(max_examples=30, deadline=5000)
    def test_anomaly_detection_properties(self, price_points: List[PricePoint]):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        Anomaly detection should identify outliers correctly and consistently.
        """
        assume(len(price_points) >= 10)
        
        # Add a clear anomaly
        prices = [pp.price for pp in price_points]
        mean_price = statistics.mean(prices)
        std_price = statistics.stdev(prices) if len(prices) > 1 else 0
        
        # Add extreme outlier
        anomalous_points = price_points.copy()
        anomalous_points.append(PricePoint(
            date=date.today(),
            price=mean_price + 5 * std_price,  # 5 standard deviations above mean
            volume=100
        ))
        
        anomalies = price_discovery_service._detect_price_anomalies(anomalous_points)
        
        # Property: Should detect the extreme outlier we added
        assert len(anomalies) >= 1
        
        # Property: All detected anomalies should have valid structure
        for anomaly in anomalies:
            assert "date" in anomaly
            assert "price" in anomaly
            assert "z_score" in anomaly
            assert "type" in anomaly
            assert "severity" in anomaly
            
            # Property: Z-score should be above threshold (2.0)
            assert anomaly["z_score"] > 2.0
            
            # Property: Type should be valid
            assert anomaly["type"] in ["spike", "drop"]
            
            # Property: Severity should be valid
            assert anomaly["severity"] in ["moderate", "extreme"]
    
    @given(price_points=price_point_list(min_size=20))
    @settings(max_examples=30, deadline=5000)
    def test_support_resistance_properties(self, price_points: List[PricePoint]):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        Support and resistance levels should be logically ordered and meaningful.
        """
        assume(len(price_points) >= 20)
        
        prices = [pp.price for pp in price_points]
        support_resistance = price_discovery_service._calculate_support_resistance(prices)
        
        # Property: Should have correct structure
        assert "support_levels" in support_resistance
        assert "resistance_levels" in support_resistance
        assert "current_price" in support_resistance
        assert "position" in support_resistance
        
        # Property: Support levels should be lower than resistance levels
        support_levels = support_resistance["support_levels"]
        resistance_levels = support_resistance["resistance_levels"]
        
        assert len(support_levels) == 2
        assert len(resistance_levels) == 2
        
        # All support levels should be less than all resistance levels
        for support in support_levels:
            for resistance in resistance_levels:
                assert support <= resistance
        
        # Property: Levels should be within the price range
        min_price = min(prices)
        max_price = max(prices)
        
        for support in support_levels:
            assert min_price <= support <= max_price
        
        for resistance in resistance_levels:
            assert min_price <= resistance <= max_price
        
        # Property: Position should be valid
        assert support_resistance["position"] in ["above_resistance", "below_support", "in_range"]
    
    @given(
        prices=st.lists(
            st.floats(min_value=100, max_value=10000), 
            min_size=15, 
            max_size=100
        )
    )
    @settings(max_examples=30, deadline=5000)
    def test_rsi_calculation_properties(self, prices: List[float]):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        RSI calculation should always return values between 0 and 100.
        """
        assume(len(prices) >= 15)
        assume(all(p > 0 for p in prices))
        
        rsi = price_discovery_service._calculate_simple_rsi(prices, period=14)
        
        if rsi is not None:
            # Property: RSI should be between 0 and 100
            assert 0 <= rsi <= 100
            
            # Property: All increasing prices should give RSI = 100
            increasing_prices = [100 + i for i in range(15)]
            rsi_increasing = price_discovery_service._calculate_simple_rsi(increasing_prices, period=14)
            assert rsi_increasing == 100
    
    @given(
        price_points=price_point_list(min_size=50),
        analysis_period=st.integers(min_value=30, max_value=365)
    )
    @settings(max_examples=20, deadline=15000)
    async def test_advanced_analysis_completeness(self, price_points: List[PricePoint], 
                                                 analysis_period: int):
        """
        **Property 8: Historical Data Completeness**
        **Validates: Requirements 2.3**
        
        Advanced trend analysis should provide complete analysis for sufficient data.
        """
        assume(len(price_points) >= 30)
        
        # Mock the historical data retrieval
        with pytest.mock.patch.object(
            price_discovery_service, 
            '_get_historical_prices',
            return_value=price_points
        ):
            analysis = await price_discovery_service.get_advanced_trend_analysis(
                commodity="Rice",
                location="Test",
                analysis_period_days=analysis_period
            )
        
        # Property: Should not have error for sufficient data
        assert "error" not in analysis
        
        # Property: Should have all required analysis components
        required_components = [
            "commodity", "data_points", "price_statistics", "trend_analysis",
            "seasonal_patterns", "volatility_analysis", "anomalies",
            "support_resistance", "moving_averages", "momentum_indicators"
        ]
        
        for component in required_components:
            assert component in analysis
        
        # Property: Data points should match input
        assert analysis["data_points"] == len(price_points)
        
        # Property: Price statistics should be valid
        stats = analysis["price_statistics"]
        prices = [pp.price for pp in price_points]
        
        assert abs(stats["mean"] - statistics.mean(prices)) < 0.01
        assert abs(stats["min"] - min(prices)) < 0.01
        assert abs(stats["max"] - max(prices)) < 0.01