"""
Personalized Insights and Recommendations Service.

Implements user behavior tracking, trading pattern recognition,
and personalized market insights generation.
"""
import asyncio
import logging
import statistics
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any, Tuple
import json
import math
from collections import defaultdict, Counter

from app.core.config import settings
from app.models.personalized_insights import (
    UserBehaviorEvent, TradingPattern, PersonalizedInsight, PersonalizedRecommendation,
    UserProfile, InsightGenerationConfig, SimilarUserGroup, RecommendationFeedback,
    BehaviorAnalysisResult, MarketOpportunity, UserBehaviorType, TradingPatternType,
    InsightType, RecommendationType, ConfidenceLevel, PersonalizedInsightsRequest,
    PersonalizedRecommendationsRequest
)
from app.models.common import TrendDirection
from app.services.market_analytics_service import market_analytics_service
from app.services.price_discovery_service import price_discovery_service
from app.db.mongodb import get_database
from app.db.redis import get_redis

logger = logging.getLogger(__name__)


class PersonalizedInsightsService:
    """Service for personalized insights and recommendations."""
    
    def __init__(self):
        self.cache_ttl = 1800  # 30 minutes cache for insights
        self.behavior_analysis_window_days = 90
        self.pattern_min_events = 10
        self.insight_relevance_threshold = 0.6
        self.recommendation_confidence_threshold = 0.7
        
        # Pattern detection thresholds
        self.pattern_thresholds = {
            TradingPatternType.BULK_BUYER: {"min_avg_quantity": 1000, "min_transactions": 5},
            TradingPatternType.FREQUENT_TRADER: {"min_frequency_per_month": 8, "min_transactions": 20},
            TradingPatternType.SEASONAL_TRADER: {"seasonality_score": 0.7, "min_transactions": 10},
            TradingPatternType.PRICE_SENSITIVE: {"price_sensitivity_score": 0.8, "min_transactions": 15},
            TradingPatternType.QUALITY_FOCUSED: {"quality_preference_score": 0.7, "min_transactions": 10},
        }
    
    async def track_user_behavior(self, behavior_event: UserBehaviorEvent) -> bool:
        """
        Track user behavior event for analysis.
        
        Args:
            behavior_event: User behavior event to track
            
        Returns:
            bool: Success status
        """
        try:
            db = await get_database()
            
            # Store behavior event
            await db.user_behavior_events.insert_one(behavior_event.dict())
            
            # Update user profile asynchronously
            asyncio.create_task(self._update_user_profile_from_behavior(behavior_event))
            
            # Cache recent behavior for quick access
            redis = await get_redis()
            cache_key = f"recent_behavior:{behavior_event.user_id}"
            
            # Add to recent behavior list (keep last 100 events)
            await redis.lpush(cache_key, json.dumps(behavior_event.dict(), default=str))
            await redis.ltrim(cache_key, 0, 99)
            await redis.expire(cache_key, 86400)  # 24 hours
            
            logger.info(f"Tracked behavior event: {behavior_event.event_type} for user {behavior_event.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking user behavior: {str(e)}")
            return False
    
    async def analyze_user_behavior(self, user_id: str) -> BehaviorAnalysisResult:
        """
        Analyze user behavior and identify trading patterns.
        
        Args:
            user_id: User ID to analyze
            
        Returns:
            BehaviorAnalysisResult with identified patterns and insights
        """
        try:
            db = await get_database()
            
            # Get behavior events for analysis period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.behavior_analysis_window_days)
            
            cursor = db.user_behavior_events.find({
                "user_id": user_id,
                "timestamp": {"$gte": start_date, "$lte": end_date}
            }).sort("timestamp", 1)
            
            events = await cursor.to_list(length=10000)
            
            if len(events) < self.pattern_min_events:
                return BehaviorAnalysisResult(
                    user_id=user_id,
                    period_start=start_date,
                    period_end=end_date,
                    total_events=len(events),
                    activity_level="low",
                    engagement_score=0.0,
                    consistency_score=0.0,
                    confidence_in_analysis=0.0
                )
            
            # Analyze patterns
            patterns = await self._identify_trading_patterns(user_id, events)
            
            # Calculate engagement metrics
            engagement_score = self._calculate_engagement_score(events)
            consistency_score = self._calculate_consistency_score(events)
            activity_level = self._determine_activity_level(events)
            
            # Identify learning indicators
            learning_indicators = self._identify_learning_indicators(events)
            
            # Detect pattern changes
            pattern_changes = await self._detect_pattern_changes(user_id, patterns)
            
            return BehaviorAnalysisResult(
                user_id=user_id,
                period_start=start_date,
                period_end=end_date,
                total_events=len(events),
                patterns=patterns,
                pattern_changes=pattern_changes,
                activity_level=activity_level,
                engagement_score=engagement_score,
                consistency_score=consistency_score,
                learning_indicators=learning_indicators,
                confidence_in_analysis=min(1.0, len(events) / 100.0)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing user behavior: {str(e)}")
            raise
    
    async def generate_personalized_insights(
        self, 
        request: PersonalizedInsightsRequest
    ) -> List[PersonalizedInsight]:
        """
        Generate personalized market insights for a user.
        
        Args:
            request: Request parameters for insight generation
            
        Returns:
            List of PersonalizedInsight objects
        """
        try:
            # Get user profile
            user_profile = await self._get_or_create_user_profile(request.user_id)
            
            # Get market data relevant to user
            market_data = await self._get_relevant_market_data(user_profile, request)
            
            insights = []
            
            # Generate different types of insights
            if not request.insight_types or InsightType.PRICE_OPPORTUNITY in request.insight_types:
                price_insights = await self._generate_price_opportunity_insights(
                    user_profile, market_data, request
                )
                insights.extend(price_insights)
            
            if not request.insight_types or InsightType.SEASONAL_TREND in request.insight_types:
                seasonal_insights = await self._generate_seasonal_trend_insights(
                    user_profile, market_data, request
                )
                insights.extend(seasonal_insights)
            
            if not request.insight_types or InsightType.TRADING_PATTERN in request.insight_types:
                pattern_insights = await self._generate_trading_pattern_insights(
                    user_profile, request
                )
                insights.extend(pattern_insights)
            
            if not request.insight_types or InsightType.MARKET_SHIFT in request.insight_types:
                market_shift_insights = await self._generate_market_shift_insights(
                    user_profile, market_data, request
                )
                insights.extend(market_shift_insights)
            
            # Filter by confidence and relevance
            filtered_insights = [
                insight for insight in insights
                if (not request.min_confidence or 
                    self._confidence_to_score(insight.confidence) >= self._confidence_to_score(request.min_confidence))
                and insight.relevance_score >= self.insight_relevance_threshold
            ]
            
            # Sort by priority and relevance
            filtered_insights.sort(key=lambda x: (x.priority, -x.relevance_score))
            
            # Limit results
            return filtered_insights[:request.max_results]
            
        except Exception as e:
            logger.error(f"Error generating personalized insights: {str(e)}")
            return []
    
    async def generate_personalized_recommendations(
        self, 
        request: PersonalizedRecommendationsRequest
    ) -> List[PersonalizedRecommendation]:
        """
        Generate personalized recommendations for a user.
        
        Args:
            request: Request parameters for recommendation generation
            
        Returns:
            List of PersonalizedRecommendation objects
        """
        try:
            # Get user profile
            user_profile = await self._get_or_create_user_profile(request.user_id)
            
            # Get market opportunities
            opportunities = await self._identify_market_opportunities(user_profile, request)
            
            recommendations = []
            
            # Generate different types of recommendations
            if not request.recommendation_types or RecommendationType.BUY_OPPORTUNITY in request.recommendation_types:
                buy_recommendations = await self._generate_buy_opportunity_recommendations(
                    user_profile, opportunities, request
                )
                recommendations.extend(buy_recommendations)
            
            if not request.recommendation_types or RecommendationType.SELL_OPPORTUNITY in request.recommendation_types:
                sell_recommendations = await self._generate_sell_opportunity_recommendations(
                    user_profile, opportunities, request
                )
                recommendations.extend(sell_recommendations)
            
            if not request.recommendation_types or RecommendationType.TIMING_OPTIMIZATION in request.recommendation_types:
                timing_recommendations = await self._generate_timing_optimization_recommendations(
                    user_profile, request
                )
                recommendations.extend(timing_recommendations)
            
            if not request.recommendation_types or RecommendationType.DIVERSIFICATION in request.recommendation_types:
                diversification_recommendations = await self._generate_diversification_recommendations(
                    user_profile, request
                )
                recommendations.extend(diversification_recommendations)
            
            # Filter by confidence
            filtered_recommendations = [
                rec for rec in recommendations
                if (not request.min_confidence or 
                    self._confidence_to_score(rec.confidence) >= self._confidence_to_score(request.min_confidence))
                and self._confidence_to_score(rec.confidence) >= self.recommendation_confidence_threshold
            ]
            
            # Sort by priority and relevance
            filtered_recommendations.sort(key=lambda x: (x.priority, -x.relevance_score))
            
            # Limit results
            return filtered_recommendations[:request.max_results]
            
        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {str(e)}")
            return []
    
    async def update_user_profile(self, user_id: str) -> UserProfile:
        """
        Update user profile based on recent behavior.
        
        Args:
            user_id: User ID to update profile for
            
        Returns:
            Updated UserProfile
        """
        try:
            # Analyze recent behavior
            analysis_result = await self.analyze_user_behavior(user_id)
            
            # Get or create user profile
            user_profile = await self._get_or_create_user_profile(user_id)
            
            # Update profile with analysis results
            user_profile.identified_patterns = analysis_result.patterns
            
            if analysis_result.patterns:
                # Set primary pattern (highest confidence)
                primary_pattern = max(analysis_result.patterns, key=lambda p: p.confidence)
                user_profile.primary_pattern = primary_pattern.pattern_type
                user_profile.pattern_confidence = primary_pattern.confidence
            
            # Update preferences from patterns
            await self._update_preferences_from_patterns(user_profile, analysis_result.patterns)
            
            # Update trading characteristics
            await self._update_trading_characteristics(user_profile, user_id)
            
            # Update engagement metrics
            user_profile.last_updated = datetime.utcnow()
            user_profile.total_behavior_events = analysis_result.total_events
            
            # Save updated profile
            db = await get_database()
            await db.user_profiles.replace_one(
                {"user_id": user_id},
                user_profile.dict(),
                upsert=True
            )
            
            return user_profile
            
        except Exception as e:
            logger.error(f"Error updating user profile: {str(e)}")
            raise
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile with behavioral insights.
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile if exists, None otherwise
        """
        try:
            db = await get_database()
            profile_doc = await db.user_profiles.find_one({"user_id": user_id})
            
            if profile_doc:
                return UserProfile(**profile_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return None
    
    async def record_recommendation_feedback(
        self, 
        feedback: RecommendationFeedback
    ) -> bool:
        """
        Record feedback on recommendations for learning.
        
        Args:
            feedback: Recommendation feedback
            
        Returns:
            bool: Success status
        """
        try:
            db = await get_database()
            
            # Calculate time to feedback
            if feedback.recommendation_created_at:
                time_diff = feedback.submitted_at - feedback.recommendation_created_at
                feedback.time_to_feedback_hours = time_diff.total_seconds() / 3600
            
            # Store feedback
            await db.recommendation_feedback.insert_one(feedback.dict())
            
            # Update recommendation with feedback
            await db.personalized_recommendations.update_one(
                {"recommendation_id": feedback.recommendation_id},
                {
                    "$set": {
                        "feedback_rating": feedback.rating,
                        "feedback_comment": feedback.comment,
                        "outcome": "successful" if feedback.outcome_successful else "failed"
                    }
                }
            )
            
            # Use feedback to improve future recommendations
            asyncio.create_task(self._learn_from_feedback(feedback))
            
            return True
            
        except Exception as e:
            logger.error(f"Error recording recommendation feedback: {str(e)}")
            return False
    
    # Helper methods for pattern identification
    
    async def _identify_trading_patterns(
        self, 
        user_id: str, 
        events: List[Dict[str, Any]]
    ) -> List[TradingPattern]:
        """Identify trading patterns from user behavior events."""
        patterns = []
        
        # Filter transaction events
        transaction_events = [e for e in events if e.get("event_type") == UserBehaviorType.TRANSACTION.value]
        
        if len(transaction_events) < self.pattern_min_events:
            return patterns
        
        # Calculate pattern scores
        pattern_scores = {}
        
        # Bulk buyer pattern
        if len(transaction_events) >= self.pattern_thresholds[TradingPatternType.BULK_BUYER]["min_transactions"]:
            avg_quantity = statistics.mean([e.get("quantity", 0) for e in transaction_events if e.get("quantity")])
            if avg_quantity >= self.pattern_thresholds[TradingPatternType.BULK_BUYER]["min_avg_quantity"]:
                pattern_scores[TradingPatternType.BULK_BUYER] = min(1.0, avg_quantity / 5000)
        
        # Frequent trader pattern
        if len(transaction_events) >= self.pattern_thresholds[TradingPatternType.FREQUENT_TRADER]["min_transactions"]:
            # Calculate monthly frequency
            months_span = max(1, (events[-1]["timestamp"] - events[0]["timestamp"]).days / 30)
            monthly_frequency = len(transaction_events) / months_span
            
            if monthly_frequency >= self.pattern_thresholds[TradingPatternType.FREQUENT_TRADER]["min_frequency_per_month"]:
                pattern_scores[TradingPatternType.FREQUENT_TRADER] = min(1.0, monthly_frequency / 20)
        
        # Seasonal trader pattern
        if len(transaction_events) >= self.pattern_thresholds[TradingPatternType.SEASONAL_TRADER]["min_transactions"]:
            seasonality_score = self._calculate_seasonality_score(transaction_events)
            if seasonality_score >= self.pattern_thresholds[TradingPatternType.SEASONAL_TRADER]["seasonality_score"]:
                pattern_scores[TradingPatternType.SEASONAL_TRADER] = seasonality_score
        
        # Price sensitive pattern
        price_events = [e for e in events if e.get("event_type") == UserBehaviorType.PRICE_CHECK.value]
        if len(price_events) >= 10 and len(transaction_events) >= self.pattern_thresholds[TradingPatternType.PRICE_SENSITIVE]["min_transactions"]:
            price_sensitivity = len(price_events) / len(transaction_events)
            if price_sensitivity >= 2.0:  # At least 2 price checks per transaction
                pattern_scores[TradingPatternType.PRICE_SENSITIVE] = min(1.0, price_sensitivity / 5.0)
        
        # Quality focused pattern
        if len(transaction_events) >= self.pattern_thresholds[TradingPatternType.QUALITY_FOCUSED]["min_transactions"]:
            quality_focus_score = self._calculate_quality_focus_score(transaction_events)
            if quality_focus_score >= self.pattern_thresholds[TradingPatternType.QUALITY_FOCUSED]["quality_preference_score"]:
                pattern_scores[TradingPatternType.QUALITY_FOCUSED] = quality_focus_score
        
        # Create pattern objects
        for pattern_type, confidence in pattern_scores.items():
            if confidence >= 0.6:  # Minimum confidence threshold
                pattern = await self._create_trading_pattern(user_id, pattern_type, confidence, transaction_events)
                patterns.append(pattern)
        
        return patterns
    
    async def _create_trading_pattern(
        self, 
        user_id: str, 
        pattern_type: TradingPatternType, 
        confidence: float,
        transaction_events: List[Dict[str, Any]]
    ) -> TradingPattern:
        """Create a trading pattern object from transaction events."""
        
        # Extract pattern characteristics
        commodities = [e.get("commodity") for e in transaction_events if e.get("commodity")]
        locations = [e.get("location") for e in transaction_events if e.get("location")]
        quantities = [e.get("quantity") for e in transaction_events if e.get("quantity")]
        values = [e.get("transaction_value") for e in transaction_events if e.get("transaction_value")]
        
        # Calculate scores
        frequency_score = len(transaction_events) / 30.0  # Normalize to monthly
        volume_score = statistics.mean(quantities) if quantities else 0.0
        seasonality_score = self._calculate_seasonality_score(transaction_events)
        
        # Get preferred items
        commodity_counts = Counter(commodities)
        location_counts = Counter(locations)
        
        preferred_commodities = [item for item, count in commodity_counts.most_common(5)]
        preferred_locations = [item for item, count in location_counts.most_common(3)]
        
        # Calculate ranges
        quantity_range = None
        if quantities:
            quantity_range = {"min": min(quantities), "max": max(quantities), "avg": statistics.mean(quantities)}
        
        value_range = None
        if values:
            value_range = {"min": min(values), "max": max(values), "avg": statistics.mean(values)}
        
        # Get peak trading months
        months = [datetime.fromisoformat(e["timestamp"]).month for e in transaction_events]
        month_counts = Counter(months)
        peak_months = [month for month, count in month_counts.most_common(3)]
        
        return TradingPattern(
            user_id=user_id,
            pattern_type=pattern_type,
            confidence=confidence,
            frequency_score=min(1.0, frequency_score),
            volume_score=min(1.0, volume_score / 1000.0),  # Normalize
            seasonality_score=seasonality_score,
            preferred_commodities=preferred_commodities,
            preferred_locations=preferred_locations,
            typical_quantity_range=quantity_range,
            typical_price_range=value_range,
            peak_trading_months=peak_months,
            sample_size=len(transaction_events),
            pattern_strength=confidence
        )
    
    def _calculate_seasonality_score(self, transaction_events: List[Dict[str, Any]]) -> float:
        """Calculate how seasonal the user's trading behavior is."""
        if len(transaction_events) < 12:  # Need at least a year of data
            return 0.0
        
        # Group transactions by month
        monthly_counts = defaultdict(int)
        for event in transaction_events:
            month = datetime.fromisoformat(event["timestamp"]).month
            monthly_counts[month] += 1
        
        # Calculate coefficient of variation
        counts = list(monthly_counts.values())
        if len(counts) < 3:
            return 0.0
        
        mean_count = statistics.mean(counts)
        if mean_count == 0:
            return 0.0
        
        std_dev = statistics.stdev(counts)
        coefficient_of_variation = std_dev / mean_count
        
        # Convert to 0-1 scale (higher CV = more seasonal)
        return min(1.0, coefficient_of_variation)
    
    def _calculate_quality_focus_score(self, transaction_events: List[Dict[str, Any]]) -> float:
        """Calculate how quality-focused the user is."""
        quality_grades = [e.get("quality_grade") for e in transaction_events if e.get("quality_grade")]
        
        if not quality_grades:
            return 0.0
        
        # Count premium/high quality transactions
        premium_count = sum(1 for grade in quality_grades if grade in ["premium", "high", "A", "grade_a"])
        
        return premium_count / len(quality_grades)
    
    def _calculate_engagement_score(self, events: List[Dict[str, Any]]) -> float:
        """Calculate user engagement score."""
        if not events:
            return 0.0
        
        # Factors for engagement
        total_events = len(events)
        unique_days = len(set(datetime.fromisoformat(e["timestamp"]).date() for e in events))
        event_types = len(set(e["event_type"] for e in events))
        
        # Normalize scores
        frequency_score = min(1.0, total_events / 100.0)
        consistency_score = min(1.0, unique_days / 30.0)
        diversity_score = min(1.0, event_types / 8.0)  # 8 different event types
        
        return (frequency_score + consistency_score + diversity_score) / 3.0
    
    def _calculate_consistency_score(self, events: List[Dict[str, Any]]) -> float:
        """Calculate consistency of user behavior."""
        if len(events) < 7:
            return 0.0
        
        # Group events by week
        weekly_counts = defaultdict(int)
        for event in events:
            week = datetime.fromisoformat(event["timestamp"]).isocalendar()[1]
            weekly_counts[week] += 1
        
        counts = list(weekly_counts.values())
        if len(counts) < 2:
            return 0.0
        
        # Lower coefficient of variation = higher consistency
        mean_count = statistics.mean(counts)
        if mean_count == 0:
            return 0.0
        
        std_dev = statistics.stdev(counts)
        cv = std_dev / mean_count
        
        # Convert to consistency score (inverse of CV)
        return max(0.0, 1.0 - cv)
    
    def _determine_activity_level(self, events: List[Dict[str, Any]]) -> str:
        """Determine user activity level."""
        if not events:
            return "low"
        
        # Calculate events per day
        days_span = max(1, (datetime.fromisoformat(events[-1]["timestamp"]) - 
                           datetime.fromisoformat(events[0]["timestamp"])).days)
        events_per_day = len(events) / days_span
        
        if events_per_day >= 2.0:
            return "high"
        elif events_per_day >= 0.5:
            return "medium"
        else:
            return "low"
    
    def _identify_learning_indicators(self, events: List[Dict[str, Any]]) -> List[str]:
        """Identify indicators that user is learning/improving."""
        indicators = []
        
        # Check for increasing feature usage
        feature_usage = defaultdict(list)
        for event in events:
            timestamp = datetime.fromisoformat(event["timestamp"])
            feature_usage[event["event_type"]].append(timestamp)
        
        for feature, timestamps in feature_usage.items():
            if len(timestamps) >= 5:
                # Check if usage is increasing over time
                recent_usage = sum(1 for ts in timestamps if ts > datetime.utcnow() - timedelta(days=30))
                early_usage = sum(1 for ts in timestamps if ts < datetime.utcnow() - timedelta(days=60))
                
                if recent_usage > early_usage * 1.5:
                    indicators.append(f"increasing_{feature}_usage")
        
        # Check for price checking behavior before transactions
        transaction_events = [e for e in events if e.get("event_type") == UserBehaviorType.TRANSACTION.value]
        price_check_events = [e for e in events if e.get("event_type") == UserBehaviorType.PRICE_CHECK.value]
        
        if len(price_check_events) > len(transaction_events):
            indicators.append("price_conscious_behavior")
        
        return indicators
    
    # Helper methods for insight generation
    
    async def _get_or_create_user_profile(self, user_id: str) -> UserProfile:
        """Get existing user profile or create a new one."""
        profile = await self.get_user_profile(user_id)
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            
            # Initialize with basic data if available
            db = await get_database()
            user_doc = await db.users.find_one({"_id": user_id})
            
            if user_doc:
                # Set basic preferences from user data
                if user_doc.get("vendor_profile"):
                    vendor_profile = user_doc["vendor_profile"]
                    profile.preferred_commodities = vendor_profile.get("specializations", [])
                    if vendor_profile.get("location"):
                        profile.preferred_locations = [vendor_profile["location"].get("city", "")]
        
        return profile
    
    async def _get_relevant_market_data(
        self, 
        user_profile: UserProfile, 
        request: PersonalizedInsightsRequest
    ) -> Dict[str, Any]:
        """Get market data relevant to the user's interests."""
        market_data = {}
        
        # Determine commodities to analyze
        commodities = request.commodities or user_profile.preferred_commodities[:5]
        if not commodities:
            commodities = ["rice", "wheat", "onion"]  # Default commodities
        
        # Determine locations
        locations = request.locations or user_profile.preferred_locations[:3]
        
        # Get current prices
        for commodity in commodities:
            try:
                prices = await price_discovery_service.get_current_prices(commodity)
                if prices:
                    market_data[f"{commodity}_prices"] = prices
                
                # Get price trends
                trends = await price_discovery_service.get_price_trends(commodity, "30_days")
                if trends:
                    market_data[f"{commodity}_trends"] = trends
                
            except Exception as e:
                logger.warning(f"Error getting market data for {commodity}: {str(e)}")
        
        # Get market analytics
        for commodity in commodities[:2]:  # Limit to avoid too many API calls
            try:
                analytics = await market_analytics_service.generate_comprehensive_analytics(
                    commodity=commodity,
                    location=locations[0] if locations else None
                )
                market_data[f"{commodity}_analytics"] = analytics
                
            except Exception as e:
                logger.warning(f"Error getting analytics for {commodity}: {str(e)}")
        
        return market_data
    
    async def _generate_price_opportunity_insights(
        self, 
        user_profile: UserProfile, 
        market_data: Dict[str, Any], 
        request: PersonalizedInsightsRequest
    ) -> List[PersonalizedInsight]:
        """Generate price opportunity insights."""
        insights = []
        
        for commodity in user_profile.preferred_commodities[:3]:
            price_key = f"{commodity}_prices"
            trend_key = f"{commodity}_trends"
            
            if price_key in market_data and trend_key in market_data:
                prices = market_data[price_key]
                trends = market_data[trend_key]
                
                # Look for price opportunities
                if prices and trends:
                    current_price = statistics.mean([p.price_modal for p in prices])
                    
                    # Check if current price is significantly below recent average
                    if hasattr(trends, 'price_points') and trends.price_points:
                        recent_avg = statistics.mean([pp.price for pp in trends.price_points[-7:]])
                        price_diff_pct = ((current_price - recent_avg) / recent_avg) * 100
                        
                        if price_diff_pct < -10:  # Price is 10% below recent average
                            insight = PersonalizedInsight(
                                user_id=user_profile.user_id,
                                insight_type=InsightType.PRICE_OPPORTUNITY,
                                title=f"Price Opportunity: {commodity.title()}",
                                description=f"Current {commodity} prices are {abs(price_diff_pct):.1f}% below recent average. This could be a good buying opportunity.",
                                commodity=commodity,
                                current_price=current_price,
                                predicted_price=recent_avg,
                                price_change_percentage=price_diff_pct,
                                trend_direction=TrendDirection.FALLING,
                                confidence=ConfidenceLevel.MEDIUM,
                                relevance_score=self._calculate_commodity_relevance(commodity, user_profile),
                                priority=2,
                                supporting_factors=[
                                    f"Current price: ₹{current_price:.2f}",
                                    f"Recent average: ₹{recent_avg:.2f}",
                                    "Price below historical average"
                                ],
                                data_sources=["price_discovery", "trend_analysis"]
                            )
                            insights.append(insight)
        
        return insights
    
    async def _generate_seasonal_trend_insights(
        self, 
        user_profile: UserProfile, 
        market_data: Dict[str, Any], 
        request: PersonalizedInsightsRequest
    ) -> List[PersonalizedInsight]:
        """Generate seasonal trend insights."""
        insights = []
        
        current_month = datetime.now().month
        
        for commodity in user_profile.preferred_commodities[:3]:
            analytics_key = f"{commodity}_analytics"
            
            if analytics_key in market_data:
                analytics = market_data[analytics_key]
                
                # Check for seasonal alerts
                if hasattr(analytics, 'active_alerts') and analytics.active_alerts:
                    for alert in analytics.active_alerts:
                        if alert.alert_type == "seasonal" and abs(alert.expected_demand_change) > 15:
                            insight = PersonalizedInsight(
                                user_id=user_profile.user_id,
                                insight_type=InsightType.SEASONAL_TREND,
                                title=f"Seasonal Trend: {commodity.title()}",
                                description=f"Seasonal demand for {commodity} is expected to {'increase' if alert.expected_demand_change > 0 else 'decrease'} by {abs(alert.expected_demand_change):.1f}% due to {alert.event_name}.",
                                commodity=commodity,
                                price_change_percentage=alert.expected_demand_change * 0.8,  # Price usually follows demand
                                trend_direction=TrendDirection.RISING if alert.expected_demand_change > 0 else TrendDirection.FALLING,
                                confidence=ConfidenceLevel.HIGH if alert.severity.value == "high" else ConfidenceLevel.MEDIUM,
                                relevance_score=self._calculate_commodity_relevance(commodity, user_profile),
                                priority=1 if alert.severity.value == "high" else 2,
                                supporting_factors=[
                                    f"Event: {alert.event_name}",
                                    f"Expected demand change: {alert.expected_demand_change:.1f}%",
                                    f"Historical pattern: {alert.historical_data}"
                                ],
                                data_sources=["seasonal_analysis", "market_analytics"],
                                valid_until=alert.event_end_date
                            )
                            insights.append(insight)
        
        return insights
    
    async def _generate_trading_pattern_insights(
        self, 
        user_profile: UserProfile, 
        request: PersonalizedInsightsRequest
    ) -> List[PersonalizedInsight]:
        """Generate insights based on user's trading patterns."""
        insights = []
        
        if not user_profile.identified_patterns:
            return insights
        
        primary_pattern = user_profile.identified_patterns[0]  # Highest confidence pattern
        
        # Generate pattern-specific insights
        if primary_pattern.pattern_type == TradingPatternType.SEASONAL_TRADER:
            current_month = datetime.now().month
            if current_month in primary_pattern.peak_trading_months:
                insight = PersonalizedInsight(
                    user_id=user_profile.user_id,
                    insight_type=InsightType.TRADING_PATTERN,
                    title="Peak Trading Season",
                    description=f"Based on your trading history, this is typically one of your most active trading months. Consider preparing for increased activity.",
                    confidence=ConfidenceLevel.HIGH,
                    relevance_score=0.9,
                    priority=1,
                    supporting_factors=[
                        f"Historical peak months: {primary_pattern.peak_trading_months}",
                        f"Pattern confidence: {primary_pattern.confidence:.1f}",
                        "Seasonal trading pattern identified"
                    ],
                    data_sources=["behavior_analysis", "pattern_recognition"]
                )
                insights.append(insight)
        
        elif primary_pattern.pattern_type == TradingPatternType.PRICE_SENSITIVE:
            insight = PersonalizedInsight(
                user_id=user_profile.user_id,
                insight_type=InsightType.TRADING_PATTERN,
                title="Price-Sensitive Trading Detected",
                description="Your trading pattern shows high price sensitivity. Consider setting up price alerts for your preferred commodities to catch good deals.",
                confidence=ConfidenceLevel.HIGH,
                relevance_score=0.8,
                priority=2,
                supporting_factors=[
                    f"Price sensitivity score: {primary_pattern.price_sensitivity_score:.1f}",
                    "High price checking frequency",
                    "Pattern suggests price-conscious behavior"
                ],
                data_sources=["behavior_analysis", "pattern_recognition"]
            )
            insights.append(insight)
        
        return insights
    
    async def _generate_market_shift_insights(
        self, 
        user_profile: UserProfile, 
        market_data: Dict[str, Any], 
        request: PersonalizedInsightsRequest
    ) -> List[PersonalizedInsight]:
        """Generate market shift insights."""
        insights = []
        
        for commodity in user_profile.preferred_commodities[:2]:
            analytics_key = f"{commodity}_analytics"
            
            if analytics_key in market_data:
                analytics = market_data[analytics_key]
                
                # Check for significant market sentiment changes
                if hasattr(analytics, 'overall_market_sentiment'):
                    if analytics.overall_market_sentiment in ["bullish", "bearish"]:
                        insight = PersonalizedInsight(
                            user_id=user_profile.user_id,
                            insight_type=InsightType.MARKET_SHIFT,
                            title=f"Market Sentiment Shift: {commodity.title()}",
                            description=f"Market sentiment for {commodity} has turned {analytics.overall_market_sentiment}. This could impact prices in the coming weeks.",
                            commodity=commodity,
                            trend_direction=TrendDirection.RISING if analytics.overall_market_sentiment == "bullish" else TrendDirection.FALLING,
                            confidence=ConfidenceLevel.MEDIUM,
                            relevance_score=self._calculate_commodity_relevance(commodity, user_profile),
                            priority=2,
                            supporting_factors=[
                                f"Market sentiment: {analytics.overall_market_sentiment}",
                                f"Confidence score: {analytics.confidence_score:.1f}",
                                f"Risk assessment: {analytics.risk_assessment}"
                            ],
                            data_sources=["market_analytics", "sentiment_analysis"]
                        )
                        insights.append(insight)
        
        return insights
    
    def _calculate_commodity_relevance(self, commodity: str, user_profile: UserProfile) -> float:
        """Calculate how relevant a commodity is to the user."""
        relevance = 0.0
        
        # Check if it's in preferred commodities
        if commodity in user_profile.preferred_commodities:
            position = user_profile.preferred_commodities.index(commodity)
            relevance += 1.0 - (position * 0.1)  # Higher relevance for top preferences
        
        # Check trading history
        if commodity in user_profile.preferred_commodities:
            relevance += 0.3
        
        # Check if user has trading patterns related to this commodity
        for pattern in user_profile.identified_patterns:
            if commodity in pattern.preferred_commodities:
                relevance += pattern.confidence * 0.2
        
        return min(1.0, relevance)
    
    def _confidence_to_score(self, confidence: ConfidenceLevel) -> float:
        """Convert confidence level to numeric score."""
        mapping = {
            ConfidenceLevel.LOW: 0.3,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.HIGH: 0.8,
            ConfidenceLevel.VERY_HIGH: 0.95
        }
        return mapping.get(confidence, 0.5)
    
    # Helper methods for recommendation generation
    
    async def _identify_market_opportunities(
        self, 
        user_profile: UserProfile, 
        request: PersonalizedRecommendationsRequest
    ) -> List[MarketOpportunity]:
        """Identify market opportunities relevant to the user."""
        opportunities = []
        
        commodities = request.commodities or user_profile.preferred_commodities[:3]
        locations = request.locations or user_profile.preferred_locations[:2]
        
        for commodity in commodities:
            for location in locations or [None]:
                try:
                    # Get current prices
                    prices = await price_discovery_service.get_current_prices(commodity, location)
                    if not prices:
                        continue
                    
                    current_price = statistics.mean([p.price_modal for p in prices])
                    
                    # Get price trends to identify opportunities
                    trends = await price_discovery_service.get_price_trends(commodity, "30_days")
                    if trends and hasattr(trends, 'price_points') and trends.price_points:
                        # Calculate recent average
                        recent_prices = [pp.price for pp in trends.price_points[-14:]]  # Last 2 weeks
                        recent_avg = statistics.mean(recent_prices)
                        
                        # Look for arbitrage opportunities
                        price_diff_pct = ((current_price - recent_avg) / recent_avg) * 100
                        
                        if abs(price_diff_pct) > 8:  # Significant price difference
                            opportunity_type = "price_arbitrage"
                            if price_diff_pct < 0:
                                opportunity_type = "buy_opportunity"
                            else:
                                opportunity_type = "sell_opportunity"
                            
                            opportunity = MarketOpportunity(
                                user_id=user_profile.user_id,
                                opportunity_type=opportunity_type,
                                commodity=commodity,
                                location=location or "general",
                                current_price=current_price,
                                opportunity_price=recent_avg,
                                potential_profit_percentage=abs(price_diff_pct),
                                opportunity_window_start=datetime.utcnow(),
                                opportunity_window_end=datetime.utcnow() + timedelta(days=7),
                                urgency="medium" if abs(price_diff_pct) > 15 else "low",
                                risk_level="low" if abs(price_diff_pct) < 12 else "medium",
                                success_probability=0.7,
                                relevance_to_user=self._calculate_commodity_relevance(commodity, user_profile),
                                source="price_analysis",
                                confidence=ConfidenceLevel.MEDIUM
                            )
                            opportunities.append(opportunity)
                
                except Exception as e:
                    logger.warning(f"Error identifying opportunities for {commodity}: {str(e)}")
        
        return opportunities
    
    async def _generate_buy_opportunity_recommendations(
        self, 
        user_profile: UserProfile, 
        opportunities: List[MarketOpportunity], 
        request: PersonalizedRecommendationsRequest
    ) -> List[PersonalizedRecommendation]:
        """Generate buy opportunity recommendations."""
        recommendations = []
        
        buy_opportunities = [op for op in opportunities if op.opportunity_type in ["buy_opportunity", "price_arbitrage"]]
        
        for opportunity in buy_opportunities[:3]:  # Limit to top 3
            # Calculate suggested quantity based on user's typical trading volume
            suggested_quantity = None
            if user_profile.identified_patterns:
                pattern = user_profile.identified_patterns[0]
                if pattern.typical_quantity_range:
                    suggested_quantity = pattern.typical_quantity_range.get("avg", 100)
            
            # Calculate expected savings
            expected_savings = None
            if suggested_quantity and opportunity.potential_profit_percentage > 0:
                expected_savings = (opportunity.opportunity_price - opportunity.current_price) * suggested_quantity
            
            recommendation = PersonalizedRecommendation(
                user_id=user_profile.user_id,
                recommendation_type=RecommendationType.BUY_OPPORTUNITY,
                title=f"Buy Opportunity: {opportunity.commodity.title()}",
                description=f"Current {opportunity.commodity} prices are {opportunity.potential_profit_percentage:.1f}% below recent average. Consider buying now for potential savings.",
                commodity=opportunity.commodity,
                location=opportunity.location,
                suggested_price=opportunity.current_price,
                suggested_quantity=suggested_quantity,
                suggested_timing="immediate" if opportunity.urgency == "high" else "within_week",
                expected_savings=expected_savings,
                risk_level=opportunity.risk_level,
                success_probability=opportunity.success_probability,
                confidence=opportunity.confidence,
                relevance_score=opportunity.relevance_to_user,
                priority=1 if opportunity.urgency == "high" else 2,
                reasoning=[
                    f"Price is {opportunity.potential_profit_percentage:.1f}% below recent average",
                    f"Historical success rate: {opportunity.success_probability:.0%}",
                    f"Risk level: {opportunity.risk_level}",
                    "Matches your trading patterns" if opportunity.matches_user_patterns else "New opportunity"
                ],
                market_conditions={
                    "current_price": opportunity.current_price,
                    "recent_average": opportunity.opportunity_price,
                    "price_trend": "declining"
                },
                valid_until=opportunity.opportunity_window_end
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_sell_opportunity_recommendations(
        self, 
        user_profile: UserProfile, 
        opportunities: List[MarketOpportunity], 
        request: PersonalizedRecommendationsRequest
    ) -> List[PersonalizedRecommendation]:
        """Generate sell opportunity recommendations."""
        recommendations = []
        
        sell_opportunities = [op for op in opportunities if op.opportunity_type == "sell_opportunity"]
        
        for opportunity in sell_opportunities[:2]:  # Limit to top 2
            recommendation = PersonalizedRecommendation(
                user_id=user_profile.user_id,
                recommendation_type=RecommendationType.SELL_OPPORTUNITY,
                title=f"Sell Opportunity: {opportunity.commodity.title()}",
                description=f"Current {opportunity.commodity} prices are {opportunity.potential_profit_percentage:.1f}% above recent average. Consider selling if you have inventory.",
                commodity=opportunity.commodity,
                location=opportunity.location,
                suggested_price=opportunity.current_price,
                suggested_timing="immediate" if opportunity.urgency == "high" else "within_week",
                expected_profit=opportunity.potential_profit_percentage,
                risk_level=opportunity.risk_level,
                success_probability=opportunity.success_probability,
                confidence=opportunity.confidence,
                relevance_score=opportunity.relevance_to_user,
                priority=1 if opportunity.urgency == "high" else 2,
                reasoning=[
                    f"Price is {opportunity.potential_profit_percentage:.1f}% above recent average",
                    f"Good time to realize profits",
                    f"Risk level: {opportunity.risk_level}"
                ],
                market_conditions={
                    "current_price": opportunity.current_price,
                    "recent_average": opportunity.opportunity_price,
                    "price_trend": "rising"
                },
                valid_until=opportunity.opportunity_window_end
            )
            recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_timing_optimization_recommendations(
        self, 
        user_profile: UserProfile, 
        request: PersonalizedRecommendationsRequest
    ) -> List[PersonalizedRecommendation]:
        """Generate timing optimization recommendations."""
        recommendations = []
        
        # Check if user has seasonal trading patterns
        for pattern in user_profile.identified_patterns:
            if pattern.pattern_type == TradingPatternType.SEASONAL_TRADER:
                current_month = datetime.now().month
                
                # Check if we're approaching a peak trading month
                next_peak_months = [m for m in pattern.peak_trading_months if m > current_month]
                if not next_peak_months:
                    next_peak_months = pattern.peak_trading_months  # Wrap around to next year
                
                if next_peak_months:
                    next_peak = min(next_peak_months)
                    months_until_peak = next_peak - current_month if next_peak > current_month else (12 - current_month + next_peak)
                    
                    if 1 <= months_until_peak <= 2:  # 1-2 months before peak
                        recommendation = PersonalizedRecommendation(
                            user_id=user_profile.user_id,
                            recommendation_type=RecommendationType.TIMING_OPTIMIZATION,
                            title="Seasonal Trading Preparation",
                            description=f"Based on your trading history, you typically increase activity in month {next_peak}. Consider preparing your inventory and cash flow now.",
                            suggested_timing="next_month",
                            confidence=ConfidenceLevel.HIGH,
                            relevance_score=0.9,
                            priority=2,
                            reasoning=[
                                f"Historical peak trading month: {next_peak}",
                                f"Pattern confidence: {pattern.confidence:.1f}",
                                f"Typical commodities: {', '.join(pattern.preferred_commodities[:3])}"
                            ],
                            market_conditions={
                                "seasonal_pattern": "approaching_peak",
                                "months_until_peak": months_until_peak
                            }
                        )
                        recommendations.append(recommendation)
        
        return recommendations
    
    async def _generate_diversification_recommendations(
        self, 
        user_profile: UserProfile, 
        request: PersonalizedRecommendationsRequest
    ) -> List[PersonalizedRecommendation]:
        """Generate diversification recommendations."""
        recommendations = []
        
        # Check if user is too concentrated in few commodities
        if len(user_profile.preferred_commodities) <= 2:
            # Suggest diversification
            all_commodities = ["rice", "wheat", "sugar", "onion", "tomato", "potato", "pulses", "cotton"]
            suggested_commodities = [c for c in all_commodities if c not in user_profile.preferred_commodities]
            
            if suggested_commodities:
                recommendation = PersonalizedRecommendation(
                    user_id=user_profile.user_id,
                    recommendation_type=RecommendationType.DIVERSIFICATION,
                    title="Portfolio Diversification",
                    description=f"Consider diversifying into {suggested_commodities[0]} or {suggested_commodities[1]} to reduce risk and explore new opportunities.",
                    commodity=suggested_commodities[0],
                    suggested_timing="next_month",
                    risk_level="low",
                    confidence=ConfidenceLevel.MEDIUM,
                    relevance_score=0.6,
                    priority=3,
                    reasoning=[
                        f"Currently focused on: {', '.join(user_profile.preferred_commodities)}",
                        "Diversification can reduce risk",
                        "New market opportunities available"
                    ]
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    # Helper methods for profile updates
    
    async def _update_user_profile_from_behavior(self, behavior_event: UserBehaviorEvent):
        """Update user profile based on new behavior event."""
        try:
            user_profile = await self._get_or_create_user_profile(behavior_event.user_id)
            
            # Update preferences based on event
            if behavior_event.commodity and behavior_event.commodity not in user_profile.preferred_commodities:
                user_profile.preferred_commodities.append(behavior_event.commodity)
                user_profile.preferred_commodities = user_profile.preferred_commodities[:10]  # Keep top 10
            
            if behavior_event.location and behavior_event.location not in user_profile.preferred_locations:
                user_profile.preferred_locations.append(behavior_event.location)
                user_profile.preferred_locations = user_profile.preferred_locations[:5]  # Keep top 5
            
            # Update activity metrics
            user_profile.total_behavior_events += 1
            user_profile.last_updated = datetime.utcnow()
            
            # Save updated profile
            db = await get_database()
            await db.user_profiles.replace_one(
                {"user_id": behavior_event.user_id},
                user_profile.dict(),
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"Error updating user profile from behavior: {str(e)}")
    
    async def _detect_pattern_changes(
        self, 
        user_id: str, 
        current_patterns: List[TradingPattern]
    ) -> List[str]:
        """Detect changes in user's trading patterns."""
        changes = []
        
        try:
            db = await get_database()
            
            # Get previous patterns
            previous_analysis = await db.behavior_analysis_results.find_one(
                {"user_id": user_id},
                sort=[("analysis_date", -1)]
            )
            
            if not previous_analysis:
                return ["initial_analysis"]
            
            previous_patterns = [TradingPattern(**p) for p in previous_analysis.get("patterns", [])]
            
            # Compare patterns
            current_types = set(p.pattern_type for p in current_patterns)
            previous_types = set(p.pattern_type for p in previous_patterns)
            
            # New patterns
            new_patterns = current_types - previous_types
            for pattern_type in new_patterns:
                changes.append(f"new_pattern_{pattern_type.value}")
            
            # Lost patterns
            lost_patterns = previous_types - current_types
            for pattern_type in lost_patterns:
                changes.append(f"lost_pattern_{pattern_type.value}")
            
            # Changed confidence
            for current_pattern in current_patterns:
                for previous_pattern in previous_patterns:
                    if current_pattern.pattern_type == previous_pattern.pattern_type:
                        confidence_change = current_pattern.confidence - previous_pattern.confidence
                        if abs(confidence_change) > 0.2:
                            if confidence_change > 0:
                                changes.append(f"strengthened_{current_pattern.pattern_type.value}")
                            else:
                                changes.append(f"weakened_{current_pattern.pattern_type.value}")
            
            return changes
            
        except Exception as e:
            logger.error(f"Error detecting pattern changes: {str(e)}")
            return []
    
    async def _learn_from_feedback(self, feedback: RecommendationFeedback):
        """Learn from recommendation feedback to improve future recommendations."""
        try:
            # This is a simplified learning mechanism
            # In production, this would involve more sophisticated ML techniques
            
            db = await get_database()
            
            # Store learning data
            learning_data = {
                "user_id": feedback.user_id,
                "recommendation_type": None,  # Would get from recommendation
                "feedback_rating": feedback.rating,
                "outcome_successful": feedback.outcome_successful,
                "learned_at": datetime.utcnow()
            }
            
            await db.recommendation_learning.insert_one(learning_data)
            
            # Update user profile learning rate based on feedback
            user_profile = await self.get_user_profile(feedback.user_id)
            if user_profile:
                # Adjust learning rate based on feedback quality
                if feedback.rating >= 4:
                    user_profile.learning_rate = min(0.3, user_profile.learning_rate + 0.01)
                elif feedback.rating <= 2:
                    user_profile.learning_rate = max(0.05, user_profile.learning_rate - 0.01)
                
                # Update response rate
                total_recommendations = await db.personalized_recommendations.count_documents({
                    "user_id": feedback.user_id
                })
                total_feedback = await db.recommendation_feedback.count_documents({
                    "user_id": feedback.user_id
                })
                
                user_profile.response_rate_to_recommendations = total_feedback / max(1, total_recommendations)
                
                # Save updated profile
                await db.user_profiles.replace_one(
                    {"user_id": feedback.user_id},
                    user_profile.dict(),
                    upsert=True
                )
            
        except Exception as e:
            logger.error(f"Error learning from feedback: {str(e)}")


# Create service instance
personalized_insights_service = PersonalizedInsightsService()