"""
Product management endpoints for marketplace operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
import logging

from app.core.dependencies import get_current_user
from app.core.database import get_database
from app.core.exceptions import NotFoundException, ValidationException, AuthorizationException
from app.models.user import UserResponse
from app.models.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    ProductResponse,
    ProductSearchQuery,
    ProductSearchResponse,
    ImageUploadResponse,
    ProductStatus,
    QualityGrade,
    MeasurementUnit,
    SupportedLanguage,
    ProductCategory,
    ImageReference
)
from app.services.product_service import ProductService
from app.services.image_service import ImageService

logger = logging.getLogger(__name__)

router = APIRouter()
product_service = ProductService()
image_service = ImageService()


@router.get("/my-products", response_model=List[ProductResponse])
async def get_my_products(
    status_filter: Optional[ProductStatus] = None,
    limit: int = 50,
    skip: int = 0,
    current_user: UserResponse = Depends(get_current_user)
) -> List[ProductResponse]:
    """
    Get products for the current authenticated vendor.
    
    Args:
        status_filter: Filter by product status
        limit: Maximum results to return
        skip: Number of results to skip
        current_user: Current authenticated user
        
    Returns:
        List of current user's products
    """
    try:
        return await product_service.get_vendor_products(
            vendor_id=current_user.user_id,
            status=status_filter,
            limit=min(limit, 100),
            skip=max(skip, 0)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve your products"
        )


@router.post("/search/initialize")
async def initialize_search_index(
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Initialize Elasticsearch search index and bulk index existing products.
    This endpoint is typically used during deployment or maintenance.
    
    Args:
        current_user: Current authenticated user (admin only)
        
    Returns:
        Initialization status and statistics
        
    Raises:
        HTTPException: If initialization fails or user not authorized
    """
    try:
        # TODO: Add admin role check
        # For now, any authenticated user can initialize (should be restricted in production)
        
        result = await product_service.initialize_search_index()
        
        if result["status"] == "error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize search index"
        )


