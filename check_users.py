#!/usr/bin/env python3
"""
Script to check the user database for registered users
"""

import sys
import os
from sqlalchemy.orm import Session

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.auth_crud import UserCRUD
from app.models import User, Role


def check_users():
    """Check the user database for registered users"""
    db = SessionLocal()
    
    try:
        print("🔍 Checking user database for registered users...")
        print("=" * 60)
        
        # Get all users (including inactive ones)
        all_users = UserCRUD.get_users(db, skip=0, limit=1000, active_only=False)
        
        if not all_users:
            print("❌ No users found in the database.")
            return
        
        print(f"✅ Found {len(all_users)} user(s) in the database:")
        print()
        
        # Display user information
        for i, user in enumerate(all_users, 1):
            print(f"👤 User #{i}:")
            print(f"   ID: {user.id}")
            print(f"   Full Name: {user.full_name}")
            print(f"   Email: {user.email}")
            print(f"   Phone: {user.phone or 'Not provided'}")
            print(f"   Status: {'🟢 Active' if user.is_active else '🔴 Inactive'}")
            print(f"   Verified: {'✅ Yes' if user.is_verified else '❌ No'}")
            print(f"   Login Count: {user.login_count}")
            print(f"   Created: {user.created_at}")
            print(f"   Last Updated: {user.updated_at or 'Never'}")
            print(f"   Last Login: {user.last_login or 'Never'}")
            
            # Get user roles
            roles = [role.name for role in user.roles]
            print(f"   Roles: {', '.join(roles) if roles else 'No roles assigned'}")
            print("-" * 40)
        
        # Summary statistics
        active_users = [u for u in all_users if u.is_active]
        verified_users = [u for u in all_users if u.is_verified]
        
        print("\n📊 Summary Statistics:")
        print(f"   Total Users: {len(all_users)}")
        print(f"   Active Users: {len(active_users)}")
        print(f"   Inactive Users: {len(all_users) - len(active_users)}")
        print(f"   Verified Users: {len(verified_users)}")
        print(f"   Unverified Users: {len(all_users) - len(verified_users)}")
        
        # Check for users with login activity
        users_with_logins = [u for u in all_users if u.login_count > 0]
        print(f"   Users with Login Activity: {len(users_with_logins)}")
        
        if users_with_logins:
            print(f"   Total Login Attempts: {sum(u.login_count for u in all_users)}")
        
    except Exception as e:
        print(f"❌ Error checking users: {e}")
    finally:
        db.close()


def check_roles():
    """Check available roles in the database"""
    db = SessionLocal()
    
    try:
        print("\n🔍 Checking available roles...")
        print("=" * 40)
        
        roles = db.query(Role).filter(Role.is_active == True).all()
        
        if not roles:
            print("❌ No roles found in the database.")
            return
        
        print(f"✅ Found {len(roles)} role(s):")
        for role in roles:
            print(f"   • {role.name}: {role.description or 'No description'}")
            
    except Exception as e:
        print(f"❌ Error checking roles: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("🏫 College Connect - User Database Checker")
    print("=" * 60)
    
    check_users()
    check_roles()
    
    print("\n✅ Database check completed!")
