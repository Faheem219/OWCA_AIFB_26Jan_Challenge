"""
Product catalog API endpoints.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.models.product import (
    Product, ProductCreate, ProductUpdate, ProductSearchFilters,
    ProductSearchResult, ImageUploadRequest, ImageUploadResponse,
    ProductAnalytics, AIProductSuggestion, BulkProductOperation
)
from app.models.common import PaginationParams, APIResponse
from app.services.product_catalog_service import ProductCatalogService
from app.api.deps import get_current_user, get_db
from app.models.user import User

router = APIRouter()


@router.post("/", response_model=Product)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create a new product listing."""
    if not current_user.vendor_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can create products"
        )
    
    service = ProductCatalogService(db)
    return await service.create_product(str(current_user.id), product_data)


@router.get("/search", response_model=ProductSearchResult)
async def search_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    quality_grade: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    location_radius_km: Optional[float] = None,
    certifications: Optional[List[str]] = None,
    freshness_level: Optional[str] = None,
    available_only: bool = True,
    featured_only: bool = False,
    page: int = 1,
    size: int = 20,
    db = Depends(get_db)
):
    """Search products with filters."""
    filters = ProductSearchFilters(
        category=category,
        subcategory=subcategory,
        quality_grade=quality_grade,
        price_min=price_min,
        price_max=price_max,
        location_radius_km=location_radius_km,
        certifications=certifications or [],
        freshness_level=freshness_level,
        available_only=available_only,
        featured_only=featured_only
    )
    
    pagination = PaginationParams(page=page, size=size)
    service = ProductCatalogService(db)
    
    return await service.search_products(filters, pagination)


@router.get("/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    db = Depends(get_db)
):
    """Get product by ID."""
    service = ProductCatalogService(db)
    
    try:
        from bson import ObjectId
        product_data = await db.products.find_one({"_id": ObjectId(product_id)})
        if not product_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        # Increment view count
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {"views_count": 1}}
        )
        
        return Product(**product_data)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product"
        )


