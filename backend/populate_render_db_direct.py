#!/usr/bin/env python3
"""
Populate Render Postgres database with test data.
This connects to the remote Render database using DATABASE_URL environment variable.

Usage:
    export DATABASE_URL="postgresql://user:pass@host/db"
    python populate_render_db_direct.py
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Get DATABASE_URL from environment (Render sets this automatically)
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("❌ DATABASE_URL not set. Cannot connect to Render database.")
    print("   Set it as: export DATABASE_URL='postgresql://...'")
    sys.exit(1)

# Create engine directly with Render URL
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.models import Base, School, Student, CheckIn, Justification, JustificationType, JustificationStatus
from faker import Faker

print(f"📊 Using database: {db_url[:40]}...")

# Create engine for Render database
engine = create_engine(db_url, echo=False)
SessionLocal = sessionmaker(bind=engine)

# Ensure tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()
fake = Faker(['es_ES', 'es_MX'])
CLASSES = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B", "6A", "6B"]

print("\n" + "="*70)
print("🚀 Populating Render Database")
print("="*70 + "\n")

# Check if schools exist
schools = db.query(School).all()
if not schools:
    print("❌ No schools found in Render database!")
    print("   Please ensure schools are created first.")
    db.close()
    sys.exit(1)

print(f"✅ Found {len(schools)} schools\n")

# Clean old TEST data
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
    print(f"   ✅ Deleted {old_count} old TEST students\n")

# Create fresh test students
print("📚 Creating test students...")
students_created = []
for school in schools:
    for i in range(15):
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

# Simulate check-ins
print("🎯 Simulating check-ins and absences...")
today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

checkins_count = 0
absences_count = 0
late_count = 0

for days_back in [0, 1]:
    date_utc = today_utc - timedelta(days=days_back)
    date_str = date_utc.strftime("%Y-%m-%d")
    
    attendance_rate = 0.85
    attending = random.sample(students_created, int(len(students_created) * attendance_rate))
    absent = [s for s in students_created if s not in attending]
    
    for student in attending:
        existing = db.query(CheckIn).filter(
            CheckIn.student_id == student.id,
            CheckIn.checkin_time >= date_utc,
            CheckIn.checkin_time < date_utc + timedelta(days=1)
        ).first()
        
        if existing:
            continue
        
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
    print(f"   📅 {date_str}: {len(attending)} present (late: {sum(1 for s in attending if db.query(CheckIn).filter(CheckIn.student_id==s.id, CheckIn.is_late==True).first())}), {len(absent)} absent ({len(justified)} justified)")

db.commit()
print(f"   ✨ Total: {checkins_count} check-ins, {absences_count} absences\n")

# Verify
print("✅ Verifying data...")
total_students = db.query(Student).filter(Student.is_active == True).count()
total_checkins = db.query(CheckIn).count()
total_justifications = db.query(Justification).count()

today_end = today_utc + timedelta(days=1)
today_checkins = db.query(CheckIn).filter(
    CheckIn.checkin_time >= today_utc,
    CheckIn.checkin_time < today_end
).count()

print(f"   Total active students: {total_students}")
print(f"   Total check-ins: {total_checkins}")
print(f"   Today's check-ins: {today_checkins}")
print(f"   Total justifications: {total_justifications}\n")

db.close()

print("=" * 70)
print("✅ Render database populated successfully!")
print("=" * 70)
print("\n💡 Refresh dashboard to see new test data\n")
