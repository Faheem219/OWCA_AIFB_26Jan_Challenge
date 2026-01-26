"""
Image upload and management service for the Multilingual Mandi Marketplace Platform.

This service handles image uploads, processing, and cloud storage integration.
"""

import logging
import os
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from PIL import Image
import io
import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import ValidationException
from app.models.product import ImageReference

logger = logging.getLogger(__name__)


class ImageService:
    """Image service for handling uploads and processing."""
    
    def __init__(self):
        """Initialize image service with AWS S3 client."""
        self.s3_client = None
        self.bucket_name = getattr(settings, 'AWS_S3_BUCKET', 'mandi-marketplace-images')
        
        # Initialize S3 client if AWS credentials are available
        try:
            if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=getattr(settings, 'AWS_REGION', 'ap-south-1')
                )
            else:
                logger.warning("AWS credentials not configured, using local file storage")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            self.s3_client = None
    
    async def upload_product_image(
        self,
        image_data: bytes,
        filename: str,
        product_id: str,
        content_type: str = "image/jpeg"
    ) -> ImageReference:
        """
        Upload a product image to cloud storage.
        
        Args:
            image_data: Image binary data
            filename: Original filename
            product_id: Product ID
            content_type: Image content type
            
        Returns:
            ImageReference with URLs and metadata
            
        Raises:
            ValidationException: If image is invalid or upload fails
        """
        try:
            # Validate image
            self._validate_image(image_data, filename)
            
            # Generate unique image ID and filename
            image_id = str(uuid.uuid4())
            file_extension = self._get_file_extension(filename)
            s3_key = f"products/{product_id}/{image_id}{file_extension}"
            
            # Process image (resize, optimize)
            processed_image, thumbnail_image, dimensions = await self._process_image(image_data)
            
            # Upload to cloud storage
            if self.s3_client:
                image_url = await self._upload_to_s3(processed_image, s3_key, content_type)
                thumbnail_url = await self._upload_to_s3(
                    thumbnail_image, 
                    f"products/{product_id}/thumbnails/{image_id}{file_extension}",
                    content_type
                )
            else:
                # Fallback to local storage for development
                image_url = await self._upload_to_local(processed_image, s3_key)
                thumbnail_url = await self._upload_to_local(
                    thumbnail_image,
                    f"products/{product_id}/thumbnails/{image_id}{file_extension}"
                )
            
            # Create image reference
            image_ref = ImageReference(
                image_id=image_id,
                image_url=image_url,
                thumbnail_url=thumbnail_url,
                alt_text=None,
                is_primary=False,
                uploaded_at=datetime.utcnow(),
                file_size=len(processed_image),
                dimensions=dimensions
            )
            
            return image_ref
            
        except Exception as e:
            logger.error(f"Failed to upload product image: {e}")
            raise ValidationException(f"Image upload failed: {str(e)}")
    
    async def delete_product_image(
        self,
        image_id: str,
        product_id: str
    ) -> bool:
        """
        Delete a product image from cloud storage.
        
        Args:
            image_id: Image ID to delete
            product_id: Product ID
            
        Returns:
            True if deletion was successful
        """
        try:
            # Construct S3 keys
            s3_key = f"products/{product_id}/{image_id}"
            thumbnail_key = f"products/{product_id}/thumbnails/{image_id}"
            
            if self.s3_client:
                # Delete from S3
                try:
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
                    self.s3_client.delete_object(Bucket=self.bucket_name, Key=thumbnail_key)
                except ClientError as e:
                    logger.warning(f"Failed to delete image from S3: {e}")
            else:
                # Delete from local storage
                await self._delete_from_local(s3_key)
                await self._delete_from_local(thumbnail_key)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete product image {image_id}: {e}")
            return False
    
    async def get_upload_presigned_url(
        self,
        product_id: str,
        filename: str,
        content_type: str = "image/jpeg"
    ) -> Dict[str, str]:
        """
        Generate a presigned URL for direct client upload to S3.
        
        Args:
            product_id: Product ID
            filename: Original filename
            content_type: Image content type
            
        Returns:
            Dictionary with presigned URL and fields
            
        Raises:
            ValidationException: If S3 is not configured
        """
        try:
            if not self.s3_client:
                raise ValidationException("Cloud storage not configured")
            
            # Generate unique filename
            image_id = str(uuid.uuid4())
            file_extension = self._get_file_extension(filename)
            s3_key = f"products/{product_id}/{image_id}{file_extension}"
            
            # Generate presigned POST URL
            response = self.s3_client.generate_presigned_post(
                Bucket=self.bucket_name,
                Key=s3_key,
                Fields={"Content-Type": content_type},
                Conditions=[
                    {"Content-Type": content_type},
                    ["content-length-range", 1024, 10 * 1024 * 1024]  # 1KB to 10MB
                ],
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                "upload_url": response["url"],
                "fields": response["fields"],
                "image_id": image_id,
                "s3_key": s3_key
            }
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise ValidationException(f"Failed to generate upload URL: {str(e)}")
    
    # Private helper methods
    
    def _validate_image(self, image_data: bytes, filename: str) -> None:
        """Validate image data and format."""
        # Check file size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            raise ValidationException("Image file size cannot exceed 10MB")
        
        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        file_extension = self._get_file_extension(filename).lower()
        if file_extension not in valid_extensions:
            raise ValidationException(f"Invalid image format. Supported formats: {', '.join(valid_extensions)}")
        
        # Validate image can be opened
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Check image dimensions
                width, height = img.size
                if width < 100 or height < 100:
                    raise ValidationException("Image dimensions must be at least 100x100 pixels")
                if width > 4000 or height > 4000:
                    raise ValidationException("Image dimensions cannot exceed 4000x4000 pixels")
        except Exception as e:
            raise ValidationException(f"Invalid image file: {str(e)}")
    
    def _get_file_extension(self, filename: str) -> str:
        """Get file extension from filename."""
        return os.path.splitext(filename)[1].lower()
    
    async def _process_image(self, image_data: bytes) -> tuple[bytes, bytes, Dict[str, int]]:
        """
        Process image: resize, optimize, and create thumbnail.
        
        Returns:
            Tuple of (processed_image_data, thumbnail_data, dimensions)
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                original_width, original_height = img.size
                
                # Resize main image if too large (max 1200px on longest side)
                max_size = 1200
                if max(original_width, original_height) > max_size:
                    if original_width > original_height:
                        new_width = max_size
                        new_height = int((original_height * max_size) / original_width)
                    else:
                        new_height = max_size
                        new_width = int((original_width * max_size) / original_height)
                    
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Save processed image
                processed_buffer = io.BytesIO()
                img.save(processed_buffer, format='JPEG', quality=85, optimize=True)
                processed_data = processed_buffer.getvalue()
                
                # Create thumbnail (300x300)
                thumbnail_size = (300, 300)
                thumbnail_img = img.copy()
                thumbnail_img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                thumbnail_buffer = io.BytesIO()
                thumbnail_img.save(thumbnail_buffer, format='JPEG', quality=80, optimize=True)
                thumbnail_data = thumbnail_buffer.getvalue()
                
                dimensions = {"width": img.width, "height": img.height}
                
                return processed_data, thumbnail_data, dimensions
                
        except Exception as e:
            logger.error(f"Failed to process image: {e}")
            raise ValidationException(f"Image processing failed: {str(e)}")
    
    async def _upload_to_s3(self, image_data: bytes, s3_key: str, content_type: str) -> str:
        """Upload image data to S3."""
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=image_data,
                ContentType=content_type,
                CacheControl='max-age=31536000',  # 1 year cache
                Metadata={
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'service': 'mandi-marketplace'
                }
            )
            
            # Return public URL
            return f"https://{self.bucket_name}.s3.{getattr(settings, 'AWS_REGION', 'ap-south-1')}.amazonaws.com/{s3_key}"
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise ValidationException(f"Cloud upload failed: {str(e)}")
    
    async def _upload_to_local(self, image_data: bytes, file_path: str) -> str:
        """Upload image data to local storage (development fallback)."""
        try:
            # Create local uploads directory
            local_dir = "uploads"
            os.makedirs(local_dir, exist_ok=True)
            
            # Create subdirectories
            full_path = os.path.join(local_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            # Write file
            with open(full_path, 'wb') as f:
                f.write(image_data)
            
            # Return local URL (assuming served by static file server)
            return f"/uploads/{file_path}"
            
        except Exception as e:
            logger.error(f"Failed to upload to local storage: {e}")
            raise ValidationException(f"Local upload failed: {str(e)}")
    
    async def _delete_from_local(self, file_path: str) -> None:
        """Delete file from local storage."""
        try:
            full_path = os.path.join("uploads", file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
        except Exception as e:
            logger.warning(f"Failed to delete local file {file_path}: {e}")
    
    def get_image_info(self, image_data: bytes) -> Dict[str, Any]:
        """
        Get information about an image.
        
        Args:
            image_data: Image binary data
            
        Returns:
            Dictionary with image information
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                return {
                    "format": img.format,
                    "mode": img.mode,
                    "size": img.size,
                    "width": img.width,
                    "height": img.height,
                    "file_size": len(image_data)
                }
        except Exception as e:
            logger.error(f"Failed to get image info: {e}")
            return {}
    
    def is_image_valid(self, image_data: bytes) -> bool:
        """
        Check if image data is valid.
        
        Args:
            image_data: Image binary data
            
        Returns:
            True if image is valid
        """
        try:
            with Image.open(io.BytesIO(image_data)) as img:
                img.verify()
            return True
        except Exception:
            return False