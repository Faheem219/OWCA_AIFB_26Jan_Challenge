"""
Vendor verification service for handling vendor registration and verification workflow.
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status, UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import uuid
import os
import logging
from pathlib import Path

from app.models.user import (
    VendorRegistrationRequest, 
    DocumentUploadRequest, 
    DocumentUploadResponse,
    Document, 
    DocumentType, 
    DocumentStatus,
    VerificationStep,
    VerificationWorkflow,
    VerificationStatus,
    VerificationStatusUpdate,
    AdminVerificationAction,
    VendorProfile,
    UserInDB,
    TransactionStats
)
from app.db.mongodb import Collections
from app.core.config import settings

logger = logging.getLogger(__name__)


class VendorVerificationService:
    """Service for vendor verification and document management."""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db[Collections.USERS]
        self.documents_collection = db[Collections.VENDORS]  # Store verification documents
        
        # Create upload directory if it doesn't exist
        self.upload_dir = Path("uploads/vendor_documents")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def initiate_vendor_registration(
        self, 
        user_id: str, 
        registration_data: VendorRegistrationRequest
    ) -> Dict[str, Any]:
        """Initiate vendor registration process."""
        try:
            # Check if user exists and doesn't already have a vendor profile
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            if user.get("vendor_profile"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User already has a vendor profile"
                )
            
            # Determine required documents based on business type
            required_documents = self._get_required_documents(registration_data.business_type)
            
            # Create verification workflow
            workflow = VerificationWorkflow(
                current_step=VerificationStep.DOCUMENTS_UPLOADED,
                required_documents=required_documents
            )
            
            # Create vendor profile
            vendor_profile = VendorProfile(
                business_name=registration_data.business_name,
                business_type=registration_data.business_type,
                location=registration_data.location,
                specializations=registration_data.specializations,
                languages_spoken=registration_data.languages_spoken,
                business_hours=registration_data.business_hours,
                description=registration_data.description,
                verification_workflow=workflow
            )
            
            # Update user with vendor profile
            result = await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "vendor_profile": vendor_profile.dict(),
                        "user_type": "vendor" if user.get("user_type") == "buyer" else "both",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            if result.modified_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create vendor profile"
                )
            
            logger.info(f"Initiated vendor registration for user {user_id}")
            
            return {
                "vendor_id": user_id,
                "verification_status": VerificationStatus.PENDING,
                "required_documents": required_documents,
                "next_step": VerificationStep.DOCUMENTS_UPLOADED
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error initiating vendor registration: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initiate vendor registration"
            )
    
    async def request_document_upload(
        self, 
        user_id: str, 
        document_request: DocumentUploadRequest
    ) -> DocumentUploadResponse:
        """Request document upload and return upload URL."""
        try:
            # Verify user has vendor profile
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("vendor_profile"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor profile not found"
                )
            
            # Generate document ID and upload path
            document_id = str(ObjectId())
            file_path = self.upload_dir / f"{user_id}_{document_id}"
            
            # Create document record
            document = Document(
                id=document_id,
                type=document_request.document_type,
                number=document_request.number,
                issuing_authority=document_request.issuing_authority,
                issue_date=document_request.issue_date,
                expiry_date=document_request.expiry_date,
                document_url=str(file_path),
                status=DocumentStatus.PENDING
            )
            
            # Store document metadata
            await self.documents_collection.insert_one({
                "_id": ObjectId(document_id),
                "user_id": user_id,
                "document": document.dict(),
                "created_at": datetime.utcnow()
            })
            
            return DocumentUploadResponse(
                document_id=document_id,
                upload_url=f"/api/v1/vendor/upload-document/{document_id}"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error requesting document upload: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to request document upload"
            )
    
    async def upload_document(
        self, 
        user_id: str, 
        document_id: str, 
        file: UploadFile
    ) -> Dict[str, Any]:
        """Upload document file."""
        try:
            # Verify document belongs to user
            doc_record = await self.documents_collection.find_one({
                "_id": ObjectId(document_id),
                "user_id": user_id
            })
            
            if not doc_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            # Validate file
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File size exceeds 10MB limit"
                )
            
            allowed_types = ["image/jpeg", "image/png", "application/pdf"]
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not allowed"
                )
            
            # Save file
            file_path = self.upload_dir / f"{user_id}_{document_id}_{file.filename}"
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            # Update document record
            await self.documents_collection.update_one(
                {"_id": ObjectId(document_id)},
                {
                    "$set": {
                        "document.document_url": str(file_path),
                        "document.file_size": file.size,
                        "document.mime_type": file.content_type,
                        "document.status": DocumentStatus.UNDER_REVIEW,
                        "uploaded_at": datetime.utcnow()
                    }
                }
            )
            
            # Update vendor profile workflow
            await self._update_verification_workflow(user_id, document_id)
            
            logger.info(f"Document {document_id} uploaded for user {user_id}")
            
            return {
                "document_id": document_id,
                "status": DocumentStatus.UNDER_REVIEW,
                "message": "Document uploaded successfully and is under review"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error uploading document: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload document"
            )
    
    async def verify_government_id(self, user_id: str, document_id: str) -> Dict[str, Any]:
        """Verify government ID document."""
        try:
            # Get document
            doc_record = await self.documents_collection.find_one({
                "_id": ObjectId(document_id),
                "user_id": user_id
            })
            
            if not doc_record:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            document = doc_record["document"]
            
            # Basic validation (in production, this would integrate with government APIs)
            is_valid = await self._validate_government_id(document)
            
            if is_valid:
                # Update document status
                await self.documents_collection.update_one(
                    {"_id": ObjectId(document_id)},
                    {
                        "$set": {
                            "document.status": DocumentStatus.VERIFIED,
                            "document.verified_at": datetime.utcnow(),
                            "document.verified_by": "system"
                        }
                    }
                )
                
                # Update vendor profile
                await self.users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {
                            "vendor_profile.government_id_verified": True,
                            "vendor_profile.verification_workflow.completed_steps": 
                                [VerificationStep.GOVERNMENT_ID_VERIFIED]
                        }
                    }
                )
                
                return {
                    "verified": True,
                    "message": "Government ID verified successfully"
                }
            else:
                await self.documents_collection.update_one(
                    {"_id": ObjectId(document_id)},
                    {
                        "$set": {
                            "document.status": DocumentStatus.REJECTED,
                            "document.verification_notes": "Invalid government ID"
                        }
                    }
                )
                
                return {
                    "verified": False,
                    "message": "Government ID verification failed"
                }
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error verifying government ID: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify government ID"
            )
    
    async def get_verification_status(self, user_id: str) -> Dict[str, Any]:
        """Get vendor verification status."""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("vendor_profile"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor profile not found"
                )
            
            vendor_profile = user["vendor_profile"]
            workflow = vendor_profile.get("verification_workflow", {})
            
            # Get uploaded documents
            documents = await self.documents_collection.find(
                {"user_id": user_id}
            ).to_list(length=None)
            
            document_status = []
            for doc in documents:
                document_status.append({
                    "id": str(doc["_id"]),
                    "type": doc["document"]["type"],
                    "status": doc["document"]["status"],
                    "uploaded_at": doc.get("uploaded_at"),
                    "verified_at": doc["document"].get("verified_at")
                })
            
            return {
                "verification_status": vendor_profile.get("verification_status"),
                "current_step": workflow.get("current_step"),
                "completed_steps": workflow.get("completed_steps", []),
                "required_documents": workflow.get("required_documents", []),
                "documents": document_status,
                "government_id_verified": vendor_profile.get("government_id_verified", False),
                "business_license_verified": vendor_profile.get("business_license_verified", False)
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting verification status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get verification status"
            )
    
    async def admin_review_vendor(
        self, 
        user_id: str, 
        action: AdminVerificationAction,
        admin_user_id: str
    ) -> Dict[str, Any]:
        """Admin review and approve/reject vendor."""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("vendor_profile"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor profile not found"
                )
            
            if action.action == "approve":
                # Update vendor profile to approved
                await self.users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {
                            "vendor_profile.verification_status": VerificationStatus.VERIFIED,
                            "vendor_profile.verification_workflow.current_step": VerificationStep.APPROVED,
                            "vendor_profile.verification_workflow.completed_at": datetime.utcnow(),
                            "vendor_profile.verification_workflow.admin_notes": action.notes,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                return {
                    "status": "approved",
                    "message": "Vendor profile approved successfully"
                }
                
            elif action.action == "reject":
                await self.users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {
                            "vendor_profile.verification_status": VerificationStatus.REJECTED,
                            "vendor_profile.verification_workflow.current_step": VerificationStep.REJECTED,
                            "vendor_profile.verification_workflow.rejection_reason": action.notes,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                return {
                    "status": "rejected",
                    "message": "Vendor profile rejected"
                }
                
            elif action.action == "request_documents":
                await self.users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {
                            "vendor_profile.verification_workflow.required_documents": action.required_documents,
                            "vendor_profile.verification_workflow.admin_notes": action.notes,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                return {
                    "status": "documents_requested",
                    "message": "Additional documents requested",
                    "required_documents": action.required_documents
                }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in admin review: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process admin review"
            )
    
    @staticmethod
    def _get_required_documents(business_type: str) -> List[DocumentType]:
        """Get required documents based on business type."""
        base_documents = [
            DocumentType.GOVERNMENT_ID,
            DocumentType.ADDRESS_PROOF
        ]
        
        if business_type in ["retail", "wholesale", "manufacturing"]:
            base_documents.extend([
                DocumentType.BUSINESS_LICENSE,
                DocumentType.TAX_CERTIFICATE
            ])
        
        if business_type == "organic":
            base_documents.append(DocumentType.ORGANIC_CERTIFICATION)
        
        return base_documents
    
    async def _validate_government_id(self, document: Dict[str, Any]) -> bool:
        """Validate government ID document."""
        # Basic validation - in production, integrate with government APIs
        doc_type = document.get("type")
        doc_number = document.get("number")
        
        if doc_type == DocumentType.GOVERNMENT_ID:
            # Basic format validation
            if len(doc_number) >= 8:  # Minimum length check
                return True
        
        return False
    
    async def calculate_credibility_score(self, user_id: str) -> float:
        """Calculate vendor credibility score based on multiple factors."""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("vendor_profile"):
                return 0.0
            
            vendor_profile = user["vendor_profile"]
            score = 0.0
            max_score = 100.0
            
            # 1. Verification Status (30 points)
            verification_status = vendor_profile.get("verification_status")
            if verification_status == VerificationStatus.VERIFIED:
                score += 30.0
            elif verification_status == VerificationStatus.PENDING:
                score += 10.0
            
            # 2. Document Verification (20 points)
            document_score = 0.0
            if vendor_profile.get("government_id_verified", False):
                document_score += 8.0
            if vendor_profile.get("business_license_verified", False):
                document_score += 6.0
            if vendor_profile.get("tax_registration_verified", False):
                document_score += 3.0
            if vendor_profile.get("bank_account_verified", False):
                document_score += 3.0
            score += document_score
            
            # 3. Transaction History (25 points)
            transaction_stats = vendor_profile.get("transaction_stats", {})
            total_transactions = transaction_stats.get("total_transactions", 0)
            completed_transactions = transaction_stats.get("completed_transactions", 0)
            
            if total_transactions > 0:
                completion_rate = completed_transactions / total_transactions
                transaction_score = min(15.0, total_transactions * 0.5)  # Up to 15 points for volume
                completion_score = completion_rate * 10.0  # Up to 10 points for completion rate
                score += transaction_score + completion_score
            
            # 4. Customer Ratings (15 points)
            average_rating = transaction_stats.get("average_rating", 0.0)
            if average_rating > 0:
                rating_score = (average_rating / 5.0) * 15.0
                score += rating_score
            
            # 5. Response Time (10 points)
            response_time_hours = transaction_stats.get("response_time_hours", 24.0)
            if response_time_hours <= 1.0:
                score += 10.0
            elif response_time_hours <= 4.0:
                score += 7.0
            elif response_time_hours <= 12.0:
                score += 4.0
            elif response_time_hours <= 24.0:
                score += 2.0
            
            # Normalize score to 0-100 range
            final_score = min(max_score, score)
            
            # Update vendor profile with new score
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "vendor_profile.credibility_score": final_score,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"Updated credibility score for vendor {user_id}: {final_score}")
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating credibility score: {e}")
            return 0.0
    
    async def update_transaction_stats(
        self, 
        user_id: str, 
        transaction_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update vendor transaction statistics."""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("vendor_profile"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor profile not found"
                )
            
            current_stats = user["vendor_profile"].get("transaction_stats", {})
            
            # Update statistics
            total_transactions = current_stats.get("total_transactions", 0) + 1
            completed_transactions = current_stats.get("completed_transactions", 0)
            total_revenue = current_stats.get("total_revenue", 0.0)
            
            if transaction_data.get("status") == "completed":
                completed_transactions += 1
                total_revenue += transaction_data.get("amount", 0.0)
            
            # Calculate new average rating if rating provided
            current_rating = current_stats.get("average_rating", 0.0)
            rating_count = current_stats.get("rating_count", 0)
            
            if transaction_data.get("rating"):
                new_rating = transaction_data["rating"]
                if rating_count == 0:
                    average_rating = new_rating
                else:
                    average_rating = ((current_rating * rating_count) + new_rating) / (rating_count + 1)
                rating_count += 1
            else:
                average_rating = current_rating
            
            # Update response time if provided
            response_time = transaction_data.get("response_time_hours", 
                                                current_stats.get("response_time_hours", 24.0))
            
            updated_stats = TransactionStats(
                total_transactions=total_transactions,
                completed_transactions=completed_transactions,
                total_revenue=total_revenue,
                average_rating=average_rating,
                response_time_hours=response_time
            )
            
            # Update database
            await self.users_collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "vendor_profile.transaction_stats": updated_stats.dict(),
                        "vendor_profile.transaction_stats.rating_count": rating_count,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Recalculate credibility score
            new_score = await self.calculate_credibility_score(user_id)
            
            return {
                "transaction_stats": updated_stats.dict(),
                "credibility_score": new_score,
                "message": "Transaction statistics updated successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating transaction stats: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update transaction statistics"
            )
    
    async def get_vendor_analytics(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive vendor analytics."""
        try:
            user = await self.users_collection.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("vendor_profile"):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vendor profile not found"
                )
            
            vendor_profile = user["vendor_profile"]
            transaction_stats = vendor_profile.get("transaction_stats", {})
            
            # Calculate additional metrics
            completion_rate = 0.0
            if transaction_stats.get("total_transactions", 0) > 0:
                completion_rate = (transaction_stats.get("completed_transactions", 0) / 
                                 transaction_stats.get("total_transactions", 0)) * 100
            
            # Get recent transaction trends (mock data for now)
            recent_trends = await self._get_transaction_trends(user_id)
            
            # Calculate specialization tags
            specialization_tags = await self._calculate_specialization_tags(vendor_profile)
            
            return {
                "credibility_score": vendor_profile.get("credibility_score", 0.0),
                "verification_status": vendor_profile.get("verification_status"),
                "transaction_stats": transaction_stats,
                "completion_rate": completion_rate,
                "specialization_tags": specialization_tags,
                "recent_trends": recent_trends,
                "verification_details": {
                    "government_id_verified": vendor_profile.get("government_id_verified", False),
                    "business_license_verified": vendor_profile.get("business_license_verified", False),
                    "tax_registration_verified": vendor_profile.get("tax_registration_verified", False),
                    "bank_account_verified": vendor_profile.get("bank_account_verified", False)
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting vendor analytics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get vendor analytics"
            )
    
    async def _get_transaction_trends(self, user_id: str) -> Dict[str, Any]:
        """Get transaction trends for the vendor."""
        # This would typically query transaction history
        # For now, return mock data structure
        return {
            "monthly_revenue": [1000, 1200, 1500, 1800, 2000],
            "monthly_transactions": [10, 12, 15, 18, 20],
            "rating_trend": [4.0, 4.1, 4.2, 4.3, 4.4],
            "response_time_trend": [12, 10, 8, 6, 4]
        }
    
    async def _calculate_specialization_tags(self, vendor_profile: Dict[str, Any]) -> List[str]:
        """Calculate specialization tags based on vendor profile and performance."""
        tags = []
        
        # Base specializations from profile
        specializations = vendor_profile.get("specializations", [])
        tags.extend(specializations)
        
        # Performance-based tags
        credibility_score = vendor_profile.get("credibility_score", 0.0)
        transaction_stats = vendor_profile.get("transaction_stats", {})
        
        if credibility_score >= 90:
            tags.append("premium_quality")
        elif credibility_score >= 75:
            tags.append("trusted_vendor")
        
        if transaction_stats.get("average_rating", 0.0) >= 4.5:
            tags.append("highly_rated")
        
        if transaction_stats.get("response_time_hours", 24.0) <= 2.0:
            tags.append("quick_response")
        
        # Verification-based tags
        if vendor_profile.get("government_id_verified") and vendor_profile.get("business_license_verified"):
            tags.append("verified_business")
        
        return list(set(tags))  # Remove duplicates
    
    async def _update_verification_workflow(self, user_id: str, document_id: str):
        """Update verification workflow based on uploaded document."""
        try:
            # Get document type
            doc_record = await self.documents_collection.find_one({"_id": ObjectId(document_id)})
            if not doc_record:
                return
            
            document_type = doc_record["document"]["type"]
            
            # Update workflow step based on document type
            if document_type == DocumentType.GOVERNMENT_ID:
                await self.users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {
                            "vendor_profile.verification_workflow.current_step": VerificationStep.GOVERNMENT_ID_VERIFIED
                        }
                    }
                )
            elif document_type == DocumentType.BUSINESS_LICENSE:
                await self.users_collection.update_one(
                    {"_id": ObjectId(user_id)},
                    {
                        "$set": {
                            "vendor_profile.verification_workflow.current_step": VerificationStep.BUSINESS_LICENSE_VERIFIED
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"Error updating verification workflow: {e}")