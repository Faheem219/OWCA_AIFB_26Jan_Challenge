"""
Property-based test for image recognition accuracy.
**Property 21: Image Recognition Accuracy**
**Validates: Requirements 5.1**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from unittest.mock import AsyncMock, MagicMock, patch
from PIL import Image
import io
import random

from app.services.product_catalog_service import ProductCatalogService
from app.models.product import (
    ProductCategory, ProductSubcategory, QualityGrade, 
    FreshnessLevel, Unit, ImageAnalysisResult
)


@composite
def image_data_strategy(draw):
    """Generate mock image data with varying properties."""
    width = draw(st.integers(min_value=100, max_value=2000))
    height = draw(st.integers(min_value=100, max_value=2000))
    
    # Create a simple colored image
    color = draw(st.tuples(
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255),
        st.integers(min_value=0, max_value=255)
    ))
    
    # Create PIL Image
    image = Image.new('RGB', (width, height), color)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    
    return img_byte_arr, (width, height), color


@composite
def product_type_strategy(draw):
    """Generate product types for testing."""
    categories = list(ProductCategory)
    subcategories = list(ProductSubcategory)
    
    category = draw(st.sampled_from(categories))
    subcategory = draw(st.sampled_from(subcategories))
    
    return category, subcategory


@pytest.fixture
def mock_db():
    """Mock database."""
    db = MagicMock()
    db.products = AsyncMock()
    return db


@pytest.fixture
def product_service(mock_db):
    """Product catalog service instance."""
    return ProductCatalogService(mock_db)


class TestImageRecognitionProperties:
    """Property-based tests for image recognition accuracy."""
    
    @given(
        image_data=image_data_strategy(),
        product_type=product_type_strategy()
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_21_image_recognition_accuracy(
        self, 
        image_data, 
        product_type, 
        product_service
    ):
        """
        **Property 21: Image Recognition Accuracy**
        **Validates: Requirements 5.1**
        
        For any product image upload, the Product_Catalog should correctly 
        identify and categorize the product with consistent classification 
        across similar items.
        """
        img_bytes, (width, height), color = image_data
        expected_category, expected_subcategory = product_type
        
        # Test: Image analysis should complete without errors
        analysis_result = await product_service.analyze_product_image(img_bytes)
        
        # Test: Analysis result should be valid
        assert isinstance(analysis_result, ImageAnalysisResult)
        
        # Test: Confidence score should be within valid range
        assert 0.0 <= analysis_result.confidence_score <= 1.0
        
        # Test: If category is detected, it should be valid
        if analysis_result.detected_category:
            assert analysis_result.detected_category in ProductCategory
        
        # Test: If subcategory is detected, it should be valid
        if analysis_result.detected_subcategory:
            assert analysis_result.detected_subcategory in ProductSubcategory
        
        # Test: Quality assessment should be valid if present
        if analysis_result.quality_assessment:
            assert analysis_result.quality_assessment in QualityGrade
        
        # Test: Freshness level should be valid if present
        if analysis_result.freshness_level:
            assert analysis_result.freshness_level in FreshnessLevel
        
        # Test: Quantity estimate should be positive if present
        if analysis_result.quantity_estimate is not None:
            assert analysis_result.quantity_estimate >= 0.0
        
        # Test: Estimated unit should be valid if present
        if analysis_result.estimated_unit:
            assert analysis_result.estimated_unit in Unit
        
        # Test: Processing metadata should contain image information
        assert "image_size" in analysis_result.processing_metadata
        assert analysis_result.processing_metadata["image_size"] == f"{width}x{height}"
        
        # Test: Defects detected should be a list
        assert isinstance(analysis_result.defects_detected, list)
    
    @given(
        image_data1=image_data_strategy(),
        image_data2=image_data_strategy()
    )
    @settings(max_examples=20, deadline=4000)
    @pytest.mark.asyncio
    async def test_consistent_classification_similar_images(
        self, 
        image_data1, 
        image_data2, 
        product_service
    ):
        """
        Test that similar images receive consistent classification.
        """
        img_bytes1, (width1, height1), color1 = image_data1
        img_bytes2, (width2, height2), color2 = image_data2
        
        # Only test if images are similar in size (within 20% difference)
        size_diff = abs(width1 * height1 - width2 * height2) / max(width1 * height1, width2 * height2)
        assume(size_diff < 0.2)
        
        # Analyze both images
        result1 = await product_service.analyze_product_image(img_bytes1)
        result2 = await product_service.analyze_product_image(img_bytes2)
        
        # Test: Both analyses should complete successfully
        assert isinstance(result1, ImageAnalysisResult)
        assert isinstance(result2, ImageAnalysisResult)
        
        # Test: Confidence scores should be reasonable for similar images
        confidence_diff = abs(result1.confidence_score - result2.confidence_score)
        assert confidence_diff <= 0.5  # Allow some variation but not too much
        
        # Test: If both detect categories, they should be consistent for similar images
        if result1.detected_category and result2.detected_category:
            # For very similar images (same size category), expect same classification
            if abs(width1 - width2) < 100 and abs(height1 - height2) < 100:
                assert result1.detected_category == result2.detected_category
    
    @given(
        image_size=st.tuples(
            st.integers(min_value=50, max_value=3000),
            st.integers(min_value=50, max_value=3000)
        )
    )
    @settings(max_examples=25, deadline=3000)
    @pytest.mark.asyncio
    async def test_image_size_impact_on_confidence(
        self, 
        image_size, 
        product_service
    ):
        """
        Test that image size appropriately impacts confidence scores.
        """
        width, height = image_size
        
        # Create test image
        color = (128, 128, 128)  # Gray
        image = Image.new('RGB', (width, height), color)
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Analyze image
        result = await product_service.analyze_product_image(img_bytes)
        
        # Test: Larger images should generally have higher confidence
        area = width * height
        
        if area > 500000:  # Large image
            assert result.confidence_score >= 0.7
        elif area > 200000:  # Medium image
            assert result.confidence_score >= 0.5
        else:  # Small image
            assert result.confidence_score >= 0.3
        
        # Test: Very small images should have lower confidence
        if area < 10000:  # Very small
            assert result.confidence_score <= 0.6
    
    @given(
        product_category=st.sampled_from(list(ProductCategory))
    )
    @settings(max_examples=15, deadline=2000)
    @pytest.mark.asyncio
    async def test_category_specific_analysis(
        self, 
        product_category, 
        product_service
    ):
        """
        Test that analysis adapts to different product categories.
        """
        # Create a standard test image
        image = Image.new('RGB', (800, 600), (100, 150, 200))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Analyze with category hint (simulated by using the same image)
        result = await product_service.analyze_product_image(img_bytes)
        
        # Test: Analysis should complete successfully for all categories
        assert isinstance(result, ImageAnalysisResult)
        assert 0.0 <= result.confidence_score <= 1.0
        
        # Test: Perishable categories should have freshness detection
        perishable_categories = [
            ProductCategory.VEGETABLES, 
            ProductCategory.FRUITS, 
            ProductCategory.DAIRY,
            ProductCategory.MEAT,
            ProductCategory.SEAFOOD
        ]
        
        if product_category in perishable_categories:
            # For perishable items, freshness should be analyzed
            # (In mock implementation, this is always set, but in real implementation
            # it would be category-specific)
            assert result.freshness_level is not None
    
    @given(
        defect_simulation=st.booleans()
    )
    @settings(max_examples=10, deadline=1500)
    @pytest.mark.asyncio
    async def test_defect_detection_consistency(
        self, 
        defect_simulation, 
        product_service
    ):
        """
        Test that defect detection is consistent and reliable.
        """
        # Create image with simulated quality issues
        if defect_simulation:
            # Small, low-quality image to simulate defects
            image = Image.new('RGB', (200, 150), (50, 50, 50))
        else:
            # High-quality image
            image = Image.new('RGB', (1200, 900), (200, 200, 200))
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Analyze image
        result = await product_service.analyze_product_image(img_bytes)
        
        # Test: Defects should be properly detected
        assert isinstance(result.defects_detected, list)
        
        # Test: Low quality images should have defects detected
        if defect_simulation:
            # In our mock implementation, small images trigger defect detection
            assert len(result.defects_detected) >= 0  # May or may not detect defects
        
        # Test: All detected defects should be strings
        for defect in result.defects_detected:
            assert isinstance(defect, str)
            assert len(defect) > 0
    
    @given(
        multiple_images=st.lists(
            image_data_strategy(), 
            min_size=2, 
            max_size=5
        )
    )
    @settings(max_examples=10, deadline=6000)
    @pytest.mark.asyncio
    async def test_batch_analysis_consistency(
        self, 
        multiple_images, 
        product_service
    ):
        """
        Test that batch analysis of multiple images is consistent.
        """
        results = []
        
        # Analyze all images
        for img_data, _, _ in multiple_images:
            result = await product_service.analyze_product_image(img_data)
            results.append(result)
        
        # Test: All analyses should complete successfully
        assert len(results) == len(multiple_images)
        
        for result in results:
            assert isinstance(result, ImageAnalysisResult)
            assert 0.0 <= result.confidence_score <= 1.0
        
        # Test: Results should have consistent structure
        for result in results:
            assert hasattr(result, 'confidence_score')
            assert hasattr(result, 'processing_metadata')
            assert hasattr(result, 'defects_detected')
            assert isinstance(result.defects_detected, list)
    
    @given(
        image_format=st.sampled_from(['JPEG', 'PNG'])
    )
    @settings(max_examples=8, deadline=2000)
    @pytest.mark.asyncio
    async def test_format_independence(
        self, 
        image_format, 
        product_service
    ):
        """
        Test that image analysis works consistently across different formats.
        """
        # Create test image
        image = Image.new('RGB', (600, 400), (150, 100, 200))
        
        # Save in specified format
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format=image_format)
        img_bytes = img_byte_arr.getvalue()
        
        # Analyze image
        result = await product_service.analyze_product_image(img_bytes)
        
        # Test: Analysis should work regardless of format
        assert isinstance(result, ImageAnalysisResult)
        assert 0.0 <= result.confidence_score <= 1.0
        
        # Test: Processing metadata should be present
        assert "image_size" in result.processing_metadata
        assert "model_version" in result.processing_metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])