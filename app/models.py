from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy import UniqueConstraint
from sqlalchemy.sql import func

class College(Base):
    __tablename__ = "colleges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(Integer)  # e.g., 1150
    name = Column(String)
    status = Column(String)  # e.g., 'Government', 'Private', 'Aided'
    university = Column(String)
    region = Column(String)
     
    # Relationship with cutoffs
    cutoffs = relationship("Cutoff", back_populates="college")
    
    __table_args__ = (
        UniqueConstraint('code', 'name', 'status', name='unique_college_code_name_status'),
    )

class Cutoff(Base):
    __tablename__ = "cutoffs"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, ForeignKey('colleges.id'), nullable=False)
    college_code = Column(Integer, nullable=False)
    branch = Column(String)
    course_code = Column(Integer, nullable=False)
    category = Column(String)
    rank = Column(Integer, nullable=True)
    percent = Column(Float, nullable=True)
    gender = Column(String)
    level = Column(String)  # Home/Other/State level
    year = Column(Integer, nullable=True)
    stage = Column(String, nullable=True)
    
    # Relationship with college
    college = relationship("College", back_populates="cutoffs")

class RankedCollege(Base):
    __tablename__ = "ranked_colleges"

    id = Column(Integer, primary_key=True, index=True)
    college_id = Column(Integer, nullable=False)
    college_code = Column(Integer, nullable=False)
    college_name = Column(String, nullable=False)
    college_status = Column(String, nullable=True)
    branch = Column(String, nullable=False)  # Normalized branch name
    branch_code = Column(String, nullable=False)
    cutoff_rank = Column(Integer, nullable=False)
    rank_position = Column(Integer, nullable=False)
    year = Column(Integer, nullable=True)
    stage = Column(String, nullable=True)


# Association tables for many-to-many relationships
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

role_permissions = Table(
    'role_permissions', 
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, unique=True, index=True, nullable=True)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    login_count = Column(Integer, default=0, nullable=False)  # Counter for login attempts
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Many-to-many relationship with roles
    roles = relationship("Role", secondary=user_roles, back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # e.g., 'admin', 'user', 'moderator'
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Many-to-many relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # e.g., 'read:colleges', 'write:users', 'admin:all'
    description = Column(String, nullable=True)
    resource = Column(String, nullable=False)  # e.g., 'colleges', 'users', 'admin'
    action = Column(String, nullable=False)  # e.g., 'read', 'write', 'delete', 'create'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Many-to-many relationship with roles
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")
