"""
Personalized Insights and Recommendations Models.

Models for user behavior tracking, trading pattern recognition,
and personalized market insights.
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from bson import ObjectId

from app.models.common import PyObjectId, TrendDirection


class UserBehaviorType(str, Enum):
    """Types of user behavior to track."""
    SEARCH = "search"
    VIEW_PRODUCT = "view_product"
    PRICE_CHECK = "price_check"
    NEGOTIATION = "negotiation"
    TRANSACTION = "transaction"
    MARKET_ANALYSIS = "market_analysis"
    ALERT_SUBSCRIPTION = "alert_subscription"
    COMMUNICATION = "communication"


class TradingPatternType(str, Enum):
    """Types of trading patterns."""
    BULK_BUYER = "bulk_buyer"
    FREQUENT_TRADER = "frequent_trader"
    SEASONAL_TRADER = "seasonal_trader"
    PRICE_SENSITIVE = "price_sensitive"
    QUALITY_FOCUSED = "quality_focused"
    REGIONAL_SPECIALIST = "regional_specialist"
    COMMODITY_SPECIALIST = "commodity_specialist"
    OPPORTUNISTIC = "opportunistic"


class InsightType(str, Enum):
    """Types of personalized insights."""
    PRICE_OPPORTUNITY = "price_opportunity"
    SEASONAL_TREND = "seasonal_trend"
    MARKET_SHIFT = "market_shift"
    TRADING_PATTERN = "trading_pattern"
    COMMODITY_RECOMMENDATION = "commodity_recommendation"
    TIMING_SUGGESTION = "timing_suggestion"
    RISK_ALERT = "risk_alert"
    EFFICIENCY_TIP = "efficiency_tip"


class RecommendationType(str, Enum):
    """Types of recommendations."""
    BUY_OPPORTUNITY = "buy_opportunity"
    SELL_OPPORTUNITY = "sell_opportunity"
    MARKET_ENTRY = "market_entry"
    DIVERSIFICATION = "diversification"
    TIMING_OPTIMIZATION = "timing_optimization"
    NEGOTIATION_STRATEGY = "negotiation_strategy"
    SUPPLIER_RECOMMENDATION = "supplier_recommendation"
    QUALITY_UPGRADE = "quality_upgrade"


class ConfidenceLevel(str, Enum):
    """Confidence levels for insights and recommendations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class UserBehaviorEvent(BaseModel):
    """Individual user behavior event."""
    event_id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    event_type: UserBehaviorType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Event-specific data
    commodity: Optional[str] = None
    location: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None  # {"min": 100, "max": 200}
    quantity: Optional[float] = None
    quality_grade: Optional[str] = None
    vendor_id: Optional[str] = None
    transaction_value: Optional[float] = None
    
    # Context data
    session_id: Optional[str] = None
    device_type: Optional[str] = None
    source_page: Optional[str] = None
    search_query: Optional[str] = None
    filters_applied: Optional[Dict[str, Any]] = None
    
    # Outcome data
    action_taken: Optional[str] = None  # "purchased", "negotiated", "saved", "ignored"
    success: Optional[bool] = None
    duration_seconds: Optional[int] = None


class TradingPattern(BaseModel):
    """Identified trading pattern for a user."""
    pattern_id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    pattern_type: TradingPatternType
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Pattern characteristics
    frequency_score: float = 0.0  # How often user trades
    volume_score: float = 0.0  # Average transaction volume
    seasonality_score: float = 0.0  # Seasonal trading behavior
    price_sensitivity_score: float = 0.0  # Response to price changes
    quality_preference_score: float = 0.0  # Preference for quality
    
    # Pattern details
    preferred_commodities: List[str] = []
    preferred_locations: List[str] = []
    typical_quantity_range: Optional[Dict[str, float]] = None
    typical_price_range: Optional[Dict[str, float]] = None
    peak_trading_months: List[int] = []
    preferred_vendors: List[str] = []
    
    # Metadata
    identified_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    sample_size: int = 0  # Number of events used to identify pattern
    pattern_strength: float = 0.0  # How strong/consistent the pattern is


