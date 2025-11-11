from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, date, time
from typing import List, Optional
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_school_user
from app.models.models import Student, CheckIn, User, UserRole
from app.models.schemas import (
    CheckInCreate, CheckIn as CheckInSchema, 
    DashboardData, DashboardStats, CheckInLog, LateStudent, AbsentStudent
)
from app.services.email_service import send_checkin_notification, send_email
from app.core.config import get_settings

router = APIRouter(prefix="/api/checkin", tags=["Check-in"])
settings = get_settings()


@router.post("/scan", status_code=status.HTTP_201_CREATED)
async def checkin_scan(
    student_id: str = Query(..., description="Student ID from QR code"),
    db: Session = Depends(get_db)
):
    """Handle QR code scan for both check-in and check-out with security validations."""
    # Find student by student_id
    student = db.query(Student).filter(
        Student.student_id == student_id,
        Student.is_active == True
    ).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if already checked in today
    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)
    
    existing_checkin = db.query(CheckIn).filter(
        CheckIn.student_id == student.id,
        CheckIn.checkin_time >= today_start,
        CheckIn.checkin_time <= today_end
    ).first()
    
    now = datetime.now()
    
    # CASE 1: Student already checked in today (no checkout yet)
    if existing_checkin and not existing_checkin.checkout_time:
        # Calculate time difference since check-in
        time_diff = (now - existing_checkin.checkin_time).total_seconds() / 60  # in minutes
        
        # SECURITY: Prevent duplicate check-in within 10 minutes (likely accidental double scan)
        if time_diff < 10:
            return {
                "error": "duplicate_scan",
                "message": f"⚠️ {student.name} ya ha registrado entrada hace {int(time_diff)} minutos",
                "student_name": student.name,
                "checkin_time": existing_checkin.checkin_time,
                "minutes_ago": int(time_diff)
            }
        
        # SECURITY: Minimum stay time of 30 minutes before checkout
        # (prevents accidental checkout right after check-in)
        if time_diff < 30:
            return {
                "error": "too_early_checkout",
                "message": f"⏱️ Debe esperar al menos 30 minutos antes de registrar salida\nEntrada: {existing_checkin.checkin_time.strftime('%H:%M')}h",
                "student_name": student.name,
                "checkin_time": existing_checkin.checkin_time,
                "minutes_since_checkin": int(time_diff),
                "minutes_remaining": 30 - int(time_diff)
            }
        
        # VALID CHECK-OUT: Process check-out
        existing_checkin.checkout_time = now
        db.commit()
        
        # Detect early dismissal (before 14:00 / 2:00 PM)
        is_early_dismissal = now.hour < 14
        
        # Send check-out email notification
        try:
            checkout_time_str = now.strftime("%H:%M")
            checkin_time_str = existing_checkin.checkin_time.strftime("%H:%M")
            duration_hours = int(time_diff // 60)
            duration_mins = int(time_diff % 60)
            
            if is_early_dismissal:
                subject = f"⚠️ ArrivApp: {student.name} ha salido TEMPRANO del colegio"
                body = f"""¡Hola!

⚠️ ALERTA DE SALIDA TEMPRANA

Te informamos que {student.name} ({student.class_name}) ha registrado su salida del colegio antes del horario habitual.

📍 Resumen de hoy:
• Hora de entrada: {checkin_time_str}h
• Hora de salida: {checkout_time_str}h ⚠️ (Salida temprana)
• Tiempo en el colegio: {duration_hours}h {duration_mins}min

Si esta salida temprana no estaba prevista, por favor contacta con el colegio inmediatamente.

Gracias por participar en el programa piloto de ArrivApp.

---
Este es un mensaje automático. Por favor no responder.
"""
            else:
                subject = f"✅ ArrivApp: {student.name} ha salido del colegio"
                body = f"""¡Hola!

Te informamos que {student.name} ({student.class_name}) ha registrado su salida del colegio.

📍 Resumen de hoy:
• Hora de entrada: {checkin_time_str}h
• Hora de salida: {checkout_time_str}h
• Tiempo en el colegio: {duration_hours}h {duration_mins}min

Gracias por participar en el programa piloto de ArrivApp.

---
Este es un mensaje automático. Por favor no responder.
"""
            await send_email(student.parent_email, subject, body)
        except Exception as e:
            print(f"Error sending checkout email: {e}")
        
        return {
            "message": f"¡Hasta luego, {student.name}!" + (" ⚠️ Salida temprana" if is_early_dismissal else ""),
            "action": "checkout",
            "student_name": student.name,
            "class": student.class_name,
            "checkin_time": existing_checkin.checkin_time,
            "checkout_time": now,
            "duration_minutes": int(time_diff),
            "early_dismissal": is_early_dismissal
        }
    
    # CASE 2: Student already completed both check-in and check-out today
    if existing_checkin and existing_checkin.checkout_time:
        return {
            "error": "already_completed",
            "message": f"✅ {student.name} ya completó entrada y salida hoy\nEntrada: {existing_checkin.checkin_time.strftime('%H:%M')}h\nSalida: {existing_checkin.checkout_time.strftime('%H:%M')}h",
            "already_completed": True,
            "student_name": student.name,
            "checkin_time": existing_checkin.checkin_time,
            "checkout_time": existing_checkin.checkout_time
        }
    
    # CASE 3: First scan of the day - Process CHECK-IN
    is_late = (now.hour > settings.LATE_THRESHOLD_HOUR or 
               (now.hour == settings.LATE_THRESHOLD_HOUR and now.minute > settings.LATE_THRESHOLD_MINUTE))
    
    db_checkin = CheckIn(
        student_id=student.id,
        checkin_time=now,
        is_late=is_late,
    )
    db.add(db_checkin)
    db.commit()
    db.refresh(db_checkin)
    
    # Send check-in email notification
    try:
        email_sent = await send_checkin_notification(
            student.parent_email,
            student.name,
            student.class_name,
            now,
            is_late=is_late
        )
        db_checkin.email_sent = email_sent
        db.commit()
    except Exception as e:
        print(f"Error sending email: {e}")
    
    return {
        "message": f"¡Bienvenido/a, {student.name}!",
        "action": "checkin",
        "student_name": student.name,
        "class": student.class_name,
        "checkin_time": now,
        "is_late": is_late,
        "email_sent": db_checkin.email_sent
    }


@router.get("/classes", response_model=List[str])
async def get_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_school_user)
):
    """Get list of unique class names (filtered by school for non-admins)."""
    query = db.query(Student.class_name).filter(Student.is_active == True).distinct()
    
    if current_user.role != UserRole.admin:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be associated with a school"
            )
        query = query.filter(Student.school_id == current_user.school_id)
    
    classes = query.order_by(Student.class_name).all()
    return [class_name[0] for class_name in classes]


