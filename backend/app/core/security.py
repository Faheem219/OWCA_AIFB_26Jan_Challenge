"""
Security utilities for the Multilingual Mandi Marketplace Platform.

This module provides password hashing, JWT token generation/validation,
and other security-related utilities.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import uuid

from app.core.config import settings
from app.models.auth import TokenData, TokenType
from app.models.user import UserRole


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class SecurityUtils:
    """Security utilities class."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.
        
        Args:
            length: Token length in bytes
            
        Returns:
            Random token as hex string
        """
        return secrets.token_hex(length)
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """
        Generate a numeric OTP.
        
        Args:
            length: OTP length
            
        Returns:
            Numeric OTP string
        """
        return ''.join(secrets.choice('0123456789') for _ in range(length))
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Hash a token for secure storage.
        
        Args:
            token: Token to hash
            
        Returns:
            SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()


class JWTManager:
    """JWT token management utilities."""
    
    @staticmethod
    def create_access_token(
        user_id: str,
        email: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.
        
        Args:
            user_id: User ID
            email: User email
            role: User role
            expires_delta: Custom expiration time
            
        Returns:
            JWT access token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        jti = str(uuid.uuid4())
        issued_at = datetime.utcnow()
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "token_type": TokenType.ACCESS.value,
            "exp": expire,
            "iat": issued_at,
            "jti": jti,
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        user_id: str,
        email: str,
        role: UserRole,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.
        
        Args:
            user_id: User ID
            email: User email
            role: User role
            expires_delta: Custom expiration time
            
        Returns:
            JWT refresh token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
            )
        
        jti = str(uuid.uuid4())
        issued_at = datetime.utcnow()
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "role": role.value,
            "token_type": TokenType.REFRESH.value,
            "exp": expire,
            "iat": issued_at,
            "jti": jti,
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_verification_token(
        user_id: str,
        email: str,
        verification_type: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT verification token.
        
        Args:
            user_id: User ID
            email: User email
            verification_type: Type of verification
            expires_delta: Custom expiration time
            
        Returns:
            JWT verification token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)  # 24 hours for verification
        
        jti = str(uuid.uuid4())
        issued_at = datetime.utcnow()
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "verification_type": verification_type,
            "token_type": TokenType.VERIFICATION.value,
            "exp": expire,
            "iat": issued_at,
            "jti": jti,
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_reset_token(
        user_id: str,
        email: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT password reset token.
        
        Args:
            user_id: User ID
            email: User email
            expires_delta: Custom expiration time
            
        Returns:
            JWT reset token string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour for password reset
        
        jti = str(uuid.uuid4())
        issued_at = datetime.utcnow()
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "token_type": TokenType.RESET.value,
            "exp": expire,
            "iat": issued_at,
            "jti": jti,
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            TokenData if valid, None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            role_str: str = payload.get("role")
            token_type_str: str = payload.get("token_type")
            exp: int = payload.get("exp")
            iat: int = payload.get("iat")
            jti: str = payload.get("jti")
            
            if not all([user_id, email, token_type_str, exp, iat, jti]):
                return None
            
            # Convert timestamps
            issued_at = datetime.fromtimestamp(iat)
            expires_at = datetime.fromtimestamp(exp)
            
            # Check if token is expired
            if datetime.utcnow() > expires_at:
                return None
            
            # Convert role and token type
            try:
                role = UserRole(role_str) if role_str else None
                token_type = TokenType(token_type_str)
            except ValueError:
                return None
            
            return TokenData(
                user_id=user_id,
                email=email,
                role=role,
                token_type=token_type,
                issued_at=issued_at,
                expires_at=expires_at,
                jti=jti
            )
            
        except JWTError:
            return None
    
    @staticmethod
    def is_token_blacklisted(jti: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            jti: JWT ID
            
        Returns:
            True if blacklisted, False otherwise
        """
        # TODO: Implement token blacklist check using Redis
        # For now, return False (no blacklist)
        return False
    
    @staticmethod
    def blacklist_token(jti: str, expires_at: datetime) -> bool:
        """
        Add a token to the blacklist.
        
        Args:
            jti: JWT ID
            expires_at: Token expiration time
            
        Returns:
            True if successfully blacklisted
        """
        # TODO: Implement token blacklisting using Redis
        # Store the JTI with expiration time
        return True


class PasswordValidator:
    """Password validation utilities."""
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {
            "is_valid": True,
            "errors": [],
            "score": 0,
            "suggestions": []
        }
        
        # Length check
        if len(password) < 8:
            result["is_valid"] = False
            result["errors"].append("Password must be at least 8 characters long")
        else:
            result["score"] += 1
        
        # Character variety checks
        has_lower = any(c.islower() for c in password)
        has_upper = any(c.isupper() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
        
        if not has_lower:
            result["suggestions"].append("Add lowercase letters")
        else:
            result["score"] += 1
            
        if not has_upper:
            result["suggestions"].append("Add uppercase letters")
        else:
            result["score"] += 1
            
        if not has_digit:
            result["suggestions"].append("Add numbers")
        else:
            result["score"] += 1
            
        if not has_special:
            result["suggestions"].append("Add special characters")
        else:
            result["score"] += 1
        
        # Require at least 3 character types
        char_types = sum([has_lower, has_upper, has_digit, has_special])
        if char_types < 3:
            result["is_valid"] = False
            result["errors"].append("Password must contain at least 3 different character types")
        
        # Common password check (basic)
        common_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        ]
        if password.lower() in common_passwords:
            result["is_valid"] = False
            result["errors"].append("Password is too common")
        
        return result
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """
        Generate a secure random password.
        
        Args:
            length: Password length
            
        Returns:
            Secure random password
        """
        import string
        
        # Ensure we have at least one character from each category
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*()_+-="
        
        # Start with one character from each category
        password = [
            secrets.choice(lowercase),
            secrets.choice(uppercase),
            secrets.choice(digits),
            secrets.choice(special)
        ]
        
        # Fill the rest with random characters from all categories
        all_chars = lowercase + uppercase + digits + special
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Shuffle the password
        secrets.SystemRandom().shuffle(password)
        
        return ''.join(password)


# Utility functions for common operations
def create_user_tokens(user_id: str, email: str, role: UserRole) -> Dict[str, Any]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User ID
        email: User email
        role: User role
        
    Returns:
        Dictionary with access and refresh tokens
    """
    access_token = JWTManager.create_access_token(user_id, email, role)
    refresh_token = JWTManager.create_refresh_token(user_id, email, role)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


def verify_token_and_get_user_id(token: str, expected_type: TokenType = TokenType.ACCESS) -> Optional[str]:
    """
    Verify a token and return the user ID if valid.
    
    Args:
        token: JWT token
        expected_type: Expected token type
        
    Returns:
        User ID if token is valid, None otherwise
    """
    token_data = JWTManager.decode_token(token)
    
    if not token_data:
        return None
    
    if token_data.token_type != expected_type:
        return None
    
    if JWTManager.is_token_blacklisted(token_data.jti):
        return None
    
    return token_data.user_id