class PersonalizedInsight(BaseModel):
    """Personalized market insight for a user."""
    insight_id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    insight_type: InsightType
    title: str
    description: str
    
    # Insight data
    commodity: Optional[str] = None
    location: Optional[str] = None
    current_price: Optional[float] = None
    predicted_price: Optional[float] = None
    price_change_percentage: Optional[float] = None
    trend_direction: Optional[TrendDirection] = None
    
    # Confidence and relevance
    confidence: ConfidenceLevel
    relevance_score: float = Field(ge=0.0, le=1.0)
    priority: int = Field(ge=1, le=5, default=3)  # 1=highest, 5=lowest
    
    # Supporting data
    supporting_factors: List[str] = []
    data_sources: List[str] = []
    historical_accuracy: Optional[float] = None
    
    # Timing
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # User interaction
    viewed: bool = False
    viewed_at: Optional[datetime] = None
    acted_upon: bool = False
    action_taken: Optional[str] = None
    feedback_rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_comment: Optional[str] = None


class PersonalizedRecommendation(BaseModel):
    """Personalized recommendation for a user."""
    recommendation_id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    recommendation_type: RecommendationType
    title: str
    description: str
    
    # Recommendation details
    commodity: Optional[str] = None
    location: Optional[str] = None
    vendor_id: Optional[str] = None
    suggested_price: Optional[float] = None
    suggested_quantity: Optional[float] = None
    suggested_timing: Optional[str] = None  # "immediate", "within_week", "next_month"
    
    # Expected outcomes
    expected_savings: Optional[float] = None
    expected_profit: Optional[float] = None
    risk_level: Optional[str] = None  # "low", "medium", "high"
    success_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    
    # Confidence and relevance
    confidence: ConfidenceLevel
    relevance_score: float = Field(ge=0.0, le=1.0)
    priority: int = Field(ge=1, le=5, default=3)
    
    # Supporting data
    reasoning: List[str] = []
    similar_users_success: Optional[float] = None
    market_conditions: Optional[Dict[str, Any]] = None
    
    # Timing
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # User interaction
    viewed: bool = False
    viewed_at: Optional[datetime] = None
    accepted: bool = False
    accepted_at: Optional[datetime] = None
    rejected: bool = False
    rejection_reason: Optional[str] = None
    outcome: Optional[str] = None  # "successful", "failed", "partial"
    outcome_value: Optional[float] = None


class UserProfile(BaseModel):
    """Enhanced user profile with behavioral insights."""
    user_id: str
    
    # Trading patterns
    identified_patterns: List[TradingPattern] = []
    primary_pattern: Optional[TradingPatternType] = None
    pattern_confidence: float = 0.0
    
    # Preferences (learned from behavior)
    preferred_commodities: List[str] = []
    preferred_locations: List[str] = []
    preferred_price_ranges: Dict[str, Dict[str, float]] = {}  # commodity -> {min, max}
    preferred_quality_grades: List[str] = []
    preferred_vendors: List[str] = []
    
    # Trading characteristics
    average_transaction_value: float = 0.0
    trading_frequency: float = 0.0  # transactions per month
    price_sensitivity: float = 0.0  # 0-1 scale
    quality_focus: float = 0.0  # 0-1 scale
    risk_tolerance: float = 0.5  # 0-1 scale
    
    # Seasonal behavior
    peak_trading_months: List[int] = []
    seasonal_commodities: Dict[int, List[str]] = {}  # month -> commodities
    
    # Engagement metrics
    platform_usage_hours_per_week: float = 0.0
    feature_usage_frequency: Dict[str, float] = {}
    response_rate_to_recommendations: float = 0.0
    average_session_duration_minutes: float = 0.0
    
    # Learning and adaptation
    learning_rate: float = 0.1  # How quickly to adapt to new behavior
    stability_score: float = 0.5  # How stable user's patterns are
    last_pattern_update: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata
    profile_created: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    total_behavior_events: int = 0
    profile_completeness: float = 0.0  # 0-1 score of how complete the profile is


class InsightGenerationConfig(BaseModel):
    """Configuration for insight generation."""
    user_id: str
    
    # Generation settings
    max_insights_per_type: int = 5
    min_confidence_threshold: float = 0.6
    min_relevance_threshold: float = 0.7
    lookback_days: int = 30
    lookahead_days: int = 14
    
    # Personalization settings
    use_trading_patterns: bool = True
    use_seasonal_behavior: bool = True
    use_price_sensitivity: bool = True
    use_similar_users: bool = True
    
    # Content preferences
    preferred_languages: List[str] = ["en"]
    include_risk_alerts: bool = True
    include_opportunity_alerts: bool = True
    include_efficiency_tips: bool = True
    
    # Delivery preferences
    delivery_frequency: str = "daily"  # "realtime", "daily", "weekly"
    preferred_channels: List[str] = ["app", "email"]
    quiet_hours_start: Optional[int] = None  # Hour of day (0-23)
    quiet_hours_end: Optional[int] = None


