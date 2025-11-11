"""
Add 5 more schools with 30 students each for stress testing
"""
from faker import Faker
from app.core.database import SessionLocal
from app.models.models import School, Student
from datetime import datetime

fake = Faker(['es_ES', 'es_MX'])

def create_schools_and_students():
    db = SessionLocal()
    
    # Define 5 new schools
    new_schools = [
        {
            "name": "Colegio Internacional Madrid",
            "address": "Calle Velázquez 89, Madrid",
            "contact_email": "admin@cimadrid.edu",
            "timezone": "Europe/Madrid"
        },
        {
            "name": "Escuela Tecnológica Avanzada",
            "address": "Avenida Tecnología 234, Madrid",
            "contact_email": "info@tecavanzada.edu",
            "timezone": "Europe/Madrid"
        },
        {
            "name": "Instituto Bilingüe Central",
            "address": "Plaza Central 15, Madrid",
            "contact_email": "contacto@bilinguecentral.edu",
            "timezone": "Europe/Madrid"
        },
        {
            "name": "Colegio Arte y Ciencia",
            "address": "Calle Arte 78, Madrid",
            "contact_email": "admin@arteciencia.edu",
            "timezone": "Europe/Madrid"
        },
        {
            "name": "Academia Superior Innovación",
            "address": "Paseo Innovación 456, Madrid",
            "contact_email": "info@academiasuper.edu",
            "timezone": "Europe/Madrid"
        }
    ]
    
    print("=" * 70)
    print("ADDING 5 NEW SCHOOLS WITH 150 STUDENTS")
    print("=" * 70)
    
    created_schools = []
    total_students = 0
    
    # Classes from 1st to 12th grade with sections A, B, C
    classes = [f"{grade}{section}" for grade in range(1, 13) for section in ['A', 'B', 'C']]
    
    # Starting student ID - find highest numeric ID
    from app.models.models import Student as StudentModel
    all_students = db.query(StudentModel).all()
    max_numeric_id = 40000  # Default starting point
    
    for s in all_students:
        try:
            numeric_id = int(s.student_id)
            if numeric_id > max_numeric_id:
                max_numeric_id = numeric_id
        except ValueError:
            # Skip non-numeric IDs
            continue
    
    student_id_counter = max_numeric_id + 1
    
    for school_data in new_schools:
        # Create school
        school = School(**school_data)
        db.add(school)
        db.flush()  # Get the school ID
        
        print(f"\n✓ Created school: {school.name} (ID: {school.id})")
        created_schools.append(school)
        
        # Create 30 students for this school
        print(f"  Creating 30 students...")
        for i in range(30):
            # Generate Spanish name
            first_name = fake.first_name()
            last_name = f"{fake.last_name()} {fake.last_name()}"
            name = f"{first_name} {last_name}"
            
            # Generate email (remove spaces)
            email_name = f"{first_name.lower()}.{last_name.split()[0].lower()}".replace(' ', '')
            parent_email = f"{email_name}.parent@example.com"
            
            # Assign random class
            import random
            class_name = random.choice(classes)
            
            # Create student
            student = Student(
                student_id=str(student_id_counter),
                name=name,
                class_name=class_name,
                parent_email=parent_email,
                school_id=school.id,
                qr_code_path=f"QR_{student_id_counter}.png",
                is_active=True
            )
            
            db.add(student)
            student_id_counter += 1
            total_students += 1
        
        print(f"  ✓ Added 30 students to {school.name}")
    
    # Commit all changes
    db.commit()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Schools created: {len(created_schools)}")
    print(f"Total students added: {total_students}")
    
    print("\nNew schools:")
    for school in created_schools:
        student_count = db.query(Student).filter(Student.school_id == school.id).count()
        print(f"  • {school.name}: {student_count} students")
    
    # Get overall totals
    total_schools = db.query(School).filter(School.is_active == True).count()
    total_all_students = db.query(Student).filter(Student.is_active == True).count()
    
    print(f"\n📊 OVERALL TOTALS:")
    print(f"Total active schools: {total_schools}")
    print(f"Total active students: {total_all_students}")
    
    db.close()
    print("\n✅ Done!")


if __name__ == "__main__":
    create_schools_and_students()
