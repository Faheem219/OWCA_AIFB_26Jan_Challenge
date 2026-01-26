"""
Negotiation models and AI guidance.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from bson import ObjectId

from app.models.common import PyObjectId


class NegotiationStatus(str, Enum):
    """Negotiation status."""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COUNTER_OFFERED = "counter_offered"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class OfferType(str, Enum):
    """Type of offer in negotiation."""
    INITIAL = "initial"
    COUNTER = "counter"
    FINAL = "final"


class NegotiationStrategy(str, Enum):
    """AI negotiation strategies."""
    COMPETITIVE = "competitive"
    COLLABORATIVE = "collaborative"
    ACCOMMODATING = "accommodating"
    COMPROMISING = "compromising"
    AVOIDING = "avoiding"


class CulturalContext(str, Enum):
    """Cultural contexts for negotiations."""
    NORTH_INDIAN = "north_indian"
    SOUTH_INDIAN = "south_indian"
    WESTERN_INDIAN = "western_indian"
    EASTERN_INDIAN = "eastern_indian"
    CENTRAL_INDIAN = "central_indian"
    URBAN = "urban"
    RURAL = "rural"
    TRADITIONAL = "traditional"
    MODERN = "modern"


class SeasonalFactor(str, Enum):
    """Seasonal factors affecting negotiations."""
    HARVEST_SEASON = "harvest_season"
    OFF_SEASON = "off_season"
    FESTIVAL_SEASON = "festival_season"
    MONSOON = "monsoon"
    WINTER = "winter"
    SUMMER = "summer"


class MarketCondition(str, Enum):
    """Market conditions."""
    HIGH_DEMAND = "high_demand"
    LOW_DEMAND = "low_demand"
    OVERSUPPLY = "oversupply"
    SHORTAGE = "shortage"
    STABLE = "stable"
    VOLATILE = "volatile"


class Offer(BaseModel):
    """Negotiation offer model."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    product_id: str
    quantity: float
    unit_price: float
    total_amount: float
    offer_type: OfferType
    valid_until: datetime
    terms_and_conditions: Optional[str] = None
    bulk_discount_applied: Optional[float] = None
    delivery_terms: Optional[str] = None
    payment_terms: Optional[str] = None
    quality_requirements: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NegotiationStep(BaseModel):
    """Individual step in negotiation process."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    step_number: int
    participant_id: str  # User who made this step
    participant_role: str  # "buyer" or "seller"
    action: str  # "offer", "counter_offer", "accept", "reject", "message"
    offer: Optional[Offer] = None
    message: Optional[str] = None
    ai_recommendation_used: bool = False
    ai_recommendation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MarketContext(BaseModel):
    """Market context for AI recommendations."""
    commodity: str
    location: str
    current_market_price: float
    price_trend: str  # "rising", "falling", "stable"
    seasonal_factor: Optional[SeasonalFactor] = None
    market_condition: MarketCondition
    supply_demand_ratio: float
    weather_impact: Optional[str] = None
    festival_impact: Optional[str] = None
    msp_price: Optional[float] = None
    export_price: Optional[float] = None


class CulturalGuidance(BaseModel):
    """Cultural guidance for negotiations."""
    buyer_region: str
    seller_region: str
    cultural_context: CulturalContext
    greeting_style: str
    negotiation_approach: str
    cultural_sensitivities: List[str]
    recommended_phrases: Dict[str, str]  # language -> phrase
    taboo_topics: List[str]
    gift_giving_customs: Optional[str] = None
    time_orientation: str  # "punctual", "flexible"
    relationship_importance: str  # "high", "medium", "low"


class PriceRecommendation(BaseModel):
    """AI price recommendation."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    recommended_price: float
    price_range_min: float
    price_range_max: float
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning: str
    factors_considered: List[str]
    market_comparison: Dict[str, float]
    risk_assessment: str  # "low", "medium", "high"
    success_probability: float = Field(ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CounterOfferSuggestion(BaseModel):
    """AI counter-offer suggestion."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    suggested_price: float
    negotiation_strategy: NegotiationStrategy
    justification: str
    cultural_considerations: Optional[str] = None
    bulk_discount_applicable: bool = False
    bulk_discount_percentage: Optional[float] = None
    seasonal_factors: List[str] = []
    market_factors: List[str] = []
    psychological_factors: List[str] = []
    success_probability: float = Field(ge=0.0, le=1.0)
    alternative_offers: List[Dict[str, Any]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class NegotiationSession(BaseModel):
    """Complete negotiation session."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: str
    buyer_id: str
    seller_id: str
    initial_offer: Offer
    current_offer: Optional[Offer] = None
    status: NegotiationStatus = NegotiationStatus.INITIATED
    steps: List[NegotiationStep] = []
    market_context: Optional[MarketContext] = None
    cultural_guidance: Optional[CulturalGuidance] = None
    ai_recommendations: List[Union[PriceRecommendation, CounterOfferSuggestion]] = []
    final_agreed_price: Optional[float] = None
    final_agreed_quantity: Optional[float] = None
    agreement_terms: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class NegotiationCreate(BaseModel):
    """Create negotiation session."""
    product_id: str
    seller_id: str
    initial_offer: Offer
    message: Optional[str] = None


class NegotiationUpdate(BaseModel):
    """Update negotiation session."""
    action: str  # "counter_offer", "accept", "reject", "message"
    offer: Optional[Offer] = None
    message: Optional[str] = None
    use_ai_recommendation: bool = False


class NegotiationAnalytics(BaseModel):
    """Negotiation analytics."""
    session_id: str
    total_steps: int
    duration_hours: float
    success_rate: float
    average_discount_percentage: float
    ai_recommendations_used: int
    ai_recommendations_successful: int
    cultural_factors_impact: Dict[str, float]
    seasonal_factors_impact: Dict[str, float]
    final_price_vs_market: float
    participant_satisfaction: Optional[Dict[str, float]] = None


class NegotiationInsights(BaseModel):
    """AI insights for negotiation improvement."""
    user_id: str
    negotiation_style: str
    success_patterns: List[str]
    improvement_areas: List[str]
    cultural_adaptation_score: float
    market_awareness_score: float
    timing_effectiveness: float
    recommended_strategies: List[NegotiationStrategy]
    personalized_tips: List[str]


class BulkNegotiationRequest(BaseModel):
    """Bulk negotiation for multiple products."""
    product_requests: List[Dict[str, Any]]  # product_id, quantity, max_price
    seller_id: str
    delivery_location: str
    delivery_timeline: str
    payment_terms: str
    total_budget: Optional[float] = None
    priority_products: List[str] = []


class GroupNegotiationSession(BaseModel):
    """Group negotiation with multiple participants."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    product_id: str
    seller_id: str
    buyer_ids: List[str]
    group_offer: Offer
    individual_allocations: Dict[str, Dict[str, float]]  # buyer_id -> {quantity, amount}
    group_status: NegotiationStatus
    coordination_method: str  # "equal_split", "proportional", "custom"
    group_discount_percentage: Optional[float] = None
    minimum_group_size: int
    current_group_size: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}