"""
Review service for handling multilingual ratings and reviews.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import re
from collections import defaultdict

from app.models.review import (
    Review, ReviewCreate, ReviewUpdate, ReviewResponse, ReviewWithTranslations,
    ReviewSummary, ReviewModerationRequest, ReviewModerationResponse,
    ReviewHelpfulnessRequest, ReviewReportRequest, ReviewFilters,
    ReviewStats, ReviewAnalytics, ReviewNotification,
    ReviewStatus, ModerationAction, ReviewCategory, ReviewTranslation,
    BulkReviewOperation
)
from app.models.translation import TranslationRequest
from app.models.user import UserInDB
from app.services.translation_service import TranslationService
from app.db.mongodb import Collections
from app.core.config import settings

logger = logging.getLogger(__name__)


class ReviewService:
    """Service for managing multilingual reviews and ratings."""
    
    def __init__(self, db: AsyncIOMotorDatabase, translation_service: TranslationService):
        self.db = db
        self.translation_service = translation_service
        self.reviews_collection = db[Collections.REVIEWS]
        self.users_collection = db[Collections.USERS]
        self.transactions_collection = db[Collections.TRANSACTIONS]
        self.notifications_collection = db[Collections.NOTIFICATIONS]
        
        # Content moderation settings
        self.profanity_words = self._load_profanity_words()
        self.spam_patterns = self._load_spam_patterns()
    
    async def create_review(
        self, 
        buyer_id: str, 
        review_data: ReviewCreate
    ) -> Review:
        """Create a new review with multilingual support."""
        try:
            # Validate buyer exists and can review this vendor
            buyer = await self.users_collection.find_one({"_id": ObjectId(buyer_id)})
            if not buyer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Buyer not found"
                )
            
            # Validate vendor exists
            vendor = await self.users_collection.find_one({"_id": ObjectId(review_data.vendor_id)})
            if not vendor or not vendor.get("vendor_profile"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor not found"
                )
            
            # Check if buyer has already reviewed this vendor for this transaction
            if review_data.transaction_id:
                existing_review = await self.reviews_collection.find_one({
                    "buyer_id": buyer_id,
                    "vendor_id": review_data.vendor_id,
                    "transaction_id": review_data.transaction_id
                })
                if existing_review:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Review already exists for this transaction"
                    )
            
            # Verify transaction if provided
            if review_data.transaction_id:
                transaction = await self.transactions_collection.find_one({
                    "_id": ObjectId(review_data.transaction_id),
                    "buyer_id": buyer_id,
                    "vendor_id": review_data.vendor_id
                })
                if transaction:
                    review_data.is_verified_purchase = True
            
            # Create review document
            review = Review(
                **review_data.dict(),
                buyer_id=buyer_id,
                status=ReviewStatus.PENDING  # All reviews start as pending
            )
            
            # Perform content moderation
            moderation_result = await self._moderate_content(review)
            if moderation_result["requires_review"]:
                review.status = ReviewStatus.FLAGGED
                review.moderation_notes = moderation_result["reason"]
            else:
                review.status = ReviewStatus.APPROVED
            
            # Insert review into database
            result = await self.reviews_collection.insert_one(review.dict(by_alias=True))
            review.id = result.inserted_id
            
            # Generate translations for the review
            await self._generate_review_translations(review)
            
            # Update vendor's rating statistics
            await self._update_vendor_rating_stats(review_data.vendor_id)
            
            # Send notification to vendor
            await self._send_review_notification(review_data.vendor_id, review, "new_review")
            
            logger.info(f"Review created: {review.id} by buyer {buyer_id} for vendor {review_data.vendor_id}")
            
            return review
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating review: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create review"
            )
    
    async def get_review(self, review_id: str, language: Optional[str] = None) -> ReviewWithTranslations:
        """Get a review by ID with optional language translation."""
        try:
            review = await self.reviews_collection.find_one({"_id": ObjectId(review_id)})
            if not review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found"
                )
            
            # Get buyer information (if not anonymous)
            buyer_name = None
            if not review.get("is_anonymous", False):
                buyer = await self.users_collection.find_one({"_id": ObjectId(review["buyer_id"])})
                if buyer:
                    buyer_name = buyer.get("full_name", "Anonymous")
            
            # Convert to response model
            review_response = ReviewWithTranslations(
                id=str(review["_id"]),
                vendor_id=review["vendor_id"],
                buyer_id=review["buyer_id"],
                buyer_name=buyer_name,
                transaction_id=review.get("transaction_id"),
                product_id=review.get("product_id"),
                overall_rating=review["overall_rating"],
                detailed_ratings=review.get("detailed_ratings", []),
                title=review.get("title"),
                content=review["content"],
                original_language=review.get("original_language", "en"),
                is_verified_purchase=review.get("is_verified_purchase", False),
                is_anonymous=review.get("is_anonymous", False),
                status=review.get("status", ReviewStatus.PENDING),
                helpful_votes=review.get("helpful_votes", 0),
                total_votes=review.get("total_votes", 0),
                created_at=review.get("created_at", datetime.utcnow()),
                updated_at=review.get("updated_at", datetime.utcnow()),
                translations=review.get("translations", {}),
                available_languages=list(review.get("translations", {}).keys())
            )
            
            # If specific language requested and available, use translated content
            if language and language in review_response.translations:
                translation = review_response.translations[language]
                review_response.title = translation.title or review_response.title
                review_response.content = translation.content
            
            return review_response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting review: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get review"
            )
    
    async def get_vendor_reviews(
        self, 
        vendor_id: str, 
        filters: ReviewFilters,
        language: Optional[str] = None
    ) -> Tuple[List[ReviewWithTranslations], int]:
        """Get reviews for a vendor with filtering and pagination."""
        try:
            # Build query
            query = {"vendor_id": vendor_id}
            
            if filters.min_rating is not None:
                query["overall_rating"] = {"$gte": filters.min_rating}
            if filters.max_rating is not None:
                if "overall_rating" in query:
                    query["overall_rating"]["$lte"] = filters.max_rating
                else:
                    query["overall_rating"] = {"$lte": filters.max_rating}
            
            if filters.status:
                query["status"] = filters.status
            else:
                query["status"] = ReviewStatus.APPROVED  # Only show approved reviews by default
            
            if filters.is_verified_purchase is not None:
                query["is_verified_purchase"] = filters.is_verified_purchase
            
            if filters.date_from:
                query["created_at"] = {"$gte": filters.date_from}
            if filters.date_to:
                if "created_at" in query:
                    query["created_at"]["$lte"] = filters.date_to
                else:
                    query["created_at"] = {"$lte": filters.date_to}
            
            # Count total matching reviews
            total_count = await self.reviews_collection.count_documents(query)
            
            # Build sort criteria
            sort_criteria = []
            if filters.sort_by == "rating":
                sort_direction = 1 if filters.sort_order == "asc" else -1
                sort_criteria.append(("overall_rating", sort_direction))
            elif filters.sort_by == "helpful_votes":
                sort_direction = 1 if filters.sort_order == "asc" else -1
                sort_criteria.append(("helpful_votes", sort_direction))
            else:  # Default to created_at
                sort_direction = 1 if filters.sort_order == "asc" else -1
                sort_criteria.append(("created_at", sort_direction))
            
            # Get reviews with pagination
            cursor = self.reviews_collection.find(query).sort(sort_criteria)
            if filters.skip > 0:
                cursor = cursor.skip(filters.skip)
            if filters.limit > 0:
                cursor = cursor.limit(filters.limit)
            
            reviews = await cursor.to_list(length=None)
            
            # Convert to response models
            review_responses = []
            for review in reviews:
                # Get buyer information
                buyer_name = None
                if not review.get("is_anonymous", False):
                    buyer = await self.users_collection.find_one({"_id": ObjectId(review["buyer_id"])})
                    if buyer:
                        buyer_name = buyer.get("full_name", "Anonymous")
                
                review_response = ReviewWithTranslations(
                    id=str(review["_id"]),
                    vendor_id=review["vendor_id"],
                    buyer_id=review["buyer_id"],
                    buyer_name=buyer_name,
                    transaction_id=review.get("transaction_id"),
                    product_id=review.get("product_id"),
                    overall_rating=review["overall_rating"],
                    detailed_ratings=review.get("detailed_ratings", []),
                    title=review.get("title"),
                    content=review["content"],
                    original_language=review.get("original_language", "en"),
                    is_verified_purchase=review.get("is_verified_purchase", False),
                    is_anonymous=review.get("is_anonymous", False),
                    status=review.get("status", ReviewStatus.PENDING),
                    helpful_votes=review.get("helpful_votes", 0),
                    total_votes=review.get("total_votes", 0),
                    created_at=review.get("created_at", datetime.utcnow()),
                    updated_at=review.get("updated_at", datetime.utcnow()),
                    translations=review.get("translations", {}),
                    available_languages=list(review.get("translations", {}).keys())
                )
                
                # Apply language translation if requested
                if language and language in review_response.translations:
                    translation = review_response.translations[language]
                    review_response.title = translation.title or review_response.title
                    review_response.content = translation.content
                
                review_responses.append(review_response)
            
            return review_responses, total_count
            
        except Exception as e:
            logger.error(f"Error getting vendor reviews: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get vendor reviews"
            )
    
    async def get_review_summary(self, vendor_id: str) -> ReviewSummary:
        """Get review summary statistics for a vendor."""
        try:
            # Aggregate review statistics
            pipeline = [
                {"$match": {"vendor_id": vendor_id, "status": ReviewStatus.APPROVED}},
                {"$group": {
                    "_id": None,
                    "total_reviews": {"$sum": 1},
                    "average_rating": {"$avg": "$overall_rating"},
                    "ratings": {"$push": "$overall_rating"},
                    "detailed_ratings": {"$push": "$detailed_ratings"}
                }}
            ]
            
            result = await self.reviews_collection.aggregate(pipeline).to_list(length=1)
            
            if not result:
                return ReviewSummary()
            
            stats = result[0]
            
            # Calculate rating distribution
            rating_distribution = {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}
            for rating in stats.get("ratings", []):
                rating_key = str(int(rating))
                if rating_key in rating_distribution:
                    rating_distribution[rating_key] += 1
            
            # Calculate category ratings
            category_ratings = {}
            all_detailed_ratings = stats.get("detailed_ratings", [])
            category_sums = defaultdict(list)
            
            for detailed_ratings_list in all_detailed_ratings:
                for rating in detailed_ratings_list:
                    category_sums[rating["category"]].append(rating["score"])
            
            for category, scores in category_sums.items():
                if scores:
                    category_ratings[category] = sum(scores) / len(scores)
            
            # Get recent reviews (last 5)
            recent_reviews_cursor = self.reviews_collection.find(
                {"vendor_id": vendor_id, "status": ReviewStatus.APPROVED}
            ).sort("created_at", -1).limit(5)
            
            recent_reviews = []
            async for review in recent_reviews_cursor:
                # Get buyer name
                buyer_name = None
                if not review.get("is_anonymous", False):
                    buyer = await self.users_collection.find_one({"_id": ObjectId(review["buyer_id"])})
                    if buyer:
                        buyer_name = buyer.get("full_name", "Anonymous")
                
                recent_reviews.append(ReviewResponse(
                    id=str(review["_id"]),
                    vendor_id=review["vendor_id"],
                    buyer_id=review["buyer_id"],
                    buyer_name=buyer_name,
                    transaction_id=review.get("transaction_id"),
                    product_id=review.get("product_id"),
                    overall_rating=review["overall_rating"],
                    detailed_ratings=review.get("detailed_ratings", []),
                    title=review.get("title"),
                    content=review["content"],
                    original_language=review.get("original_language", "en"),
                    is_verified_purchase=review.get("is_verified_purchase", False),
                    is_anonymous=review.get("is_anonymous", False),
                    status=review.get("status", ReviewStatus.PENDING),
                    helpful_votes=review.get("helpful_votes", 0),
                    total_votes=review.get("total_votes", 0),
                    created_at=review.get("created_at", datetime.utcnow()),
                    updated_at=review.get("updated_at", datetime.utcnow())
                ))
            
            return ReviewSummary(
                total_reviews=stats.get("total_reviews", 0),
                average_rating=round(stats.get("average_rating", 0.0), 1),
                rating_distribution=rating_distribution,
                category_ratings=category_ratings,
                recent_reviews=recent_reviews
            )
            
        except Exception as e:
            logger.error(f"Error getting review summary: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get review summary"
            )
    
    async def update_review(
        self, 
        review_id: str, 
        buyer_id: str, 
        update_data: ReviewUpdate
    ) -> Review:
        """Update an existing review."""
        try:
            # Check if review exists and belongs to buyer
            review = await self.reviews_collection.find_one({
                "_id": ObjectId(review_id),
                "buyer_id": buyer_id
            })
            
            if not review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found or not authorized"
                )
            
            # Prepare update data
            update_fields = {}
            for field, value in update_data.dict(exclude_unset=True).items():
                if value is not None:
                    update_fields[field] = value
            
            if not update_fields:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields to update"
                )
            
            update_fields["updated_at"] = datetime.utcnow()
            
            # If content is updated, re-moderate and regenerate translations
            if "content" in update_fields or "title" in update_fields:
                # Create temporary review object for moderation
                temp_review = Review(**review)
                if "content" in update_fields:
                    temp_review.content = update_fields["content"]
                if "title" in update_fields:
                    temp_review.title = update_fields["title"]
                
                moderation_result = await self._moderate_content(temp_review)
                if moderation_result["requires_review"]:
                    update_fields["status"] = ReviewStatus.FLAGGED
                    update_fields["moderation_notes"] = moderation_result["reason"]
                else:
                    update_fields["status"] = ReviewStatus.APPROVED
                
                # Clear existing translations - they'll be regenerated
                update_fields["translations"] = {}
            
            # Update review
            result = await self.reviews_collection.update_one(
                {"_id": ObjectId(review_id)},
                {"$set": update_fields}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update review"
                )
            
            # Get updated review
            updated_review = await self.reviews_collection.find_one({"_id": ObjectId(review_id)})
            review_obj = Review(**updated_review)
            
            # Regenerate translations if content was updated
            if "content" in update_fields or "title" in update_fields:
                await self._generate_review_translations(review_obj)
            
            # Update vendor rating stats if rating changed
            if "overall_rating" in update_fields or "detailed_ratings" in update_fields:
                await self._update_vendor_rating_stats(review["vendor_id"])
            
            logger.info(f"Review updated: {review_id} by buyer {buyer_id}")
            
            return review_obj
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating review: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update review"
            )
    
    async def moderate_review(
        self, 
        review_id: str, 
        moderation_request: ReviewModerationRequest,
        moderator_id: str
    ) -> ReviewModerationResponse:
        """Moderate a review (admin function)."""
        try:
            review = await self.reviews_collection.find_one({"_id": ObjectId(review_id)})
            if not review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found"
                )
            
            # Determine new status based on action
            new_status = ReviewStatus.PENDING
            if moderation_request.action == ModerationAction.APPROVE:
                new_status = ReviewStatus.APPROVED
            elif moderation_request.action == ModerationAction.REJECT:
                new_status = ReviewStatus.REJECTED
            elif moderation_request.action == ModerationAction.FLAG:
                new_status = ReviewStatus.FLAGGED
            elif moderation_request.action == ModerationAction.REMOVE:
                # For remove action, we'll mark as rejected
                new_status = ReviewStatus.REJECTED
            
            # Update review
            update_data = {
                "status": new_status,
                "moderated_by": moderator_id,
                "moderated_at": datetime.utcnow(),
                "moderation_notes": moderation_request.notes,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.reviews_collection.update_one(
                {"_id": ObjectId(review_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to moderate review"
                )
            
            # Update vendor rating stats if status changed to/from approved
            if (review.get("status") == ReviewStatus.APPROVED and new_status != ReviewStatus.APPROVED) or \
               (review.get("status") != ReviewStatus.APPROVED and new_status == ReviewStatus.APPROVED):
                await self._update_vendor_rating_stats(review["vendor_id"])
            
            # Send notification to review author
            notification_type = f"review_{moderation_request.action.value}"
            await self._send_review_notification(review["buyer_id"], review, notification_type)
            
            logger.info(f"Review moderated: {review_id} by {moderator_id} - {moderation_request.action}")
            
            return ReviewModerationResponse(
                review_id=review_id,
                action=moderation_request.action,
                status=new_status,
                moderated_by=moderator_id,
                moderated_at=datetime.utcnow(),
                notes=moderation_request.notes
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error moderating review: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to moderate review"
            )
    
    async def mark_review_helpful(
        self, 
        review_id: str, 
        user_id: str, 
        helpfulness_request: ReviewHelpfulnessRequest
    ) -> Dict[str, Any]:
        """Mark a review as helpful or unhelpful."""
        try:
            review = await self.reviews_collection.find_one({"_id": ObjectId(review_id)})
            if not review:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Review not found"
                )
            
            # Check if user has already voted on this review
            # In a production system, you'd track individual votes
            # For now, we'll just increment the counters
            
            update_data = {
                "total_votes": review.get("total_votes", 0) + 1,
                "updated_at": datetime.utcnow()
            }
            
            if helpfulness_request.is_helpful:
                update_data["helpful_votes"] = review.get("helpful_votes", 0) + 1
            
            result = await self.reviews_collection.update_one(
                {"_id": ObjectId(review_id)},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update review helpfulness"
                )
            
            return {
                "review_id": review_id,
                "helpful_votes": update_data["helpful_votes"] if helpfulness_request.is_helpful else review.get("helpful_votes", 0),
                "total_votes": update_data["total_votes"],
                "message": "Review helpfulness updated successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error marking review helpful: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update review helpfulness"
            )
    
    async def _generate_review_translations(self, review: Review):
        """Generate translations for review content."""
        try:
            # Get list of supported languages
            supported_languages = settings.SUPPORTED_LANGUAGES
            original_language = review.original_language
            
            translations = {}
            
            for target_language in supported_languages:
                if target_language == original_language:
                    continue
                
                try:
                    # Translate content
                    content_translation = await self.translation_service.translate_text(
                        TranslationRequest(
                            text=review.content,
                            source_language=original_language,
                            target_language=target_language,
                            context="product_review"
                        )
                    )
                    
                    # Translate title if present
                    title_translation = None
                    if review.title:
                        title_result = await self.translation_service.translate_text(
                            TranslationRequest(
                                text=review.title,
                                source_language=original_language,
                                target_language=target_language,
                                context="review_title"
                            )
                        )
                        title_translation = title_result.translated_text
                    
                    # Store translation
                    translations[target_language] = ReviewTranslation(
                        language=target_language,
                        title=title_translation,
                        content=content_translation.translated_text,
                        translation_provider=content_translation.provider,
                        confidence_score=content_translation.confidence_score
                    ).dict()
                    
                except Exception as e:
                    logger.warning(f"Failed to translate review to {target_language}: {e}")
                    continue
            
            # Update review with translations
            if translations:
                await self.reviews_collection.update_one(
                    {"_id": review.id},
                    {"$set": {"translations": translations}}
                )
                
        except Exception as e:
            logger.error(f"Error generating review translations: {e}")
    
    async def _moderate_content(self, review: Review) -> Dict[str, Any]:
        """Perform content moderation on review."""
        content = (review.content or "").lower()
        title = (review.title or "").lower()
        
        # Check for profanity
        for word in self.profanity_words:
            if word in content or word in title:
                return {
                    "requires_review": True,
                    "reason": "Contains inappropriate language"
                }
        
        # Check for spam patterns
        for pattern in self.spam_patterns:
            if re.search(pattern, content, re.IGNORECASE) or re.search(pattern, title, re.IGNORECASE):
                return {
                    "requires_review": True,
                    "reason": "Potential spam content detected"
                }
        
        # Check for excessive repetition
        words = content.split()
        if len(words) > 10:
            word_count = {}
            for word in words:
                word_count[word] = word_count.get(word, 0) + 1
            
            # If any word appears more than 30% of the time, flag as spam
            for word, count in word_count.items():
                if count / len(words) > 0.3:
                    return {
                        "requires_review": True,
                        "reason": "Excessive word repetition detected"
                    }
        
        return {"requires_review": False, "reason": None}
    
    async def _update_vendor_rating_stats(self, vendor_id: str):
        """Update vendor's rating statistics."""
        try:
            # Calculate new rating statistics
            pipeline = [
                {"$match": {"vendor_id": vendor_id, "status": ReviewStatus.APPROVED}},
                {"$group": {
                    "_id": None,
                    "total_reviews": {"$sum": 1},
                    "average_rating": {"$avg": "$overall_rating"}
                }}
            ]
            
            result = await self.reviews_collection.aggregate(pipeline).to_list(length=1)
            
            if result:
                stats = result[0]
                # Update vendor profile with new stats
                await self.users_collection.update_one(
                    {"_id": ObjectId(vendor_id)},
                    {
                        "$set": {
                            "vendor_profile.transaction_stats.total_transactions": stats["total_reviews"],
                            "vendor_profile.transaction_stats.average_rating": round(stats["average_rating"], 1),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"Error updating vendor rating stats: {e}")
    
    async def _send_review_notification(self, user_id: str, review: Dict[str, Any], notification_type: str):
        """Send notification about review activity."""
        try:
            # Create notification messages based on type
            messages = {
                "new_review": {
                    "title": "New Review Received",
                    "message": f"You received a new {review.get('overall_rating', 0)}-star review"
                },
                "review_approved": {
                    "title": "Review Approved",
                    "message": "Your review has been approved and is now visible"
                },
                "review_flagged": {
                    "title": "Review Flagged",
                    "message": "Your review has been flagged for moderation"
                },
                "review_rejected": {
                    "title": "Review Rejected",
                    "message": "Your review has been rejected"
                }
            }
            
            if notification_type not in messages:
                return
            
            notification = ReviewNotification(
                user_id=user_id,
                review_id=str(review.get("_id", "")),
                notification_type=notification_type,
                title=messages[notification_type]["title"],
                message=messages[notification_type]["message"]
            )
            
            await self.notifications_collection.insert_one(notification.dict(by_alias=True))
            
        except Exception as e:
            logger.error(f"Error sending review notification: {e}")
    
    def _load_profanity_words(self) -> List[str]:
        """Load profanity words for content moderation."""
        # Basic profanity list - in production, use a comprehensive database
        return [
            "spam", "fake", "scam", "fraud", "cheat", "terrible", "worst", "horrible",
            # Add more words as needed
        ]
    
    def _load_spam_patterns(self) -> List[str]:
        """Load spam patterns for content moderation."""
        # Basic spam patterns - in production, use ML-based detection
        return [
            r"(buy|click|visit).*(now|here|link)",
            r"(free|cheap|discount).*(offer|deal|price)",
            r"(contact|call|whatsapp).*(number|phone|\d{10})",
            r"(website|site|url).*(\.com|\.in|\.org)",
            # Add more patterns as needed
        ]