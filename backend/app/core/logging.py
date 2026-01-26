"""
Logging configuration for the Multilingual Mandi Marketplace Platform.

This module sets up structured logging with proper formatting and handlers
for development and production environments.
"""

import logging
import logging.config
import sys
from typing import Dict, Any

from app.core.config import settings


def setup_logging() -> None:
    """
    Setup application logging configuration.
    """
    
    # Define log format based on environment
    if settings.LOG_FORMAT == "json":
        # Use standard formatter for now, can add JSON later if needed
        formatter_class = "logging.Formatter"
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    else:
        formatter_class = "logging.Formatter"
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Logging configuration
    config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "class": formatter_class,
                "format": format_string,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default",
                "stream": sys.stdout,
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": settings.LOG_LEVEL,
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
            "fastapi": {
                "level": "INFO",
                "handlers": ["console"],
                "propagate": False,
            },
        },
    }
    
    # Add file handler for production
    if not settings.DEBUG:
        config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": settings.LOG_LEVEL,
            "formatter": "default",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
        
        # Add file handler to all loggers
        for logger_config in config["loggers"].values():
            logger_config["handlers"].append("file")
    
    # Apply configuration
    logging.config.dictConfig(config)
    
    # Set third-party library log levels
    logging.getLogger("motor").setLevel(logging.WARNING)
    logging.getLogger("pymongo").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {settings.LOG_LEVEL}")


class ContextFilter(logging.Filter):
    """
    Custom logging filter to add request context to log records.
    """
    
    def filter(self, record):
        # Add custom fields to log record
        record.service = "mandi-marketplace-api"
        record.environment = settings.ENVIRONMENT
        return True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with proper configuration.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.addFilter(ContextFilter())
    return logger