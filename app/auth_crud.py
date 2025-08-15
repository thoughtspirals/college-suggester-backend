"""
CRUD operations for authentication and user management
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_
from typing import Optional, List
from datetime import datetime, timedelta

from app.models import User, Role, Permission, user_roles, role_permissions
from app.auth_schemas import UserCreate, UserUpdate, RoleCreate, RoleUpdate, PermissionCreate, PermissionUpdate
from app.auth_utils import AuthUtils
from fastapi import HTTPException, status


class UserCRUD:
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_phone(db: Session, phone: str) -> Optional[User]:
        """Get user by phone."""
        return db.query(User).filter(User.phone == phone).first()
    
    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[User]:
        """Get list of users with pagination."""
        query = db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Create a new user."""
        # Check if user already exists
        if UserCRUD.get_user_by_email(db, user.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if user.phone and UserCRUD.get_user_by_phone(db, user.phone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered"
            )
        
        # Hash password
        hashed_password = AuthUtils.hash_password(user.password)
        
        # Create user
        db_user = User(
            email=user.email,
            phone=user.phone,
            password_hash=hashed_password,
            full_name=user.full_name,
            login_count=0,
            is_active=True,
            is_verified=False
        )
        
        try:
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            # Assign default 'user' role
            default_role = RoleCRUD.get_role_by_name(db, "user")
            if default_role:
                UserCRUD.assign_role_to_user(db, db_user.id, default_role.id)
            
            return db_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User creation failed due to constraint violation"
            )
    
    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
        """Update user information."""
        db_user = UserCRUD.get_user(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        db_user.updated_at = datetime.utcnow()
        
        try:
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed due to constraint violation"
            )
    
    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Soft delete user (set is_active to False)."""
        db_user = UserCRUD.get_user(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        db_user.is_active = False
        db_user.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password."""
        user = UserCRUD.get_user_by_email(db, email)
        if not user or not user.is_active:
            return None
        
        if not AuthUtils.verify_password(password, user.password_hash):
            return None
        
        # Update login count and last login
        user.login_count += 1
        user.last_login = datetime.utcnow()
        db.commit()
        
        return user
    
    @staticmethod
    def change_password(db: Session, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password."""
        db_user = UserCRUD.get_user(db, user_id)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        if not AuthUtils.verify_password(current_password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        db_user.password_hash = AuthUtils.hash_password(new_password)
        db_user.updated_at = datetime.utcnow()
        db.commit()
        return True
    
    @staticmethod
    def assign_role_to_user(db: Session, user_id: int, role_id: int) -> bool:
        """Assign a role to a user."""
        user = UserCRUD.get_user(db, user_id)
        role = RoleCRUD.get_role(db, role_id)
        
        if not user or not role:
            return False
        
        # Check if already assigned
        if role in user.roles:
            return True
        
        user.roles.append(role)
        db.commit()
        return True
    
    @staticmethod
    def remove_role_from_user(db: Session, user_id: int, role_id: int) -> bool:
        """Remove a role from a user."""
        user = UserCRUD.get_user(db, user_id)
        role = RoleCRUD.get_role(db, role_id)
        
        if not user or not role:
            return False
        
        if role in user.roles:
            user.roles.remove(role)
            db.commit()
        
        return True
    
    @staticmethod
    def get_user_permissions(db: Session, user_id: int) -> List[str]:
        """Get all permissions for a user through their roles."""
        user = UserCRUD.get_user(db, user_id)
        if not user:
            return []
        
        permissions = set()
        for role in user.roles:
            if role.is_active:
                for permission in role.permissions:
                    permissions.add(permission.name)
        
        return list(permissions)


class RoleCRUD:
    @staticmethod
    def get_role(db: Session, role_id: int) -> Optional[Role]:
        """Get role by ID."""
        return db.query(Role).filter(Role.id == role_id).first()
    
    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Optional[Role]:
        """Get role by name."""
        return db.query(Role).filter(Role.name == name).first()
    
    @staticmethod
    def get_roles(db: Session, skip: int = 0, limit: int = 100, active_only: bool = True) -> List[Role]:
        """Get list of roles with pagination."""
        query = db.query(Role)
        if active_only:
            query = query.filter(Role.is_active == True)
        return query.offset(skip).limit(limit).all()
    
    @staticmethod
    def create_role(db: Session, role: RoleCreate) -> Role:
        """Create a new role."""
        # Check if role already exists
        if RoleCRUD.get_role_by_name(db, role.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name already exists"
            )
        
        db_role = Role(
            name=role.name,
            description=role.description,
            is_active=True
        )
        
        try:
            db.add(db_role)
            db.commit()
            db.refresh(db_role)
            return db_role
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role creation failed"
            )
    
    @staticmethod
    def update_role(db: Session, role_id: int, role_update: RoleUpdate) -> Role:
        """Update role information."""
        db_role = RoleCRUD.get_role(db, role_id)
        if not db_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        update_data = role_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_role, field, value)
        
        try:
            db.commit()
            db.refresh(db_role)
            return db_role
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role update failed"
            )
    
    @staticmethod
    def delete_role(db: Session, role_id: int) -> bool:
        """Soft delete role (set is_active to False)."""
        db_role = RoleCRUD.get_role(db, role_id)
        if not db_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        db_role.is_active = False
        db.commit()
        return True
    
    @staticmethod
    def assign_permission_to_role(db: Session, role_id: int, permission_id: int) -> bool:
        """Assign a permission to a role."""
        role = RoleCRUD.get_role(db, role_id)
        permission = PermissionCRUD.get_permission(db, permission_id)
        
        if not role or not permission:
            return False
        
        # Check if already assigned
        if permission in role.permissions:
            return True
        
        role.permissions.append(permission)
        db.commit()
        return True
    
    @staticmethod
    def remove_permission_from_role(db: Session, role_id: int, permission_id: int) -> bool:
        """Remove a permission from a role."""
        role = RoleCRUD.get_role(db, role_id)
        permission = PermissionCRUD.get_permission(db, permission_id)
        
        if not role or not permission:
            return False
        
        if permission in role.permissions:
            role.permissions.remove(permission)
            db.commit()
        
        return True


class PermissionCRUD:
    @staticmethod
    def get_permission(db: Session, permission_id: int) -> Optional[Permission]:
        """Get permission by ID."""
        return db.query(Permission).filter(Permission.id == permission_id).first()
    
    @staticmethod
    def get_permission_by_name(db: Session, name: str) -> Optional[Permission]:
        """Get permission by name."""
        return db.query(Permission).filter(Permission.name == name).first()
    
    @staticmethod
    def get_permissions(db: Session, skip: int = 0, limit: int = 100) -> List[Permission]:
        """Get list of permissions with pagination."""
        return db.query(Permission).offset(skip).limit(limit).all()
    
    @staticmethod
    def create_permission(db: Session, permission: PermissionCreate) -> Permission:
        """Create a new permission."""
        # Check if permission already exists
        if PermissionCRUD.get_permission_by_name(db, permission.name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission name already exists"
            )
        
        db_permission = Permission(
            name=permission.name,
            description=permission.description,
            resource=permission.resource,
            action=permission.action
        )
        
        try:
            db.add(db_permission)
            db.commit()
            db.refresh(db_permission)
            return db_permission
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission creation failed"
            )
    
    @staticmethod
    def update_permission(db: Session, permission_id: int, permission_update: PermissionUpdate) -> Permission:
        """Update permission information."""
        db_permission = PermissionCRUD.get_permission(db, permission_id)
        if not db_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
        
        update_data = permission_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_permission, field, value)
        
        try:
            db.commit()
            db.refresh(db_permission)
            return db_permission
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Permission update failed"
            )
    
    @staticmethod
    def delete_permission(db: Session, permission_id: int) -> bool:
        """Delete permission permanently."""
        db_permission = PermissionCRUD.get_permission(db, permission_id)
        if not db_permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Permission not found"
            )
        
        db.delete(db_permission)
        db.commit()
        return True
