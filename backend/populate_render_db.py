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
    from app.models.models import School, Student, CheckIn
    
    # Test database connection
    try:
        db = SessionLocal()
        schools = db.query(School).count()
        students = db.query(Student).count()
        checkins = db.query(CheckIn).count()
        db.close()
        print(f"✅ Connected to database")
        print(f"   Schools: {schools}")
        print(f"   Students: {students}")
        print(f"   Check-ins: {checkins}\n")
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        print("Make sure DATABASE_URL is set correctly.")
        sys.exit(1)
    
    # Clear old TEST data to avoid unique constraint violations
    print("🧹 Cleaning up old TEST data...")
    try:
        db = SessionLocal()
        # Delete all test students (those with student_id starting with TEST)
        old_test_students = db.query(Student).filter(
            Student.student_id.like('TEST%')
        ).count()
        
        if old_test_students > 0:
            db.query(CheckIn).filter(
                CheckIn.student_id.in_(
                    db.query(Student.id).filter(Student.student_id.like('TEST%'))
                )
            ).delete()
            db.query(Student).filter(Student.student_id.like('TEST%')).delete()
            db.commit()
            print(f"   ✅ Deleted {old_test_students} old TEST students and their check-ins\n")
        else:
            print(f"   ℹ️  No old TEST data found\n")
        db.close()
    except Exception as e:
        print(f"   ⚠️  Could not clean old data: {e}")
        print("   Continuing anyway...\n")
    
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
