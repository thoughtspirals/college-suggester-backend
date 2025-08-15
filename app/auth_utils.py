"""
Authentication utilities for password hashing, JWT tokens, and security functions
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
import secrets
import os
from fastapi import HTTPException, status


# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")  
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """Generate a random token for various purposes."""
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Basic phone validation."""
        import re
        # Remove all non-digit characters
        phone_digits = re.sub(r'\D', '', phone)
        # Check if it has 10-15 digits (international format)
        return 10 <= len(phone_digits) <= 15


class PermissionChecker:
    """Helper class to check user permissions."""
    
    @staticmethod
    def has_permission(user_permissions: list, required_permission: str) -> bool:
        """
        Check if user has a specific permission.
        
        Args:
            user_permissions: List of user's permission strings
            required_permission: Required permission in format 'action:resource'
        
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Check for exact match
        if required_permission in user_permissions:
            return True
        
        # Check for wildcard permissions (admin:all, etc.)
        for permission in user_permissions:
            if permission == "admin:all":
                return True
            
            # Check for resource-level wildcard (like "write:all")
            action, resource = required_permission.split(":", 1) 
            if f"{action}:all" in user_permissions:
                return True
                
            # Check for action-level wildcard (like "all:colleges")
            if f"all:{resource}" in user_permissions:
                return True
        
        return False
    
    @staticmethod
    def has_role(user_roles: list, required_role: str) -> bool:
        """Check if user has a specific role."""
        return required_role in user_roles
    
    @staticmethod
    def is_admin(user_roles: list) -> bool:
        """Check if user has admin role."""
        return "admin" in user_roles or "super_admin" in user_roles


# Predefined permission constants
class Permissions:
    """Predefined permission constants for consistency."""
    
    # College data permissions
    READ_COLLEGES = "read:colleges"
    WRITE_COLLEGES = "write:colleges"
    DELETE_COLLEGES = "delete:colleges"
    
    # User management permissions
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    
    # Role and permission management
    READ_ROLES = "read:roles"
    WRITE_ROLES = "write:roles"
    DELETE_ROLES = "delete:roles"
    
    READ_PERMISSIONS = "read:permissions"
    WRITE_PERMISSIONS = "write:permissions"
    DELETE_PERMISSIONS = "delete:permissions"
    
    # Admin permissions
    ADMIN_ALL = "admin:all"
    
    # System permissions
    READ_ANALYTICS = "read:analytics"
    WRITE_ANALYTICS = "write:analytics"


class Roles:
    """Predefined role constants."""
    
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"
