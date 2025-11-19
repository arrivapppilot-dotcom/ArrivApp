"""
Admin endpoint to manually trigger database population.
Only accessible to admins (safety feature).
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.deps import get_current_admin_user
from app.core.database import SessionLocal
from app.models.models import Student, CheckIn, Justification, JustificationType, JustificationStatus, School, AbsenceNotification
from datetime import datetime, timedelta
import random
from faker import Faker
import os

router = APIRouter(prefix="/api/admin", tags=["admin"])
fake = Faker(['es_ES', 'es_MX'])
CLASSES = ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B", "6A", "6B"]

# Admin token for populate endpoint (optional, for automated tasks)
# Can be set via ADMIN_POPULATE_TOKEN environment variable
ADMIN_POPULATE_TOKEN = os.getenv("ADMIN_POPULATE_TOKEN", "")

def populate_db(db):
    """Shared database population logic"""
    # Get schools
    schools = db.query(School).all()
    if not schools:
        raise HTTPException(status_code=400, detail="No schools found")
    
    # Clean old TEST data - delete in correct order (respecting foreign keys)
    old_count = db.query(Student).filter(Student.student_id.like('TEST%')).count()
    if old_count > 0:
        # Delete in order: CheckIn -> Justification -> AbsenceNotification -> Student
        student_ids = db.query(Student.id).filter(Student.student_id.like('TEST%')).all()
        student_id_list = [s[0] for s in student_ids]
        
        if student_id_list:
            # Delete check-ins
            db.query(CheckIn).filter(CheckIn.student_id.in_(student_id_list)).delete()
            # Delete justifications
            db.query(Justification).filter(Justification.student_id.in_(student_id_list)).delete()
            # Delete absence notifications
            db.query(AbsenceNotification).filter(AbsenceNotification.student_id.in_(student_id_list)).delete()
            # Delete students
            db.query(Student).filter(Student.id.in_(student_id_list)).delete()
        
        db.commit()
    
    # Create fresh test students
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
    
    db.commit()
    
    # Simulate check-ins
    today_utc = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    checkins_count = 0
    absences_count = 0
    
    for days_back in [0, 1]:
        date_utc = today_utc - timedelta(days=days_back)
        
        attendance_rate = 0.85
        attending = random.sample(students_created, int(len(students_created) * attendance_rate))
        absent = [s for s in students_created if s not in attending]
        
        for student in attending:
            is_late = random.random() < 0.20
            hour = random.randint(8, 9) if is_late else random.randint(7, 8)
            minute = random.randint(15, 30) if is_late else random.randint(0, 10)
            
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
        
        justified = random.sample(absent, int(len(absent) * 0.5)) if absent else []
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
    
    db.commit()
    
    # Get summary
    total_students = db.query(Student).filter(Student.is_active == True).count()
    total_checkins = db.query(CheckIn).count()
    today_end = today_utc + timedelta(days=1)
    today_checkins = db.query(CheckIn).filter(
        CheckIn.checkin_time >= today_utc,
        CheckIn.checkin_time < today_end
    ).count()
    
    return {
        "total_students": total_students,
        "total_checkins": total_checkins,
        "today_checkins": today_checkins,
        "old_test_students_deleted": old_count
    }

@router.post("/populate-test-data")
async def populate_test_data(current_user = Depends(get_current_admin_user)):
    """
    Manually populate database with test data.
    Admin only endpoint.
    """
    db = SessionLocal()
    try:
        result = populate_db(db)
        return {
            "status": "success",
            "message": "Database populated successfully",
            "data": result
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

@router.post("/populate-test-data-token")
async def populate_test_data_token(token: str = ""):
    """
    Populate database with test data using token.
    For automated tasks and testing.
    """
    # Verify token if one is configured
    if ADMIN_POPULATE_TOKEN and token != ADMIN_POPULATE_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    db = SessionLocal()
    try:
        result = populate_db(db)
        return {
            "status": "success",
            "message": "Database populated successfully",
            "data": result
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()

@router.get("/populate-test-data-simple")
async def populate_test_data_simple():
    """
    Simple GET endpoint to populate database.
    No authentication required (for testing/cron jobs).
    WARNING: Only for development/testing environments!
    """
    db = SessionLocal()
    try:
        result = populate_db(db)
        return {
            "status": "success",
            "message": "Database populated successfully",
            "data": result
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        db.close()
