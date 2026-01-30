"""
Market data models for external price integration.

This module contains models for market data from external sources like Agmarknet,
price history tracking, and data validation structures.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class DataSource(str, Enum):
    """External data sources for market information."""
    AGMARKNET = "agmarknet"
    COMMODITY_API = "commodity_api"
    MANUAL = "manual"
    PREDICTED = "predicted"


class DataQuality(str, Enum):
    """Data quality indicators."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class PriceUnit(str, Enum):
    """Price units for market data."""
    PER_KG = "per_kg"
    PER_QUINTAL = "per_quintal"
    PER_TON = "per_ton"
    PER_PIECE = "per_piece"
    PER_DOZEN = "per_dozen"


class MarketPrice(BaseModel):
    """Market price data from external sources."""
    price_id: Optional[str] = Field(None, description="Unique price record identifier")
    commodity: str = Field(..., description="Commodity name")
    variety: Optional[str] = Field(None, description="Commodity variety")
    market: str = Field(..., description="Market/mandi name")
    state: str = Field(..., description="State name")
    district: Optional[str] = Field(None, description="District name")
    
    # Price information
    min_price: Decimal = Field(..., ge=0, description="Minimum price")
    max_price: Decimal = Field(..., ge=0, description="Maximum price")
    modal_price: Decimal = Field(..., ge=0, description="Modal/average price")
    unit: PriceUnit = Field(..., description="Price unit")
    currency: str = Field(default="INR", description="Currency code")
    
    # Market data
    arrivals: Optional[int] = Field(None, ge=0, description="Quantity arrived in market")
    arrivals_unit: Optional[str] = Field(None, description="Unit for arrivals")
    
    # Metadata
    price_date: date = Field(..., description="Price date")
    source: DataSource = Field(..., description="Data source")
    data_quality: DataQuality = Field(default=DataQuality.UNVERIFIED, description="Data quality indicator")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    # Validation flags
    is_validated: bool = Field(default=False, description="Whether data has been validated")
    validation_notes: Optional[str] = Field(None, description="Validation notes")
    
    @validator("max_price")
    def validate_price_range(cls, v, values):
        if "min_price" in values and v < values["min_price"]:
            raise ValueError("Maximum price must be greater than or equal to minimum price")
        return v
    
    @validator("modal_price")
    def validate_modal_price(cls, v, values):
        if "min_price" in values and "max_price" in values:
            min_price = values["min_price"]
            max_price = values["max_price"]
            if v < min_price or v > max_price:
                raise ValueError("Modal price must be between minimum and maximum price")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class PriceHistory(BaseModel):
    """Historical price data for a commodity."""
    commodity: str = Field(..., description="Commodity name")
    variety: Optional[str] = Field(None, description="Commodity variety")
    market: str = Field(..., description="Market name")
    state: str = Field(..., description="State name")
    
    # Price data points
    prices: List[MarketPrice] = Field(..., description="Historical price points")
    
    # Statistics
    period_start: date = Field(..., description="Start date of the period")
    period_end: date = Field(..., description="End date of the period")
    average_price: Decimal = Field(..., description="Average price over the period")
    price_volatility: float = Field(..., description="Price volatility (standard deviation)")
    trend: str = Field(..., description="Price trend (increasing/decreasing/stable)")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    @validator("period_end")
    def validate_period(cls, v, values):
        if "period_start" in values and v < values["period_start"]:
            raise ValueError("Period end must be after period start")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class DataValidationResult(BaseModel):
    """Result of data validation checks."""
    is_valid: bool = Field(..., description="Whether data passed validation")
    quality_score: float = Field(..., ge=0, le=1, description="Quality score (0-1)")
    validation_checks: Dict[str, bool] = Field(..., description="Individual validation check results")
    issues: List[str] = Field(default=[], description="List of validation issues")
    recommendations: List[str] = Field(default=[], description="Recommendations for data improvement")
    validated_at: datetime = Field(default_factory=datetime.utcnow, description="Validation timestamp")


class MarketDataCache(BaseModel):
    """Cached market data with expiration."""
    cache_key: str = Field(..., description="Cache key")
    data: Dict[str, Any] = Field(..., description="Cached data")
    cached_at: datetime = Field(default_factory=datetime.utcnow, description="Cache timestamp")
    expires_at: datetime = Field(..., description="Cache expiration timestamp")
    source: DataSource = Field(..., description="Data source")
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return datetime.utcnow() > self.expires_at