@router.post("/", response_model=ProductResponse)
async def create_product(
    product_data: ProductCreateRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> ProductResponse:
    """
    Create a new product listing.
    
    Args:
        product_data: Product information
        current_user: Current authenticated user
        
    Returns:
        Created product information
        
    Raises:
        HTTPException: If creation fails
    """
    try:
        return await product_service.create_product(
            product_data=product_data,
            vendor_id=current_user.user_id,
            requesting_user_id=current_user.user_id
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create product"
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_detail(
    product_id: str,
    language: SupportedLanguage = SupportedLanguage.ENGLISH
) -> ProductResponse:
    """
    Get detailed information about a specific product.
    
    Args:
        product_id: Product identifier
        language: Preferred language for response
        
    Returns:
        Detailed product information
        
    Raises:
        HTTPException: If product not found
    """
    try:
        product = await product_service.get_product_by_id(
            product_id=product_id,
            language=language,
            increment_views=True
        )
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve product"
        )


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_data: ProductUpdateRequest,
    current_user: UserResponse = Depends(get_current_user)
) -> ProductResponse:
    """
    Update an existing product listing.
    
    Args:
        product_id: Product identifier
        product_data: Updated product information
        current_user: Current authenticated user
        
    Returns:
        Updated product information
        
    Raises:
        HTTPException: If update fails
    """
    try:
        return await product_service.update_product(
            product_id=product_id,
            updates=product_data,
            requesting_user_id=current_user.user_id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, str]:
    """
    Delete a product listing.
    
    Args:
        product_id: Product identifier
        current_user: Current authenticated user
        
    Returns:
        Deletion confirmation
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        return await product_service.delete_product(
            product_id=product_id,
            requesting_user_id=current_user.user_id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


@router.get("/", response_model=ProductSearchResponse)
async def search_products(
    query: Optional[str] = None,
    language: SupportedLanguage = SupportedLanguage.ENGLISH,
    category: Optional[ProductCategory] = None,
    subcategory: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius_km: Optional[float] = None,
    quality_grades: Optional[List[QualityGrade]] = Query(None),
    available_only: bool = True,
    organic_only: bool = False,
    sort_by: str = "relevance",
    sort_order: str = "desc",
    limit: int = 20,
    skip: int = 0
) -> ProductSearchResponse:
    """
    Search products with filtering and multilingual support.
    
    Args:
        query: Search text
        language: Search language
        category: Filter by category
        subcategory: Filter by subcategory
        min_price: Minimum price filter
        max_price: Maximum price filter
        city: Filter by city
        state: Filter by state
        latitude: Latitude for geolocation search
        longitude: Longitude for geolocation search
        radius_km: Search radius in kilometers
        quality_grades: Filter by quality grades
        available_only: Show only available products
        organic_only: Show only organic products
        sort_by: Sort criteria
        sort_order: Sort order (asc/desc)
        limit: Results limit
        skip: Results to skip
        
    Returns:
        Search results with products and metadata
    """
    try:
        # Build coordinates if both lat and lon provided
        coordinates = None
        if latitude is not None and longitude is not None:
            coordinates = [longitude, latitude]  # GeoJSON format: [lon, lat]
        
        search_query = ProductSearchQuery(
            query=query,
            language=language,
            category=category,
            subcategory=subcategory,
            min_price=min_price,
            max_price=max_price,
            city=city,
            state=state,
            coordinates=coordinates,
            radius_km=radius_km,
            quality_grades=quality_grades or [],
            available_only=available_only,
            organic_only=organic_only,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=min(limit, 100),  # Cap at 100
            skip=max(skip, 0)  # Ensure non-negative
        )
        
        return await product_service.search_products(search_query)
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed"
        )


@router.get("/vendor/{vendor_id}", response_model=List[ProductResponse])
async def get_vendor_products(
    vendor_id: str,
    status_filter: Optional[ProductStatus] = None,
    limit: int = 20,
    skip: int = 0
) -> List[ProductResponse]:
    """
    Get products for a specific vendor.
    
    Args:
        vendor_id: Vendor ID
        status_filter: Filter by product status
        limit: Maximum results to return
        skip: Number of results to skip
        
    Returns:
        List of vendor's products
    """
    try:
        return await product_service.get_vendor_products(
            vendor_id=vendor_id,
            status=status_filter,
            limit=min(limit, 100),
            skip=max(skip, 0)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve vendor products"
        )


@router.patch("/{product_id}/availability")
async def update_product_availability(
    product_id: str,
    quantity_available: int,
    current_user: UserResponse = Depends(get_current_user)
) -> ProductResponse:
    """
    Update product availability quantity.
    
    Args:
        product_id: Product ID
        quantity_available: New available quantity
        current_user: Current authenticated user
        
    Returns:
        Updated product information
        
    Raises:
        HTTPException: If update fails
    """
    try:
        return await product_service.update_product_availability(
            product_id=product_id,
            quantity_available=quantity_available,
            requesting_user_id=current_user.user_id
        )
    except NotFoundException as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthorizationException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update availability"
        )


@router.post("/{product_id}/images", response_model=ImageUploadResponse)
async def upload_product_image(
    product_id: str,
    file: UploadFile = File(...),
    alt_text: Optional[str] = Form(None),
    is_primary: bool = Form(False),
    current_user: UserResponse = Depends(get_current_user)
) -> ImageUploadResponse:
    """
    Upload an image for a product.
    
    Args:
        product_id: Product ID
        file: Image file to upload
        alt_text: Alternative text for accessibility
        is_primary: Whether this is the primary image
        current_user: Current authenticated user
        
    Returns:
        Upload result with image URLs
        
    Raises:
        HTTPException: If upload fails
    """
    try:
        # Verify product exists and user owns it
        product = await product_service.get_product_by_id(product_id, increment_views=False)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product.vendor_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload images to your own products"
            )
        
        # Read file data
        file_data = await file.read()
        
        # Upload image
        image_ref = await image_service.upload_product_image(
            image_data=file_data,
            filename=file.filename or "image.jpg",
            product_id=product_id,
            content_type=file.content_type or "image/jpeg"
        )
        
        # Update product with new image reference
        db = await get_database()
        
        # Create image reference dict for database
        new_image = {
            "image_id": image_ref.image_id,
            "image_url": image_ref.image_url,
            "thumbnail_url": image_ref.thumbnail_url or image_ref.image_url,
            "alt_text": alt_text,
            "is_primary": is_primary,
            "uploaded_at": datetime.utcnow()
        }
        
        # Get current images
        current_product = await db.products.find_one({"product_id": product_id})
        current_images = current_product.get("images", [])
        
        # If this is primary, mark all other images as not primary
        if is_primary:
            for img in current_images:
                img["is_primary"] = False
        
        # If this is the first image, make it primary
        if len(current_images) == 0:
            new_image["is_primary"] = True
        
        # Add new image
        current_images.append(new_image)
        
        # Update product
        await db.products.update_one(
            {"product_id": product_id},
            {
                "$set": {
                    "images": current_images,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        logger.info(f"Image uploaded successfully for product {product_id}: {image_ref.image_url}")
        
        return ImageUploadResponse(
            image_id=image_ref.image_id,
            image_url=image_ref.image_url,
            thumbnail_url=image_ref.thumbnail_url or image_ref.image_url,
            upload_status="success",
            message="Image uploaded successfully"
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed"
        )


@router.get("/upload-url/{product_id}")
async def get_upload_presigned_url(
    product_id: str,
    filename: str,
    content_type: str = "image/jpeg",
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get a presigned URL for direct client upload to cloud storage.
    
    Args:
        product_id: Product ID
        filename: Original filename
        content_type: Image content type
        current_user: Current authenticated user
        
    Returns:
        Presigned URL and upload fields
        
    Raises:
        HTTPException: If URL generation fails
    """
    try:
        # Verify product exists and user owns it
        product = await product_service.get_product_by_id(product_id, increment_views=False)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product.vendor_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload images to your own products"
            )
        
        return await image_service.get_upload_presigned_url(
            product_id=product_id,
            filename=filename,
            content_type=content_type
        )
        
    except ValidationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate upload URL"
        )