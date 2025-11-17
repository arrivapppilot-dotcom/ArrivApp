#!/usr/bin/env python
"""
Script to add comedor user to Render PostgreSQL database.

Usage:
    python add_comedor_to_render.py <render_database_url> [school_name] [password]

Example:
    python add_comedor_to_render.py "postgresql://user:pass@host/db" "Colegio San José" "kitchen2025"
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import NullPool
import bcrypt

# Import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.models.models import Base, User, UserRole, School


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def add_comedor_user(database_url: str, school_name: str = None, password: str = "comedor123"):
    """
    Add comedor user to Render database.
    
    Args:
        database_url: PostgreSQL connection string from Render
        school_name: Name of the school (if None, uses first active school)
        password: Password for the user (default: comedor123)
    """
    
    try:
        # Connect to Render database
        print("🔗 Connecting to Render database...")
        engine = create_engine(database_url, poolclass=NullPool)
        db = Session(engine)
        
        # Get school
        if school_name:
            school = db.query(School).filter(School.name == school_name).first()
            if not school:
                print(f"❌ School '{school_name}' not found in Render database")
                return False
        else:
            # Get first active school
            school = db.query(School).filter(School.is_active == True).first()
            if not school:
                print("❌ No active schools found in Render database")
                return False
        
        print(f"✅ Found school: {school.name}")
        
        # Check if comedor user already exists
        existing_user = db.query(User).filter(User.username == "comedor").first()
        if existing_user:
            print(f"⚠️  User 'comedor' already exists in Render database")
            db.close()
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
        
        print("\n✅ Comedor user created successfully in Render database!")
        print(f"   Username: comedor")
        print(f"   Password: {password}")
        print(f"   Email: comedor@example.com")
        print(f"   School: {school.name}")
        print(f"   Role: comedor")
        print(f"   Access: /comedor page only")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python add_comedor_to_render.py <render_database_url> [school_name] [password]")
        print("\nExample:")
        print('  python add_comedor_to_render.py "postgresql://user:pass@db.render.com/db" "Colegio San José" "kitchen2025"')
        sys.exit(1)
    
    database_url = sys.argv[1]
    school_name = sys.argv[2] if len(sys.argv) > 2 else None
    password = sys.argv[3] if len(sys.argv) > 3 else "comedor123"
    
    print("\n🍽️  Adding Comedor User to Render Database...")
    print(f"   School: {school_name or 'First active school'}")
    print(f"   Password: {password}\n")
    
    success = add_comedor_user(database_url, school_name, password)
    sys.exit(0 if success else 1)
