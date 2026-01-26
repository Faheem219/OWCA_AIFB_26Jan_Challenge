"""
User data models for the Multilingual Mandi Marketplace Platform.

This module contains all user-related Pydantic models including profiles,
preferences, and related data structures.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, validator
import phonenumbers
from phonenumbers import NumberParseException


class SupportedLanguage(str, Enum):
    """Supported languages for the platform."""
    HINDI = "hi"
    ENGLISH = "en"
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    MALAYALAM = "ml"
    GUJARATI = "gu"
    PUNJABI = "pa"
    BENGALI = "bn"
    MARATHI = "mr"


class UserRole(str, Enum):
    """User roles in the marketplace."""
    VENDOR = "vendor"
    BUYER = "buyer"
    ADMIN = "admin"


class BusinessType(str, Enum):
    """Types of vendor businesses."""
    INDIVIDUAL = "individual"
    SMALL_BUSINESS = "small_business"
    COOPERATIVE = "cooperative"
    WHOLESALER = "wholesaler"
    RETAILER = "retailer"


class VerificationStatus(str, Enum):
    """User verification status."""
    UNVERIFIED = "unverified"
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ProductCategory(str, Enum):
    """Product categories available in the marketplace."""
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    GRAINS = "grains"
    SPICES = "spices"
    DAIRY = "dairy"


class LocationData(BaseModel):
    """Geographic location data."""
    address: str = Field(..., description="Full address")
    city: str = Field(..., description="City name")
    state: str = Field(..., description="State name")
    pincode: str = Field(..., pattern=r"^\d{6}$", description="6-digit pincode")
    country: str = Field(default="India", description="Country name")
    coordinates: Optional[List[float]] = Field(
        None, 
        description="[longitude, latitude] coordinates",
        min_items=2,
        max_items=2
    )
    
    @validator("coordinates")
    def validate_coordinates(cls, v):
        if v is not None:
            if len(v) != 2:
                raise ValueError("Coordinates must contain exactly 2 values [longitude, latitude]")
            longitude, latitude = v
            if not (-180 <= longitude <= 180):
                raise ValueError("Longitude must be between -180 and 180")
            if not (-90 <= latitude <= 90):
                raise ValueError("Latitude must be between -90 and 90")
        return v


class Address(BaseModel):
    """Address information for delivery."""
    label: str = Field(..., description="Address label (e.g., 'Home', 'Office')")
    location: LocationData
    is_default: bool = Field(default=False, description="Whether this is the default address")


class BudgetRange(BaseModel):
    """Budget range for buyers."""
    min_amount: Decimal = Field(..., ge=0, description="Minimum budget amount")
    max_amount: Decimal = Field(..., ge=0, description="Maximum budget amount")
    currency: str = Field(default="INR", description="Currency code")
    
    @validator("max_amount")
    def validate_max_amount(cls, v, values):
        if "min_amount" in values and v < values["min_amount"]:
            raise ValueError("Maximum amount must be greater than or equal to minimum amount")
        return v


class UserPreferences(BaseModel):
    """User preferences and settings."""
    preferred_languages: List[SupportedLanguage] = Field(
        default=[SupportedLanguage.ENGLISH],
        description="User's preferred languages in order of preference"
    )
    notification_settings: Dict[str, bool] = Field(
        default={
            "email_notifications": True,
            "sms_notifications": True,
            "push_notifications": True,
            "marketing_emails": False,
        },
        description="Notification preferences"
    )
    privacy_settings: Dict[str, bool] = Field(
        default={
            "show_phone": False,
            "show_location": True,
            "allow_direct_contact": True,
        },
        description="Privacy settings"
    )
    accessibility_settings: Dict[str, Any] = Field(
        default={
            "high_contrast": False,
            "large_text": False,
            "voice_navigation": False,
            "screen_reader": False,
        },
        description="Accessibility settings"
    )


class DocumentReference(BaseModel):
    """Reference to uploaded verification documents."""
    document_type: str = Field(..., description="Type of document (e.g., 'aadhaar', 'pan', 'gst')")
    document_url: str = Field(..., description="URL to the uploaded document")
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        description="Verification status of the document"
    )
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class TransactionReference(BaseModel):
    """Reference to a transaction."""
    transaction_id: str = Field(..., description="Transaction ID")
    product_name: str = Field(..., description="Product name")
    amount: Decimal = Field(..., description="Transaction amount")
    date: datetime = Field(..., description="Transaction date")


class UserProfile(BaseModel):
    """Base user profile model."""
    user_id: Optional[str] = Field(None, description="Unique user identifier")
    email: EmailStr = Field(..., description="User's email address")
    phone: Optional[str] = Field(None, description="User's phone number")
    role: UserRole = Field(..., description="User role in the marketplace")
    preferred_languages: List[SupportedLanguage] = Field(
        default=[SupportedLanguage.ENGLISH],
        description="User's preferred languages"
    )
    location: LocationData = Field(..., description="User's location")
    verification_status: VerificationStatus = Field(
        default=VerificationStatus.UNVERIFIED,
        description="User verification status"
    )
    preferences: UserPreferences = Field(
        default_factory=UserPreferences,
        description="User preferences and settings"
    )
    is_active: bool = Field(default=True, description="Whether the user account is active")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    @validator("phone")
    def validate_phone(cls, v):
        if v is not None:
            try:
                # Parse phone number assuming Indian numbers
                parsed = phonenumbers.parse(v, "IN")
                if not phonenumbers.is_valid_number(parsed):
                    raise ValueError("Invalid phone number")
                # Return in international format
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            except NumberParseException:
                raise ValueError("Invalid phone number format")
        return v
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class VendorProfile(UserProfile):
    """Vendor-specific profile model."""
    business_name: str = Field(..., description="Business name")
    business_type: BusinessType = Field(..., description="Type of business")
    product_categories: List[ProductCategory] = Field(
        ..., 
        description="Categories of products the vendor sells"
    )
    market_location: str = Field(..., description="Primary market location")
    verification_documents: List[DocumentReference] = Field(
        default=[],
        description="Uploaded verification documents"
    )
    rating: float = Field(default=0.0, ge=0, le=5, description="Vendor rating (0-5)")
    total_transactions: int = Field(default=0, ge=0, description="Total completed transactions")
    total_revenue: Decimal = Field(default=Decimal("0"), ge=0, description="Total revenue earned")
    
    # Override role to ensure it's always VENDOR
    role: UserRole = Field(default=UserRole.VENDOR, description="User role (always vendor)")


class BuyerProfile(UserProfile):
    """Buyer-specific profile model."""
    purchase_history: List[TransactionReference] = Field(
        default=[],
        description="Purchase history references"
    )
    preferred_categories: List[ProductCategory] = Field(
        default=[],
        description="Preferred product categories"
    )
    budget_range: Optional[BudgetRange] = Field(
        None,
        description="Typical budget range for purchases"
    )
    delivery_addresses: List[Address] = Field(
        default=[],
        description="Saved delivery addresses"
    )
    total_purchases: int = Field(default=0, ge=0, description="Total number of purchases")
    total_spent: Decimal = Field(default=Decimal("0"), ge=0, description="Total amount spent")
    
    # Override role to ensure it's always BUYER
    role: UserRole = Field(default=UserRole.BUYER, description="User role (always buyer)")


# Request/Response models
class UserCreateRequest(BaseModel):
    """Request model for creating a new user."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=8, description="User's password")
    phone: Optional[str] = Field(None, description="User's phone number")
    role: UserRole = Field(..., description="User role")
    preferred_languages: List[SupportedLanguage] = Field(
        default=[SupportedLanguage.ENGLISH],
        description="Preferred languages"
    )
    location: LocationData = Field(..., description="User's location")
    
    # Vendor-specific fields (required if role is VENDOR)
    business_name: Optional[str] = Field(None, description="Business name (required for vendors)")
    business_type: Optional[BusinessType] = Field(None, description="Business type (required for vendors)")
    product_categories: Optional[List[ProductCategory]] = Field(
        None, 
        description="Product categories (required for vendors)"
    )
    market_location: Optional[str] = Field(None, description="Market location (required for vendors)")
    
    # Buyer-specific fields (optional)
    preferred_categories: Optional[List[ProductCategory]] = Field(
        None,
        description="Preferred categories (optional for buyers)"
    )
    budget_range: Optional[BudgetRange] = Field(
        None,
        description="Budget range (optional for buyers)"
    )
    
    @validator("business_name")
    def validate_vendor_fields(cls, v, values):
        if values.get("role") == UserRole.VENDOR and not v:
            raise ValueError("Business name is required for vendors")
        return v
    
    @validator("business_type")
    def validate_business_type(cls, v, values):
        if values.get("role") == UserRole.VENDOR and not v:
            raise ValueError("Business type is required for vendors")
        return v
    
    @validator("product_categories")
    def validate_product_categories(cls, v, values):
        if values.get("role") == UserRole.VENDOR and not v:
            raise ValueError("Product categories are required for vendors")
        return v
    
    @validator("market_location")
    def validate_market_location(cls, v, values):
        if values.get("role") == UserRole.VENDOR and not v:
            raise ValueError("Market location is required for vendors")
        return v


