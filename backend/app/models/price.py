"""
Price and market data models.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from app.models.common import QualityGrade, TrendDirection, TimePeriod


class PriceSource(str, Enum):
    """Price data sources."""
    AGMARKNET = "agmarknet"
    MANUAL = "manual"
    PREDICTED = "predicted"
    CACHED = "cached"


class MarketType(str, Enum):
    """Market types."""
    WHOLESALE = "wholesale"
    RETAIL = "retail"
    MANDI = "mandi"
    ONLINE = "online"


class Location(BaseModel):
    """Geographic location model."""
    state: str
    district: str
    market_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    pincode: Optional[str] = None
    
    def distance_to(self, other: 'Location') -> Optional[float]:
        """Calculate distance to another location in kilometers."""
        if not all([self.latitude, self.longitude, other.latitude, other.longitude]):
            return None
        
        import math
        
        # Haversine formula for calculating distance between two points on Earth
        lat1, lon1 = math.radians(self.latitude), math.radians(self.longitude)
        lat2, lon2 = math.radians(other.latitude), math.radians(other.longitude)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth's radius in kilometers
        earth_radius = 6371.0
        
        return earth_radius * c


class PriceData(BaseModel):
    """Individual price data point."""
    commodity: str
    variety: Optional[str] = None
    market_name: str
    location: Location
    price_min: float = Field(..., ge=0)
    price_max: float = Field(..., ge=0)
    price_modal: float = Field(..., ge=0)  # Most common price
    quality_grade: QualityGrade = QualityGrade.STANDARD
    unit: str = "quintal"  # Default unit for Indian markets
    date: date
    source: PriceSource
    market_type: MarketType = MarketType.MANDI
    arrivals: Optional[float] = None  # Quantity arrived in market
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class PricePoint(BaseModel):
    """Price point for trend analysis."""
    date: date
    price: float
    volume: Optional[float] = None


class SeasonalFactor(BaseModel):
    """Seasonal price factor."""
    month: int = Field(..., ge=1, le=12)
    factor: float  # Multiplier for seasonal adjustment
    description: str


class MarketTrend(BaseModel):
    """Market trend analysis."""
    commodity: str
    location: Optional[str] = None
    time_period: TimePeriod
    price_points: List[PricePoint]
    trend_direction: TrendDirection
    volatility_index: float = Field(..., ge=0, le=1)
    seasonal_factors: List[SeasonalFactor] = []
    prediction_confidence: float = Field(..., ge=0, le=1)
    analysis_date: datetime = Field(default_factory=datetime.utcnow)


class PriceForecast(BaseModel):
    """Price forecast model."""
    commodity: str
    location: Optional[str] = None
    forecast_date: date
    predicted_price: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    confidence: float = Field(..., ge=0, le=1)
    factors_considered: List[str] = []
    model_used: str = "seasonal_arima"


class MarketComparison(BaseModel):
    """Market price comparison."""
    commodity: str
    comparison_date: date
    markets: List[PriceData]
    price_spread: float  # Difference between highest and lowest
    average_price: float
    best_market: str  # Market with best price for buyers
    analysis: Dict[str, Any] = {}


class MSPData(BaseModel):
    """Minimum Support Price data."""
    commodity: str
    crop_year: str  # e.g., "2024-25"
    msp_price: float
    effective_from: date
    effective_to: Optional[date] = None
    unit: str = "quintal"
    source: str = "government"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PriceAlert(BaseModel):
    """Price alert configuration."""
    user_id: str
    commodity: str
    location: Optional[str] = None
    alert_type: str  # "above", "below", "change"
    threshold_price: float
    percentage_change: Optional[float] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None


class AGMARKNETResponse(BaseModel):
    """AGMARKNET API response model."""
    status: str
    message: str
    data: List[Dict[str, Any]]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PriceQuery(BaseModel):
    """Price query parameters."""
    commodity: str
    location: Optional[str] = None
    radius_km: int = Field(50, ge=1, le=500)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    quality_grade: Optional[QualityGrade] = None
    market_type: Optional[MarketType] = None
    include_predictions: bool = False


class PriceSearchResult(BaseModel):
    """Price search result."""
    query: PriceQuery
    results: List[PriceData]
    total_count: int
    average_price: Optional[float] = None
    price_range: Optional[Dict[str, float]] = None  # min, max
    last_updated: datetime
    cache_hit: bool = False


class WeatherImpact(BaseModel):
    """Weather impact on prices."""
    commodity: str
    weather_condition: str  # "drought", "flood", "normal", "excessive_rain"
    impact_factor: float  # Multiplier for price impact
    affected_regions: List[str]
    impact_duration_days: int
    confidence: float = Field(..., ge=0, le=1)


class FestivalDemand(BaseModel):
    """Festival demand impact."""
    festival_name: str
    affected_commodities: List[str]
    demand_multiplier: float
    start_date: date
    end_date: date
    regions: List[str]
    historical_impact: Optional[float] = None


class TrendAnalysisResult(BaseModel):
    """Comprehensive trend analysis result."""
    commodity: str
    location: Optional[str] = None
    analysis_period_days: int
    data_points: int
    price_statistics: Dict[str, float]
    trend_analysis: Dict[str, Any]
    seasonal_patterns: Dict[str, Any]
    volatility_analysis: Dict[str, Any]
    anomalies: List[Dict[str, Any]]
    support_resistance: Dict[str, Any]
    moving_averages: Dict[str, Any]
    momentum_indicators: Dict[str, Any]
    analysis_date: datetime = Field(default_factory=datetime.utcnow)


class EnsemblePrediction(BaseModel):
    """Ensemble prediction result."""
    commodity: str
    location: Optional[str] = None
    forecast_days: int
    predicted_price: float
    confidence: float = Field(..., ge=0, le=1)
    confidence_interval_lower: float
    confidence_interval_upper: float
    model_weights: Dict[str, float]
    individual_predictions: Dict[str, PriceForecast]
    model_agreement: str  # "high", "medium", "low"
    data_points_used: int
    prediction_date: datetime = Field(default_factory=datetime.utcnow)


class VolatilityMetrics(BaseModel):
    """Volatility analysis metrics."""
    standard_deviation: float
    coefficient_of_variation: float
    volatility_classification: str  # "low", "moderate", "high"
    rolling_volatility_avg: Optional[float] = None
    volatility_trend: str  # "increasing", "decreasing", "stable"
    value_at_risk_95: Optional[float] = None
    maximum_drawdown: Optional[float] = None
    sharpe_ratio: Optional[float] = None


class SeasonalPattern(BaseModel):
    """Seasonal pattern analysis."""
    commodity: str
    monthly_averages: Dict[int, float]  # month -> average price
    seasonal_factors: Dict[int, float]  # month -> seasonal factor
    peak_month: int
    trough_month: int
    seasonality_strength: float
    seasonal_classification: str  # "high", "moderate", "low"
    yearly_patterns: Optional[Dict[int, Dict[int, float]]] = None  # year -> month -> price


class PriceAnomaly(BaseModel):
    """Price anomaly detection result."""
    date: date
    price: float
    z_score: float
    anomaly_type: str  # "spike", "drop"
    severity: str  # "moderate", "extreme"
    deviation_from_mean: float
    percentage_deviation: float


class SupportResistanceLevels(BaseModel):
    """Support and resistance levels."""
    support_levels: List[float]
    resistance_levels: List[float]
    current_price: float
    position: str  # "above_resistance", "below_support", "in_range"


class MomentumIndicators(BaseModel):
    """Price momentum indicators."""
    rate_of_change: Dict[str, float]  # period -> ROC value
    rsi: Optional[float] = None
    momentum_classification: str  # "strong_bullish", "bullish", "neutral", "bearish", "strong_bearish"


class GeographicPriceQuery(BaseModel):
    """Geographic price query parameters."""
    commodity: str
    center_location: Location
    radius_km: int = Field(50, ge=1, le=500)
    quality_grades: Optional[List[QualityGrade]] = None
    market_types: Optional[List[MarketType]] = None
    include_msp_comparison: bool = True
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class GeographicPriceResult(BaseModel):
    """Geographic price search result with distance information."""
    price_data: PriceData
    distance_km: Optional[float] = None
    msp_comparison: Optional[Dict[str, Any]] = None


class RadiusFilterResult(BaseModel):
    """Result of radius-based price filtering."""
    query: GeographicPriceQuery
    results: List[GeographicPriceResult]
    total_markets: int
    average_price: Optional[float] = None
    price_statistics: Dict[str, float]
    distance_statistics: Dict[str, float]
    msp_analysis: Optional[Dict[str, Any]] = None
    quality_distribution: Dict[str, int]
    search_timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketDistanceInfo(BaseModel):
    """Market information with distance."""
    market_name: str
    location: Location
    distance_km: Optional[float] = None
    price_data: List[PriceData] = []
    average_price: Optional[float] = None
    quality_grades_available: List[QualityGrade] = []


class GeographicMarketComparison(BaseModel):
    """Geographic market comparison within radius."""
    commodity: str
    center_location: Location
    radius_km: int
    markets: List[MarketDistanceInfo]
    comparison_date: date
    best_price_market: Optional[str] = None
    nearest_market: Optional[str] = None
    price_range: Dict[str, float]  # min, max, spread
    distance_range: Dict[str, float]  # min, max, average
    recommendations: List[str] = []


class QualityBasedPriceCategory(BaseModel):
    """Quality-based price categorization."""
    commodity: str
    location: Optional[str] = None
    quality_grade: QualityGrade
    price_range: Dict[str, float]  # min, max, average
    market_count: int
    price_premium_percentage: Optional[float] = None  # Premium over standard grade
    availability_score: float = Field(..., ge=0, le=1)  # Based on market count and volume


class QualityPriceCategorization(BaseModel):
    """Complete quality-based price categorization."""
    commodity: str
    location: Optional[str] = None
    analysis_date: date
    categories: List[QualityBasedPriceCategory]
    overall_statistics: Dict[str, Any]
    quality_recommendations: List[str] = []