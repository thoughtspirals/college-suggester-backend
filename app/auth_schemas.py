"""
Authentication and User Management Schemas
"""

from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional
from datetime import datetime


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    full_name: str

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v is not None and len(v) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None

class UserInDB(UserBase):
    id: int
    login_count: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    roles: List["RoleInDB"] = []

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    id: int
    email: str
    phone: Optional[str] = None
    full_name: str
    login_count: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    roles: List[str] = []  # Just role names for simplicity

    class Config:
        from_attributes = True


# Role Schemas
class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class RoleInDB(RoleBase):
    id: int
    created_at: datetime
    is_active: bool
    permissions: List["PermissionInDB"] = []

    class Config:
        from_attributes = True

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    permissions: List[str] = []  # Just permission names

    class Config:
        from_attributes = True


# Permission Schemas
class PermissionBase(BaseModel):
    name: str
    description: Optional[str] = None
    resource: str
    action: str

class PermissionCreate(PermissionBase):
    pass

class PermissionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None

class PermissionInDB(PermissionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PermissionResponse(PermissionInDB):
    pass


# Authentication Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


# Role Assignment Schemas
class UserRoleAssignment(BaseModel):
    user_id: int
    role_id: int

class RolePermissionAssignment(BaseModel):
    role_id: int
    permission_id: int


# Update forward references
UserInDB.model_rebuild()
RoleInDB.model_rebuild()
