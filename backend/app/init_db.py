"""
Initialize the database with a default admin user.
Run this script once after setting up the database.

Usage:
    python -m app.init_db
"""

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.models import User, Student
import sys


def init_db():
    """Initialize database with default admin user."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == "admin").first()
        
        if not admin:
            print("Creating default admin user...")
            admin = User(
                email="admin@arrivapp.com",
                username="admin",
                full_name="Administrator",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("✓ Admin user created successfully!")
            print("  Username: admin")
            print("  Password: admin123")
            print("  ⚠️  IMPORTANT: Change this password in production!")
        else:
            print("✓ Admin user already exists")
        
        # Check for sample data
        student_count = db.query(Student).count()
        print(f"\n✓ Database initialized successfully!")
        print(f"  Students: {student_count}")
        print(f"  Users: {db.query(User).count()}")
        
        if student_count == 0:
            print("\n💡 Tip: Add students through the admin panel or API")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