class UserUpdateRequest(BaseModel):
    """Request model for updating user profile."""
    phone: Optional[str] = Field(None, description="Updated phone number")
    preferred_languages: Optional[List[SupportedLanguage]] = Field(
        None,
        description="Updated preferred languages"
    )
    location: Optional[LocationData] = Field(None, description="Updated location")
    preferences: Optional[UserPreferences] = Field(None, description="Updated preferences")
    
    # Vendor-specific updates
    business_name: Optional[str] = Field(None, description="Updated business name")
    business_type: Optional[BusinessType] = Field(None, description="Updated business type")
    product_categories: Optional[List[ProductCategory]] = Field(
        None,
        description="Updated product categories"
    )
    market_location: Optional[str] = Field(None, description="Updated market location")
    
    # Buyer-specific updates
    preferred_categories: Optional[List[ProductCategory]] = Field(
        None,
        description="Updated preferred categories"
    )
    budget_range: Optional[BudgetRange] = Field(None, description="Updated budget range")


class UserResponse(BaseModel):
    """Response model for user data."""
    user_id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    role: UserRole = Field(..., description="User role")
    preferred_languages: List[SupportedLanguage] = Field(..., description="Preferred languages")
    location: LocationData = Field(..., description="Location")
    verification_status: VerificationStatus = Field(..., description="Verification status")
    preferences: UserPreferences = Field(..., description="User preferences")
    is_active: bool = Field(..., description="Account status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    
    # Role-specific fields (populated based on role)
    business_name: Optional[str] = Field(None, description="Business name (vendors only)")
    business_type: Optional[BusinessType] = Field(None, description="Business type (vendors only)")
    product_categories: Optional[List[ProductCategory]] = Field(
        None,
        description="Product categories (vendors only)"
    )
    market_location: Optional[str] = Field(None, description="Market location (vendors only)")
    rating: Optional[float] = Field(None, description="Vendor rating (vendors only)")
    total_transactions: Optional[int] = Field(None, description="Total transactions (vendors only)")
    
    preferred_categories: Optional[List[ProductCategory]] = Field(
        None,
        description="Preferred categories (buyers only)"
    )
    budget_range: Optional[BudgetRange] = Field(None, description="Budget range (buyers only)")
    total_purchases: Optional[int] = Field(None, description="Total purchases (buyers only)")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }