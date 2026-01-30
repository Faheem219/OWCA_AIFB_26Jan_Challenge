"""
Product data models for the Multilingual Mandi Marketplace Platform.

This module contains all product-related Pydantic models including products,
multilingual text, and related data structures.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from bson import ObjectId

from .user import SupportedLanguage, ProductCategory


class ProductStatus(str, Enum):
    """Product status in the marketplace."""
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    SUSPENDED = "suspended"
    DRAFT = "draft"


class QualityGrade(str, Enum):
    """Quality grades for products."""
    PREMIUM = "premium"
    GRADE_A = "grade_a"
    GRADE_B = "grade_b"
    STANDARD = "standard"
    ORGANIC = "organic"


class MeasurementUnit(str, Enum):
    """Measurement units for products."""
    KG = "kg"
    GRAM = "gram"
    QUINTAL = "quintal"
    TON = "ton"
    LITER = "liter"
    PIECE = "piece"
    DOZEN = "dozen"
    BAG = "bag"
    BOX = "box"


class ImageReference(BaseModel):
    """Reference to uploaded product images."""
    image_id: str = Field(..., description="Unique image identifier")
    image_url: str = Field(..., description="URL to the image")
    thumbnail_url: Optional[str] = Field(None, description="URL to thumbnail version")
    alt_text: Optional[str] = Field(None, description="Alternative text for accessibility")
    is_primary: bool = Field(default=False, description="Whether this is the primary image")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    dimensions: Optional[Dict[str, int]] = Field(None, description="Image dimensions (width, height)")


class MultilingualText(BaseModel):
    """Multilingual text with original and translated versions."""
    original_language: SupportedLanguage = Field(..., description="Original language of the text")
    original_text: str = Field(..., description="Original text content")
    translations: Dict[str, str] = Field(
        default_factory=dict,
        description="Translations in different languages (language code as key)"
    )
    auto_translated: bool = Field(default=False, description="Whether translations were auto-generated")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def get_text(self, language: SupportedLanguage) -> str:
        """
        Get text in the specified language, falling back to original if not available.
        
        Args:
            language: Desired language
            
        Returns:
            Text in the specified language or original text
        """
        if language == self.original_language:
            return self.original_text
        return self.translations.get(language.value, self.original_text)
    
    def add_translation(self, language: SupportedLanguage, text: str, auto_translated: bool = False) -> None:
        """
        Add or update a translation.
        
        Args:
            language: Target language
            text: Translated text
            auto_translated: Whether this is an auto-generated translation
        """
        self.translations[language.value] = text
        if auto_translated:
            self.auto_translated = True
        self.last_updated = datetime.utcnow()


class LocationData(BaseModel):
    """Geographic location data for products."""
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
    market_name: Optional[str] = Field(None, description="Name of the local market/mandi")
    
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


class PriceInfo(BaseModel):
    """Price information for products."""
    base_price: Decimal = Field(..., ge=0, description="Base price per unit")
    currency: str = Field(default="INR", description="Currency code")
    negotiable: bool = Field(default=True, description="Whether price is negotiable")
    bulk_discount: Optional[Dict[str, Any]] = Field(None, description="Bulk discount information")
    seasonal_pricing: Optional[Dict[str, Any]] = Field(None, description="Seasonal pricing adjustments")
    
    @validator("base_price")
    def validate_base_price(cls, v):
        if v <= 0:
            raise ValueError("Base price must be greater than 0")
        return v


class AvailabilityInfo(BaseModel):
    """Product availability information."""
    quantity_available: int = Field(..., ge=0, description="Available quantity")
    unit: MeasurementUnit = Field(..., description="Unit of measurement")
    minimum_order: int = Field(default=1, ge=1, description="Minimum order quantity")
    maximum_order: Optional[int] = Field(None, description="Maximum order quantity")
    available_from: Optional[datetime] = Field(None, description="Available from date")
    available_until: Optional[datetime] = Field(None, description="Available until date")
    restocking_date: Optional[date] = Field(None, description="Expected restocking date")
    
    @validator("maximum_order")
    def validate_maximum_order(cls, v, values):
        if v is not None and "minimum_order" in values and v < values["minimum_order"]:
            raise ValueError("Maximum order must be greater than or equal to minimum order")
        return v


class ProductMetadata(BaseModel):
    """Additional product metadata."""
    harvest_date: Optional[date] = Field(None, description="Harvest date for fresh produce")
    expiry_date: Optional[date] = Field(None, description="Product expiry date")
    storage_conditions: Optional[str] = Field(None, description="Required storage conditions")
    certifications: List[str] = Field(default=[], description="Product certifications (organic, etc.)")
    origin: Optional[str] = Field(None, description="Product origin/source")
    variety: Optional[str] = Field(None, description="Product variety/type")
    processing_method: Optional[str] = Field(None, description="Processing method if applicable")


class Product(BaseModel):
    """Main product model."""
    product_id: Optional[str] = Field(None, description="Unique product identifier")
    vendor_id: str = Field(..., description="Vendor who owns this product")
    
    # Basic product information
    name: MultilingualText = Field(..., description="Product name in multiple languages")
    description: MultilingualText = Field(..., description="Product description in multiple languages")
    category: ProductCategory = Field(..., description="Primary product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    tags: List[str] = Field(default=[], description="Product tags for search and categorization")
    
    # Images and media
    images: List[ImageReference] = Field(default=[], description="Product images")
    
    # Pricing and availability
    price_info: PriceInfo = Field(..., description="Pricing information")
    availability: AvailabilityInfo = Field(..., description="Availability information")
    
    # Location and logistics
    location: LocationData = Field(..., description="Product location")
    
    # Quality and metadata
    quality_grade: QualityGrade = Field(..., description="Quality grade")
    metadata: ProductMetadata = Field(default_factory=ProductMetadata, description="Additional metadata")
    
    # Status and timestamps
    status: ProductStatus = Field(default=ProductStatus.ACTIVE, description="Product status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    views_count: int = Field(default=0, description="Number of views")
    favorites_count: int = Field(default=0, description="Number of times favorited")
    
    # Search and discovery
    search_keywords: List[str] = Field(default=[], description="Keywords for search optimization")
    featured: bool = Field(default=False, description="Whether product is featured")
    
    @validator("images")
    def validate_images(cls, v):
        if not v:
            raise ValueError("At least one product image is required")
        
        # Check that only one image is marked as primary
        primary_count = sum(1 for img in v if img.is_primary)
        if primary_count == 0:
            # If no primary image is set, make the first one primary
            v[0].is_primary = True
        elif primary_count > 1:
            raise ValueError("Only one image can be marked as primary")
        
        return v
    
    @validator("tags")
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError("Cannot have more than 10 tags")
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    @validator("search_keywords")
    def validate_search_keywords(cls, v):
        if len(v) > 20:
            raise ValueError("Cannot have more than 20 search keywords")
        return [keyword.lower().strip() for keyword in v if keyword.strip()]
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


# Request/Response models
class ProductCreateRequest(BaseModel):
    """Request model for creating a new product."""
    # Basic information
    name_text: str = Field(..., min_length=2, max_length=200, description="Product name")
    name_language: SupportedLanguage = Field(..., description="Language of the product name")
    description_text: str = Field(..., min_length=10, max_length=2000, description="Product description")
    description_language: SupportedLanguage = Field(..., description="Language of the description")
    
    category: ProductCategory = Field(..., description="Product category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Product subcategory")
    tags: List[str] = Field(default=[], description="Product tags")
    
    # Pricing and availability
    base_price: Decimal = Field(..., ge=0, description="Base price per unit")
    negotiable: bool = Field(default=True, description="Whether price is negotiable")
    quantity_available: int = Field(..., ge=1, description="Available quantity")
    unit: MeasurementUnit = Field(..., description="Unit of measurement")
    minimum_order: int = Field(default=1, ge=1, description="Minimum order quantity")
    maximum_order: Optional[int] = Field(None, description="Maximum order quantity")
    
    # Quality and metadata
    quality_grade: QualityGrade = Field(..., description="Quality grade")
    harvest_date: Optional[date] = Field(None, description="Harvest date")
    expiry_date: Optional[date] = Field(None, description="Expiry date")
    certifications: List[str] = Field(default=[], description="Certifications")
    origin: Optional[str] = Field(None, description="Product origin")
    variety: Optional[str] = Field(None, description="Product variety")
    
    # Location (will be populated from vendor profile if not provided)
    location_address: Optional[str] = Field(None, description="Specific address for this product")
    market_name: Optional[str] = Field(None, description="Market name")
    
    # Images (will be handled separately through image upload endpoints)
    image_urls: List[str] = Field(default=[], description="URLs of uploaded images")
    
    @validator("maximum_order")
    def validate_maximum_order(cls, v, values):
        if v is not None and "minimum_order" in values and v < values["minimum_order"]:
            raise ValueError("Maximum order must be greater than or equal to minimum order")
        return v
    
    @validator("expiry_date")
    def validate_expiry_date(cls, v, values):
        if v is not None and "harvest_date" in values and values["harvest_date"] and v < values["harvest_date"]:
            raise ValueError("Expiry date cannot be before harvest date")
        return v


class ProductUpdateRequest(BaseModel):
    """Request model for updating a product."""
    # Basic information
    name_text: Optional[str] = Field(None, min_length=2, max_length=200, description="Updated product name")
    name_language: Optional[SupportedLanguage] = Field(None, description="Language of the product name")
    description_text: Optional[str] = Field(None, min_length=10, max_length=2000, description="Updated description")
    description_language: Optional[SupportedLanguage] = Field(None, description="Language of the description")
    
    subcategory: Optional[str] = Field(None, max_length=100, description="Updated subcategory")
    tags: Optional[List[str]] = Field(None, description="Updated tags")
    
    # Pricing and availability
    base_price: Optional[Decimal] = Field(None, ge=0, description="Updated base price")
    negotiable: Optional[bool] = Field(None, description="Updated negotiable status")
    quantity_available: Optional[int] = Field(None, ge=0, description="Updated quantity")
    minimum_order: Optional[int] = Field(None, ge=1, description="Updated minimum order")
    maximum_order: Optional[int] = Field(None, description="Updated maximum order")
    
    # Quality and metadata
    quality_grade: Optional[QualityGrade] = Field(None, description="Updated quality grade")
    harvest_date: Optional[date] = Field(None, description="Updated harvest date")
    expiry_date: Optional[date] = Field(None, description="Updated expiry date")
    certifications: Optional[List[str]] = Field(None, description="Updated certifications")
    origin: Optional[str] = Field(None, description="Updated origin")
    variety: Optional[str] = Field(None, description="Updated variety")
    
    # Status
    status: Optional[ProductStatus] = Field(None, description="Updated status")
    
    # Location
    location_address: Optional[str] = Field(None, description="Updated address")
    market_name: Optional[str] = Field(None, description="Updated market name")


class ProductResponse(BaseModel):
    """Response model for product data."""
    product_id: str = Field(..., description="Product ID")
    vendor_id: str = Field(..., description="Vendor ID")
    
    # Basic information
    name: MultilingualText = Field(..., description="Product name")
    description: MultilingualText = Field(..., description="Product description")
    category: ProductCategory = Field(..., description="Product category")
    subcategory: Optional[str] = Field(None, description="Product subcategory")
    tags: List[str] = Field(..., description="Product tags")
    
    # Images
    images: List[ImageReference] = Field(..., description="Product images")
    
    # Pricing and availability
    price_info: PriceInfo = Field(..., description="Pricing information")
    availability: AvailabilityInfo = Field(..., description="Availability information")
    
    # Location
    location: LocationData = Field(..., description="Product location")
    
    # Quality and metadata
    quality_grade: QualityGrade = Field(..., description="Quality grade")
    metadata: ProductMetadata = Field(..., description="Product metadata")
    
    # Status and stats
    status: ProductStatus = Field(..., description="Product status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    views_count: int = Field(..., description="Views count")
    favorites_count: int = Field(..., description="Favorites count")
    featured: bool = Field(..., description="Featured status")
    
    # Vendor information (basic)
    vendor_name: Optional[str] = Field(None, description="Vendor business name")
    vendor_rating: Optional[float] = Field(None, description="Vendor rating")
    vendor_location: Optional[str] = Field(None, description="Vendor location")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class ProductSearchQuery(BaseModel):
    """Search query parameters for products."""
    query: Optional[str] = Field(None, description="Search text")
    language: SupportedLanguage = Field(default=SupportedLanguage.ENGLISH, description="Search language")
    category: Optional[ProductCategory] = Field(None, description="Filter by category")
    subcategory: Optional[str] = Field(None, description="Filter by subcategory")
    
    # Price filters
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price")
    
    # Location filters
    city: Optional[str] = Field(None, description="Filter by city")
    state: Optional[str] = Field(None, description="Filter by state")
    coordinates: Optional[List[float]] = Field(None, description="Search center coordinates")
    radius_km: Optional[float] = Field(None, ge=0, description="Search radius in kilometers")
    
    # Quality and availability filters
    quality_grades: Optional[List[QualityGrade]] = Field(None, description="Filter by quality grades")
    available_only: bool = Field(default=True, description="Show only available products")
    organic_only: bool = Field(default=False, description="Show only organic products")
    
    # Sorting and pagination
    sort_by: str = Field(default="relevance", description="Sort criteria")
    sort_order: str = Field(default="desc", description="Sort order (asc/desc)")
    limit: int = Field(default=20, ge=1, le=100, description="Results limit")
    skip: int = Field(default=0, ge=0, description="Results to skip")
    
    @validator("max_price")
    def validate_price_range(cls, v, values):
        if v is not None and "min_price" in values and values["min_price"] and v < values["min_price"]:
            raise ValueError("Maximum price must be greater than or equal to minimum price")
        return v
    
    @validator("sort_by")
    def validate_sort_by(cls, v):
        valid_sorts = ["relevance", "price", "date", "rating", "distance", "popularity"]
        if v not in valid_sorts:
            raise ValueError(f"Sort by must be one of: {', '.join(valid_sorts)}")
        return v
    
    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v not in ["asc", "desc"]:
            raise ValueError("Sort order must be 'asc' or 'desc'")
        return v


class ProductSearchResponse(BaseModel):
    """Response model for product search results."""
    products: List[ProductResponse] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of matching products")
    page_info: Dict[str, Any] = Field(..., description="Pagination information")
    search_metadata: Dict[str, Any] = Field(..., description="Search metadata and suggestions")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
            Decimal: lambda v: str(v),
        }


class ImageUploadRequest(BaseModel):
    """Request model for image upload."""
    product_id: str = Field(..., description="Product ID")
    alt_text: Optional[str] = Field(None, description="Alternative text")
    is_primary: bool = Field(default=False, description="Whether this is the primary image")


class ImageUploadResponse(BaseModel):
    """Response model for image upload."""
    image_id: str = Field(..., description="Image ID")
    image_url: str = Field(..., description="Image URL")
    thumbnail_url: str = Field(..., description="Thumbnail URL")
    upload_status: str = Field(..., description="Upload status")
    message: str = Field(..., description="Upload message")