from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional
from datetime import datetime, date
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_school_user
from app.models.models import Justification, Student, User, UserRole, JustificationType, JustificationStatus
from app.models.schemas import (
    JustificationCreate, 
    JustificationUpdate, 
    Justification as JustificationSchema
)

router = APIRouter(prefix="/api/justifications", tags=["Justifications"])


@router.get("/validate-email")
async def validate_parent_email(
    email: str = Query(..., description="Parent email address"),
    db: Session = Depends(get_db)
):
    """Validate parent email and return associated students (public endpoint)."""
    # Find all students with this parent email
    students = db.query(Student).filter(
        Student.parent_email.ilike(email.strip())
    ).all()
    
    if not students:
        raise HTTPException(
            status_code=404, 
            detail="No students found with this email address"
        )
    
    # Return basic student info
    return {
        "email": email,
        "students": [
            {
                "id": student.id,
                "name": student.name,
                "class_name": student.class_name
            }
            for student in students
        ]
    }


@router.post("/", response_model=JustificationSchema, status_code=status.HTTP_201_CREATED)
async def create_justification(
    justification: JustificationCreate,
    db: Session = Depends(get_db)
):
    """Create a new justification (open endpoint for parents)."""
    # Verify student exists
    student = db.query(Student).filter(Student.id == justification.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Verify the email matches the student's parent email
    if justification.submitted_by.lower() != student.parent_email.lower():
        raise HTTPException(
            status_code=403, 
            detail="Only the registered parent can submit justifications"
        )
    
    # Create justification
    db_justification = Justification(
        student_id=justification.student_id,
        justification_type=JustificationType[justification.justification_type],
        date=justification.date,
        reason=justification.reason,
        submitted_by=justification.submitted_by,
        status=JustificationStatus.pending
    )
    
    db.add(db_justification)
    db.commit()
    db.refresh(db_justification)
    
    return db_justification


@router.get("/", response_model=List[JustificationSchema])
async def get_justifications(
    student_id: Optional[int] = None,
    status: Optional[str] = None,
    date: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_school_user)
):
    """Get justifications (filtered by school for non-admins)."""
    query = db.query(Justification).join(Student)
    
    # Filter by school for non-admin users
    if current_user.role != UserRole.admin:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be associated with a school"
            )
        query = query.filter(Student.school_id == current_user.school_id)
    
    # Apply filters
    if student_id:
        query = query.filter(Justification.student_id == student_id)
    
    if status:
        query = query.filter(Justification.status == JustificationStatus[status])
    
    # If specific date is provided, filter for that exact date
    if date:
        query = query.filter(Justification.date == date)
    # Otherwise use date range if provided
    elif start_date or end_date:
        if start_date:
            query = query.filter(Justification.date >= start_date)
        
        if end_date:
            query = query.filter(Justification.date <= end_date)
    
    justifications = query.order_by(Justification.submitted_at.desc()).all()
    
    # Add student names to justifications
    for j in justifications:
        student = db.query(Student).filter(Student.id == j.student_id).first()
        if student:
            j.student_name = student.name
    
    return justifications


@router.get("/{justification_id}", response_model=JustificationSchema)
async def get_justification(
    justification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_school_user)
):
    """Get a specific justification."""
    justification = db.query(Justification).filter(
        Justification.id == justification_id
    ).first()
    
    if not justification:
        raise HTTPException(status_code=404, detail="Justification not found")
    
    # Check access rights
    student = db.query(Student).filter(Student.id == justification.student_id).first()
    if current_user.role != UserRole.admin:
        if student.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    return justification


@router.put("/{justification_id}", response_model=JustificationSchema)
async def update_justification(
    justification_id: int,
    justification_update: JustificationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_school_user)
):
    """Update justification status (staff only)."""
    justification = db.query(Justification).filter(
        Justification.id == justification_id
    ).first()
    
    if not justification:
        raise HTTPException(status_code=404, detail="Justification not found")
    
    # Check access rights
    student = db.query(Student).filter(Student.id == justification.student_id).first()
    if current_user.role != UserRole.admin:
        if student.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    # Update fields
    if justification_update.status:
        justification.status = JustificationStatus[justification_update.status]
        justification.reviewed_by = current_user.id
        justification.reviewed_at = datetime.utcnow()
    
    if justification_update.notes is not None:
        justification.notes = justification_update.notes
    
    db.commit()
    db.refresh(justification)
    
    return justification


@router.delete("/{justification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_justification(
    justification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_school_user)
):
    """Delete a justification (staff only)."""
    justification = db.query(Justification).filter(
        Justification.id == justification_id
    ).first()
    
    if not justification:
        raise HTTPException(status_code=404, detail="Justification not found")
    
    # Check access rights
    student = db.query(Student).filter(Student.id == justification.student_id).first()
    if current_user.role != UserRole.admin:
        if student.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    
    db.delete(justification)
    db.commit()
    
    return None


@router.get("/student/{student_id}/pending", response_model=List[JustificationSchema])
async def get_student_pending_justifications(
    student_id: int,
    db: Session = Depends(get_db)
):
    """Get pending justifications for a student (public for parents)."""
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    justifications = db.query(Justification).filter(
        and_(
            Justification.student_id == student_id,
            Justification.status == JustificationStatus.pending
        )
    ).order_by(Justification.submitted_at.desc()).all()
    
    return justifications