@router.get("/dashboard", response_model=DashboardData)
async def get_dashboard_data(
    date_filter: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    class_filter: Optional[str] = Query(None, description="Filter by class name"),
    school_id: Optional[int] = Query(None, description="Filter by school ID (admin only)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_school_user)
):
    """Get dashboard data for a specific date (filtered by school and optionally by class)."""
    # Parse date
    if date_filter:
        try:
            target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        target_date = date.today()
    
    date_start = datetime.combine(target_date, time.min)
    date_end = datetime.combine(target_date, time.max)
    
    # Get all active students (filtered by school for non-admins)
    students_query = db.query(Student).options(joinedload(Student.school)).filter(Student.is_active == True)
    if current_user.role != UserRole.admin:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be associated with a school"
            )
        students_query = students_query.filter(Student.school_id == current_user.school_id)
    else:
        # Admin can filter by specific school if provided
        if school_id:
            students_query = students_query.filter(Student.school_id == school_id)
    
    # Apply class filter if provided
    if class_filter:
        students_query = students_query.filter(Student.class_name == class_filter)
    
    all_students = students_query.all()
    
    # Get check-ins for the date (filtered by school)
    checkins_query = db.query(CheckIn).options(joinedload(CheckIn.student).joinedload(Student.school)).filter(
        CheckIn.checkin_time >= date_start,
        CheckIn.checkin_time <= date_end
    ).join(Student)
    
    if current_user.role != UserRole.admin:
        checkins_query = checkins_query.filter(Student.school_id == current_user.school_id)
    else:
        # Admin can filter by specific school if provided
        if school_id:
            checkins_query = checkins_query.filter(Student.school_id == school_id)
    
    # Apply class filter to check-ins if provided
    if class_filter:
        checkins_query = checkins_query.filter(Student.class_name == class_filter)
    
    checkins = checkins_query.all()
    
    # Calculate stats
    present_student_ids = {checkin.student_id for checkin in checkins}
    late_checkins = [checkin for checkin in checkins if checkin.is_late]
    
    stats = DashboardStats(
        total_present=len(present_student_ids),
        total_absent=len(all_students) - len(present_student_ids),
        total_late=len(late_checkins),
        date=target_date.strftime("%d/%m/%Y")
    )
    
    # Format check-in logs
    checkin_logs = [
        CheckInLog(
            checkin_time=checkin.checkin_time.strftime("%d/%m/%Y %H:%M:%S"),
            student_name=checkin.student.name,
            school_name=checkin.student.school.name,
            checkout_time=checkin.checkout_time.strftime("%d/%m/%Y %H:%M:%S") if checkin.checkout_time else None
        )
        for checkin in checkins
    ]
    
    # Late students
    late_students = [
        LateStudent(
            name=checkin.student.name,
            time=checkin.checkin_time.strftime("%d/%m/%Y %H:%M:%S"),
            school_name=checkin.student.school.name,
            email_sent=checkin.email_sent
        )
        for checkin in late_checkins
    ]
    
    # Absent students - check if 9:10 AM email has been sent
    current_time = datetime.now().time()
    absent_email_time = settings.CHECK_ABSENT_TIME.split(':')
    absent_check_hour = int(absent_email_time[0])
    absent_check_minute = int(absent_email_time[1])
    
    # Email is sent after 9:10 AM
    email_has_been_sent = (current_time.hour > absent_check_hour or 
                          (current_time.hour == absent_check_hour and current_time.minute >= absent_check_minute))
    
    absent_students = [
        AbsentStudent(
            id=student.id,
            name=student.name,
            class_name=student.class_name,
            school_name=student.school.name,
            email_sent=email_has_been_sent  # True if current time >= 9:10 AM
        )
        for student in all_students
        if student.id not in present_student_ids
    ]
    
    return DashboardData(
        stats=stats,
        checkins=checkin_logs,
        late_students=late_students,
        absent_students=absent_students
    )


@router.get("/", response_model=List[CheckInSchema])
async def get_checkins(
    skip: int = 0,
    limit: int = 100,
    date_filter: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get check-in records."""
    query = db.query(CheckIn)
    
    if date_filter:
        try:
            target_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            date_start = datetime.combine(target_date, time.min)
            date_end = datetime.combine(target_date, time.max)
            query = query.filter(
                CheckIn.checkin_time >= date_start,
                CheckIn.checkin_time <= date_end
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")
    
    checkins = query.order_by(CheckIn.checkin_time.desc()).offset(skip).limit(limit).all()
    return checkins
