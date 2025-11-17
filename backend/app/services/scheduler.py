"""
Scheduled tasks for ArrivApp
Handles daily absent student reports and other scheduled operations
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date, time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, Integer
from app.core.database import SessionLocal
from app.models.models import (
    Student, CheckIn, User, UserRole, 
    StudentDietaryNeeds, KitchenAttendance, AbsenceNotification, School
)
from app.services.email_service import send_email
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Create scheduler instance
scheduler = AsyncIOScheduler()


async def check_absent_students():
    """Check for students who haven't checked in and send notifications to parents, schools, and admins."""
    logger.info("Running absent students check...")
    
    db = SessionLocal()
    try:
        # Get today's date range
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)
        now = datetime.now()
        
        # Get all active students with their schools
        all_students = db.query(Student).options(
            joinedload(Student.school)
        ).filter(Student.is_active == True).all()
        
        # Get students who checked in today
        checked_in_today = db.query(CheckIn).filter(
            CheckIn.checkin_time >= today_start,
            CheckIn.checkin_time <= today_end
        ).all()
        
        checked_in_ids = {checkin.student_id for checkin in checked_in_today}
        
        # Group absent students by school
        absent_by_school = {}
        for student in all_students:
            if student.id not in checked_in_ids:
                school_id = student.school_id
                if school_id not in absent_by_school:
                    absent_by_school[school_id] = {
                        'school': student.school,
                        'students': []
                    }
                absent_by_school[school_id]['students'].append(student)
        
        if not absent_by_school:
            logger.info("✅ All students have checked in today!")
            return
        
        # Get all admin users
        admins = db.query(User).filter(User.role == UserRole.admin).all()
        
        # Process each school's absent students
        for school_id, data in absent_by_school.items():
            school = data['school']
            absent_students = data['students']
            
            logger.info(f"📋 School '{school.name}': {len(absent_students)} absent students")
            
            # 1. Send email to each parent
            for student in absent_students:
                subject = f"⚠️ ArrivApp: {student.name} no ha registrado su entrada"
                body = f"""Hola,

Te informamos que {student.name} ({student.class_name}) NO ha registrado su entrada en el colegio hoy.

Fecha: {now.strftime('%d/%m/%Y')}
Hora del reporte: {now.strftime('%H:%M')}

Si tu hijo/a está en el colegio, por favor contacta con la administración.
Si está ausente, te agradeceríamos que informes al colegio.

Colegio: {school.name}
{f'Contacto: {school.contact_email}' if school.contact_email else ''}

---
Este es un mensaje automático de ArrivApp.
"""
                try:
                    await send_email(student.parent_email, subject, body)
                    logger.info(f"  ✉️ Parent notification sent: {student.parent_email}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to send to parent {student.parent_email}: {e}")
            
            # 2. Send email to school contact
            if school.contact_email:
                subject = f"📋 ArrivApp - Alumnos Ausentes ({school.name})"
                body = f"""Hola,

Reporte de ausencias para {school.name}:

Fecha: {now.strftime('%d/%m/%Y')}
Hora del reporte: {now.strftime('%H:%M')}

Alumnos que NO han registrado entrada:

"""
                for student in absent_students:
                    body += f"• {student.name} ({student.class_name}) - Email padre: {student.parent_email}\n"
                
                body += f"\n\nTotal: {len(absent_students)} alumnos ausentes\n\n"
                body += "Por favor, verifica estas ausencias y contacta a los padres si es necesario.\n\n"
                body += "---\nArrivApp Sistema de Control"
                
                try:
                    await send_email(school.contact_email, subject, body)
                    logger.info(f"  ✉️ School notification sent: {school.contact_email}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to send school email: {e}")
            
            # 3. Send email to all admins
            for admin in admins:
                subject = f"📋 ArrivApp Admin - Ausencias en {school.name}"
                body = f"""Hola Admin,

Reporte automático de ausencias:

Colegio: {school.name}
Fecha: {now.strftime('%d/%m/%Y')}
Hora: {now.strftime('%H:%M')}

Alumnos ausentes ({len(absent_students)}):

"""
                for student in absent_students:
                    body += f"• {student.name} ({student.class_name})\n"
                    body += f"  Padre: {student.parent_email}\n"
                    body += f"  ID Alumno: {student.student_id}\n\n"
                
                body += f"\nTotal: {len(absent_students)} ausentes en {school.name}\n"
                body += "\n---\nArrivApp Admin Panel"
                
                try:
                    await send_email(admin.email, subject, body)
                    logger.info(f"  ✉️ Admin notification sent: {admin.email}")
                except Exception as e:
                    logger.error(f"  ❌ Failed to send admin email: {e}")
        
        logger.info("✅ Absent notification process completed")
            
    except Exception as e:
        logger.error(f"Error checking absent students: {e}")
    finally:
        db.close()


