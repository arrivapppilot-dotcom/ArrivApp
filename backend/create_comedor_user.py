#!/usr/bin/env python
"""
Script to create a comedor (kitchen manager) user in the database.
This user can only access the /comedor page.
"""

import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import Base, User, UserRole, School
from app.core.config import settings
import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def create_comedor_user(school_name: str = None, password: str = "comedor123"):
    """
    Create a new comedor user that can access only the /comedor page.
    
    Args:
        school_name: Name of the school (if None, uses first active school)
        password: Password for the user (default: comedor123)
    """
    db = SessionLocal()
    
    try:
        # Get school
        if school_name:
            school = db.query(School).filter(School.name == school_name).first()
            if not school:
                print(f"❌ School '{school_name}' not found")
                return False
        else:
            # Get first active school
            school = db.query(School).filter(School.is_active == True).first()
            if not school:
                print("❌ No active schools found in database")
                return False
        
        print(f"✅ Found school: {school.name}")
        
        # Check if comedor user already exists
        existing_user = db.query(User).filter(User.username == "comedor").first()
        if existing_user:
            print(f"⚠️  User 'comedor' already exists")
            return False
        
        # Create new comedor user
        new_user = User(
            email="comedor@example.com",
            username="comedor",
            full_name="Kitchen Manager",
            hashed_password=hash_password(password),
            role=UserRole.comedor,
            school_id=school.id,
            is_active=True,
            is_admin=False
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("\n✅ Comedor user created successfully!")
        print(f"   Username: comedor")
        print(f"   Password: {password}")
        print(f"   Email: comedor@example.com")
        print(f"   School: {school.name}")
        print(f"   Role: comedor")
        print(f"   Access: /comedor page only")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    school_name = sys.argv[1] if len(sys.argv) > 1 else None
    password = sys.argv[2] if len(sys.argv) > 2 else "comedor123"
    
    print("\n🍽️  Creating Comedor User Profile...")
    print(f"   School: {school_name or 'First active school'}")
    print(f"   Password: {password}\n")
    
    success = create_comedor_user(school_name, password)
    sys.exit(0 if success else 1)
