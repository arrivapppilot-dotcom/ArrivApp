from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, Integer, extract
from typing import Optional, List
from datetime import datetime, date, timedelta
from app.core.database import get_db
from app.models.models import CheckIn, Student, School, User, UserRole, AbsenceNotification, Justification, JustificationStatus, JustificationType
from app.core.deps import get_current_user
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT

router = APIRouter(prefix="/api/reports", tags=["Reports"])

# Internal helper function - does not use Query/Depends
def _get_attendance_history_internal(
    db: Session,
    current_user: User,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    school_id: Optional[int] = None,
    student_id: Optional[int] = None,
    class_name: Optional[str] = None,
):
    """Internal function to get attendance history"""
    
    # Build base query
    query = db.query(CheckIn).join(Student)
    
    # Role-based filtering
    if current_user.role in [UserRole.director, UserRole.teacher]:
        if not current_user.school_id:
            raise HTTPException(status_code=403, detail="User has no assigned school")
        query = query.filter(Student.school_id == current_user.school_id)
    elif current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Admin can filter by school
    if school_id and current_user.role == UserRole.admin:
        query = query.filter(Student.school_id == school_id)
    
    # Filter by class
    if class_name:
        query = query.filter(Student.class_name == class_name)
    
    # Filter by student
    if student_id:
        query = query.filter(CheckIn.student_id == student_id)
    
    # Filter by date range
    if start_date:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        query = query.filter(CheckIn.checkin_time >= start)
    
    if end_date:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        end = end.replace(hour=23, minute=59, second=59)
        query = query.filter(CheckIn.checkin_time <= end)
    
    # Execute query
    records = query.order_by(CheckIn.checkin_time.desc()).all()
    
    # Format response
    result = []
    for record in records:
        student = record.student
        result.append({
            "id": record.id,
            "student_id": student.id,
            "student_name": student.name,
            "class_name": student.class_name,
            "school_id": student.school_id,
            "school_name": student.school.name if student.school else None,
            "checkin_time": record.checkin_time.isoformat(),
            "checkout_time": record.checkout_time.isoformat() if record.checkout_time else None,
            "is_late": record.is_late,
            "email_sent": record.email_sent
        })
    
    return {"records": result, "total": len(result)}


