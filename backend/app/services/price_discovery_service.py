"""
Price Discovery Engine service for market intelligence and price analysis.
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
import statistics
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.models.price import (
    PriceData, PriceQuery, PriceSearchResult, MarketTrend, PriceForecast,
    MarketComparison, MSPData, PriceAlert, WeatherImpact, FestivalDemand,
    PricePoint, SeasonalFactor, TrendDirection, TimePeriod, QualityGrade,
    Location, GeographicPriceQuery, GeographicPriceResult, RadiusFilterResult,
    MarketDistanceInfo, GeographicMarketComparison, QualityBasedPriceCategory,
    QualityPriceCategorization, MarketType
)
from app.services.agmarknet_service import agmarknet_service
from app.db.mongodb import get_database
from app.db.redis import get_redis
import json

logger = logging.getLogger(__name__)


class PriceDiscoveryService:
    """Service for price discovery and market intelligence."""
    
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes cache
        self.prediction_models = {
            "seasonal_arima": self._seasonal_arima_predict,
            "moving_average": self._moving_average_predict,
            "linear_trend": self._linear_trend_predict
        }
    
    async def get_current_prices(
        self,
        commodity: str,
        location: Optional[str] = None,
        radius_km: int = 50
    ) -> List[PriceData]:
        """
        Get current market prices for a commodity.
        
        Args:
            commodity: Commodity name
            location: Location filter
            radius_km: Search radius in kilometers
            
        Returns:
            List of current PriceData within 5 minutes of latest update
        """
        try:
            # Check cache first
            cache_key = f"current_prices:{commodity}:{location or 'all'}:{radius_km}"
            cached_result = await self._get_cached_result(cache_key)
            
            if cached_result:
                logger.info(f"Returning cached prices for {commodity}")
                return cached_result
            
            # Get fresh data from AGMARKNET
            current_prices = await agmarknet_service.get_current_prices(
                commodity=commodity,
                location=location,
                radius_km=radius_km
            )
            
            # Filter prices within 5 minutes of latest update
            if current_prices:
                latest_time = max(pd.updated_at for pd in current_prices)
                cutoff_time = latest_time - timedelta(minutes=5)
                
                current_prices = [
                    pd for pd in current_prices
                    if pd.updated_at >= cutoff_time
                ]
            
            # Cache the result
            await self._cache_result(cache_key, current_prices, ttl=300)
            
            logger.info(f"Retrieved {len(current_prices)} current prices for {commodity}")
            return current_prices
            
        except Exception as e:
            logger.error(f"Error getting current prices: {str(e)}")
            return []
    
    async def get_price_trends(
        self,
        commodity: str,
        period: TimePeriod,
        location: Optional[str] = None
    ) -> MarketTrend:
        """
        Get price trends for a commodity over a specified period.
        
        Args:
            commodity: Commodity name
            period: Time period for trend analysis
            location: Optional location filter
            
        Returns:
            MarketTrend with historical data and analysis
        """
        try:
            # Calculate date range based on period
            end_date = date.today()
            if period == TimePeriod.DAILY:
                start_date = end_date - timedelta(days=30)
            elif period == TimePeriod.WEEKLY:
                start_date = end_date - timedelta(weeks=26)  # 6 months
            elif period == TimePeriod.MONTHLY:
                start_date = end_date - timedelta(days=365)  # 1 year
            else:
                start_date = end_date - timedelta(days=90)  # Default 3 months
            
            # Get historical price data
            price_points = await self._get_historical_prices(
                commodity, start_date, end_date, location
            )
            
            if not price_points:
                logger.warning(f"No historical data found for {commodity}")
                return MarketTrend(
                    commodity=commodity,
                    location=location,
                    time_period=period,
                    price_points=[],
                    trend_direction=TrendDirection.STABLE,
                    volatility_index=0.0,
                    prediction_confidence=0.0
                )
            
            # Calculate trend direction
            trend_direction = self._calculate_trend_direction(price_points)
            
            # Calculate volatility index
            volatility_index = self._calculate_volatility(price_points)
            
            # Get seasonal factors
            seasonal_factors = await self._get_seasonal_factors(commodity)
            
            # Calculate prediction confidence
            prediction_confidence = self._calculate_prediction_confidence(
                price_points, volatility_index
            )
            
            return MarketTrend(
                commodity=commodity,
                location=location,
                time_period=period,
                price_points=price_points,
                trend_direction=trend_direction,
                volatility_index=volatility_index,
                seasonal_factors=seasonal_factors,
                prediction_confidence=prediction_confidence
            )
            
        except Exception as e:
            logger.error(f"Error getting price trends: {str(e)}")
            raise
    
    async def predict_seasonal_prices(
        self,
        commodity: str,
        forecast_days: int,
        location: Optional[str] = None
    ) -> PriceForecast:
        """
        Predict seasonal price variations using machine learning.
        
        Args:
            commodity: Commodity name
            forecast_days: Number of days to forecast
            location: Optional location filter
            
        Returns:
            PriceForecast with predicted prices and confidence
        """
        try:
            # Get historical data for model training
            end_date = date.today()
            start_date = end_date - timedelta(days=730)  # 2 years of data
            
            historical_data = await self._get_historical_prices(
                commodity, start_date, end_date, location
            )
            
            if len(historical_data) < 30:  # Need minimum data for prediction
                logger.warning(f"Insufficient data for prediction: {len(historical_data)} points")
                return PriceForecast(
                    commodity=commodity,
                    location=location,
                    forecast_date=end_date + timedelta(days=forecast_days),
                    predicted_price=0.0,
                    confidence_interval_lower=0.0,
                    confidence_interval_upper=0.0,
                    confidence=0.0,
                    factors_considered=["insufficient_data"],
                    model_used="none"
                )
            
            # Use seasonal ARIMA model for prediction
            forecast = await self._seasonal_arima_predict(
                historical_data, forecast_days, commodity
            )
            
            return forecast
            
        except Exception as e:
            logger.error(f"Error predicting seasonal prices: {str(e)}")
            raise
    
    async def compare_market_prices(
        self,
        commodity: str,
        markets: List[str]
    ) -> MarketComparison:
        """
        Compare prices across different markets.
        
        Args:
            commodity: Commodity name
            markets: List of market names to compare
            
        Returns:
            MarketComparison with price analysis
        """
        try:
            market_prices = []
            
            # Get current prices for each market
            for market in markets:
                prices = await self.get_current_prices(
                    commodity=commodity,
                    location=market,
                    radius_km=25  # Smaller radius for specific markets
                )
                market_prices.extend(prices)
            
            if not market_prices:
                logger.warning(f"No price data found for markets: {markets}")
                return MarketComparison(
                    commodity=commodity,
                    comparison_date=date.today(),
                    markets=[],
                    price_spread=0.0,
                    average_price=0.0,
                    best_market="none"
                )
            
            # Calculate statistics
            prices = [pd.price_modal for pd in market_prices]
            price_spread = max(prices) - min(prices)
            average_price = statistics.mean(prices)
            
            # Find best market (lowest price for buyers)
            best_price_data = min(market_prices, key=lambda x: x.price_modal)
            best_market = best_price_data.market_name
            
            # Additional analysis
            analysis = {
                "total_markets": len(set(pd.market_name for pd in market_prices)),
                "price_variance": statistics.variance(prices) if len(prices) > 1 else 0.0,
                "quality_distribution": self._analyze_quality_distribution(market_prices)
            }
            
            return MarketComparison(
                commodity=commodity,
                comparison_date=date.today(),
                markets=market_prices,
                price_spread=price_spread,
                average_price=average_price,
                best_market=best_market,
                analysis=analysis
            )
            
        except Exception as e:
            logger.error(f"Error comparing market prices: {str(e)}")
            raise
    
    async def get_msp_data(self, commodity: str) -> Optional[MSPData]:
        """
        Get Minimum Support Price data for agricultural products.
        
        Args:
            commodity: Commodity name
            
        Returns:
            MSPData if available, None otherwise
        """
        try:
            db = await get_database()
            collection = db.msp_data
            
            # Get current crop year MSP
            current_year = date.today().year
            crop_year = f"{current_year}-{str(current_year + 1)[2:]}"
            
            msp_doc = await collection.find_one({
                "commodity": {"$regex": commodity, "$options": "i"},
                "crop_year": crop_year
            })
            
            if msp_doc:
                return MSPData(**msp_doc)
            
            # Try previous year if current year not found
            prev_crop_year = f"{current_year - 1}-{str(current_year)[2:]}"
            msp_doc = await collection.find_one({
                "commodity": {"$regex": commodity, "$options": "i"},
                "crop_year": prev_crop_year
            })
            
            if msp_doc:
                return MSPData(**msp_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting MSP data: {str(e)}")
            return None
    
    async def check_price_below_msp(
        self,
        commodity: str,
        current_price: float
    ) -> Tuple[bool, Optional[MSPData]]:
        """
        Check if current market price is below MSP.
        
        Args:
            commodity: Commodity name
            current_price: Current market price
            
        Returns:
            Tuple of (is_below_msp, msp_data)
        """
        try:
            msp_data = await self.get_msp_data(commodity)
            
            if not msp_data:
                return False, None
            
            is_below = current_price < msp_data.msp_price
            return is_below, msp_data
            
        except Exception as e:
            logger.error(f"Error checking price below MSP: {str(e)}")
            return False, None
    
    async def _get_historical_prices(
        self,
        commodity: str,
        start_date: date,
        end_date: date,
        location: Optional[str] = None
    ) -> List[PricePoint]:
        """Get historical price data from database."""
        try:
            db = await get_database()
            collection = db.price_data
            
            # Build query
            query = {
                "commodity": {"$regex": commodity, "$options": "i"},
                "date": {
                    "$gte": start_date.isoformat(),
                    "$lte": end_date.isoformat()
                }
            }
            
            if location:
                query["$or"] = [
                    {"location.state": {"$regex": location, "$options": "i"}},
                    {"location.district": {"$regex": location, "$options": "i"}},
                    {"market_name": {"$regex": location, "$options": "i"}}
                ]
            
            # Get data sorted by date
            cursor = collection.find(query).sort("date", 1)
            documents = await cursor.to_list(length=None)
            
            # Convert to PricePoint objects and aggregate by date
            price_points = {}
            for doc in documents:
                doc_date = datetime.fromisoformat(doc["date"]).date()
                
                if doc_date not in price_points:
                    price_points[doc_date] = []
                
                price_points[doc_date].append(doc["price_modal"])
            
            # Calculate average price per date
            result = []
            for date_key in sorted(price_points.keys()):
                avg_price = statistics.mean(price_points[date_key])
                result.append(PricePoint(
                    date=date_key,
                    price=avg_price,
                    volume=len(price_points[date_key])  # Number of markets
                ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting historical prices: {str(e)}")
            return []
    
    def _calculate_trend_direction(self, price_points: List[PricePoint]) -> TrendDirection:
        """Calculate trend direction from price points."""
        if len(price_points) < 2:
            return TrendDirection.STABLE
        
        # Calculate linear regression slope
        n = len(price_points)
        x_values = list(range(n))
        y_values = [pp.price for pp in price_points]
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return TrendDirection.STABLE
        
        slope = numerator / denominator
        
        # Determine trend based on slope
        if slope > 0.1:
            return TrendDirection.RISING
        elif slope < -0.1:
            return TrendDirection.FALLING
        else:
            # Check volatility for stable vs volatile
            if len(y_values) > 1:
                volatility = statistics.stdev(y_values) / y_mean if y_mean > 0 else 0
                if volatility > 0.1:
                    return TrendDirection.VOLATILE
            
            return TrendDirection.STABLE
    
    def _calculate_volatility(self, price_points: List[PricePoint]) -> float:
        """Calculate volatility index (0-1 scale)."""
        if len(price_points) < 2:
            return 0.0
        
        prices = [pp.price for pp in price_points]
        mean_price = statistics.mean(prices)
        
        if mean_price == 0:
            return 0.0
        
        # Calculate coefficient of variation
        std_dev = statistics.stdev(prices)
        cv = std_dev / mean_price
        
        # Normalize to 0-1 scale (cap at 1.0)
        return min(cv, 1.0)
    
    async def _get_seasonal_factors(self, commodity: str) -> List[SeasonalFactor]:
        """Get seasonal factors for a commodity."""
        try:
            db = await get_database()
            collection = db.seasonal_factors
            
            cursor = collection.find({"commodity": {"$regex": commodity, "$options": "i"}})
            documents = await cursor.to_list(length=12)  # Max 12 months
            
            seasonal_factors = []
            for doc in documents:
                seasonal_factors.append(SeasonalFactor(**doc))
            
            # If no data found, return default seasonal factors
            if not seasonal_factors:
                seasonal_factors = self._get_default_seasonal_factors(commodity)
            
            return seasonal_factors
            
        except Exception as e:
            logger.error(f"Error getting seasonal factors: {str(e)}")
            return self._get_default_seasonal_factors(commodity)
    
    def _get_default_seasonal_factors(self, commodity: str) -> List[SeasonalFactor]:
        """Get default seasonal factors based on commodity type."""
        # Default seasonal patterns for common commodities
        patterns = {
            "rice": [1.0, 1.0, 0.9, 0.9, 0.95, 1.1, 1.2, 1.1, 1.0, 0.9, 0.9, 1.0],
            "wheat": [0.9, 0.9, 0.95, 1.2, 1.1, 1.0, 0.9, 0.9, 0.9, 0.95, 1.0, 1.0],
            "onion": [1.2, 1.3, 1.1, 0.9, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.2, 1.1],
            "potato": [0.8, 0.9, 1.0, 1.1, 1.2, 1.1, 1.0, 0.9, 0.8, 0.9, 1.0, 1.0],
            "tomato": [1.1, 1.2, 1.0, 0.9, 0.8, 0.9, 1.0, 1.1, 1.2, 1.1, 1.0, 1.0]
        }
        
        # Get pattern for commodity or use default
        commodity_lower = commodity.lower()
        pattern = patterns.get(commodity_lower, [1.0] * 12)  # Default flat pattern
        
        seasonal_factors = []
        for month, factor in enumerate(pattern, 1):
            seasonal_factors.append(SeasonalFactor(
                month=month,
                factor=factor,
                description=f"Seasonal factor for {commodity} in month {month}"
            ))
        
        return seasonal_factors
    
    def _calculate_prediction_confidence(
        self,
        price_points: List[PricePoint],
        volatility_index: float
    ) -> float:
        """Calculate prediction confidence based on data quality and volatility."""
        if not price_points:
            return 0.0
        
        # Base confidence on data quantity
        data_confidence = min(len(price_points) / 100.0, 1.0)  # Max at 100 points
        
        # Reduce confidence based on volatility
        volatility_penalty = volatility_index * 0.5
        
        # Confidence based on data recency
        latest_date = max(pp.date for pp in price_points)
        days_old = (date.today() - latest_date).days
        recency_confidence = max(0.0, 1.0 - (days_old / 30.0))  # Reduce over 30 days
        
        # Combined confidence
        confidence = (data_confidence * 0.4 + 
                     (1.0 - volatility_penalty) * 0.4 + 
                     recency_confidence * 0.2)
        
        return max(0.0, min(1.0, confidence))
    
    def _analyze_quality_distribution(self, price_data: List[PriceData]) -> Dict[str, int]:
        """Analyze quality grade distribution in price data."""
        quality_counts = {}
        
        for pd in price_data:
            grade = pd.quality_grade.value
            quality_counts[grade] = quality_counts.get(grade, 0) + 1
        
        return quality_counts
    
    async def _seasonal_arima_predict(
        self,
        historical_data: List[PricePoint],
        forecast_days: int,
        commodity: str
    ) -> PriceForecast:
        """Seasonal ARIMA prediction model (simplified implementation)."""
        try:
            if len(historical_data) < 10:
                raise ValueError("Insufficient data for ARIMA prediction")
            
            prices = [pp.price for pp in historical_data]
            
            # Simple seasonal decomposition and prediction
            # This is a simplified version - in production, use proper ARIMA libraries
            
            # Calculate trend
            trend = self._calculate_simple_trend(prices)
            
            # Get seasonal component
            seasonal_factors = await self._get_seasonal_factors(commodity)
            current_month = date.today().month
            forecast_date = date.today() + timedelta(days=forecast_days)
            forecast_month = forecast_date.month
            
            seasonal_factor = 1.0
            for sf in seasonal_factors:
                if sf.month == forecast_month:
                    seasonal_factor = sf.factor
                    break
            
            # Simple prediction: last price + trend + seasonal adjustment
            last_price = prices[-1]
            predicted_price = last_price + (trend * forecast_days) * seasonal_factor
            
            # Calculate confidence interval (±10% for simplicity)
            confidence_interval = predicted_price * 0.1
            
            return PriceForecast(
                commodity=commodity,
                forecast_date=forecast_date,
                predicted_price=predicted_price,
                confidence_interval_lower=predicted_price - confidence_interval,
                confidence_interval_upper=predicted_price + confidence_interval,
                confidence=0.7,  # Fixed confidence for simplified model
                factors_considered=["trend", "seasonal", "historical_average"],
                model_used="seasonal_arima"
            )
            
        except Exception as e:
            logger.error(f"Error in ARIMA prediction: {str(e)}")
            raise
    
    def _calculate_simple_trend(self, prices: List[float]) -> float:
        """Calculate simple linear trend from prices."""
        if len(prices) < 2:
            return 0.0
        
        n = len(prices)
        x_values = list(range(n))
        
        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(prices)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, prices))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    async def _moving_average_predict(
        self,
        historical_data: List[PricePoint],
        forecast_days: int,
        commodity: str
    ) -> PriceForecast:
        """Moving average prediction model."""
        try:
            if len(historical_data) < 5:
                raise ValueError("Insufficient data for moving average prediction")
            
            prices = [pp.price for pp in historical_data]
            
            # Calculate different moving averages
            short_ma = statistics.mean(prices[-5:])  # 5-day MA
            long_ma = statistics.mean(prices[-10:]) if len(prices) >= 10 else short_ma
            
            # Trend based on MA crossover
            trend_factor = 1.0
            if short_ma > long_ma:
                trend_factor = 1.02  # Slight upward trend
            elif short_ma < long_ma:
                trend_factor = 0.98  # Slight downward trend
            
            # Simple prediction: apply trend to last price
            last_price = prices[-1]
            predicted_price = last_price * (trend_factor ** (forecast_days / 30))
            
            # Calculate confidence interval based on recent volatility
            recent_prices = prices[-10:] if len(prices) >= 10 else prices
            volatility = statistics.stdev(recent_prices) if len(recent_prices) > 1 else 0
            confidence_interval = volatility * 1.96  # 95% confidence interval
            
            forecast_date = date.today() + timedelta(days=forecast_days)
            
            return PriceForecast(
                commodity=commodity,
                forecast_date=forecast_date,
                predicted_price=predicted_price,
                confidence_interval_lower=max(0, predicted_price - confidence_interval),
                confidence_interval_upper=predicted_price + confidence_interval,
                confidence=0.6,  # Moderate confidence for MA model
                factors_considered=["moving_average", "trend_crossover", "volatility"],
                model_used="moving_average"
            )
            
        except Exception as e:
            logger.error(f"Error in moving average prediction: {str(e)}")
            raise
    
    async def _linear_trend_predict(
        self,
        historical_data: List[PricePoint],
        forecast_days: int,
        commodity: str
    ) -> PriceForecast:
        """Linear trend prediction model."""
        try:
            if len(historical_data) < 3:
                raise ValueError("Insufficient data for linear trend prediction")
            
            prices = [pp.price for pp in historical_data]
            n = len(prices)
            
            # Calculate linear regression
            x_values = list(range(n))
            x_mean = statistics.mean(x_values)
            y_mean = statistics.mean(prices)
            
            # Calculate slope and intercept
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
            
            # Ensure positive price
            predicted_price = max(0, predicted_price)
            
            # Calculate R-squared for confidence
            y_pred = [slope * x + intercept for x in x_values]
            ss_res = sum((y - y_pred) ** 2 for y, y_pred in zip(prices, y_pred))
            ss_tot = sum((y - y_mean) ** 2 for y in prices)
            
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            confidence = max(0.3, min(0.9, r_squared))  # Clamp between 0.3 and 0.9
            
            # Calculate confidence interval based on residual standard error
            residuals = [y - y_pred for y, y_pred in zip(prices, y_pred)]
            residual_std = statistics.stdev(residuals) if len(residuals) > 1 else 0
            confidence_interval = residual_std * 1.96
            
            forecast_date = date.today() + timedelta(days=forecast_days)
            
            return PriceForecast(
                commodity=commodity,
                forecast_date=forecast_date,
                predicted_price=predicted_price,
                confidence_interval_lower=max(0, predicted_price - confidence_interval),
                confidence_interval_upper=predicted_price + confidence_interval,
                confidence=confidence,
                factors_considered=["linear_trend", "regression_analysis", "r_squared"],
                model_used="linear_trend"
            )
            
        except Exception as e:
            logger.error(f"Error in linear trend prediction: {str(e)}")
            raise
    
    async def _get_cached_result(self, cache_key: str) -> Optional[List[PriceData]]:
        """Get cached result from Redis."""
        try:
            redis = await get_redis()
            cached_data = await redis.get(cache_key)
            
            if cached_data:
                data_list = json.loads(cached_data)
                return [PriceData(**item) for item in data_list]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting cached result: {str(e)}")
            return None
    
    async def get_advanced_trend_analysis(
        self,
        commodity: str,
        location: Optional[str] = None,
        analysis_period_days: int = 365
    ) -> Dict[str, Any]:
        """
        Get advanced trend analysis including pattern recognition and anomaly detection.
        
        Args:
            commodity: Commodity name
            location: Optional location filter
            analysis_period_days: Number of days to analyze
            
        Returns:
            Dictionary with comprehensive trend analysis
        """
        try:
            # Get historical data
            end_date = date.today()
            start_date = end_date - timedelta(days=analysis_period_days)
            
            price_points = await self._get_historical_prices(
                commodity, start_date, end_date, location
            )
            
            if len(price_points) < 30:
                logger.warning(f"Insufficient data for advanced analysis: {len(price_points)} points")
                return {
                    "error": "insufficient_data",
                    "message": "Need at least 30 data points for advanced analysis",
                    "data_points": len(price_points)
                }
            
            prices = [pp.price for pp in price_points]
            dates = [pp.date for pp in price_points]
            
            # Calculate various trend metrics
            analysis = {
                "commodity": commodity,
                "location": location,
                "analysis_period": analysis_period_days,
                "data_points": len(price_points),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                
                # Basic statistics
                "price_statistics": {
                    "mean": statistics.mean(prices),
                    "median": statistics.median(prices),
                    "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0,
                    "min": min(prices),
                    "max": max(prices),
                    "range": max(prices) - min(prices),
                    "coefficient_of_variation": statistics.stdev(prices) / statistics.mean(prices) if statistics.mean(prices) > 0 and len(prices) > 1 else 0
                },
                
                # Trend analysis
                "trend_analysis": await self._calculate_trend_metrics(price_points),
                
                # Seasonal patterns
                "seasonal_patterns": await self._detect_seasonal_patterns(price_points),
                
                # Volatility analysis
                "volatility_analysis": self._calculate_volatility_metrics(prices),
                
                # Anomaly detection
                "anomalies": self._detect_price_anomalies(price_points),
                
                # Support and resistance levels
                "support_resistance": self._calculate_support_resistance(prices),
                
                # Moving averages
                "moving_averages": self._calculate_moving_averages(prices),
                
                # Price momentum
                "momentum_indicators": self._calculate_momentum_indicators(prices)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in advanced trend analysis: {str(e)}")
            raise
    
    async def _calculate_trend_metrics(self, price_points: List[PricePoint]) -> Dict[str, Any]:
        """Calculate comprehensive trend metrics."""
        prices = [pp.price for pp in price_points]
        n = len(prices)
        
        if n < 2:
            return {"error": "insufficient_data"}
        
        # Linear regression for overall trend
        x_values = list(range(n))
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(prices)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, prices))
        denominator = sum((x - x_mean) ** 2 for x in x_values)
        
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Calculate R-squared
        y_pred = [slope * x + intercept for x in x_values]
        ss_res = sum((y - y_pred) ** 2 for y, y_pred in zip(prices, y_pred))
        ss_tot = sum((y - y_mean) ** 2 for y in prices)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Trend strength classification
        if abs(slope) < 0.1:
            trend_strength = "weak"
        elif abs(slope) < 1.0:
            trend_strength = "moderate"
        else:
            trend_strength = "strong"
        
        # Trend direction
        if slope > 0.1:
            trend_direction = "bullish"
        elif slope < -0.1:
            trend_direction = "bearish"
        else:
            trend_direction = "sideways"
        
        return {
            "slope": slope,
            "intercept": intercept,
            "r_squared": r_squared,
            "trend_direction": trend_direction,
            "trend_strength": trend_strength,
            "daily_change_rate": slope,
            "projected_30_day_change": slope * 30,
            "trend_reliability": "high" if r_squared > 0.7 else "medium" if r_squared > 0.4 else "low"
        }
    
    async def _detect_seasonal_patterns(self, price_points: List[PricePoint]) -> Dict[str, Any]:
        """Detect seasonal patterns in price data."""
        if len(price_points) < 90:  # Need at least 3 months of data
            return {"error": "insufficient_data_for_seasonal_analysis"}
        
        # Group prices by month
        monthly_prices = {}
        for pp in price_points:
            month = pp.date.month
            if month not in monthly_prices:
                monthly_prices[month] = []
            monthly_prices[month].append(pp.price)
        
        # Calculate monthly averages
        monthly_averages = {}
        for month, prices in monthly_prices.items():
            monthly_averages[month] = statistics.mean(prices)
        
        # Calculate seasonal factors (relative to annual average)
        annual_average = statistics.mean([avg for avg in monthly_averages.values()])
        seasonal_factors = {}
        for month, avg in monthly_averages.items():
            seasonal_factors[month] = avg / annual_average if annual_average > 0 else 1.0
        
        # Identify peak and trough months
        peak_month = max(seasonal_factors.keys(), key=lambda k: seasonal_factors[k])
        trough_month = min(seasonal_factors.keys(), key=lambda k: seasonal_factors[k])
        
        # Calculate seasonality strength
        factor_values = list(seasonal_factors.values())
        seasonality_strength = statistics.stdev(factor_values) if len(factor_values) > 1 else 0
        
        return {
            "monthly_averages": monthly_averages,
            "seasonal_factors": seasonal_factors,
            "peak_month": peak_month,
            "trough_month": trough_month,
            "seasonality_strength": seasonality_strength,
            "seasonal_classification": "high" if seasonality_strength > 0.2 else "moderate" if seasonality_strength > 0.1 else "low"
        }
    
    def _calculate_volatility_metrics(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate comprehensive volatility metrics."""
        if len(prices) < 2:
            return {"error": "insufficient_data"}
        
        # Basic volatility
        mean_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices)
        coefficient_of_variation = std_dev / mean_price if mean_price > 0 else 0
        
        # Rolling volatility (if enough data)
        rolling_volatilities = []
        window_size = min(30, len(prices) // 3)  # 30-day or 1/3 of data
        
        if len(prices) >= window_size:
            for i in range(window_size, len(prices)):
                window_prices = prices[i-window_size:i]
                window_std = statistics.stdev(window_prices)
                window_mean = statistics.mean(window_prices)
                rolling_cv = window_std / window_mean if window_mean > 0 else 0
                rolling_volatilities.append(rolling_cv)
        
        # Volatility classification
        if coefficient_of_variation < 0.1:
            volatility_class = "low"
        elif coefficient_of_variation < 0.2:
            volatility_class = "moderate"
        else:
            volatility_class = "high"
        
        return {
            "standard_deviation": std_dev,
            "coefficient_of_variation": coefficient_of_variation,
            "volatility_classification": volatility_class,
            "rolling_volatility_avg": statistics.mean(rolling_volatilities) if rolling_volatilities else None,
            "volatility_trend": "increasing" if len(rolling_volatilities) > 10 and rolling_volatilities[-5:] > rolling_volatilities[:5] else "stable"
        }
    
    def _detect_price_anomalies(self, price_points: List[PricePoint]) -> List[Dict[str, Any]]:
        """Detect price anomalies using statistical methods."""
        if len(price_points) < 10:
            return []
        
        prices = [pp.price for pp in price_points]
        mean_price = statistics.mean(prices)
        std_dev = statistics.stdev(prices)
        
        anomalies = []
        threshold = 2.0  # 2 standard deviations
        
        for i, pp in enumerate(price_points):
            z_score = abs(pp.price - mean_price) / std_dev if std_dev > 0 else 0
            
            if z_score > threshold:
                anomaly_type = "spike" if pp.price > mean_price else "drop"
                severity = "extreme" if z_score > 3.0 else "moderate"
                
                anomalies.append({
                    "date": pp.date.isoformat(),
                    "price": pp.price,
                    "z_score": z_score,
                    "type": anomaly_type,
                    "severity": severity,
                    "deviation_from_mean": pp.price - mean_price,
                    "percentage_deviation": ((pp.price - mean_price) / mean_price) * 100
                })
        
        return anomalies
    
    def _calculate_support_resistance(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate support and resistance levels."""
        if len(prices) < 20:
            return {"error": "insufficient_data"}
        
        # Sort prices to find levels
        sorted_prices = sorted(prices)
        n = len(sorted_prices)
        
        # Support levels (lower quartiles)
        support_1 = sorted_prices[n // 4]  # 25th percentile
        support_2 = sorted_prices[n // 10]  # 10th percentile
        
        # Resistance levels (upper quartiles)
        resistance_1 = sorted_prices[3 * n // 4]  # 75th percentile
        resistance_2 = sorted_prices[9 * n // 10]  # 90th percentile
        
        # Current price position
        current_price = prices[-1]
        
        return {
            "support_levels": [support_2, support_1],
            "resistance_levels": [resistance_1, resistance_2],
            "current_price": current_price,
            "position": "above_resistance" if current_price > resistance_1 else 
                       "below_support" if current_price < support_1 else "in_range"
        }
    
    def _calculate_moving_averages(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate various moving averages."""
        if len(prices) < 5:
            return {"error": "insufficient_data"}
        
        moving_averages = {}
        
        # Calculate different MA periods
        periods = [5, 10, 20, 50]
        for period in periods:
            if len(prices) >= period:
                ma = statistics.mean(prices[-period:])
                moving_averages[f"ma_{period}"] = ma
        
        # Current price vs MAs
        current_price = prices[-1]
        ma_signals = {}
        
        for period_key, ma_value in moving_averages.items():
            if current_price > ma_value:
                ma_signals[period_key] = "bullish"
            elif current_price < ma_value:
                ma_signals[period_key] = "bearish"
            else:
                ma_signals[period_key] = "neutral"
        
        return {
            "moving_averages": moving_averages,
            "current_price": current_price,
            "ma_signals": ma_signals
        }
    
    def _calculate_momentum_indicators(self, prices: List[float]) -> Dict[str, Any]:
        """Calculate momentum indicators."""
        if len(prices) < 14:
            return {"error": "insufficient_data"}
        
        # Rate of Change (ROC)
        roc_periods = [5, 10, 20]
        roc_values = {}
        
        for period in roc_periods:
            if len(prices) > period:
                current = prices[-1]
                past = prices[-period-1]
                roc = ((current - past) / past) * 100 if past > 0 else 0
                roc_values[f"roc_{period}"] = roc
        
        # Relative Strength Index (RSI) - simplified
        rsi = self._calculate_simple_rsi(prices)
        
        # Price momentum classification
        recent_roc = roc_values.get("roc_10", 0)
        if recent_roc > 5:
            momentum = "strong_bullish"
        elif recent_roc > 2:
            momentum = "bullish"
        elif recent_roc < -5:
            momentum = "strong_bearish"
        elif recent_roc < -2:
            momentum = "bearish"
        else:
            momentum = "neutral"
        
        return {
            "rate_of_change": roc_values,
            "rsi": rsi,
            "momentum_classification": momentum
        }
    
    def _calculate_simple_rsi(self, prices: List[float], period: int = 14) -> Optional[float]:
        """Calculate a simplified RSI."""
        if len(prices) < period + 1:
            return None
        
        # Calculate price changes
        changes = []
        for i in range(1, len(prices)):
            changes.append(prices[i] - prices[i-1])
        
        # Separate gains and losses
        gains = [change if change > 0 else 0 for change in changes[-period:]]
        losses = [-change if change < 0 else 0 for change in changes[-period:]]
        
        avg_gain = statistics.mean(gains)
        avg_loss = statistics.mean(losses)
        
        if avg_loss == 0:
            return 100  # All gains, RSI = 100
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    async def get_ensemble_price_prediction(
        self,
        commodity: str,
        forecast_days: int,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get ensemble price prediction using multiple ML models.
        
        Args:
            commodity: Commodity name
            forecast_days: Number of days to forecast
            location: Optional location filter
            
        Returns:
            Dictionary with ensemble prediction results
        """
        try:
            # Get historical data
            end_date = date.today()
            start_date = end_date - timedelta(days=730)  # 2 years of data
            
            historical_data = await self._get_historical_prices(
                commodity, start_date, end_date, location
            )
            
            if len(historical_data) < 30:
                return {
                    "error": "insufficient_data",
                    "message": "Need at least 30 data points for ensemble prediction",
                    "data_points": len(historical_data)
                }
            
            # Run multiple prediction models
            predictions = {}
            model_weights = {}
            
            try:
                # Seasonal ARIMA
                arima_forecast = await self._seasonal_arima_predict(
                    historical_data, forecast_days, commodity
                )
                predictions["seasonal_arima"] = arima_forecast
                model_weights["seasonal_arima"] = 0.4  # Higher weight for ARIMA
            except Exception as e:
                logger.warning(f"ARIMA prediction failed: {str(e)}")
            
            try:
                # Moving Average
                ma_forecast = await self._moving_average_predict(
                    historical_data, forecast_days, commodity
                )
                predictions["moving_average"] = ma_forecast
                model_weights["moving_average"] = 0.3
            except Exception as e:
                logger.warning(f"Moving average prediction failed: {str(e)}")
            
            try:
                # Linear Trend
                trend_forecast = await self._linear_trend_predict(
                    historical_data, forecast_days, commodity
                )
                predictions["linear_trend"] = trend_forecast
                model_weights["linear_trend"] = 0.3
            except Exception as e:
                logger.warning(f"Linear trend prediction failed: {str(e)}")
            
            if not predictions:
                return {
                    "error": "all_models_failed",
                    "message": "All prediction models failed to generate forecasts"
                }
            
            # Calculate ensemble prediction
            ensemble_prediction = self._calculate_ensemble_prediction(
                predictions, model_weights
            )
            
            # Add model comparison
            model_comparison = self._compare_model_predictions(predictions)
            
            return {
                "commodity": commodity,
                "location": location,
                "forecast_days": forecast_days,
                "ensemble_prediction": ensemble_prediction,
                "individual_predictions": {k: v.dict() for k, v in predictions.items()},
                "model_comparison": model_comparison,
                "data_points_used": len(historical_data),
                "prediction_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in ensemble prediction: {str(e)}")
            raise
    
    def _calculate_ensemble_prediction(
        self,
        predictions: Dict[str, PriceForecast],
        weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate weighted ensemble prediction."""
        if not predictions:
            return {}
        
        # Normalize weights
        total_weight = sum(weights.get(model, 0) for model in predictions.keys())
        if total_weight == 0:
            # Equal weights if no weights specified
            normalized_weights = {model: 1.0/len(predictions) for model in predictions.keys()}
        else:
            normalized_weights = {model: weights.get(model, 0)/total_weight for model in predictions.keys()}
        
        # Calculate weighted averages
        weighted_price = sum(
            pred.predicted_price * normalized_weights[model]
            for model, pred in predictions.items()
        )
        
        weighted_confidence = sum(
            pred.confidence * normalized_weights[model]
            for model, pred in predictions.items()
        )
        
        # Calculate ensemble confidence interval
        lower_bounds = [pred.confidence_interval_lower for pred in predictions.values()]
        upper_bounds = [pred.confidence_interval_upper for pred in predictions.values()]
        
        ensemble_lower = sum(
            lower * normalized_weights[model]
            for model, lower in zip(predictions.keys(), lower_bounds)
        )
        
        ensemble_upper = sum(
            upper * normalized_weights[model]
            for model, upper in zip(predictions.keys(), upper_bounds)
        )
        
        # Get forecast date (should be same for all models)
        forecast_date = list(predictions.values())[0].forecast_date
        
        return {
            "predicted_price": weighted_price,
            "confidence": weighted_confidence,
            "confidence_interval_lower": ensemble_lower,
            "confidence_interval_upper": ensemble_upper,
            "forecast_date": forecast_date.isoformat(),
            "model_weights": normalized_weights,
            "ensemble_method": "weighted_average"
        }
    
    def _compare_model_predictions(
        self,
        predictions: Dict[str, PriceForecast]
    ) -> Dict[str, Any]:
        """Compare predictions from different models."""
        if len(predictions) < 2:
            return {"message": "Need at least 2 models for comparison"}
        
        prices = [pred.predicted_price for pred in predictions.values()]
        confidences = [pred.confidence for pred in predictions.values()]
        
        comparison = {
            "price_range": {
                "min": min(prices),
                "max": max(prices),
                "spread": max(prices) - min(prices),
                "spread_percentage": ((max(prices) - min(prices)) / statistics.mean(prices)) * 100
            },
            "confidence_range": {
                "min": min(confidences),
                "max": max(confidences),
                "average": statistics.mean(confidences)
            },
            "model_agreement": "high" if (max(prices) - min(prices)) / statistics.mean(prices) < 0.1 else "low",
            "individual_models": {}
        }
        
        # Add individual model details
        for model_name, pred in predictions.items():
            comparison["individual_models"][model_name] = {
                "predicted_price": pred.predicted_price,
                "confidence": pred.confidence,
                "factors_considered": pred.factors_considered,
                "relative_to_ensemble": "above" if pred.predicted_price > statistics.mean(prices) else "below"
            }
        
        return comparison
    
    async def store_trend_analysis_results(
        self,
        commodity: str,
        location: Optional[str],
        analysis_results: Dict[str, Any]
    ) -> str:
        """
        Store trend analysis results in database for future reference.
        
        Args:
            commodity: Commodity name
            location: Location filter used
            analysis_results: Analysis results to store
            
        Returns:
            Analysis ID
        """
        try:
            db = await get_database()
            collection = db.trend_analysis
            
            # Prepare document
            document = {
                "commodity": commodity,
                "location": location,
                "analysis_results": analysis_results,
                "created_at": datetime.utcnow(),
                "analysis_type": "advanced_trend_analysis"
            }
            
            # Insert document
            result = await collection.insert_one(document)
            analysis_id = str(result.inserted_id)
            
            logger.info(f"Stored trend analysis results with ID: {analysis_id}")
            return analysis_id
            
        except Exception as e:
            logger.error(f"Error storing trend analysis results: {str(e)}")
            raise
    
    async def get_stored_trend_analysis(
        self,
        commodity: str,
        location: Optional[str] = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get previously stored trend analysis results.
        
        Args:
            commodity: Commodity name
            location: Optional location filter
            days_back: Number of days to look back
            
        Returns:
            List of stored analysis results
        """
        try:
            db = await get_database()
            collection = db.trend_analysis
            
            # Build query
            query = {
                "commodity": {"$regex": commodity, "$options": "i"},
                "created_at": {
                    "$gte": datetime.utcnow() - timedelta(days=days_back)
                }
            }
            
            if location:
                query["location"] = {"$regex": location, "$options": "i"}
            
            # Execute query
            cursor = collection.find(query).sort("created_at", -1).limit(10)
            documents = await cursor.to_list(length=10)
            
            # Convert ObjectId to string
            for doc in documents:
                doc["_id"] = str(doc["_id"])
                doc["created_at"] = doc["created_at"].isoformat()
            
            return documents
            
        except Exception as e:
            logger.error(f"Error getting stored trend analysis: {str(e)}")
            return []
    
    async def _cache_result(
        self,
        cache_key: str,
        data: List[PriceData],
        ttl: int = 300
    ) -> None:
        """Cache result in Redis."""
        try:
            redis = await get_redis()
            
            # Convert to JSON serializable format
            data_list = [item.dict() for item in data]
            
            await redis.setex(
                cache_key,
                ttl,
                json.dumps(data_list, default=str)
            )
            
        except Exception as e:
            logger.error(f"Error caching result: {str(e)}")
    
    # Geographic Price Filtering Methods
    
    async def get_prices_within_radius(
        self,
        commodity: str,
        center_location: Location,
        radius_km: int = 50,
        quality_grades: Optional[List[QualityGrade]] = None,
        market_types: Optional[List[MarketType]] = None,
        include_msp_comparison: bool = True
    ) -> RadiusFilterResult:
        """
        Get prices within a specified radius of a center location.
        
        Args:
            commodity: Commodity name
            center_location: Center location with coordinates
            radius_km: Search radius in kilometers
            quality_grades: Optional quality grade filters
            market_types: Optional market type filters
            include_msp_comparison: Include MSP comparison data
            
        Returns:
            RadiusFilterResult with filtered prices and analysis
        """
        try:
            # Create query object
            query = GeographicPriceQuery(
                commodity=commodity,
                center_location=center_location,
                radius_km=radius_km,
                quality_grades=quality_grades,
                market_types=market_types,
                include_msp_comparison=include_msp_comparison
            )
            
            # Get all current prices for the commodity
            all_prices = await self.get_current_prices(commodity)
            
            # Filter by distance and other criteria
            filtered_results = []
            
            for price_data in all_prices:
                # Calculate distance if coordinates are available
                distance = None
                if (center_location.latitude and center_location.longitude and
                    price_data.location.latitude and price_data.location.longitude):
                    distance = center_location.distance_to(price_data.location)
                    
                    # Skip if outside radius
                    if distance and distance > radius_km:
                        continue
                
                # Apply quality grade filter
                if quality_grades and price_data.quality_grade not in quality_grades:
                    continue
                
                # Apply market type filter
                if market_types and price_data.market_type not in market_types:
                    continue
                
                # Get MSP comparison if requested
                msp_comparison = None
                if include_msp_comparison:
                    is_below_msp, msp_data = await self.check_price_below_msp(
                        commodity, price_data.price_modal
                    )
                    if msp_data:
                        msp_comparison = {
                            "msp_price": msp_data.msp_price,
                            "is_below_msp": is_below_msp,
                            "price_difference": price_data.price_modal - msp_data.msp_price,
                            "percentage_difference": ((price_data.price_modal - msp_data.msp_price) / msp_data.msp_price) * 100
                        }
                
                filtered_results.append(GeographicPriceResult(
                    price_data=price_data,
                    distance_km=distance,
                    msp_comparison=msp_comparison
                ))
            
            # Calculate statistics
            if filtered_results:
                prices = [r.price_data.price_modal for r in filtered_results]
                distances = [r.distance_km for r in filtered_results if r.distance_km is not None]
                
                price_statistics = {
                    "min": min(prices),
                    "max": max(prices),
                    "average": statistics.mean(prices),
                    "median": statistics.median(prices),
                    "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0,
                    "spread": max(prices) - min(prices)
                }
                
                distance_statistics = {}
                if distances:
                    distance_statistics = {
                        "min": min(distances),
                        "max": max(distances),
                        "average": statistics.mean(distances),
                        "median": statistics.median(distances)
                    }
                
                # Quality distribution
                quality_distribution = {}
                for result in filtered_results:
                    grade = result.price_data.quality_grade.value
                    quality_distribution[grade] = quality_distribution.get(grade, 0) + 1
                
                # MSP analysis
                msp_analysis = None
                if include_msp_comparison:
                    msp_results = [r.msp_comparison for r in filtered_results if r.msp_comparison]
                    if msp_results:
                        below_msp_count = sum(1 for r in msp_results if r["is_below_msp"])
                        msp_analysis = {
                            "total_markets_with_msp": len(msp_results),
                            "markets_below_msp": below_msp_count,
                            "percentage_below_msp": (below_msp_count / len(msp_results)) * 100,
                            "average_msp_difference": statistics.mean([r["price_difference"] for r in msp_results])
                        }
            else:
                price_statistics = {}
                distance_statistics = {}
                quality_distribution = {}
                msp_analysis = None
            
            return RadiusFilterResult(
                query=query,
                results=filtered_results,
                total_markets=len(filtered_results),
                average_price=price_statistics.get("average"),
                price_statistics=price_statistics,
                distance_statistics=distance_statistics,
                msp_analysis=msp_analysis,
                quality_distribution=quality_distribution
            )
            
        except Exception as e:
            logger.error(f"Error filtering prices by radius: {str(e)}")
            raise
    
    async def compare_markets_within_radius(
        self,
        commodity: str,
        center_location: Location,
        radius_km: int = 50
    ) -> GeographicMarketComparison:
        """
        Compare markets within a specified radius.
        
        Args:
            commodity: Commodity name
            center_location: Center location with coordinates
            radius_km: Search radius in kilometers
            
        Returns:
            GeographicMarketComparison with market analysis
        """
        try:
            # Get prices within radius
            radius_result = await self.get_prices_within_radius(
                commodity, center_location, radius_km
            )
            
            # Group by market
            market_data = {}
            for result in radius_result.results:
                market_name = result.price_data.market_name
                
                if market_name not in market_data:
                    market_data[market_name] = {
                        "location": result.price_data.location,
                        "distance": result.distance_km,
                        "prices": [],
                        "quality_grades": set()
                    }
                
                market_data[market_name]["prices"].append(result.price_data)
                market_data[market_name]["quality_grades"].add(result.price_data.quality_grade)
            
            # Create market info objects
            markets = []
            for market_name, data in market_data.items():
                prices = [p.price_modal for p in data["prices"]]
                average_price = statistics.mean(prices) if prices else None
                
                market_info = MarketDistanceInfo(
                    market_name=market_name,
                    location=data["location"],
                    distance_km=data["distance"],
                    price_data=data["prices"],
                    average_price=average_price,
                    quality_grades_available=list(data["quality_grades"])
                )
                markets.append(market_info)
            
            # Find best price and nearest market
            best_price_market = None
            nearest_market = None
            
            if markets:
                # Best price (lowest for buyers)
                markets_with_prices = [m for m in markets if m.average_price is not None]
                if markets_with_prices:
                    best_market = min(markets_with_prices, key=lambda m: m.average_price)
                    best_price_market = best_market.market_name
                
                # Nearest market
                markets_with_distance = [m for m in markets if m.distance_km is not None]
                if markets_with_distance:
                    nearest = min(markets_with_distance, key=lambda m: m.distance_km)
                    nearest_market = nearest.market_name
            
            # Calculate ranges
            all_prices = [m.average_price for m in markets if m.average_price is not None]
            all_distances = [m.distance_km for m in markets if m.distance_km is not None]
            
            price_range = {}
            if all_prices:
                price_range = {
                    "min": min(all_prices),
                    "max": max(all_prices),
                    "spread": max(all_prices) - min(all_prices)
                }
            
            distance_range = {}
            if all_distances:
                distance_range = {
                    "min": min(all_distances),
                    "max": max(all_distances),
                    "average": statistics.mean(all_distances)
                }
            
            # Generate recommendations
            recommendations = []
            if best_price_market and nearest_market:
                if best_price_market == nearest_market:
                    recommendations.append(f"{best_price_market} offers both best price and shortest distance")
                else:
                    recommendations.append(f"Best price: {best_price_market}")
                    recommendations.append(f"Nearest market: {nearest_market}")
            
            if len(markets) > 3:
                recommendations.append(f"Multiple options available - {len(markets)} markets within {radius_km}km")
            
            return GeographicMarketComparison(
                commodity=commodity,
                center_location=center_location,
                radius_km=radius_km,
                markets=markets,
                comparison_date=date.today(),
                best_price_market=best_price_market,
                nearest_market=nearest_market,
                price_range=price_range,
                distance_range=distance_range,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error comparing markets within radius: {str(e)}")
            raise
    
    async def get_quality_based_price_categorization(
        self,
        commodity: str,
        location: Optional[str] = None,
        radius_km: int = 50
    ) -> QualityPriceCategorization:
        """
        Get quality-based price categorization for a commodity.
        
        Args:
            commodity: Commodity name
            location: Optional location filter
            radius_km: Search radius if location provided
            
        Returns:
            QualityPriceCategorization with quality analysis
        """
        try:
            # Get current prices
            if location:
                # Create a dummy location for radius search
                # In production, you'd geocode the location string
                center_location = Location(
                    state=location,
                    district=location,
                    market_name=location,
                    latitude=None,
                    longitude=None
                )
                prices = await self.get_current_prices(commodity, location, radius_km)
            else:
                prices = await self.get_current_prices(commodity)
            
            # Group by quality grade
            quality_groups = {}
            for price_data in prices:
                grade = price_data.quality_grade
                if grade not in quality_groups:
                    quality_groups[grade] = []
                quality_groups[grade].append(price_data)
            
            # Calculate categories
            categories = []
            standard_average = None
            
            for quality_grade, price_list in quality_groups.items():
                prices_values = [p.price_modal for p in price_list]
                
                if prices_values:
                    price_range = {
                        "min": min(prices_values),
                        "max": max(prices_values),
                        "average": statistics.mean(prices_values)
                    }
                    
                    # Calculate availability score based on market count and volume
                    market_count = len(set(p.market_name for p in price_list))
                    total_arrivals = sum(p.arrivals or 0 for p in price_list)
                    
                    # Normalize availability score (0-1)
                    availability_score = min(1.0, (market_count / 10.0) + (total_arrivals / 1000.0))
                    
                    # Store standard grade average for premium calculation
                    if quality_grade == QualityGrade.STANDARD:
                        standard_average = price_range["average"]
                    
                    category = QualityBasedPriceCategory(
                        commodity=commodity,
                        location=location,
                        quality_grade=quality_grade,
                        price_range=price_range,
                        market_count=market_count,
                        availability_score=availability_score
                    )
                    categories.append(category)
            
            # Calculate premium percentages
            if standard_average:
                for category in categories:
                    if category.quality_grade != QualityGrade.STANDARD:
                        premium_percentage = ((category.price_range["average"] - standard_average) / standard_average) * 100
                        category.price_premium_percentage = premium_percentage
            
            # Overall statistics
            all_prices = [p.price_modal for p in prices]
            overall_statistics = {}
            
            if all_prices:
                overall_statistics = {
                    "total_markets": len(set(p.market_name for p in prices)),
                    "total_price_points": len(all_prices),
                    "overall_average": statistics.mean(all_prices),
                    "price_range": max(all_prices) - min(all_prices),
                    "quality_diversity": len(quality_groups),
                    "dominant_quality": max(quality_groups.keys(), key=lambda k: len(quality_groups[k])).value
                }
            
            # Generate recommendations
            recommendations = []
            
            # Find best value quality
            if len(categories) > 1:
                best_value = min(categories, key=lambda c: c.price_range["average"] / max(c.availability_score, 0.1))
                recommendations.append(f"Best value: {best_value.quality_grade.value} grade")
            
            # Premium availability
            premium_categories = [c for c in categories if c.quality_grade == QualityGrade.PREMIUM]
            if premium_categories and premium_categories[0].availability_score > 0.5:
                recommendations.append("Premium quality widely available")
            
            # Price spread analysis
            if len(categories) > 1:
                price_spreads = [c.price_range["max"] - c.price_range["min"] for c in categories]
                avg_spread = statistics.mean(price_spreads)
                if avg_spread > overall_statistics.get("overall_average", 0) * 0.2:
                    recommendations.append("High price variation - negotiate carefully")
            
            return QualityPriceCategorization(
                commodity=commodity,
                location=location,
                analysis_date=date.today(),
                categories=categories,
                overall_statistics=overall_statistics,
                quality_recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Error in quality-based price categorization: {str(e)}")
            raise
    
    async def get_location_based_price_variations(
        self,
        commodity: str,
        center_location: Location,
        radius_km: int = 50
    ) -> Dict[str, Any]:
        """
        Analyze location-based price variations (wholesale vs retail, urban vs rural).
        
        Args:
            commodity: Commodity name
            center_location: Center location for analysis
            radius_km: Analysis radius
            
        Returns:
            Dictionary with location-based price analysis
        """
        try:
            # Get prices within radius
            radius_result = await self.get_prices_within_radius(
                commodity, center_location, radius_km
            )
            
            # Categorize by market type and location characteristics
            market_type_analysis = {}
            location_analysis = {
                "urban": [],
                "rural": [],
                "semi_urban": []
            }
            
            for result in radius_result.results:
                price_data = result.price_data
                
                # Market type analysis
                market_type = price_data.market_type.value
                if market_type not in market_type_analysis:
                    market_type_analysis[market_type] = []
                market_type_analysis[market_type].append(price_data.price_modal)
                
                # Location type classification (simplified heuristic)
                # In production, this would use more sophisticated classification
                location_name = price_data.location.market_name.lower()
                if any(keyword in location_name for keyword in ["city", "metro", "urban", "mall"]):
                    location_analysis["urban"].append(price_data.price_modal)
                elif any(keyword in location_name for keyword in ["village", "rural", "gram"]):
                    location_analysis["rural"].append(price_data.price_modal)
                else:
                    location_analysis["semi_urban"].append(price_data.price_modal)
            
            # Calculate statistics for market types
            market_type_stats = {}
            for market_type, prices in market_type_analysis.items():
                if prices:
                    market_type_stats[market_type] = {
                        "average_price": statistics.mean(prices),
                        "min_price": min(prices),
                        "max_price": max(prices),
                        "market_count": len(prices),
                        "price_std": statistics.stdev(prices) if len(prices) > 1 else 0
                    }
            
            # Calculate statistics for location types
            location_type_stats = {}
            for location_type, prices in location_analysis.items():
                if prices:
                    location_type_stats[location_type] = {
                        "average_price": statistics.mean(prices),
                        "min_price": min(prices),
                        "max_price": max(prices),
                        "market_count": len(prices),
                        "price_std": statistics.stdev(prices) if len(prices) > 1 else 0
                    }
            
            # Price variation analysis
            price_variations = {}
            
            # Wholesale vs Retail comparison
            if "wholesale" in market_type_stats and "retail" in market_type_stats:
                wholesale_avg = market_type_stats["wholesale"]["average_price"]
                retail_avg = market_type_stats["retail"]["average_price"]
                price_variations["wholesale_retail_difference"] = {
                    "absolute_difference": retail_avg - wholesale_avg,
                    "percentage_difference": ((retail_avg - wholesale_avg) / wholesale_avg) * 100,
                    "retail_premium": retail_avg > wholesale_avg
                }
            
            # Urban vs Rural comparison
            if "urban" in location_type_stats and "rural" in location_type_stats:
                urban_avg = location_type_stats["urban"]["average_price"]
                rural_avg = location_type_stats["rural"]["average_price"]
                price_variations["urban_rural_difference"] = {
                    "absolute_difference": urban_avg - rural_avg,
                    "percentage_difference": ((urban_avg - rural_avg) / rural_avg) * 100,
                    "urban_premium": urban_avg > rural_avg
                }
            
            return {
                "commodity": commodity,
                "center_location": center_location.dict(),
                "radius_km": radius_km,
                "analysis_date": date.today().isoformat(),
                "market_type_analysis": market_type_stats,
                "location_type_analysis": location_type_stats,
                "price_variations": price_variations,
                "total_markets_analyzed": len(radius_result.results),
                "recommendations": self._generate_location_recommendations(
                    market_type_stats, location_type_stats, price_variations
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing location-based price variations: {str(e)}")
            raise
    
    def _generate_location_recommendations(
        self,
        market_type_stats: Dict[str, Any],
        location_type_stats: Dict[str, Any],
        price_variations: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on location analysis."""
        recommendations = []
        
        # Market type recommendations
        if market_type_stats:
            best_market_type = min(market_type_stats.keys(), 
                                 key=lambda k: market_type_stats[k]["average_price"])
            recommendations.append(f"Best prices found in {best_market_type} markets")
        
        # Location type recommendations
        if location_type_stats:
            best_location_type = min(location_type_stats.keys(),
                                   key=lambda k: location_type_stats[k]["average_price"])
            recommendations.append(f"Lowest prices in {best_location_type} areas")
        
        # Price variation insights
        if "wholesale_retail_difference" in price_variations:
            diff = price_variations["wholesale_retail_difference"]
            if abs(diff["percentage_difference"]) > 10:
                recommendations.append(f"Significant wholesale-retail price gap: {diff['percentage_difference']:.1f}%")
        
        if "urban_rural_difference" in price_variations:
            diff = price_variations["urban_rural_difference"]
            if abs(diff["percentage_difference"]) > 15:
                recommendations.append(f"Notable urban-rural price difference: {diff['percentage_difference']:.1f}%")
        
        return recommendations


# Global service instance
price_discovery_service = PriceDiscoveryService()