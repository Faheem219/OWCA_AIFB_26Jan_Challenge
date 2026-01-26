"""
Smart Product Catalog Service with AI features.
"""
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import uuid
import os
from pathlib import Path
import json
import base64
from PIL import Image
import io

from app.models.product import (
    Product, ProductCreate, ProductUpdate, ProductSearchFilters,
    ProductSearchResult, ProductImage, ImageAnalysisResult,
    ProductCategory, ProductSubcategory, QualityGrade, FreshnessLevel,
    Unit, BarcodeInfo, ProductAnalytics, AIProductSuggestion,
    ImageUploadRequest, ImageUploadResponse, BulkProductOperation
)
from app.models.common import PaginationParams, PaginatedResponse
from app.db.mongodb import Collections
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProductCatalogService:
    """Service for smart product catalog with AI features."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.products_collection = db[Collections.PRODUCTS]
        self.vendors_collection = db[Collections.USERS]
        
        # Create upload directory
        self.upload_dir = Path("uploads/product_images")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # AI model configurations (mock for now)
        self.ai_models = {
            "image_classification": "mock_classifier_v1",
            "quality_assessment": "mock_quality_v1",
            "quantity_estimation": "mock_quantity_v1",
            "freshness_detection": "mock_freshness_v1"
        }
    
    async def create_product(
        self, 
        vendor_id: str, 
        product_data: ProductCreate
    ) -> Product:
        """Create a new product listing."""
        try:
            # Verify vendor exists
            vendor = await self.vendors_collection.find_one({"_id": ObjectId(vendor_id)})
            if not vendor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor not found"
                )
            
            # Create product
            product = Product(
                vendor_id=vendor_id,
                **product_data.dict()
            )
            
            # Insert into database
            result = await self.products_collection.insert_one(product.dict(by_alias=True))
            product.id = result.inserted_id
            
            logger.info(f"Created product {product.id} for vendor {vendor_id}")
            return product
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create product"
            )
    
    async def analyze_product_image(
        self, 
        image_data: bytes,
        product_id: Optional[str] = None
    ) -> ImageAnalysisResult:
        """Analyze product image using AI."""
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            
            # Mock AI analysis (in production, integrate with actual AI services)
            analysis_result = await self._mock_image_analysis(image, product_id)
            
            logger.info(f"Analyzed image for product {product_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}")
            # Return basic analysis result on error
            return ImageAnalysisResult(
                confidence_score=0.0,
                processing_metadata={"error": str(e)}
            )
    
    async def estimate_quantity(
        self, 
        images: List[bytes], 
        product_type: str
    ) -> Dict[str, Any]:
        """Estimate quantity from product images."""
        try:
            total_estimated_quantity = 0.0
            confidence_scores = []
            
            for image_data in images:
                image = Image.open(io.BytesIO(image_data))
                
                # Mock quantity estimation
                quantity, confidence = await self._mock_quantity_estimation(image, product_type)
                total_estimated_quantity += quantity
                confidence_scores.append(confidence)
            
            average_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            # Determine appropriate unit based on product type
            estimated_unit = self._determine_unit_from_product_type(product_type)
            
            return {
                "estimated_quantity": total_estimated_quantity,
                "unit": estimated_unit,
                "confidence": average_confidence,
                "images_analyzed": len(images),
                "method": "computer_vision_estimation"
            }
            
        except Exception as e:
            logger.error(f"Error estimating quantity: {e}")
            return {
                "estimated_quantity": 0.0,
                "unit": Unit.KG,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def assess_quality(
        self, 
        product_images: List[bytes], 
        product_category: str
    ) -> Dict[str, Any]:
        """Assess product quality from images."""
        try:
            quality_scores = []
            defects_found = []
            
            for image_data in product_images:
                image = Image.open(io.BytesIO(image_data))
                
                # Mock quality assessment
                quality_score, defects = await self._mock_quality_assessment(image, product_category)
                quality_scores.append(quality_score)
                defects_found.extend(defects)
            
            # Calculate overall quality
            average_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            
            # Determine quality grade
            if average_quality >= 0.8:
                quality_grade = QualityGrade.PREMIUM
            elif average_quality >= 0.6:
                quality_grade = QualityGrade.STANDARD
            else:
                quality_grade = QualityGrade.BELOW_STANDARD
            
            return {
                "quality_grade": quality_grade,
                "quality_score": average_quality,
                "defects_detected": list(set(defects_found)),
                "images_analyzed": len(product_images),
                "assessment_method": "ai_visual_inspection"
            }
            
        except Exception as e:
            logger.error(f"Error assessing quality: {e}")
            return {
                "quality_grade": QualityGrade.STANDARD,
                "quality_score": 0.5,
                "error": str(e)
            }
    
    async def detect_freshness(
        self, 
        image_data: bytes, 
        product_type: str
    ) -> Dict[str, Any]:
        """Detect freshness level for perishable goods."""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Mock freshness detection
            freshness_score, indicators = await self._mock_freshness_detection(image, product_type)
            
            # Determine freshness level
            if freshness_score >= 0.8:
                freshness_level = FreshnessLevel.VERY_FRESH
            elif freshness_score >= 0.6:
                freshness_level = FreshnessLevel.FRESH
            elif freshness_score >= 0.4:
                freshness_level = FreshnessLevel.MODERATE
            else:
                freshness_level = FreshnessLevel.POOR
            
            return {
                "freshness_level": freshness_level,
                "freshness_score": freshness_score,
                "indicators": indicators,
                "detection_method": "ai_freshness_analysis"
            }
            
        except Exception as e:
            logger.error(f"Error detecting freshness: {e}")
            return {
                "freshness_level": FreshnessLevel.MODERATE,
                "freshness_score": 0.5,
                "error": str(e)
            }
    
    async def scan_barcode(self, image_data: bytes) -> Optional[BarcodeInfo]:
        """Scan barcode or QR code from image."""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Mock barcode scanning (in production, use libraries like pyzbar)
            barcode_info = await self._mock_barcode_scanning(image)
            
            return barcode_info
            
        except Exception as e:
            logger.error(f"Error scanning barcode: {e}")
            return None
    
    async def search_products(
        self, 
        filters: ProductSearchFilters,
        pagination: PaginationParams,
        user_location: Optional[Dict[str, float]] = None
    ) -> ProductSearchResult:
        """Search products with filters."""
        try:
            # Build query
            query = {"status": "active"}
            
            if filters.category:
                query["category"] = filters.category
            
            if filters.subcategory:
                query["subcategory"] = filters.subcategory
            
            if filters.quality_grade:
                query["quality_grade"] = filters.quality_grade
            
            if filters.price_min or filters.price_max:
                price_query = {}
                if filters.price_min:
                    price_query["$gte"] = filters.price_min
                if filters.price_max:
                    price_query["$lte"] = filters.price_max
                query["price_info.base_price"] = price_query
            
            if filters.certifications:
                query["certifications"] = {"$in": filters.certifications}
            
            if filters.freshness_level:
                query["freshness_level"] = filters.freshness_level
            
            if filters.available_only:
                query["inventory_info.available_quantity"] = {"$gt": 0}
            
            if filters.featured_only:
                query["featured"] = True
            
            # Location-based filtering
            if user_location and filters.location_radius_km:
                # This would require geospatial indexing in production
                pass
            
            # Execute search
            cursor = self.products_collection.find(query)
            total_count = await self.products_collection.count_documents(query)
            
            # Apply pagination
            products_data = await cursor.skip(pagination.skip).limit(pagination.size).to_list(length=None)
            
            # Convert to Product objects
            products = [Product(**product_data) for product_data in products_data]
            
            return ProductSearchResult(
                products=products,
                total_count=total_count,
                filters_applied=filters
            )
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search products"
            )
    
    async def get_product_analytics(self, product_id: str) -> ProductAnalytics:
        """Get product analytics and performance metrics."""
        try:
            product = await self.products_collection.find_one({"_id": ObjectId(product_id)})
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product not found"
                )
            
            # Calculate analytics (mock implementation)
            analytics = ProductAnalytics(
                product_id=product_id,
                views_count=product.get("views_count", 0),
                inquiries_count=product.get("inquiries_count", 0),
                conversion_rate=0.15,  # Mock data
                average_rating=4.2,    # Mock data
                price_competitiveness=0.75,  # Mock data
                search_ranking=10,     # Mock data
                performance_score=0.8, # Mock data
                recommendations=[
                    "Consider adding more product images",
                    "Update product description with more details",
                    "Competitive pricing compared to market average"
                ]
            )
            
            return analytics
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting product analytics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get product analytics"
            )
    
    async def get_ai_product_suggestions(
        self, 
        vendor_id: str,
        market_context: Optional[Dict[str, Any]] = None
    ) -> List[AIProductSuggestion]:
        """Get AI-powered product suggestions for vendor."""
        try:
            # Mock AI suggestions (in production, use ML models)
            suggestions = [
                AIProductSuggestion(
                    suggested_category=ProductCategory.VEGETABLES,
                    suggested_subcategory=ProductSubcategory.ONION,
                    suggested_price_range={"min": 20.0, "max": 35.0},
                    market_demand_score=0.85,
                    competition_level="medium",
                    seasonal_factors=["High demand during festival season"],
                    reasoning="Based on your location and current market trends, onions show high demand with moderate competition."
                ),
                AIProductSuggestion(
                    suggested_category=ProductCategory.SPICES,
                    suggested_subcategory=ProductSubcategory.TURMERIC,
                    suggested_price_range={"min": 150.0, "max": 200.0},
                    market_demand_score=0.75,
                    competition_level="low",
                    seasonal_factors=["Consistent year-round demand"],
                    reasoning="Turmeric has consistent demand with low competition in your area."
                )
            ]
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting AI suggestions: {e}")
            return []
    
    # Mock AI methods (replace with actual AI service integrations)
    
    async def _mock_image_analysis(
        self, 
        image: Image.Image, 
        product_id: Optional[str] = None
    ) -> ImageAnalysisResult:
        """Mock image analysis."""
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        # Mock analysis based on image properties
        width, height = image.size
        
        # Simple heuristics for demo
        if width > 800 and height > 600:
            confidence = 0.85
            quality = QualityGrade.PREMIUM
        elif width > 400 and height > 300:
            confidence = 0.70
            quality = QualityGrade.STANDARD
        else:
            confidence = 0.50
            quality = QualityGrade.BELOW_STANDARD
        
        return ImageAnalysisResult(
            detected_category=ProductCategory.VEGETABLES,
            detected_subcategory=ProductSubcategory.TOMATO,
            confidence_score=confidence,
            quality_assessment=quality,
            freshness_level=FreshnessLevel.FRESH,
            quantity_estimate=5.0,
            estimated_unit=Unit.KG,
            defects_detected=[],
            processing_metadata={
                "image_size": f"{width}x{height}",
                "model_version": self.ai_models["image_classification"]
            }
        )
    
    async def _mock_quantity_estimation(
        self, 
        image: Image.Image, 
        product_type: str
    ) -> Tuple[float, float]:
        """Mock quantity estimation."""
        await asyncio.sleep(0.05)
        
        # Simple estimation based on image size
        width, height = image.size
        area = width * height
        
        # Mock estimation
        if area > 500000:  # Large image
            quantity = 10.0
            confidence = 0.8
        elif area > 200000:  # Medium image
            quantity = 5.0
            confidence = 0.7
        else:  # Small image
            quantity = 2.0
            confidence = 0.6
        
        return quantity, confidence
    
    async def _mock_quality_assessment(
        self, 
        image: Image.Image, 
        product_category: str
    ) -> Tuple[float, List[str]]:
        """Mock quality assessment."""
        await asyncio.sleep(0.05)
        
        # Mock assessment
        quality_score = 0.75
        defects = []
        
        # Simulate some defect detection
        if image.size[0] < 300:  # Low resolution might indicate poor quality
            quality_score -= 0.2
            defects.append("low_image_quality")
        
        return quality_score, defects
    
    async def _mock_freshness_detection(
        self, 
        image: Image.Image, 
        product_type: str
    ) -> Tuple[float, List[str]]:
        """Mock freshness detection."""
        await asyncio.sleep(0.05)
        
        # Mock freshness analysis
        freshness_score = 0.8
        indicators = ["good_color", "firm_texture"]
        
        return freshness_score, indicators
    
    async def _mock_barcode_scanning(self, image: Image.Image) -> Optional[BarcodeInfo]:
        """Mock barcode scanning."""
        await asyncio.sleep(0.05)
        
        # Mock barcode detection (very simplified)
        if image.size[0] > 200 and image.size[1] > 200:
            return BarcodeInfo(
                code="1234567890123",
                format="EAN13",
                product_name="Sample Product",
                manufacturer="Sample Manufacturer"
            )
        
        return None
    
    def _determine_unit_from_product_type(self, product_type: str) -> Unit:
        """Determine appropriate unit based on product type."""
        unit_mapping = {
            "vegetables": Unit.KG,
            "fruits": Unit.KG,
            "grains": Unit.QUINTAL,
            "spices": Unit.KG,
            "dairy": Unit.LITER,
            "processed_food": Unit.PIECE
        }
        
        return unit_mapping.get(product_type.lower(), Unit.KG)