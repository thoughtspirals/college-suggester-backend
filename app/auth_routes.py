"""
Authentication and User Management API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import timedelta

from app.database import get_db
from app.models import User, Role, Permission
from app.auth_schemas import (
    UserCreate, UserUpdate, UserResponse, 
    LoginRequest, LoginResponse, PasswordChangeRequest,
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionCreate, PermissionUpdate, PermissionResponse,
    UserRoleAssignment, RolePermissionAssignment
)
from app.auth_crud import UserCRUD, RoleCRUD, PermissionCRUD
from app.auth_utils import AuthUtils, Permissions, Roles
from app.auth_dependencies import (
    get_current_user, get_current_active_user, get_current_verified_user,
    require_role, require_permission, require_admin, require_self_or_admin
)


# Create router
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
user_router = APIRouter(prefix="/users", tags=["User Management"])  
admin_router = APIRouter(prefix="/admin", tags=["Admin"])


# ================ Authentication Routes ================

@auth_router.post("/register", response_model=UserResponse)
def register_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        db_user = UserCRUD.create_user(db, user)
        
        # Convert roles to simple list of names for response
        role_names = [role.name for role in db_user.roles if role.is_active]
        
        return UserResponse(
            id=db_user.id,
            email=db_user.email,
            phone=db_user.phone,
            full_name=db_user.full_name,
            login_count=db_user.login_count,
            is_active=db_user.is_active,
            is_verified=db_user.is_verified,
            created_at=db_user.created_at,
            last_login=db_user.last_login,
            roles=role_names
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@auth_router.post("/login", response_model=LoginResponse)
def login_user(
    login_request: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticate user and return access token."""
    user = UserCRUD.authenticate_user(db, login_request.email, login_request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)  # Or from config
    access_token = AuthUtils.create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=access_token_expires
    )
    
    # Prepare user response
    role_names = [role.name for role in user.roles if role.is_active]
    user_response = UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        login_count=user.login_count,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login,
        roles=role_names
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response
    )


@auth_router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    role_names = [role.name for role in current_user.roles if role.is_active]
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        phone=current_user.phone,
        full_name=current_user.full_name,
        login_count=current_user.login_count,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        roles=role_names
    )


@auth_router.post("/change-password")
def change_password(
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password."""
    success = UserCRUD.change_password(
        db, 
        current_user.id, 
        password_change.current_password,
        password_change.new_password
    )
    
    if success:
        return {"message": "Password changed successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


# ================ User Management Routes ================

@user_router.get("", response_model=List[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    current_user: User = Depends(require_permission(Permissions.READ_USERS)),
    db: Session = Depends(get_db)
):
    """List users (requires read:users permission)."""
    users = UserCRUD.get_users(db, skip=skip, limit=limit, active_only=active_only)
    
    response = []
    for user in users:
        role_names = [role.name for role in user.roles if role.is_active]
        response.append(UserResponse(
            id=user.id,
            email=user.email,
            phone=user.phone,
            full_name=user.full_name,
            login_count=user.login_count,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
            roles=role_names
        ))
    
    return response


@user_router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(require_self_or_admin()),
    db: Session = Depends(get_db)
):
    """Get specific user (self or admin access)."""
    user = UserCRUD.get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    role_names = [role.name for role in user.roles if role.is_active]
    
    return UserResponse(
        id=user.id,
        email=user.email,
        phone=user.phone,
        full_name=user.full_name,
        login_count=user.login_count,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at,
        last_login=user.last_login,
        roles=role_names
    )


@user_router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(require_self_or_admin()),
    db: Session = Depends(get_db)
):
    """Update user information (self or admin access)."""
    updated_user = UserCRUD.update_user(db, user_id, user_update)
    
    role_names = [role.name for role in updated_user.roles if role.is_active]
    
    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        phone=updated_user.phone,
        full_name=updated_user.full_name,
        login_count=updated_user.login_count,
        is_active=updated_user.is_active,
        is_verified=updated_user.is_verified,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login,
        roles=role_names
    )


@user_router.delete("/{user_id}")
def delete_user(
    user_id: int,
    current_user: User = Depends(require_permission(Permissions.DELETE_USERS)),
    db: Session = Depends(get_db)
):
    """Delete user (requires delete:users permission)."""
    success = UserCRUD.delete_user(db, user_id)
    if success:
        return {"message": "User deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User deletion failed"
        )


# ================ Admin Routes ================

@admin_router.get("/roles", response_model=List[RoleResponse])
def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = Query(True),
    current_user: User = Depends(require_permission(Permissions.READ_ROLES)),
    db: Session = Depends(get_db)
):
    """List roles (requires read:roles permission)."""
    roles = RoleCRUD.get_roles(db, skip=skip, limit=limit, active_only=active_only)
    
    response = []
    for role in roles:
        permission_names = [permission.name for permission in role.permissions]
        response.append(RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
            created_at=role.created_at,
            permissions=permission_names
        ))
    
    return response


@admin_router.post("/roles", response_model=RoleResponse)
def create_role(
    role: RoleCreate,
    current_user: User = Depends(require_permission(Permissions.WRITE_ROLES)),
    db: Session = Depends(get_db)
):
    """Create new role (requires write:roles permission)."""
    db_role = RoleCRUD.create_role(db, role)
    
    return RoleResponse(
        id=db_role.id,
        name=db_role.name,
        description=db_role.description,
        is_active=db_role.is_active,
        created_at=db_role.created_at,
        permissions=[]
    )


@admin_router.get("/permissions", response_model=List[PermissionResponse])
def list_permissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(require_permission(Permissions.READ_PERMISSIONS)),
    db: Session = Depends(get_db)
):
    """List permissions (requires read:permissions permission)."""
    permissions = PermissionCRUD.get_permissions(db, skip=skip, limit=limit)
    return permissions


@admin_router.post("/permissions", response_model=PermissionResponse)
def create_permission(
    permission: PermissionCreate,
    current_user: User = Depends(require_permission(Permissions.WRITE_PERMISSIONS)),
    db: Session = Depends(get_db)
):
    """Create new permission (requires write:permissions permission)."""
    db_permission = PermissionCRUD.create_permission(db, permission)
    return db_permission


@admin_router.post("/assign-role")
def assign_role_to_user(
    assignment: UserRoleAssignment,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Assign role to user (requires admin access)."""
    success = UserCRUD.assign_role_to_user(db, assignment.user_id, assignment.role_id)
    if success:
        return {"message": "Role assigned successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role assignment failed"
        )


@admin_router.post("/assign-permission")
def assign_permission_to_role(
    assignment: RolePermissionAssignment,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Assign permission to role (requires admin access)."""
    success = RoleCRUD.assign_permission_to_role(db, assignment.role_id, assignment.permission_id)
    if success:
        return {"message": "Permission assigned successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Permission assignment failed"
        )


# ================ Utility Routes ================

@admin_router.get("/user/{user_id}/permissions")
def get_user_permissions(
    user_id: int,
    current_user: User = Depends(require_admin()),
    db: Session = Depends(get_db)
):
    """Get all permissions for a specific user (requires admin access)."""
    permissions = UserCRUD.get_user_permissions(db, user_id)
    return {"user_id": user_id, "permissions": permissions}
