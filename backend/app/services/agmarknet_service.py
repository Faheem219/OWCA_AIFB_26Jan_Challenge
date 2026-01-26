"""
AGMARKNET API integration service for fetching daily mandi rates.
"""
import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import httpx
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.models.price import (
    PriceData, Location, PriceSource, MarketType, QualityGrade,
    AGMARKNETResponse, PriceQuery, PriceSearchResult
)
from app.db.mongodb import get_database
from app.db.redis import get_redis

logger = logging.getLogger(__name__)


class AGMARKNETService:
    """Service for AGMARKNET API integration."""
    
    def __init__(self):
        self.base_url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"
        self.api_key = settings.AGMARKNET_API_KEY
        self.timeout = 30.0
        self.max_retries = 3
        
        # Common commodity mappings for AGMARKNET
        self.commodity_mappings = {
            "rice": ["Rice", "Paddy(Dhan)(Common)", "Paddy(Dhan)(Basmati)"],
            "wheat": ["Wheat", "Wheat (Desi)", "Wheat (Sharbati)"],
            "onion": ["Onion", "Onion (Pole)", "Onion (Nasik Red)"],
            "potato": ["Potato", "Potato (Red)", "Potato (White)"],
            "tomato": ["Tomato", "Tomato (Desi)", "Tomato (Hybrid)"],
            "sugar": ["Sugar", "Sugarcane"],
            "cotton": ["Cotton", "Cotton (Kapas)", "Cotton (Medium Staple)"],
            "turmeric": ["Turmeric", "Turmeric (Finger)", "Turmeric (Bulb)"],
            "chili": ["Chili Red", "Chili Green", "Chili (Dry)"],
            "coriander": ["Coriander", "Coriander (Leaves)", "Coriander (Seed)"]
        }
    
    async def fetch_daily_rates(
        self, 
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        market: Optional[str] = None,
        date_filter: Optional[date] = None
    ) -> List[PriceData]:
        """
        Fetch daily mandi rates from AGMARKNET API.
        
        Args:
            commodity: Commodity name to filter
            state: State name to filter
            district: District name to filter
            market: Market name to filter
            date_filter: Date to filter (defaults to today)
            
        Returns:
            List of PriceData objects
        """
        try:
            if not self.api_key:
                logger.warning("AGMARKNET API key not configured, using mock data")
                return await self._get_mock_data(commodity, state, district)
            
            # Build query parameters
            params = {
                "api-key": self.api_key,
                "format": "json",
                "limit": 1000
            }
            
            # Add filters
            filters = []
            if commodity:
                # Map common commodity names to AGMARKNET names
                agmarknet_commodities = self.commodity_mappings.get(
                    commodity.lower(), [commodity]
                )
                commodity_filter = " OR ".join([f'commodity:"{c}"' for c in agmarknet_commodities])
                filters.append(f"({commodity_filter})")
            
            if state:
                filters.append(f'state:"{state}"')
            
            if district:
                filters.append(f'district:"{district}"')
            
            if market:
                filters.append(f'market:"{market}"')
            
            if date_filter:
                date_str = date_filter.strftime("%d/%m/%Y")
                filters.append(f'arrival_date:"{date_str}"')
            
            if filters:
                params["filters"] = " AND ".join(filters)
            
            # Make API request with retries
            for attempt in range(self.max_retries):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.get(self.base_url, params=params)
                        response.raise_for_status()
                        
                        data = response.json()
                        return await self._parse_agmarknet_response(data)
                        
                except httpx.TimeoutException:
                    logger.warning(f"AGMARKNET API timeout, attempt {attempt + 1}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    
                except httpx.HTTPStatusError as e:
                    logger.error(f"AGMARKNET API error: {e.response.status_code}")
                    if e.response.status_code == 429:  # Rate limit
                        await asyncio.sleep(60)  # Wait 1 minute
                        continue
                    raise
                    
        except Exception as e:
            logger.error(f"Error fetching AGMARKNET data: {str(e)}")
            # Fallback to cached data
            return await self._get_cached_data(commodity, state, district)
    
    async def _parse_agmarknet_response(self, data: Dict[str, Any]) -> List[PriceData]:
        """Parse AGMARKNET API response into PriceData objects."""
        price_data_list = []
        
        try:
            records = data.get("records", [])
            
            for record in records:
                try:
                    # Parse location
                    location = Location(
                        state=record.get("state", "").strip(),
                        district=record.get("district", "").strip(),
                        market_name=record.get("market", "").strip()
                    )
                    
                    # Parse prices (handle different formats)
                    price_min = self._parse_price(record.get("min_price", "0"))
                    price_max = self._parse_price(record.get("max_price", "0"))
                    price_modal = self._parse_price(record.get("modal_price", "0"))
                    
                    # Skip if no valid prices
                    if price_min == 0 and price_max == 0 and price_modal == 0:
                        continue
                    
                    # Parse date
                    arrival_date = self._parse_date(record.get("arrival_date", ""))
                    if not arrival_date:
                        arrival_date = date.today()
                    
                    # Determine quality grade based on price range
                    quality_grade = self._determine_quality_grade(
                        price_min, price_max, price_modal
                    )
                    
                    price_data = PriceData(
                        commodity=record.get("commodity", "").strip(),
                        variety=record.get("variety", "").strip() or None,
                        market_name=location.market_name,
                        location=location,
                        price_min=price_min,
                        price_max=price_max,
                        price_modal=price_modal,
                        quality_grade=quality_grade,
                        unit=record.get("units", "Quintal").strip(),
                        date=arrival_date,
                        source=PriceSource.AGMARKNET,
                        market_type=MarketType.MANDI,
                        arrivals=self._parse_arrivals(record.get("arrivals", "0"))
                    )
                    
                    price_data_list.append(price_data)
                    
                except Exception as e:
                    logger.warning(f"Error parsing AGMARKNET record: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing AGMARKNET response: {str(e)}")
        
        logger.info(f"Parsed {len(price_data_list)} price records from AGMARKNET")
        return price_data_list
    
    def _parse_price(self, price_str: str) -> float:
        """Parse price string to float."""
        try:
            if not price_str or price_str.strip() in ["", "NR", "N/A", "-"]:
                return 0.0
            
            # Remove currency symbols and commas
            cleaned = str(price_str).replace("₹", "").replace(",", "").strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date string to date object."""
        try:
            if not date_str:
                return None
            
            # Try different date formats
            formats = ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str.strip(), fmt).date()
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None
    
    def _parse_arrivals(self, arrivals_str: str) -> Optional[float]:
        """Parse arrivals string to float."""
        try:
            if not arrivals_str or arrivals_str.strip() in ["", "NR", "N/A", "-"]:
                return None
            
            cleaned = str(arrivals_str).replace(",", "").strip()
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _determine_quality_grade(
        self, price_min: float, price_max: float, price_modal: float
    ) -> QualityGrade:
        """Determine quality grade based on price distribution."""
        if price_min == price_max == price_modal:
            return QualityGrade.STANDARD
        
        # If modal price is closer to max, likely premium
        if price_modal > (price_min + price_max) / 2:
            return QualityGrade.PREMIUM
        elif price_modal < (price_min + price_max) / 2:
            return QualityGrade.BELOW_STANDARD
        else:
            return QualityGrade.STANDARD
    
    async def _get_mock_data(
        self, 
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None
    ) -> List[PriceData]:
        """Generate mock data for testing when API key is not available."""
        mock_data = []
        
        # Sample commodities and locations
        commodities = ["Rice", "Wheat", "Onion", "Potato", "Tomato"]
        states = ["Maharashtra", "Punjab", "Uttar Pradesh", "Karnataka", "Tamil Nadu"]
        districts = ["Mumbai", "Ludhiana", "Lucknow", "Bangalore", "Chennai"]
        markets = ["APMC Market", "Mandi", "Wholesale Market"]
        
        if commodity:
            commodities = [commodity]
        
        for i, comm in enumerate(commodities[:5]):  # Limit to 5 for testing
            location = Location(
                state=state or states[i % len(states)],
                district=district or districts[i % len(districts)],
                market_name=markets[i % len(markets)]
            )
            
            # Generate realistic price ranges
            base_price = 2000 + (i * 500)  # Base price per quintal
            price_min = base_price * 0.9
            price_max = base_price * 1.1
            price_modal = base_price
            
            mock_data.append(PriceData(
                commodity=comm,
                market_name=location.market_name,
                location=location,
                price_min=price_min,
                price_max=price_max,
                price_modal=price_modal,
                quality_grade=QualityGrade.STANDARD,
                unit="Quintal",
                date=date.today(),
                source=PriceSource.AGMARKNET,
                market_type=MarketType.MANDI,
                arrivals=100.0 + (i * 50)
            ))
        
        logger.info(f"Generated {len(mock_data)} mock price records")
        return mock_data
    
    async def _get_cached_data(
        self,
        commodity: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None
    ) -> List[PriceData]:
        """Get cached price data as fallback."""
        try:
            redis = await get_redis()
            cache_key = f"agmarknet:fallback:{commodity or 'all'}:{state or 'all'}:{district or 'all'}"
            
            cached_data = await redis.get(cache_key)
            if cached_data:
                # Parse cached data (implement based on your caching strategy)
                logger.info("Using cached AGMARKNET data as fallback")
                return []  # Return parsed cached data
            
            # If no cache, return mock data
            return await self._get_mock_data(commodity, state, district)
            
        except Exception as e:
            logger.error(f"Error getting cached data: {str(e)}")
            return await self._get_mock_data(commodity, state, district)
    
    async def store_price_data(self, price_data_list: List[PriceData]) -> int:
        """
        Store price data in MongoDB with upsert logic.
        
        Args:
            price_data_list: List of PriceData objects to store
            
        Returns:
            Number of records stored/updated
        """
        if not price_data_list:
            return 0
        
        try:
            db = await get_database()
            collection = db.price_data
            
            stored_count = 0
            
            for price_data in price_data_list:
                # Create unique identifier for upsert
                filter_query = {
                    "commodity": price_data.commodity,
                    "market_name": price_data.market_name,
                    "location.state": price_data.location.state,
                    "location.district": price_data.location.district,
                    "date": price_data.date.isoformat(),
                    "source": price_data.source.value
                }
                
                # Update timestamp
                price_data.updated_at = datetime.utcnow()
                
                # Convert the price_data to dict and handle date serialization
                price_dict = price_data.dict()
                price_dict["date"] = price_data.date.isoformat()
                price_dict["source"] = price_data.source.value
                price_dict["quality_grade"] = price_data.quality_grade.value
                price_dict["market_type"] = price_data.market_type.value
                
                # Upsert the document
                result = await collection.replace_one(
                    filter_query,
                    price_dict,
                    upsert=True
                )
                
                if result.upserted_id or result.modified_count > 0:
                    stored_count += 1
            
            logger.info(f"Stored/updated {stored_count} price records in database")
            return stored_count
            
        except Exception as e:
            logger.error(f"Error storing price data: {str(e)}")
            raise
    
    async def get_current_prices(
        self,
        commodity: str,
        location: Optional[str] = None,
        radius_km: int = 50
    ) -> List[PriceData]:
        """
        Get current prices for a commodity within a radius.
        
        Args:
            commodity: Commodity name
            location: Location (state/district/market)
            radius_km: Search radius in kilometers
            
        Returns:
            List of current PriceData
        """
        try:
            # First try to get fresh data from AGMARKNET
            fresh_data = await self.fetch_daily_rates(
                commodity=commodity,
                date_filter=date.today()
            )
            
            if fresh_data:
                # Store fresh data
                await self.store_price_data(fresh_data)
                
                # Filter by location if specified
                if location:
                    fresh_data = [
                        pd for pd in fresh_data
                        if location.lower() in pd.location.state.lower() or
                           location.lower() in pd.location.district.lower() or
                           location.lower() in pd.market_name.lower()
                    ]
                
                return fresh_data
            
            # Fallback to database
            return await self._get_prices_from_db(commodity, location, radius_km)
            
        except Exception as e:
            logger.error(f"Error getting current prices: {str(e)}")
            return await self._get_prices_from_db(commodity, location, radius_km)
    
    async def _get_prices_from_db(
        self,
        commodity: str,
        location: Optional[str] = None,
        radius_km: int = 50
    ) -> List[PriceData]:
        """Get prices from database."""
        try:
            db = await get_database()
            collection = db.price_data
            
            # Build query
            query = {
                "commodity": {"$regex": commodity, "$options": "i"},
                "date": {"$gte": (date.today() - timedelta(days=7)).isoformat()}
            }
            
            if location:
                query["$or"] = [
                    {"location.state": {"$regex": location, "$options": "i"}},
                    {"location.district": {"$regex": location, "$options": "i"}},
                    {"market_name": {"$regex": location, "$options": "i"}}
                ]
            
            # Execute query
            cursor = collection.find(query).sort("date", -1).limit(100)
            documents = await cursor.to_list(length=100)
            
            # Convert to PriceData objects
            price_data_list = []
            for doc in documents:
                try:
                    # Convert date string back to date object
                    if isinstance(doc["date"], str):
                        doc["date"] = datetime.fromisoformat(doc["date"]).date()
                    
                    price_data = PriceData(**doc)
                    price_data_list.append(price_data)
                except Exception as e:
                    logger.warning(f"Error parsing price data from DB: {str(e)}")
                    continue
            
            return price_data_list
            
        except Exception as e:
            logger.error(f"Error getting prices from database: {str(e)}")
            return []


# Global service instance
agmarknet_service = AGMARKNETService()