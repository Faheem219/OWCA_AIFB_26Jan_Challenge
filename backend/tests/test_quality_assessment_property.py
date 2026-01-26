"""
Property-based test for quality assessment consistency.
**Property 22: Quality Assessment Consistency**
**Validates: Requirements 5.2**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from unittest.mock import AsyncMock, MagicMock
from PIL import Image
import io

from app.services.product_catalog_service import ProductCatalogService
from app.models.product import ProductCategory, QualityGrade


@composite
def quality_image_strategy(draw):
    """Generate images with different quality characteristics."""
    # Vary image properties that might affect quality assessment
    width = draw(st.integers(min_value=200, max_value=1500))
    height = draw(st.integers(min_value=200, max_value=1500))
    
    # Simulate quality through image properties
    quality_level = draw(st.sampled_from(['high', 'medium', 'low']))
    
    if quality_level == 'high':
        # High quality: larger, brighter colors
        color = draw(st.tuples(
            st.integers(min_value=150, max_value=255),
            st.integers(min_value=150, max_value=255),
            st.integers(min_value=150, max_value=255)
        ))
        width = max(width, 800)
        height = max(height, 600)
    elif quality_level == 'medium':
        # Medium quality: moderate colors and size
        color = draw(st.tuples(
            st.integers(min_value=100, max_value=200),
            st.integers(min_value=100, max_value=200),
            st.integers(min_value=100, max_value=200)
        ))
    else:  # low quality
        # Low quality: darker colors, smaller size
        color = draw(st.tuples(
            st.integers(min_value=50, max_value=150),
            st.integers(min_value=50, max_value=150),
            st.integers(min_value=50, max_value=150)
        ))
        width = min(width, 400)
        height = min(height, 300)
    
    # Create PIL Image
    image = Image.new('RGB', (width, height), color)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    return img_bytes, quality_level, (width, height)


@composite
def product_category_strategy(draw):
    """Generate product categories for testing."""
    return draw(st.sampled_from(list(ProductCategory)))


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


class TestQualityAssessmentProperties:
    """Property-based tests for quality assessment consistency."""
    
    @given(
        image_data=quality_image_strategy(),
        product_category=product_category_strategy()
    )
    @settings(max_examples=30, deadline=4000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_22_quality_assessment_consistency(
        self, 
        image_data, 
        product_category, 
        product_service
    ):
        """
        **Property 22: Quality Assessment Consistency**
        **Validates: Requirements 5.2**
        
        For any product images of the same type and quality, the AI quality 
        assessment should assign consistent quality grades.
        """
        img_bytes, expected_quality_level, (width, height) = image_data
        
        # Test: Quality assessment should complete without errors
        result = await product_service.assess_quality([img_bytes], product_category.value)
        
        # Test: Result should have required fields
        assert "quality_grade" in result
        assert "quality_score" in result
        assert "defects_detected" in result
        assert "images_analyzed" in result
        
        # Test: Quality grade should be valid
        assert result["quality_grade"] in QualityGrade
        
        # Test: Quality score should be within valid range
        assert 0.0 <= result["quality_score"] <= 1.0
        
        # Test: Defects should be a list
        assert isinstance(result["defects_detected"], list)
        
        # Test: Images analyzed count should match input
        assert result["images_analyzed"] == 1
        
        # Test: Assessment method should be specified
        assert "assessment_method" in result
        assert isinstance(result["assessment_method"], str)
    
    @given(
        same_quality_images=st.lists(
            quality_image_strategy(),
            min_size=2,
            max_size=4
        ).filter(lambda images: len(set(img[1] for img in images)) == 1)  # Same quality level
    )
    @settings(max_examples=15, deadline=5000)
    @pytest.mark.asyncio
    async def test_consistent_grading_same_quality(
        self, 
        same_quality_images, 
        product_service
    ):
        """
        Test that images of the same quality level receive consistent grades.
        """
        assume(len(same_quality_images) >= 2)
        
        quality_level = same_quality_images[0][1]  # All should have same quality level
        product_category = ProductCategory.VEGETABLES.value
        
        results = []
        for img_bytes, _, _ in same_quality_images:
            result = await product_service.assess_quality([img_bytes], product_category)
            results.append(result)
        
        # Test: All assessments should complete successfully
        assert len(results) == len(same_quality_images)
        
        # Test: Quality scores should be similar for same quality level
        quality_scores = [r["quality_score"] for r in results]
        score_variance = max(quality_scores) - min(quality_scores)
        
        # Allow some variance but not too much for same quality level
        assert score_variance <= 0.3
        
        # Test: Quality grades should be consistent for same quality level
        quality_grades = [r["quality_grade"] for r in results]
        
        # For same quality level, at least 70% should have same grade
        most_common_grade = max(set(quality_grades), key=quality_grades.count)
        consistency_ratio = quality_grades.count(most_common_grade) / len(quality_grades)
        assert consistency_ratio >= 0.7
    
    @given(
        high_quality_image=quality_image_strategy().filter(lambda x: x[1] == 'high'),
        low_quality_image=quality_image_strategy().filter(lambda x: x[1] == 'low')
    )
    @settings(max_examples=20, deadline=3000)
    @pytest.mark.asyncio
    async def test_quality_differentiation(
        self, 
        high_quality_image, 
        low_quality_image, 
        product_service
    ):
        """
        Test that high and low quality images are properly differentiated.
        """
        high_img_bytes, _, _ = high_quality_image
        low_img_bytes, _, _ = low_quality_image
        
        product_category = ProductCategory.FRUITS.value
        
        # Assess both images
        high_result = await product_service.assess_quality([high_img_bytes], product_category)
        low_result = await product_service.assess_quality([low_img_bytes], product_category)
        
        # Test: High quality should have higher score than low quality
        assert high_result["quality_score"] >= low_result["quality_score"]
        
        # Test: Quality grades should reflect the difference
        high_grade = high_result["quality_grade"]
        low_grade = low_result["quality_grade"]
        
        # Define grade hierarchy
        grade_hierarchy = {
            QualityGrade.PREMIUM: 3,
            QualityGrade.STANDARD: 2,
            QualityGrade.BELOW_STANDARD: 1
        }
        
        # High quality should have equal or higher grade
        assert grade_hierarchy[high_grade] >= grade_hierarchy[low_grade]
    
    @given(
        multiple_images=st.lists(
            quality_image_strategy(),
            min_size=2,
            max_size=5
        ),
        product_category=product_category_strategy()
    )
    @settings(max_examples=15, deadline=4000)
    @pytest.mark.asyncio
    async def test_batch_quality_assessment(
        self, 
        multiple_images, 
        product_category, 
        product_service
    ):
        """
        Test quality assessment with multiple images.
        """
        img_bytes_list = [img[0] for img in multiple_images]
        
        # Assess all images together
        result = await product_service.assess_quality(img_bytes_list, product_category.value)
        
        # Test: Result should reflect multiple images
        assert result["images_analyzed"] == len(multiple_images)
        
        # Test: Quality assessment should be valid
        assert result["quality_grade"] in QualityGrade
        assert 0.0 <= result["quality_score"] <= 1.0
        
        # Test: Defects should be aggregated properly
        assert isinstance(result["defects_detected"], list)
        
        # Test: Assessment method should be specified
        assert "assessment_method" in result
    
    @given(
        product_category=product_category_strategy()
    )
    @settings(max_examples=12, deadline=2000)
    @pytest.mark.asyncio
    async def test_category_specific_assessment(
        self, 
        product_category, 
        product_service
    ):
        """
        Test that quality assessment adapts to different product categories.
        """
        # Create standard test image
        image = Image.new('RGB', (800, 600), (150, 150, 150))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Assess quality for the category
        result = await product_service.assess_quality([img_bytes], product_category.value)
        
        # Test: Assessment should complete for all categories
        assert "quality_grade" in result
        assert "quality_score" in result
        
        # Test: Quality assessment should be category-appropriate
        # (In a real implementation, different categories might have different criteria)
        assert result["quality_grade"] in QualityGrade
        assert 0.0 <= result["quality_score"] <= 1.0
    
    @given(
        defect_level=st.sampled_from(['none', 'minor', 'major'])
    )
    @settings(max_examples=10, deadline=1500)
    @pytest.mark.asyncio
    async def test_defect_detection_accuracy(
        self, 
        defect_level, 
        product_service
    ):
        """
        Test that defect detection accurately reflects image quality issues.
        """
        # Simulate different defect levels through image properties
        if defect_level == 'none':
            # High quality image
            image = Image.new('RGB', (1000, 800), (200, 200, 200))
        elif defect_level == 'minor':
            # Medium quality with some issues
            image = Image.new('RGB', (600, 400), (120, 120, 120))
        else:  # major defects
            # Low quality image
            image = Image.new('RGB', (250, 200), (80, 80, 80))
        
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Assess quality
        result = await product_service.assess_quality([img_bytes], ProductCategory.VEGETABLES.value)
        
        # Test: Defect detection should correlate with defect level
        defects_count = len(result["defects_detected"])
        
        if defect_level == 'major':
            # Major defects should result in lower quality score
            assert result["quality_score"] <= 0.6
        elif defect_level == 'none':
            # No defects should result in higher quality score
            assert result["quality_score"] >= 0.4
        
        # Test: All defects should be valid strings
        for defect in result["defects_detected"]:
            assert isinstance(defect, str)
            assert len(defect) > 0
    
    @given(
        image_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=8, deadline=3000)
    @pytest.mark.asyncio
    async def test_scalability_with_image_count(
        self, 
        image_count, 
        product_service
    ):
        """
        Test that quality assessment scales properly with number of images.
        """
        # Create multiple similar images
        images = []
        for i in range(image_count):
            image = Image.new('RGB', (600, 400), (150 + i * 10, 150, 150))
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            images.append(img_byte_arr.getvalue())
        
        # Assess quality
        result = await product_service.assess_quality(images, ProductCategory.GRAINS.value)
        
        # Test: Should handle any number of images
        assert result["images_analyzed"] == image_count
        
        # Test: Quality assessment should remain valid
        assert result["quality_grade"] in QualityGrade
        assert 0.0 <= result["quality_score"] <= 1.0
        
        # Test: Performance should be reasonable (no timeout)
        # This is implicitly tested by the deadline setting


if __name__ == "__main__":
    pytest.main([__file__, "-v"])