"""
Market data service for external API integration and data management.

This service handles integration with external market data sources like Agmarknet,
data validation, caching, price history tracking, and ML-based price predictions.
"""

import asyncio
import json
import logging
import math
import random
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from urllib.parse import urlencode

import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..core.config import settings
from ..core.redis import get_redis_client
from ..models.market_data import (
    MarketPrice, PriceHistory, DataValidationResult, MarketDataCache,
    DataSource, DataQuality, PriceUnit, AgmarknetApiResponse,
    MarketPriceRequest, MarketPriceResponse, PriceHistoryRequest, PriceHistoryResponse,
    DataSyncStatus
)

logger = logging.getLogger(__name__)


class MarketDataService:
    """Service for managing external market data integration."""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.market_prices_collection = database.market_prices
        self.price_history_collection = database.price_history
        self.data_sync_status_collection = database.data_sync_status
        self.redis_client = None
        
        # API configuration
        self.agmarknet_base_url = settings.AGMARKNET_BASE_URL
        self.agmarknet_api_key = settings.AGMARKNET_API_KEY
        self.cache_ttl = settings.PRICE_CACHE_TTL
        
        # HTTP client for API calls
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
    
    async def initialize(self):
        """Initialize the service with Redis connection."""
        self.redis_client = await get_redis_client()
        
        # Create indexes for efficient querying
        await self._create_indexes()
    
    async def _create_indexes(self):
        """Create database indexes for market data collections."""
        try:
            # Market prices indexes
            await self.market_prices_collection.create_index([
                ("commodity", 1), ("market", 1), ("date", -1)
            ])
            await self.market_prices_collection.create_index([
                ("commodity", 1), ("state", 1), ("date", -1)
            ])
            await self.market_prices_collection.create_index([("date", -1)])
            await self.market_prices_collection.create_index([("source", 1), ("date", -1)])
            
            # Price history indexes
            await self.price_history_collection.create_index([
                ("commodity", 1), ("market", 1), ("period_start", -1)
            ])
            
            logger.info("Market data indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating market data indexes: {e}")
    
    async def fetch_agmarknet_data(
        self,
        commodity: str,
        state: Optional[str] = None,
        market: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[MarketPrice]:
        """
        Fetch market data from Agmarknet API.
        
        Args:
            commodity: Commodity name
            state: State name (optional)
            market: Market name (optional)
            date_from: Start date (optional)
            date_to: End date (optional)
            
        Returns:
            List of MarketPrice objects
        """
        try:
            # Build API parameters
            params = {
                "api-key": self.agmarknet_api_key,
                "format": "json",
                "filters[commodity]": commodity.lower()
            }
            
            if state:
                params["filters[state]"] = state.lower()
            if market:
                params["filters[market]"] = market.lower()
            if date_from:
                params["filters[date][from]"] = date_from.strftime("%Y-%m-%d")
            if date_to:
                params["filters[date][to]"] = date_to.strftime("%Y-%m-%d")
            
            # Make API request
            url = f"{self.agmarknet_base_url}/9ef84268-d588-465a-a308-a864a43d0070"
            
            logger.info(f"Fetching Agmarknet data for commodity: {commodity}")
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            
            # Parse response
            data = response.json()
            api_response = AgmarknetApiResponse(**data)
            
            # Convert to MarketPrice objects
            market_prices = api_response.to_market_prices()
            
            # Validate and filter data
            validated_prices = []
            for price in market_prices:
                validation_result = await self.validate_market_data(price)
                if validation_result.is_valid:
                    price.data_quality = self._determine_data_quality(validation_result)
                    price.is_validated = True
                    validated_prices.append(price)
                else:
                    logger.warning(f"Invalid market data for {commodity}: {validation_result.issues}")
            
            logger.info(f"Fetched {len(validated_prices)} valid price records for {commodity}")
            return validated_prices
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error fetching Agmarknet data: {e}")
            raise Exception(f"Failed to fetch market data: {e}")
        except Exception as e:
            logger.error(f"Error fetching Agmarknet data: {e}")
            raise Exception(f"Failed to fetch market data: {e}")
    
    async def validate_market_data(self, market_price: MarketPrice) -> DataValidationResult:
        """
        Validate market price data for quality and consistency.
        
        Args:
            market_price: MarketPrice object to validate
            
        Returns:
            DataValidationResult with validation details
        """
        validation_checks = {}
        issues = []
        recommendations = []
        
        # Check required fields
        validation_checks["has_commodity"] = bool(market_price.commodity and market_price.commodity.strip())
        if not validation_checks["has_commodity"]:
            issues.append("Commodity name is missing or empty")
        
        validation_checks["has_market"] = bool(market_price.market and market_price.market.strip())
        if not validation_checks["has_market"]:
            issues.append("Market name is missing or empty")
        
        validation_checks["has_state"] = bool(market_price.state and market_price.state.strip())
        if not validation_checks["has_state"]:
            issues.append("State name is missing or empty")
        
        # Check price validity
        validation_checks["valid_prices"] = (
            market_price.min_price > 0 and 
            market_price.max_price > 0 and 
            market_price.modal_price > 0 and
            market_price.min_price <= market_price.modal_price <= market_price.max_price
        )
        if not validation_checks["valid_prices"]:
            issues.append("Invalid price values (must be positive and in correct order)")
        
        # Check price reasonableness (basic sanity check)
        if market_price.max_price > 0:
            price_ratio = float(market_price.max_price / market_price.min_price)
            validation_checks["reasonable_price_range"] = price_ratio <= 10.0  # Max 10x difference
            if not validation_checks["reasonable_price_range"]:
                issues.append("Price range seems unreasonable (max/min ratio > 10)")
                recommendations.append("Verify price data accuracy")
        
        # Check date validity
        validation_checks["valid_date"] = (
            market_price.date <= date.today() and 
            market_price.date >= date.today() - timedelta(days=365)
        )
        if not validation_checks["valid_date"]:
            issues.append("Date is either in the future or too old (>1 year)")
        
        # Check arrivals data if present
        if market_price.arrivals is not None:
            validation_checks["valid_arrivals"] = market_price.arrivals >= 0
            if not validation_checks["valid_arrivals"]:
                issues.append("Arrivals quantity cannot be negative")
        else:
            validation_checks["valid_arrivals"] = True  # Optional field
        
        # Calculate quality score
        passed_checks = sum(1 for check in validation_checks.values() if check)
        total_checks = len(validation_checks)
        quality_score = passed_checks / total_checks if total_checks > 0 else 0.0
        
        # Determine overall validity
        is_valid = len(issues) == 0 and quality_score >= 0.8
        
        if quality_score < 0.9:
            recommendations.append("Consider additional data verification")
        
        return DataValidationResult(
            is_valid=is_valid,
            quality_score=quality_score,
            validation_checks=validation_checks,
            issues=issues,
            recommendations=recommendations
        )
    
    def _determine_data_quality(self, validation_result: DataValidationResult) -> DataQuality:
        """Determine data quality based on validation result."""
        if validation_result.quality_score >= 0.95:
            return DataQuality.HIGH
        elif validation_result.quality_score >= 0.8:
            return DataQuality.MEDIUM
        elif validation_result.quality_score >= 0.6:
            return DataQuality.LOW
        else:
            return DataQuality.UNVERIFIED
    
    async def store_market_data(self, market_prices: List[MarketPrice]) -> int:
        """
        Store market price data in the database.
        
        Args:
            market_prices: List of MarketPrice objects to store
            
        Returns:
            Number of records stored
        """
        if not market_prices:
            return 0
        
        try:
            # Prepare documents for insertion
            documents = []
            for price in market_prices:
                doc = price.dict()
                doc["_id"] = f"{price.commodity}_{price.market}_{price.date}_{price.source}"
                documents.append(doc)
            
            # Use upsert to avoid duplicates
            operations = []
            for doc in documents:
                operations.append({
                    "replaceOne": {
                        "filter": {"_id": doc["_id"]},
                        "replacement": doc,
                        "upsert": True
                    }
                })
            
            if operations:
                result = await self.market_prices_collection.bulk_write(operations)
                stored_count = result.upserted_count + result.modified_count
                logger.info(f"Stored {stored_count} market price records")
                return stored_count
            
            return 0
            
        except Exception as e:
            logger.error(f"Error storing market data: {e}")
            raise Exception(f"Failed to store market data: {e}")
    
    async def get_cached_market_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached market data from Redis."""
        if not self.redis_client:
            return None
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning(f"Error retrieving cached data: {e}")
        
        return None
    
    async def cache_market_data(self, cache_key: str, data: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Cache market data in Redis."""
        if not self.redis_client:
            return
        
        try:
            cache_ttl = ttl or self.cache_ttl
            await self.redis_client.setex(
                cache_key,
                cache_ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            logger.warning(f"Error caching data: {e}")
    
    async def get_market_price(self, request: MarketPriceRequest) -> MarketPriceResponse:
        """
        Get market price data with caching and external API integration.
        
        Args:
            request: MarketPriceRequest with search parameters
            
        Returns:
            MarketPriceResponse with price data
        """
        # Generate cache key
        cache_key = f"market_price:{request.commodity}:{request.state or 'all'}:{request.market or 'all'}"
        
        # Try to get cached data first
        cached_data = await self.get_cached_market_data(cache_key)
        if cached_data:
            logger.info(f"Returning cached market data for {request.commodity}")
            return MarketPriceResponse(**cached_data)
        
        # Fetch from database first
        query = {"commodity": {"$regex": request.commodity, "$options": "i"}}
        if request.state:
            query["state"] = {"$regex": request.state, "$options": "i"}
        if request.market:
            query["market"] = {"$regex": request.market, "$options": "i"}
        if request.date_from or request.date_to:
            date_filter = {}
            if request.date_from:
                date_filter["$gte"] = request.date_from
            if request.date_to:
                date_filter["$lte"] = request.date_to
            query["date"] = date_filter
        
        # Get recent data (last 30 days if no date range specified)
        if "date" not in query:
            query["date"] = {"$gte": date.today() - timedelta(days=30)}
        
        cursor = self.market_prices_collection.find(query).sort("date", -1).limit(100)
        db_records = await cursor.to_list(length=100)
        
        market_prices = []
        for record in db_records:
            try:
                # Remove MongoDB _id field
                record.pop("_id", None)
                market_prices.append(MarketPrice(**record))
            except Exception as e:
                logger.warning(f"Error parsing market price record: {e}")
                continue
        
        # If no recent data in database, fetch from external API
        if not market_prices:
            logger.info(f"No cached data found, fetching from Agmarknet for {request.commodity}")
            try:
                external_prices = await self.fetch_agmarknet_data(
                    commodity=request.commodity,
                    state=request.state,
                    market=request.market,
                    date_from=request.date_from or date.today() - timedelta(days=7),
                    date_to=request.date_to or date.today()
                )
                
                if external_prices:
                    # Store the fetched data
                    await self.store_market_data(external_prices)
                    market_prices = external_prices
                
            except Exception as e:
                logger.error(f"Error fetching external market data: {e}")
                # Continue with empty data rather than failing
        
        # Calculate summary statistics
        summary = self._calculate_price_summary(market_prices)
        
        # Determine overall data quality
        if market_prices:
            quality_scores = [price.data_quality for price in market_prices]
            if DataQuality.HIGH in quality_scores:
                overall_quality = DataQuality.HIGH
            elif DataQuality.MEDIUM in quality_scores:
                overall_quality = DataQuality.MEDIUM
            else:
                overall_quality = DataQuality.LOW
        else:
            overall_quality = DataQuality.UNVERIFIED
        
        response = MarketPriceResponse(
            commodity=request.commodity,
            variety=request.variety,
            prices=market_prices,
            summary=summary,
            data_quality=overall_quality,
            last_updated=datetime.utcnow()
        )
        
        # Cache the response
        await self.cache_market_data(cache_key, response.dict())
        
        return response
    
    def _calculate_price_summary(self, prices: List[MarketPrice]) -> Dict[str, Any]:
        """Calculate summary statistics for price data."""
        if not prices:
            return {
                "count": 0,
                "avg_price": 0,
                "min_price": 0,
                "max_price": 0,
                "price_trend": "no_data"
            }
        
        modal_prices = [float(price.modal_price) for price in prices]
        
        summary = {
            "count": len(prices),
            "avg_price": sum(modal_prices) / len(modal_prices),
            "min_price": min(modal_prices),
            "max_price": max(modal_prices),
            "latest_date": max(price.date for price in prices).isoformat(),
            "markets_count": len(set(price.market for price in prices)),
            "states_count": len(set(price.state for price in prices))
        }
        
        # Calculate price trend (simple comparison of first and last prices)
        if len(prices) >= 2:
            sorted_prices = sorted(prices, key=lambda x: x.date)
            first_price = float(sorted_prices[0].modal_price)
            last_price = float(sorted_prices[-1].modal_price)
            
            if last_price > first_price * 1.05:  # 5% increase
                summary["price_trend"] = "increasing"
            elif last_price < first_price * 0.95:  # 5% decrease
                summary["price_trend"] = "decreasing"
            else:
                summary["price_trend"] = "stable"
        else:
            summary["price_trend"] = "insufficient_data"
        
        return summary
    
    async def get_price_history(self, request: PriceHistoryRequest) -> PriceHistoryResponse:
        """
        Get historical price data for a commodity.
        
        Args:
            request: PriceHistoryRequest with parameters
            
        Returns:
            PriceHistoryResponse with historical data
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=request.days)
        
        # Query database for historical data
        query = {
            "commodity": {"$regex": request.commodity, "$options": "i"},
            "date": {"$gte": start_date, "$lte": end_date}
        }
        
        if request.market:
            query["market"] = {"$regex": request.market, "$options": "i"}
        if request.state:
            query["state"] = {"$regex": request.state, "$options": "i"}
        if request.variety:
            query["variety"] = {"$regex": request.variety, "$options": "i"}
        
        cursor = self.market_prices_collection.find(query).sort("date", 1)
        records = await cursor.to_list(length=None)
        
        prices = []
        for record in records:
            try:
                record.pop("_id", None)
                prices.append(MarketPrice(**record))
            except Exception as e:
                logger.warning(f"Error parsing price history record: {e}")
                continue
        
        # If insufficient data, try to fetch from external API
        if len(prices) < request.days // 7:  # Less than weekly data
            try:
                external_prices = await self.fetch_agmarknet_data(
                    commodity=request.commodity,
                    state=request.state,
                    market=request.market,
                    date_from=start_date,
                    date_to=end_date
                )
                
                if external_prices:
                    await self.store_market_data(external_prices)
                    # Merge with existing data
                    existing_keys = {f"{p.commodity}_{p.market}_{p.date}" for p in prices}
                    for price in external_prices:
                        key = f"{price.commodity}_{price.market}_{price.date}"
                        if key not in existing_keys:
                            prices.append(price)
                
            except Exception as e:
                logger.error(f"Error fetching historical data: {e}")
        
        # Create price history object
        if prices:
            modal_prices = [float(p.modal_price) for p in prices]
            avg_price = sum(modal_prices) / len(modal_prices)
            
            # Calculate volatility (standard deviation)
            variance = sum((price - avg_price) ** 2 for price in modal_prices) / len(modal_prices)
            volatility = variance ** 0.5
            
            # Determine trend
            if len(prices) >= 2:
                sorted_prices = sorted(prices, key=lambda x: x.date)
                first_price = float(sorted_prices[0].modal_price)
                last_price = float(sorted_prices[-1].modal_price)
                
                if last_price > first_price * 1.1:
                    trend = "strongly_increasing"
                elif last_price > first_price * 1.05:
                    trend = "increasing"
                elif last_price < first_price * 0.9:
                    trend = "strongly_decreasing"
                elif last_price < first_price * 0.95:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            history = PriceHistory(
                commodity=request.commodity,
                variety=request.variety,
                market=request.market or "multiple",
                state=request.state or "multiple",
                prices=prices,
                period_start=start_date,
                period_end=end_date,
                average_price=Decimal(str(avg_price)),
                price_volatility=volatility,
                trend=trend
            )
        else:
            # Empty history
            history = PriceHistory(
                commodity=request.commodity,
                variety=request.variety,
                market=request.market or "unknown",
                state=request.state or "unknown",
                prices=[],
                period_start=start_date,
                period_end=end_date,
                average_price=Decimal("0"),
                price_volatility=0.0,
                trend="no_data"
            )
        
        # Calculate trend analysis
        trends = self._analyze_price_trends(prices)
        
        return PriceHistoryResponse(
            commodity=request.commodity,
            variety=request.variety,
            history=history,
            trends=trends,
            predictions=None  # Will be implemented in task 6.3
        )
    
    def _analyze_price_trends(self, prices: List[MarketPrice]) -> Dict[str, Any]:
        """Analyze price trends and patterns."""
        if not prices:
            return {"status": "no_data"}
        
        # Sort prices by date
        sorted_prices = sorted(prices, key=lambda x: x.date)
        modal_prices = [float(p.modal_price) for p in sorted_prices]
        
        trends = {
            "total_records": len(prices),
            "date_range": {
                "start": sorted_prices[0].date.isoformat(),
                "end": sorted_prices[-1].date.isoformat()
            },
            "price_range": {
                "min": min(modal_prices),
                "max": max(modal_prices),
                "avg": sum(modal_prices) / len(modal_prices)
            }
        }
        
        # Calculate moving averages if enough data
        if len(prices) >= 7:
            # 7-day moving average
            ma_7 = []
            for i in range(6, len(modal_prices)):
                avg = sum(modal_prices[i-6:i+1]) / 7
                ma_7.append(avg)
            
            trends["moving_average_7d"] = ma_7[-1] if ma_7 else None
            
            # Price momentum (last 7 days vs previous 7 days)
            if len(modal_prices) >= 14:
                recent_avg = sum(modal_prices[-7:]) / 7
                previous_avg = sum(modal_prices[-14:-7]) / 7
                momentum = (recent_avg - previous_avg) / previous_avg * 100
                trends["momentum_7d"] = round(momentum, 2)
        
        return trends
    
    async def sync_external_data(self, commodities: List[str]) -> DataSyncStatus:
        """
        Synchronize data from external sources for specified commodities.
        
        Args:
            commodities: List of commodity names to sync
            
        Returns:
            DataSyncStatus with sync results
        """
        sync_start = datetime.utcnow()
        total_synced = 0
        errors = []
        
        try:
            for commodity in commodities:
                try:
                    # Fetch recent data (last 7 days)
                    date_from = date.today() - timedelta(days=7)
                    prices = await self.fetch_agmarknet_data(
                        commodity=commodity,
                        date_from=date_from
                    )
                    
                    if prices:
                        synced_count = await self.store_market_data(prices)
                        total_synced += synced_count
                        logger.info(f"Synced {synced_count} records for {commodity}")
                    
                    # Small delay to avoid overwhelming the API
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    error_msg = f"Error syncing {commodity}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Update sync status
            sync_status = DataSyncStatus(
                source=DataSource.AGMARKNET,
                last_sync=sync_start,
                next_sync=sync_start + timedelta(hours=6),  # Next sync in 6 hours
                sync_status="completed" if not errors else "completed_with_errors",
                records_synced=total_synced,
                errors=errors
            )
            
            # Store sync status
            await self.data_sync_status_collection.replace_one(
                {"source": DataSource.AGMARKNET},
                sync_status.dict(),
                upsert=True
            )
            
            return sync_status
            
        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            logger.error(error_msg)
            
            return DataSyncStatus(
                source=DataSource.AGMARKNET,
                last_sync=sync_start,
                next_sync=sync_start + timedelta(hours=1),  # Retry in 1 hour
                sync_status="failed",
                records_synced=total_synced,
                errors=[error_msg]
            )
    
    async def predict_price(
        self,
        commodity: str,
        state: Optional[str] = None,
        market: Optional[str] = None,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Generate ML-based price prediction using mathematical models.
        
        Args:
            commodity: Commodity name
            state: State name (optional)
            market: Market name (optional)
            days_ahead: Number of days to predict (default: 7)
            
        Returns:
            Price prediction with confidence scores
        """
        try:
            # Fetch historical data
            date_from = date.today() - timedelta(days=30)
            prices = await self.fetch_agmarknet_data(
                commodity=commodity,
                state=state,
                market=market,
                date_from=date_from
            )
            
            if not prices:
                # Return mock prediction if no historical data
                return self._generate_mock_prediction(commodity, days_ahead)
            
            # Sort prices by date
            sorted_prices = sorted(prices, key=lambda x: x.date)
            modal_prices = [float(p.modal_price) for p in sorted_prices]
            
            # Calculate trend and seasonality
            prediction = self._calculate_price_forecast(
                modal_prices, days_ahead, commodity
            )
            
            # Add confidence score based on data quality
            prediction["confidence"] = self._calculate_prediction_confidence(prices)
            prediction["historical_data_points"] = len(prices)
            prediction["commodity"] = commodity
            prediction["state"] = state or "all"
            prediction["market"] = market or "all"
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error predicting price for {commodity}: {e}")
            return self._generate_mock_prediction(commodity, days_ahead)
    
    def _calculate_price_forecast(
        self,
        historical_prices: List[float],
        days_ahead: int,
        commodity: str
    ) -> Dict[str, Any]:
        """
        Calculate price forecast using mathematical models.
        
        Uses a combination of:
        - Moving average for trend
        - Sine wave for seasonality
        - Random walk for volatility
        """
        if not historical_prices:
            return self._generate_mock_prediction(commodity, days_ahead)
        
        # Calculate base statistics
        avg_price = sum(historical_prices) / len(historical_prices)
        std_dev = math.sqrt(
            sum((p - avg_price) ** 2 for p in historical_prices) / len(historical_prices)
        )
        
        # Calculate trend (simple linear regression)
        n = len(historical_prices)
        x_vals = list(range(n))
        x_mean = sum(x_vals) / n
        y_mean = avg_price
        
        numerator = sum((x_vals[i] - x_mean) * (historical_prices[i] - y_mean) for i in range(n))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean
        
        # Generate predictions
        predictions = []
        for day in range(1, days_ahead + 1):
            # Base trend prediction
            trend_price = intercept + slope * (n + day)
            
            # Add seasonality (commodity-specific cycles)
            seasonality = self._get_seasonality_factor(commodity, day)
            seasonal_adjustment = trend_price * seasonality
            
            # Add volatility
            volatility = random.uniform(-std_dev * 0.1, std_dev * 0.1)
            
            # Predicted price
            predicted_price = max(trend_price + seasonal_adjustment + volatility, 0)
            
            # Generate min/max range
            min_price = predicted_price * 0.95
            max_price = predicted_price * 1.05
            
            predictions.append({
                "date": (date.today() + timedelta(days=day)).isoformat(),
                "predicted_price": round(predicted_price, 2),
                "min_price": round(min_price, 2),
                "max_price": round(max_price, 2),
                "trend": "increasing" if slope > 0 else "decreasing" if slope < 0 else "stable"
            })
        
        # Calculate overall trend
        overall_trend = "increasing" if slope > 0.5 else "decreasing" if slope < -0.5 else "stable"
        
        return {
            "predictions": predictions,
            "model_type": "mathematical_forecast",
            "trend": overall_trend,
            "average_historical_price": round(avg_price, 2),
            "price_volatility": round(std_dev, 2),
            "forecast_days": days_ahead
        }
    
    def _get_seasonality_factor(self, commodity: str, day_offset: int) -> float:
        """
        Get seasonality factor for commodity based on typical seasonal patterns.
        
        Args:
            commodity: Commodity name
            day_offset: Days from today
            
        Returns:
            Seasonality factor (-0.1 to 0.1)
        """
        # Define seasonal patterns for different commodity categories
        seasonal_commodities = {
            "vegetables": ["tomato", "potato", "onion", "cabbage", "cauliflower"],
            "fruits": ["apple", "mango", "banana", "orange", "grapes"],
            "grains": ["wheat", "rice", "maize", "bajra", "jowar"],
            "pulses": ["chickpea", "lentil", "pigeon pea", "moong", "urad"]
        }
        
        commodity_lower = commodity.lower()
        
        # Determine commodity category
        category = "other"
        for cat, items in seasonal_commodities.items():
            if any(item in commodity_lower for item in items):
                category = cat
                break
        
        # Calculate seasonality based on category and time of year
        current_month = (date.today() + timedelta(days=day_offset)).month
        
        if category == "vegetables":
            # Peak in winter (Nov-Feb), low in summer
            return math.sin((current_month - 6) * math.pi / 6) * 0.1
        elif category == "fruits":
            # Peak in summer (Apr-Jun), low in winter
            return math.sin((current_month - 12) * math.pi / 6) * 0.1
        elif category == "grains":
            # Peak after harvest (Mar-May, Oct-Nov)
            if current_month in [3, 4, 5, 10, 11]:
                return -0.05  # Prices drop
            return 0.05  # Prices rise
        else:
            # Minimal seasonality for other commodities
            return 0.0
    
    def _calculate_prediction_confidence(self, prices: List[MarketPrice]) -> float:
        """
        Calculate confidence score for predictions based on data quality.
        
        Args:
            prices: List of historical prices
            
        Returns:
            Confidence score (0.0 to 1.0)
        """
        if not prices:
            return 0.3  # Low confidence with no data
        
        # Factors affecting confidence
        data_points = len(prices)
        validated_count = sum(1 for p in prices if p.is_validated)
        high_quality_count = sum(1 for p in prices if p.data_quality == DataQuality.HIGH)
        
        # Base confidence on data quantity
        quantity_score = min(data_points / 30.0, 1.0)  # 30 days = full score
        
        # Quality score
        validation_score = validated_count / data_points if data_points > 0 else 0.0
        quality_score = high_quality_count / data_points if data_points > 0 else 0.0
        
        # Combined confidence
        confidence = (quantity_score * 0.4 + validation_score * 0.3 + quality_score * 0.3)
        
        return round(confidence, 2)
    
    def _generate_mock_prediction(self, commodity: str, days_ahead: int) -> Dict[str, Any]:
        """Generate mock prediction when no historical data is available."""
        # Commodity base prices (mock data)
        base_prices = {
            "tomato": 30.0, "potato": 25.0, "onion": 35.0,
            "wheat": 2000.0, "rice": 2500.0,
            "apple": 80.0, "mango": 60.0,
            "chickpea": 5000.0, "lentil": 6000.0
        }
        
        # Get base price or default
        commodity_lower = commodity.lower()
        base_price = next(
            (price for key, price in base_prices.items() if key in commodity_lower),
            100.0  # Default price
        )
        
        predictions = []
        for day in range(1, days_ahead + 1):
            # Add some randomness
            variation = random.uniform(-0.05, 0.05)
            predicted_price = base_price * (1 + variation)
            
            predictions.append({
                "date": (date.today() + timedelta(days=day)).isoformat(),
                "predicted_price": round(predicted_price, 2),
                "min_price": round(predicted_price * 0.95, 2),
                "max_price": round(predicted_price * 1.05, 2),
                "trend": "stable"
            })
        
        return {
            "predictions": predictions,
            "model_type": "mock_forecast",
            "trend": "stable",
            "average_historical_price": round(base_price, 2),
            "price_volatility": round(base_price * 0.1, 2),
            "forecast_days": days_ahead,
            "confidence": 0.3,
            "historical_data_points": 0,
            "commodity": commodity,
            "note": "Limited historical data - using estimated prices"
        }
    
    async def suggest_price_for_product(
        self,
        commodity: str,
        state: Optional[str] = None,
        market: Optional[str] = None,
        quality: str = "medium"
    ) -> Dict[str, Any]:
        """
        Suggest a fair price for a product listing.
        
        Args:
            commodity: Commodity name
            state: State name
            market: Market name
            quality: Product quality (high/medium/low)
            
        Returns:
            Price suggestion with reasoning
        """
        try:
            # Get recent market prices
            date_from = date.today() - timedelta(days=7)
            prices = await self.fetch_agmarknet_data(
                commodity=commodity,
                state=state,
                market=market,
                date_from=date_from
            )
            
            if not prices:
                # Return mock suggestion
                return self._generate_mock_price_suggestion(commodity, quality)
            
            # Calculate price statistics
            modal_prices = [float(p.modal_price) for p in prices]
            avg_price = sum(modal_prices) / len(modal_prices)
            min_price = min(modal_prices)
            max_price = max(modal_prices)
            
            # Adjust for quality
            quality_multipliers = {
                "high": 1.1,
                "medium": 1.0,
                "low": 0.9
            }
            multiplier = quality_multipliers.get(quality.lower(), 1.0)
            suggested_price = avg_price * multiplier
            
            # Generate reasoning
            reasoning = self._generate_price_reasoning(
                commodity, suggested_price, avg_price, min_price, max_price, quality
            )
            
            return {
                "commodity": commodity,
                "suggested_price": round(suggested_price, 2),
                "price_range": {
                    "min": round(min_price * multiplier, 2),
                    "max": round(max_price * multiplier, 2)
                },
                "market_average": round(avg_price, 2),
                "quality_adjustment": quality,
                "confidence": self._calculate_prediction_confidence(prices),
                "reasoning": reasoning,
                "based_on_records": len(prices),
                "data_period": "last_7_days"
            }
            
        except Exception as e:
            logger.error(f"Error suggesting price for {commodity}: {e}")
            return self._generate_mock_price_suggestion(commodity, quality)
    
    def _generate_price_reasoning(
        self,
        commodity: str,
        suggested_price: float,
        avg_price: float,
        min_price: float,
        max_price: float,
        quality: str
    ) -> List[str]:
        """Generate human-readable reasoning for price suggestion."""
        reasoning = []
        
        reasoning.append(
            f"Based on recent market data for {commodity}, "
            f"the average price is ₹{avg_price:.2f} per kg."
        )
        
        if quality.lower() == "high":
            reasoning.append(
                "Your product is marked as high quality, so we recommend "
                "pricing 10% above market average."
            )
        elif quality.lower() == "low":
            reasoning.append(
                "For competitive pricing of lower quality product, "
                "we recommend pricing 10% below market average."
            )
        else:
            reasoning.append("Your product is standard quality, priced at market average.")
        
        price_range = max_price - min_price
        volatility = price_range / avg_price if avg_price > 0 else 0
        
        if volatility > 0.3:
            reasoning.append(
                "Market prices show high volatility. Consider pricing flexibly."
            )
        else:
            reasoning.append("Market prices are stable with low volatility.")
        
        reasoning.append(
            f"Recommended price range: ₹{min_price:.2f} - ₹{max_price:.2f} per kg."
        )
        
        return reasoning
    
    def _generate_mock_price_suggestion(self, commodity: str, quality: str) -> Dict[str, Any]:
        """Generate mock price suggestion when no data is available."""
        base_prices = {
            "tomato": 30.0, "potato": 25.0, "onion": 35.0,
            "wheat": 2000.0, "rice": 2500.0,
            "apple": 80.0, "mango": 60.0
        }
        
        commodity_lower = commodity.lower()
        base_price = next(
            (price for key, price in base_prices.items() if key in commodity_lower),
            100.0
        )
        
        quality_multipliers = {"high": 1.1, "medium": 1.0, "low": 0.9}
        multiplier = quality_multipliers.get(quality.lower(), 1.0)
        suggested_price = base_price * multiplier
        
        return {
            "commodity": commodity,
            "suggested_price": round(suggested_price, 2),
            "price_range": {
                "min": round(base_price * 0.9 * multiplier, 2),
                "max": round(base_price * 1.1 * multiplier, 2)
            },
            "market_average": round(base_price, 2),
            "quality_adjustment": quality,
            "confidence": 0.3,
            "reasoning": [
                f"Limited market data available for {commodity}.",
                f"Suggested price based on typical market rates.",
                "Consider updating based on local market conditions."
            ],
            "based_on_records": 0,
            "data_period": "estimated"
        }
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.http_client:
            await self.http_client.aclose()