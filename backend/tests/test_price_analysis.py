"""
Unit tests for price analysis and trending system.
"""
import pytest
from datetime import date, datetime, timedelta
from unittest.mock import AsyncMock, patch
import statistics

from app.services.price_discovery_service import price_discovery_service
from app.models.price import PricePoint, PriceData, Location, PriceSource, MarketType, QualityGrade


class TestPriceAnalysisSystem:
    """Test suite for price analysis and trending system."""
    
    @pytest.fixture
    def sample_price_points(self):
        """Generate sample price points for testing."""
        base_date = date.today() - timedelta(days=100)
        price_points = []
        
        for i in range(100):
            # Generate realistic price data with trend and seasonality
            base_price = 2000
            trend = i * 2  # Upward trend
            seasonal = 100 * (1 + 0.3 * (i % 30) / 30)  # Monthly seasonality
            noise = (i % 7) * 10  # Weekly noise
            
            price = base_price + trend + seasonal + noise
            
            price_points.append(PricePoint(
                date=base_date + timedelta(days=i),
                price=price,
                volume=100 + (i % 20)
            ))
        
        return price_points
    
    @pytest.fixture
    def sample_price_data(self):
        """Generate sample PriceData objects for testing."""
        location = Location(
            state="Maharashtra",
            district="Mumbai",
            market_name="APMC Market"
        )
        
        price_data = []
        for i in range(10):
            price_data.append(PriceData(
                commodity="Rice",
                market_name="APMC Market",
                location=location,
                price_min=1800 + i * 10,
                price_max=2200 + i * 10,
                price_modal=2000 + i * 10,
                quality_grade=QualityGrade.STANDARD,
                unit="Quintal",
                date=date.today() - timedelta(days=i),
                source=PriceSource.AGMARKNET,
                market_type=MarketType.MANDI
            ))
        
        return price_data
    async def test_calculate_trend_direction(self, sample_price_points):
        """Test trend direction calculation."""
        # Test upward trend
        trend_direction = price_discovery_service._calculate_trend_direction(sample_price_points)
        assert trend_direction.value in ["rising", "falling", "stable", "volatile"]
        
        # Test with stable prices
        stable_points = [PricePoint(date=date.today() - timedelta(days=i), price=2000) 
                        for i in range(10)]
        stable_trend = price_discovery_service._calculate_trend_direction(stable_points)
        assert stable_trend.value == "stable"
        
        # Test with insufficient data
        single_point = [PricePoint(date=date.today(), price=2000)]
        single_trend = price_discovery_service._calculate_trend_direction(single_point)
        assert single_trend.value == "stable"
    
    async def test_calculate_volatility(self, sample_price_points):
        """Test volatility calculation."""
        volatility = price_discovery_service._calculate_volatility(sample_price_points)
        assert 0 <= volatility <= 1
        
        # Test with stable prices (low volatility)
        stable_points = [PricePoint(date=date.today() - timedelta(days=i), price=2000) 
                        for i in range(10)]
        stable_volatility = price_discovery_service._calculate_volatility(stable_points)
        assert stable_volatility < 0.1
        
        # Test with highly volatile prices
        volatile_prices = [2000, 1000, 3000, 500, 4000]
        volatile_points = [PricePoint(date=date.today() - timedelta(days=i), price=price) 
                          for i, price in enumerate(volatile_prices)]
        high_volatility = price_discovery_service._calculate_volatility(volatile_points)
        assert high_volatility > 0.2
    
    async def test_seasonal_arima_predict(self, sample_price_points):
        """Test seasonal ARIMA prediction model."""
        forecast = await price_discovery_service._seasonal_arima_predict(
            sample_price_points, 30, "Rice"
        )
        
        assert forecast.commodity == "Rice"
        assert forecast.predicted_price > 0
        assert 0 <= forecast.confidence <= 1
        assert forecast.confidence_interval_lower <= forecast.predicted_price
        assert forecast.predicted_price <= forecast.confidence_interval_upper
        assert forecast.model_used == "seasonal_arima"
        
        # Test with insufficient data
        with pytest.raises(ValueError, match="Insufficient data"):
            await price_discovery_service._seasonal_arima_predict(
                sample_price_points[:5], 30, "Rice"
            )
    
    async def test_moving_average_predict(self, sample_price_points):
        """Test moving average prediction model."""
        forecast = await price_discovery_service._moving_average_predict(
            sample_price_points, 30, "Rice"
        )
        
        assert forecast.commodity == "Rice"
        assert forecast.predicted_price > 0
        assert 0 <= forecast.confidence <= 1
        assert forecast.model_used == "moving_average"
        assert "moving_average" in forecast.factors_considered
        
        # Test with insufficient data
        with pytest.raises(ValueError, match="Insufficient data"):
            await price_discovery_service._moving_average_predict(
                sample_price_points[:3], 30, "Rice"
            )
    
    async def test_linear_trend_predict(self, sample_price_points):
        """Test linear trend prediction model."""
        forecast = await price_discovery_service._linear_trend_predict(
            sample_price_points, 30, "Rice"
        )
        
        assert forecast.commodity == "Rice"
        assert forecast.predicted_price > 0
        assert 0 <= forecast.confidence <= 1
        assert forecast.model_used == "linear_trend"
        assert "linear_trend" in forecast.factors_considered
        
        # Test with insufficient data
        with pytest.raises(ValueError, match="Insufficient data"):
            await price_discovery_service._linear_trend_predict(
                sample_price_points[:2], 30, "Rice"
            )
    @patch('app.services.price_discovery_service.price_discovery_service._get_historical_prices')
    async def test_get_advanced_trend_analysis(self, mock_get_historical, sample_price_points):
        """Test advanced trend analysis."""
        mock_get_historical.return_value = sample_price_points
        
        analysis = await price_discovery_service.get_advanced_trend_analysis(
            commodity="Rice",
            location="Mumbai",
            analysis_period_days=100
        )
        
        assert analysis["commodity"] == "Rice"
        assert analysis["location"] == "Mumbai"
        assert analysis["data_points"] == len(sample_price_points)
        assert "price_statistics" in analysis
        assert "trend_analysis" in analysis
        assert "seasonal_patterns" in analysis
        assert "volatility_analysis" in analysis
        assert "anomalies" in analysis
        assert "support_resistance" in analysis
        assert "moving_averages" in analysis
        assert "momentum_indicators" in analysis
        
        # Check price statistics
        stats = analysis["price_statistics"]
        assert "mean" in stats
        assert "median" in stats
        assert "std_dev" in stats
        assert "min" in stats
        assert "max" in stats
        
        # Test with insufficient data
        mock_get_historical.return_value = sample_price_points[:10]
        analysis_insufficient = await price_discovery_service.get_advanced_trend_analysis(
            commodity="Rice", analysis_period_days=100
        )
        assert "error" in analysis_insufficient
        assert analysis_insufficient["error"] == "insufficient_data"
    
    def test_detect_price_anomalies(self, sample_price_points):
        """Test price anomaly detection."""
        # Add some anomalous prices
        anomalous_points = sample_price_points.copy()
        anomalous_points.append(PricePoint(
            date=date.today(),
            price=5000,  # Anomalously high price
            volume=100
        ))
        anomalous_points.append(PricePoint(
            date=date.today() - timedelta(days=1),
            price=500,   # Anomalously low price
            volume=100
        ))
        
        anomalies = price_discovery_service._detect_price_anomalies(anomalous_points)
        
        assert len(anomalies) >= 2  # Should detect at least the two anomalies we added
        
        for anomaly in anomalies:
            assert "date" in anomaly
            assert "price" in anomaly
            assert "z_score" in anomaly
            assert "type" in anomaly
            assert anomaly["type"] in ["spike", "drop"]
            assert "severity" in anomaly
            assert anomaly["severity"] in ["moderate", "extreme"]
            assert anomaly["z_score"] > 2.0  # Should be above threshold
    
    def test_calculate_support_resistance(self, sample_price_points):
        """Test support and resistance level calculation."""
        prices = [pp.price for pp in sample_price_points]
        support_resistance = price_discovery_service._calculate_support_resistance(prices)
        
        assert "support_levels" in support_resistance
        assert "resistance_levels" in support_resistance
        assert "current_price" in support_resistance
        assert "position" in support_resistance
        
        assert len(support_resistance["support_levels"]) == 2
        assert len(support_resistance["resistance_levels"]) == 2
        assert support_resistance["position"] in ["above_resistance", "below_support", "in_range"]
        
        # Support levels should be lower than resistance levels
        assert all(s < r for s in support_resistance["support_levels"] 
                  for r in support_resistance["resistance_levels"])
    
    def test_calculate_moving_averages(self, sample_price_points):
        """Test moving average calculations."""
        prices = [pp.price for pp in sample_price_points]
        ma_result = price_discovery_service._calculate_moving_averages(prices)
        
        assert "moving_averages" in ma_result
        assert "current_price" in ma_result
        assert "ma_signals" in ma_result
        
        # Should have multiple MA periods
        ma_values = ma_result["moving_averages"]
        assert "ma_5" in ma_values or "ma_10" in ma_values
        
        # Signals should be valid
        for signal in ma_result["ma_signals"].values():
            assert signal in ["bullish", "bearish", "neutral"]
    
    def test_calculate_momentum_indicators(self, sample_price_points):
        """Test momentum indicator calculations."""
        prices = [pp.price for pp in sample_price_points]
        momentum = price_discovery_service._calculate_momentum_indicators(prices)
        
        assert "rate_of_change" in momentum
        assert "rsi" in momentum
        assert "momentum_classification" in momentum
        
        # ROC should have multiple periods
        roc_values = momentum["rate_of_change"]
        assert len(roc_values) > 0
        
        # RSI should be between 0 and 100
        if momentum["rsi"] is not None:
            assert 0 <= momentum["rsi"] <= 100
        
        # Momentum classification should be valid
        assert momentum["momentum_classification"] in [
            "strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"
        ]
    @patch('app.services.price_discovery_service.price_discovery_service._get_historical_prices')
    async def test_ensemble_price_prediction(self, mock_get_historical, sample_price_points):
        """Test ensemble price prediction."""
        mock_get_historical.return_value = sample_price_points
        
        prediction = await price_discovery_service.get_ensemble_price_prediction(
            commodity="Rice",
            forecast_days=30,
            location="Mumbai"
        )
        
        assert prediction["commodity"] == "Rice"
        assert prediction["location"] == "Mumbai"
        assert prediction["forecast_days"] == 30
        assert "ensemble_prediction" in prediction
        assert "individual_predictions" in prediction
        assert "model_comparison" in prediction
        
        # Check ensemble prediction structure
        ensemble = prediction["ensemble_prediction"]
        assert "predicted_price" in ensemble
        assert "confidence" in ensemble
        assert "confidence_interval_lower" in ensemble
        assert "confidence_interval_upper" in ensemble
        assert "model_weights" in ensemble
        
        # Confidence should be between 0 and 1
        assert 0 <= ensemble["confidence"] <= 1
        
        # Confidence interval should be valid
        assert ensemble["confidence_interval_lower"] <= ensemble["predicted_price"]
        assert ensemble["predicted_price"] <= ensemble["confidence_interval_upper"]
        
        # Should have individual model predictions
        individual = prediction["individual_predictions"]
        assert len(individual) > 0
        
        # Test with insufficient data
        mock_get_historical.return_value = sample_price_points[:10]
        prediction_insufficient = await price_discovery_service.get_ensemble_price_prediction(
            commodity="Rice", forecast_days=30
        )
        assert "error" in prediction_insufficient
        assert prediction_insufficient["error"] == "insufficient_data"
    
    def test_calculate_ensemble_prediction(self):
        """Test ensemble prediction calculation."""
        from app.models.price import PriceForecast
        
        # Create mock predictions
        predictions = {
            "model1": PriceForecast(
                commodity="Rice",
                forecast_date=date.today() + timedelta(days=30),
                predicted_price=2000,
                confidence_interval_lower=1900,
                confidence_interval_upper=2100,
                confidence=0.8
            ),
            "model2": PriceForecast(
                commodity="Rice",
                forecast_date=date.today() + timedelta(days=30),
                predicted_price=2100,
                confidence_interval_lower=2000,
                confidence_interval_upper=2200,
                confidence=0.7
            )
        }
        
        weights = {"model1": 0.6, "model2": 0.4}
        
        ensemble = price_discovery_service._calculate_ensemble_prediction(predictions, weights)
        
        assert "predicted_price" in ensemble
        assert "confidence" in ensemble
        assert "model_weights" in ensemble
        
        # Check weighted average calculation
        expected_price = 2000 * 0.6 + 2100 * 0.4
        assert abs(ensemble["predicted_price"] - expected_price) < 0.01
        
        expected_confidence = 0.8 * 0.6 + 0.7 * 0.4
        assert abs(ensemble["confidence"] - expected_confidence) < 0.01
    
    def test_compare_model_predictions(self):
        """Test model prediction comparison."""
        from app.models.price import PriceForecast
        
        predictions = {
            "model1": PriceForecast(
                commodity="Rice",
                forecast_date=date.today() + timedelta(days=30),
                predicted_price=2000,
                confidence_interval_lower=1900,
                confidence_interval_upper=2100,
                confidence=0.8,
                factors_considered=["trend", "seasonal"]
            ),
            "model2": PriceForecast(
                commodity="Rice",
                forecast_date=date.today() + timedelta(days=30),
                predicted_price=2200,
                confidence_interval_lower=2100,
                confidence_interval_upper=2300,
                confidence=0.6,
                factors_considered=["moving_average"]
            )
        }
        
        comparison = price_discovery_service._compare_model_predictions(predictions)
        
        assert "price_range" in comparison
        assert "confidence_range" in comparison
        assert "model_agreement" in comparison
        assert "individual_models" in comparison
        
        # Check price range
        price_range = comparison["price_range"]
        assert price_range["min"] == 2000
        assert price_range["max"] == 2200
        assert price_range["spread"] == 200
        
        # Check individual model details
        individual = comparison["individual_models"]
        assert len(individual) == 2
        assert "model1" in individual
        assert "model2" in individual
        
        for model_data in individual.values():
            assert "predicted_price" in model_data
            assert "confidence" in model_data
            assert "factors_considered" in model_data
            assert "relative_to_ensemble" in model_data
    
    def test_calculate_simple_rsi(self):
        """Test RSI calculation."""
        # Create price series with known pattern
        prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109, 111, 110, 112, 114, 113]
        
        rsi = price_discovery_service._calculate_simple_rsi(prices, period=14)
        
        assert rsi is not None
        assert 0 <= rsi <= 100
        
        # Test with insufficient data
        short_prices = [100, 102, 101]
        rsi_short = price_discovery_service._calculate_simple_rsi(short_prices, period=14)
        assert rsi_short is None
        
        # Test with all gains (should return 100)
        all_gains = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114]
        rsi_gains = price_discovery_service._calculate_simple_rsi(all_gains, period=14)
        assert rsi_gains == 100