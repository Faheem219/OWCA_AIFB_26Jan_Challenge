"""
Unit tests for vendor verification service.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException, UploadFile
from io import BytesIO

from app.services.vendor_verification_service import VendorVerificationService
from app.models.user import (
    VendorRegistrationRequest, 
    DocumentUploadRequest,
    DocumentType,
    DocumentStatus,
    VerificationStatus,
    VerificationStep,
    AdminVerificationAction,
    Location
)


@pytest.fixture
def mock_db():
    """Mock database."""
    db = MagicMock()
    db.users = AsyncMock()
    db.vendors = AsyncMock()
    return db


@pytest.fixture
def vendor_service(mock_db):
    """Vendor verification service instance."""
    service = VendorVerificationService(mock_db)
    # Mock the collections as AsyncMock
    service.users_collection = AsyncMock()
    service.documents_collection = AsyncMock()
    return service


@pytest.fixture
def sample_registration_data():
    """Sample vendor registration data."""
    return VendorRegistrationRequest(
        business_name="Test Farm",
        business_type="agriculture",
        location=Location(
            address="123 Farm Road",
            city="Pune",
            state="Maharashtra",
            pincode="411001"
        ),
        specializations=["organic", "vegetables"],
        languages_spoken=["hi", "mr", "en"],
        government_id_number="ABCD1234567890",
        government_id_type="aadhaar"
    )


@pytest.fixture
def sample_document_request():
    """Sample document upload request."""
    return DocumentUploadRequest(
        document_type=DocumentType.GOVERNMENT_ID,
        number="ABCD1234567890",
        issuing_authority="UIDAI",
        issue_date=datetime(2020, 1, 1),
        expiry_date=None
    )


class TestVendorVerificationService:
    """Test vendor verification service."""
    
    @pytest.mark.asyncio
    async def test_initiate_vendor_registration_success(
        self, 
        vendor_service, 
        sample_registration_data
    ):
        """Test successful vendor registration initiation."""
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user exists without vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "email": "test@example.com",
            "user_type": "buyer"
        }
        
        # Mock successful update
        vendor_service.users_collection.update_one.return_value = MagicMock(
            modified_count=1
        )
        
        result = await vendor_service.initiate_vendor_registration(
            user_id, 
            sample_registration_data
        )
        
        assert result["vendor_id"] == user_id
        assert result["verification_status"] == VerificationStatus.PENDING
        assert result["next_step"] == VerificationStep.DOCUMENTS_UPLOADED
        assert DocumentType.GOVERNMENT_ID in result["required_documents"]
    
    @pytest.mark.asyncio
    async def test_initiate_vendor_registration_user_not_found(
        self, 
        vendor_service, 
        sample_registration_data
    ):
        """Test vendor registration with non-existent user."""
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user not found
        vendor_service.users_collection.find_one.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.initiate_vendor_registration(
                user_id, 
                sample_registration_data
            )
        
        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_initiate_vendor_registration_already_vendor(
        self, 
        vendor_service, 
        sample_registration_data
    ):
        """Test vendor registration when user already has vendor profile."""
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user with existing vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "email": "test@example.com",
            "vendor_profile": {"business_name": "Existing Business"}
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.initiate_vendor_registration(
                user_id, 
                sample_registration_data
            )
        
        assert exc_info.value.status_code == 400
        assert "already has a vendor profile" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_request_document_upload_success(
        self, 
        vendor_service, 
        sample_document_request
    ):
        """Test successful document upload request."""
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user with vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "vendor_profile": {"business_name": "Test Farm"}
        }
        
        # Mock successful document insertion
        vendor_service.documents_collection.insert_one.return_value = MagicMock()
        
        result = await vendor_service.request_document_upload(
            user_id, 
            sample_document_request
        )
        
        assert result.document_id  # Just check that document_id exists
        assert result.upload_url.startswith("/api/v1/vendor/upload-document/")
        assert result.max_file_size == 10 * 1024 * 1024  # 10MB
    
    @pytest.mark.asyncio
    async def test_request_document_upload_no_vendor_profile(
        self, 
        vendor_service, 
        sample_document_request
    ):
        """Test document upload request without vendor profile."""
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user without vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "email": "test@example.com"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.request_document_upload(
                user_id, 
                sample_document_request
            )
        
        assert exc_info.value.status_code == 404
        assert "Vendor profile not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_document_success(self, vendor_service):
        """Test successful document upload."""
        user_id = "507f1f77bcf86cd799439011"
        document_id = "507f1f77bcf86cd799439012"
        
        # Mock document record
        vendor_service.documents_collection.find_one.return_value = {
            "_id": document_id,
            "user_id": user_id,
            "document": {"type": DocumentType.GOVERNMENT_ID}
        }
        
        # Mock successful update
        vendor_service.documents_collection.update_one.return_value = MagicMock()
        vendor_service.users_collection.update_one.return_value = MagicMock()
        
        # Create mock file
        file_content = b"fake image content"
        mock_file = MagicMock(spec=UploadFile)
        mock_file.filename = "test_id.jpg"
        mock_file.content_type = "image/jpeg"
        mock_file.size = len(file_content)
        mock_file.read = AsyncMock(return_value=file_content)
        
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.write = MagicMock()
            
            result = await vendor_service.upload_document(
                user_id, 
                document_id, 
                mock_file
            )
        
        assert result["document_id"] == document_id
        assert result["status"] == DocumentStatus.UNDER_REVIEW
        assert "uploaded successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_upload_document_file_too_large(self, vendor_service):
        """Test document upload with file too large."""
        user_id = "507f1f77bcf86cd799439011"
        document_id = "507f1f77bcf86cd799439012"
        
        # Mock document record
        vendor_service.documents_collection.find_one.return_value = {
            "_id": document_id,
            "user_id": user_id
        }
        
        # Create mock file that's too large
        mock_file = MagicMock(spec=UploadFile)
        mock_file.size = 15 * 1024 * 1024  # 15MB (exceeds 10MB limit)
        mock_file.content_type = "image/jpeg"
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.upload_document(
                user_id, 
                document_id, 
                mock_file
            )
        
        assert exc_info.value.status_code == 413
        assert "File size exceeds" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_upload_document_invalid_file_type(self, vendor_service):
        """Test document upload with invalid file type."""
        user_id = "507f1f77bcf86cd799439011"
        document_id = "507f1f77bcf86cd799439012"
        
        # Mock document record
        vendor_service.documents_collection.find_one.return_value = {
            "_id": document_id,
            "user_id": user_id
        }
        
        # Create mock file with invalid type
        mock_file = MagicMock(spec=UploadFile)
        mock_file.size = 1024  # 1KB
        mock_file.content_type = "text/plain"  # Invalid type
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.upload_document(
                user_id, 
                document_id, 
                mock_file
            )
        
        assert exc_info.value.status_code == 400
        assert "File type" in str(exc_info.value.detail)
        assert "not allowed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_verify_government_id_success(self, vendor_service):
        """Test successful government ID verification."""
        user_id = "507f1f77bcf86cd799439011"
        document_id = "507f1f77bcf86cd799439012"
        
        # Mock document record
        vendor_service.documents_collection.find_one.return_value = {
            "_id": document_id,
            "user_id": user_id,
            "document": {
                "type": DocumentType.GOVERNMENT_ID,
                "number": "ABCD1234567890"
            }
        }
        
        # Mock successful updates
        vendor_service.documents_collection.update_one.return_value = MagicMock()
        vendor_service.users_collection.update_one.return_value = MagicMock()
        
        result = await vendor_service.verify_government_id(user_id, document_id)
        
        assert result["verified"] is True
        assert "verified successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_verification_status_success(self, vendor_service):
        """Test getting verification status."""
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user with vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "vendor_profile": {
                "verification_status": VerificationStatus.PENDING,
                "verification_workflow": {
                    "current_step": VerificationStep.DOCUMENTS_UPLOADED,
                    "completed_steps": [],
                    "required_documents": [DocumentType.GOVERNMENT_ID]
                },
                "government_id_verified": False,
                "business_license_verified": False
            }
        }
        
        # Mock documents - need to mock the find method to return an async cursor
        documents_data = [
            {
                "_id": "doc1",
                "document": {
                    "type": DocumentType.GOVERNMENT_ID,
                    "status": DocumentStatus.PENDING
                },
                "uploaded_at": datetime.utcnow()
            }
        ]
        
        # Create a proper async mock for the cursor
        mock_cursor = AsyncMock()
        mock_cursor.to_list = AsyncMock(return_value=documents_data)
        vendor_service.documents_collection.find = MagicMock(return_value=mock_cursor)
        
        result = await vendor_service.get_verification_status(user_id)
        
        assert result["verification_status"] == VerificationStatus.PENDING
        assert result["current_step"] == VerificationStep.DOCUMENTS_UPLOADED
        assert len(result["documents"]) == 1
        assert result["government_id_verified"] is False
    
    @pytest.mark.asyncio
    async def test_admin_review_vendor_approve(self, vendor_service):
        """Test admin approval of vendor."""
        user_id = "507f1f77bcf86cd799439011"
        admin_user_id = "507f1f77bcf86cd799439013"
        
        # Mock user with vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "vendor_profile": {"business_name": "Test Farm"}
        }
        
        # Mock successful update
        vendor_service.users_collection.update_one.return_value = MagicMock()
        
        action = AdminVerificationAction(
            action="approve",
            notes="All documents verified"
        )
        
        result = await vendor_service.admin_review_vendor(
            user_id, 
            action, 
            admin_user_id
        )
        
        assert result["status"] == "approved"
        assert "approved successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_admin_review_vendor_reject(self, vendor_service):
        """Test admin rejection of vendor."""
        user_id = "507f1f77bcf86cd799439011"
        admin_user_id = "507f1f77bcf86cd799439013"
        
        # Mock user with vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "vendor_profile": {"business_name": "Test Farm"}
        }
        
        # Mock successful update
        vendor_service.users_collection.update_one.return_value = MagicMock()
        
        action = AdminVerificationAction(
            action="reject",
            notes="Invalid documents"
        )
        
        result = await vendor_service.admin_review_vendor(
            user_id, 
            action, 
            admin_user_id
        )
        
        assert result["status"] == "rejected"
        assert "rejected" in result["message"]
    
    def test_get_required_documents_agriculture(self, vendor_service):
        """Test getting required documents for agriculture business."""
        required_docs = VendorVerificationService._get_required_documents("agriculture")
        
        assert DocumentType.GOVERNMENT_ID in required_docs
        assert DocumentType.ADDRESS_PROOF in required_docs
        # Agriculture doesn't require business license by default
        assert len(required_docs) >= 2
    
    def test_get_required_documents_retail(self, vendor_service):
        """Test getting required documents for retail business."""
        required_docs = VendorVerificationService._get_required_documents("retail")
        
        assert DocumentType.GOVERNMENT_ID in required_docs
        assert DocumentType.ADDRESS_PROOF in required_docs
        assert DocumentType.BUSINESS_LICENSE in required_docs
        assert DocumentType.TAX_CERTIFICATE in required_docs
    
    def test_get_required_documents_organic(self, vendor_service):
        """Test getting required documents for organic business."""
        required_docs = VendorVerificationService._get_required_documents("organic")
        
        assert DocumentType.GOVERNMENT_ID in required_docs
        assert DocumentType.ADDRESS_PROOF in required_docs
        assert DocumentType.ORGANIC_CERTIFICATION in required_docs
    
    @pytest.mark.asyncio
    async def test_validate_government_id_valid(self, vendor_service):
        """Test government ID validation with valid ID."""
        document = {
            "type": DocumentType.GOVERNMENT_ID,
            "number": "ABCD1234567890"  # Valid length
        }
        
        is_valid = await vendor_service._validate_government_id(document)
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_government_id_invalid(self, vendor_service):
        """Test government ID validation with invalid ID."""
        document = {
            "type": DocumentType.GOVERNMENT_ID,
            "number": "123"  # Too short
        }
        
        is_valid = await vendor_service._validate_government_id(document)
        assert is_valid is False


class TestVendorVerificationEdgeCases:
    """Test edge cases for vendor verification."""
    
    @pytest.mark.asyncio
    async def test_upload_document_document_not_found(self, vendor_service):
        """Test document upload when document record not found."""
        user_id = "507f1f77bcf86cd799439011"
        document_id = "507f1f77bcf86cd799439012"
        
        # Mock document not found
        vendor_service.documents_collection.find_one.return_value = None
        
        mock_file = MagicMock(spec=UploadFile)
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.upload_document(user_id, document_id, mock_file)
        
        assert exc_info.value.status_code == 404
        assert "Document not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_verify_government_id_document_not_found(self, vendor_service):
        """Test government ID verification when document not found."""
        user_id = "507f1f77bcf86cd799439011"
        document_id = "507f1f77bcf86cd799439012"
        
        # Mock document not found
        vendor_service.documents_collection.find_one.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.verify_government_id(user_id, document_id)
        
        assert exc_info.value.status_code == 404
        assert "Document not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_verification_status_no_vendor_profile(self, vendor_service):
        """Test getting verification status without vendor profile."""
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user without vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "email": "test@example.com"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.get_verification_status(user_id)
        
        assert exc_info.value.status_code == 404
        assert "Vendor profile not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_admin_review_vendor_not_found(self, vendor_service):
        """Test admin review when vendor not found."""
        user_id = "507f1f77bcf86cd799439011"
        admin_user_id = "507f1f77bcf86cd799439013"
        
        # Mock user not found
        vendor_service.users_collection.find_one.return_value = None
        
        action = AdminVerificationAction(action="approve")
        
        with pytest.raises(HTTPException) as exc_info:
            await vendor_service.admin_review_vendor(user_id, action, admin_user_id)
        
        assert exc_info.value.status_code == 404
        assert "Vendor profile not found" in str(exc_info.value.detail)