class SimilarUserGroup(BaseModel):
    """Group of users with similar trading patterns."""
    group_id: str = Field(default_factory=lambda: str(ObjectId()))
    group_name: str
    description: str
    
    # Group characteristics
    primary_pattern: TradingPatternType
    common_commodities: List[str] = []
    common_locations: List[str] = []
    average_transaction_value: float = 0.0
    average_trading_frequency: float = 0.0
    
    # Group members
    member_user_ids: List[str] = []
    member_count: int = 0
    
    # Group insights
    successful_strategies: List[str] = []
    common_mistakes: List[str] = []
    best_performing_members: List[str] = []
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    group_stability: float = 0.0  # How stable the group composition is


class RecommendationFeedback(BaseModel):
    """Feedback on recommendations for learning."""
    feedback_id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    recommendation_id: str
    
    # Feedback data
    rating: int = Field(ge=1, le=5)
    usefulness: int = Field(ge=1, le=5)
    accuracy: int = Field(ge=1, le=5)
    timeliness: int = Field(ge=1, le=5)
    
    # Qualitative feedback
    comment: Optional[str] = None
    improvement_suggestions: List[str] = []
    
    # Outcome data
    followed_recommendation: bool = False
    outcome_successful: Optional[bool] = None
    actual_savings: Optional[float] = None
    actual_profit: Optional[float] = None
    
    # Metadata
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    recommendation_created_at: datetime
    time_to_feedback_hours: Optional[float] = None


class PersonalizedInsightsRequest(BaseModel):
    """Request for personalized insights."""
    user_id: str
    insight_types: Optional[List[InsightType]] = None
    commodities: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    max_results: int = Field(default=10, ge=1, le=50)
    min_confidence: Optional[ConfidenceLevel] = None
    include_historical: bool = False


class PersonalizedRecommendationsRequest(BaseModel):
    """Request for personalized recommendations."""
    user_id: str
    recommendation_types: Optional[List[RecommendationType]] = None
    commodities: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    max_results: int = Field(default=5, ge=1, le=20)
    min_confidence: Optional[ConfidenceLevel] = None
    risk_tolerance: Optional[str] = None  # "low", "medium", "high"


class BehaviorAnalysisResult(BaseModel):
    """Result of user behavior analysis."""
    user_id: str
    analysis_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Analysis period
    period_start: datetime
    period_end: datetime
    total_events: int
    
    # Identified patterns
    patterns: List[TradingPattern] = []
    pattern_changes: List[str] = []  # Changes from previous analysis
    
    # Behavioral insights
    activity_level: str  # "low", "medium", "high"
    engagement_score: float = Field(ge=0.0, le=1.0)
    consistency_score: float = Field(ge=0.0, le=1.0)
    learning_indicators: List[str] = []
    
    # Recommendations for profile updates
    suggested_profile_updates: Dict[str, Any] = {}
    confidence_in_analysis: float = Field(ge=0.0, le=1.0)


class MarketOpportunity(BaseModel):
    """Market opportunity identified for a user."""
    opportunity_id: str = Field(default_factory=lambda: str(ObjectId()))
    user_id: str
    
    # Opportunity details
    opportunity_type: str  # "price_arbitrage", "seasonal_demand", "supply_shortage"
    commodity: str
    location: str
    
    # Financial details
    current_price: float
    opportunity_price: float
    potential_profit_percentage: float
    estimated_volume: Optional[float] = None
    total_potential_profit: Optional[float] = None
    
    # Timing
    opportunity_window_start: datetime
    opportunity_window_end: datetime
    urgency: str  # "low", "medium", "high", "critical"
    
    # Risk assessment
    risk_level: str  # "low", "medium", "high"
    risk_factors: List[str] = []
    success_probability: float = Field(ge=0.0, le=1.0)
    
    # Personalization
    relevance_to_user: float = Field(ge=0.0, le=1.0)
    matches_user_patterns: bool = False
    similar_past_successes: int = 0
    
    # Metadata
    identified_at: datetime = Field(default_factory=datetime.utcnow)
    source: str  # "price_analysis", "seasonal_pattern", "market_intelligence"
    confidence: ConfidenceLevel