# Request/Response models
class MarketPriceRequest(BaseModel):
    """Request model for market price data."""
    commodity: str = Field(..., min_length=2, max_length=100, description="Commodity name")
    variety: Optional[str] = Field(None, max_length=100, description="Commodity variety")
    market: Optional[str] = Field(None, max_length=100, description="Specific market name")
    state: Optional[str] = Field(None, max_length=50, description="State name")
    date_from: Optional[date] = Field(None, description="Start date for price data")
    date_to: Optional[date] = Field(None, description="End date for price data")
    
    @validator("date_to")
    def validate_date_range(cls, v, values):
        if v is not None and "date_from" in values and values["date_from"] and v < values["date_from"]:
            raise ValueError("End date must be after start date")
        return v


class MarketPriceResponse(BaseModel):
    """Response model for market price data."""
    commodity: str = Field(..., description="Commodity name")
    variety: Optional[str] = Field(None, description="Commodity variety")
    prices: List[MarketPrice] = Field(..., description="Price data")
    summary: Dict[str, Any] = Field(..., description="Price summary statistics")
    data_quality: DataQuality = Field(..., description="Overall data quality")
    last_updated: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class PriceHistoryRequest(BaseModel):
    """Request model for price history data."""
    commodity: str = Field(..., min_length=2, max_length=100, description="Commodity name")
    variety: Optional[str] = Field(None, max_length=100, description="Commodity variety")
    market: Optional[str] = Field(None, max_length=100, description="Market name")
    state: Optional[str] = Field(None, max_length=50, description="State name")
    days: int = Field(default=30, ge=1, le=365, description="Number of days of history")
    include_predictions: bool = Field(default=False, description="Include price predictions")


class PriceHistoryResponse(BaseModel):
    """Response model for price history data."""
    commodity: str = Field(..., description="Commodity name")
    variety: Optional[str] = Field(None, description="Commodity variety")
    history: PriceHistory = Field(..., description="Historical price data")
    trends: Dict[str, Any] = Field(..., description="Price trend analysis")
    predictions: Optional[List[Dict[str, Any]]] = Field(None, description="Future price predictions")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class DataSyncStatus(BaseModel):
    """Status of data synchronization from external sources."""
    source: DataSource = Field(..., description="Data source")
    last_sync: datetime = Field(..., description="Last successful sync timestamp")
    next_sync: datetime = Field(..., description="Next scheduled sync timestamp")
    sync_status: str = Field(..., description="Current sync status")
    records_synced: int = Field(default=0, description="Number of records synced")
    errors: List[str] = Field(default=[], description="Sync errors")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }


class AgmarknetApiResponse(BaseModel):
    """Response model for Agmarknet API data."""
    status: str = Field(..., description="API response status")
    total: int = Field(..., description="Total records")
    count: int = Field(..., description="Records in current response")
    records: List[Dict[str, Any]] = Field(..., description="Raw API records")
    
    def to_market_prices(self) -> List[MarketPrice]:
        """Convert Agmarknet API response to MarketPrice objects."""
        market_prices = []
        
        for record in self.records:
            try:
                # Parse Agmarknet record format
                market_price = MarketPrice(
                    commodity=record.get("commodity", "").strip(),
                    variety=record.get("variety", "").strip() or None,
                    market=record.get("market", "").strip(),
                    state=record.get("state", "").strip(),
                    district=record.get("district", "").strip() or None,
                    min_price=Decimal(str(record.get("min_price", 0))),
                    max_price=Decimal(str(record.get("max_price", 0))),
                    modal_price=Decimal(str(record.get("modal_price", 0))),
                    unit=PriceUnit.PER_QUINTAL,  # Agmarknet typically uses quintal
                    arrivals=int(record.get("arrivals", 0)) if record.get("arrivals") else None,
                    arrivals_unit="quintal",
                    date=datetime.strptime(record.get("date", ""), "%Y-%m-%d").date(),
                    source=DataSource.AGMARKNET,
                    data_quality=DataQuality.MEDIUM,  # Default quality for Agmarknet
                )
                market_prices.append(market_price)
            except (ValueError, KeyError, TypeError) as e:
                # Skip invalid records but log the error
                continue
        
        return market_prices