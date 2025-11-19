#!/usr/bin/env python3
"""
Simple populate script - creates test data with proper UTC timestamps.
No timezone issues, just straightforward UTC handling.

Populates whichever database is configured in DATABASE_URL environment variable.
On Render: Uses Render Postgres database
Locally: Uses local database (SQLite or Postgres)

Usage:
    python populate_simple.py
"""
import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Use whatever database is configured (Render or local)
from app.core.database import SessionLocal
from app.models.models import (
    School, Student, CheckIn, Justification,
    JustificationType, JustificationStatus, User
)
from faker import Faker

fake = Faker(['es_ES', 'es_MX'])

CLASSES = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B", "6A", "6B"]

def clear_old_data(db):
    """Delete old TEST data"""
    print("🧹 Cleaning old TEST data...")
    old_count = db.query(Student).filter(Student.student_id.like('TEST%')).count()
    if old_count > 0:
        db.query(CheckIn).filter(
            CheckIn.student_id.in_(
                db.query(Student.id).filter(Student.student_id.like('TEST%'))
            )
        ).delete()
        db.query(Student).filter(Student.student_id.like('TEST%')).delete()
        db.commit()
        print(f"   ✅ Deleted {old_count} old TEST students and their check-ins\n")
    return old_count

def create_test_students(db):
    """Create fresh test students for today"""
    print("📚 Creating test students...")
    
    schools = db.query(School).all()
    if not schools:
        print("   ❌ No schools found!")
        return []
    
    students_created = []
    for school in schools:
        for i in range(15):  # 15 students per school
            student = Student(
                student_id=f"TEST{datetime.utcnow().strftime('%Y%m%d')}{school.id}{i:04d}",
                name=fake.name(),
                parent_email=fake.email(),
                class_name=random.choice(CLASSES),
                school_id=school.id,
                is_active=True
            )
            db.add(student)
            students_created.append(student)
        print(f"   ✅ Created 15 students for {school.name}")
    
    db.commit()
    print(f"   📊 Total: {len(students_created)} students\n")
    return students_created

def simulate_checkins(db, students):
    """Simulate check-ins, late arrivals, and absences for today and yesterday"""
    print("🎯 Simulating check-ins and absences...")
    
    # Use UTC for all timestamps to match database storage
    today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    checkins_count = 0
    absences_count = 0
    late_count = 0
    
    for days_back in [0, 1]:  # Today and yesterday
        date_utc = today_utc - timedelta(days=days_back)
        date_str = date_utc.strftime("%Y-%m-%d")
        
        # 85% attendance rate
        attendance_rate = 0.85
        attending = random.sample(students, int(len(students) * attendance_rate))
        absent = [s for s in students if s not in attending]
        
        # Create check-ins for attending students
        for student in attending:
            # Check for duplicates
            existing = db.query(CheckIn).filter(
                CheckIn.student_id == student.id,
                CheckIn.checkin_time >= date_utc,
                CheckIn.checkin_time < date_utc + timedelta(days=1)
            ).first()
            
            if existing:
                continue
            
            # 20% late
            is_late = random.random() < 0.20
            if is_late:
                late_count += 1
                hour = random.randint(8, 9)
                minute = random.randint(15, 30)
            else:
                hour = random.randint(7, 8)
                minute = random.randint(0, 10)
            
            checkin_time = date_utc.replace(
                hour=hour,
                minute=minute,
                second=random.randint(0, 59)
            )
            
            # 80% also checkout
            checkout_time = None
            if random.random() < 0.8:
                checkout_hour = random.randint(14, 16)
                checkout_time = date_utc.replace(
                    hour=checkout_hour,
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
            
            checkin = CheckIn(
                student_id=student.id,
                checkin_time=checkin_time,
                checkout_time=checkout_time,
                is_late=is_late
            )
            db.add(checkin)
            checkins_count += 1
        
        # Create absence justifications for 50% of absent students
        justified = random.sample(absent, int(len(absent) * 0.5))
        for student in justified:
            justification = Justification(
                student_id=student.id,
                date=date_utc.date(),
                justification_type=JustificationType.absence,
                reason=random.choice([
                    "Mi hijo/a está enfermo/a",
                    "Cita médica",
                    "Viaje familiar",
                    "Problema de transporte"
                ]),
                submitted_by=student.parent_email,
                submitted_at=date_utc.replace(hour=6, minute=0),
                status=random.choice([JustificationStatus.pending, JustificationStatus.approved])
            )
            db.add(justification)
        
        absences_count += len(absent)
        
        print(f"   📅 {date_str}: {checkins_count} check-ins (late: {late_count}), {len(absent)} absences ({len(justified)} justified)")
    
    db.commit()
    print(f"   ✨ Total: {checkins_count} check-ins, {absences_count} absences\n")
    return checkins_count, absences_count

def verify_data(db):
    """Verify data was created correctly"""
    print("✅ Verifying data...")
    
    total_students = db.query(Student).filter(Student.is_active == True).count()
    total_checkins = db.query(CheckIn).count()
    total_justifications = db.query(Justification).count()
    
    # Check today's data specifically
    today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_utc + timedelta(days=1)
    
    today_checkins = db.query(CheckIn).filter(
        CheckIn.checkin_time >= today_utc,
        CheckIn.checkin_time < today_end
    ).count()
    
    print(f"   Total active students: {total_students}")
    print(f"   Total check-ins: {total_checkins}")
    print(f"   Today's check-ins: {today_checkins}")
    print(f"   Total justifications: {total_justifications}\n")
    
    return total_students, today_checkins

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Simple Populate Script")
    print("=" * 70 + "\n")
    
    # Show which database is being used
    db_url = os.getenv("DATABASE_URL", "")
    if "render" in db_url.lower() or "postgres" in db_url.lower():
        print("📊 Database: POSTGRES (Render or remote)")
    else:
        print("📊 Database: LOCAL (SQLite)")
    print()
    
    try:
        db = SessionLocal()
        
        # Step 1: Clear old data
        clear_old_data(db)
        
        # Step 2: Create test students
        students = create_test_students(db)
        
        # Step 3: Simulate check-ins, late arrivals, absences
        checkins, absences = simulate_checkins(db, students)
        
        # Step 4: Verify
        total_students, today_checkins = verify_data(db)
        
        db.close()
        
        print("=" * 70)
        print("✅ Population complete!")
        print("=" * 70)
        print("\n📊 Summary:")
        print(f"   Students: {total_students}")
        print(f"   Today's check-ins: {today_checkins}")
        print(f"   Total check-ins: {db.query(CheckIn).count() if db else 'N/A'}")
        print("\n💡 Hard refresh dashboard: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
