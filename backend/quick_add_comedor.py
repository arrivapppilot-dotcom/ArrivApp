#!/usr/bin/env python
"""
Quick script to add comedor user to current database.
Run this in Render Shell: python backend/quick_add_comedor.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models import User, UserRole, School
import bcrypt


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def main():
    db = SessionLocal()
    
    try:
        # Check if comedor already exists
        existing = db.query(User).filter(User.username == "comedor").first()
        if existing:
            print("✅ Comedor user already exists!")
            print(f"   Username: {existing.username}")
            print(f"   School: {existing.school_id}")
            print(f"   Email: {existing.email}")
            db.close()
            return
        
        # Get first active school
        school = db.query(School).filter(School.is_active == True).first()
        if not school:
            print("❌ No active schools found!")
            db.close()
            return
        
        # Create comedor user
        comedor = User(
            email="comedor@example.com",
            username="comedor",
            full_name="Kitchen Manager",
            hashed_password=hash_password("kitchen2025"),
            role=UserRole.comedor,
            school_id=school.id,
            is_active=True,
            is_admin=False
        )
        
        db.add(comedor)
        db.commit()
        db.refresh(comedor)
        
        print("\n✅ Comedor user created successfully!")
        print(f"   Username: comedor")
        print(f"   Password: kitchen2025")
        print(f"   Email: comedor@example.com")
        print(f"   School: {school.name} (ID: {school.id})")
        print(f"   Role: comedor")
        print(f"   Access: /comedor page only\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
