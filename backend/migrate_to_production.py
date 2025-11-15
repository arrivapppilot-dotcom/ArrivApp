"""
Migrate data from local SQLite database to production PostgreSQL
This script copies all schools, students, and users from local to production
"""
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.models import School, Student, User, CheckIn, Justification

# Local SQLite database
LOCAL_DB = "sqlite:///arrivapp.db"

# Production PostgreSQL database
PROD_DB = os.getenv("DATABASE_URL", "")

if not PROD_DB:
    print("ERROR: DATABASE_URL environment variable not set")
    print("\nPlease run:")
    print("export DATABASE_URL='your_production_database_url'")
    sys.exit(1)

def migrate_data():
    """Migrate all data from local to production"""
    
    # Create engines
    local_engine = create_engine(LOCAL_DB)
    prod_engine = create_engine(PROD_DB)
    
    LocalSession = sessionmaker(bind=local_engine)
    ProdSession = sessionmaker(bind=prod_engine)
    
    local_db = LocalSession()
    prod_db = ProdSession()
    
    try:
        print("=" * 70)
        print("MIGRATING DATA FROM LOCAL TO PRODUCTION")
        print("=" * 70)
        
        # Check local data
        local_schools = local_db.query(School).count()
        local_students = local_db.query(Student).count()
        local_users = local_db.query(User).count()
        
        print(f"\nLocal database has:")
        print(f"  Schools: {local_schools}")
        print(f"  Students: {local_students}")
        print(f"  Users: {local_users}")
        
        if local_schools == 0 and local_students == 0:
            print("\n❌ No data found in local database!")
            return
        
        # Check production data
        prod_schools = prod_db.query(School).count()
        prod_students = prod_db.query(Student).count()
        prod_users = prod_db.query(User).count()
        
        print(f"\nProduction database currently has:")
        print(f"  Schools: {prod_schools}")
        print(f"  Students: {prod_students}")
        print(f"  Users: {prod_users}")
        
        # Ask for confirmation
        response = input("\n⚠️  This will ADD data to production. Continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return
        
        print("\n" + "=" * 70)
        print("Starting migration...")
        print("=" * 70)
        
        # Migrate Schools
        print("\n1. Migrating Schools...")
        schools = local_db.query(School).all()
        school_id_map = {}  # Map old IDs to new IDs
        
        for school in schools:
            # Check if school already exists
            existing = prod_db.query(School).filter(School.name == school.name).first()
            if existing:
                print(f"  ⚠️  School '{school.name}' already exists, skipping...")
                school_id_map[school.id] = existing.id
                continue
            
            new_school = School(
                name=school.name,
                address=school.address,
                contact_email=school.contact_email,
                contact_phone=school.contact_phone,
                timezone=school.timezone,
                is_active=school.is_active,
                created_at=school.created_at
            )
            prod_db.add(new_school)
            prod_db.flush()
            school_id_map[school.id] = new_school.id
            print(f"  ✓ Migrated: {school.name} (old ID: {school.id} → new ID: {new_school.id})")
        
        prod_db.commit()
        print(f"  ✓ Schools migration complete!")
        
        # Migrate Users (excluding admin which already exists)
        print("\n2. Migrating Users...")
        users = local_db.query(User).all()
        user_id_map = {}
        
        for user in users:
            # Skip admin user (already exists in production)
            if user.username == 'admin':
                existing_admin = prod_db.query(User).filter(User.username == 'admin').first()
                if existing_admin:
                    user_id_map[user.id] = existing_admin.id
                    print(f"  ⚠️  Admin user already exists, skipping...")
                continue
            
            # Check if user already exists
            existing = prod_db.query(User).filter(User.username == user.username).first()
            if existing:
                print(f"  ⚠️  User '{user.username}' already exists, skipping...")
                user_id_map[user.id] = existing.id
                continue
            
            new_user = User(
                username=user.username,
                email=user.email,
                hashed_password=user.hashed_password,
                full_name=user.full_name,
                role=user.role,
                school_id=school_id_map.get(user.school_id) if user.school_id else None,
                is_active=user.is_active,
                is_admin=user.is_admin,
                created_at=user.created_at
            )
            prod_db.add(new_user)
            prod_db.flush()
            user_id_map[user.id] = new_user.id
            print(f"  ✓ Migrated: {user.username} ({user.role.value})")
        
        prod_db.commit()
        print(f"  ✓ Users migration complete!")
        
        # Migrate Students
        print("\n3. Migrating Students...")
        students = local_db.query(Student).all()
        migrated_students = 0
        
        for i, student in enumerate(students, 1):
            # Check if student already exists
            existing = prod_db.query(Student).filter(Student.student_id == student.student_id).first()
            if existing:
                print(f"  ⚠️  Student ID '{student.student_id}' already exists, skipping...")
                continue
            
            new_student = Student(
                student_id=student.student_id,
                name=student.name,
                class_name=student.class_name,
                parent_email=student.parent_email,
                school_id=school_id_map.get(student.school_id),
                qr_code_path=student.qr_code_path,
                is_active=student.is_active,
                created_at=student.created_at
            )
            prod_db.add(new_student)
            migrated_students += 1
            
            # Commit every 100 students
            if i % 100 == 0:
                prod_db.commit()
                print(f"  → Migrated {i}/{len(students)} students...")
        
        prod_db.commit()
        print(f"  ✓ Students migration complete! ({migrated_students} new students)")
        
        # Final summary
        print("\n" + "=" * 70)
        print("MIGRATION SUMMARY")
        print("=" * 70)
        
        final_schools = prod_db.query(School).count()
        final_students = prod_db.query(Student).count()
        final_users = prod_db.query(User).count()
        
        print(f"Production database now has:")
        print(f"  Schools: {final_schools} (added {final_schools - prod_schools})")
        print(f"  Students: {final_students} (added {final_students - prod_students})")
        print(f"  Users: {final_users} (added {final_users - prod_users})")
        print("=" * 70)
        print("✓ Migration completed successfully!")
        print("\nNote: QR codes need to be regenerated for production.")
        print("You can do this from the admin panel: Students → Download QR Codes")
        
    except Exception as e:
        print(f"\n❌ Error during migration: {e}")
        import traceback
        traceback.print_exc()
        prod_db.rollback()
        raise
    finally:
        local_db.close()
        prod_db.close()


if __name__ == "__main__":
    migrate_data()
