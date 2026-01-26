"""
Custom exceptions for the Multilingual Mandi Marketplace Platform.

This module defines custom exception classes for different types of errors
that can occur in the application.
"""

from typing import Any, Dict, Optional


class MandiMarketplaceException(Exception):
    """Base exception class for all application-specific exceptions."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(MandiMarketplaceException):
    """Exception raised for data validation errors."""
    pass


class AuthenticationException(MandiMarketplaceException):
    """Exception raised for authentication failures."""
    pass


class AuthorizationException(MandiMarketplaceException):
    """Exception raised for authorization failures."""
    pass


class NotFoundException(MandiMarketplaceException):
    """Exception raised when a requested resource is not found."""
    pass


class ConflictException(MandiMarketplaceException):
    """Exception raised for resource conflicts (e.g., duplicate email)."""
    pass


class ExternalServiceException(MandiMarketplaceException):
    """Exception raised for external service failures."""
    
    def __init__(self, message: str, service: str, details: Optional[Dict[str, Any]] = None):
        self.service = service
        super().__init__(message, details)


class TranslationException(ExternalServiceException):
    """Exception raised for translation service failures."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "translation_service", details)


class PriceDiscoveryException(ExternalServiceException):
    """Exception raised for price discovery service failures."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "price_discovery_service", details)


class PaymentException(ExternalServiceException):
    """Exception raised for payment processing failures."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "payment_service", details)


class FileUploadException(MandiMarketplaceException):
    """Exception raised for file upload failures."""
    pass


class RateLimitException(MandiMarketplaceException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message)


class DatabaseException(MandiMarketplaceException):
    """Exception raised for database operation failures."""
    pass


class CacheException(MandiMarketplaceException):
    """Exception raised for cache operation failures."""
    pass


class WebSocketException(MandiMarketplaceException):
    """Exception raised for WebSocket connection failures."""
    pass


class AIServiceException(ExternalServiceException):
    """Exception raised for AI service failures."""
    
    def __init__(self, message: str, service: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, f"ai_service_{service}", details)