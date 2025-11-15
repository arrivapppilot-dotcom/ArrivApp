"""
Populate production database with schools and students
Run this script to add initial data to the production PostgreSQL database
"""
import os
import sys
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import School, Student, User, UserRole
from app.core.security import get_password_hash
import random

# Production database URL from environment or hardcoded
DATABASE_URL = os.getenv("DATABASE_URL", "")

if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    print("Please set it to your Render PostgreSQL URL")
    sys.exit(1)

# Create engine and session
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

fake = Faker(['es_ES', 'es_MX'])

def create_schools_and_students(num_schools=10, students_per_school=85):
    """Create schools and students in production database"""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print(f"POPULATING PRODUCTION DATABASE")
        print(f"Creating {num_schools} schools with {students_per_school} students each")
        print(f"Total students: {num_schools * students_per_school}")
        print("=" * 70)
        
        # School names
        school_names = [
            "Colegio San Fernando",
            "Instituto Cervantes Madrid",
            "Escuela Internacional Europa",
            "Colegio Bilingüe Goya",
            "Academia Santa Teresa",
            "Instituto Técnico Industrial",
            "Colegio Virgen del Carmen",
            "Escuela Superior de Comercio",
            "Instituto Ramón y Cajal",
            "Colegio Nuestra Señora de Fátima",
            "Academia Miguel de Cervantes",
            "Instituto Científico Galileo",
            "Colegio Internacional Madrid",
            "Escuela Tecnológica Avanzada",
            "Instituto Bilingüe Central"
        ]
        
        grades = ["1º ESO", "2º ESO", "3º ESO", "4º ESO", "1º Bach", "2º Bach"]
        sections = ["A", "B", "C"]
        
        for i in range(num_schools):
            school_name = school_names[i] if i < len(school_names) else f"Colegio {fake.company()}"
            
            # Create school
            school = School(
                name=school_name,
                address=fake.address().replace('\n', ', '),
                contact_email=f"admin@{school_name.lower().replace(' ', '').replace('ó', 'o').replace('é', 'e').replace('í', 'i')}{''.join(random.choices('0123456789', k=2))}.edu",
                contact_phone=fake.phone_number(),
                timezone="Europe/Madrid",
                is_active=True
            )
            db.add(school)
            db.flush()  # Get school ID
            
            print(f"\n✓ Created school: {school.name} (ID: {school.id})")
            
            # Create students for this school
            students_created = 0
            for j in range(students_per_school):
                grade = random.choice(grades)
                section = random.choice(sections)
                class_name = f"{grade}-{section}"
                
                # Generate student ID (school code + sequential number)
                student_code = f"{school.id:03d}{j+1:05d}"
                
                student = Student(
                    student_id=student_code,
                    name=fake.name(),
                    class_name=class_name,
                    parent_email=fake.email(),
                    school_id=school.id,
                    is_active=True
                )
                db.add(student)
                students_created += 1
                
                # Commit every 50 students to avoid memory issues
                if students_created % 50 == 0:
                    db.commit()
                    print(f"  → Created {students_created}/{students_per_school} students...")
            
            db.commit()
            print(f"  ✓ Total students created for {school.name}: {students_created}")
        
        # Create additional users (directors and teachers)
        print("\n" + "=" * 70)
        print("Creating additional users...")
        print("=" * 70)
        
        # Get all schools
        schools = db.query(School).all()
        
        for school in schools[:5]:  # Create directors for first 5 schools
            director = User(
                username=f"director_{school.id}",
                email=f"director@{school.name.lower().replace(' ', '')}{''.join(random.choices('0123456789', k=2))}.edu",
                hashed_password=get_password_hash("director123"),
                full_name=f"Director {fake.last_name()}",
                role=UserRole.director,
                school_id=school.id,
                is_admin=False,
                is_active=True
            )
            db.add(director)
            print(f"✓ Created director for {school.name}")
        
        db.commit()
        
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        total_schools = db.query(School).count()
        total_students = db.query(Student).count()
        total_users = db.query(User).count()
        
        print(f"Total Schools: {total_schools}")
        print(f"Total Students: {total_students}")
        print(f"Total Users: {total_users}")
        print("=" * 70)
        print("✓ Production database populated successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    # Default: 10 schools with 85 students each = 850 students total
    num_schools = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    students_per_school = int(sys.argv[2]) if len(sys.argv) > 2 else 85
    
    create_schools_and_students(num_schools, students_per_school)
