"""
Product catalog models with AI features.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator
from enum import Enum
from bson import ObjectId

from app.models.common import PyObjectId, QualityGrade, FreshnessLevel


class ProductCategory(str, Enum):
    """Product categories."""
    GRAINS = "grains"
    VEGETABLES = "vegetables"
    FRUITS = "fruits"
    SPICES = "spices"
    PULSES = "pulses"
    DAIRY = "dairy"
    MEAT = "meat"
    SEAFOOD = "seafood"
    PROCESSED_FOOD = "processed_food"
    TEXTILES = "textiles"
    HANDICRAFTS = "handicrafts"
    ELECTRONICS = "electronics"
    MACHINERY = "machinery"
    OTHER = "other"


class ProductSubcategory(str, Enum):
    """Product subcategories."""
    # Grains
    RICE = "rice"
    WHEAT = "wheat"
    BARLEY = "barley"
    CORN = "corn"
    MILLET = "millet"
    
    # Vegetables
    ONION = "onion"
    POTATO = "potato"
    TOMATO = "tomato"
    CABBAGE = "cabbage"
    CAULIFLOWER = "cauliflower"
    CARROT = "carrot"
    SPINACH = "spinach"
    
    # Fruits
    APPLE = "apple"
    BANANA = "banana"
    MANGO = "mango"
    ORANGE = "orange"
    GRAPES = "grapes"
    POMEGRANATE = "pomegranate"
    
    # Spices
    TURMERIC = "turmeric"
    CHILI = "chili"
    CORIANDER = "coriander"
    CUMIN = "cumin"
    CARDAMOM = "cardamom"
    BLACK_PEPPER = "black_pepper"


class Unit(str, Enum):
    """Measurement units."""
    KG = "kg"
    GRAM = "gram"
    QUINTAL = "quintal"
    TON = "ton"
    LITER = "liter"
    PIECE = "piece"
    DOZEN = "dozen"
    BOX = "box"
    BAG = "bag"


class CertificationType(str, Enum):
    """Product certifications."""
    ORGANIC = "organic"
    FAIR_TRADE = "fair_trade"
    ISO_CERTIFIED = "iso_certified"
    FSSAI = "fssai"
    AGMARK = "agmark"
    BIS = "bis"
    EXPORT_QUALITY = "export_quality"


class ProductStatus(str, Enum):
    """Product listing status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    PENDING_APPROVAL = "pending_approval"
    REJECTED = "rejected"


class ImageAnalysisResult(BaseModel):
    """AI image analysis result."""
    detected_category: Optional[ProductCategory] = None
    detected_subcategory: Optional[ProductSubcategory] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    quality_assessment: Optional[QualityGrade] = None
    freshness_level: Optional[FreshnessLevel] = None
    quantity_estimate: Optional[float] = None
    estimated_unit: Optional[Unit] = None
    defects_detected: List[str] = []
    color_analysis: Optional[Dict[str, Any]] = None
    size_analysis: Optional[Dict[str, Any]] = None
    processing_metadata: Dict[str, Any] = {}


class BarcodeInfo(BaseModel):
    """Barcode/QR code information."""
    code: str
    format: str  # "EAN13", "UPC", "QR", etc.
    product_name: Optional[str] = None
    manufacturer: Optional[str] = None
    additional_info: Optional[Dict[str, Any]] = None


