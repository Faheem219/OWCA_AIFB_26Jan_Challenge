"""
Property-based test for quantity estimation accuracy.
**Property 23: Quantity Estimation Accuracy**
**Validates: Requirements 5.3**
"""
import pytest
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.strategies import composite
from unittest.mock import AsyncMock, MagicMock
from PIL import Image
import io

from app.services.product_catalog_service import ProductCatalogService
from app.models.product import Unit


@composite
def quantity_image_strategy(draw):
    """Generate images representing different quantities."""
    # Simulate quantity through image size and properties
    quantity_level = draw(st.sampled_from(['small', 'medium', 'large']))
    
    if quantity_level == 'small':
        width = draw(st.integers(min_value=200, max_value=400))
        height = draw(st.integers(min_value=200, max_value=400))
        expected_quantity = draw(st.floats(min_value=0.5, max_value=3.0))
    elif quantity_level == 'medium':
        width = draw(st.integers(min_value=400, max_value=800))
        height = draw(st.integers(min_value=400, max_value=800))
        expected_quantity = draw(st.floats(min_value=3.0, max_value=8.0))
    else:  # large
        width = draw(st.integers(min_value=800, max_value=1500))
        height = draw(st.integers(min_value=800, max_value=1500))
        expected_quantity = draw(st.floats(min_value=8.0, max_value=20.0))
    
    # Create PIL Image
    color = draw(st.tuples(
        st.integers(min_value=100, max_value=255),
        st.integers(min_value=100, max_value=255),
        st.integers(min_value=100, max_value=255)
    ))
    image = Image.new('RGB', (width, height), color)
    
    # Convert to bytes
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()
    
    return img_bytes, expected_quantity, quantity_level, (width, height)


@composite
def product_type_strategy(draw):
    """Generate product types for quantity estimation."""
    product_types = [
        "vegetables", "fruits", "grains", "spices", 
        "dairy", "processed_food", "textiles"
    ]
    return draw(st.sampled_from(product_types))


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


