from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, Integer, cast
from typing import Optional, List
from datetime import datetime, date, timedelta
from app.core.database import get_db
from app.models.models import (
    KitchenAttendance, StudentDietaryNeeds, CheckIn, Student, 
    School, User, UserRole, AbsenceNotification
)
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/comedor", tags=["Kitchen/Comedor"])


@router.get("/today")
async def get_kitchen_data_today(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get today's kitchen meal planning data at 10 AM snapshot"""
    
    # Only kitchen staff (teachers/directors) can access - or admins
    if current_user.role not in [UserRole.admin, UserRole.director, UserRole.teacher]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get user's school
    if current_user.role in [UserRole.director, UserRole.teacher]:
        if not current_user.school_id:
            raise HTTPException(status_code=403, detail="User has no assigned school")
        school_id = current_user.school_id
    else:
        # Admin - try to infer from query param
        school_id = None
    
    today = datetime.now().date()
    
    # Get today's kitchen attendance snapshot (at 10 AM)
    snapshots = db.query(KitchenAttendance).filter(
        and_(
            func.date(KitchenAttendance.snapshot_date) == today,
            KitchenAttendance.school_id == school_id if school_id else True
        )
    ).all()
    
    if not snapshots:
        # If no snapshot yet, generate it on-the-fly
        snapshots = _generate_kitchen_snapshot_for_today(db, school_id)
    
    # Calculate totals
    total_students_all_classes = sum(s.total_students for s in snapshots)
    total_present = sum(s.present for s in snapshots)
    total_absent = sum(s.absent for s in snapshots)
    total_with_allergies = sum(s.with_allergies for s in snapshots)
    total_with_special_diet = sum(s.with_special_diet for s in snapshots)
    
    # Get school name
    school = db.query(School).filter(School.id == school_id).first() if school_id else None
    
    return {
        "date": today.isoformat(),
        "school": school.name if school else "All Schools",
        "overview": {
            "total_students": total_students_all_classes,
            "expected_to_eat": total_present,  # Will eat today (already present)
            "absent": total_absent,
            "will_arrive_later": total_students_all_classes - total_present - total_absent,
            "with_allergies": total_with_allergies,
            "with_special_diet": total_with_special_diet
        },
        "by_class": [
            {
                "class_name": s.class_name,
                "total_students": s.total_students,
                "present": s.present,
                "absent": s.absent,
                "will_arrive_later": s.will_arrive_later,
                "with_allergies": s.with_allergies,
                "with_special_diet": s.with_special_diet
            }
            for s in sorted(snapshots, key=lambda x: x.class_name)
        ]
    }


@router.get("/history")
async def get_kitchen_data_history(
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get kitchen attendance history for the last N days"""
    
    # Only kitchen staff (teachers/directors) can access - or admins
    if current_user.role not in [UserRole.admin, UserRole.director, UserRole.teacher]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get user's school
    if current_user.role in [UserRole.director, UserRole.teacher]:
        if not current_user.school_id:
            raise HTTPException(status_code=403, detail="User has no assigned school")
        school_id = current_user.school_id
    else:
        school_id = None
    
    start_date = datetime.now().date() - timedelta(days=days)
    
    snapshots = db.query(KitchenAttendance).filter(
        and_(
            func.date(KitchenAttendance.snapshot_date) >= start_date,
            KitchenAttendance.school_id == school_id if school_id else True
        )
    ).order_by(KitchenAttendance.snapshot_date.desc()).all()
    
    # Group by date
    by_date = {}
    for snapshot in snapshots:
        snapshot_date = snapshot.snapshot_date.date().isoformat()
        if snapshot_date not in by_date:
            by_date[snapshot_date] = []
        by_date[snapshot_date].append({
            "class_name": snapshot.class_name,
            "total_students": snapshot.total_students,
            "present": snapshot.present,
            "with_allergies": snapshot.with_allergies,
            "with_special_diet": snapshot.with_special_diet
        })
    
    return {
        "days": days,
        "history": by_date
    }


@router.get("/dietary-summary")
async def get_dietary_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get overall dietary requirements for the school"""
    
    if current_user.role not in [UserRole.admin, UserRole.director, UserRole.teacher]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if current_user.role in [UserRole.director, UserRole.teacher]:
        if not current_user.school_id:
            raise HTTPException(status_code=403, detail="User has no assigned school")
        school_id = current_user.school_id
    else:
        school_id = None
    
    # Get all active students for this school
    student_query = db.query(Student).filter(Student.is_active == True)
    if school_id:
        student_query = student_query.filter(Student.school_id == school_id)
    
    total_students = student_query.count()
    
    # Get dietary needs
    dietary_needs = db.query(StudentDietaryNeeds).filter(
        StudentDietaryNeeds.student_id.in_(
            db.query(Student.id).filter(
                Student.school_id == school_id if school_id else True
            )
        )
    ).all()
    
    students_with_allergies = sum(1 for d in dietary_needs if d.has_allergies)
    students_with_special_diet = sum(1 for d in dietary_needs if d.has_special_diet)
    
    # Get common allergies
    allergies = {}
    special_diets = {}
    for dietary in dietary_needs:
        if dietary.has_allergies and dietary.allergies_description:
            for allergy in dietary.allergies_description.split(","):
                allergy = allergy.strip()
                allergies[allergy] = allergies.get(allergy, 0) + 1
        if dietary.has_special_diet and dietary.special_diet_description:
            for diet in dietary.special_diet_description.split(","):
                diet = diet.strip()
                special_diets[diet] = special_diets.get(diet, 0) + 1
    
    return {
        "total_students": total_students,
        "with_allergies": {
            "count": students_with_allergies,
            "percentage": round((students_with_allergies / total_students) * 100, 1) if total_students > 0 else 0,
            "common_allergies": sorted(allergies.items(), key=lambda x: x[1], reverse=True)
        },
        "with_special_diet": {
            "count": students_with_special_diet,
            "percentage": round((students_with_special_diet / total_students) * 100, 1) if total_students > 0 else 0,
            "common_diets": sorted(special_diets.items(), key=lambda x: x[1], reverse=True)
        }
    }


def _generate_kitchen_snapshot_for_today(db: Session, school_id: Optional[int]) -> List[KitchenAttendance]:
    """Generate kitchen attendance snapshot for today at 10 AM"""
    
    today = datetime.now().date()
    snapshot_datetime = datetime.combine(today, datetime.min.time()).replace(hour=10, minute=0)
    
    # Get all classes for the school
    student_query = db.query(Student).filter(Student.is_active == True)
    if school_id:
        student_query = student_query.filter(Student.school_id == school_id)
    
    all_students = student_query.all()
    
    # Group students by class
    classes = {}
    for student in all_students:
        if student.class_name not in classes:
            classes[student.class_name] = []
        classes[student.class_name].append(student)
    
    # Generate snapshot for each class
    snapshots = []
    for class_name, students in classes.items():
        total = len(students)
        
        # Check who checked in today
        checkins_today = db.query(CheckIn).filter(
            and_(
                CheckIn.student_id.in_([s.id for s in students]),
                func.date(CheckIn.checkin_time) == today
            )
        ).all()
        
        present = len(checkins_today)
        
        # Check who has absence notifications (absent)
        absences_today = db.query(AbsenceNotification).filter(
            and_(
                AbsenceNotification.student_id.in_([s.id for s in students]),
                func.date(AbsenceNotification.notification_date) == today
            )
        ).all()
        
        absent = len(absences_today)
        will_arrive = total - present - absent
        
        # Count dietary needs
        dietary_counts = db.query(
            func.sum(cast(StudentDietaryNeeds.has_allergies, Integer)).label('allergies'),
            func.sum(cast(StudentDietaryNeeds.has_special_diet, Integer)).label('special_diet')
        ).filter(
            StudentDietaryNeeds.student_id.in_([s.id for s in students])
        ).first()
        
        with_allergies = dietary_counts.allergies or 0 if dietary_counts else 0
        with_special_diet = dietary_counts.special_diet or 0 if dietary_counts else 0
        
        # Get school_id from first student in class
        school_id_class = students[0].school_id if students else school_id
        
        snapshot = KitchenAttendance(
            school_id=school_id_class,
            snapshot_date=snapshot_datetime,
            class_name=class_name,
            total_students=total,
            present=present,
            absent=absent,
            will_arrive_later=will_arrive,
            with_allergies=with_allergies,
            with_special_diet=with_special_diet
        )
        
        snapshots.append(snapshot)
    
    # Save snapshots to database
    for snapshot in snapshots:
        db.add(snapshot)
    
    db.commit()
    
    return snapshots
