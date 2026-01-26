"""
Market analytics and forecasting models.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

from app.models.common import TimePeriod, TrendDirection


class ForecastModel(str, Enum):
    """Forecasting model types."""
    ARIMA = "arima"
    LINEAR_REGRESSION = "linear_regression"
    MOVING_AVERAGE = "moving_average"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    ENSEMBLE = "ensemble"


class WeatherCondition(str, Enum):
    """Weather conditions affecting commodity prices."""
    NORMAL = "normal"
    DROUGHT = "drought"
    FLOOD = "flood"
    EXCESSIVE_RAIN = "excessive_rain"
    CYCLONE = "cyclone"
    HAILSTORM = "hailstorm"
    FROST = "frost"
    HEAT_WAVE = "heat_wave"


class FestivalType(str, Enum):
    """Types of festivals affecting demand."""
    RELIGIOUS = "religious"
    HARVEST = "harvest"
    NATIONAL = "national"
    REGIONAL = "regional"
    SEASONAL = "seasonal"


class TradeDirection(str, Enum):
    """Trade direction for export-import analysis."""
    EXPORT = "export"
    IMPORT = "import"
    BOTH = "both"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DemandForecast(BaseModel):
    """Demand forecasting result."""
    commodity: str
    location: Optional[str] = None
    forecast_date: date
    forecast_period_days: int
    predicted_demand: float  # Relative demand multiplier (1.0 = normal)
    confidence: float = Field(..., ge=0, le=1)
    demand_trend: TrendDirection
    seasonal_factor: float = 1.0
    weather_factor: float = 1.0
    festival_factor: float = 1.0
    export_import_factor: float = 1.0
    historical_accuracy: Optional[float] = None
    model_used: ForecastModel
    factors_considered: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WeatherImpactPrediction(BaseModel):
    """Weather impact prediction on commodity prices."""
    commodity: str
    weather_condition: WeatherCondition
    affected_regions: List[str]
    impact_start_date: date
    impact_duration_days: int
    price_impact_percentage: float  # Expected price change percentage
    supply_impact_percentage: float  # Expected supply change percentage
    confidence: float = Field(..., ge=0, le=1)
    historical_precedents: List[Dict[str, Any]] = []
    mitigation_suggestions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SeasonalDemandAlert(BaseModel):
    """Seasonal and festival demand alert."""
    alert_id: str
    commodity: str
    location: Optional[str] = None
    alert_type: str  # "seasonal", "festival", "harvest"
    event_name: str
    event_start_date: date
    event_end_date: date
    expected_demand_change: float  # Percentage change in demand
    price_impact_prediction: float  # Expected price change percentage
    severity: AlertSeverity
    affected_markets: List[str] = []
    preparation_suggestions: List[str] = []
    historical_data: Optional[Dict[str, Any]] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    triggered_at: Optional[datetime] = None


class ExportImportData(BaseModel):
    """Export-import trade data."""
    commodity: str
    trade_direction: TradeDirection
    country: str
    volume: float  # In metric tons
    value: float  # In USD
    unit_price: float  # USD per unit
    trade_date: date
    port_of_entry_exit: Optional[str] = None
    quality_grade: Optional[str] = None
    source: str = "government_data"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExportImportInfluence(BaseModel):
    """Export-import price influence analysis."""
    commodity: str
    analysis_date: date
    domestic_price: float
    international_price: float
    price_differential: float  # Domestic - International
    price_differential_percentage: float
    trade_balance: float  # Net export (+) or import (-)
    influence_factor: float  # How much international prices affect domestic
    arbitrage_opportunity: Optional[str] = None  # "export", "import", "none"
    key_trading_partners: List[Dict[str, Any]] = []
    trade_policy_impact: Optional[str] = None
    recommendations: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MarketAnalytics(BaseModel):
    """Comprehensive market analytics result."""
    commodity: str
    location: Optional[str] = None
    analysis_date: date
    analysis_period_days: int
    
    # Demand forecasting
    demand_forecast: Optional[DemandForecast] = None
    
    # Weather impact
    weather_predictions: List[WeatherImpactPrediction] = []
    
    # Seasonal and festival alerts
    active_alerts: List[SeasonalDemandAlert] = []
    
    # Export-import analysis
    trade_influence: Optional[ExportImportInfluence] = None
    
    # Summary metrics
    overall_market_sentiment: str  # "bullish", "bearish", "neutral"
    risk_assessment: str  # "low", "medium", "high"
    confidence_score: float = Field(..., ge=0, le=1)
    
    # Recommendations
    trading_recommendations: List[str] = []
    risk_mitigation_strategies: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FestivalCalendar(BaseModel):
    """Festival calendar entry."""
    festival_name: str
    festival_type: FestivalType
    start_date: date
    end_date: date
    regions: List[str]
    affected_commodities: List[str]
    demand_multiplier: float = 1.0  # Expected demand increase
    historical_impact: Optional[Dict[str, float]] = None  # commodity -> avg price increase %
    preparation_days: int = 7  # Days before festival to start alerts
    description: Optional[str] = None


class WeatherAlert(BaseModel):
    """Weather-based market alert."""
    alert_id: str
    commodity: str
    weather_condition: WeatherCondition
    affected_regions: List[str]
    alert_date: date
    severity: AlertSeverity
    expected_impact: str
    duration_estimate: str
    action_recommendations: List[str] = []
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MarketIntelligenceReport(BaseModel):
    """Comprehensive market intelligence report."""
    report_id: str
    commodity: str
    location: Optional[str] = None
    report_date: date
    report_type: str  # "daily", "weekly", "monthly"
    
    # Key metrics
    current_price: float
    price_change_24h: float
    price_change_7d: float
    price_change_30d: float
    
    # Analytics components
    demand_analysis: Optional[DemandForecast] = None
    weather_analysis: List[WeatherImpactPrediction] = []
    seasonal_analysis: List[SeasonalDemandAlert] = []
    trade_analysis: Optional[ExportImportInfluence] = None
    
    # Market insights
    key_insights: List[str] = []
    market_drivers: List[str] = []
    risk_factors: List[str] = []
    opportunities: List[str] = []
    
    # Forecasts
    short_term_outlook: str  # 1-7 days
    medium_term_outlook: str  # 1-4 weeks
    long_term_outlook: str  # 1-3 months
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalyticsConfiguration(BaseModel):
    """Configuration for market analytics service."""
    commodity: str
    location: Optional[str] = None
    
    # Forecasting settings
    enable_demand_forecasting: bool = True
    forecasting_horizon_days: int = 30
    forecasting_models: List[ForecastModel] = [ForecastModel.ENSEMBLE]
    
    # Weather monitoring
    enable_weather_monitoring: bool = True
    weather_alert_threshold: float = 0.1  # 10% price impact threshold
    
    # Festival monitoring
    enable_festival_alerts: bool = True
    festival_alert_days_ahead: int = 7
    
    # Trade monitoring
    enable_trade_monitoring: bool = True
    trade_data_sources: List[str] = ["government", "market"]
    
    # Alert settings
    alert_severity_threshold: AlertSeverity = AlertSeverity.MEDIUM
    notification_channels: List[str] = ["email", "sms", "push"]
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HistoricalAccuracy(BaseModel):
    """Historical accuracy tracking for forecasting models."""
    model_name: str
    commodity: str
    location: Optional[str] = None
    forecast_horizon_days: int
    accuracy_percentage: float
    mean_absolute_error: float
    root_mean_square_error: float
    evaluation_period_start: date
    evaluation_period_end: date
    sample_size: int
    last_updated: datetime = Field(default_factory=datetime.utcnow)


class AlertSubscription(BaseModel):
    """User subscription to market analytics alerts."""
    user_id: str
    commodity: str
    location: Optional[str] = None
    alert_types: List[str] = []  # "demand", "weather", "seasonal", "trade"
    severity_threshold: AlertSeverity = AlertSeverity.MEDIUM
    notification_preferences: Dict[str, bool] = {
        "email": True,
        "sms": False,
        "push": True
    }
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)