"""
Database initialization script for authentication system.
Creates default roles, permissions, and admin user.
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, Role, Permission
from app.auth_crud import UserCRUD, RoleCRUD, PermissionCRUD
from app.auth_schemas import UserCreate, RoleCreate, PermissionCreate
from app.auth_utils import Permissions, Roles, AuthUtils


def init_permissions(db: Session):
    """Initialize default permissions."""
    default_permissions = [
        # College data permissions
        {"name": Permissions.READ_COLLEGES, "description": "Read college data", 
         "resource": "colleges", "action": "read"},
        {"name": Permissions.WRITE_COLLEGES, "description": "Write/update college data", 
         "resource": "colleges", "action": "write"},
        {"name": Permissions.DELETE_COLLEGES, "description": "Delete college data", 
         "resource": "colleges", "action": "delete"},
        
        # User management permissions
        {"name": Permissions.READ_USERS, "description": "Read user data", 
         "resource": "users", "action": "read"},
        {"name": Permissions.WRITE_USERS, "description": "Write/update user data", 
         "resource": "users", "action": "write"},
        {"name": Permissions.DELETE_USERS, "description": "Delete users", 
         "resource": "users", "action": "delete"},
        
        # Role and permission management
        {"name": Permissions.READ_ROLES, "description": "Read roles", 
         "resource": "roles", "action": "read"},
        {"name": Permissions.WRITE_ROLES, "description": "Write/update roles", 
         "resource": "roles", "action": "write"},
        {"name": Permissions.DELETE_ROLES, "description": "Delete roles", 
         "resource": "roles", "action": "delete"},
        
        {"name": Permissions.READ_PERMISSIONS, "description": "Read permissions", 
         "resource": "permissions", "action": "read"},
        {"name": Permissions.WRITE_PERMISSIONS, "description": "Write/update permissions", 
         "resource": "permissions", "action": "write"},
        {"name": Permissions.DELETE_PERMISSIONS, "description": "Delete permissions", 
         "resource": "permissions", "action": "delete"},
        
        # Admin permissions
        {"name": Permissions.ADMIN_ALL, "description": "Full admin access", 
         "resource": "admin", "action": "all"},
        
        # System permissions
        {"name": Permissions.READ_ANALYTICS, "description": "Read analytics data", 
         "resource": "analytics", "action": "read"},
        {"name": Permissions.WRITE_ANALYTICS, "description": "Write analytics data", 
         "resource": "analytics", "action": "write"},
    ]
    
    created_permissions = []
    for perm_data in default_permissions:
        try:
            # Check if permission already exists
            existing = PermissionCRUD.get_permission_by_name(db, perm_data["name"])
            if existing:
                print(f"Permission '{perm_data['name']}' already exists")
                created_permissions.append(existing)
                continue
            
            permission = PermissionCreate(**perm_data)
            db_permission = PermissionCRUD.create_permission(db, permission)
            print(f"Created permission: {db_permission.name}")
            created_permissions.append(db_permission)
            
        except Exception as e:
            print(f"Error creating permission '{perm_data['name']}': {e}")
    
    return created_permissions


def init_roles(db: Session, permissions: list):
    """Initialize default roles."""
    # Create permission lookup
    perm_lookup = {p.name: p for p in permissions}
    
    default_roles = [
        {
            "name": Roles.SUPER_ADMIN,
            "description": "Super administrator with full system access",
            "permissions": [Permissions.ADMIN_ALL]
        },
        {
            "name": Roles.ADMIN,
            "description": "System administrator",
            "permissions": [
                Permissions.READ_COLLEGES, Permissions.WRITE_COLLEGES, Permissions.DELETE_COLLEGES,
                Permissions.READ_USERS, Permissions.WRITE_USERS, Permissions.DELETE_USERS,
                Permissions.READ_ROLES, Permissions.WRITE_ROLES,
                Permissions.READ_PERMISSIONS, Permissions.READ_ANALYTICS
            ]
        },
        {
            "name": Roles.MODERATOR,
            "description": "Content moderator",
            "permissions": [
                Permissions.READ_COLLEGES, Permissions.WRITE_COLLEGES,
                Permissions.READ_USERS, Permissions.READ_ANALYTICS
            ]
        },
        {
            "name": Roles.USER,
            "description": "Regular user",
            "permissions": [Permissions.READ_COLLEGES]
        },
        {
            "name": Roles.GUEST,
            "description": "Guest user with minimal access",
            "permissions": [Permissions.READ_COLLEGES]
        }
    ]
    
    created_roles = []
    for role_data in default_roles:
        try:
            # Check if role already exists
            existing = RoleCRUD.get_role_by_name(db, role_data["name"])
            if existing:
                print(f"Role '{role_data['name']}' already exists")
                created_roles.append(existing)
                continue
            
            # Create role
            role_create = RoleCreate(name=role_data["name"], description=role_data["description"])
            db_role = RoleCRUD.create_role(db, role_create)
            print(f"Created role: {db_role.name}")
            
            # Assign permissions to role
            for perm_name in role_data["permissions"]:
                if perm_name in perm_lookup:
                    success = RoleCRUD.assign_permission_to_role(db, db_role.id, perm_lookup[perm_name].id)
                    if success:
                        print(f"  - Assigned permission '{perm_name}' to role '{db_role.name}'")
                    else:
                        print(f"  - Failed to assign permission '{perm_name}' to role '{db_role.name}'")
                else:
                    print(f"  - Permission '{perm_name}' not found")
            
            created_roles.append(db_role)
            
        except Exception as e:
            print(f"Error creating role '{role_data['name']}': {e}")
    
    return created_roles


def create_admin_user(db: Session):
    """Create default admin user."""
    admin_email = "admin@collegeconnect.com"
    
    # Check if admin user already exists
    existing_admin = UserCRUD.get_user_by_email(db, admin_email)
    if existing_admin:
        print(f"Admin user '{admin_email}' already exists")
        return existing_admin
    
    # Create admin user
    admin_user_data = UserCreate(
        email=admin_email,
        phone="+919999999999",
        full_name="System Administrator",
        password="admin123456"  # Change this in production!
    )
    
    try:
        # Create user without assigning default role (we'll assign admin role)
        admin_user = User(
            email=admin_user_data.email,
            phone=admin_user_data.phone,
            password_hash=AuthUtils.hash_password(admin_user_data.password),
            full_name=admin_user_data.full_name,
            login_count=0,
            is_active=True,
            is_verified=True  # Pre-verify admin user
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        # Assign super_admin role
        super_admin_role = RoleCRUD.get_role_by_name(db, Roles.SUPER_ADMIN)
        if super_admin_role:
            success = UserCRUD.assign_role_to_user(db, admin_user.id, super_admin_role.id)
            if success:
                print(f"Assigned super_admin role to user '{admin_user.email}'")
            else:
                print(f"Failed to assign super_admin role to user '{admin_user.email}'")
        
        print(f"Created admin user: {admin_user.email}")
        print(f"Default password: admin123456 (CHANGE THIS IN PRODUCTION!)")
        
        return admin_user
        
    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return None


def init_database():
    """Initialize the database with default data."""
    print("Initializing authentication database...")
    
    # Create tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Initialize permissions
        print("\n--- Initializing Permissions ---")
        permissions = init_permissions(db)
        
        # Initialize roles
        print("\n--- Initializing Roles ---")
        roles = init_roles(db, permissions)
        
        # Create admin user
        print("\n--- Creating Admin User ---")
        admin_user = create_admin_user(db)
        
        print("\n--- Database initialization completed! ---")
        print(f"Created {len(permissions)} permissions")
        print(f"Created {len(roles)} roles")
        if admin_user:
            print(f"Created admin user: {admin_user.email}")
        
        print("\nDefault admin credentials:")
        print("Email: admin@collegeconnect.com")
        print("Password: admin123456")
        print("*** IMPORTANT: Change the admin password in production! ***")
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
