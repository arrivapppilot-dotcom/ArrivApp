"""
One-time script to populate Render's production database with test data.
Run this to sync faker data to production.

Usage:
    python populate_render_db.py
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from populate_daily import TestDataManager

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Populating Render Production Database")
    print("=" * 70)
    print("\nThis will create test data on the PRODUCTION database.")
    print("Make sure DATABASE_URL points to Render's database.\n")
    
    from app.core.database import SessionLocal
    
    # Test database connection
    try:
        db = SessionLocal()
        from app.models.models import School
        schools = db.query(School).count()
        db.close()
        print(f"✅ Connected to database with {schools} schools\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("Make sure DATABASE_URL is set correctly.")
        sys.exit(1)
    
    # Run the faker
    manager = TestDataManager()
    success = manager.run()
    
    if success:
        print("\n" + "=" * 70)
        print("✅ Production database populated successfully!")
        print("=" * 70)
        print("\nDashboard will refresh automatically in 30 seconds.")
        print("If not, hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)")
    else:
        print("\n" + "=" * 70)
        print("❌ Failed to populate database")
        print("=" * 70)
        sys.exit(1)
