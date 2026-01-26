"""
Property-based test for credibility score calculation consistency.
**Property 18: Credibility Score Calculation Consistency**
**Validates: Requirements 4.3**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from app.services.vendor_verification_service import VendorVerificationService
from app.models.user import (
    VendorProfile, TransactionStats, VerificationStatus, 
    Location, VerificationWorkflow
)


@composite
def transaction_stats_strategy(draw):
    """Generate transaction statistics."""
    total_transactions = draw(st.integers(min_value=0, max_value=1000))
    completed_transactions = draw(st.integers(min_value=0, max_value=total_transactions))
    total_revenue = draw(st.floats(min_value=0.0, max_value=100000.0))
    average_rating = draw(st.floats(min_value=0.0, max_value=5.0))
    response_time_hours = draw(st.floats(min_value=0.1, max_value=72.0))
    
    return TransactionStats(
        total_transactions=total_transactions,
        completed_transactions=completed_transactions,
        total_revenue=total_revenue,
        average_rating=average_rating,
        response_time_hours=response_time_hours
    )


@composite
def vendor_profile_strategy(draw):
    """Generate vendor profile with varying verification states."""
    verification_status = draw(st.sampled_from(list(VerificationStatus)))
    government_id_verified = draw(st.booleans())
    business_license_verified = draw(st.booleans())
    tax_registration_verified = draw(st.booleans())
    bank_account_verified = draw(st.booleans())
    transaction_stats = draw(transaction_stats_strategy())
    
    location = Location(
        address="Test Address",
        city="Test City",
        state="Test State",
        pincode="123456"
    )
    
    return VendorProfile(
        business_name="Test Business",
        business_type="retail",
        location=location,
        verification_status=verification_status,
        government_id_verified=government_id_verified,
        business_license_verified=business_license_verified,
        tax_registration_verified=tax_registration_verified,
        bank_account_verified=bank_account_verified,
        transaction_stats=transaction_stats
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
    return VendorVerificationService(mock_db)


class TestCredibilityScoreProperties:
    """Property-based tests for credibility score calculation."""
    
    @given(vendor_profile=vendor_profile_strategy())
    @settings(max_examples=50, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_18_credibility_score_consistency(
        self, 
        vendor_profile, 
        vendor_service,
        mock_db
    ):
        """
        **Property 18: Credibility Score Calculation Consistency**
        **Validates: Requirements 4.3**
        
        For any vendor, the credibility score should be calculated using the same 
        algorithm considering transaction history, ratings, and dispute resolution outcomes.
        """
        user_id = str(ObjectId())
        
        # Mock database response
        mock_user = {
            "_id": ObjectId(user_id),
            "vendor_profile": vendor_profile.dict()
        }
        mock_db.users.find_one.return_value = mock_user
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        
        # Calculate credibility score
        score = await vendor_service.calculate_credibility_score(user_id)
        
        # Test: Score is within valid range (0-100)
        assert 0.0 <= score <= 100.0
        
        # Test: Score calculation is deterministic
        score2 = await vendor_service.calculate_credibility_score(user_id)
        assert score == score2
        
        # Test: Verification status affects score
        if vendor_profile.verification_status == VerificationStatus.VERIFIED:
            assert score >= 30.0  # Should get verification points
        elif vendor_profile.verification_status == VerificationStatus.PENDING:
            assert score >= 10.0  # Should get partial points
        
        # Test: Document verification affects score
        document_points = 0.0
        if vendor_profile.government_id_verified:
            document_points += 8.0
        if vendor_profile.business_license_verified:
            document_points += 6.0
        if vendor_profile.tax_registration_verified:
            document_points += 3.0
        if vendor_profile.bank_account_verified:
            document_points += 3.0
        
        # Score should include document verification points
        if document_points > 0:
            assert score >= document_points
        
        # Test: Transaction history affects score
        stats = vendor_profile.transaction_stats
        if stats.total_transactions > 0:
            completion_rate = stats.completed_transactions / stats.total_transactions
            if completion_rate > 0.8:  # High completion rate
                assert score > 0  # Should contribute to score
        
        # Test: Rating affects score
        if stats.average_rating > 4.0:
            assert score > 0  # Good ratings should contribute
        
        # Test: Response time affects score
        if stats.response_time_hours <= 1.0:
            assert score >= 10.0  # Should get full response time points
    
    @given(
        stats1=transaction_stats_strategy(),
        stats2=transaction_stats_strategy()
    )
    @settings(max_examples=30, deadline=2000)
    @pytest.mark.asyncio
    async def test_transaction_stats_comparison(
        self, 
        stats1, 
        stats2, 
        vendor_service,
        mock_db
    ):
        """
        Test that vendors with better transaction stats get higher scores.
        """
        user_id1 = str(ObjectId())
        user_id2 = str(ObjectId())
        
        # Create identical profiles except for transaction stats
        base_profile = VendorProfile(
            business_name="Test Business",
            business_type="retail",
            location=Location(
                address="Test Address",
                city="Test City", 
                state="Test State",
                pincode="123456"
            ),
            verification_status=VerificationStatus.VERIFIED,
            government_id_verified=True,
            business_license_verified=True,
            transaction_stats=stats1
        )
        
        profile2 = base_profile.copy()
        profile2.transaction_stats = stats2
        
        # Mock database responses
        mock_db.users.find_one.side_effect = [
            {"_id": ObjectId(user_id1), "vendor_profile": base_profile.dict()},
            {"_id": ObjectId(user_id2), "vendor_profile": profile2.dict()}
        ]
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        
        score1 = await vendor_service.calculate_credibility_score(user_id1)
        score2 = await vendor_service.calculate_credibility_score(user_id2)
        
        # Test: Both scores are valid
        assert 0.0 <= score1 <= 100.0
        assert 0.0 <= score2 <= 100.0
        
        # Test: Better completion rate should yield higher score
        if stats1.total_transactions > 0 and stats2.total_transactions > 0:
            completion_rate1 = stats1.completed_transactions / stats1.total_transactions
            completion_rate2 = stats2.completed_transactions / stats2.total_transactions
            
            if completion_rate1 > completion_rate2 + 0.1:  # Significant difference
                assert score1 >= score2
        
        # Test: Better ratings should yield higher score
        if abs(stats1.average_rating - stats2.average_rating) > 0.5:
            if stats1.average_rating > stats2.average_rating:
                assert score1 >= score2
            else:
                assert score2 >= score1
    
    @given(verification_status=st.sampled_from(list(VerificationStatus)))
    @settings(max_examples=10, deadline=1000)
    @pytest.mark.asyncio
    async def test_verification_status_impact(
        self, 
        verification_status, 
        vendor_service,
        mock_db
    ):
        """
        Test that verification status consistently impacts credibility score.
        """
        user_id = str(ObjectId())
        
        profile = VendorProfile(
            business_name="Test Business",
            business_type="retail",
            location=Location(
                address="Test Address",
                city="Test City",
                state="Test State", 
                pincode="123456"
            ),
            verification_status=verification_status
        )
        
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(user_id),
            "vendor_profile": profile.dict()
        }
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        
        score = await vendor_service.calculate_credibility_score(user_id)
        
        # Test: Verification status affects score predictably
        if verification_status == VerificationStatus.VERIFIED:
            assert score >= 30.0
        elif verification_status == VerificationStatus.PENDING:
            assert 10.0 <= score < 30.0
        elif verification_status == VerificationStatus.REJECTED:
            assert score < 30.0
    
    @given(
        response_time=st.floats(min_value=0.1, max_value=72.0)
    )
    @settings(max_examples=20, deadline=1000)
    @pytest.mark.asyncio
    async def test_response_time_scoring(
        self, 
        response_time, 
        vendor_service,
        mock_db
    ):
        """
        Test that response time consistently affects credibility score.
        """
        user_id = str(ObjectId())
        
        stats = TransactionStats(
            total_transactions=10,
            completed_transactions=10,
            response_time_hours=response_time
        )
        
        profile = VendorProfile(
            business_name="Test Business",
            business_type="retail",
            location=Location(
                address="Test Address",
                city="Test City",
                state="Test State",
                pincode="123456"
            ),
            verification_status=VerificationStatus.VERIFIED,
            transaction_stats=stats
        )
        
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(user_id),
            "vendor_profile": profile.dict()
        }
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        
        score = await vendor_service.calculate_credibility_score(user_id)
        
        # Test: Response time affects score according to defined tiers
        if response_time <= 1.0:
            # Should get full 10 points for response time
            assert score >= 40.0  # Base 30 + 10 response time
        elif response_time <= 4.0:
            # Should get 7 points for response time
            assert score >= 37.0  # Base 30 + 7 response time
        elif response_time <= 12.0:
            # Should get 4 points for response time
            assert score >= 34.0  # Base 30 + 4 response time
        elif response_time <= 24.0:
            # Should get 2 points for response time
            assert score >= 32.0  # Base 30 + 2 response time
    
    @given(
        rating=st.floats(min_value=1.0, max_value=5.0)
    )
    @settings(max_examples=15, deadline=1000)
    @pytest.mark.asyncio
    async def test_rating_impact_consistency(
        self, 
        rating, 
        vendor_service,
        mock_db
    ):
        """
        Test that customer ratings consistently impact credibility score.
        """
        user_id = str(ObjectId())
        
        stats = TransactionStats(
            total_transactions=20,
            completed_transactions=20,
            average_rating=rating
        )
        
        profile = VendorProfile(
            business_name="Test Business",
            business_type="retail",
            location=Location(
                address="Test Address",
                city="Test City",
                state="Test State",
                pincode="123456"
            ),
            verification_status=VerificationStatus.VERIFIED,
            transaction_stats=stats
        )
        
        mock_db.users.find_one.return_value = {
            "_id": ObjectId(user_id),
            "vendor_profile": profile.dict()
        }
        mock_db.users.update_one.return_value = MagicMock(modified_count=1)
        
        score = await vendor_service.calculate_credibility_score(user_id)
        
        # Test: Rating contributes proportionally to score
        expected_rating_points = (rating / 5.0) * 15.0
        # Score should include rating contribution
        assert score >= 30.0 + expected_rating_points - 1.0  # Allow small margin for other factors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])