"""
User and authentication models.
"""
from datetime import datetime
from typing import Optional, List, Dict, Union, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
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


class UserType(str, Enum):
    """User type enumeration."""
    VENDOR = "vendor"
    BUYER = "buyer"
    BOTH = "both"


class VerificationStatus(str, Enum):
    """Verification status enumeration."""
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class Location(BaseModel):
    """Location model."""
    address: str
    city: str
    state: str
    pincode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DocumentType(str, Enum):
    """Document type enumeration."""
    GOVERNMENT_ID = "government_id"
    BUSINESS_LICENSE = "business_license"
    TAX_CERTIFICATE = "tax_certificate"
    TRADE_LICENSE = "trade_license"
    ORGANIC_CERTIFICATION = "organic_certification"
    QUALITY_CERTIFICATION = "quality_certification"
    BANK_STATEMENT = "bank_statement"
    ADDRESS_PROOF = "address_proof"


class DocumentStatus(str, Enum):
    """Document verification status."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Document(BaseModel):
    """Document model for verification."""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    type: DocumentType
    number: str
    issuing_authority: str
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    document_url: str
    thumbnail_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    status: DocumentStatus = DocumentStatus.PENDING
    verification_notes: Optional[str] = None
    verified_by: Optional[str] = None  # Admin user ID
    verified_at: Optional[datetime] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class Credential(BaseModel):
    """Credential model for vendor verification."""
    type: str  # "government_id", "license", "certification"
    number: str
    issuing_authority: str
    expiry_date: Optional[datetime] = None
    document_url: Optional[str] = None
    verified: bool = False


class TransactionStats(BaseModel):
    """Transaction statistics for vendors."""
    total_transactions: int = 0
    completed_transactions: int = 0
    total_revenue: float = 0.0
    average_rating: float = 0.0
    response_time_hours: float = 0.0


class VerificationStep(str, Enum):
    """Verification workflow steps."""
    PROFILE_CREATED = "profile_created"
    DOCUMENTS_UPLOADED = "documents_uploaded"
    GOVERNMENT_ID_VERIFIED = "government_id_verified"
    BUSINESS_LICENSE_VERIFIED = "business_license_verified"
    ADMIN_REVIEW = "admin_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class VerificationWorkflow(BaseModel):
    """Verification workflow tracking."""
    current_step: VerificationStep = VerificationStep.PROFILE_CREATED
    completed_steps: List[VerificationStep] = []
    required_documents: List[DocumentType] = []
    uploaded_documents: List[Document] = []
    rejection_reason: Optional[str] = None
    admin_notes: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class VendorProfile(BaseModel):
    """Vendor profile model."""
    business_name: str
    business_type: str
    specializations: List[str] = []
    location: Location
    credentials: List[Credential] = []
    credibility_score: float = 0.0
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_workflow: VerificationWorkflow = VerificationWorkflow()
    transaction_stats: TransactionStats = TransactionStats()
    languages_spoken: List[str] = []
    business_hours: Optional[Dict[str, str]] = None
    description: Optional[Dict[str, str]] = None  # Multi-language descriptions
    government_id_verified: bool = False
    business_license_verified: bool = False
    tax_registration_verified: bool = False
    bank_account_verified: bool = False


class BuyerProfile(BaseModel):
    """Buyer profile model."""
    organization_name: Optional[str] = None
    buyer_type: str = "individual"  # "individual", "business", "government"
    location: Location
    preferred_categories: List[str] = []
    languages_spoken: List[str] = []
    purchase_history_summary: Optional[Dict] = None


class UserBase(BaseModel):
    """Base user model."""
    email: EmailStr
    phone: str
    preferred_language: str = "en"
    user_type: UserType
    is_active: bool = True
    
    @field_validator("preferred_language")
    @classmethod
    def validate_language(cls, v):
        from app.core.config import settings
        if v not in settings.SUPPORTED_LANGUAGES:
            raise ValueError(f"Language {v} not supported")
        return v


class UserCreate(UserBase):
    """User creation model."""
    password: str
    full_name: str
    vendor_profile: Optional[VendorProfile] = None
    buyer_profile: Optional[BuyerProfile] = None


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    preferred_language: Optional[str] = None
    full_name: Optional[str] = None
    vendor_profile: Optional[VendorProfile] = None
    buyer_profile: Optional[BuyerProfile] = None


class User(UserBase):
    """User model with database fields."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    full_name: str
    hashed_password: str
    vendor_profile: Optional[VendorProfile] = None
    buyer_profile: Optional[BuyerProfile] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UserInDB(User):
    """User model as stored in database."""
    pass


class UserResponse(BaseModel):
    """User response model (without sensitive data)."""
    id: str
    email: EmailStr
    phone: str
    full_name: str
    preferred_language: str
    user_type: UserType
    is_active: bool
    vendor_profile: Optional[VendorProfile] = None
    buyer_profile: Optional[BuyerProfile] = None
    created_at: datetime
    last_active: Optional[datetime] = None


class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class VendorRegistrationRequest(BaseModel):
    """Vendor registration request model."""
    business_name: str
    business_type: str
    location: Location
    specializations: List[str] = []
    languages_spoken: List[str] = []
    business_hours: Optional[Dict[str, str]] = None
    description: Optional[Dict[str, str]] = None
    government_id_number: str
    government_id_type: str  # "aadhaar", "pan", "voter_id", "passport"
    business_license_number: Optional[str] = None
    tax_registration_number: Optional[str] = None


class DocumentUploadRequest(BaseModel):
    """Document upload request model."""
    document_type: DocumentType
    number: str
    issuing_authority: str
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None


class DocumentUploadResponse(BaseModel):
    """Document upload response model."""
    document_id: str
    upload_url: str
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_mime_types: List[str] = ["image/jpeg", "image/png", "application/pdf"]


class VerificationStatusUpdate(BaseModel):
    """Verification status update model."""
    status: VerificationStatus
    notes: Optional[str] = None
    required_documents: Optional[List[DocumentType]] = None


class AdminVerificationAction(BaseModel):
    """Admin verification action model."""
    action: str  # "approve", "reject", "request_documents"
    notes: Optional[str] = None
    required_documents: Optional[List[DocumentType]] = None


class TokenData(BaseModel):
    """Token data model."""
    user_id: Optional[str] = None
    email: Optional[str] = None