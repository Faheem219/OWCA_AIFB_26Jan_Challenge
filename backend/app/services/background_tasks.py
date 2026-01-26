"""
Background tasks for market data synchronization and maintenance.

This module contains background tasks for periodic data synchronization,
cache management, and data quality monitoring.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List

from ..core.config import settings
from ..core.database import get_database
from .market_data_service import MarketDataService

logger = logging.getLogger(__name__)


class BackgroundTaskService:
    """Service for managing background tasks."""
    
    def __init__(self):
        self.market_data_service = None
        self.is_running = False
        
        # Common commodities to sync
        self.default_commodities = [
            "onion", "potato", "tomato", "rice", "wheat", "maize",
            "apple", "banana", "mango", "orange", "grapes",
            "turmeric", "coriander", "cumin", "chilli",
            "milk", "ghee", "paneer"
        ]
    
    async def initialize(self):
        """Initialize the background task service."""
        database = await get_database()
        self.market_data_service = MarketDataService(database)
        await self.market_data_service.initialize()
        logger.info("Background task service initialized")
    
    async def start_periodic_tasks(self):
        """Start all periodic background tasks."""
        if self.is_running:
            logger.warning("Background tasks are already running")
            return
        
        self.is_running = True
        logger.info("Starting periodic background tasks")
        
        # Start tasks concurrently
        tasks = [
            self._market_data_sync_task(),
            self._data_quality_monitoring_task(),
            self._cache_cleanup_task(),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Error in background tasks: {e}")
            self.is_running = False
            raise
    
    async def stop_periodic_tasks(self):
        """Stop all periodic background tasks."""
        self.is_running = False
        logger.info("Stopping periodic background tasks")
    
    async def _market_data_sync_task(self):
        """Periodic task to sync market data from external sources."""
        logger.info("Starting market data sync task")
        
        while self.is_running:
            try:
                # Sync data every 6 hours
                await asyncio.sleep(6 * 3600)  # 6 hours
                
                if not self.is_running:
                    break
                
                logger.info("Starting scheduled market data sync")
                sync_status = await self.market_data_service.sync_external_data(
                    self.default_commodities
                )
                
                if sync_status.sync_status == "completed":
                    logger.info(f"Market data sync completed: {sync_status.records_synced} records synced")
                else:
                    logger.warning(f"Market data sync completed with errors: {sync_status.errors}")
                
            except Exception as e:
                logger.error(f"Error in market data sync task: {e}")
                # Continue running even if one sync fails
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    async def _data_quality_monitoring_task(self):
        """Periodic task to monitor data quality and cleanup invalid data."""
        logger.info("Starting data quality monitoring task")
        
        while self.is_running:
            try:
                # Run quality checks every 12 hours
                await asyncio.sleep(12 * 3600)  # 12 hours
                
                if not self.is_running:
                    break
                
                logger.info("Starting data quality monitoring")
                await self._check_data_quality()
                await self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"Error in data quality monitoring task: {e}")
                await asyncio.sleep(3600)  # Wait 1 hour before retrying
    
    async def _cache_cleanup_task(self):
        """Periodic task to cleanup expired cache entries."""
        logger.info("Starting cache cleanup task")
        
        while self.is_running:
            try:
                # Cleanup cache every 2 hours
                await asyncio.sleep(2 * 3600)  # 2 hours
                
                if not self.is_running:
                    break
                
                logger.info("Starting cache cleanup")
                await self._cleanup_expired_cache()
                
            except Exception as e:
                logger.error(f"Error in cache cleanup task: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes before retrying
    
    async def _check_data_quality(self):
        """Check and report data quality issues."""
        try:
            # Get recent market data for quality analysis
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            cursor = self.market_data_service.market_prices_collection.find({
                "last_updated": {"$gte": cutoff_date}
            })
            
            total_records = 0
            quality_issues = 0
            
            async for record in cursor:
                total_records += 1
                
                # Check for quality issues
                if not record.get("is_validated", False):
                    quality_issues += 1
                elif record.get("data_quality") == "unverified":
                    quality_issues += 1
            
            if total_records > 0:
                quality_percentage = ((total_records - quality_issues) / total_records) * 100
                logger.info(f"Data quality check: {quality_percentage:.1f}% of {total_records} records are high quality")
                
                if quality_percentage < 80:
                    logger.warning(f"Data quality below threshold: {quality_percentage:.1f}%")
            else:
                logger.warning("No recent market data found for quality analysis")
                
        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
    
    async def _cleanup_old_data(self):
        """Remove old market data to manage storage."""
        try:
            # Remove data older than 1 year
            cutoff_date = datetime.utcnow() - timedelta(days=365)
            
            result = await self.market_data_service.market_prices_collection.delete_many({
                "date": {"$lt": cutoff_date.date()}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old market price records")
            
            # Remove old price history records
            result = await self.market_data_service.price_history_collection.delete_many({
                "period_end": {"$lt": cutoff_date.date()}
            })
            
            if result.deleted_count > 0:
                logger.info(f"Cleaned up {result.deleted_count} old price history records")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    async def _cleanup_expired_cache(self):
        """Remove expired cache entries from Redis."""
        try:
            if not self.market_data_service.redis_client:
                return
            
            # Get all cache keys with market data prefix
            pattern = "market_price:*"
            keys = await self.market_data_service.redis_client.keys(pattern)
            
            expired_count = 0
            for key in keys:
                ttl = await self.market_data_service.redis_client.ttl(key)
                if ttl == -1:  # Key exists but has no expiration
                    # Set expiration for keys without TTL
                    await self.market_data_service.redis_client.expire(key, settings.PRICE_CACHE_TTL)
                elif ttl == -2:  # Key doesn't exist (already expired)
                    expired_count += 1
            
            if expired_count > 0:
                logger.info(f"Found {expired_count} expired cache entries")
                
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    async def sync_commodity_data(self, commodity: str) -> bool:
        """
        Manually sync data for a specific commodity.
        
        Args:
            commodity: Commodity name to sync
            
        Returns:
            True if sync was successful, False otherwise
        """
        try:
            logger.info(f"Manual sync requested for commodity: {commodity}")
            
            sync_status = await self.market_data_service.sync_external_data([commodity])
            
            if sync_status.sync_status == "completed":
                logger.info(f"Manual sync completed for {commodity}: {sync_status.records_synced} records")
                return True
            else:
                logger.warning(f"Manual sync completed with errors for {commodity}: {sync_status.errors}")
                return False
                
        except Exception as e:
            logger.error(f"Error in manual sync for {commodity}: {e}")
            return False
    
    async def get_sync_status(self) -> dict:
        """
        Get current synchronization status.
        
        Returns:
            Dictionary with sync status information
        """
        try:
            # Get latest sync status from database
            sync_record = await self.market_data_service.data_sync_status_collection.find_one(
                {"source": "agmarknet"},
                sort=[("last_sync", -1)]
            )
            
            if sync_record:
                return {
                    "last_sync": sync_record.get("last_sync"),
                    "next_sync": sync_record.get("next_sync"),
                    "sync_status": sync_record.get("sync_status"),
                    "records_synced": sync_record.get("records_synced", 0),
                    "errors": sync_record.get("errors", []),
                    "is_running": self.is_running
                }
            else:
                return {
                    "last_sync": None,
                    "next_sync": None,
                    "sync_status": "never_run",
                    "records_synced": 0,
                    "errors": [],
                    "is_running": self.is_running
                }
                
        except Exception as e:
            logger.error(f"Error getting sync status: {e}")
            return {
                "last_sync": None,
                "next_sync": None,
                "sync_status": "error",
                "records_synced": 0,
                "errors": [str(e)],
                "is_running": self.is_running
            }
    
    async def cleanup(self):
        """Cleanup resources."""
        self.is_running = False
        if self.market_data_service:
            await self.market_data_service.cleanup()


# Global instance
background_task_service = BackgroundTaskService()


async def get_background_task_service() -> BackgroundTaskService:
    """Dependency to get background task service."""
    if not background_task_service.market_data_service:
        await background_task_service.initialize()
    return background_task_service