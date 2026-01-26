"""
Data models for the Multilingual Mandi Marketplace Platform.

This package contains all Pydantic models used for data validation,
serialization, and API request/response schemas.
"""

from .user import (
    UserProfile,
    VendorProfile,
    BuyerProfile,
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserPreferences,
    LocationData,
    Address,
    VerificationStatus,
    BusinessType,
    UserRole,
    SupportedLanguage,
)

from .auth import (
    AuthCredentials,
    AuthResult,
    TokenData,
    LoginRequest,
    RegisterRequest,
    RefreshTokenRequest,
    PasswordResetRequest,
    VerificationData,
    OAuthCredentials,
    AadhaarCredentials,
)

from .product import (
    Product,
    MultilingualText,
    ImageReference,
    LocationData as ProductLocationData,
    PriceInfo,
    AvailabilityInfo,
    ProductMetadata,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductSearchQuery,
    ProductSearchResponse,
    ImageUploadRequest,
    ImageUploadResponse,
    ProductStatus,
    QualityGrade,
    MeasurementUnit,
)

from .market_data import (
    MarketPrice,
    PriceHistory,
    DataValidationResult,
    MarketDataCache,
    MarketPriceRequest,
    MarketPriceResponse,
    PriceHistoryRequest,
    PriceHistoryResponse,
    DataSyncStatus,
    AgmarknetApiResponse,
    DataSource,
    DataQuality,
    PriceUnit,
)

__all__ = [
    # User models
    "UserProfile",
    "VendorProfile", 
    "BuyerProfile",
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserResponse",
    "UserPreferences",
    "LocationData",
    "Address",
    "VerificationStatus",
    "BusinessType",
    "UserRole",
    "SupportedLanguage",
    
    # Auth models
    "AuthCredentials",
    "AuthResult",
    "TokenData",
    "LoginRequest",
    "RegisterRequest",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "VerificationData",
    "OAuthCredentials",
    "AadhaarCredentials",
    
    # Product models
    "Product",
    "MultilingualText",
    "ImageReference",
    "ProductLocationData",
    "PriceInfo",
    "AvailabilityInfo",
    "ProductMetadata",
    "ProductCreateRequest",
    "ProductUpdateRequest",
    "ProductResponse",
    "ProductSearchQuery",
    "ProductSearchResponse",
    "ImageUploadRequest",
    "ImageUploadResponse",
    "ProductStatus",
    "QualityGrade",
    "MeasurementUnit",
    
    # Market data models
    "MarketPrice",
    "PriceHistory",
    "DataValidationResult",
    "MarketDataCache",
    "MarketPriceRequest",
    "MarketPriceResponse",
    "PriceHistoryRequest",
    "PriceHistoryResponse",
    "DataSyncStatus",
    "AgmarknetApiResponse",
    "DataSource",
    "DataQuality",
    "PriceUnit",
]