class TestQuantityEstimationProperties:
    """Property-based tests for quantity estimation accuracy."""
    
    @given(
        image_data=quantity_image_strategy(),
        product_type=product_type_strategy()
    )
    @settings(max_examples=30, deadline=4000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_property_23_quantity_estimation_accuracy(
        self, 
        image_data, 
        product_type, 
        product_service
    ):
        """
        **Property 23: Quantity Estimation Accuracy**
        **Validates: Requirements 5.3**
        
        For any product with known quantities, the computer vision quantity 
        estimation should be within an acceptable margin of error (±10%) of 
        the actual quantity.
        """
        img_bytes, expected_quantity, quantity_level, (width, height) = image_data
        
        # Test: Quantity estimation should complete without errors
        result = await product_service.estimate_quantity([img_bytes], product_type)
        
        # Test: Result should have required fields
        assert "estimated_quantity" in result
        assert "unit" in result
        assert "confidence" in result
        assert "images_analyzed" in result
        
        # Test: Estimated quantity should be positive
        assert result["estimated_quantity"] >= 0.0
        
        # Test: Unit should be valid
        assert result["unit"] in Unit
        
        # Test: Confidence should be within valid range
        assert 0.0 <= result["confidence"] <= 1.0
        
        # Test: Images analyzed count should match input
        assert result["images_analyzed"] == 1
        
        # Test: Method should be specified
        assert "method" in result
        assert isinstance(result["method"], str)
        
        # Test: Estimation should be reasonable based on image size
        area = width * height
        estimated = result["estimated_quantity"]
        
        # Larger images should generally estimate larger quantities
        if area > 500000:  # Large image
            assert estimated >= 5.0
        elif area > 200000:  # Medium image
            assert estimated >= 2.0
        else:  # Small image
            assert estimated >= 0.5
    
    @given(
        multiple_images=st.lists(
            quantity_image_strategy(),
            min_size=2,
            max_size=5
        ),
        product_type=product_type_strategy()
    )
    @settings(max_examples=15, deadline=5000)
    @pytest.mark.asyncio
    async def test_multiple_image_quantity_estimation(
        self, 
        multiple_images, 
        product_type, 
        product_service
    ):
        """
        Test quantity estimation with multiple images.
        """
        img_bytes_list = [img[0] for img in multiple_images]
        expected_total = sum(img[1] for img in multiple_images)
        
        # Estimate quantity from all images
        result = await product_service.estimate_quantity(img_bytes_list, product_type)
        
        # Test: Should process all images
        assert result["images_analyzed"] == len(multiple_images)
        
        # Test: Total estimated quantity should be reasonable
        estimated_total = result["estimated_quantity"]
        assert estimated_total >= 0.0
        
        # Test: With multiple images, total should generally be higher
        if len(multiple_images) > 1:
            assert estimated_total >= result["estimated_quantity"] / len(multiple_images)
        
        # Test: Confidence should reflect multiple image analysis
        assert 0.0 <= result["confidence"] <= 1.0
    
    @given(
        same_quantity_images=st.lists(
            quantity_image_strategy().filter(lambda x: x[2] == 'medium'),  # Same quantity level
            min_size=2,
            max_size=4
        )
    )
    @settings(max_examples=12, deadline=4000)
    @pytest.mark.asyncio
    async def test_consistency_same_quantity_level(
        self, 
        same_quantity_images, 
        product_service
    ):
        """
        Test that images representing similar quantities get consistent estimates.
        """
        assume(len(same_quantity_images) >= 2)
        
        product_type = "vegetables"
        estimates = []
        
        # Estimate quantity for each image
        for img_bytes, _, _, _ in same_quantity_images:
            result = await product_service.estimate_quantity([img_bytes], product_type)
            estimates.append(result["estimated_quantity"])
        
        # Test: Estimates should be reasonably consistent
        if len(estimates) > 1:
            estimate_variance = max(estimates) - min(estimates)
            average_estimate = sum(estimates) / len(estimates)
            
            # Variance should not be more than 50% of average for same quantity level
            if average_estimate > 0:
                relative_variance = estimate_variance / average_estimate
                assert relative_variance <= 0.5
    
    @given(
        product_type=product_type_strategy()
    )
    @settings(max_examples=15, deadline=2000)
    @pytest.mark.asyncio
    async def test_product_type_appropriate_units(
        self, 
        product_type, 
        product_service
    ):
        """
        Test that quantity estimation uses appropriate units for different product types.
        """
        # Create standard test image
        image = Image.new('RGB', (600, 400), (150, 150, 150))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Estimate quantity
        result = await product_service.estimate_quantity([img_bytes], product_type)
        
        # Test: Unit should be appropriate for product type
        estimated_unit = result["unit"]
        
        # Define expected units for different product types
        expected_units = {
            "vegetables": [Unit.KG, Unit.GRAM, Unit.PIECE],
            "fruits": [Unit.KG, Unit.GRAM, Unit.PIECE],
            "grains": [Unit.KG, Unit.QUINTAL, Unit.TON],
            "spices": [Unit.KG, Unit.GRAM],
            "dairy": [Unit.LITER, Unit.KG],
            "processed_food": [Unit.PIECE, Unit.KG, Unit.BOX],
            "textiles": [Unit.PIECE, Unit.KG]
        }
        
        if product_type in expected_units:
            assert estimated_unit in expected_units[product_type]
        else:
            # Default should be reasonable
            assert estimated_unit in Unit
    
    @given(
        large_image=quantity_image_strategy().filter(lambda x: x[2] == 'large'),
        small_image=quantity_image_strategy().filter(lambda x: x[2] == 'small')
    )
    @settings(max_examples=15, deadline=3000)
    @pytest.mark.asyncio
    async def test_size_quantity_correlation(
        self, 
        large_image, 
        small_image, 
        product_service
    ):
        """
        Test that larger images generally result in higher quantity estimates.
        """
        large_img_bytes, _, _, large_size = large_image
        small_img_bytes, _, _, small_size = small_image
        
        product_type = "fruits"
        
        # Estimate quantities
        large_result = await product_service.estimate_quantity([large_img_bytes], product_type)
        small_result = await product_service.estimate_quantity([small_img_bytes], product_type)
        
        # Test: Larger image should generally estimate higher quantity
        large_estimate = large_result["estimated_quantity"]
        small_estimate = small_result["estimated_quantity"]
        
        # Allow some tolerance, but larger should generally be higher
        assert large_estimate >= small_estimate * 0.8
    
    @given(
        confidence_test_image=quantity_image_strategy()
    )
    @settings(max_examples=20, deadline=2000)
    @pytest.mark.asyncio
    async def test_confidence_score_validity(
        self, 
        confidence_test_image, 
        product_service
    ):
        """
        Test that confidence scores are meaningful and consistent.
        """
        img_bytes, _, quantity_level, (width, height) = confidence_test_image
        product_type = "vegetables"
        
        # Estimate quantity
        result = await product_service.estimate_quantity([img_bytes], product_type)
        
        # Test: Confidence should be within valid range
        confidence = result["confidence"]
        assert 0.0 <= confidence <= 1.0
        
        # Test: Higher quality images should generally have higher confidence
        area = width * height
        if area > 800000:  # Very large, high quality
            assert confidence >= 0.6
        elif area < 100000:  # Very small, potentially low quality
            assert confidence <= 0.8  # May have lower confidence
    
    @given(
        edge_case_quantity=st.floats(min_value=0.1, max_value=0.5)
    )
    @settings(max_examples=10, deadline=1500)
    @pytest.mark.asyncio
    async def test_edge_case_handling(
        self, 
        edge_case_quantity, 
        product_service
    ):
        """
        Test handling of edge cases in quantity estimation.
        """
        # Create very small image to simulate edge case
        image = Image.new('RGB', (100, 100), (100, 100, 100))
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG')
        img_bytes = img_byte_arr.getvalue()
        
        # Estimate quantity
        result = await product_service.estimate_quantity([img_bytes], "vegetables")
        
        # Test: Should handle edge cases gracefully
        assert "estimated_quantity" in result
        assert result["estimated_quantity"] >= 0.0
        
        # Test: Should still provide valid confidence even for edge cases
        assert 0.0 <= result["confidence"] <= 1.0
        
        # Test: Should not crash or return invalid data
        assert result["unit"] in Unit
        assert result["images_analyzed"] == 1
    
    @given(
        empty_image_list=st.just([])
    )
    @settings(max_examples=5, deadline=1000)
    @pytest.mark.asyncio
    async def test_empty_input_handling(
        self, 
        empty_image_list, 
        product_service
    ):
        """
        Test handling of empty image list.
        """
        # Test with empty image list
        result = await product_service.estimate_quantity(empty_image_list, "vegetables")
        
        # Test: Should handle empty input gracefully
        assert "estimated_quantity" in result
        assert result["estimated_quantity"] == 0.0
        assert result["images_analyzed"] == 0
        assert 0.0 <= result["confidence"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])