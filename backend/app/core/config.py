"""
Configuration settings for the Multilingual Mandi Marketplace Platform.

This module contains all configuration settings loaded from environment variables
with proper validation and type checking using Pydantic Settings.
"""

import os
from typing import List, Optional
from pydantic import validator, AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application settings
    NODE_ENV: str = "development"
    PYTHON_ENV: str = "development"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    RELOAD: bool = True
    WORKERS: int = 1
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Database settings
    MONGODB_URL: str
    MONGODB_DATABASE: str = "mandi_marketplace"
    REDIS_URL: str
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    
    # Security settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS and host settings
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost:80"
    ALLOWED_HOSTS: str = "localhost,127.0.0.1,0.0.0.0"
    
    # AWS settings for AI services
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "ap-south-1"
    AWS_TRANSLATE_REGION: str = "ap-south-1"
    AWS_SAGEMAKER_REGION: str = "ap-south-1"
    
    # Google OAuth settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    
    # External API settings
    AGMARKNET_API_KEY: str
    AGMARKNET_BASE_URL: str = "https://api.data.gov.in/resource"
    
    # Payment gateway settings
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    UPI_MERCHANT_ID: str
    
    # File upload settings
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_IMAGE_TYPES: str = "jpg,jpeg,png,webp"
    UPLOAD_DIRECTORY: str = "uploads"
    
    # Cache settings
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    TRANSLATION_CACHE_TTL: int = 86400  # 24 hours
    PRICE_CACHE_TTL: int = 1800  # 30 minutes
    
    # Feature flags
    ENABLE_VOICE_MESSAGES: bool = True
    ENABLE_AI_MODERATION: bool = True
    ENABLE_PRICE_PREDICTION: bool = True
    ENABLE_OFFLINE_MODE: bool = True
    
    # Supported languages
    SUPPORTED_LANGUAGES: List[str] = [
        "hi",  # Hindi
        "en",  # English
        "ta",  # Tamil
        "te",  # Telugu
        "kn",  # Kannada
        "ml",  # Malayalam
        "gu",  # Gujarati
        "pa",  # Punjabi
        "bn",  # Bengali
        "mr",  # Marathi
    ]
    
    # Product categories
    PRODUCT_CATEGORIES: List[str] = [
        "VEGETABLES",
        "FRUITS",
        "GRAINS",
        "SPICES",
        "DAIRY",
    ]
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [i.strip() for i in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS
    
    def get_allowed_hosts(self) -> List[str]:
        """Get allowed hosts as a list."""
        if isinstance(self.ALLOWED_HOSTS, str):
            return [i.strip() for i in self.ALLOWED_HOSTS.split(",")]
        return self.ALLOWED_HOSTS
    
    def get_allowed_image_types(self) -> List[str]:
        """Get allowed image types as a list."""
        if isinstance(self.ALLOWED_IMAGE_TYPES, str):
            return [i.strip() for i in self.ALLOWED_IMAGE_TYPES.split(",")]
        return self.ALLOWED_IMAGE_TYPES
    
    @validator("MAX_FILE_SIZE_MB")
    def validate_file_size(cls, v):
        if v <= 0 or v > 100:
            raise ValueError("MAX_FILE_SIZE_MB must be between 1 and 100")
        return v
    
    @validator("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    def validate_token_expire_minutes(cls, v):
        if v <= 0:
            raise ValueError("JWT_ACCESS_TOKEN_EXPIRE_MINUTES must be positive")
        return v
    
    @validator("JWT_REFRESH_TOKEN_EXPIRE_DAYS")
    def validate_refresh_token_expire_days(cls, v):
        if v <= 0:
            raise ValueError("JWT_REFRESH_TOKEN_EXPIRE_DAYS must be positive")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env


# Create global settings instance
settings = Settings()