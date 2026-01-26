"""
Integration tests for vendor verification API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.main import app
from app.models.user import (
    VendorRegistrationRequest,
    DocumentUploadRequest,
    DocumentType,
    Location
)


@pytest.fixture
def client():
    """Test client."""
    return TestClient(app)


@pytest.fixture
def mock_auth_token():
    """Mock authentication token."""
    return "Bearer test_token"


@pytest.fixture
def sample_vendor_registration():
    """Sample vendor registration data."""
    return {
        "business_name": "Test Farm",
        "business_type": "agriculture",
        "location": {
            "address": "123 Farm Road",
            "city": "Pune",
            "state": "Maharashtra",
            "pincode": "411001"
        },
        "specializations": ["organic", "vegetables"],
        "languages_spoken": ["hi", "mr", "en"],
        "government_id_number": "ABCD1234567890",
        "government_id_type": "aadhaar"
    }


class TestVendorAPIIntegration:
    """Integration tests for vendor API endpoints."""
    
    @patch('app.api.deps.get_current_active_user')
    @patch('app.api.v1.vendor.get_vendor_verification_service')
    def test_register_vendor_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        sample_vendor_registration
    ):
        """Test successful vendor registration."""
        # Mock current user
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_get_user.return_value = mock_user
        
        # Mock verification service
        mock_service = AsyncMock()
        mock_service.initiate_vendor_registration.return_value = {
            "vendor_id": "507f1f77bcf86cd799439011",
            "verification_status": "pending",
            "required_documents": ["government_id", "address_proof"],
            "next_step": "documents_uploaded"
        }
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/vendor/register",
            json=sample_vendor_registration,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "vendor_id" in data["data"]
        assert data["data"]["verification_status"] == "pending"
    
    @patch('app.api.deps.get_current_vendor')
    @patch('app.api.v1.vendor.get_vendor_verification_service')
    def test_request_document_upload_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client
    ):
        """Test successful document upload request."""
        # Mock current user
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_get_user.return_value = mock_user
        
        # Mock verification service
        mock_service = AsyncMock()
        mock_service.request_document_upload.return_value = MagicMock(
            document_id="doc123",
            upload_url="/api/v1/vendor/upload-document/doc123",
            max_file_size=10485760,
            allowed_mime_types=["image/jpeg", "image/png", "application/pdf"]
        )
        mock_get_service.return_value = mock_service
        
        # Request data
        document_request = {
            "document_type": "government_id",
            "number": "ABCD1234567890",
            "issuing_authority": "UIDAI",
            "issue_date": "2020-01-01T00:00:00",
            "expiry_date": None
        }
        
        # Make request
        response = client.post(
            "/api/v1/vendor/request-document-upload",
            json=document_request,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "document_id" in data["data"]
        assert "upload_url" in data["data"]
    
    @patch('app.api.deps.get_current_vendor')
    @patch('app.api.v1.vendor.get_vendor_verification_service')
    def test_get_verification_status_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client
    ):
        """Test getting verification status."""
        # Mock current user
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_get_user.return_value = mock_user
        
        # Mock verification service
        mock_service = AsyncMock()
        mock_service.get_verification_status.return_value = {
            "verification_status": "pending",
            "current_step": "documents_uploaded",
            "completed_steps": [],
            "required_documents": ["government_id"],
            "documents": [],
            "government_id_verified": False,
            "business_license_verified": False
        }
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.get(
            "/api/v1/vendor/verification-status",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["verification_status"] == "pending"
        assert data["data"]["government_id_verified"] is False
    
    @patch('app.api.deps.get_current_vendor')
    def test_get_vendor_profile_success(self, mock_get_user, client):
        """Test getting vendor profile."""
        # Mock current user with vendor profile
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_user.vendor_profile = MagicMock()
        mock_user.vendor_profile.dict.return_value = {
            "business_name": "Test Farm",
            "business_type": "agriculture",
            "verification_status": "pending"
        }
        mock_get_user.return_value = mock_user
        
        # Make request
        response = client.get(
            "/api/v1/vendor/profile",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["business_name"] == "Test Farm"
    
    @patch('app.api.deps.get_current_active_user')
    @patch('app.api.v1.vendor.get_vendor_verification_service')
    def test_admin_review_vendor_success(
        self, 
        mock_get_service, 
        mock_get_user, 
        client
    ):
        """Test admin vendor review."""
        # Mock current user (admin)
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439013"
        mock_get_user.return_value = mock_user
        
        # Mock verification service
        mock_service = AsyncMock()
        mock_service.admin_review_vendor.return_value = {
            "status": "approved",
            "message": "Vendor profile approved successfully"
        }
        mock_get_service.return_value = mock_service
        
        # Request data
        admin_action = {
            "action": "approve",
            "notes": "All documents verified"
        }
        
        # Make request
        response = client.post(
            "/api/v1/vendor/admin/review/507f1f77bcf86cd799439011",
            json=admin_action,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "approved"
    
    def test_get_required_documents_success(self, client):
        """Test getting required documents for business type."""
        # Make request
        response = client.get("/api/v1/vendor/required-documents/retail")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["business_type"] == "retail"
        assert "required_documents" in data["data"]
        assert "government_id" in data["data"]["required_documents"]
    
    @patch('app.api.deps.get_current_active_user')
    @patch('app.api.v1.vendor.get_vendor_verification_service')
    def test_register_vendor_validation_error(
        self, 
        mock_get_service, 
        mock_get_user, 
        client
    ):
        """Test vendor registration with validation error."""
        # Mock current user
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_get_user.return_value = mock_user
        
        # Invalid registration data (missing required fields)
        invalid_data = {
            "business_name": "Test Farm"
            # Missing other required fields
        }
        
        # Make request
        response = client.post(
            "/api/v1/vendor/register",
            json=invalid_data,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.deps.get_current_vendor')
    @patch('app.api.v1.vendor.get_vendor_verification_service')
    def test_upload_document_file_too_large(
        self, 
        mock_get_service, 
        mock_get_user, 
        client
    ):
        """Test document upload with file too large."""
        from fastapi import HTTPException
        
        # Mock current user
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_get_user.return_value = mock_user
        
        # Mock verification service to raise file too large error
        mock_service = AsyncMock()
        mock_service.upload_document.side_effect = HTTPException(
            status_code=413,
            detail="File size exceeds 10MB limit"
        )
        mock_get_service.return_value = mock_service
        
        # Create a large file (mock)
        large_file_content = b"x" * (15 * 1024 * 1024)  # 15MB
        
        # Make request
        response = client.post(
            "/api/v1/vendor/upload-document/doc123",
            files={"file": ("large_file.jpg", large_file_content, "image/jpeg")},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 413
    
    @patch('app.api.deps.get_current_vendor')
    def test_get_vendor_profile_not_found(self, mock_get_user, client):
        """Test getting vendor profile when not found."""
        # Mock current user without vendor profile
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_user.vendor_profile = None
        mock_get_user.return_value = mock_user
        
        # Make request
        response = client.get(
            "/api/v1/vendor/profile",
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 404


class TestVendorAPIErrorHandling:
    """Test error handling in vendor API endpoints."""
    
    def test_register_vendor_unauthorized(self, client, sample_vendor_registration):
        """Test vendor registration without authentication."""
        # Make request without auth token
        response = client.post(
            "/api/v1/vendor/register",
            json=sample_vendor_registration
        )
        
        # Verify response
        assert response.status_code == 403  # Forbidden (no auth)
    
    @patch('app.api.deps.get_current_active_user')
    @patch('app.api.v1.vendor.get_vendor_verification_service')
    def test_register_vendor_service_error(
        self, 
        mock_get_service, 
        mock_get_user, 
        client, 
        sample_vendor_registration
    ):
        """Test vendor registration with service error."""
        from fastapi import HTTPException
        
        # Mock current user
        mock_user = MagicMock()
        mock_user.id = "507f1f77bcf86cd799439011"
        mock_get_user.return_value = mock_user
        
        # Mock verification service to raise error
        mock_service = AsyncMock()
        mock_service.initiate_vendor_registration.side_effect = HTTPException(
            status_code=400,
            detail="User already has a vendor profile"
        )
        mock_get_service.return_value = mock_service
        
        # Make request
        response = client.post(
            "/api/v1/vendor/register",
            json=sample_vendor_registration,
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Verify response
        assert response.status_code == 400
        data = response.json()
        assert "already has a vendor profile" in data["detail"]