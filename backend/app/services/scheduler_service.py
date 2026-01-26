"""
Scheduler service for background tasks and cron jobs.
"""
import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, Any, Optional, Callable, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.services.agmarknet_service import agmarknet_service
from app.services.price_discovery_service import price_discovery_service
from app.db.mongodb import get_database
from app.db.redis import get_redis

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled background tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.job_status: Dict[str, Dict[str, Any]] = {}
    
    async def start(self):
        """Start the scheduler and register all jobs."""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        try:
            # Register scheduled jobs
            await self._register_jobs()
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            logger.info("Scheduler service started successfully")
            
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
            raise
    
    async def stop(self):
        """Stop the scheduler."""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("Scheduler service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    async def _register_jobs(self):
        """Register all scheduled jobs."""
        try:
            # Daily AGMARKNET data fetch - Run every day at 6 AM IST
            self.scheduler.add_job(
                func=self._fetch_daily_agmarknet_data,
                trigger=CronTrigger(hour=6, minute=0, timezone='Asia/Kolkata'),
                id='daily_agmarknet_fetch',
                name='Daily AGMARKNET Data Fetch',
                replace_existing=True,
                max_instances=1
            )
            
            # Hourly price updates for active commodities - Every hour during market hours
            self.scheduler.add_job(
                func=self._fetch_hourly_price_updates,
                trigger=CronTrigger(
                    hour='9-17',  # 9 AM to 5 PM IST
                    minute=0,
                    timezone='Asia/Kolkata'
                ),
                id='hourly_price_updates',
                name='Hourly Price Updates',
                replace_existing=True,
                max_instances=1
            )
            
            # Cache cleanup - Every 30 minutes
            self.scheduler.add_job(
                func=self._cleanup_expired_cache,
                trigger=IntervalTrigger(minutes=30),
                id='cache_cleanup',
                name='Cache Cleanup',
                replace_existing=True,
                max_instances=1
            )
            
            # Price alerts check - Every 15 minutes during market hours
            self.scheduler.add_job(
                func=self._check_price_alerts,
                trigger=IntervalTrigger(minutes=15),
                id='price_alerts_check',
                name='Price Alerts Check',
                replace_existing=True,
                max_instances=1
            )
            
            # Weekly trend analysis - Every Sunday at 8 PM IST
            self.scheduler.add_job(
                func=self._generate_weekly_trends,
                trigger=CronTrigger(
                    day_of_week='sun',
                    hour=20,
                    minute=0,
                    timezone='Asia/Kolkata'
                ),
                id='weekly_trend_analysis',
                name='Weekly Trend Analysis',
                replace_existing=True,
                max_instances=1
            )
            
            # Database maintenance - Every day at 2 AM IST
            self.scheduler.add_job(
                func=self._database_maintenance,
                trigger=CronTrigger(hour=2, minute=0, timezone='Asia/Kolkata'),
                id='database_maintenance',
                name='Database Maintenance',
                replace_existing=True,
                max_instances=1
            )
            
            logger.info("All scheduled jobs registered successfully")
            
        except Exception as e:
            logger.error(f"Error registering jobs: {str(e)}")
            raise
    
    async def _fetch_daily_agmarknet_data(self):
        """Fetch daily AGMARKNET data for all major commodities."""
        job_id = 'daily_agmarknet_fetch'
        
        try:
            logger.info("Starting daily AGMARKNET data fetch")
            
            # Update job status
            self.job_status[job_id] = {
                'status': 'running',
                'started_at': datetime.utcnow(),
                'message': 'Fetching daily AGMARKNET data'
            }
            
            # List of major commodities to fetch
            major_commodities = [
                'Rice', 'Wheat', 'Onion', 'Potato', 'Tomato',
                'Sugar', 'Cotton', 'Turmeric', 'Chili', 'Coriander',
                'Soybean', 'Groundnut', 'Mustard', 'Jowar', 'Bajra'
            ]
            
            total_records = 0
            failed_commodities = []
            
            for commodity in major_commodities:
                try:
                    # Fetch data for each commodity
                    price_data = await agmarknet_service.fetch_daily_rates(
                        commodity=commodity
                    )
                    
                    if price_data:
                        # Store in database
                        stored_count = await agmarknet_service.store_price_data(price_data)
                        total_records += stored_count
                        logger.info(f"Stored {stored_count} records for {commodity}")
                    else:
                        logger.warning(f"No data received for {commodity}")
                        failed_commodities.append(commodity)
                    
                    # Small delay to avoid overwhelming the API
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error fetching data for {commodity}: {str(e)}")
                    failed_commodities.append(commodity)
            
            # Update job status
            self.job_status[job_id] = {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'message': f'Fetched {total_records} records',
                'total_records': total_records,
                'failed_commodities': failed_commodities
            }
            
            logger.info(f"Daily AGMARKNET fetch completed: {total_records} records")
            
        except Exception as e:
            logger.error(f"Error in daily AGMARKNET fetch: {str(e)}")
            self.job_status[job_id] = {
                'status': 'failed',
                'failed_at': datetime.utcnow(),
                'error': str(e)
            }
    
    async def _fetch_hourly_price_updates(self):
        """Fetch hourly price updates for active commodities."""
        job_id = 'hourly_price_updates'
        
        try:
            logger.info("Starting hourly price updates")
            
            self.job_status[job_id] = {
                'status': 'running',
                'started_at': datetime.utcnow(),
                'message': 'Fetching hourly price updates'
            }
            
            # Get list of active commodities (those with recent queries)
            active_commodities = await self._get_active_commodities()
            
            if not active_commodities:
                logger.info("No active commodities found for hourly updates")
                return
            
            total_updates = 0
            
            for commodity in active_commodities:
                try:
                    # Fetch latest prices
                    price_data = await agmarknet_service.fetch_daily_rates(
                        commodity=commodity
                    )
                    
                    if price_data:
                        stored_count = await agmarknet_service.store_price_data(price_data)
                        total_updates += stored_count
                    
                    await asyncio.sleep(1)  # Short delay
                    
                except Exception as e:
                    logger.error(f"Error updating prices for {commodity}: {str(e)}")
            
            self.job_status[job_id] = {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'message': f'Updated {total_updates} price records',
                'total_updates': total_updates
            }
            
            logger.info(f"Hourly price updates completed: {total_updates} records")
            
        except Exception as e:
            logger.error(f"Error in hourly price updates: {str(e)}")
            self.job_status[job_id] = {
                'status': 'failed',
                'failed_at': datetime.utcnow(),
                'error': str(e)
            }
    
    async def _cleanup_expired_cache(self):
        """Clean up expired cache entries."""
        job_id = 'cache_cleanup'
        
        try:
            logger.info("Starting cache cleanup")
            
            redis = await get_redis()
            
            # Get all keys with TTL
            keys_cleaned = 0
            
            # Clean up price cache keys older than 1 hour
            pattern = "current_prices:*"
            async for key in redis.scan_iter(match=pattern):
                ttl = await redis.ttl(key)
                if ttl == -1:  # No expiration set
                    await redis.expire(key, 3600)  # Set 1 hour expiration
                elif ttl == -2:  # Key doesn't exist
                    keys_cleaned += 1
            
            # Clean up translation cache keys older than 24 hours
            pattern = "translation:*"
            async for key in redis.scan_iter(match=pattern):
                ttl = await redis.ttl(key)
                if ttl == -1:
                    await redis.expire(key, 86400)  # Set 24 hour expiration
            
            self.job_status[job_id] = {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'keys_cleaned': keys_cleaned
            }
            
            logger.info(f"Cache cleanup completed: {keys_cleaned} keys processed")
            
        except Exception as e:
            logger.error(f"Error in cache cleanup: {str(e)}")
            self.job_status[job_id] = {
                'status': 'failed',
                'failed_at': datetime.utcnow(),
                'error': str(e)
            }
    
    async def _check_price_alerts(self):
        """Check and trigger price alerts."""
        job_id = 'price_alerts_check'
        
        try:
            logger.info("Checking price alerts")
            
            db = await get_database()
            alerts_collection = db.price_alerts
            
            # Get active price alerts
            active_alerts = await alerts_collection.find({"is_active": True}).to_list(length=None)
            
            if not active_alerts:
                return
            
            alerts_triggered = 0
            
            for alert_doc in active_alerts:
                try:
                    # Get current price for the commodity
                    current_prices = await price_discovery_service.get_current_prices(
                        commodity=alert_doc['commodity'],
                        location=alert_doc.get('location')
                    )
                    
                    if not current_prices:
                        continue
                    
                    # Calculate average current price
                    avg_price = sum(pd.price_modal for pd in current_prices) / len(current_prices)
                    
                    # Check alert conditions
                    should_trigger = False
                    
                    if alert_doc['alert_type'] == 'above' and avg_price > alert_doc['threshold_price']:
                        should_trigger = True
                    elif alert_doc['alert_type'] == 'below' and avg_price < alert_doc['threshold_price']:
                        should_trigger = True
                    elif alert_doc['alert_type'] == 'change' and alert_doc.get('percentage_change'):
                        # Check percentage change (implementation needed)
                        pass
                    
                    if should_trigger:
                        # Trigger alert (send notification, email, etc.)
                        await self._trigger_price_alert(alert_doc, avg_price)
                        alerts_triggered += 1
                        
                        # Update last triggered time
                        await alerts_collection.update_one(
                            {"_id": alert_doc["_id"]},
                            {"$set": {"last_triggered": datetime.utcnow()}}
                        )
                
                except Exception as e:
                    logger.error(f"Error processing alert {alert_doc.get('_id')}: {str(e)}")
            
            self.job_status[job_id] = {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'alerts_checked': len(active_alerts),
                'alerts_triggered': alerts_triggered
            }
            
            logger.info(f"Price alerts check completed: {alerts_triggered} alerts triggered")
            
        except Exception as e:
            logger.error(f"Error checking price alerts: {str(e)}")
            self.job_status[job_id] = {
                'status': 'failed',
                'failed_at': datetime.utcnow(),
                'error': str(e)
            }
    
    async def _generate_weekly_trends(self):
        """Generate weekly trend analysis for major commodities."""
        job_id = 'weekly_trend_analysis'
        
        try:
            logger.info("Generating weekly trend analysis")
            
            self.job_status[job_id] = {
                'status': 'running',
                'started_at': datetime.utcnow(),
                'message': 'Generating weekly trends'
            }
            
            # Get major commodities
            major_commodities = [
                'Rice', 'Wheat', 'Onion', 'Potato', 'Tomato',
                'Sugar', 'Cotton', 'Turmeric'
            ]
            
            trends_generated = 0
            
            for commodity in major_commodities:
                try:
                    # Generate trend analysis
                    trend = await price_discovery_service.get_price_trends(
                        commodity=commodity,
                        period='weekly'
                    )
                    
                    # Store trend analysis in database
                    db = await get_database()
                    trends_collection = db.market_trends
                    
                    await trends_collection.replace_one(
                        {
                            "commodity": commodity,
                            "time_period": "weekly"
                        },
                        trend.dict(),
                        upsert=True
                    )
                    
                    trends_generated += 1
                    
                except Exception as e:
                    logger.error(f"Error generating trend for {commodity}: {str(e)}")
            
            self.job_status[job_id] = {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'trends_generated': trends_generated
            }
            
            logger.info(f"Weekly trend analysis completed: {trends_generated} trends generated")
            
        except Exception as e:
            logger.error(f"Error generating weekly trends: {str(e)}")
            self.job_status[job_id] = {
                'status': 'failed',
                'failed_at': datetime.utcnow(),
                'error': str(e)
            }
    
    async def _database_maintenance(self):
        """Perform database maintenance tasks."""
        job_id = 'database_maintenance'
        
        try:
            logger.info("Starting database maintenance")
            
            db = await get_database()
            
            # Clean up old price data (older than 2 years)
            cutoff_date = datetime.utcnow() - timedelta(days=730)
            
            result = await db.price_data.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            old_records_deleted = result.deleted_count
            
            # Update database indexes
            await self._ensure_database_indexes(db)
            
            self.job_status[job_id] = {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'old_records_deleted': old_records_deleted
            }
            
            logger.info(f"Database maintenance completed: {old_records_deleted} old records deleted")
            
        except Exception as e:
            logger.error(f"Error in database maintenance: {str(e)}")
            self.job_status[job_id] = {
                'status': 'failed',
                'failed_at': datetime.utcnow(),
                'error': str(e)
            }
    
    async def _get_active_commodities(self) -> List[str]:
        """Get list of commodities with recent query activity."""
        try:
            redis = await get_redis()
            
            # Get commodities from recent cache keys
            active_commodities = set()
            
            pattern = "current_prices:*"
            async for key in redis.scan_iter(match=pattern):
                # Extract commodity from cache key
                parts = key.decode().split(':')
                if len(parts) >= 2:
                    active_commodities.add(parts[1])
            
            # Fallback to major commodities if no activity
            if not active_commodities:
                active_commodities = {
                    'Rice', 'Wheat', 'Onion', 'Potato', 'Tomato'
                }
            
            return list(active_commodities)
            
        except Exception as e:
            logger.error(f"Error getting active commodities: {str(e)}")
            return ['Rice', 'Wheat', 'Onion']  # Fallback
    
    async def _trigger_price_alert(self, alert_doc: Dict[str, Any], current_price: float):
        """Trigger a price alert notification."""
        try:
            # Here you would implement notification logic:
            # - Send email
            # - Send SMS
            # - Push notification
            # - Store in notifications collection
            
            logger.info(f"Price alert triggered for user {alert_doc['user_id']}: "
                       f"{alert_doc['commodity']} price is {current_price}")
            
            # Store notification in database
            db = await get_database()
            notifications_collection = db.notifications
            
            notification = {
                "user_id": alert_doc["user_id"],
                "type": "price_alert",
                "title": f"Price Alert: {alert_doc['commodity']}",
                "message": f"Current price: ₹{current_price:.2f}",
                "data": {
                    "commodity": alert_doc["commodity"],
                    "current_price": current_price,
                    "threshold_price": alert_doc["threshold_price"],
                    "alert_type": alert_doc["alert_type"]
                },
                "created_at": datetime.utcnow(),
                "read": False
            }
            
            await notifications_collection.insert_one(notification)
            
        except Exception as e:
            logger.error(f"Error triggering price alert: {str(e)}")
    
    async def _ensure_database_indexes(self, db):
        """Ensure proper database indexes exist."""
        try:
            # Price data indexes
            await db.price_data.create_index([
                ("commodity", 1),
                ("date", -1)
            ])
            
            await db.price_data.create_index([
                ("location.state", 1),
                ("location.district", 1)
            ])
            
            await db.price_data.create_index([
                ("created_at", -1)
            ])
            
            # User indexes
            await db.users.create_index([("email", 1)], unique=True)
            await db.users.create_index([("phone", 1)], unique=True)
            
            # Price alerts indexes
            await db.price_alerts.create_index([
                ("user_id", 1),
                ("is_active", 1)
            ])
            
            logger.info("Database indexes ensured")
            
        except Exception as e:
            logger.error(f"Error ensuring database indexes: {str(e)}")
    
    def get_job_status(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """Get status of scheduled jobs."""
        if job_id:
            return self.job_status.get(job_id, {"status": "not_found"})
        
        return self.job_status
    
    def get_scheduler_info(self) -> Dict[str, Any]:
        """Get scheduler information."""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "is_running": self.is_running,
            "jobs": jobs,
            "job_count": len(jobs)
        }


# Global scheduler instance
scheduler_service = SchedulerService()