class ProductImage(BaseModel):
    """Product image with AI analysis."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    url: str
    thumbnail_url: Optional[str] = None
    is_primary: bool = False
    analysis_result: Optional[ImageAnalysisResult] = None
    barcode_info: Optional[BarcodeInfo] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class ProductSpecification(BaseModel):
    """Product specifications."""
    variety: Optional[str] = None
    grade: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    moisture_content: Optional[float] = None
    purity_percentage: Optional[float] = None
    shelf_life_days: Optional[int] = None
    storage_conditions: Optional[str] = None
    origin_state: Optional[str] = None
    origin_district: Optional[str] = None
    harvest_date: Optional[datetime] = None
    processing_date: Optional[datetime] = None


class PriceInfo(BaseModel):
    """Product pricing information."""
    base_price: float = Field(gt=0)
    unit: Unit
    minimum_order_quantity: float = Field(gt=0)
    bulk_discount_threshold: Optional[float] = None
    bulk_discount_percentage: Optional[float] = None
    negotiable: bool = True
    price_valid_until: Optional[datetime] = None
    seasonal_pricing: Optional[Dict[str, float]] = None


class InventoryInfo(BaseModel):
    """Product inventory information."""
    available_quantity: float = Field(ge=0)
    unit: Unit
    reserved_quantity: float = Field(ge=0, default=0)
    restock_date: Optional[datetime] = None
    low_stock_threshold: Optional[float] = None
    auto_restock: bool = False


class Product(BaseModel):
    """Product model with AI features."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    vendor_id: str
    name: str
    category: ProductCategory
    subcategory: Optional[ProductSubcategory] = None
    description: Dict[str, str] = {}  # Multi-language descriptions
    images: List[ProductImage] = []
    specifications: Optional[ProductSpecification] = None
    price_info: PriceInfo
    inventory_info: InventoryInfo
    certifications: List[CertificationType] = []
    quality_grade: Optional[QualityGrade] = None
    freshness_level: Optional[FreshnessLevel] = None
    ai_generated_tags: List[str] = []
    manual_tags: List[str] = []
    status: ProductStatus = ProductStatus.PENDING_APPROVAL
    featured: bool = False
    views_count: int = 0
    inquiries_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ProductCreate(BaseModel):
    """Product creation model."""
    name: str
    category: ProductCategory
    subcategory: Optional[ProductSubcategory] = None
    description: Dict[str, str] = {}
    specifications: Optional[ProductSpecification] = None
    price_info: PriceInfo
    inventory_info: InventoryInfo
    certifications: List[CertificationType] = []
    manual_tags: List[str] = []


class ProductUpdate(BaseModel):
    """Product update model."""
    name: Optional[str] = None
    category: Optional[ProductCategory] = None
    subcategory: Optional[ProductSubcategory] = None
    description: Optional[Dict[str, str]] = None
    specifications: Optional[ProductSpecification] = None
    price_info: Optional[PriceInfo] = None
    inventory_info: Optional[InventoryInfo] = None
    certifications: Optional[List[CertificationType]] = None
    manual_tags: Optional[List[str]] = None
    status: Optional[ProductStatus] = None


class ProductSearchFilters(BaseModel):
    """Product search filters."""
    category: Optional[ProductCategory] = None
    subcategory: Optional[ProductSubcategory] = None
    quality_grade: Optional[QualityGrade] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    location_radius_km: Optional[float] = None
    certifications: Optional[List[CertificationType]] = None
    freshness_level: Optional[FreshnessLevel] = None
    available_only: bool = True
    featured_only: bool = False


class ProductSearchResult(BaseModel):
    """Product search result."""
    products: List[Product]
    total_count: int
    filters_applied: ProductSearchFilters
    suggested_filters: Optional[Dict[str, Any]] = None


class ImageUploadRequest(BaseModel):
    """Image upload request."""
    product_id: str
    is_primary: bool = False
    analyze_image: bool = True


class ImageUploadResponse(BaseModel):
    """Image upload response."""
    image_id: str
    upload_url: str
    analysis_requested: bool
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_mime_types: List[str] = ["image/jpeg", "image/png", "image/webp"]


class BulkProductOperation(BaseModel):
    """Bulk product operation."""
    operation: str  # "activate", "deactivate", "delete", "update_price"
    product_ids: List[str]
    parameters: Optional[Dict[str, Any]] = None


class ProductAnalytics(BaseModel):
    """Product analytics."""
    product_id: str
    views_count: int
    inquiries_count: int
    conversion_rate: float
    average_rating: float
    price_competitiveness: float
    search_ranking: int
    performance_score: float
    recommendations: List[str]


class AIProductSuggestion(BaseModel):
    """AI-generated product suggestions."""
    suggested_category: ProductCategory
    suggested_subcategory: Optional[ProductSubcategory] = None
    suggested_price_range: Dict[str, float]  # min, max
    market_demand_score: float
    competition_level: str  # "low", "medium", "high"
    seasonal_factors: List[str]
    reasoning: str