@router.put("/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_update: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update product."""
    try:
        from bson import ObjectId
        from datetime import datetime
        
        # Check if product exists and belongs to user
        product = await db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product["vendor_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this product"
            )
        
        # Update product
        update_data = {k: v for k, v in product_update.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )
        
        # Return updated product
        updated_product = await db.products.find_one({"_id": ObjectId(product_id)})
        return Product(**updated_product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update product"
        )


@router.delete("/{product_id}")
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Delete product."""
    try:
        from bson import ObjectId
        
        # Check if product exists and belongs to user
        product = await db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product["vendor_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this product"
            )
        
        # Delete product
        await db.products.delete_one({"_id": ObjectId(product_id)})
        
        return APIResponse(
            success=True,
            message="Product deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete product"
        )


@router.post("/{product_id}/images/upload", response_model=ImageUploadResponse)
async def request_image_upload(
    product_id: str,
    upload_request: ImageUploadRequest,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Request image upload for product."""
    try:
        from bson import ObjectId
        import uuid
        
        # Verify product ownership
        product = await db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product["vendor_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload images for this product"
            )
        
        # Generate image ID and upload URL
        image_id = str(uuid.uuid4())
        upload_url = f"/api/v1/products/{product_id}/images/{image_id}/upload"
        
        return ImageUploadResponse(
            image_id=image_id,
            upload_url=upload_url,
            analysis_requested=upload_request.analyze_image
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request image upload"
        )


@router.post("/{product_id}/images/{image_id}/upload")
async def upload_product_image(
    product_id: str,
    image_id: str,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    analyze_image: bool = Form(True),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Upload product image."""
    try:
        from bson import ObjectId
        from datetime import datetime
        import aiofiles
        from pathlib import Path
        
        # Verify product ownership
        product = await db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product["vendor_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload images for this product"
            )
        
        # Validate file
        if file.size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 10MB limit"
            )
        
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed"
            )
        
        # Save file
        upload_dir = Path("uploads/product_images")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = upload_dir / f"{product_id}_{image_id}_{file.filename}"
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Analyze image if requested
        analysis_result = None
        if analyze_image:
            service = ProductCatalogService(db)
            analysis_result = await service.analyze_product_image(content, product_id)
        
        # Create product image record
        from app.models.product import ProductImage
        product_image = ProductImage(
            id=image_id,
            url=str(file_path),
            is_primary=is_primary,
            analysis_result=analysis_result,
            file_size=file.size,
            mime_type=file.content_type
        )
        
        # Update product with new image
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {
                "$push": {"images": product_image.dict()},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # If this is primary image, update other images
        if is_primary:
            await db.products.update_one(
                {"_id": ObjectId(product_id)},
                {"$set": {"images.$[elem].is_primary": False}},
                array_filters=[{"elem.id": {"$ne": image_id}}]
            )
        
        return APIResponse(
            success=True,
            message="Image uploaded successfully",
            data={
                "image_id": image_id,
                "analysis_result": analysis_result.dict() if analysis_result else None
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload image"
        )


@router.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    product_type: Optional[str] = Form(None),
    db = Depends(get_db)
):
    """Analyze product image without creating a product."""
    try:
        # Validate file
        if file.size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 10MB limit"
            )
        
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type {file.content_type} not allowed"
            )
        
        # Analyze image
        content = await file.read()
        service = ProductCatalogService(db)
        analysis_result = await service.analyze_product_image(content)
        
        return APIResponse(
            success=True,
            message="Image analyzed successfully",
            data=analysis_result.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze image"
        )


@router.get("/{product_id}/analytics", response_model=ProductAnalytics)
async def get_product_analytics(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get product analytics."""
    try:
        from bson import ObjectId
        
        # Verify product ownership
        product = await db.products.find_one({"_id": ObjectId(product_id)})
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found"
            )
        
        if product["vendor_id"] != str(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view analytics for this product"
            )
        
        service = ProductCatalogService(db)
        return await service.get_product_analytics(product_id)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get product analytics"
        )


@router.get("/vendor/suggestions", response_model=List[AIProductSuggestion])
async def get_ai_product_suggestions(
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get AI-powered product suggestions for vendor."""
    if not current_user.vendor_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only vendors can get product suggestions"
        )
    
    service = ProductCatalogService(db)
    return await service.get_ai_product_suggestions(str(current_user.id))


@router.post("/bulk-operation")
async def bulk_product_operation(
    operation: BulkProductOperation,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Perform bulk operations on products."""
    try:
        from bson import ObjectId
        from datetime import datetime
        
        # Verify all products belong to the user
        product_ids = [ObjectId(pid) for pid in operation.product_ids]
        products = await db.products.find({
            "_id": {"$in": product_ids},
            "vendor_id": str(current_user.id)
        }).to_list(length=None)
        
        if len(products) != len(operation.product_ids):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Some products don't belong to you or don't exist"
            )
        
        # Perform operation
        if operation.operation == "activate":
            await db.products.update_many(
                {"_id": {"$in": product_ids}},
                {"$set": {"status": "active", "updated_at": datetime.utcnow()}}
            )
        elif operation.operation == "deactivate":
            await db.products.update_many(
                {"_id": {"$in": product_ids}},
                {"$set": {"status": "inactive", "updated_at": datetime.utcnow()}}
            )
        elif operation.operation == "delete":
            await db.products.delete_many({"_id": {"$in": product_ids}})
        elif operation.operation == "update_price":
            if not operation.parameters or "price_multiplier" not in operation.parameters:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Price multiplier required for price update operation"
                )
            
            multiplier = operation.parameters["price_multiplier"]
            await db.products.update_many(
                {"_id": {"$in": product_ids}},
                {
                    "$mul": {"price_info.base_price": multiplier},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        return APIResponse(
            success=True,
            message=f"Bulk {operation.operation} completed successfully",
            data={"affected_products": len(operation.product_ids)}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform bulk operation"
        )