@router.get("/attendance-history")
async def get_attendance_history(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    student_id: Optional[int] = Query(None),
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance history with filters"""
    return _get_attendance_history_internal(
        db=db,
        current_user=current_user,
        start_date=start_date,
        end_date=end_date,
        school_id=school_id,
        student_id=student_id,
        class_name=class_name
    )


@router.get("/attendance-with-absences")
async def get_attendance_with_absences(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance history including absent students with notification status"""
    
    # Parse dates - IMPORTANT: CheckIn times are stored in UTC
    if start_date:
        date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        start_datetime = date_obj.replace(hour=0, minute=0, second=0)
    else:
        start_datetime = datetime.utcnow().replace(hour=0, minute=0, second=0)
    
    if end_date:
        date_obj = datetime.strptime(end_date, "%Y-%m-%d")
        end_datetime = date_obj.replace(hour=23, minute=59, second=59)
    else:
        end_datetime = datetime.utcnow().replace(hour=23, minute=59, second=59)
    
    # Build student query for authorization
    student_query = db.query(Student)
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        if not current_user.school_id:
            raise HTTPException(status_code=403, detail="User has no assigned school")
        student_query = student_query.filter(Student.school_id == current_user.school_id)
    elif current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Admin can filter by school
    if school_id and current_user.role == UserRole.admin:
        student_query = student_query.filter(Student.school_id == school_id)
    
    # Filter by class
    if class_name:
        student_query = student_query.filter(Student.class_name == class_name)
    
    # Get all active students in scope
    all_students = student_query.filter(Student.is_active == True).all()
    
    # Get all checked-in students for the date range
    checkins = db.query(CheckIn).join(Student).filter(
        and_(
            CheckIn.checkin_time >= start_datetime,
            CheckIn.checkin_time <= end_datetime
        )
    )
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        checkins = checkins.filter(Student.school_id == current_user.school_id)
    elif school_id and current_user.role == UserRole.admin:
        checkins = checkins.filter(Student.school_id == school_id)
    
    # Filter by class
    if class_name:
        checkins = checkins.filter(Student.class_name == class_name)
    
    checkins = checkins.all()
    checkin_student_ids = set(c.student_id for c in checkins)
    
    # Format checked-in records
    result = []
    for record in checkins:
        student = record.student
        result.append({
            "id": record.id,
            "student_id": student.id,
            "student_name": student.name,
            "class_name": student.class_name,
            "school_id": student.school_id,
            "school_name": student.school.name if student.school else None,
            "checkin_time": record.checkin_time.isoformat(),
            "checkout_time": record.checkout_time.isoformat() if record.checkout_time else None,
            "is_late": record.is_late,
            "email_sent": record.email_sent,
            "is_absent": False
        })
    
    # Add absent students (those not in check-ins for the date)
    absent_students = [s for s in all_students if s.id not in checkin_student_ids]
    
    for student in absent_students:
        # Check if there's an absence notification for this student on this date
        absence_notif = db.query(AbsenceNotification).filter(
            and_(
                AbsenceNotification.student_id == student.id,
                AbsenceNotification.notification_date >= start_datetime,
                AbsenceNotification.notification_date <= end_datetime
            )
        ).first()
        
        result.append({
            "id": None,
            "student_id": student.id,
            "student_name": student.name,
            "class_name": student.class_name,
            "school_id": student.school_id,
            "school_name": student.school.name if student.school else None,
            "checkin_time": None,
            "checkout_time": None,
            "is_late": False,
            "email_sent": absence_notif.email_sent if absence_notif else False,
            "is_absent": True
        })
    
    return {"records": result, "total": len(result)}


@router.get("/statistics")
async def get_statistics(
    period: str = Query("weekly", regex="^(daily|weekly|monthly)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get attendance statistics for different periods"""
    
    # Determine date range - IMPORTANT: CheckIn times are stored in UTC
    if not start_date or not end_date:
        end = datetime.utcnow()  # Use UTC, not local time
        if period == "daily":
            start = end.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "weekly":
            start = end - timedelta(days=7)
        else:  # monthly
            start = end - timedelta(days=30)
    else:
        # Parse dates as UTC (CheckIn.checkin_time is stored in UTC)
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        # Treat as UTC dates - start at 00:00:00 UTC, end at 23:59:59 UTC
        end = end.replace(hour=23, minute=59, second=59)
    
    # Build query with role-based filtering
    query = db.query(CheckIn).join(Student)
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        if not current_user.school_id:
            raise HTTPException(status_code=403, detail="User has no assigned school")
        query = query.filter(Student.school_id == current_user.school_id)
    elif current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Admin can filter by school
    if school_id and current_user.role == UserRole.admin:
        query = query.filter(Student.school_id == school_id)
    
    # Filter by class
    if class_name:
        query = query.filter(Student.class_name == class_name)
    
    # Filter by date range
    query = query.filter(
        and_(
            CheckIn.checkin_time >= start,
            CheckIn.checkin_time <= end
        )
    )
    
    # Calculate statistics
    total_attendance = query.count()
    
    # DEBUG: Log query details
    print(f"[DEBUG QUERY] Start: {start} ({start.isoformat()})")
    print(f"[DEBUG QUERY] End: {end} ({end.isoformat()})")
    print(f"[DEBUG QUERY] Total attendance found: {total_attendance}")
    
    # Sample some CheckIn records to see what we have
    sample = db.query(CheckIn).limit(3).all()
    if sample:
        print(f"[DEBUG QUERY] Sample CheckIn times: {[c.checkin_time for c in sample]}")
    
    # Present students (checked in) - all records are present
    present = total_attendance
    
    # Late arrivals
    late = query.filter(CheckIn.is_late == True).count()
    
    # DEBUG: Log request context
    print(f"[DEBUG STATS] Period: {period}, Date: {start.date()}")
    print(f"[DEBUG STATS] Current user role: {current_user.role}, school_id: {current_user.school_id}")
    
    # Students who checked out
    checked_out = query.filter(CheckIn.checkout_time.isnot(None)).count()
    
    # Count approved justifications for absences in this period
    # We need to count justifications where:
    # 1. Type is "absence"
    # 2. Status is "approved"
    # 3. Date falls within our period
    # 4. Student is in the same school/class scope
    justified_query = db.query(Justification).filter(
        Justification.status == JustificationStatus.approved,
        Justification.justification_type == JustificationType.absence
    ).join(Student)
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        justified_query = justified_query.filter(Student.school_id == current_user.school_id)
    elif school_id and current_user.role == UserRole.admin:
        justified_query = justified_query.filter(Student.school_id == school_id)
    
    if class_name:
        justified_query = justified_query.filter(Student.class_name == class_name)
    
    # Filter by date range - Justification.date is a DateTime, so we need to convert it
    justified_query = justified_query.filter(
        and_(
            func.date(Justification.date) >= start.date(),
            func.date(Justification.date) <= end.date()
        )
    )
    
    justified = justified_query.count()
    
    # Get total students in scope
    student_query = db.query(Student)
    if current_user.role in [UserRole.director, UserRole.teacher]:
        student_query = student_query.filter(Student.school_id == current_user.school_id)
    elif school_id and current_user.role == UserRole.admin:
        student_query = student_query.filter(Student.school_id == school_id)
    
    # Filter by class
    if class_name:
        student_query = student_query.filter(Student.class_name == class_name)
    
    total_students = student_query.filter(Student.is_active == True).count()
    
    # DEBUG: Log computed statistics (after total_students is calculated)
    try:
        print(f"[DEBUG STATS] Total students: {total_students}")
        print(f"[DEBUG STATS] Total attendance: {total_attendance}")
        print(f"[DEBUG STATS] Present: {present}")
        print(f"[DEBUG STATS] Late: {late}")
    except Exception as e:
        print(f"[DEBUG STATS] Warning: could not log stats - {e}")
    
    # Daily breakdown
    daily_stats = db.query(
        func.date(CheckIn.checkin_time).label('date'),
        func.count(CheckIn.id).label('total'),
        func.sum(func.cast(CheckIn.is_late, Integer)).label('late_count')
    ).join(Student)
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        daily_stats = daily_stats.filter(Student.school_id == current_user.school_id)
    elif school_id and current_user.role == UserRole.admin:
        daily_stats = daily_stats.filter(Student.school_id == school_id)
    
    daily_stats = daily_stats.filter(
        and_(
            CheckIn.checkin_time >= start,
            CheckIn.checkin_time <= end
        )
    ).group_by(func.date(CheckIn.checkin_time)).all()
    
    daily_breakdown = [
        {
            "date": str(day.date),
            "total": day.total,
            "late": int(day.late_count) if day.late_count else 0
        }
        for day in daily_stats
    ]
    
    return {
        "period": period,
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "total_students": total_students,
        "total_attendance": total_attendance,
        "present": present,
        "late": late,
        "checked_out": checked_out,
        "justified": justified,
        "attendance_rate": round((present / total_students * 100) if total_students > 0 else 0, 2),
        "late_rate": round((late / total_attendance * 100) if total_attendance > 0 else 0, 2),
        "daily_breakdown": daily_breakdown
    }


@router.get("/tardiness-analysis")
async def get_tardiness_analysis(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analyze tardiness trends"""
    
    # Date range
    if not start_date or not end_date:
        end = datetime.now()
        start = end - timedelta(days=30)
    else:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        end = end.replace(hour=23, minute=59, second=59)
    
    # Build query with role-based filtering
    query = db.query(
        Student.id,
        Student.name,
        Student.name,
        func.count(CheckIn.id).label('total_attendance'),
        func.sum(func.cast(CheckIn.is_late, Integer)).label('late_count')
    ).join(CheckIn)
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        if not current_user.school_id:
            raise HTTPException(status_code=403, detail="User has no assigned school")
        query = query.filter(Student.school_id == current_user.school_id)
    elif current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if school_id and current_user.role == UserRole.admin:
        query = query.filter(Student.school_id == school_id)
    
    if class_name:
        query = query.filter(Student.class_name == class_name)
    
    query = query.filter(
        and_(
            CheckIn.checkin_time >= start,
            CheckIn.checkin_time <= end
        )
    ).group_by(Student.id, Student.name, Student.name)
    
    results = query.all()
    
    # Format results
    students_analysis = []
    for row in results:
        late_count = int(row.late_count) if row.late_count else 0
        late_percentage = round((late_count / row.total_attendance * 100) if row.total_attendance > 0 else 0, 2)
        
        students_analysis.append({
            "student_id": row.id,
            "student_name": row.name,  # Student model only has 'name' field
            "total_attendance": row.total_attendance,
            "late_count": late_count,
            "late_percentage": late_percentage
        })
    
    # Sort by late percentage
    students_analysis.sort(key=lambda x: x['late_percentage'], reverse=True)
    
    # Get trends (week by week)
    # Use PostgreSQL TO_CHAR for week formatting
    weekly_query = db.query(
        func.to_char(CheckIn.checkin_time, 'YYYY-IW').label('week'),
        func.count(CheckIn.id).label('total'),
        func.sum(func.cast(CheckIn.is_late, Integer)).label('late_count')
    ).join(Student)
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        weekly_query = weekly_query.filter(Student.school_id == current_user.school_id)
    elif school_id and current_user.role == UserRole.admin:
        weekly_query = weekly_query.filter(Student.school_id == school_id)
    
    weekly_query = weekly_query.filter(
        and_(
            CheckIn.checkin_time >= start,
            CheckIn.checkin_time <= end
        )
    ).group_by(func.to_char(CheckIn.checkin_time, 'YYYY-IW'))
    
    weekly_trends = weekly_query.all()
    
    trends = [
        {
            "week": row.week,
            "total": row.total,
            "late": int(row.late_count) if row.late_count else 0,
            "late_percentage": round((int(row.late_count) / row.total * 100) if row.total > 0 and row.late_count else 0, 2)
        }
        for row in weekly_trends
    ]
    
    return {
        "start_date": start.strftime("%Y-%m-%d"),
        "end_date": end.strftime("%Y-%m-%d"),
        "top_tardy_students": students_analysis[:20],  # Top 20
        "weekly_trends": trends
    }


@router.get("/export-pdf")
async def export_pdf_report(
    report_type: str = Query(..., regex="^(history|statistics|tardiness)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export report to PDF"""
    
    from fastapi.responses import StreamingResponse
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    # Get school name for header
    school_name = "All Schools"
    if current_user.role in [UserRole.director, UserRole.teacher]:
        school = db.query(School).filter(School.id == current_user.school_id).first()
        school_name = school.name if school else "Unknown School"
    elif school_id and current_user.role == UserRole.admin:
        school = db.query(School).filter(School.id == school_id).first()
        school_name = school.name if school else f"School #{school_id}"
    
    # Header
    title_text = f"ArrivApp - {report_type.title()} Report"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Paragraph(f"School: {school_name}", styles['Normal']))
    if class_name:
        elements.append(Paragraph(f"Class: {class_name}", styles['Normal']))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    if report_type == "history":
        # Get attendance history using internal helper
        history_data = _get_attendance_history_internal(
            db=db,
            current_user=current_user,
            start_date=start_date,
            end_date=end_date,
            school_id=school_id,
            class_name=class_name
        )
        
        elements.append(Paragraph(f"<b>CheckIn History</b> ({history_data['total']} records)", styles['Heading2']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Table data
        data = [['Date', 'Student', 'School', 'Check-in', 'Check-out', 'Status']]
        for record in history_data['records'][:100]:  # Limit to 100 records
            check_in = datetime.fromisoformat(record['check_in_time']).strftime('%Y-%m-%d %H:%M')
            check_out = datetime.fromisoformat(record['check_out_time']).strftime('%H:%M') if record['check_out_time'] else '-'
            status = '⏰ Late' if record['late'] else '✓ On time'
            
            data.append([
                check_in.split()[0],
                f"{record['student_name']} {record['student_surname']}",
                record['school_name'] or '-',
                check_in.split()[1],
                check_out,
                status
            ])
        
        table = Table(data, colWidths=[1.2*inch, 2*inch, 1.5*inch, 1*inch, 1*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(table)
    
    elif report_type == "statistics":
        # Get statistics - inline implementation for PDF export
        # Determine date range
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        end = end.replace(hour=23, minute=59, second=59)
        
        # Build query with role-based filtering
        query = db.query(CheckIn).join(Student)
        
        if current_user.role in [UserRole.director, UserRole.teacher]:
            if not current_user.school_id:
                raise HTTPException(status_code=403, detail="User has no assigned school")
            query = query.filter(Student.school_id == current_user.school_id)
        elif current_user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        # Admin can filter by school
        if school_id and current_user.role == UserRole.admin:
            query = query.filter(Student.school_id == school_id)
        
        # Filter by class
        if class_name:
            query = query.filter(Student.class_name == class_name)
        
        # Filter by date range
        query_with_dates = query.filter(
            and_(
                CheckIn.checkin_time >= start,
                CheckIn.checkin_time <= end
            )
        )
        
        # Calculate statistics
        total_attendance = query_with_dates.count()
        present = total_attendance
        late = query_with_dates.filter(CheckIn.is_late == True).count()
        checked_out = query_with_dates.filter(CheckIn.checkout_time.isnot(None)).count()
        
        # Get total students in scope
        student_query = db.query(Student)
        if current_user.role in [UserRole.director, UserRole.teacher]:
            student_query = student_query.filter(Student.school_id == current_user.school_id)
        elif school_id and current_user.role == UserRole.admin:
            student_query = student_query.filter(Student.school_id == school_id)
        
        total_students = student_query.filter(Student.is_active == True).count()
        
        # Calculate rates
        attendance_rate = round((total_attendance / (total_students * 20)) * 100, 2) if total_students > 0 else 0
        late_rate = round((late / total_attendance) * 100, 2) if total_attendance > 0 else 0
        
        # Daily breakdown
        daily_stats = db.query(
            func.date(CheckIn.checkin_time).label('date'),
            func.count(CheckIn.id).label('total'),
            func.sum(func.cast(CheckIn.is_late, Integer)).label('late_count')
        ).join(Student)
        
        if current_user.role in [UserRole.director, UserRole.teacher]:
            daily_stats = daily_stats.filter(Student.school_id == current_user.school_id)
        elif school_id and current_user.role == UserRole.admin:
            daily_stats = daily_stats.filter(Student.school_id == school_id)
        
        daily_stats = daily_stats.filter(
            and_(
                CheckIn.checkin_time >= start,
                CheckIn.checkin_time <= end
            )
        ).group_by(func.date(CheckIn.checkin_time)).all()
        
        daily_breakdown = [
            {
                "date": str(day.date),
                "total": day.total,
                "late": int(day.late_count) if day.late_count else 0
            }
            for day in daily_stats
        ]
        
        stats_data = {
            "period": "monthly",
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "total_students": total_students,
            "total_attendance": total_attendance,
            "present": present,
            "late": late,
            "early_checkout": 0,
            "attendance_rate": attendance_rate,
            "late_rate": late_rate,
            "daily_breakdown": daily_breakdown
        }
        
        elements.append(Paragraph(f"<b>Statistics Report</b>", styles['Heading2']))
        elements.append(Paragraph(f"Period: {stats_data['start_date']} to {stats_data['end_date']}", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Students', str(stats_data['total_students'])],
            ['Total CheckIn Records', str(stats_data['total_attendance'])],
            ['Present', str(stats_data['present'])],
            ['Late Arrivals', str(stats_data['late'])],
            ['Early Checkouts', str(stats_data['early_checkout'])],
            ['CheckIn Rate', f"{stats_data['attendance_rate']}%"],
            ['Late Rate', f"{stats_data['late_rate']}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3b82f6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        
        # Daily breakdown
        if stats_data['daily_breakdown']:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("<b>Daily Breakdown</b>", styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            daily_data = [['Date', 'Total CheckIn', 'Late Arrivals']]
            for day in stats_data['daily_breakdown']:
                daily_data.append([day['date'], str(day['total']), str(day['late'])])
            
            daily_table = Table(daily_data, colWidths=[2*inch, 2*inch, 2*inch])
            daily_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(daily_table)
    
    elif report_type == "tardiness":
        # Get tardiness analysis - inline implementation
        # Date range
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        end = end.replace(hour=23, minute=59, second=59)
        
        # Get all check-ins for period
        query = db.query(CheckIn).join(Student)
        
        if current_user.role in [UserRole.director, UserRole.teacher]:
            if not current_user.school_id:
                raise HTTPException(status_code=403, detail="User has no assigned school")
            query = query.filter(Student.school_id == current_user.school_id)
        elif current_user.role != UserRole.admin:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        
        if school_id and current_user.role == UserRole.admin:
            query = query.filter(Student.school_id == school_id)
        
        if class_name:
            query = query.filter(Student.class_name == class_name)
        
        query = query.filter(
            and_(
                CheckIn.checkin_time >= start,
                CheckIn.checkin_time <= end
            )
        )
        
        records = query.all()
        
        # Group by student and calculate tardiness
        student_tardiness = {}
        for record in records:
            student_id = record.student_id
            if student_id not in student_tardiness:
                student_name = f"{record.student.name}" if record.student else "Unknown"
                student_tardiness[student_id] = {
                    "student_name": student_name,
                    "total_attendance": 0,
                    "late_count": 0
                }
            student_tardiness[student_id]["total_attendance"] += 1
            if record.is_late:
                student_tardiness[student_id]["late_count"] += 1
        
        # Calculate percentages and sort
        top_tardy_students = []
        for student_id, data in student_tardiness.items():
            late_pct = round((data["late_count"] / data["total_attendance"]) * 100, 1) if data["total_attendance"] > 0 else 0
            top_tardy_students.append({
                "student_name": data["student_name"],
                "total_attendance": data["total_attendance"],
                "late_count": data["late_count"],
                "late_percentage": late_pct
            })
        
        top_tardy_students.sort(key=lambda x: x["late_count"], reverse=True)
        
        # Weekly trends
        weekly_stats = db.query(
            func.strftime('%Y-W%W', CheckIn.checkin_time).label('week'),
            func.count(CheckIn.id).label('total'),
            func.sum(func.cast(CheckIn.is_late, Integer)).label('late_count')
        ).join(Student)
        
        if current_user.role in [UserRole.director, UserRole.teacher]:
            weekly_stats = weekly_stats.filter(Student.school_id == current_user.school_id)
        elif school_id and current_user.role == UserRole.admin:
            weekly_stats = weekly_stats.filter(Student.school_id == school_id)
        
        if class_name:
            weekly_stats = weekly_stats.filter(Student.class_name == class_name)
        
        weekly_stats = weekly_stats.filter(
            and_(
                CheckIn.checkin_time >= start,
                CheckIn.checkin_time <= end
            )
        ).group_by(func.strftime('%Y-W%W', CheckIn.checkin_time)).all()
        
        weekly_trends = [
            {
                "week": week.week,
                "total": week.total,
                "late": int(week.late_count) if week.late_count else 0,
                "late_percentage": round((int(week.late_count if week.late_count else 0) / week.total) * 100, 1) if week.total > 0 else 0
            }
            for week in weekly_stats
        ]
        
        tardiness_data = {
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": end.strftime("%Y-%m-%d"),
            "top_tardy_students": top_tardy_students,
            "weekly_trends": weekly_trends
        }
        
        elements.append(Paragraph(f"<b>Tardiness Analysis</b>", styles['Heading2']))
        elements.append(Paragraph(f"Period: {tardiness_data['start_date']} to {tardiness_data['end_date']}", styles['Normal']))
        elements.append(Spacer(1, 0.2*inch))
        
        # Top tardy students
        elements.append(Paragraph("<b>Students with Most Late Arrivals</b>", styles['Heading3']))
        elements.append(Spacer(1, 0.1*inch))
        
        tardy_data = [['Student', 'Total CheckIn', 'Late Count', 'Late %']]
        for student in tardiness_data['top_tardy_students'][:15]:
            tardy_data.append([
                student['student_name'],
                str(student['total_attendance']),
                str(student['late_count']),
                f"{student['late_percentage']}%"
            ])
        
        tardy_table = Table(tardy_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        tardy_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(tardy_table)
        
        # Weekly trends
        if tardiness_data['weekly_trends']:
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph("<b>Weekly Trends</b>", styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
            
            trend_data = [['Week', 'Total', 'Late', 'Late %']]
            for week in tardiness_data['weekly_trends']:
                trend_data.append([
                    week['week'],
                    str(week['total']),
                    str(week['late']),
                    f"{week['late_percentage']}%"
                ])
            
            trend_table = Table(trend_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            trend_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(trend_table)
    
    # Build PDF
    doc.build(elements)
    
    # Return PDF
    buffer.seek(0)
    filename = f"arrivapp_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/historical-analytics")
async def get_historical_analytics(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    school_id: Optional[int] = Query(None),
    class_name: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get long-term analytics including trends, chronic absenteeism, and improvement tracking"""
    
    # Determine date range (default to last 90 days)
    if not end_date:
        end = datetime.now()
    else:
        end = datetime.strptime(end_date, "%Y-%m-%d")
        end = end.replace(hour=23, minute=59, second=59)
    
    if not start_date:
        start = end - timedelta(days=90)
    else:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        start = start.replace(hour=0, minute=0, second=0)
    
    # Build base query with role-based filtering
    base_query = db.query(CheckIn).join(Student)
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        if not current_user.school_id:
            raise HTTPException(status_code=403, detail="User has no assigned school")
        base_query = base_query.filter(Student.school_id == current_user.school_id)
    elif current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if school_id and current_user.role == UserRole.admin:
        base_query = base_query.filter(Student.school_id == school_id)
    
    if class_name:
        base_query = base_query.filter(Student.class_name == class_name)
    
    # Filter by date range
    base_query = base_query.filter(
        CheckIn.checkin_time >= start,
        CheckIn.checkin_time <= end
    )
    
    # ===== MONTHLY TRENDS =====
    monthly_trends = []
    current_date = start
    
    while current_date <= end:
        month_start = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if current_date.month == 12:
            month_end = current_date.replace(year=current_date.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        else:
            month_end = current_date.replace(month=current_date.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        
        # Get data for this month
        month_checkins = db.query(CheckIn).join(Student).filter(
            CheckIn.checkin_time >= month_start,
            CheckIn.checkin_time <= month_end
        )
        
        if current_user.role in [UserRole.director, UserRole.teacher]:
            month_checkins = month_checkins.filter(Student.school_id == current_user.school_id)
        elif school_id and current_user.role == UserRole.admin:
            month_checkins = month_checkins.filter(Student.school_id == school_id)
        
        if class_name:
            month_checkins = month_checkins.filter(Student.class_name == class_name)
        
        total = month_checkins.count()
        late = month_checkins.filter(CheckIn.is_late == True).count()
        
        # Calculate business days in month
        days_in_month = (month_end - month_start).days + 1
        # Rough estimate: ~22 business days per month (excluding weekends)
        business_days = days_in_month * 5 // 7
        
        # Get unique students who checked in
        unique_students = month_checkins.with_entities(CheckIn.student_id).distinct().count()
        
        attendance_rate = (total / (unique_students * business_days * 1.0)) * 100 if unique_students > 0 else 0
        
        monthly_trends.append({
            "month": month_start.strftime("%Y-%m"),
            "total_attendance": total,
            "late_count": late,
            "attendance_rate": min(attendance_rate, 100)  # Cap at 100%
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1, day=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1, day=1)
    
    # ===== MONTHLY COMPARISON =====
    monthly_comparison = []
    for trend in monthly_trends:
        month_data = trend
        # Get total students for the period
        students_query = db.query(Student)
        if current_user.role in [UserRole.director, UserRole.teacher]:
            students_query = students_query.filter(Student.school_id == current_user.school_id)
        elif school_id and current_user.role == UserRole.admin:
            students_query = students_query.filter(Student.school_id == school_id)
        
        total_students = students_query.count()
        business_days = 22  # Approximate
        expected_attendance = total_students * business_days
        
        present = month_data["total_attendance"]
        late = month_data["late_count"]
        absent = max(0, expected_attendance - present)
        
        monthly_comparison.append({
            "month": month_data["month"],
            "present": present,
            "late": late,
            "absent": absent
        })
    
    # ===== CHRONIC ABSENTEEISM =====
    # Students with < 80% attendance rate
    students_query = db.query(Student.id, Student.name, Student.school_id)
    if current_user.role in [UserRole.director, UserRole.teacher]:
        students_query = students_query.filter(Student.school_id == current_user.school_id)
    elif school_id and current_user.role == UserRole.admin:
        students_query = students_query.filter(Student.school_id == school_id)
    
    if class_name:
        students_query = students_query.filter(Student.class_name == class_name)
    
    chronic_absentees = []
    total_days = (end - start).days
    expected_attendance_days = total_days * 5 // 7  # Business days
    
    for student in students_query.all():
        attended = db.query(CheckIn).filter(
            CheckIn.student_id == student.id,
            CheckIn.checkin_time >= start,
            CheckIn.checkin_time <= end
        ).count()
        
        attendance_rate = (attended / expected_attendance_days) * 100 if expected_attendance_days > 0 else 0
        
        if attendance_rate < 80:
            school = db.query(School).filter(School.id == student.school_id).first()
            chronic_absentees.append({
                "student_name": student.name,
                "school_name": school.name if school else None,
                "expected_days": expected_attendance_days,
                "attended_days": attended,
                "attendance_rate": attendance_rate
            })
    
    # Sort by attendance rate (lowest first)
    chronic_absentees.sort(key=lambda x: x["attendance_rate"])
    
    # ===== WEEKDAY PATTERNS =====
    weekday_patterns = []
    for weekday in range(5):  # Monday=0 to Friday=4
        # PostgreSQL: 1=Monday, ..., 7=Sunday (ISO 8601)
        # Python: 0=Monday, ..., 4=Friday
        # Convert: Monday(0) -> 1, Tuesday(1) -> 2, ..., Friday(4) -> 5
        dow_value = weekday + 1
        
        day_checkins = base_query.filter(
            extract('isodow', CheckIn.checkin_time) == dow_value
        )
        
        total = day_checkins.count()
        on_time = day_checkins.filter(CheckIn.is_late == False).count()
        
        weekday_patterns.append({
            "weekday": weekday,
            "attendance_rate": 100 if total == 0 else min(100, (total / (total_days // 7)) * 100 * 0.2),  # Normalized
            "punctuality_rate": (on_time / total * 100) if total > 0 else 0
        })
    
    # ===== STUDENT IMPROVEMENT TRACKING =====
    # Compare first month vs last month
    if len(monthly_trends) >= 2:
        first_month = monthly_trends[0]
        last_month = monthly_trends[-1]
        
        first_month_start = datetime.strptime(first_month["month"], "%Y-%m").replace(day=1)
        first_month_end = (first_month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        last_month_start = datetime.strptime(last_month["month"], "%Y-%m").replace(day=1)
        last_month_end = (last_month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        
        improved_students = []
        
        for student in students_query.all():
            first_attended = db.query(CheckIn).filter(
                CheckIn.student_id == student.id,
                CheckIn.checkin_time >= first_month_start,
                CheckIn.checkin_time <= first_month_end
            ).count()
            
            last_attended = db.query(CheckIn).filter(
                CheckIn.student_id == student.id,
                CheckIn.checkin_time >= last_month_start,
                CheckIn.checkin_time <= last_month_end
            ).count()
            
            # Calculate rates (assuming 22 business days per month)
            first_rate = (first_attended / 22) * 100
            last_rate = (last_attended / 22) * 100
            improvement = last_rate - first_rate
            
            if improvement > 5:  # At least 5% improvement
                improved_students.append({
                    "student_name": student.name,
                    "first_month_rate": first_rate,
                    "last_month_rate": last_rate,
                    "improvement": improvement
                })
        
        # Sort by improvement (highest first)
        improved_students.sort(key=lambda x: x["improvement"], reverse=True)
        top_improved = improved_students[:10]  # Top 10
    else:
        top_improved = []
    
    # ===== CALCULATE SUMMARY METRICS =====
    avg_monthly_attendance = sum(t["total_attendance"] for t in monthly_trends) / len(monthly_trends) if monthly_trends else 0
    
    # Overall trend (compare first vs last month attendance rate)
    overall_trend = 0
    if len(monthly_trends) >= 2:
        overall_trend = monthly_trends[-1]["attendance_rate"] - monthly_trends[0]["attendance_rate"]
    
    # Punctuality improvement
    punctuality_improvement = 0
    if len(monthly_trends) >= 2:
        first_late_rate = (monthly_trends[0]["late_count"] / monthly_trends[0]["total_attendance"] * 100) if monthly_trends[0]["total_attendance"] > 0 else 0
        last_late_rate = (monthly_trends[-1]["late_count"] / monthly_trends[-1]["total_attendance"] * 100) if monthly_trends[-1]["total_attendance"] > 0 else 0
        punctuality_improvement = first_late_rate - last_late_rate  # Positive = improvement (less late)
    
    return {
        "monthly_trends": monthly_trends,
        "monthly_comparison": monthly_comparison,
        "chronic_absentees": chronic_absentees[:20],  # Limit to top 20
        "chronic_absentee_count": len(chronic_absentees),
        "weekday_patterns": weekday_patterns,
        "top_improved_students": top_improved,
        "avg_monthly_attendance": avg_monthly_attendance,
        "overall_trend": overall_trend,
        "punctuality_improvement": punctuality_improvement
    }
