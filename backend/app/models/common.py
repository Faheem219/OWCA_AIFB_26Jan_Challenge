"""
Common models and enums used across the application.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: Dict[str, Any]) -> Dict[str, Any]:
        field_schema.update(type="string")
        return field_schema


class QualityGrade(str, Enum):
    """Product quality grades."""
    PREMIUM = "premium"
    STANDARD = "standard"
    BELOW_STANDARD = "below_standard"


class FreshnessLevel(str, Enum):
    """Freshness levels for perishable goods."""
    VERY_FRESH = "very_fresh"
    FRESH = "fresh"
    MODERATE = "moderate"
    POOR = "poor"


class MessageType(str, Enum):
    """Message types in conversations."""
    TEXT = "text"
    VOICE = "voice"
    IMAGE = "image"
    OFFER = "offer"
    SYSTEM = "system"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class DeliveryStatus(str, Enum):
    """Delivery status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class TrendDirection(str, Enum):
    """Price trend direction."""
    RISING = "rising"
    FALLING = "falling"
    STABLE = "stable"
    VOLATILE = "volatile"


class TimePeriod(str, Enum):
    """Time period for analytics."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class NotificationType(str, Enum):
    """Notification types."""
    PRICE_ALERT = "price_alert"
    MESSAGE = "message"
    TRANSACTION = "transaction"
    SYSTEM = "system"
    MARKET_UPDATE = "market_update"


class APIResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    
    @property
    def skip(self) -> int:
        return (self.page - 1) * self.size


class PaginatedResponse(BaseModel):
    """Paginated response model."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    
    @classmethod
    def create(cls, items: List[Any], total: int, page: int, size: int):
        """Create paginated response."""
        pages = (total + size - 1) // size  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )


class LanguageDetection(BaseModel):
    """Language detection result."""
    language: str
    confidence: float
    alternatives: Optional[List[Dict[str, float]]] = None


class TranslationResult(BaseModel):
    """Translation result model."""
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    confidence: float
    cached: bool = False


class AudioResponse(BaseModel):
    """Audio response for text-to-speech."""
    audio_url: str
    duration_seconds: float
    format: str = "mp3"


class SpeechRecognitionResult(BaseModel):
    """Speech recognition result."""
    text: str
    confidence: float
    language: str
    alternatives: Optional[List[str]] = None


class MarketContext(BaseModel):
    """Market context for negotiations."""
    commodity: str
    location: str
    season: str
    weather_conditions: Optional[str] = None
    festival_period: Optional[str] = None
    supply_demand_ratio: Optional[float] = None


class PriceRecommendation(BaseModel):
    """Price recommendation from negotiation assistant."""
    recommended_price: float
    price_range_min: float
    price_range_max: float
    confidence: float
    reasoning: str
    factors_considered: List[str]


class CounterOfferSuggestion(BaseModel):
    """Counter offer suggestion."""
    suggested_price: float
    negotiation_strategy: str
    cultural_considerations: Optional[str] = None
    bulk_discount_applicable: bool = False
    seasonal_factors: Optional[str] = None


class CulturalNegotiationTips(BaseModel):
    """Cultural negotiation guidance."""
    buyer_region: str
    seller_region: str
    greeting_style: str
    negotiation_approach: str
    cultural_sensitivities: List[str]
    recommended_phrases: Dict[str, str]  # language -> phrase


class HealthCheck(BaseModel):
    """Health check response."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    services: Dict[str, str]  # service_name -> status