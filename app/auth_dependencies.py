"""
Authentication and Authorization Dependencies for FastAPI
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from functools import wraps

from app.database import get_db
from app.models import User
from app.auth_utils import AuthUtils, PermissionChecker
from app.auth_crud import UserCRUD


# Security scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token.
    """
    try:
        # Verify token
        payload = AuthUtils.verify_token(credentials.credentials)
        user_id: int = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = UserCRUD.get_user(db, user_id=user_id)
        if user is None or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user. This is an alias for get_current_user since
    we already check for active status there.
    """
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current verified user (email verified).
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.
    
    Usage:
        @router.get("/admin")
        def admin_endpoint(user: User = Depends(require_role("admin"))):
            return {"message": "Admin access granted"}
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        user_roles = [role.name for role in current_user.roles if role.is_active]
        
        if not PermissionChecker.has_role(user_roles, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        
        return current_user
    
    return role_checker


def require_permission(required_permission: str):
    """
    Dependency factory to require a specific permission.
    
    Usage:
        @router.get("/users")
        def list_users(user: User = Depends(require_permission("read:users"))):
            return {"users": []}
    """
    def permission_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        user_permissions = UserCRUD.get_user_permissions(db, current_user.id)
        
        if not PermissionChecker.has_permission(user_permissions, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{required_permission}' required"
            )
        
        return current_user
    
    return permission_checker


def require_admin():
    """
    Dependency to require admin role.
    """
    def admin_checker(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        user_roles = [role.name for role in current_user.roles if role.is_active]
        
        if not PermissionChecker.is_admin(user_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        return current_user
    
    return admin_checker


def require_self_or_admin(user_id_param: str = "user_id"):
    """
    Dependency factory to require that the user is accessing their own resource or is an admin.
    
    Args:
        user_id_param: The name of the path parameter containing the user ID
    
    Usage:
        @router.get("/users/{user_id}")
        def get_user(
            user_id: int,
            current_user: User = Depends(require_self_or_admin("user_id"))
        ):
            return {"user_id": user_id}
    """
    def self_or_admin_checker(
        path_user_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> User:
        # Check if user is accessing their own resource
        if current_user.id == path_user_id:
            return current_user
        
        # Check if user is admin
        user_roles = [role.name for role in current_user.roles if role.is_active]
        if PermissionChecker.is_admin(user_roles):
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only access your own resources or need admin privileges"
        )
    
    return self_or_admin_checker


# Optional authentication - for endpoints that can work with or without auth
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    Useful for endpoints that can work with or without authentication.
    """
    if not credentials:
        return None
    
    try:
        payload = AuthUtils.verify_token(credentials.credentials)
        user_id: int = payload.get("sub")
        
        if user_id is None:
            return None
        
        user = UserCRUD.get_user(db, user_id=user_id)
        if user is None or not user.is_active:
            return None
        
        return user
    
    except Exception:
        return None
