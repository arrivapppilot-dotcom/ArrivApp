from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models import models, schemas

router = APIRouter(prefix="/api/schools", tags=["Schools"])


@router.post("/", response_model=schemas.School, status_code=status.HTTP_201_CREATED)
def create_school(
    school: schemas.SchoolCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Create a new school (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create schools"
        )
    
    # Check if school name already exists
    db_school = db.query(models.School).filter(
        models.School.name == school.name
    ).first()
    if db_school:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School with this name already exists"
        )
    
    db_school = models.School(**school.dict())
    db.add(db_school)
    db.commit()
    db.refresh(db_school)
    return db_school


@router.get("/", response_model=List[schemas.School])
def list_schools(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """List all schools"""
    if current_user.is_admin:
        # Admin can see all schools
        schools = db.query(models.School).offset(skip).limit(limit).all()
    elif current_user.school_id:
        # Regular user can only see their school
        schools = db.query(models.School).filter(
            models.School.id == current_user.school_id
        ).all()
    else:
        schools = []
    
    return schools


@router.get("/{school_id}", response_model=schemas.School)
def get_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get a specific school"""
    school = db.query(models.School).filter(models.School.id == school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Check access permissions
    if not current_user.is_admin and current_user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this school"
        )
    
    return school


@router.put("/{school_id}", response_model=schemas.School)
def update_school(
    school_id: int,
    school_update: schemas.SchoolUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update a school (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update schools"
        )
    
    db_school = db.query(models.School).filter(models.School.id == school_id).first()
    if not db_school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    update_data = school_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_school, field, value)
    
    db.commit()
    db.refresh(db_school)
    return db_school


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_school(
    school_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Delete a school (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete schools"
        )
    
    db_school = db.query(models.School).filter(models.School.id == school_id).first()
    if not db_school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    # Check if school has students
    student_count = db.query(models.Student).filter(
        models.Student.school_id == school_id
    ).count()
    
    if student_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete school with {student_count} active students"
        )
    
    db.delete(db_school)
    db.commit()
    return None
