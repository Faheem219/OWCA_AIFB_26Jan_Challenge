"""
Market Analytics and Forecasting Service.

Implements demand forecasting algorithms, weather impact prediction,
seasonal and festival demand alerts, and export-import price influence tracking.
"""
import asyncio
import logging
import statistics
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
import json
import math

from app.core.config import settings
from app.models.market_analytics import (
    DemandForecast, WeatherImpactPrediction, SeasonalDemandAlert,
    ExportImportInfluence, MarketAnalytics, FestivalCalendar,
    WeatherAlert, MarketIntelligenceReport, AnalyticsConfiguration,
    ForecastModel, WeatherCondition, FestivalType, TradeDirection,
    AlertSeverity, ExportImportData, HistoricalAccuracy
)
from app.models.price import PricePoint, SeasonalFactor
from app.models.common import TrendDirection
from app.services.price_discovery_service import price_discovery_service
from app.db.mongodb import get_database
from app.db.redis import get_redis

logger = logging.getLogger(__name__)


class MarketAnalyticsService:
    """Service for market analytics and forecasting."""
    
    def __init__(self):
        self.cache_ttl = 3600  # 1 hour cache for analytics
        self.price_discovery_service = price_discovery_service  # Add reference to price service
        self.forecast_models = {
            ForecastModel.ARIMA: self._arima_forecast,
            ForecastModel.LINEAR_REGRESSION: self._linear_regression_forecast,
            ForecastModel.MOVING_AVERAGE: self._moving_average_forecast,
            ForecastModel.SEASONAL_DECOMPOSITION: self._seasonal_decomposition_forecast,
            ForecastModel.ENSEMBLE: self._ensemble_forecast
        }
        
        # Weather impact coefficients (commodity -> weather_condition -> impact_factor)
        self.weather_impact_coefficients = {
            "rice": {
                WeatherCondition.DROUGHT: 0.25,
                WeatherCondition.FLOOD: 0.15,
                WeatherCondition.EXCESSIVE_RAIN: 0.10,
                WeatherCondition.CYCLONE: 0.30,
                WeatherCondition.NORMAL: 0.0
            },
            "wheat": {
                WeatherCondition.DROUGHT: 0.30,
                WeatherCondition.EXCESSIVE_RAIN: 0.12,
                WeatherCondition.HAILSTORM: 0.20,
                WeatherCondition.FROST: 0.15,
                WeatherCondition.NORMAL: 0.0
            },
            "onion": {
                WeatherCondition.EXCESSIVE_RAIN: 0.35,
                WeatherCondition.DROUGHT: 0.20,
                WeatherCondition.FLOOD: 0.25,
                WeatherCondition.NORMAL: 0.0
            },
            "tomato": {
                WeatherCondition.EXCESSIVE_RAIN: 0.40,
                WeatherCondition.HEAT_WAVE: 0.25,
                WeatherCondition.HAILSTORM: 0.30,
                WeatherCondition.NORMAL: 0.0
            }
        }
    
    async def generate_demand_forecast(
        self,
        commodity: str,
        location: Optional[str] = None,
        forecast_days: int = 30,
        model: ForecastModel = ForecastModel.ENSEMBLE
    ) -> DemandForecast:
        """
        Generate demand forecast for a commodity.
        
        Args:
            commodity: Commodity name
            location: Optional location filter
            forecast_days: Number of days to forecast
            model: Forecasting model to use
            
        Returns:
            DemandForecast with predicted demand and confidence
        """
        try:
            # Get historical price data for demand analysis
            end_date = date.today()
            start_date = end_date - timedelta(days=365)  # 1 year of data
            
            price_points = await self.price_discovery_service._get_historical_prices(
                commodity, start_date, end_date, location
            )
            
            if len(price_points) < 30:
                logger.warning(f"Insufficient data for demand forecasting: {len(price_points)} points")
                return DemandForecast(
                    commodity=commodity,
                    location=location,
                    forecast_date=end_date + timedelta(days=forecast_days),
                    forecast_period_days=forecast_days,
                    predicted_demand=1.0,
                    confidence=0.0,
                    demand_trend=TrendDirection.STABLE,
                    model_used=model,
                    factors_considered=["insufficient_data"]
                )
            
            # Use selected forecasting model
            forecast_func = self.forecast_models.get(model, self._ensemble_forecast)
            base_forecast = await forecast_func(price_points, forecast_days, commodity)
            
            # Calculate demand from price trends (inverse relationship)
            current_avg_price = statistics.mean([pp.price for pp in price_points[-7:]])  # Last week average
            predicted_price = base_forecast.get("predicted_price", current_avg_price)
            
            # Demand multiplier based on price change (simplified inverse relationship)
            price_change_ratio = predicted_price / current_avg_price if current_avg_price > 0 else 1.0
            demand_multiplier = 2.0 - price_change_ratio  # Inverse relationship
            
            # Apply seasonal factors
            seasonal_factor = await self._get_seasonal_demand_factor(commodity, forecast_days)
            
            # Apply weather factors
            weather_factor = await self._get_weather_demand_factor(commodity, location, forecast_days)
            
            # Apply festival factors
            festival_factor = await self._get_festival_demand_factor(commodity, location, forecast_days)
            
            # Apply export-import factors
            trade_factor = await self._get_trade_demand_factor(commodity, forecast_days)
            
            # Calculate final demand prediction
            predicted_demand = demand_multiplier * seasonal_factor * weather_factor * festival_factor * trade_factor
            
            # Determine trend direction
            if predicted_demand > 1.1:
                demand_trend = TrendDirection.RISING
            elif predicted_demand < 0.9:
                demand_trend = TrendDirection.FALLING
            else:
                demand_trend = TrendDirection.STABLE
            
            # Calculate confidence based on data quality and model performance
            confidence = self._calculate_forecast_confidence(
                price_points, model, commodity, location
            )
            
            # Get historical accuracy if available
            historical_accuracy = await self._get_model_historical_accuracy(
                model, commodity, location, forecast_days
            )
            
            factors_considered = ["historical_prices", "seasonal_patterns"]
            if weather_factor != 1.0:
                factors_considered.append("weather_conditions")
            if festival_factor != 1.0:
                factors_considered.append("festival_demand")
            if trade_factor != 1.0:
                factors_considered.append("export_import_trends")
            
            return DemandForecast(
                commodity=commodity,
                location=location,
                forecast_date=end_date + timedelta(days=forecast_days),
                forecast_period_days=forecast_days,
                predicted_demand=predicted_demand,
                confidence=confidence,
                demand_trend=demand_trend,
                seasonal_factor=seasonal_factor,
                weather_factor=weather_factor,
                festival_factor=festival_factor,
                export_import_factor=trade_factor,
                historical_accuracy=historical_accuracy,
                model_used=model,
                factors_considered=factors_considered
            )
            
        except Exception as e:
            logger.error(f"Error generating demand forecast: {str(e)}")
            raise
    
    async def predict_weather_impact(
        self,
        commodity: str,
        weather_condition: WeatherCondition,
        affected_regions: List[str],
        impact_duration_days: int = 7
    ) -> WeatherImpactPrediction:
        """
        Predict weather impact on commodity prices.
        
        Args:
            commodity: Commodity name
            weather_condition: Type of weather condition
            affected_regions: List of affected regions
            impact_duration_days: Duration of impact in days
            
        Returns:
            WeatherImpactPrediction with impact analysis
        """
        try:
            # Get weather impact coefficient for commodity
            commodity_lower = commodity.lower()
            impact_coefficients = self.weather_impact_coefficients.get(
                commodity_lower, 
                {weather_condition: 0.1}  # Default 10% impact
            )
            
            base_impact = impact_coefficients.get(weather_condition, 0.1)
            
            # Adjust impact based on affected regions (more regions = higher impact)
            region_multiplier = min(1.0 + (len(affected_regions) - 1) * 0.1, 2.0)
            price_impact_percentage = base_impact * region_multiplier * 100
            
            # Supply impact is typically higher than price impact
            supply_impact_percentage = price_impact_percentage * 1.5
            
            # Get historical precedents
            historical_precedents = await self._get_weather_historical_precedents(
                commodity, weather_condition, affected_regions
            )
            
            # Calculate confidence based on historical data
            confidence = 0.7  # Base confidence
            if historical_precedents:
                confidence = min(0.9, 0.7 + len(historical_precedents) * 0.05)
            
            # Generate mitigation suggestions
            mitigation_suggestions = self._generate_weather_mitigation_suggestions(
                commodity, weather_condition, price_impact_percentage
            )
            
            return WeatherImpactPrediction(
                commodity=commodity,
                weather_condition=weather_condition,
                affected_regions=affected_regions,
                impact_start_date=date.today(),
                impact_duration_days=impact_duration_days,
                price_impact_percentage=price_impact_percentage,
                supply_impact_percentage=supply_impact_percentage,
                confidence=confidence,
                historical_precedents=historical_precedents,
                mitigation_suggestions=mitigation_suggestions
            )
            
        except Exception as e:
            logger.error(f"Error predicting weather impact: {str(e)}")
            raise
    
    async def generate_seasonal_alerts(
        self,
        commodity: str,
        location: Optional[str] = None,
        days_ahead: int = 30
    ) -> List[SeasonalDemandAlert]:
        """
        Generate seasonal and festival demand alerts.
        
        Args:
            commodity: Commodity name
            location: Optional location filter
            days_ahead: Number of days to look ahead for alerts
            
        Returns:
            List of SeasonalDemandAlert objects
        """
        try:
            alerts = []
            
            # Get festival calendar for the next period
            festivals = await self._get_upcoming_festivals(location, days_ahead)
            
            for festival in festivals:
                if commodity.lower() in [c.lower() for c in festival.affected_commodities]:
                    # Calculate expected demand change
                    demand_change = (festival.demand_multiplier - 1.0) * 100
                    
                    # Get historical impact if available
                    historical_impact = festival.historical_impact.get(commodity.lower(), demand_change)
                    
                    # Determine severity
                    if abs(demand_change) >= 30:
                        severity = AlertSeverity.HIGH
                    elif abs(demand_change) >= 15:
                        severity = AlertSeverity.MEDIUM
                    else:
                        severity = AlertSeverity.LOW
                    
                    # Generate preparation suggestions
                    preparation_suggestions = self._generate_festival_preparation_suggestions(
                        commodity, festival, demand_change
                    )
                    
                    # Determine affected markets
                    affected_markets = await self._get_markets_in_regions(festival.regions)
                    
                    alert = SeasonalDemandAlert(
                        alert_id=f"festival_{festival.festival_name}_{commodity}_{date.today().isoformat()}",
                        commodity=commodity,
                        location=location,
                        alert_type="festival",
                        event_name=festival.festival_name,
                        event_start_date=festival.start_date,
                        event_end_date=festival.end_date,
                        expected_demand_change=demand_change,
                        price_impact_prediction=historical_impact,
                        severity=severity,
                        affected_markets=affected_markets,
                        preparation_suggestions=preparation_suggestions,
                        historical_data={
                            "festival_type": festival.festival_type.value,
                            "historical_impact": historical_impact,
                            "regions": festival.regions
                        }
                    )
                    alerts.append(alert)
            
            # Add seasonal alerts (harvest seasons, etc.)
            seasonal_alerts = await self._generate_seasonal_pattern_alerts(
                commodity, location, days_ahead
            )
            alerts.extend(seasonal_alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating seasonal alerts: {str(e)}")
            return []
    
    async def analyze_export_import_influence(
        self,
        commodity: str,
        analysis_period_days: int = 30
    ) -> ExportImportInfluence:
        """
        Analyze export-import price influence on domestic markets.
        
        Args:
            commodity: Commodity name
            analysis_period_days: Period for analysis in days
            
        Returns:
            ExportImportInfluence with trade analysis
        """
        try:
            # Get domestic price data
            domestic_prices = await self.price_discovery_service.get_current_prices(commodity)
            if not domestic_prices:
                raise ValueError(f"No domestic price data found for {commodity}")
            
            avg_domestic_price = statistics.mean([p.price_modal for p in domestic_prices])
            
            # Get international price data (mock implementation - in production, integrate with trade APIs)
            international_price = await self._get_international_price(commodity)
            
            # Calculate price differential
            price_differential = avg_domestic_price - international_price
            price_differential_percentage = (price_differential / international_price) * 100 if international_price > 0 else 0
            
            # Get trade balance data
            trade_balance = await self._get_trade_balance(commodity, analysis_period_days)
            
            # Calculate influence factor based on trade volume and price correlation
            influence_factor = await self._calculate_trade_influence_factor(commodity, analysis_period_days)
            
            # Determine arbitrage opportunity
            arbitrage_opportunity = "none"
            if price_differential_percentage > 10:
                arbitrage_opportunity = "export"
            elif price_differential_percentage < -10:
                arbitrage_opportunity = "import"
            
            # Get key trading partners
            key_trading_partners = await self._get_key_trading_partners(commodity)
            
            # Analyze trade policy impact
            trade_policy_impact = await self._analyze_trade_policy_impact(commodity)
            
            # Generate recommendations
            recommendations = self._generate_trade_recommendations(
                commodity, price_differential_percentage, trade_balance, arbitrage_opportunity
            )
            
            return ExportImportInfluence(
                commodity=commodity,
                analysis_date=date.today(),
                domestic_price=avg_domestic_price,
                international_price=international_price,
                price_differential=price_differential,
                price_differential_percentage=price_differential_percentage,
                trade_balance=trade_balance,
                influence_factor=influence_factor,
                arbitrage_opportunity=arbitrage_opportunity,
                key_trading_partners=key_trading_partners,
                trade_policy_impact=trade_policy_impact,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error analyzing export-import influence: {str(e)}")
            raise
    
    async def generate_comprehensive_analytics(
        self,
        commodity: str,
        location: Optional[str] = None,
        analysis_period_days: int = 30
    ) -> MarketAnalytics:
        """
        Generate comprehensive market analytics report.
        
        Args:
            commodity: Commodity name
            location: Optional location filter
            analysis_period_days: Analysis period in days
            
        Returns:
            MarketAnalytics with complete analysis
        """
        try:
            # Generate demand forecast
            demand_forecast = await self.generate_demand_forecast(
                commodity, location, analysis_period_days
            )
            
            # Get weather predictions
            weather_predictions = await self._get_active_weather_predictions(commodity, location)
            
            # Generate seasonal alerts
            active_alerts = await self.generate_seasonal_alerts(commodity, location)
            
            # Analyze trade influence
            trade_influence = await self.analyze_export_import_influence(commodity)
            
            # Calculate overall market sentiment
            sentiment_factors = []
            if demand_forecast.demand_trend == TrendDirection.RISING:
                sentiment_factors.append(1)
            elif demand_forecast.demand_trend == TrendDirection.FALLING:
                sentiment_factors.append(-1)
            else:
                sentiment_factors.append(0)
            
            # Weather impact on sentiment
            for weather_pred in weather_predictions:
                if weather_pred.price_impact_percentage > 0:
                    sentiment_factors.append(1)
                elif weather_pred.price_impact_percentage < 0:
                    sentiment_factors.append(-1)
            
            # Festival impact on sentiment
            for alert in active_alerts:
                if alert.expected_demand_change > 0:
                    sentiment_factors.append(1)
                elif alert.expected_demand_change < 0:
                    sentiment_factors.append(-1)
            
            # Trade impact on sentiment
            if trade_influence.arbitrage_opportunity == "export":
                sentiment_factors.append(1)
            elif trade_influence.arbitrage_opportunity == "import":
                sentiment_factors.append(-1)
            
            # Calculate overall sentiment
            avg_sentiment = statistics.mean(sentiment_factors) if sentiment_factors else 0
            if avg_sentiment > 0.3:
                overall_sentiment = "bullish"
            elif avg_sentiment < -0.3:
                overall_sentiment = "bearish"
            else:
                overall_sentiment = "neutral"
            
            # Calculate risk assessment
            risk_factors = []
            
            # Weather risks
            for weather_pred in weather_predictions:
                if weather_pred.price_impact_percentage > 20:
                    risk_factors.append("high_weather_risk")
                elif weather_pred.price_impact_percentage > 10:
                    risk_factors.append("moderate_weather_risk")
            
            # Volatility risk
            if demand_forecast.confidence < 0.5:
                risk_factors.append("high_forecast_uncertainty")
            
            # Trade risks
            if abs(trade_influence.price_differential_percentage) > 20:
                risk_factors.append("high_trade_volatility")
            
            # Determine overall risk
            if len(risk_factors) >= 3 or any("high" in rf for rf in risk_factors):
                risk_assessment = "high"
            elif len(risk_factors) >= 1:
                risk_assessment = "medium"
            else:
                risk_assessment = "low"
            
            # Calculate confidence score
            confidence_components = [demand_forecast.confidence]
            if weather_predictions:
                confidence_components.extend([wp.confidence for wp in weather_predictions])
            if trade_influence:
                confidence_components.append(0.7)  # Base trade analysis confidence
            
            confidence_score = statistics.mean(confidence_components)
            
            # Generate recommendations
            trading_recommendations = self._generate_trading_recommendations(
                demand_forecast, weather_predictions, active_alerts, trade_influence
            )
            
            risk_mitigation_strategies = self._generate_risk_mitigation_strategies(
                risk_factors, weather_predictions, active_alerts
            )
            
            return MarketAnalytics(
                commodity=commodity,
                location=location,
                analysis_date=date.today(),
                analysis_period_days=analysis_period_days,
                demand_forecast=demand_forecast,
                weather_predictions=weather_predictions,
                active_alerts=active_alerts,
                trade_influence=trade_influence,
                overall_market_sentiment=overall_sentiment,
                risk_assessment=risk_assessment,
                confidence_score=confidence_score,
                trading_recommendations=trading_recommendations,
                risk_mitigation_strategies=risk_mitigation_strategies
            )
            
        except Exception as e:
            logger.error(f"Error generating comprehensive analytics: {str(e)}")
            raise
    
    # Helper methods for forecasting models
    
    async def _arima_forecast(
        self, 
        price_points: List[PricePoint], 
        forecast_days: int, 
        commodity: str
    ) -> Dict[str, Any]:
        """ARIMA forecasting model (simplified implementation)."""
        prices = [pp.price for pp in price_points]
        
        # Simple ARIMA approximation using trend and seasonality
        trend = self._calculate_linear_trend(prices)
        seasonal_component = await self._get_seasonal_component(commodity, forecast_days)
        
        last_price = prices[-1]
        predicted_price = last_price + (trend * forecast_days) + seasonal_component
        
        return {
            "predicted_price": max(0, predicted_price),
            "model": "arima",
            "confidence": 0.75
        }
    
    async def _linear_regression_forecast(
        self, 
        price_points: List[PricePoint], 
        forecast_days: int, 
        commodity: str
    ) -> Dict[str, Any]:
        """Linear regression forecasting model."""
        prices = [pp.price for pp in price_points]
        n = len(prices)
        
        # Calculate linear regression
        x_values = list(range(n))
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(prices)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, prices))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            slope = 0
        else:
            slope = numerator / denominator
        
        intercept = y_mean - slope * x_mean
        
        # Predict future price
        future_x = n + forecast_days - 1
        predicted_price = slope * future_x + intercept
        
        return {
            "predicted_price": max(0, predicted_price),
            "model": "linear_regression",
            "confidence": 0.65
        }
    
    async def _moving_average_forecast(
        self, 
        price_points: List[PricePoint], 
        forecast_days: int, 
        commodity: str
    ) -> Dict[str, Any]:
        """Moving average forecasting model."""
        prices = [pp.price for pp in price_points]
        
        # Use different moving averages
        short_ma = statistics.mean(prices[-7:]) if len(prices) >= 7 else statistics.mean(prices)
        long_ma = statistics.mean(prices[-30:]) if len(prices) >= 30 else statistics.mean(prices)
        
        # Trend based on MA crossover
        if short_ma > long_ma:
            trend_factor = 1.01  # Slight upward trend
        elif short_ma < long_ma:
            trend_factor = 0.99  # Slight downward trend
        else:
            trend_factor = 1.0
        
        predicted_price = short_ma * (trend_factor ** (forecast_days / 30))
        
        return {
            "predicted_price": predicted_price,
            "model": "moving_average",
            "confidence": 0.60
        }
    
    async def _seasonal_decomposition_forecast(
        self, 
        price_points: List[PricePoint], 
        forecast_days: int, 
        commodity: str
    ) -> Dict[str, Any]:
        """Seasonal decomposition forecasting model."""
        prices = [pp.price for pp in price_points]
        
        # Calculate trend
        trend = self._calculate_linear_trend(prices)
        
        # Get seasonal component
        seasonal_component = await self._get_seasonal_component(commodity, forecast_days)
        
        # Calculate residual (simplified)
        base_price = statistics.mean(prices)
        
        predicted_price = base_price + (trend * forecast_days) + seasonal_component
        
        return {
            "predicted_price": max(0, predicted_price),
            "model": "seasonal_decomposition",
            "confidence": 0.70
        }
    
    async def _ensemble_forecast(
        self, 
        price_points: List[PricePoint], 
        forecast_days: int, 
        commodity: str
    ) -> Dict[str, Any]:
        """Ensemble forecasting using multiple models."""
        # Get predictions from different models
        arima_result = await self._arima_forecast(price_points, forecast_days, commodity)
        lr_result = await self._linear_regression_forecast(price_points, forecast_days, commodity)
        ma_result = await self._moving_average_forecast(price_points, forecast_days, commodity)
        seasonal_result = await self._seasonal_decomposition_forecast(price_points, forecast_days, commodity)
        
        # Weight the predictions based on model confidence
        predictions = [
            (arima_result["predicted_price"], arima_result["confidence"]),
            (lr_result["predicted_price"], lr_result["confidence"]),
            (ma_result["predicted_price"], ma_result["confidence"]),
            (seasonal_result["predicted_price"], seasonal_result["confidence"])
        ]
        
        # Calculate weighted average
        total_weight = sum(conf for _, conf in predictions)
        if total_weight > 0:
            weighted_prediction = sum(pred * conf for pred, conf in predictions) / total_weight
            avg_confidence = total_weight / len(predictions)
        else:
            weighted_prediction = statistics.mean([pred for pred, _ in predictions])
            avg_confidence = 0.5
        
        return {
            "predicted_price": weighted_prediction,
            "model": "ensemble",
            "confidence": min(0.85, avg_confidence + 0.1)  # Ensemble bonus
        }
    
    # Helper methods for demand factors
    
    async def _get_seasonal_demand_factor(self, commodity: str, forecast_days: int) -> float:
        """Get seasonal demand factor for forecast period."""
        try:
            forecast_date = date.today() + timedelta(days=forecast_days)
            forecast_month = forecast_date.month
            
            # Get seasonal factors from database
            db = await get_database()
            seasonal_factor_doc = await db.seasonal_factors.find_one({
                "commodity": {"$regex": commodity, "$options": "i"},
                "month": forecast_month
            })
            
            if seasonal_factor_doc:
                return seasonal_factor_doc["factor"]
            
            # Default seasonal patterns if no data found
            default_patterns = {
                "rice": [1.0, 1.0, 0.9, 0.9, 0.95, 1.1, 1.2, 1.1, 1.0, 0.9, 0.9, 1.0],
                "wheat": [0.9, 0.9, 0.95, 1.2, 1.1, 1.0, 0.9, 0.9, 0.9, 0.95, 1.0, 1.0],
                "onion": [1.2, 1.3, 1.1, 0.9, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.2, 1.1]
            }
            
            commodity_lower = commodity.lower()
            if commodity_lower in default_patterns:
                return default_patterns[commodity_lower][forecast_month - 1]
            
            return 1.0  # No seasonal effect
            
        except Exception as e:
            logger.error(f"Error getting seasonal demand factor: {str(e)}")
            return 1.0
    
    async def _get_weather_demand_factor(
        self, 
        commodity: str, 
        location: Optional[str], 
        forecast_days: int
    ) -> float:
        """Get weather-based demand factor."""
        try:
            # Check for active weather alerts
            db = await get_database()
            
            # Look for weather alerts in the forecast period
            forecast_date = date.today() + timedelta(days=forecast_days)
            
            weather_alerts = await db.weather_alerts.find({
                "commodity": {"$regex": commodity, "$options": "i"},
                "alert_date": {"$lte": forecast_date.isoformat()},
                "is_active": True
            }).to_list(length=10)
            
            if not weather_alerts:
                return 1.0  # No weather impact
            
            # Calculate combined weather impact
            weather_factors = []
            for alert in weather_alerts:
                weather_condition = WeatherCondition(alert["weather_condition"])
                impact_coefficient = self.weather_impact_coefficients.get(
                    commodity.lower(), {}
                ).get(weather_condition, 0.1)
                
                # Convert price impact to demand impact (inverse relationship)
                demand_factor = 1.0 + impact_coefficient
                weather_factors.append(demand_factor)
            
            # Return average weather factor
            return statistics.mean(weather_factors) if weather_factors else 1.0
            
        except Exception as e:
            logger.error(f"Error getting weather demand factor: {str(e)}")
            return 1.0
    
    async def _get_festival_demand_factor(
        self, 
        commodity: str, 
        location: Optional[str], 
        forecast_days: int
    ) -> float:
        """Get festival-based demand factor."""
        try:
            forecast_date = date.today() + timedelta(days=forecast_days)
            
            # Get upcoming festivals
            festivals = await self._get_upcoming_festivals(location, forecast_days + 7)
            
            festival_factors = []
            for festival in festivals:
                # Check if forecast date falls within festival period
                if festival.start_date <= forecast_date <= festival.end_date:
                    if commodity.lower() in [c.lower() for c in festival.affected_commodities]:
                        festival_factors.append(festival.demand_multiplier)
            
            # Return maximum festival factor (most significant festival)
            return max(festival_factors) if festival_factors else 1.0
            
        except Exception as e:
            logger.error(f"Error getting festival demand factor: {str(e)}")
            return 1.0
    
    async def _get_trade_demand_factor(self, commodity: str, forecast_days: int) -> float:
        """Get export-import based demand factor."""
        try:
            # Get recent trade data
            db = await get_database()
            
            # Look for recent export-import data
            recent_date = date.today() - timedelta(days=30)
            
            trade_data = await db.export_import_data.find({
                "commodity": {"$regex": commodity, "$options": "i"},
                "trade_date": {"$gte": recent_date.isoformat()}
            }).to_list(length=50)
            
            if not trade_data:
                return 1.0  # No trade impact
            
            # Calculate net trade balance
            exports = sum(td["volume"] for td in trade_data if td["trade_direction"] == "export")
            imports = sum(td["volume"] for td in trade_data if td["trade_direction"] == "import")
            
            net_trade = exports - imports
            
            # Convert trade balance to demand factor
            # Positive net exports increase domestic demand (higher prices)
            # Negative net exports (net imports) decrease domestic demand
            if abs(net_trade) < 1000:  # Minimal trade impact
                return 1.0
            
            # Scale factor based on trade volume
            trade_factor = 1.0 + (net_trade / 10000) * 0.1  # 10% impact per 10k tons
            return max(0.5, min(2.0, trade_factor))  # Clamp between 0.5 and 2.0
            
        except Exception as e:
            logger.error(f"Error getting trade demand factor: {str(e)}")
            return 1.0
    
    async def _get_weather_historical_precedents(
        self,
        commodity: str,
        weather_condition: WeatherCondition,
        affected_regions: List[str]
    ) -> List[Dict[str, Any]]:
        """Get historical weather impact precedents."""
        try:
            db = await get_database()
            
            # Look for similar weather events
            precedents = await db.weather_impact_history.find({
                "commodity": {"$regex": commodity, "$options": "i"},
                "weather_condition": weather_condition.value
            }).to_list(length=10)
            
            return precedents
            
        except Exception as e:
            logger.error(f"Error getting weather precedents: {str(e)}")
            return []
    
    def _generate_weather_mitigation_suggestions(
        self,
        commodity: str,
        weather_condition: WeatherCondition,
        price_impact_percentage: float
    ) -> List[str]:
        """Generate weather impact mitigation suggestions."""
        suggestions = []
        
        if weather_condition in [WeatherCondition.DROUGHT, WeatherCondition.HEAT_WAVE]:
            suggestions.extend([
                "Consider sourcing from regions with better water availability",
                "Monitor irrigation-dependent areas closely",
                "Prepare for potential quality degradation"
            ])
        
        elif weather_condition in [WeatherCondition.FLOOD, WeatherCondition.EXCESSIVE_RAIN]:
            suggestions.extend([
                "Expect transportation delays and increased logistics costs",
                "Monitor storage facilities for moisture damage",
                "Consider alternative supply routes"
            ])
        
        elif weather_condition == WeatherCondition.CYCLONE:
            suggestions.extend([
                "Prepare for supply chain disruptions",
                "Consider emergency stock building",
                "Monitor port operations for delays"
            ])
        
        if price_impact_percentage > 20:
            suggestions.append("Consider hedging strategies to manage price volatility")
        
        return suggestions
    
    def _generate_festival_preparation_suggestions(
        self,
        commodity: str,
        festival: FestivalCalendar,
        demand_change: float
    ) -> List[str]:
        """Generate festival preparation suggestions."""
        suggestions = []
        
        if demand_change > 20:
            suggestions.extend([
                f"Stock up on {commodity} at least {festival.preparation_days} days before {festival.festival_name}",
                "Consider premium pricing during festival period",
                "Ensure adequate storage and distribution capacity"
            ])
        
        if festival.festival_type == FestivalType.HARVEST:
            suggestions.extend([
                "Expect fresh supply from harvest regions",
                "Monitor quality variations in new crop"
            ])
        
        elif festival.festival_type == FestivalType.RELIGIOUS:
            suggestions.extend([
                "Prepare for concentrated demand in specific regions",
                "Consider special packaging or quality grades"
            ])
        
        return suggestions
    
    async def _get_markets_in_regions(self, regions: List[str]) -> List[str]:
        """Get market names in specified regions."""
        try:
            db = await get_database()
            
            # Get markets from price data
            markets = set()
            for region in regions:
                cursor = db.price_data.find({
                    "$or": [
                        {"location.state": {"$regex": region, "$options": "i"}},
                        {"location.district": {"$regex": region, "$options": "i"}}
                    ]
                }).limit(50)
                
                async for doc in cursor:
                    markets.add(doc["market_name"])
            
            return list(markets)
            
        except Exception as e:
            logger.error(f"Error getting markets in regions: {str(e)}")
            return []
    
    async def _generate_seasonal_pattern_alerts(
        self,
        commodity: str,
        location: Optional[str],
        days_ahead: int
    ) -> List[SeasonalDemandAlert]:
        """Generate seasonal pattern alerts (harvest seasons, etc.)."""
        alerts = []
        
        try:
            # Get seasonal factors for upcoming months
            current_date = date.today()
            
            for days_offset in range(0, days_ahead, 30):  # Check monthly
                check_date = current_date + timedelta(days=days_offset)
                month = check_date.month
                
                # Get seasonal factor for this month
                db = await get_database()
                seasonal_doc = await db.seasonal_factors.find_one({
                    "commodity": {"$regex": commodity, "$options": "i"},
                    "month": month
                })
                
                if seasonal_doc and abs(seasonal_doc["factor"] - 1.0) > 0.1:
                    # Significant seasonal variation
                    demand_change = (seasonal_doc["factor"] - 1.0) * 100
                    
                    alert_type = "seasonal"
                    event_name = f"Seasonal pattern for {commodity} in month {month}"
                    
                    # Determine severity
                    if abs(demand_change) >= 20:
                        severity = AlertSeverity.HIGH
                    elif abs(demand_change) >= 10:
                        severity = AlertSeverity.MEDIUM
                    else:
                        severity = AlertSeverity.LOW
                    
                    alert = SeasonalDemandAlert(
                        alert_id=f"seasonal_{commodity}_{month}_{current_date.isoformat()}",
                        commodity=commodity,
                        location=location,
                        alert_type=alert_type,
                        event_name=event_name,
                        event_start_date=check_date.replace(day=1),
                        event_end_date=check_date.replace(day=28),  # Approximate month end
                        expected_demand_change=demand_change,
                        price_impact_prediction=demand_change * 0.8,  # Price impact usually less than demand
                        severity=severity,
                        preparation_suggestions=[
                            f"Prepare for {abs(demand_change):.1f}% {'increase' if demand_change > 0 else 'decrease'} in demand",
                            seasonal_doc.get("description", "Seasonal variation expected")
                        ],
                        historical_data={
                            "seasonal_factor": seasonal_doc["factor"],
                            "month": month
                        }
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error generating seasonal pattern alerts: {str(e)}")
            return []
    
    async def _get_international_price(self, commodity: str) -> float:
        """Get international price for commodity (mock implementation)."""
        try:
            db = await get_database()
            
            # Get latest international price
            intl_price_doc = await db.international_prices.find_one(
                {"commodity": {"$regex": commodity, "$options": "i"}},
                sort=[("date", -1)]
            )
            
            if intl_price_doc:
                return intl_price_doc["price_usd_per_ton"]
            
            # Fallback to mock data
            mock_prices = {
                "rice": 420.0,
                "wheat": 280.0,
                "sugar": 550.0,
                "onion": 250.0,
                "cotton": 1800.0,
                "pulses": 750.0
            }
            
            return mock_prices.get(commodity.lower(), 400.0)
            
        except Exception as e:
            logger.error(f"Error getting international price: {str(e)}")
            return 400.0  # Default fallback
    
    async def _get_trade_balance(self, commodity: str, period_days: int) -> float:
        """Get trade balance (exports - imports) for commodity."""
        try:
            db = await get_database()
            
            start_date = date.today() - timedelta(days=period_days)
            
            # Get export data
            export_cursor = db.export_import_data.find({
                "commodity": {"$regex": commodity, "$options": "i"},
                "trade_direction": "export",
                "trade_date": {"$gte": start_date.isoformat()}
            })
            
            total_exports = 0
            async for doc in export_cursor:
                total_exports += doc["volume"]
            
            # Get import data
            import_cursor = db.export_import_data.find({
                "commodity": {"$regex": commodity, "$options": "i"},
                "trade_direction": "import",
                "trade_date": {"$gte": start_date.isoformat()}
            })
            
            total_imports = 0
            async for doc in import_cursor:
                total_imports += doc["volume"]
            
            return total_exports - total_imports
            
        except Exception as e:
            logger.error(f"Error getting trade balance: {str(e)}")
            return 0.0
    
    async def _calculate_trade_influence_factor(self, commodity: str, period_days: int) -> float:
        """Calculate how much international prices influence domestic prices."""
        try:
            # This is a simplified calculation
            # In production, this would involve correlation analysis between international and domestic prices
            
            trade_balance = await self._get_trade_balance(commodity, period_days)
            
            # Higher trade volume = higher influence
            if abs(trade_balance) > 10000:  # High trade volume
                return 0.8
            elif abs(trade_balance) > 5000:  # Medium trade volume
                return 0.6
            elif abs(trade_balance) > 1000:  # Low trade volume
                return 0.4
            else:  # Minimal trade
                return 0.2
            
        except Exception as e:
            logger.error(f"Error calculating trade influence factor: {str(e)}")
            return 0.3  # Default moderate influence
    
    async def _get_key_trading_partners(self, commodity: str) -> List[Dict[str, Any]]:
        """Get key trading partners for commodity."""
        try:
            db = await get_database()
            
            # Aggregate trade data by country
            pipeline = [
                {"$match": {"commodity": {"$regex": commodity, "$options": "i"}}},
                {"$group": {
                    "_id": "$country",
                    "total_volume": {"$sum": "$volume"},
                    "total_value": {"$sum": "$value"},
                    "trade_count": {"$sum": 1}
                }},
                {"$sort": {"total_volume": -1}},
                {"$limit": 5}
            ]
            
            partners = []
            async for doc in db.export_import_data.aggregate(pipeline):
                partners.append({
                    "country": doc["_id"],
                    "total_volume": doc["total_volume"],
                    "total_value": doc["total_value"],
                    "trade_count": doc["trade_count"],
                    "avg_price": doc["total_value"] / doc["total_volume"] if doc["total_volume"] > 0 else 0
                })
            
            return partners
            
        except Exception as e:
            logger.error(f"Error getting key trading partners: {str(e)}")
            return []
    
    async def _analyze_trade_policy_impact(self, commodity: str) -> Optional[str]:
        """Analyze trade policy impact (simplified implementation)."""
        try:
            # This would integrate with trade policy databases in production
            # For now, return generic policy considerations
            
            trade_balance = await self._get_trade_balance(commodity, 90)
            
            if trade_balance > 50000:
                return "High export volume may be subject to export restrictions during domestic shortages"
            elif trade_balance < -50000:
                return "High import dependency may be affected by import duty changes"
            else:
                return "Balanced trade position with moderate policy sensitivity"
            
        except Exception as e:
            logger.error(f"Error analyzing trade policy impact: {str(e)}")
            return None
    
    def _generate_trade_recommendations(
        self,
        commodity: str,
        price_differential_percentage: float,
        trade_balance: float,
        arbitrage_opportunity: str
    ) -> List[str]:
        """Generate trade-based recommendations."""
        recommendations = []
        
        if arbitrage_opportunity == "export":
            recommendations.extend([
                f"Export opportunity: domestic prices are {price_differential_percentage:.1f}% higher than international",
                "Consider export contracts if quality meets international standards",
                "Monitor export policy changes and duties"
            ])
        
        elif arbitrage_opportunity == "import":
            recommendations.extend([
                f"Import opportunity: international prices are {abs(price_differential_percentage):.1f}% lower than domestic",
                "Consider import contracts to reduce procurement costs",
                "Factor in import duties and logistics costs"
            ])
        
        if abs(trade_balance) > 20000:
            if trade_balance > 0:
                recommendations.append("High export dependency - monitor domestic supply carefully")
            else:
                recommendations.append("High import dependency - diversify supply sources")
        
        return recommendations
    
    async def _get_active_weather_predictions(
        self,
        commodity: str,
        location: Optional[str]
    ) -> List[WeatherImpactPrediction]:
        """Get active weather predictions for commodity."""
        try:
            db = await get_database()
            
            # Look for active weather alerts
            query = {
                "commodity": {"$regex": commodity, "$options": "i"},
                "is_active": True,
                "alert_date": {"$gte": (date.today() - timedelta(days=7)).isoformat()}
            }
            
            if location:
                query["affected_regions"] = {"$in": [location]}
            
            weather_alerts = await db.weather_alerts.find(query).to_list(length=10)
            
            predictions = []
            for alert in weather_alerts:
                # Convert alert to prediction format
                prediction = WeatherImpactPrediction(
                    commodity=commodity,
                    weather_condition=WeatherCondition(alert["weather_condition"]),
                    affected_regions=alert["affected_regions"],
                    impact_start_date=date.fromisoformat(alert["alert_date"]),
                    impact_duration_days=7,  # Default duration
                    price_impact_percentage=15.0,  # Default impact
                    supply_impact_percentage=20.0,  # Default supply impact
                    confidence=0.7,
                    mitigation_suggestions=alert.get("action_recommendations", [])
                )
                predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error getting active weather predictions: {str(e)}")
            return []
    
    def _calculate_linear_trend(self, prices: List[float]) -> float:
        """Calculate linear trend from price data."""
        if len(prices) < 2:
            return 0.0
        
        n = len(prices)
        x_values = list(range(n))
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(prices)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, prices))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        return numerator / denominator if denominator != 0 else 0.0
    
    async def _get_seasonal_component(self, commodity: str, forecast_days: int) -> float:
        """Get seasonal price component."""
        seasonal_factor = await self._get_seasonal_demand_factor(commodity, forecast_days)
        # Convert demand factor to price component (inverse relationship)
        return (2.0 - seasonal_factor - 1.0) * 100  # Price adjustment in currency units
    
    def _calculate_forecast_confidence(
        self, 
        price_points: List[PricePoint], 
        model: ForecastModel, 
        commodity: str, 
        location: Optional[str]
    ) -> float:
        """Calculate forecast confidence based on data quality and model performance."""
        # Base confidence on data quantity
        data_confidence = min(len(price_points) / 100.0, 1.0)
        
        # Model-specific confidence adjustments
        model_confidence = {
            ForecastModel.ARIMA: 0.75,
            ForecastModel.LINEAR_REGRESSION: 0.65,
            ForecastModel.MOVING_AVERAGE: 0.60,
            ForecastModel.SEASONAL_DECOMPOSITION: 0.70,
            ForecastModel.ENSEMBLE: 0.80
        }.get(model, 0.60)
        
        # Data recency confidence
        if price_points:
            latest_date = max(pp.date for pp in price_points)
            days_old = (date.today() - latest_date).days
            recency_confidence = max(0.0, 1.0 - (days_old / 30.0))
        else:
            recency_confidence = 0.0
        
        # Combined confidence
        return (data_confidence * 0.4 + model_confidence * 0.4 + recency_confidence * 0.2)
    
    async def _get_model_historical_accuracy(
        self, 
        model: ForecastModel, 
        commodity: str, 
        location: Optional[str], 
        forecast_days: int
    ) -> Optional[float]:
        """Get historical accuracy for a forecasting model."""
        try:
            db = await get_database()
            
            accuracy_doc = await db.model_accuracy.find_one({
                "model_name": model.value,
                "commodity": {"$regex": commodity, "$options": "i"},
                "location": location,
                "forecast_horizon_days": forecast_days
            })
            
            return accuracy_doc["accuracy_percentage"] if accuracy_doc else None
            
        except Exception as e:
            logger.error(f"Error getting model historical accuracy: {str(e)}")
            return None
    
    async def _get_upcoming_festivals(
        self, 
        location: Optional[str], 
        days_ahead: int
    ) -> List[FestivalCalendar]:
        """Get upcoming festivals in the specified period."""
        try:
            db = await get_database()
            
            start_date = date.today()
            end_date = start_date + timedelta(days=days_ahead)
            
            query = {
                "start_date": {"$lte": end_date.isoformat()},
                "end_date": {"$gte": start_date.isoformat()}
            }
            
            if location:
                query["regions"] = {"$in": [location]}
            
            festival_docs = await db.festival_calendar.find(query).to_list(length=20)
            
            festivals = []
            for doc in festival_docs:
                festivals.append(FestivalCalendar(**doc))
            
            return festivals
            
        except Exception as e:
            logger.error(f"Error getting upcoming festivals: {str(e)}")
            return []
    
    def _generate_trading_recommendations(
        self,
        demand_forecast: DemandForecast,
        weather_predictions: List[WeatherImpactPrediction],
        active_alerts: List[SeasonalDemandAlert],
        trade_influence: ExportImportInfluence
    ) -> List[str]:
        """Generate trading recommendations based on analytics."""
        recommendations = []
        
        # Demand-based recommendations
        if demand_forecast.demand_trend == TrendDirection.RISING:
            recommendations.append("Consider increasing inventory as demand is expected to rise")
        elif demand_forecast.demand_trend == TrendDirection.FALLING:
            recommendations.append("Consider reducing inventory as demand is expected to fall")
        
        # Weather-based recommendations
        for weather_pred in weather_predictions:
            if weather_pred.price_impact_percentage > 15:
                recommendations.append(f"Weather alert: {weather_pred.weather_condition.value} may increase prices by {weather_pred.price_impact_percentage:.1f}%")
        
        # Festival-based recommendations
        high_impact_alerts = [a for a in active_alerts if a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]]
        if high_impact_alerts:
            recommendations.append("Prepare for festival season demand surge - consider stocking up")
        
        # Trade-based recommendations
        if trade_influence.arbitrage_opportunity == "export":
            recommendations.append("Export opportunity: domestic prices are higher than international")
        elif trade_influence.arbitrage_opportunity == "import":
            recommendations.append("Import opportunity: international prices are lower than domestic")
        
        return recommendations
    
    def _generate_risk_mitigation_strategies(
        self,
        risk_factors: List[str],
        weather_predictions: List[WeatherImpactPrediction],
        active_alerts: List[SeasonalDemandAlert]
    ) -> List[str]:
        """Generate risk mitigation strategies."""
        strategies = []
        
        if "high_weather_risk" in risk_factors:
            strategies.append("Diversify sourcing across multiple regions to reduce weather risk")
            strategies.append("Consider weather insurance or hedging instruments")
        
        if "high_forecast_uncertainty" in risk_factors:
            strategies.append("Maintain flexible inventory levels due to forecast uncertainty")
            strategies.append("Monitor market conditions more frequently")
        
        if "high_trade_volatility" in risk_factors:
            strategies.append("Monitor international price movements closely")
            strategies.append("Consider currency hedging for trade-exposed positions")
        
        # Weather-specific strategies
        for weather_pred in weather_predictions:
            if weather_pred.weather_condition in [WeatherCondition.DROUGHT, WeatherCondition.FLOOD]:
                strategies.append("Consider alternative supply sources in unaffected regions")
        
        return strategies


# Create service instance
market_analytics_service = MarketAnalyticsService()