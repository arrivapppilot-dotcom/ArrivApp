"""
Migration script to add kitchen-related tables to the database
"""
from app.core.database import engine, Base
from app.models.models import StudentDietaryNeeds, KitchenAttendance

def run_migration():
    """Create new tables for kitchen management"""
    print("Creating kitchen-related tables...")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ StudentDietaryNeeds table created")
    print("✅ KitchenAttendance table created")
    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
