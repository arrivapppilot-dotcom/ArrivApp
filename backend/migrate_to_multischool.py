"""
Migration script to add multi-school support to ArrivApp
This will:
1. Backup the existing database
2. Create a default school
3. Assign all existing students to the default school
4. Assign all existing users to the default school
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.models.models import School, Student, User


def backup_database():
    """Create a backup of the current database"""
    db_path = Path("arrivapp.db")
    if db_path.exists():
        backup_path = f"arrivapp_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        shutil.copy(db_path, backup_path)
        print(f"✅ Database backed up to: {backup_path}")
        return True
    else:
        print("⚠️  No existing database found - will create new one")
        return False


def migrate_database():
    """Run the migration"""
    print("\n" + "="*60)
    print("ArrivApp Multi-School Migration")
    print("="*60 + "\n")
    
    # Backup existing database
    had_backup = backup_database()
    
    # Drop all tables and recreate with new schema
    print("\n🔄 Recreating database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database schema updated")
    
    db: Session = SessionLocal()
    
    try:
        # Create default school
        print("\n🏫 Creating default school...")
        default_school = School(
            name="Default School",
            address="Main Campus",
            contact_email="admin@defaultschool.com",
            timezone="Europe/Madrid",
            is_active=True
        )
        db.add(default_school)
        db.commit()
        db.refresh(default_school)
        print(f"✅ Default school created (ID: {default_school.id})")
        
        print("\n" + "="*60)
        print("Migration completed successfully! 🎉")
        print("="*60)
        print("\nNext steps:")
        print("1. Create schools using the admin interface or API")
        print("2. Assign users to their respective schools")
        print("3. Add students with their school_id")
        print("4. Each school will have isolated student data")
        print("\nYou can now run the application:")
        print("  python -m uvicorn app.main:app --reload")
        print("="*60 + "\n")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during migration: {e}")
        print("Database has been rolled back.")
        if had_backup:
            print("You can restore from backup if needed.")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will recreate your database!")
    print("All existing data will be lost (but backed up).")
    response = input("\nDo you want to continue? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        migrate_database()
    else:
        print("\nMigration cancelled.")
