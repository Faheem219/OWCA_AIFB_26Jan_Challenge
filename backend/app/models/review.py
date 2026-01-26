"""
Rating and review models for multilingual vendor reviews.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from bson import ObjectId

from app.models.common import PyObjectId


class ReviewStatus(str, Enum):
    """Review status enumeration."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class ModerationAction(str, Enum):
    """Moderation action enumeration."""
    APPROVE = "approve"
    REJECT = "reject"
    FLAG = "flag"
    REMOVE = "remove"


class ReviewCategory(str, Enum):
    """Review category enumeration."""
    PRODUCT_QUALITY = "product_quality"
    DELIVERY_TIME = "delivery_time"
    COMMUNICATION = "communication"
    PRICING = "pricing"
    OVERALL_EXPERIENCE = "overall_experience"


class Rating(BaseModel):
    """Individual rating for different aspects."""
    category: ReviewCategory
    score: float = Field(..., ge=1.0, le=5.0)  # 1-5 star rating
    
    @field_validator("score")
    @classmethod
    def validate_score(cls, v):
        """Validate rating score is within valid range."""
        if not (1.0 <= v <= 5.0):
            raise ValueError("Rating score must be between 1.0 and 5.0")
        return round(v, 1)  # Round to 1 decimal place


class ReviewTranslation(BaseModel):
    """Translation of review content."""
    language: str
    title: Optional[str] = None
    content: str
    translated_at: datetime = Field(default_factory=datetime.utcnow)
    translation_provider: str = "aws_translate"
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class ReviewBase(BaseModel):
    """Base review model."""
    vendor_id: str
    transaction_id: Optional[str] = None
    product_id: Optional[str] = None
    
    # Rating information
    overall_rating: float = Field(..., ge=1.0, le=5.0)
    detailed_ratings: List[Rating] = []
    
    # Review content
    title: Optional[str] = None
    content: str
    original_language: str = "en"
    
    # Metadata
    is_verified_purchase: bool = False
    is_anonymous: bool = False
    
    @field_validator("overall_rating")
    @classmethod
    def validate_overall_rating(cls, v):
        """Validate overall rating score."""
        if not (1.0 <= v <= 5.0):
            raise ValueError("Overall rating must be between 1.0 and 5.0")
        return round(v, 1)


class ReviewCreate(ReviewBase):
    """Review creation model."""
    pass


class ReviewUpdate(BaseModel):
    """Review update model."""
    title: Optional[str] = None
    content: Optional[str] = None
    overall_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    detailed_ratings: Optional[List[Rating]] = None
    is_anonymous: Optional[bool] = None


class Review(ReviewBase):
    """Review model with database fields."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    buyer_id: str  # Added here since it comes from the authenticated user
    
    # Translations
    translations: Dict[str, ReviewTranslation] = {}
    
    # Moderation
    status: ReviewStatus = ReviewStatus.PENDING
    moderation_notes: Optional[str] = None
    moderated_by: Optional[str] = None  # Admin user ID
    moderated_at: Optional[datetime] = None
    
    # Engagement metrics
    helpful_votes: int = 0
    total_votes: int = 0
    reported_count: int = 0
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ReviewResponse(BaseModel):
    """Review response model for API."""
    id: str
    vendor_id: str
    buyer_id: str
    buyer_name: Optional[str] = None  # Will be populated from user data
    transaction_id: Optional[str] = None
    product_id: Optional[str] = None
    
    overall_rating: float
    detailed_ratings: List[Rating] = []
    
    title: Optional[str] = None
    content: str
    original_language: str
    
    is_verified_purchase: bool
    is_anonymous: bool
    
    status: ReviewStatus
    helpful_votes: int
    total_votes: int
    
    created_at: datetime
    updated_at: datetime


class ReviewWithTranslations(ReviewResponse):
    """Review response with translations."""
    translations: Dict[str, ReviewTranslation] = {}
    available_languages: List[str] = []


class ReviewSummary(BaseModel):
    """Review summary for vendor profile."""
    total_reviews: int = 0
    average_rating: float = 0.0
    rating_distribution: Dict[str, int] = {
        "5": 0, "4": 0, "3": 0, "2": 0, "1": 0
    }
    category_ratings: Dict[ReviewCategory, float] = {}
    recent_reviews: List[ReviewResponse] = []


class ReviewModerationRequest(BaseModel):
    """Review moderation request."""
    action: ModerationAction
    notes: Optional[str] = None
    reason: Optional[str] = None


class ReviewModerationResponse(BaseModel):
    """Review moderation response."""
    review_id: str
    action: ModerationAction
    status: ReviewStatus
    moderated_by: str
    moderated_at: datetime
    notes: Optional[str] = None


class ReviewHelpfulnessRequest(BaseModel):
    """Request to mark review as helpful/unhelpful."""
    is_helpful: bool


class ReviewReportRequest(BaseModel):
    """Request to report a review."""
    reason: str
    details: Optional[str] = None


class ReviewFilters(BaseModel):
    """Filters for review queries."""
    vendor_id: Optional[str] = None
    buyer_id: Optional[str] = None
    min_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    max_rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    status: Optional[ReviewStatus] = None
    is_verified_purchase: Optional[bool] = None
    language: Optional[str] = None
    category: Optional[ReviewCategory] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    # Pagination
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    
    # Sorting
    sort_by: str = Field(default="created_at")  # created_at, rating, helpful_votes
    sort_order: str = Field(default="desc")  # asc, desc


class ReviewStats(BaseModel):
    """Review statistics."""
    total_reviews: int = 0
    approved_reviews: int = 0
    pending_reviews: int = 0
    flagged_reviews: int = 0
    average_rating: float = 0.0
    reviews_by_language: Dict[str, int] = {}
    reviews_by_category: Dict[str, int] = {}
    monthly_review_count: Dict[str, int] = {}  # YYYY-MM format
    top_rated_vendors: List[Dict[str, Any]] = []
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BulkReviewOperation(BaseModel):
    """Bulk review operation request."""
    review_ids: List[str]
    action: ModerationAction
    notes: Optional[str] = None


class ReviewAnalytics(BaseModel):
    """Review analytics for vendor insights."""
    vendor_id: str
    total_reviews: int
    average_rating: float
    rating_trend: List[Dict[str, Any]]  # Monthly rating trends
    category_breakdown: Dict[ReviewCategory, Dict[str, Any]]
    language_distribution: Dict[str, int]
    sentiment_analysis: Dict[str, float]  # positive, negative, neutral percentages
    common_keywords: List[Dict[str, Any]]  # keyword frequency analysis
    competitor_comparison: Optional[Dict[str, Any]] = None
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class ReviewNotification(BaseModel):
    """Review notification model."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    user_id: str
    review_id: str
    notification_type: str  # new_review, review_approved, review_flagged, etc.
    title: str
    message: str
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}