async def capture_kitchen_attendance():
    """Capture kitchen attendance snapshot at 10 AM - for meal planning."""
    logger.info("Capturing kitchen attendance snapshot...")
    
    db = SessionLocal()
    try:
        today = date.today()
        snapshot_datetime = datetime.combine(today, time(hour=10, minute=0))
        
        # Get all schools
        schools = db.query(School).filter(School.is_active == True).all()
        
        for school in schools:
            # Get all active students for this school
            all_students = db.query(Student).filter(
                and_(
                    Student.is_active == True,
                    Student.school_id == school.id
                )
            ).all()
            
            # Group by class
            classes = {}
            for student in all_students:
                if student.class_name not in classes:
                    classes[student.class_name] = []
                classes[student.class_name].append(student)
            
            # Generate snapshot for each class
            for class_name, students in classes.items():
                total = len(students)
                student_ids = [s.id for s in students]
                
                # Check who checked in today
                checkins_today = db.query(CheckIn).filter(
                    and_(
                        CheckIn.student_id.in_(student_ids),
                        func.date(CheckIn.checkin_time) == today
                    )
                ).all()
                
                present = len(checkins_today)
                
                # Check who has absence notifications (absent at 9:01 AM)
                absences_today = db.query(AbsenceNotification).filter(
                    and_(
                        AbsenceNotification.student_id.in_(student_ids),
                        func.date(AbsenceNotification.notification_date) == today
                    )
                ).all()
                
                absent = len(absences_today)
                will_arrive = total - present - absent
                
                # Count dietary needs
                dietary_counts = db.query(
                    func.sum(func.cast(StudentDietaryNeeds.has_allergies, Integer)).label('allergies'),
                    func.sum(func.cast(StudentDietaryNeeds.has_special_diet, Integer)).label('special_diet')
                ).filter(
                    StudentDietaryNeeds.student_id.in_(student_ids)
                ).first()
                
                with_allergies = int(dietary_counts.allergies) if dietary_counts.allergies else 0
                with_special_diet = int(dietary_counts.special_diet) if dietary_counts.special_diet else 0
                
                # Create snapshot
                snapshot = KitchenAttendance(
                    school_id=school.id,
                    snapshot_date=snapshot_datetime,
                    class_name=class_name,
                    total_students=total,
                    present=present,
                    absent=absent,
                    will_arrive_later=will_arrive,
                    with_allergies=with_allergies,
                    with_special_diet=with_special_diet
                )
                
                db.add(snapshot)
                logger.info(f"Created kitchen snapshot for {school.name} - {class_name}: {present}/{total} present")
            
        db.commit()
        logger.info("✅ Kitchen attendance snapshot captured")
        
    except Exception as e:
        logger.error(f"Error capturing kitchen attendance: {e}")
        db.rollback()
    finally:
        db.close()


def start_scheduler():
    """Start the scheduler with all scheduled tasks."""
    # Parse the CHECK_ABSENT_TIME setting (format: "HH:MM")
    try:
        hour, minute = map(int, settings.CHECK_ABSENT_TIME.split(':'))
    except:
        hour, minute = 9, 10  # Default to 9:10 if parsing fails
    
    # Schedule absent check daily at specified time
    scheduler.add_job(
        check_absent_students,
        trigger=CronTrigger(hour=hour, minute=minute),
        id='check_absent_students',
        name='Daily absent students check',
        replace_existing=True
    )
    
    # Schedule kitchen attendance capture at 10 AM every day
    scheduler.add_job(
        capture_kitchen_attendance,
        trigger=CronTrigger(hour=10, minute=0),
        id='capture_kitchen_attendance',
        name='Daily kitchen attendance snapshot',
        replace_existing=True
    )
    
    logger.info(f"Scheduler started. Absent check will run daily at {hour:02d}:{minute:02d}")
    logger.info("Kitchen attendance snapshot will run daily at 10:00")
    scheduler.start()


def stop_scheduler():
    """Stop the scheduler."""
    scheduler.shutdown()
    logger.info("Scheduler stopped")


# For manual testing
async def run_absent_check_now():
    """Manually trigger absent students check (for testing)."""
    await check_absent_students()
