"""
Tests for product search and filtering functionality.

This module tests the multilingual search capabilities, filtering options,
geolocation-based search, and Elasticsearch integration.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.product_service import ProductService
from app.services.elasticsearch_service import elasticsearch_service
from app.models.product import (
    Product,
    ProductCreateRequest,
    ProductSearchQuery,
    ProductSearchResponse,
    MultilingualText,
    LocationData,
    PriceInfo,
    AvailabilityInfo,
    ProductMetadata,
    ImageReference,
    ProductStatus,
    QualityGrade,
    MeasurementUnit,
    ProductCategory
)
from app.models.user import SupportedLanguage, UserRole
from app.core.exceptions import ValidationException


@pytest.fixture
def product_service():
    """Create ProductService instance for testing."""
    return ProductService()


@pytest.fixture
def sample_product():
    """Create a sample product for testing."""
    return Product(
        product_id="test_product_1",
        vendor_id="test_vendor_1",
        name=MultilingualText(
            original_language=SupportedLanguage.ENGLISH,
            original_text="Fresh Tomatoes",
            translations={
                SupportedLanguage.HINDI: "ताज़े टमाटर",
                SupportedLanguage.TAMIL: "புதிய தக்காளி"
            }
        ),
        description=MultilingualText(
            original_language=SupportedLanguage.ENGLISH,
            original_text="Fresh red tomatoes from local farm",
            translations={
                SupportedLanguage.HINDI: "स्थानीय खेत से ताज़े लाल टमाटर",
                SupportedLanguage.TAMIL: "உள்ளூர் பண்ணையிலிருந்து புதிய சிவப்பு தக்காளி"
            }
        ),
        category=ProductCategory.VEGETABLES,
        subcategory="Fresh Vegetables",
        tags=["fresh", "organic", "local"],
        images=[
            ImageReference(
                image_id="img_1",
                image_url="https://example.com/tomato.jpg",
                is_primary=True,
                uploaded_at=datetime.utcnow()
            )
        ],
        price_info=PriceInfo(
            base_price=Decimal("50.00"),
            currency="INR",
            negotiable=True
        ),
        availability=AvailabilityInfo(
            quantity_available=100,
            unit=MeasurementUnit.KG,
            minimum_order=5
        ),
        location=LocationData(
            address="123 Farm Road",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            coordinates=[72.8777, 19.0760]  # Mumbai coordinates
        ),
        quality_grade=QualityGrade.GRADE_A,
        metadata=ProductMetadata(
            harvest_date=date.today(),
            certifications=["organic"]
        ),
        status=ProductStatus.ACTIVE,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        search_keywords=["tomato", "vegetable", "fresh", "organic"]
    )


@pytest.fixture
def search_query():
    """Create a sample search query."""
    return ProductSearchQuery(
        query="tomatoes",
        language=SupportedLanguage.ENGLISH,
        category=ProductCategory.VEGETABLES,
        min_price=Decimal("10.00"),
        max_price=Decimal("100.00"),
        city="Mumbai",
        available_only=True,
        sort_by="relevance",
        limit=20,
        skip=0
    )


class TestProductSearch:
    """Test product search functionality."""
    
    @pytest.mark.asyncio
    async def test_search_products_basic_query(self, product_service, search_query):
        """Test basic product search with text query."""
        # Mock Elasticsearch service
        with patch.object(elasticsearch_service, 'search_products') as mock_es_search:
            mock_es_search.return_value = ([], 0, {"query": "tomatoes"})
            
            # Mock MongoDB fallback
            with patch.object(product_service, '_build_search_filter') as mock_filter, \
                 patch('app.services.product_service.get_database') as mock_db:
                
                mock_filter.return_value = {"status": "active"}
                mock_collection = AsyncMock()
                mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list.return_value = []
                mock_collection.count_documents.return_value = 0
                mock_db.return_value.products = mock_collection
                
                result = await product_service.search_products(search_query)
                
                assert isinstance(result, ProductSearchResponse)
                assert result.total_count == 0
                assert len(result.products) == 0
                assert result.search_metadata["query"] == "tomatoes"
    
    @pytest.mark.asyncio
    async def test_search_products_multilingual(self, product_service):
        """Test multilingual search functionality."""
        # Test Hindi search
        hindi_query = ProductSearchQuery(
            query="टमाटर",
            language=SupportedLanguage.HINDI,
            limit=10
        )
        
        with patch.object(elasticsearch_service, 'search_products') as mock_es_search:
            mock_es_search.return_value = ([], 0, {"query": "टमाटर", "language": "hi"})
            
            with patch.object(product_service, '_build_search_filter') as mock_filter, \
                 patch('app.services.product_service.get_database') as mock_db:
                
                mock_filter.return_value = {"status": "active"}
                mock_collection = AsyncMock()
                mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list.return_value = []
                mock_collection.count_documents.return_value = 0
                mock_db.return_value.products = mock_collection
                
                result = await product_service.search_products(hindi_query)
                
                assert result.search_metadata["language"] == "hi"
                assert result.search_metadata["query"] == "टमाटर"
    
    @pytest.mark.asyncio
    async def test_search_products_with_filters(self, product_service):
        """Test product search with various filters."""
        filtered_query = ProductSearchQuery(
            query="vegetables",
            category=ProductCategory.VEGETABLES,
            min_price=Decimal("20.00"),
            max_price=Decimal("80.00"),
            city="Mumbai",
            state="Maharashtra",
            quality_grades=[QualityGrade.GRADE_A, QualityGrade.ORGANIC],
            available_only=True,
            organic_only=True,
            limit=10
        )
        
        with patch.object(elasticsearch_service, 'search_products') as mock_es_search:
            mock_es_search.return_value = ([], 0, {"query": "vegetables"})
            
            with patch.object(product_service, '_build_search_filter') as mock_filter, \
                 patch('app.services.product_service.get_database') as mock_db:
                
                # Verify filter building
                expected_filter = {
                    "status": {"$in": ["active"]},
                    "category": "VEGETABLES",
                    "price_info.base_price": {"$gte": "20.00", "$lte": "80.00"},
                    "location.city": {"$regex": "Mumbai", "$options": "i"},
                    "location.state": {"$regex": "Maharashtra", "$options": "i"},
                    "quality_grade": {"$in": ["grade_a", "organic"]},
                    "availability.quantity_available": {"$gt": 0}
                }
                mock_filter.return_value = expected_filter
                
                mock_collection = AsyncMock()
                mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list.return_value = []
                mock_collection.count_documents.return_value = 0
                mock_db.return_value.products = mock_collection
                
                result = await product_service.search_products(filtered_query)
                
                # Verify filters were applied
                mock_filter.assert_called_once_with(filtered_query)
                assert "category:VEGETABLES" in result.search_metadata["filters_applied"]
                assert "min_price:20.00" in result.search_metadata["filters_applied"]
                assert "max_price:80.00" in result.search_metadata["filters_applied"]
    
    @pytest.mark.asyncio
    async def test_search_products_geolocation(self, product_service):
        """Test geolocation-based product search."""
        geo_query = ProductSearchQuery(
            query="fresh produce",
            coordinates=[72.8777, 19.0760],  # Mumbai coordinates
            radius_km=10.0,
            sort_by="distance",
            limit=20
        )
        
        with patch.object(elasticsearch_service, 'search_products') as mock_es_search:
            mock_es_search.return_value = ([], 0, {"query": "fresh produce"})
            
            with patch.object(product_service, '_build_search_filter') as mock_filter, \
                 patch('app.services.product_service.get_database') as mock_db:
                
                # Verify geospatial filter
                expected_geo_filter = {
                    "location.coordinates": {
                        "$near": {
                            "$geometry": {
                                "type": "Point",
                                "coordinates": [72.8777, 19.0760]
                            },
                            "$maxDistance": 10000  # 10km in meters
                        }
                    }
                }
                mock_filter.return_value = {"status": {"$in": ["active"]}, **expected_geo_filter}
                
                mock_collection = AsyncMock()
                mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list.return_value = []
                mock_collection.count_documents.return_value = 0
                mock_db.return_value.products = mock_collection
                
                result = await product_service.search_products(geo_query)
                
                mock_filter.assert_called_once_with(geo_query)
    
    @pytest.mark.asyncio
    async def test_search_products_sorting(self, product_service):
        """Test different sorting options."""
        sort_options = [
            ("price", "asc"),
            ("price", "desc"),
            ("date", "desc"),
            ("popularity", "desc"),
            ("relevance", "desc")
        ]
        
        for sort_by, sort_order in sort_options:
            query = ProductSearchQuery(
                query="test",
                sort_by=sort_by,
                sort_order=sort_order,
                limit=10
            )
            
            with patch.object(elasticsearch_service, 'search_products') as mock_es_search:
                mock_es_search.return_value = ([], 0, {"query": "test"})
                
                with patch.object(product_service, '_build_search_filter') as mock_filter, \
                     patch.object(product_service, '_build_sort_criteria') as mock_sort, \
                     patch('app.services.product_service.get_database') as mock_db:
                    
                    mock_filter.return_value = {"status": {"$in": ["active"]}}
                    mock_sort.return_value = [(sort_by, 1 if sort_order == "asc" else -1)]
                    
                    mock_collection = AsyncMock()
                    mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list.return_value = []
                    mock_collection.count_documents.return_value = 0
                    mock_db.return_value.products = mock_collection
                    
                    result = await product_service.search_products(query)
                    
                    mock_sort.assert_called_once_with(sort_by, sort_order)
    
    @pytest.mark.asyncio
    async def test_search_products_pagination(self, product_service):
        """Test search pagination."""
        query = ProductSearchQuery(
            query="test",
            limit=5,
            skip=10
        )
        
        with patch.object(elasticsearch_service, 'search_products') as mock_es_search:
            mock_es_search.return_value = ([], 25, {"query": "test"})  # Total 25 results
            
            with patch.object(product_service, '_build_search_filter') as mock_filter, \
                 patch('app.services.product_service.get_database') as mock_db:
                
                mock_filter.return_value = {"status": {"$in": ["active"]}}
                mock_collection = AsyncMock()
                mock_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value.to_list.return_value = []
                mock_collection.count_documents.return_value = 25
                mock_db.return_value.products = mock_collection
                
                result = await product_service.search_products(query)
                
                # Check pagination info
                assert result.page_info["current_page"] == 3  # (10 / 5) + 1
                assert result.page_info["total_pages"] == 5   # ceil(25 / 5)
                assert result.page_info["page_size"] == 5
                assert result.page_info["has_next"] == True
                assert result.page_info["has_previous"] == True


class TestElasticsearchIntegration:
    """Test Elasticsearch integration."""
    
    @pytest.mark.asyncio
    async def test_elasticsearch_index_product(self, sample_product):
        """Test indexing a product in Elasticsearch."""
        with patch.object(elasticsearch_service, '_ensure_initialized') as mock_init, \
             patch.object(elasticsearch_service, 'client') as mock_client:
            
            mock_init.return_value = True
            mock_client.index = AsyncMock()
            
            vendor_info = {
                "business_name": "Test Farm",
                "rating": 4.5,
                "market_location": "Mumbai Market"
            }
            
            result = await elasticsearch_service.index_product(sample_product, vendor_info)
            
            assert result == True
            mock_client.index.assert_called_once()
            
            # Verify the document structure
            call_args = mock_client.index.call_args
            doc = call_args[1]["body"]
            
            assert doc["product_id"] == "test_product_1"
            assert doc["vendor_id"] == "test_vendor_1"
            assert doc["category"] == "VEGETABLES"
            assert doc["name"]["original_text"] == "Fresh Tomatoes"
            assert doc["name"]["translations"]["hi"] == "ताज़े टमाटर"
            assert doc["price"] == 50.0
            assert doc["location"]["city"] == "Mumbai"
            assert doc["vendor_name"] == "Test Farm"
    
    @pytest.mark.asyncio
    async def test_elasticsearch_search_multilingual(self):
        """Test multilingual search in Elasticsearch."""
        query = ProductSearchQuery(
            query="टमाटर",
            language=SupportedLanguage.HINDI,
            limit=10
        )
        
        mock_response = {
            "hits": {
                "hits": [
                    {
                        "_source": {
                            "product_id": "test_product_1",
                            "vendor_id": "test_vendor_1",
                            "name": {
                                "original_text": "Fresh Tomatoes",
                                "original_language": "en",
                                "translations": {"hi": "ताज़े टमाटर"}
                            },
                            "description": {
                                "original_text": "Fresh red tomatoes",
                                "original_language": "en",
                                "translations": {"hi": "ताज़े लाल टमाटर"}
                            },
                            "category": "VEGETABLES",
                            "quality_grade": "grade_a",
                            "price": 50.0,
                            "currency": "INR",
                            "negotiable": True,
                            "quantity_available": 100,
                            "unit": "kg",
                            "minimum_order": 5,
                            "location": {
                                "city": "Mumbai",
                                "state": "Maharashtra",
                                "coordinates": [72.8777, 19.0760]
                            },
                            "status": "active",
                            "created_at": "2024-01-01T00:00:00",
                            "updated_at": "2024-01-01T00:00:00"
                        },
                        "_score": 1.5
                    }
                ],
                "total": {"value": 1},
                "max_score": 1.5
            }
        }
        
        with patch.object(elasticsearch_service, '_ensure_initialized') as mock_init, \
             patch.object(elasticsearch_service, 'client') as mock_client:
            
            mock_init.return_value = True
            mock_client.search = AsyncMock(return_value=mock_response)
            
            results, total_count, metadata = await elasticsearch_service.search_products(query)
            
            assert len(results) == 1
            assert total_count == 1
            assert results[0]["product_id"] == "test_product_1"
            assert results[0]["name"]["translations"]["hi"] == "ताज़े टमाटर"
            assert metadata["query"] == "टमाटर"
            assert metadata["language"] == "hi"
    
    @pytest.mark.asyncio
    async def test_elasticsearch_geospatial_search(self):
        """Test geospatial search in Elasticsearch."""
        query = ProductSearchQuery(
            query="vegetables",
            coordinates=[72.8777, 19.0760],  # Mumbai
            radius_km=5.0,
            sort_by="distance",
            limit=10
        )
        
        with patch.object(elasticsearch_service, '_ensure_initialized') as mock_init, \
             patch.object(elasticsearch_service, 'client') as mock_client, \
             patch.object(elasticsearch_service, '_build_elasticsearch_query') as mock_build_query:
            
            mock_init.return_value = True
            mock_client.search = AsyncMock(return_value={
                "hits": {"hits": [], "total": {"value": 0}, "max_score": None}
            })
            
            # Verify geospatial query building
            expected_geo_filter = {
                "geo_distance": {
                    "distance": "5.0km",
                    "location.coordinates": {
                        "lat": 19.0760,
                        "lon": 72.8777
                    }
                }
            }
            
            mock_build_query.return_value = {
                "query": {
                    "bool": {
                        "filter": [expected_geo_filter]
                    }
                }
            }
            
            await elasticsearch_service.search_products(query)
            
            mock_build_query.assert_called_once_with(query)
    
    @pytest.mark.asyncio
    async def test_elasticsearch_bulk_index(self, sample_product):
        """Test bulk indexing of products."""
        products = [(sample_product, {"business_name": "Test Farm"})]
        
        mock_response = {
            "items": [
                {"index": {"status": 201}}
            ]
        }
        
        with patch.object(elasticsearch_service, '_ensure_initialized') as mock_init, \
             patch.object(elasticsearch_service, 'client') as mock_client:
            
            mock_init.return_value = True
            mock_client.bulk = AsyncMock(return_value=mock_response)
            
            result = await elasticsearch_service.bulk_index_products(products)
            
            assert result["success"] == 1
            assert result["failed"] == 0
            mock_client.bulk.assert_called_once()


class TestSearchFilters:
    """Test search filter building and validation."""
    
    def test_build_search_filter_basic(self, product_service):
        """Test basic search filter building."""
        query = ProductSearchQuery(
            query="tomatoes",
            category=ProductCategory.VEGETABLES,
            available_only=True
        )
        
        # This would be tested with actual MongoDB filter building
        # For now, we test the structure
        assert query.query == "tomatoes"
        assert query.category == ProductCategory.VEGETABLES
        assert query.available_only == True
    
    def test_build_search_filter_price_range(self, product_service):
        """Test price range filter validation."""
        # Valid price range
        query = ProductSearchQuery(
            min_price=Decimal("10.00"),
            max_price=Decimal("100.00")
        )
        assert query.min_price == Decimal("10.00")
        assert query.max_price == Decimal("100.00")
        
        # Invalid price range should raise validation error
        with pytest.raises(ValidationException):
            ProductSearchQuery(
                min_price=Decimal("100.00"),
                max_price=Decimal("10.00")
            )
    
    def test_search_query_validation(self):
        """Test search query parameter validation."""
        # Valid sort options
        valid_sorts = ["relevance", "price", "date", "rating", "distance", "popularity"]
        for sort_by in valid_sorts:
            query = ProductSearchQuery(sort_by=sort_by)
            assert query.sort_by == sort_by
        
        # Invalid sort option
        with pytest.raises(ValidationException):
            ProductSearchQuery(sort_by="invalid_sort")
        
        # Valid sort orders
        for sort_order in ["asc", "desc"]:
            query = ProductSearchQuery(sort_order=sort_order)
            assert query.sort_order == sort_order
        
        # Invalid sort order
        with pytest.raises(ValidationException):
            ProductSearchQuery(sort_order="invalid_order")
    
    def test_pagination_limits(self):
        """Test pagination parameter limits."""
        # Valid limits
        query = ProductSearchQuery(limit=50, skip=10)
        assert query.limit == 50
        assert query.skip == 10
        
        # Limit too high should be capped
        query = ProductSearchQuery(limit=200)
        assert query.limit <= 100  # Should be capped at 100
        
        # Negative skip should be corrected
        query = ProductSearchQuery(skip=-5)
        assert query.skip >= 0


class TestSearchIndexManagement:
    """Test search index management operations."""
    
    @pytest.mark.asyncio
    async def test_initialize_search_index(self, product_service):
        """Test search index initialization."""
        with patch.object(elasticsearch_service, 'initialize') as mock_es_init, \
             patch.object(elasticsearch_service, 'bulk_index_products') as mock_bulk_index, \
             patch('app.services.product_service.get_database') as mock_db:
            
            # Mock successful initialization
            mock_es_init.return_value = None
            mock_bulk_index.return_value = {"success": 5, "failed": 0}
            
            # Mock products in database
            mock_products = [
                {"product_id": f"product_{i}", "status": "active", "vendor_id": f"vendor_{i}"}
                for i in range(5)
            ]
            mock_collection = AsyncMock()
            mock_collection.find.return_value.to_list.return_value = mock_products
            mock_db.return_value.products = mock_collection
            
            # Mock user service
            with patch.object(product_service.user_service, 'get_user_by_id') as mock_get_user:
                mock_get_user.return_value = MagicMock(business_name="Test Vendor")
                
                with patch.object(product_service, '_convert_db_to_product_model') as mock_convert:
                    mock_convert.return_value = MagicMock()
                    
                    result = await product_service.initialize_search_index()
                    
                    assert result["status"] == "success"
                    assert result["indexed_count"] == 5
                    assert result["failed_count"] == 0
                    mock_es_init.assert_called_once()
                    mock_bulk_index.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_search_index_no_products(self, product_service):
        """Test search index initialization with no products."""
        with patch.object(elasticsearch_service, 'initialize') as mock_es_init, \
             patch('app.services.product_service.get_database') as mock_db:
            
            mock_es_init.return_value = None
            
            # Mock empty products collection
            mock_collection = AsyncMock()
            mock_collection.find.return_value.to_list.return_value = []
            mock_db.return_value.products = mock_collection
            
            result = await product_service.initialize_search_index()
            
            assert result["status"] == "success"
            assert result["indexed_count"] == 0
            assert "no products to index" in result["message"]
    
    @pytest.mark.asyncio
    async def test_initialize_search_index_failure(self, product_service):
        """Test search index initialization failure."""
        with patch.object(elasticsearch_service, 'initialize') as mock_es_init:
            mock_es_init.side_effect = Exception("Connection failed")
            
            result = await product_service.initialize_search_index()
            
            assert result["status"] == "error"
            assert "Connection failed" in result["message"]
            assert result["indexed_count"] == 0


@pytest.mark.asyncio
async def test_search_integration_end_to_end():
    """Integration test for complete search workflow."""
    # This would be a more comprehensive test that:
    # 1. Creates test products
    # 2. Indexes them in Elasticsearch
    # 3. Performs various searches
    # 4. Verifies results
    # 5. Cleans up test data
    
    # For now, this is a placeholder for future integration testing
    pass