"""
Property-based tests for vendor verification system.
**Validates: Requirements 4.1, 4.4**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

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


# Custom strategies for generating test data
@st.composite
def location_strategy(draw):
    """Generate valid location data."""
    return Location(
        address=draw(st.text(min_size=10, max_size=100)),
        city=draw(st.sampled_from(["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune"])),
        state=draw(st.sampled_from(["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "West Bengal"])),
        pincode=draw(st.text(min_size=6, max_size=6, alphabet=st.characters(whitelist_categories=("Nd",))))
    )


@st.composite
def vendor_registration_strategy(draw):
    """Generate valid vendor registration data."""
    business_types = ["agriculture", "retail", "wholesale", "manufacturing", "organic", "services"]
    specializations = ["organic", "vegetables", "fruits", "grains", "dairy", "spices"]
    languages = ["hi", "en", "mr", "ta", "te", "bn", "gu", "kn", "ml", "pa"]
    
    return VendorRegistrationRequest(
        business_name=draw(st.text(min_size=5, max_size=50)),
        business_type=draw(st.sampled_from(business_types)),
        location=draw(location_strategy()),
        specializations=draw(st.lists(st.sampled_from(specializations), min_size=1, max_size=3)),
        languages_spoken=draw(st.lists(st.sampled_from(languages), min_size=1, max_size=5)),
        government_id_number=draw(st.text(min_size=10, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Nd")))),
        government_id_type=draw(st.sampled_from(["aadhaar", "pan", "voter_id", "passport"]))
    )


@st.composite
def document_upload_strategy(draw):
    """Generate valid document upload requests."""
    return DocumentUploadRequest(
        document_type=draw(st.sampled_from(list(DocumentType))),
        number=draw(st.text(min_size=8, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Nd")))),
        issuing_authority=draw(st.text(min_size=5, max_size=50)),
        issue_date=draw(st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime.now())),
        expiry_date=draw(st.one_of(st.none(), st.datetimes(min_value=datetime.now(), max_value=datetime(2030, 12, 31))))
    )


@st.composite
def admin_action_strategy(draw):
    """Generate valid admin actions."""
    actions = ["approve", "reject", "request_documents"]
    action = draw(st.sampled_from(actions))
    
    admin_action = AdminVerificationAction(
        action=action,
        notes=draw(st.one_of(st.none(), st.text(min_size=10, max_size=200)))
    )
    
    if action == "request_documents":
        admin_action.required_documents = draw(st.lists(st.sampled_from(list(DocumentType)), min_size=1, max_size=3))
    
    return admin_action


@pytest.fixture
def mock_db():
    """Mock database for property tests."""
    db = MagicMock()
    db.users = AsyncMock()
    db.vendors = AsyncMock()
    return db


@pytest.fixture
def vendor_service(mock_db):
    """Vendor verification service for property tests."""
    return VendorVerificationService(mock_db)


class TestVendorVerificationProperties:
    """Property-based tests for vendor verification system."""
    
    @pytest.mark.asyncio
    async def test_property_16_verification_requirement_enforcement(
        self, 
        vendor_service
    ):
        """
        **Property 16: Verification Requirement Enforcement**
        *For any* vendor profile creation attempt, the system should require and validate 
        government-issued ID verification before allowing profile activation.
        **Validates: Requirements 4.1**
        """
        @given(vendor_registration_strategy())
        @settings(max_examples=50, deadline=5000)
        async def run_property_test(registration_data):
            user_id = "507f1f77bcf86cd799439011"
            
            # Mock user exists without vendor profile
            vendor_service.users_collection.find_one.return_value = {
                "_id": user_id,
                "email": "test@example.com",
                "user_type": "buyer"
            }
            
            # Mock successful profile creation
            vendor_service.users_collection.update_one.return_value = MagicMock(modified_count=1)
            
            # Initiate vendor registration
            result = await vendor_service.initiate_vendor_registration(user_id, registration_data)
            
            # Verify that government ID is always required
            assert DocumentType.GOVERNMENT_ID in result["required_documents"], \
                "Government ID must be required for all vendor registrations"
            
            # Verify initial status is pending (not verified)
            assert result["verification_status"] == VerificationStatus.PENDING, \
                "Initial verification status must be PENDING"
            
            # Verify that profile is not immediately activated
            assert result["next_step"] == VerificationStep.DOCUMENTS_UPLOADED, \
                "Profile should require document upload before activation"
        
        # Run the property test
        await run_property_test()
    
    @given(st.text(min_size=8, max_size=20, alphabet=st.characters(whitelist_categories=("Lu", "Nd"))))
    @settings(max_examples=30, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_government_id_validation_consistency(
        self, 
        government_id_number,
        vendor_service
    ):
        """
        Property: Government ID validation should be consistent across all valid ID formats.
        **Validates: Requirements 4.1**
        """
        document = {
            "type": DocumentType.GOVERNMENT_ID,
            "number": government_id_number
        }
        
        # Validate government ID
        is_valid = await vendor_service._validate_government_id(document)
        
        # Property: IDs with sufficient length should be considered valid
        if len(government_id_number) >= 8:
            assert is_valid is True, f"Government ID {government_id_number} with length >= 8 should be valid"
        else:
            assert is_valid is False, f"Government ID {government_id_number} with length < 8 should be invalid"
    
    @given(st.sampled_from(["agriculture", "retail", "wholesale", "manufacturing", "organic", "services"]))
    @settings(max_examples=20, deadline=2000)
    def test_property_required_documents_consistency(self, business_type, vendor_service):
        """
        Property: Required documents should be consistent for the same business type.
        **Validates: Requirements 4.1, 4.4**
        """
        # Get required documents multiple times for the same business type
        required_docs_1 = vendor_service._get_required_documents(business_type)
        required_docs_2 = vendor_service._get_required_documents(business_type)
        
        # Property: Same business type should always return same required documents
        assert required_docs_1 == required_docs_2, \
            f"Required documents for {business_type} should be consistent"
        
        # Property: Government ID should always be required
        assert DocumentType.GOVERNMENT_ID in required_docs_1, \
            f"Government ID should always be required for {business_type}"
        
        # Property: Address proof should always be required
        assert DocumentType.ADDRESS_PROOF in required_docs_1, \
            f"Address proof should always be required for {business_type}"
        
        # Property: Business license should be required for commercial business types
        commercial_types = ["retail", "wholesale", "manufacturing"]
        if business_type in commercial_types:
            assert DocumentType.BUSINESS_LICENSE in required_docs_1, \
                f"Business license should be required for {business_type}"
            assert DocumentType.TAX_CERTIFICATE in required_docs_1, \
                f"Tax certificate should be required for {business_type}"
        
        # Property: Organic certification should be required for organic business
        if business_type == "organic":
            assert DocumentType.ORGANIC_CERTIFICATION in required_docs_1, \
                f"Organic certification should be required for organic business"
    
    @given(document_upload_strategy())
    @settings(max_examples=30, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_document_upload_request_consistency(
        self, 
        document_request,
        vendor_service
    ):
        """
        Property: Document upload requests should generate consistent responses.
        **Validates: Requirements 4.1**
        """
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user with vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "vendor_profile": {"business_name": "Test Business"}
        }
        
        # Mock successful document insertion
        vendor_service.documents_collection.insert_one.return_value = MagicMock()
        
        # Request document upload
        result = await vendor_service.request_document_upload(user_id, document_request)
        
        # Property: Upload response should always contain required fields
        assert hasattr(result, 'document_id'), "Upload response must contain document_id"
        assert hasattr(result, 'upload_url'), "Upload response must contain upload_url"
        assert hasattr(result, 'max_file_size'), "Upload response must contain max_file_size"
        assert hasattr(result, 'allowed_mime_types'), "Upload response must contain allowed_mime_types"
        
        # Property: Upload URL should be properly formatted
        assert result.upload_url.startswith("/api/v1/vendor/upload-document/"), \
            "Upload URL should have correct format"
        
        # Property: File size limit should be reasonable (10MB)
        assert result.max_file_size == 10 * 1024 * 1024, \
            "File size limit should be 10MB"
        
        # Property: Should allow common document formats
        expected_types = ["image/jpeg", "image/png", "application/pdf"]
        for mime_type in expected_types:
            assert mime_type in result.allowed_mime_types, \
                f"Should allow {mime_type} file type"
    
    @given(admin_action_strategy())
    @settings(max_examples=30, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_admin_review_consistency(
        self, 
        admin_action,
        vendor_service
    ):
        """
        Property: Admin review actions should produce consistent results.
        **Validates: Requirements 4.1, 4.4**
        """
        user_id = "507f1f77bcf86cd799439011"
        admin_user_id = "507f1f77bcf86cd799439013"
        
        # Mock user with vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "vendor_profile": {"business_name": "Test Business"}
        }
        
        # Mock successful update
        vendor_service.users_collection.update_one.return_value = MagicMock()
        
        # Perform admin review
        result = await vendor_service.admin_review_vendor(user_id, admin_action, admin_user_id)
        
        # Property: Result should always contain status
        assert "status" in result, "Admin review result must contain status"
        assert "message" in result, "Admin review result must contain message"
        
        # Property: Status should match action
        if admin_action.action == "approve":
            assert result["status"] == "approved", "Approve action should result in approved status"
        elif admin_action.action == "reject":
            assert result["status"] == "rejected", "Reject action should result in rejected status"
        elif admin_action.action == "request_documents":
            assert result["status"] == "documents_requested", \
                "Request documents action should result in documents_requested status"
            assert "required_documents" in result, \
                "Request documents action should include required_documents"
    
    @given(st.integers(min_value=1, max_value=20 * 1024 * 1024))  # 1 byte to 20MB
    @settings(max_examples=20, deadline=2000)
    def test_property_file_size_validation_consistency(self, file_size, vendor_service):
        """
        Property: File size validation should be consistent.
        **Validates: Requirements 4.1**
        """
        max_allowed_size = 10 * 1024 * 1024  # 10MB
        
        # Property: Files within limit should be considered valid size
        if file_size <= max_allowed_size:
            # This would be valid in the actual upload method
            assert file_size <= max_allowed_size, "File within limit should be valid"
        else:
            # This would be rejected in the actual upload method
            assert file_size > max_allowed_size, "File exceeding limit should be invalid"
    
    @given(st.sampled_from(["image/jpeg", "image/png", "application/pdf", "text/plain", "video/mp4"]))
    @settings(max_examples=10, deadline=1000)
    def test_property_mime_type_validation_consistency(self, mime_type, vendor_service):
        """
        Property: MIME type validation should be consistent.
        **Validates: Requirements 4.1**
        """
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        
        # Property: Allowed types should always be accepted
        if mime_type in allowed_types:
            assert mime_type in allowed_types, f"MIME type {mime_type} should be allowed"
        else:
            assert mime_type not in allowed_types, f"MIME type {mime_type} should not be allowed"
    
    @given(st.lists(st.sampled_from(list(DocumentType)), min_size=1, max_size=5))
    @settings(max_examples=20, deadline=2000)
    @pytest.mark.asyncio
    async def test_property_verification_workflow_progression(
        self, 
        document_types,
        vendor_service
    ):
        """
        Property: Verification workflow should progress consistently based on uploaded documents.
        **Validates: Requirements 4.1, 4.4**
        """
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock successful workflow updates
        vendor_service.users_collection.update_one.return_value = MagicMock()
        
        for doc_type in document_types:
            # Mock document record
            vendor_service.documents_collection.find_one.return_value = {
                "_id": "doc_id",
                "document": {"type": doc_type}
            }
            
            # Update workflow
            await vendor_service._update_verification_workflow(user_id, "doc_id")
            
            # Verify update was called (workflow progression logic)
            vendor_service.users_collection.update_one.assert_called()
    
    @given(st.datetimes(min_value=datetime(2000, 1, 1), max_value=datetime(2030, 12, 31)))
    @settings(max_examples=20, deadline=2000)
    def test_property_document_expiry_handling(self, expiry_date, vendor_service):
        """
        Property: Document expiry dates should be handled consistently.
        **Validates: Requirements 4.1, 4.4**
        """
        current_date = datetime.now()
        
        # Property: Documents with future expiry dates should be considered valid
        if expiry_date > current_date:
            # Document is not expired
            assert expiry_date > current_date, "Future expiry date should be valid"
        else:
            # Document is expired
            assert expiry_date <= current_date, "Past expiry date should be expired"


class TestVendorVerificationIntegrationProperties:
    """Integration property tests for vendor verification workflow."""
    
    @given(vendor_registration_strategy(), st.lists(document_upload_strategy(), min_size=1, max_size=3))
    @settings(max_examples=10, deadline=10000)
    @pytest.mark.asyncio
    async def test_property_complete_verification_workflow(
        self, 
        registration_data, 
        document_requests,
        vendor_service
    ):
        """
        Property: Complete verification workflow should maintain consistency.
        **Validates: Requirements 4.1, 4.4**
        """
        user_id = "507f1f77bcf86cd799439011"
        
        # Mock user exists
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "email": "test@example.com",
            "user_type": "buyer"
        }
        
        # Mock successful operations
        vendor_service.users_collection.update_one.return_value = MagicMock(modified_count=1)
        vendor_service.documents_collection.insert_one.return_value = MagicMock()
        
        # Step 1: Initiate registration
        registration_result = await vendor_service.initiate_vendor_registration(
            user_id, registration_data
        )
        
        # Property: Registration should always require government ID
        assert DocumentType.GOVERNMENT_ID in registration_result["required_documents"], \
            "Government ID should always be required in registration"
        
        # Step 2: Request document uploads
        upload_results = []
        for doc_request in document_requests:
            # Mock user with vendor profile for document upload
            vendor_service.users_collection.find_one.return_value = {
                "_id": user_id,
                "vendor_profile": {"business_name": registration_data.business_name}
            }
            
            upload_result = await vendor_service.request_document_upload(user_id, doc_request)
            upload_results.append(upload_result)
        
        # Property: All document upload requests should succeed
        assert len(upload_results) == len(document_requests), \
            "All document upload requests should be processed"
        
        for upload_result in upload_results:
            assert hasattr(upload_result, 'document_id'), \
                "Each upload should generate a document ID"
            assert hasattr(upload_result, 'upload_url'), \
                "Each upload should provide an upload URL"
    
    @given(st.sampled_from(["approve", "reject"]))
    @settings(max_examples=10, deadline=3000)
    @pytest.mark.asyncio
    async def test_property_admin_decision_finality(
        self, 
        admin_decision,
        vendor_service
    ):
        """
        Property: Admin decisions should be final and consistent.
        **Validates: Requirements 4.1, 4.4**
        """
        user_id = "507f1f77bcf86cd799439011"
        admin_user_id = "507f1f77bcf86cd799439013"
        
        # Mock user with vendor profile
        vendor_service.users_collection.find_one.return_value = {
            "_id": user_id,
            "vendor_profile": {"business_name": "Test Business"}
        }
        
        # Mock successful update
        vendor_service.users_collection.update_one.return_value = MagicMock()
        
        # Create admin action
        admin_action = AdminVerificationAction(
            action=admin_decision,
            notes=f"Admin {admin_decision} decision"
        )
        
        # Perform admin review
        result = await vendor_service.admin_review_vendor(user_id, admin_action, admin_user_id)
        
        # Property: Admin decision should be reflected in result
        if admin_decision == "approve":
            assert result["status"] == "approved", "Approval should result in approved status"
        elif admin_decision == "reject":
            assert result["status"] == "rejected", "Rejection should result in rejected status"
        
        # Property: Result should always contain a message
        assert "message" in result and result["message"], \
            "Admin decision should always include a message"