"""
User service for the Multilingual Mandi Marketplace Platform.

This service handles user profile management, preferences, and user-related operations.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from app.core.config import settings
from app.core.database import get_database
from app.core.exceptions import (
    NotFoundException,
    ValidationException,
    AuthorizationException,
    AuthenticationException
)
from app.models.user import (
    UserProfile,
    VendorProfile,
    BuyerProfile,
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
    UserPreferences,
    LocationData,
    Address,
    VerificationStatus,
    BusinessType,
    UserRole,
    SupportedLanguage,
    ProductCategory,
    DocumentReference,
    TransactionReference,
    BudgetRange
)

logger = logging.getLogger(__name__)


class UserService:
    """User service class."""
    
    async def create_user_profile(self, user_data: UserCreateRequest) -> UserResponse:
        """
        Create a new user profile with role-based validation.
        
        Args:
            user_data: User creation request data
            
        Returns:
            Created user response
            
        Raises:
            ValidationException: If user data is invalid
            AuthenticationException: If user creation fails
        """
        try:
            db = await get_database()
            
            # Check if user already exists
            existing_user = await db.users.find_one({
                "$or": [
                    {"email": user_data.email},
                    {"phone": user_data.phone} if user_data.phone else {}
                ]
            })
            
            if existing_user:
                if existing_user.get("email") == user_data.email:
                    raise ValidationException("User with this email already exists")
                if user_data.phone and existing_user.get("phone") == user_data.phone:
                    raise ValidationException("User with this phone number already exists")
            
            # Validate role-specific required fields
            self._validate_role_specific_fields(user_data)
            
            # Generate user ID
            from bson import ObjectId
            user_id = str(ObjectId())
            
            # Create base user data
            base_user_data = {
                "user_id": user_id,
                "email": user_data.email,
                "phone": user_data.phone,
                "role": user_data.role.value,
                "preferred_languages": [lang.value for lang in user_data.preferred_languages],
                "location": user_data.location.model_dump(),
                "verification_status": VerificationStatus.UNVERIFIED.value,
                "preferences": UserPreferences().model_dump(),
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None
            }
            
            # Add role-specific fields
            if user_data.role == UserRole.VENDOR:
                vendor_data = self._create_vendor_profile_data(user_data)
                base_user_data.update(vendor_data)
            elif user_data.role == UserRole.BUYER:
                buyer_data = self._create_buyer_profile_data(user_data)
                base_user_data.update(buyer_data)
            
            # Insert user into database
            result = await db.users.insert_one(base_user_data)
            
            if not result.inserted_id:
                raise AuthenticationException("Failed to create user profile")
            
            # Get created user
            created_user = await db.users.find_one({"user_id": user_id})
            return self._convert_user_to_response(created_user)
            
        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"Failed to create user profile: {e}")
            raise AuthenticationException("User profile creation failed")
    
    def _validate_role_specific_fields(self, user_data: UserCreateRequest) -> None:
        """
        Validate role-specific required fields.
        
        Args:
            user_data: User creation request data
            
        Raises:
            ValidationException: If required fields are missing or invalid
        """
        if user_data.role == UserRole.VENDOR:
            # Validate vendor-specific required fields
            if not user_data.business_name or not user_data.business_name.strip():
                raise ValidationException("Business name is required for vendors")
            
            if not user_data.business_type:
                raise ValidationException("Business type is required for vendors")
            
            if not user_data.product_categories or len(user_data.product_categories) == 0:
                raise ValidationException("At least one product category is required for vendors")
            
            if not user_data.market_location or not user_data.market_location.strip():
                raise ValidationException("Market location is required for vendors")
            
            # Validate business name length
            if len(user_data.business_name.strip()) < 2:
                raise ValidationException("Business name must be at least 2 characters long")
            
            if len(user_data.business_name.strip()) > 100:
                raise ValidationException("Business name cannot exceed 100 characters")
            
            # Validate product categories limit
            if len(user_data.product_categories) > 5:
                raise ValidationException("Cannot select more than 5 product categories")
        
        elif user_data.role == UserRole.BUYER:
            # Buyer-specific validation (optional fields, but validate if provided)
            if user_data.budget_range:
                if user_data.budget_range.min_amount < 0:
                    raise ValidationException("Budget minimum amount cannot be negative")
                if user_data.budget_range.max_amount < 0:
                    raise ValidationException("Budget maximum amount cannot be negative")
                if user_data.budget_range.min_amount > user_data.budget_range.max_amount:
                    raise ValidationException("Budget minimum amount cannot exceed maximum amount")
        
        # Common validation for all roles
        if not user_data.location:
            raise ValidationException("Location is required for all users")
        
        if not user_data.location.city or not user_data.location.city.strip():
            raise ValidationException("City is required in location")
        
        if not user_data.location.state or not user_data.location.state.strip():
            raise ValidationException("State is required in location")
        
        if not user_data.location.pincode or len(user_data.location.pincode) != 6:
            raise ValidationException("Valid 6-digit pincode is required")
        
        # Validate preferred languages
        if not user_data.preferred_languages or len(user_data.preferred_languages) == 0:
            raise ValidationException("At least one preferred language is required")
        
        if len(user_data.preferred_languages) > 3:
            raise ValidationException("Cannot select more than 3 preferred languages")
    
    def _create_vendor_profile_data(self, user_data: UserCreateRequest) -> Dict[str, Any]:
        """
        Create vendor-specific profile data.
        
        Args:
            user_data: User creation request data
            
        Returns:
            Vendor-specific data dictionary
        """
        return {
            "business_name": user_data.business_name.strip(),
            "business_type": user_data.business_type.value,
            "product_categories": [cat.value for cat in user_data.product_categories],
            "market_location": user_data.market_location.strip(),
            "verification_documents": [],
            "rating": 0.0,
            "total_transactions": 0,
            "total_revenue": "0"
        }
    
    def _create_buyer_profile_data(self, user_data: UserCreateRequest) -> Dict[str, Any]:
        """
        Create buyer-specific profile data.
        
        Args:
            user_data: User creation request data
            
        Returns:
            Buyer-specific data dictionary
        """
        buyer_data = {
            "purchase_history": [],
            "preferred_categories": [],
            "budget_range": None,
            "delivery_addresses": [],
            "total_purchases": 0,
            "total_spent": "0"
        }
        
        # Add optional fields if provided
        if user_data.preferred_categories:
            buyer_data["preferred_categories"] = [cat.value for cat in user_data.preferred_categories]
        
        if user_data.budget_range:
            buyer_data["budget_range"] = user_data.budget_range.model_dump()
        
        return buyer_data
    
    async def validate_profile_completeness(self, user_id: str) -> Dict[str, Any]:
        """
        Validate if user profile is complete based on role requirements.
        
        Args:
            user_id: User ID
            
        Returns:
            Validation result with completeness status and missing fields
            
        Raises:
            NotFoundException: If user not found
        """
        try:
            db = await get_database()
            user = await db.users.find_one({"user_id": user_id})
            
            if not user:
                raise NotFoundException("User not found")
            
            user_role = UserRole(user["role"])
            missing_fields = []
            is_complete = True
            
            # Check common required fields
            if not user.get("email"):
                missing_fields.append("email")
                is_complete = False
            
            if not user.get("location"):
                missing_fields.append("location")
                is_complete = False
            elif isinstance(user["location"], dict):
                location = user["location"]
                if not location.get("city"):
                    missing_fields.append("location.city")
                    is_complete = False
                if not location.get("state"):
                    missing_fields.append("location.state")
                    is_complete = False
                if not location.get("pincode"):
                    missing_fields.append("location.pincode")
                    is_complete = False
            
            if not user.get("preferred_languages") or len(user["preferred_languages"]) == 0:
                missing_fields.append("preferred_languages")
                is_complete = False
            
            # Check role-specific required fields
            if user_role == UserRole.VENDOR:
                if not user.get("business_name"):
                    missing_fields.append("business_name")
                    is_complete = False
                
                if not user.get("business_type"):
                    missing_fields.append("business_type")
                    is_complete = False
                
                if not user.get("product_categories") or len(user["product_categories"]) == 0:
                    missing_fields.append("product_categories")
                    is_complete = False
                
                if not user.get("market_location"):
                    missing_fields.append("market_location")
                    is_complete = False
            
            # Calculate completeness percentage
            total_required_fields = 4  # email, location, preferred_languages, role
            if user_role == UserRole.VENDOR:
                total_required_fields += 4  # business_name, business_type, product_categories, market_location
            
            completed_fields = total_required_fields - len(missing_fields)
            completeness_percentage = (completed_fields / total_required_fields) * 100
            
            return {
                "is_complete": is_complete,
                "completeness_percentage": round(completeness_percentage, 2),
                "missing_fields": missing_fields,
                "total_required_fields": total_required_fields,
                "completed_fields": completed_fields
            }
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to validate profile completeness for user {user_id}: {e}")
            raise ValidationException("Profile validation failed")
    
    async def add_verification_document(
        self,
        user_id: str,
        document_type: str,
        document_url: str,
        requesting_user_id: str
    ) -> List[DocumentReference]:
        """
        Add verification document for vendor.
        
        Args:
            user_id: User ID
            document_type: Type of document
            document_url: URL to the document
            requesting_user_id: ID of user making the request
            
        Returns:
            Updated list of verification documents
            
        Raises:
            NotFoundException: If user not found
            AuthorizationException: If user not authorized
            ValidationException: If user is not a vendor or document is invalid
        """
        try:
            # Check authorization
            if user_id != requesting_user_id:
                raise AuthorizationException("You can only add documents to your own profile")
            
            db = await get_database()
            user = await db.users.find_one({"user_id": user_id})
            
            if not user:
                raise NotFoundException("User not found")
            
            if user["role"] != UserRole.VENDOR.value:
                raise ValidationException("Only vendors can add verification documents")
            
            # Validate document type
            valid_document_types = ["aadhaar", "pan", "gst", "trade_license", "bank_statement"]
            if document_type not in valid_document_types:
                raise ValidationException(f"Invalid document type. Must be one of: {', '.join(valid_document_types)}")
            
            # Create document reference
            document_ref = DocumentReference(
                document_type=document_type,
                document_url=document_url,
                verification_status=VerificationStatus.UNVERIFIED,
                uploaded_at=datetime.utcnow()
            )
            
            # Get current documents
            current_documents = user.get("verification_documents", [])
            
            # Check if document type already exists
            existing_doc_index = None
            for i, doc in enumerate(current_documents):
                if doc.get("document_type") == document_type:
                    existing_doc_index = i
                    break
            
            # Replace existing document or add new one
            if existing_doc_index is not None:
                current_documents[existing_doc_index] = document_ref.model_dump()
            else:
                current_documents.append(document_ref.model_dump())
            
            # Update user
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "verification_documents": current_documents,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return [DocumentReference(**doc) for doc in current_documents]
            
        except (NotFoundException, AuthorizationException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Failed to add verification document for user {user_id}: {e}")
            raise ValidationException("Failed to add verification document")
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User response or None if not found
        """
        try:
            db = await get_database()
            user = await db.users.find_one({"user_id": user_id})
            
            if not user:
                return None
            
            return self._convert_user_to_response(user)
            
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User response or None if not found
        """
        try:
            db = await get_database()
            user = await db.users.find_one({"email": email})
            
            if not user:
                return None
            
            return self._convert_user_to_response(user)
            
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            return None
    
    async def update_user_profile(
        self,
        user_id: str,
        updates: UserUpdateRequest,
        requesting_user_id: str
    ) -> UserResponse:
        """
        Update user profile.
        
        Args:
            user_id: User ID to update
            updates: Profile updates
            requesting_user_id: ID of user making the request
            
        Returns:
            Updated user response
            
        Raises:
            NotFoundException: If user not found
            AuthorizationException: If user not authorized to update
            ValidationException: If update data is invalid
        """
        try:
            # Check authorization - users can only update their own profiles
            if user_id != requesting_user_id:
                raise AuthorizationException("You can only update your own profile")
            
            db = await get_database()
            user = await db.users.find_one({"user_id": user_id})
            
            if not user:
                raise NotFoundException("User not found")
            
            # Prepare update data
            update_data = {"updated_at": datetime.utcnow()}
            
            # Update basic fields
            if updates.phone is not None:
                # Validate phone number format
                # (Phone validation is handled in the model)
                update_data["phone"] = updates.phone
            
            if updates.preferred_languages is not None:
                update_data["preferred_languages"] = [lang.value for lang in updates.preferred_languages]
            
            if updates.location is not None:
                update_data["location"] = updates.location.model_dump()
            
            if updates.preferences is not None:
                update_data["preferences"] = updates.preferences.model_dump()
            
            # Update role-specific fields
            user_role = UserRole(user["role"])
            
            if user_role == UserRole.VENDOR:
                if updates.business_name is not None:
                    update_data["business_name"] = updates.business_name
                
                if updates.business_type is not None:
                    update_data["business_type"] = updates.business_type.value
                
                if updates.product_categories is not None:
                    update_data["product_categories"] = [cat.value for cat in updates.product_categories]
                
                if updates.market_location is not None:
                    update_data["market_location"] = updates.market_location
            
            elif user_role == UserRole.BUYER:
                if updates.preferred_categories is not None:
                    update_data["preferred_categories"] = [cat.value for cat in updates.preferred_categories]
                
                if updates.budget_range is not None:
                    update_data["budget_range"] = updates.budget_range.model_dump()
            
            # Update user in database
            result = await db.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise ValidationException("No changes were made")
            
            # Get updated user
            updated_user = await db.users.find_one({"user_id": user_id})
            return self._convert_user_to_response(updated_user)
            
        except (NotFoundException, AuthorizationException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Failed to update user profile {user_id}: {e}")
            raise ValidationException("Profile update failed")
    
    async def get_user_preferences(self, user_id: str) -> UserPreferences:
        """
        Get user preferences.
        
        Args:
            user_id: User ID
            
        Returns:
            User preferences
            
        Raises:
            NotFoundException: If user not found
        """
        try:
            db = await get_database()
            user = await db.users.find_one({"user_id": user_id})
            
            if not user:
                raise NotFoundException("User not found")
            
            preferences_data = user.get("preferences", {})
            return UserPreferences(**preferences_data)
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Failed to get user preferences {user_id}: {e}")
            raise NotFoundException("User preferences not found")
    
    async def update_user_preferences(
        self,
        user_id: str,
        preferences: UserPreferences,
        requesting_user_id: str
    ) -> UserPreferences:
        """
        Update user preferences.
        
        Args:
            user_id: User ID
            preferences: New preferences
            requesting_user_id: ID of user making the request
            
        Returns:
            Updated preferences
            
        Raises:
            NotFoundException: If user not found
            AuthorizationException: If user not authorized
        """
        try:
            # Check authorization
            if user_id != requesting_user_id:
                raise AuthorizationException("You can only update your own preferences")
            
            db = await get_database()
            
            result = await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "preferences": preferences.model_dump(),
                    "updated_at": datetime.utcnow()
                }}
            )
            
            if result.matched_count == 0:
                raise NotFoundException("User not found")
            
            return preferences
            
        except (NotFoundException, AuthorizationException):
            raise
        except Exception as e:
            logger.error(f"Failed to update user preferences {user_id}: {e}")
            raise ValidationException("Preferences update failed")
    
    async def add_delivery_address(
        self,
        user_id: str,
        address: Address,
        requesting_user_id: str
    ) -> List[Address]:
        """
        Add delivery address for buyer.
        
        Args:
            user_id: User ID
            address: Address to add
            requesting_user_id: ID of user making the request
            
        Returns:
            Updated list of addresses
            
        Raises:
            NotFoundException: If user not found
            AuthorizationException: If user not authorized
            ValidationException: If user is not a buyer
        """
        try:
            # Check authorization
            if user_id != requesting_user_id:
                raise AuthorizationException("You can only update your own addresses")
            
            db = await get_database()
            user = await db.users.find_one({"user_id": user_id})
            
            if not user:
                raise NotFoundException("User not found")
            
            if user["role"] != UserRole.BUYER.value:
                raise ValidationException("Only buyers can add delivery addresses")
            
            # Get current addresses
            current_addresses = user.get("delivery_addresses", [])
            
            # If this is the first address or marked as default, make it default
            if not current_addresses or address.is_default:
                # Remove default flag from other addresses
                for addr in current_addresses:
                    addr["is_default"] = False
                address.is_default = True
            
            # Add new address
            current_addresses.append(address.model_dump())
            
            # Update user
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "delivery_addresses": current_addresses,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            return [Address(**addr) for addr in current_addresses]
            
        except (NotFoundException, AuthorizationException, ValidationException):
            raise
        except Exception as e:
            logger.error(f"Failed to add delivery address for user {user_id}: {e}")
            raise ValidationException("Failed to add delivery address")
    
    async def update_verification_status(
        self,
        user_id: str,
        status: VerificationStatus,
        admin_user_id: str
    ) -> UserResponse:
        """
        Update user verification status (admin only).
        
        Args:
            user_id: User ID
            status: New verification status
            admin_user_id: Admin user ID
            
        Returns:
            Updated user response
            
        Raises:
            NotFoundException: If user not found
            AuthorizationException: If not admin
        """
        try:
            db = await get_database()
            
            # Check if requesting user is admin
            admin_user = await db.users.find_one({"user_id": admin_user_id})
            if not admin_user or admin_user["role"] != UserRole.ADMIN.value:
                raise AuthorizationException("Only admins can update verification status")
            
            # Update verification status
            result = await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "verification_status": status.value,
                    "verified_by": admin_user_id,
                    "verified_at": datetime.utcnow() if status == VerificationStatus.VERIFIED else None,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            if result.matched_count == 0:
                raise NotFoundException("User not found")
            
            # Get updated user
            updated_user = await db.users.find_one({"user_id": user_id})
            return self._convert_user_to_response(updated_user)
            
        except (NotFoundException, AuthorizationException):
            raise
        except Exception as e:
            logger.error(f"Failed to update verification status for user {user_id}: {e}")
            raise ValidationException("Verification status update failed")
    
    async def deactivate_user(
        self,
        user_id: str,
        admin_user_id: str,
        reason: str
    ) -> Dict[str, str]:
        """
        Deactivate user account (admin only).
        
        Args:
            user_id: User ID to deactivate
            admin_user_id: Admin user ID
            reason: Reason for deactivation
            
        Returns:
            Deactivation confirmation
            
        Raises:
            NotFoundException: If user not found
            AuthorizationException: If not admin
        """
        try:
            db = await get_database()
            
            # Check if requesting user is admin
            admin_user = await db.users.find_one({"user_id": admin_user_id})
            if not admin_user or admin_user["role"] != UserRole.ADMIN.value:
                raise AuthorizationException("Only admins can deactivate users")
            
            # Deactivate user
            result = await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "is_active": False,
                    "deactivated_by": admin_user_id,
                    "deactivated_at": datetime.utcnow(),
                    "deactivation_reason": reason,
                    "updated_at": datetime.utcnow()
                }}
            )
            
            if result.matched_count == 0:
                raise NotFoundException("User not found")
            
            return {
                "message": "User account has been deactivated",
                "user_id": user_id,
                "deactivated_at": datetime.utcnow().isoformat()
            }
            
        except (NotFoundException, AuthorizationException):
            raise
        except Exception as e:
            logger.error(f"Failed to deactivate user {user_id}: {e}")
            raise ValidationException("User deactivation failed")
    
    async def search_users(
        self,
        query: str,
        role: Optional[UserRole] = None,
        location: Optional[str] = None,
        limit: int = 20,
        skip: int = 0
    ) -> List[UserResponse]:
        """
        Search users by various criteria.
        
        Args:
            query: Search query (name, email, business name)
            role: Filter by user role
            location: Filter by location
            limit: Maximum results to return
            skip: Number of results to skip
            
        Returns:
            List of matching users
        """
        try:
            db = await get_database()
            
            # Build search filter
            search_filter = {"is_active": True}
            
            if query:
                search_filter["$or"] = [
                    {"full_name": {"$regex": query, "$options": "i"}},
                    {"email": {"$regex": query, "$options": "i"}},
                    {"business_name": {"$regex": query, "$options": "i"}}
                ]
            
            if role:
                search_filter["role"] = role.value
            
            if location:
                search_filter["$or"] = search_filter.get("$or", []) + [
                    {"location.city": {"$regex": location, "$options": "i"}},
                    {"location.state": {"$regex": location, "$options": "i"}},
                    {"market_location": {"$regex": location, "$options": "i"}}
                ]
            
            # Execute search
            cursor = db.users.find(search_filter).skip(skip).limit(limit)
            users = await cursor.to_list(length=limit)
            
            return [self._convert_user_to_response(user) for user in users]
            
        except Exception as e:
            logger.error(f"User search failed: {e}")
            return []
    
    def _convert_user_to_response(self, user: Dict[str, Any]) -> UserResponse:
        """
        Convert database user document to UserResponse.
        
        Args:
            user: User document from database
            
        Returns:
            UserResponse object
        """
        # Convert location data - handle empty or missing location gracefully
        location_data = user.get("location", {})
        if not location_data or not isinstance(location_data, dict):
            location_data = {}
        # Use default values for missing required fields
        location = LocationData(
            address=location_data.get("address"),
            city=location_data.get("city"),
            state=location_data.get("state"),
            pincode=location_data.get("pincode"),
            country=location_data.get("country", "India"),
            coordinates=location_data.get("coordinates")
        )
        
        # Convert preferences
        preferences_data = user.get("preferences", {})
        preferences = UserPreferences(**preferences_data)
        
        # Convert preferred languages
        preferred_languages = [
            SupportedLanguage(lang) for lang in user.get("preferred_languages", ["en"])
        ]
        
        # Base response data
        response_data = {
            "user_id": user["user_id"],
            "email": user["email"],
            "phone": user.get("phone"),
            "role": UserRole(user["role"]),
            "preferred_languages": preferred_languages,
            "location": location,
            "verification_status": VerificationStatus(user.get("verification_status", "unverified")),
            "preferences": preferences,
            "is_active": user.get("is_active", True),
            "created_at": user.get("created_at", datetime.utcnow()),
            "updated_at": user.get("updated_at", datetime.utcnow()),
            "last_login": user.get("last_login")
        }
        
        # Add role-specific fields
        user_role = UserRole(user["role"])
        
        if user_role == UserRole.VENDOR:
            response_data.update({
                "business_name": user.get("business_name"),
                "business_type": BusinessType(user["business_type"]) if user.get("business_type") else None,
                "product_categories": [
                    ProductCategory(cat) for cat in user.get("product_categories", [])
                ],
                "market_location": user.get("market_location"),
                "rating": user.get("rating", 0.0),
                "total_transactions": user.get("total_transactions", 0)
            })
        
        elif user_role == UserRole.BUYER:
            budget_range_data = user.get("budget_range")
            response_data.update({
                "preferred_categories": [
                    ProductCategory(cat) for cat in user.get("preferred_categories", [])
                ],
                "budget_range": budget_range_data,
                "total_purchases": user.get("total_purchases", 0)
            })
        
        return UserResponse(**response_data)