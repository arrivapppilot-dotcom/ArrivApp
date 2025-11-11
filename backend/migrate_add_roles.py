#!/usr/bin/env python3
"""
Migration script to add 'role' field to User table
Backs up existing database and updates schema
"""
import os
import shutil
from datetime import datetime
from sqlalchemy import create_engine, text
from app.core.config import get_settings

settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

def backup_database():
    """Create a backup of the current database"""
    if os.path.exists("arrivapp.db"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"arrivapp_backup_roles_{timestamp}.db"
        shutil.copy2("arrivapp.db", backup_name)
        print(f"✅ Database backed up to: {backup_name}")
        return backup_name
    return None

def migrate():
    """Add role column to users table"""
    print("\n🔄 Starting role migration...\n")
    
    # Backup first
    backup_file = backup_database()
    
    # Create engine
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if role column already exists
            result = conn.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
            
            if 'role' in columns:
                print("⚠️  Role column already exists. Skipping migration.")
                return
            
            # Add role column with default value 'teacher'
            print("📝 Adding 'role' column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'teacher'"))
            
            # Update existing users based on is_admin field
            print("🔄 Updating existing users...")
            conn.execute(text("""
                UPDATE users 
                SET role = CASE 
                    WHEN is_admin = 1 THEN 'admin'
                    ELSE 'teacher'
                END
            """))
            
            conn.commit()
            
            # Verify the changes
            result = conn.execute(text("SELECT username, is_admin, role FROM users"))
            users = result.fetchall()
            
            print("\n✅ Migration completed successfully!")
            print("\n📋 Updated users:")
            print("="*60)
            for username, is_admin, role in users:
                print(f"Username: {username} | Is Admin: {is_admin} | Role: {role}")
            print("="*60)
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        if backup_file:
            print(f"💡 You can restore from backup: {backup_file}")
        raise

if __name__ == "__main__":
    migrate()
    print("\n✨ All done! Your database now supports role-based access control.\n")
