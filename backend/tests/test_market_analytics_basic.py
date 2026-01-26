"""
Basic tests for market analytics functionality.
"""
import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from app.services.market_analytics_service import market_analytics_service
from app.models.market_analytics import (
    ForecastModel, WeatherCondition, AlertSeverity
)
from app.models.price import PricePoint


class TestMarketAnalyticsBasic:
    """Basic tests for market analytics service."""
    
    @pytest.mark.asyncio
    async def test_demand_forecast_basic(self):
        """Test basic demand forecasting functionality."""
        # Mock price data
        mock_price_points = [
            PricePoint(date=date.today() - timedelta(days=i), price=100 + i, volume=1000)
            for i in range(30, 0, -1)
        ]
        
        with patch.object(
            market_analytics_service.price_discovery_service,
            '_get_historical_prices',
            return_value=mock_price_points
        ):
            with patch.object(
                market_analytics_service,
                '_get_seasonal_demand_factor',
                return_value=1.1
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
                                commodity="rice",
                                location="Maharashtra",
                                forecast_days=30,
                                model=ForecastModel.ENSEMBLE
                            )
        
        assert forecast.commodity == "rice"
        assert forecast.location == "Maharashtra"
        assert forecast.forecast_period_days == 30
        assert forecast.model_used == ForecastModel.ENSEMBLE
        assert 0 <= forecast.confidence <= 1
        assert forecast.seasonal_factor == 1.1
        assert len(forecast.factors_considered) > 0
    
    @pytest.mark.asyncio
    async def test_weather_impact_prediction(self):
        """Test weather impact prediction."""
        with patch.object(
            market_analytics_service,
            '_get_weather_historical_precedents',
            return_value=[{
                "weather_condition": "drought",
                "price_impact_percentage": 20.0,
                "year": 2023
            }]
        ):
            prediction = await market_analytics_service.predict_weather_impact(
                commodity="wheat",
                weather_condition=WeatherCondition.DROUGHT,
                affected_regions=["Punjab", "Haryana"],
                impact_duration_days=14
            )
        
        assert prediction.commodity == "wheat"
        assert prediction.weather_condition == WeatherCondition.DROUGHT
        assert "Punjab" in prediction.affected_regions
        assert "Haryana" in prediction.affected_regions
        assert prediction.impact_duration_days == 14
        assert prediction.price_impact_percentage > 0
        assert 0 <= prediction.confidence <= 1
        assert len(prediction.mitigation_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_seasonal_alerts_generation(self):
        """Test seasonal alerts generation."""
        # Mock upcoming festivals
        mock_festivals = []
        
        with patch.object(
            market_analytics_service,
            '_get_upcoming_festivals',
            return_value=mock_festivals
        ):
            with patch.object(
                market_analytics_service,
                '_generate_seasonal_pattern_alerts',
                return_value=[]
            ):
                alerts = await market_analytics_service.generate_seasonal_alerts(
                    commodity="sugar",
                    location="Maharashtra",
                    days_ahead=30
                )
        
        assert isinstance(alerts, list)
        # With no festivals, should return empty list
        assert len(alerts) == 0
    
    @pytest.mark.asyncio
    async def test_export_import_influence_analysis(self):
        """Test export-import influence analysis."""
        with patch.object(
            market_analytics_service.price_discovery_service,
            'get_current_prices',
            return_value=[
                type('MockPrice', (), {
                    'price_modal': 500.0,
                    'market_name': 'Test Market'
                })()
            ]
        ):
            with patch.object(
                market_analytics_service,
                '_get_international_price',
                return_value=450.0
            ):
                with patch.object(
                    market_analytics_service,
                    '_get_trade_balance',
                    return_value=5000.0
                ):
                    with patch.object(
                        market_analytics_service,
                        '_calculate_trade_influence_factor',
                        return_value=0.6
                    ):
                        with patch.object(
                            market_analytics_service,
                            '_get_key_trading_partners',
                            return_value=[]
                        ):
                            with patch.object(
                                market_analytics_service,
                                '_analyze_trade_policy_impact',
                                return_value="Moderate policy impact"
                            ):
                                influence = await market_analytics_service.analyze_export_import_influence(
                                    commodity="rice",
                                    analysis_period_days=30
                                )
        
        assert influence.commodity == "rice"
        assert influence.domestic_price == 500.0
        assert influence.international_price == 450.0
        assert influence.price_differential == 50.0
        assert influence.price_differential_percentage > 0
        assert influence.trade_balance == 5000.0
        assert influence.influence_factor == 0.6
        assert len(influence.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_analytics(self):
        """Test comprehensive analytics generation."""
        # Create proper mock objects that match the expected models
        from app.models.market_analytics import DemandForecast, ExportImportInfluence
        from app.models.common import TrendDirection
        from datetime import date
        
        mock_demand_forecast = DemandForecast(
            commodity="wheat",
            forecast_date=date.today(),
            forecast_period_days=30,
            predicted_demand=1.2,
            confidence=0.8,
            demand_trend=TrendDirection.RISING,
            model_used=ForecastModel.ENSEMBLE,
            factors_considered=["historical_data"]
        )
        
        mock_trade_influence = ExportImportInfluence(
            commodity="wheat",
            analysis_date=date.today(),
            domestic_price=500.0,
            international_price=450.0,
            price_differential=50.0,
            price_differential_percentage=11.1,
            trade_balance=1000.0,
            influence_factor=0.6,
            arbitrage_opportunity="none",
            key_trading_partners=[],
            recommendations=[]
        )
        
        with patch.object(
            market_analytics_service,
            'generate_demand_forecast',
            return_value=mock_demand_forecast
        ):
            with patch.object(
                market_analytics_service,
                '_get_active_weather_predictions',
                return_value=[]
            ):
                with patch.object(
                    market_analytics_service,
                    'generate_seasonal_alerts',
                    return_value=[]
                ):
                    with patch.object(
                        market_analytics_service,
                        'analyze_export_import_influence',
                        return_value=mock_trade_influence
                    ):
                        analytics = await market_analytics_service.generate_comprehensive_analytics(
                            commodity="wheat",
                            location="Punjab",
                            analysis_period_days=30
                        )
        
        assert analytics.commodity == "wheat"
        assert analytics.location == "Punjab"
        assert analytics.analysis_period_days == 30
        assert analytics.demand_forecast is not None
        assert analytics.overall_market_sentiment in ["bullish", "bearish", "neutral"]
        assert analytics.risk_assessment in ["low", "medium", "high"]
        assert 0 <= analytics.confidence_score <= 1
        assert isinstance(analytics.trading_recommendations, list)
        assert isinstance(analytics.risk_mitigation_strategies, list)
    
    def test_forecast_confidence_calculation(self):
        """Test forecast confidence calculation."""
        # Mock price points
        mock_price_points = [
            PricePoint(date=date.today() - timedelta(days=i), price=100, volume=1000)
            for i in range(50)
        ]
        
        confidence = market_analytics_service._calculate_forecast_confidence(
            price_points=mock_price_points,
            model=ForecastModel.ENSEMBLE,
            commodity="rice",
            location="Maharashtra"
        )
        
        assert 0 <= confidence <= 1
        assert confidence > 0.5  # Should be reasonably confident with 50 data points
    
    def test_linear_trend_calculation(self):
        """Test linear trend calculation."""
        # Upward trending prices
        upward_prices = [100 + i for i in range(10)]
        upward_trend = market_analytics_service._calculate_linear_trend(upward_prices)
        assert upward_trend > 0
        
        # Downward trending prices
        downward_prices = [100 - i for i in range(10)]
        downward_trend = market_analytics_service._calculate_linear_trend(downward_prices)
        assert downward_trend < 0
        
        # Flat prices
        flat_prices = [100] * 10
        flat_trend = market_analytics_service._calculate_linear_trend(flat_prices)
        assert abs(flat_trend) < 0.1  # Should be close to zero
    
    def test_weather_mitigation_suggestions(self):
        """Test weather mitigation suggestions generation."""
        # Test drought suggestions
        drought_suggestions = market_analytics_service._generate_weather_mitigation_suggestions(
            commodity="wheat",
            weather_condition=WeatherCondition.DROUGHT,
            price_impact_percentage=25.0
        )
        
        assert len(drought_suggestions) > 0
        assert any("water" in suggestion.lower() for suggestion in drought_suggestions)
        assert any("hedging" in suggestion.lower() for suggestion in drought_suggestions)
        
        # Test flood suggestions
        flood_suggestions = market_analytics_service._generate_weather_mitigation_suggestions(
            commodity="rice",
            weather_condition=WeatherCondition.FLOOD,
            price_impact_percentage=20.0
        )
        
        assert len(flood_suggestions) > 0
        assert any("transportation" in suggestion.lower() for suggestion in flood_suggestions)
    
    def test_trade_recommendations_generation(self):
        """Test trade recommendations generation."""
        recommendations = market_analytics_service._generate_trade_recommendations(
            commodity="rice",
            price_differential_percentage=15.0,
            trade_balance=10000.0,
            arbitrage_opportunity="export"
        )
        
        assert len(recommendations) > 0
        assert any("export" in rec.lower() for rec in recommendations)
        assert any("higher" in rec.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_insufficient_data_handling(self):
        """Test handling of insufficient data scenarios."""
        # Mock insufficient price data
        with patch.object(
            market_analytics_service.price_discovery_service,
            '_get_historical_prices',
            return_value=[]  # No data
        ):
            forecast = await market_analytics_service.generate_demand_forecast(
                commodity="unknown_commodity",
                forecast_days=30
            )
        
        assert forecast.commodity == "unknown_commodity"
        assert forecast.confidence == 0.0
        assert "insufficient_data" in forecast.factors_considered
        assert forecast.predicted_demand == 1.0  # Default neutral demand