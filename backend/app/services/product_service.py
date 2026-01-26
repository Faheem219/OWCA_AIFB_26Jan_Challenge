"""
Product service for the Multilingual Mandi Marketplace Platform.

This service handles product management, CRUD operations, and search functionality.
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import math

from app.core.config import settings
from app.core.database import get_database
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    AuthorizationException,
)
from app.models.product import (
    Product,
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductSearchQuery,
    ProductSearchResponse,
    MultilingualText,
    ImageReference,
    LocationData,
    PriceInfo,
    AvailabilityInfo,
    ProductMetadata,
    ProductStatus,
    QualityGrade,
    MeasurementUnit,
)
from app.models.user import UserRole, SupportedLanguage
from app.services.user_service import UserService
from app.services.translation_service import TranslationService
from app.services.elasticsearch_service import elasticsearch_service

logger = logging.getLogger(__name__)


class ProductService:
    """Product service class."""
    
    def __init__(self):
        self.user_service = UserService()
        self.translation_service = TranslationService()
    
    async def initialize_search_index(self) -> Dict[str, Any]:
        """
        Initialize Elasticsearch and index existing products.
        
        Returns:
            Initialization status and statistics
        """
        try:
            # Initialize Elasticsearch
            await elasticsearch_service.initialize()
            
            # Get all active products from MongoDB
            db = await get_database()
            cursor = db.products.find({"status": {"$in": [ProductStatus.ACTIVE.value]}})
            products = await cursor.to_list(length=None)
            
            if not products:
                return {
                    "status": "success",
                    "message": "Elasticsearch initialized, no products to index",
                    "indexed_count": 0
                }
            
            # Prepare products for bulk indexing
            products_to_index = []
            for product_dict in products:
                try:
                    # Convert to Product model
                    product = await self._convert_db_to_product_model(product_dict)
                    
                    # Get vendor info
                    vendor = await self.user_service.get_user_by_id(product.vendor_id)
                    vendor_info = {
                        "business_name": getattr(vendor, 'business_name', None),
                        "rating": getattr(vendor, 'rating', None),
                        "market_location": getattr(vendor, 'market_location', None)
                    }
                    
                    products_to_index.append((product, vendor_info))
                    
                except Exception as e:
                    logger.warning(f"Failed to prepare product {product_dict.get('product_id')} for indexing: {e}")
            
            # Bulk index products
            if products_to_index:
                result = await elasticsearch_service.bulk_index_products(products_to_index)
                
                return {
                    "status": "success",
                    "message": f"Elasticsearch initialized and products indexed",
                    "total_products": len(products),
                    "indexed_count": result["success"],
                    "failed_count": result["failed"]
                }
            else:
                return {
                    "status": "success",
                    "message": "Elasticsearch initialized, no valid products to index",
                    "indexed_count": 0
                }
                
        except Exception as e:
            logger.error(f"Failed to initialize search index: {e}")
            return {
                "status": "error",
                "message": f"Failed to initialize search index: {str(e)}",
                "indexed_count": 0
            }
    
    async def create_product(
        self,
        product_data: ProductCreateRequest,
        vendor_id: str,
        requesting_user_id: str
    ) -> ProductResponse:
        """
        Create a new product listing.
        
        Args:
            product_data: Product creation data
            vendor_id: Vendor ID who owns the product
            requesting_user_id: ID of user making the request
            
        Returns:
            Created product response
            
        Raises:
            AuthorizationException: If user not authorized
            ValidationException: If product data is invalid
            NotFoundException: If vendor not found
        """
        try:
            # Check authorization - only vendors can create products for themselves
            if vendor_id != requesting_user_id:
                raise AuthorizationException("You can only create products for your own vendor account")
            
            # Verify vendor exists and is active
            vendor = await self.user_service.get_user_by_id(vendor_id)
            if not vendor:
                raise NotFoundException("Vendor not found")
            
            if vendor.role != UserRole.VENDOR:
                raise ValidationException("Only vendors can create product listings")
            
            if not vendor.is_active:
                raise ValidationException("Vendor account is not active")
            
            # Validate required fields
            self._validate_product_data(product_data)
            
            # Generate product ID
            product_id = str(ObjectId())
            
            # Create multilingual text objects
            name_ml = MultilingualText(
                original_language=product_data.name_language,
                original_text=product_data.name_text,
                translations={},
                auto_translated=False
            )
            
            description_ml = MultilingualText(
                original_language=product_data.description_language,
                original_text=product_data.description_text,
                translations={},
                auto_translated=False
            )
            
            # Create location data (use vendor location if not provided)
            location_data = await self._create_product_location(product_data, vendor)
            
            # Create price info
            price_info = PriceInfo(
                base_price=product_data.base_price,
                currency="INR",
                negotiable=product_data.negotiable,
                bulk_discount=None,
                seasonal_pricing=None
            )
            
            # Create availability info
            availability_info = AvailabilityInfo(
                quantity_available=product_data.quantity_available,
                unit=product_data.unit,
                minimum_order=product_data.minimum_order,
                maximum_order=product_data.maximum_order,
                available_from=datetime.utcnow(),
                available_until=None,
                restocking_date=None
            )
            
            # Create metadata
            metadata = ProductMetadata(
                harvest_date=product_data.harvest_date,
                expiry_date=product_data.expiry_date,
                storage_conditions=None,
                certifications=product_data.certifications,
                origin=product_data.origin,
                variety=product_data.variety,
                processing_method=None
            )
            
            # Process images
            images = await self._process_product_images(product_data.image_urls)
            
            # Create product
            product = Product(
                product_id=product_id,
                vendor_id=vendor_id,
                name=name_ml,
                description=description_ml,
                category=product_data.category,
                subcategory=product_data.subcategory,
                tags=product_data.tags,
                images=images,
                price_info=price_info,
                availability=availability_info,
                location=location_data,
                quality_grade=product_data.quality_grade,
                metadata=metadata,
                status=ProductStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                views_count=0,
                favorites_count=0,
                search_keywords=self._generate_search_keywords(product_data),
                featured=False
            )
            
            # Save to database
            db = await get_database()
            product_dict = product.model_dump()
            
            # Convert nested models to dicts for MongoDB
            product_dict = self._prepare_product_for_db(product_dict)
            
            result = await db.products.insert_one(product_dict)
            
            if not result.inserted_id:
                raise ValidationException("Failed to create product")
            
            # Auto-translate product name and description
            await self._auto_translate_product(product_id, name_ml, description_ml)
            
            # Index product in Elasticsearch
            try:
                vendor_info = {
                    "business_name": getattr(vendor, 'business_name', None),
                    "rating": getattr(vendor, 'rating', None),
                    "market_location": getattr(vendor, 'market_location', None)
                }
                await elasticsearch_service.index_product(product, vendor_info)
            except Exception as e:
                logger.warning(f"Failed to index product in Elasticsearch: {e}")
            
            # Get created product
            created_product = await db.products.find_one({"product_id": product_id})
            return await self._convert_product_to_response(created_product)
            
        except (AuthorizationException, ValidationException, NotFoundException):
            raise
        except Exception as e:
            logger.error(f"Failed to create product: {e}")
            raise ValidationException("Product creation failed")
    
    async def get_product_by_id(
        self,
        product_id: str,
        language: SupportedLanguage = SupportedLanguage.ENGLISH,
        increment_views: bool = True
    ) -> Optional[ProductResponse]:
        """
        Get product by ID.
        
        Args:
            product_id: Product ID
            language: Preferred language for response
            increment_views: Whether to increment view count
            
        Returns:
            Product response or None if not found
        """
        try:
            db = await get_database()
            product = await db.products.find_one({"product_id": product_id})
            
            if not product:
                return None
            
            # Increment view count if requested
            if increment_views:
                await db.products.update_one(
                    {"product_id": product_id},
                    {"$inc": {"views_count": 1}}
                )
                product["views_count"] = product.get("views_count", 0) + 1
            
            return await self._convert_product_to_response(product, language)
            
        except Exception as e:
            logger.error(f"Failed to get product {product_id}: {e}")
            return None
    
    async def update_product(
        self,
        product_id: str,
        updates: ProductUpdateRequest,
        requesting_user_id: str
    ) -> ProductResponse:
        """
        Update an existing product.
        
        Args:
            product_id: Product ID to update
            updates: Product updates
            requesting_user_id: ID of user making the request
            
        Returns:
            Updated product response
            
        Raises:
            NotFoundException: If product not found
            AuthorizationException: If user not authorized
            ValidationException: If update data is invalid
        """
        try:
            db = await get_database()
            product = await db.products.find_one({"product_id": product_id})
            
            if not product:
                raise NotFoundException("Product not found")
            
            # Check authorization - only product owner can update
            if product["vendor_id"] != requesting_user_id:
                raise AuthorizationException("You can only update your own products")
            
            # Prepare update data
            update_data = {"updated_at": datetime.utcnow()}
            
            # Update basic fields
            if updates.subcategory is not None:
                update_data["subcategory"] = updates.subcategory
            
            if updates.tags is not None:
                update_data["tags"] = updates.tags
                update_data["search_keywords"] = self._generate_search_keywords_from_tags(updates.tags)
            
            # Update multilingual text fields
            if updates.name_text is not None and updates.name_language is not None:
                name_ml = MultilingualText(**product["name"])
                if updates.name_language == name_ml.original_language:
                    name_ml.original_text = updates.name_text
                else:
                    name_ml.add_translation(updates.name_language, updates.name_text)
                update_data["name"] = name_ml.model_dump()
            
            if updates.description_text is not None and updates.description_language is not None:
                desc_ml = MultilingualText(**product["description"])
                if updates.description_language == desc_ml.original_language:
                    desc_ml.original_text = updates.description_text
                else:
                    desc_ml.add_translation(updates.description_language, updates.description_text)
                update_data["description"] = desc_ml.model_dump()
            
            # Update pricing
            if any([updates.base_price is not None, updates.negotiable is not None]):
                price_info = PriceInfo(**product["price_info"])
                if updates.base_price is not None:
                    price_info.base_price = updates.base_price
                if updates.negotiable is not None:
                    price_info.negotiable = updates.negotiable
                update_data["price_info"] = price_info.model_dump()
            
            # Update availability
            availability_fields = [
                updates.quantity_available, updates.minimum_order, updates.maximum_order
            ]
            if any(field is not None for field in availability_fields):
                availability = AvailabilityInfo(**product["availability"])
                if updates.quantity_available is not None:
                    availability.quantity_available = updates.quantity_available
                if updates.minimum_order is not None:
                    availability.minimum_order = updates.minimum_order
                if updates.maximum_order is not None:
                    availability.maximum_order = updates.maximum_order
                update_data["availability"] = availability.model_dump()
            
            # Update quality and metadata
            if updates.quality_grade is not None:
                update_data["quality_grade"] = updates.quality_grade.value
            
            metadata_fields = [
                updates.harvest_date, updates.expiry_date, updates.certifications,
                updates.origin, updates.variety
            ]
            if any(field is not None for field in metadata_fields):
                metadata = ProductMetadata(**product["metadata"])
                if updates.harvest_date is not None:
                    metadata.harvest_date = updates.harvest_date
                if updates.expiry_date is not None:
                    metadata.expiry_date = updates.expiry_date
                if updates.certifications is not None:
                    metadata.certifications = updates.certifications
                if updates.origin is not None:
                    metadata.origin = updates.origin
                if updates.variety is not None:
                    metadata.variety = updates.variety
                update_data["metadata"] = metadata.model_dump()
            
            # Update status
            if updates.status is not None:
                update_data["status"] = updates.status.value
            
            # Update location if provided
            if updates.location_address is not None or updates.market_name is not None:
                location = LocationData(**product["location"])
                if updates.location_address is not None:
                    location.address = updates.location_address
                if updates.market_name is not None:
                    location.market_name = updates.market_name
                update_data["location"] = location.model_dump()
            
            # Update product in database
            result = await db.products.update_one(
                {"product_id": product_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise ValidationException("No changes were made")
            
            # Get updated product
            updated_product = await db.products.find_one({"product_id": product_id})
            
            # Re-index in Elasticsearch
            try:
                product_obj = await self._convert_db_to_product_model(updated_product)
                vendor = await self.user_service.get_user_by_id(updated_product["vendor_id"])
                vendor_info = {
                    "business_name": getattr(vendor, 'business_name', None),
                    "rating": getattr(vendor, 'rating', None),
                    "market_location": getattr(vendor, 'market_location', None)
                }
                await elasticsearch_service.index_product(product_obj, vendor_info)
            except Exception as e:
                logger.warning(f"Failed to re-index product in Elasticsearch: {e}")
            
            return await self._convert_product_to_response(updated_product)
            
        except (NotFoundException, AuthorizationException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Failed to update product {product_id}: {e}")
            raise ValidationException("Product update failed")
    
    async def delete_product(
        self,
        product_id: str,
        requesting_user_id: str
    ) -> Dict[str, str]:
        """
        Delete a product (soft delete by setting status to SUSPENDED).
        
        Args:
            product_id: Product ID to delete
            requesting_user_id: ID of user making the request
            
        Returns:
            Deletion confirmation
            
        Raises:
            NotFoundException: If product not found
            AuthorizationException: If user not authorized
        """
        try:
            db = await get_database()
            product = await db.products.find_one({"product_id": product_id})
            
            if not product:
                raise NotFoundException("Product not found")
            
            # Check authorization - only product owner can delete
            if product["vendor_id"] != requesting_user_id:
                raise AuthorizationException("You can only delete your own products")
            
            # Soft delete by updating status
            result = await db.products.update_one(
                {"product_id": product_id},
                {"$set": {
                    "status": ProductStatus.SUSPENDED.value,
                    "updated_at": datetime.utcnow(),
                    "deleted_at": datetime.utcnow(),
                    "deleted_by": requesting_user_id
                }}
            )
            
            if result.modified_count == 0:
                raise ValidationException("Failed to delete product")
            
            # Remove from Elasticsearch
            try:
                await elasticsearch_service.delete_product(product_id)
            except Exception as e:
                logger.warning(f"Failed to remove product from Elasticsearch: {e}")
            
            return {
                "message": "Product has been deleted successfully",
                "product_id": product_id,
                "deleted_at": datetime.utcnow().isoformat()
            }
            
        except (NotFoundException, AuthorizationException):
            raise
        except Exception as e:
            logger.error(f"Failed to delete product {product_id}: {e}")
            raise ValidationException("Product deletion failed")
    
    async def get_vendor_products(
        self,
        vendor_id: str,
        status: Optional[ProductStatus] = None,
        limit: int = 20,
        skip: int = 0
    ) -> List[ProductResponse]:
        """
        Get products for a specific vendor.
        
        Args:
            vendor_id: Vendor ID
            status: Filter by product status
            limit: Maximum results to return
            skip: Number of results to skip
            
        Returns:
            List of vendor's products
        """
        try:
            db = await get_database()
            
            # Build filter
            filter_query = {"vendor_id": vendor_id}
            if status:
                filter_query["status"] = status.value
            
            # Get products
            cursor = db.products.find(filter_query).skip(skip).limit(limit).sort("created_at", -1)
            products = await cursor.to_list(length=limit)
            
            # Convert to responses
            responses = []
            for product in products:
                response = await self._convert_product_to_response(product)
                responses.append(response)
            
            return responses
            
        except Exception as e:
            logger.error(f"Failed to get vendor products for {vendor_id}: {e}")
            return []
    
    async def search_products(
        self,
        query: ProductSearchQuery
    ) -> ProductSearchResponse:
        """
        Search products with multilingual support and filtering using Elasticsearch.
        
        Args:
            query: Search query parameters
            
        Returns:
            Search results with products and metadata
        """
        try:
            # Try Elasticsearch first
            try:
                es_results, total_count, search_metadata = await elasticsearch_service.search_products(query)
                
                if es_results:
                    # Convert Elasticsearch results to ProductResponse objects
                    product_responses = []
                    for es_product in es_results:
                        # Convert ES document back to ProductResponse
                        product_response = await self._convert_es_to_product_response(es_product, query.language)
                        product_responses.append(product_response)
                    
                    # Build pagination info
                    page_info = {
                        "current_page": (query.skip // query.limit) + 1,
                        "total_pages": math.ceil(total_count / query.limit),
                        "page_size": query.limit,
                        "has_next": (query.skip + query.limit) < total_count,
                        "has_previous": query.skip > 0
                    }
                    
                    # Add filters applied to metadata
                    search_metadata["filters_applied"] = self._get_applied_filters(query)
                    
                    return ProductSearchResponse(
                        products=product_responses,
                        total_count=total_count,
                        page_info=page_info,
                        search_metadata=search_metadata
                    )
            
            except Exception as e:
                logger.warning(f"Elasticsearch search failed, falling back to MongoDB: {e}")
            
            # Fallback to MongoDB search
            db = await get_database()
            
            # Build search filter
            search_filter = await self._build_search_filter(query)
            
            # Build sort criteria
            sort_criteria = self._build_sort_criteria(query.sort_by, query.sort_order)
            
            # Execute search
            cursor = db.products.find(search_filter)
            
            # Apply sorting
            if sort_criteria:
                cursor = cursor.sort(sort_criteria)
            
            # Get total count
            total_count = await db.products.count_documents(search_filter)
            
            # Apply pagination
            cursor = cursor.skip(query.skip).limit(query.limit)
            products = await cursor.to_list(length=query.limit)
            
            # Convert to responses
            product_responses = []
            for product in products:
                response = await self._convert_product_to_response(product, query.language)
                product_responses.append(response)
            
            # Build pagination info
            page_info = {
                "current_page": (query.skip // query.limit) + 1,
                "total_pages": math.ceil(total_count / query.limit),
                "page_size": query.limit,
                "has_next": (query.skip + query.limit) < total_count,
                "has_previous": query.skip > 0
            }
            
            # Build search metadata
            search_metadata = {
                "query": query.query,
                "language": query.language.value,
                "filters_applied": self._get_applied_filters(query),
                "search_time_ms": 0,  # TODO: Implement timing
                "suggestions": [],  # TODO: Implement search suggestions
                "fallback_used": True
            }
            
            return ProductSearchResponse(
                products=product_responses,
                total_count=total_count,
                page_info=page_info,
                search_metadata=search_metadata
            )
            
        except Exception as e:
            logger.error(f"Product search failed: {e}")
            return ProductSearchResponse(
                products=[],
                total_count=0,
                page_info={"current_page": 1, "total_pages": 0, "page_size": query.limit, "has_next": False, "has_previous": False},
                search_metadata={"query": query.query, "language": query.language.value, "filters_applied": [], "search_time_ms": 0, "suggestions": [], "error": str(e)}
            )
    
    async def update_product_availability(
        self,
        product_id: str,
        quantity_available: int,
        requesting_user_id: str
    ) -> ProductResponse:
        """
        Update product availability quantity.
        
        Args:
            product_id: Product ID
            quantity_available: New available quantity
            requesting_user_id: ID of user making the request
            
        Returns:
            Updated product response
            
        Raises:
            NotFoundException: If product not found
            AuthorizationException: If user not authorized
            ValidationException: If quantity is invalid
        """
        try:
            db = await get_database()
            product = await db.products.find_one({"product_id": product_id})
            
            if not product:
                raise NotFoundException("Product not found")
            
            # Check authorization
            if product["vendor_id"] != requesting_user_id:
                raise AuthorizationException("You can only update your own products")
            
            if quantity_available < 0:
                raise ValidationException("Quantity cannot be negative")
            
            # Update availability
            result = await db.products.update_one(
                {"product_id": product_id},
                {"$set": {
                    "availability.quantity_available": quantity_available,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            if result.modified_count == 0:
                raise ValidationException("Failed to update availability")
            
            # Get updated product
            updated_product = await db.products.find_one({"product_id": product_id})
            return await self._convert_product_to_response(updated_product)
            
        except (NotFoundException, AuthorizationException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Failed to update product availability {product_id}: {e}")
            raise ValidationException("Availability update failed")
    
    # Private helper methods
    
    def _validate_product_data(self, product_data: ProductCreateRequest) -> None:
        """Validate product creation data."""
        if not product_data.name_text.strip():
            raise ValidationException("Product name is required")
        
        if not product_data.description_text.strip():
            raise ValidationException("Product description is required")
        
        if product_data.base_price <= 0:
            raise ValidationException("Base price must be greater than 0")
        
        if product_data.quantity_available <= 0:
            raise ValidationException("Available quantity must be greater than 0")
        
        if product_data.minimum_order <= 0:
            raise ValidationException("Minimum order must be greater than 0")
        
        if product_data.maximum_order and product_data.maximum_order < product_data.minimum_order:
            raise ValidationException("Maximum order cannot be less than minimum order")
        
        if not product_data.image_urls:
            raise ValidationException("At least one product image is required")
    
    async def _create_product_location(
        self,
        product_data: ProductCreateRequest,
        vendor: Any
    ) -> LocationData:
        """Create location data for product."""
        # Use vendor location as base
        vendor_location = vendor.location
        
        return LocationData(
            address=product_data.location_address or vendor_location.address,
            city=vendor_location.city,
            state=vendor_location.state,
            pincode=vendor_location.pincode,
            country=vendor_location.country,
            coordinates=vendor_location.coordinates,
            market_name=product_data.market_name or getattr(vendor, 'market_location', None)
        )
    
    async def _process_product_images(self, image_urls: List[str]) -> List[ImageReference]:
        """Process product images and create image references."""
        images = []
        for i, url in enumerate(image_urls):
            image_ref = ImageReference(
                image_id=str(ObjectId()),
                image_url=url,
                thumbnail_url=url,  # TODO: Generate actual thumbnails
                alt_text=None,
                is_primary=(i == 0),  # First image is primary
                uploaded_at=datetime.utcnow(),
                file_size=None,
                dimensions=None
            )
            images.append(image_ref)
        
        return images
    
    def _generate_search_keywords(self, product_data: ProductCreateRequest) -> List[str]:
        """Generate search keywords from product data."""
        keywords = []
        
        # Add name words
        keywords.extend(product_data.name_text.lower().split())
        
        # Add description words (first 10 words)
        desc_words = product_data.description_text.lower().split()[:10]
        keywords.extend(desc_words)
        
        # Add category and subcategory
        keywords.append(product_data.category.value)
        if product_data.subcategory:
            keywords.append(product_data.subcategory.lower())
        
        # Add tags
        keywords.extend([tag.lower() for tag in product_data.tags])
        
        # Add quality grade
        keywords.append(product_data.quality_grade.value)
        
        # Add certifications
        keywords.extend([cert.lower() for cert in product_data.certifications])
        
        # Remove duplicates and empty strings
        keywords = list(set([kw.strip() for kw in keywords if kw.strip()]))
        
        return keywords[:20]  # Limit to 20 keywords
    
    def _generate_search_keywords_from_tags(self, tags: List[str]) -> List[str]:
        """Generate search keywords from tags."""
        return [tag.lower().strip() for tag in tags if tag.strip()]
    
    async def _auto_translate_product(
        self,
        product_id: str,
        name_ml: MultilingualText,
        description_ml: MultilingualText
    ) -> None:
        """Auto-translate product name and description to all supported languages."""
        try:
            # Get all supported languages except the original
            target_languages = [
                lang for lang in SupportedLanguage 
                if lang != name_ml.original_language
            ]
            
            # Translate name
            for target_lang in target_languages:
                try:
                    translation_result = await self.translation_service.translate_text(
                        text=name_ml.original_text,
                        source_language=name_ml.original_language.value,
                        target_language=target_lang.value
                    )
                    if translation_result.success:
                        name_ml.add_translation(target_lang, translation_result.translated_text, auto_translated=True)
                except Exception as e:
                    logger.warning(f"Failed to translate product name to {target_lang}: {e}")
            
            # Translate description
            for target_lang in target_languages:
                try:
                    translation_result = await self.translation_service.translate_text(
                        text=description_ml.original_text,
                        source_language=description_ml.original_language.value,
                        target_language=target_lang.value
                    )
                    if translation_result.success:
                        description_ml.add_translation(target_lang, translation_result.translated_text, auto_translated=True)
                except Exception as e:
                    logger.warning(f"Failed to translate product description to {target_lang}: {e}")
            
            # Update product with translations
            db = await get_database()
            await db.products.update_one(
                {"product_id": product_id},
                {"$set": {
                    "name": name_ml.model_dump(),
                    "description": description_ml.model_dump()
                }}
            )
            
        except Exception as e:
            logger.error(f"Failed to auto-translate product {product_id}: {e}")
    
    def _prepare_product_for_db(self, product_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare product dictionary for MongoDB storage."""
        # Convert datetime objects to ISO strings for MongoDB
        if "created_at" in product_dict and isinstance(product_dict["created_at"], datetime):
            product_dict["created_at"] = product_dict["created_at"]
        
        if "updated_at" in product_dict and isinstance(product_dict["updated_at"], datetime):
            product_dict["updated_at"] = product_dict["updated_at"]
        
        # Convert Decimal to string
        if "price_info" in product_dict and "base_price" in product_dict["price_info"]:
            product_dict["price_info"]["base_price"] = str(product_dict["price_info"]["base_price"])
        
        # Convert date objects to ISO strings
        if "metadata" in product_dict:
            metadata = product_dict["metadata"]
            if "harvest_date" in metadata and metadata["harvest_date"]:
                metadata["harvest_date"] = metadata["harvest_date"].isoformat() if isinstance(metadata["harvest_date"], date) else metadata["harvest_date"]
            if "expiry_date" in metadata and metadata["expiry_date"]:
                metadata["expiry_date"] = metadata["expiry_date"].isoformat() if isinstance(metadata["expiry_date"], date) else metadata["expiry_date"]
        
        return product_dict
    
    async def _convert_product_to_response(
        self,
        product: Dict[str, Any],
        language: SupportedLanguage = SupportedLanguage.ENGLISH
    ) -> ProductResponse:
        """Convert database product document to ProductResponse."""
        # Get vendor information
        vendor = await self.user_service.get_user_by_id(product["vendor_id"])
        
        # Convert multilingual text
        name_ml = MultilingualText(**product["name"])
        description_ml = MultilingualText(**product["description"])
        
        # Convert images
        images = [ImageReference(**img) for img in product.get("images", [])]
        
        # Convert location
        location = LocationData(**product["location"])
        
        # Convert price info
        price_info = PriceInfo(**product["price_info"])
        price_info.base_price = Decimal(str(price_info.base_price))
        
        # Convert availability
        availability = AvailabilityInfo(**product["availability"])
        
        # Convert metadata
        metadata_dict = product.get("metadata", {})
        # Convert date strings back to date objects
        if "harvest_date" in metadata_dict and metadata_dict["harvest_date"]:
            if isinstance(metadata_dict["harvest_date"], str):
                metadata_dict["harvest_date"] = datetime.fromisoformat(metadata_dict["harvest_date"]).date()
        if "expiry_date" in metadata_dict and metadata_dict["expiry_date"]:
            if isinstance(metadata_dict["expiry_date"], str):
                metadata_dict["expiry_date"] = datetime.fromisoformat(metadata_dict["expiry_date"]).date()
        
        metadata = ProductMetadata(**metadata_dict)
        
        return ProductResponse(
            product_id=product["product_id"],
            vendor_id=product["vendor_id"],
            name=name_ml,
            description=description_ml,
            category=product["category"],
            subcategory=product.get("subcategory"),
            tags=product.get("tags", []),
            images=images,
            price_info=price_info,
            availability=availability,
            location=location,
            quality_grade=QualityGrade(product["quality_grade"]),
            metadata=metadata,
            status=ProductStatus(product["status"]),
            created_at=product.get("created_at", datetime.utcnow()),
            updated_at=product.get("updated_at", datetime.utcnow()),
            views_count=product.get("views_count", 0),
            favorites_count=product.get("favorites_count", 0),
            featured=product.get("featured", False),
            vendor_name=vendor.business_name if vendor and hasattr(vendor, 'business_name') else None,
            vendor_rating=vendor.rating if vendor and hasattr(vendor, 'rating') else None,
            vendor_location=vendor.market_location if vendor and hasattr(vendor, 'market_location') else None
        )
    
    async def _build_search_filter(self, query: ProductSearchQuery) -> Dict[str, Any]:
        """Build MongoDB filter for product search."""
        search_filter = {"status": {"$in": [ProductStatus.ACTIVE.value]}}
        
        # Text search
        if query.query:
            search_filter["$or"] = [
                {"name.original_text": {"$regex": query.query, "$options": "i"}},
                {"description.original_text": {"$regex": query.query, "$options": "i"}},
                {"tags": {"$in": [query.query.lower()]}},
                {"search_keywords": {"$in": [query.query.lower()]}}
            ]
            
            # Add translations search for different languages
            for lang in SupportedLanguage:
                if lang != query.language:
                    search_filter["$or"].extend([
                        {f"name.translations.{lang.value}": {"$regex": query.query, "$options": "i"}},
                        {f"description.translations.{lang.value}": {"$regex": query.query, "$options": "i"}}
                    ])
        
        # Category filter
        if query.category:
            search_filter["category"] = query.category.value
        
        if query.subcategory:
            search_filter["subcategory"] = {"$regex": query.subcategory, "$options": "i"}
        
        # Price filters
        if query.min_price is not None or query.max_price is not None:
            price_filter = {}
            if query.min_price is not None:
                price_filter["$gte"] = str(query.min_price)
            if query.max_price is not None:
                price_filter["$lte"] = str(query.max_price)
            search_filter["price_info.base_price"] = price_filter
        
        # Location filters
        if query.city:
            search_filter["location.city"] = {"$regex": query.city, "$options": "i"}
        
        if query.state:
            search_filter["location.state"] = {"$regex": query.state, "$options": "i"}
        
        # Geospatial search
        if query.coordinates and query.radius_km:
            search_filter["location.coordinates"] = {
                "$near": {
                    "$geometry": {
                        "type": "Point",
                        "coordinates": query.coordinates
                    },
                    "$maxDistance": query.radius_km * 1000  # Convert km to meters
                }
            }
        
        # Quality filters
        if query.quality_grades:
            search_filter["quality_grade"] = {"$in": [grade.value for grade in query.quality_grades]}
        
        # Availability filter
        if query.available_only:
            search_filter["availability.quantity_available"] = {"$gt": 0}
        
        # Organic filter
        if query.organic_only:
            search_filter["$or"] = search_filter.get("$or", []) + [
                {"quality_grade": QualityGrade.ORGANIC.value},
                {"metadata.certifications": {"$in": ["organic", "bio", "natural"]}}
            ]
        
        return search_filter
    
    def _build_sort_criteria(self, sort_by: str, sort_order: str) -> List[Tuple[str, int]]:
        """Build MongoDB sort criteria."""
        sort_direction = 1 if sort_order == "asc" else -1
        
        sort_mapping = {
            "relevance": [("featured", -1), ("views_count", -1), ("created_at", -1)],
            "price": [("price_info.base_price", sort_direction)],
            "date": [("created_at", sort_direction)],
            "rating": [("vendor_rating", sort_direction)],
            "popularity": [("views_count", sort_direction), ("favorites_count", sort_direction)],
            "distance": []  # TODO: Implement distance sorting
        }
        
        return sort_mapping.get(sort_by, [("created_at", -1)])
    
    def _get_applied_filters(self, query: ProductSearchQuery) -> List[str]:
        """Get list of applied filters for search metadata."""
        filters = []
        
        if query.category:
            filters.append(f"category:{query.category.value}")
        if query.subcategory:
            filters.append(f"subcategory:{query.subcategory}")
        if query.min_price is not None:
            filters.append(f"min_price:{query.min_price}")
        if query.max_price is not None:
            filters.append(f"max_price:{query.max_price}")
        if query.city:
            filters.append(f"city:{query.city}")
        if query.state:
            filters.append(f"state:{query.state}")
        if query.quality_grades:
            filters.append(f"quality:{','.join([g.value for g in query.quality_grades])}")
        if query.available_only:
            filters.append("available_only:true")
        if query.organic_only:
            filters.append("organic_only:true")
        
        return filters
    
    async def _convert_db_to_product_model(self, product_dict: Dict[str, Any]) -> Product:
        """Convert database product document to Product model."""
        # Convert multilingual text
        name_ml = MultilingualText(**product_dict["name"])
        description_ml = MultilingualText(**product_dict["description"])
        
        # Convert images
        images = [ImageReference(**img) for img in product_dict.get("images", [])]
        
        # Convert location
        location = LocationData(**product_dict["location"])
        
        # Convert price info
        price_info = PriceInfo(**product_dict["price_info"])
        price_info.base_price = Decimal(str(price_info.base_price))
        
        # Convert availability
        availability = AvailabilityInfo(**product_dict["availability"])
        
        # Convert metadata
        metadata_dict = product_dict.get("metadata", {})
        # Convert date strings back to date objects
        if "harvest_date" in metadata_dict and metadata_dict["harvest_date"]:
            if isinstance(metadata_dict["harvest_date"], str):
                metadata_dict["harvest_date"] = datetime.fromisoformat(metadata_dict["harvest_date"]).date()
        if "expiry_date" in metadata_dict and metadata_dict["expiry_date"]:
            if isinstance(metadata_dict["expiry_date"], str):
                metadata_dict["expiry_date"] = datetime.fromisoformat(metadata_dict["expiry_date"]).date()
        
        metadata = ProductMetadata(**metadata_dict)
        
        return Product(
            product_id=product_dict["product_id"],
            vendor_id=product_dict["vendor_id"],
            name=name_ml,
            description=description_ml,
            category=product_dict["category"],
            subcategory=product_dict.get("subcategory"),
            tags=product_dict.get("tags", []),
            images=images,
            price_info=price_info,
            availability=availability,
            location=location,
            quality_grade=QualityGrade(product_dict["quality_grade"]),
            metadata=metadata,
            status=ProductStatus(product_dict["status"]),
            created_at=product_dict.get("created_at", datetime.utcnow()),
            updated_at=product_dict.get("updated_at", datetime.utcnow()),
            views_count=product_dict.get("views_count", 0),
            favorites_count=product_dict.get("favorites_count", 0),
            search_keywords=product_dict.get("search_keywords", []),
            featured=product_dict.get("featured", False)
        )
    
    async def _convert_es_to_product_response(
        self,
        es_product: Dict[str, Any],
        language: SupportedLanguage = SupportedLanguage.ENGLISH
    ) -> ProductResponse:
        """Convert Elasticsearch document to ProductResponse."""
        # Convert multilingual text
        name_ml = MultilingualText(
            original_language=SupportedLanguage(es_product["name"]["original_language"]),
            original_text=es_product["name"]["original_text"],
            translations={
                SupportedLanguage(lang): text 
                for lang, text in es_product["name"]["translations"].items()
            }
        )
        
        description_ml = MultilingualText(
            original_language=SupportedLanguage(es_product["description"]["original_language"]),
            original_text=es_product["description"]["original_text"],
            translations={
                SupportedLanguage(lang): text 
                for lang, text in es_product["description"]["translations"].items()
            }
        )
        
        # Create basic image references (ES doesn't store full image data)
        images = [
            ImageReference(
                image_id="placeholder",
                image_url="",
                is_primary=True,
                uploaded_at=datetime.utcnow()
            )
        ]
        
        # Convert location
        location = LocationData(
            address=es_product["location"]["address"],
            city=es_product["location"]["city"],
            state=es_product["location"]["state"],
            pincode=es_product["location"]["pincode"],
            country=es_product["location"]["country"],
            coordinates=es_product["location"]["coordinates"],
            market_name=es_product["location"]["market_name"]
        )
        
        # Convert price info
        price_info = PriceInfo(
            base_price=Decimal(str(es_product["price"])),
            currency=es_product["currency"],
            negotiable=es_product["negotiable"]
        )
        
        # Convert availability
        availability = AvailabilityInfo(
            quantity_available=es_product["quantity_available"],
            unit=MeasurementUnit(es_product["unit"]),
            minimum_order=es_product["minimum_order"]
        )
        
        # Convert metadata
        metadata = ProductMetadata(
            harvest_date=datetime.fromisoformat(es_product["harvest_date"]).date() if es_product.get("harvest_date") else None,
            expiry_date=datetime.fromisoformat(es_product["expiry_date"]).date() if es_product.get("expiry_date") else None,
            certifications=es_product.get("certifications", []),
            origin=es_product.get("origin"),
            variety=es_product.get("variety")
        )
        
        return ProductResponse(
            product_id=es_product["product_id"],
            vendor_id=es_product["vendor_id"],
            name=name_ml,
            description=description_ml,
            category=es_product["category"],
            subcategory=es_product.get("subcategory"),
            tags=es_product.get("tags", []),
            images=images,
            price_info=price_info,
            availability=availability,
            location=location,
            quality_grade=QualityGrade(es_product["quality_grade"]),
            metadata=metadata,
            status=ProductStatus(es_product["status"]),
            created_at=datetime.fromisoformat(es_product["created_at"]) if es_product.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(es_product["updated_at"]) if es_product.get("updated_at") else datetime.utcnow(),
            views_count=es_product.get("views_count", 0),
            favorites_count=es_product.get("favorites_count", 0),
            featured=es_product.get("featured", False),
            vendor_name=es_product.get("vendor_name"),
            vendor_rating=es_product.get("vendor_rating"),
            vendor_location=es_product.get("vendor_location")
        )