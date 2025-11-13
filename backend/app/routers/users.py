from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_admin_user
from app.models.models import User, School, UserRole
from app.models.schemas import (
    User as UserSchema, 
    UserCreate, 
    UserUpdate,
    UserWithSchool
)
from app.core.security import get_password_hash

router = APIRouter(prefix="/api/users", tags=["Users"])


def serialize_user(user: User) -> dict:
    """Manually serialize user object to dict for Pydantic v1 compatibility."""
    result = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "full_name": user.full_name,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "school_id": user.school_id,
        "created_at": user.created_at.isoformat() if user.created_at else None
    }
    
    # Add school if present
    if hasattr(user, 'school') and user.school:
        result["school"] = {
            "id": user.school.id,
            "name": user.school.name,
            "address": user.school.address,
            "contact_email": user.school.contact_email,
            "contact_phone": user.school.contact_phone,
            "timezone": user.school.timezone,
            "is_active": user.school.is_active,
            "created_at": user.school.created_at.isoformat() if user.school.created_at else None
        }
    else:
        result["school"] = None
    
    return result


@router.get("/", response_model=List[UserWithSchool])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """List all users (admin only)."""
    from sqlalchemy.orm import joinedload
    users = db.query(User).options(joinedload(User.school)).offset(skip).limit(limit).all()
    return [serialize_user(user) for user in users]


@router.get("/{user_id}", response_model=UserWithSchool)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Get a specific user by ID (admin only)."""
    from sqlalchemy.orm import joinedload
    user = db.query(User).options(joinedload(User.school)).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return serialize_user(user)


@router.post("/", response_model=UserWithSchool, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Create a new user (admin only)."""
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Validate school_id if provided
    if user_data.school_id:
        school = db.query(School).filter(School.id == user_data.school_id).first()
        if not school:
            raise HTTPException(status_code=400, detail="School not found")
    
    # For directors and teachers, school_id is required
    if user_data.role in [UserRole.director, UserRole.teacher] and not user_data.school_id:
        raise HTTPException(
            status_code=400, 
            detail="School is required for directors and teachers"
        )
    
    # Create user
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        school_id=user_data.school_id,
        is_admin=(user_data.role == UserRole.admin),
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return serialize_user(db_user)


@router.put("/{user_id}", response_model=UserWithSchool)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Update a user (admin only)."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if trying to update username to an existing one
    if user_data.email and user_data.email != db_user.email:
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already exists")
    
    # Validate school_id if provided
    if user_data.school_id:
        school = db.query(School).filter(School.id == user_data.school_id).first()
        if not school:
            raise HTTPException(status_code=400, detail="School not found")
    
    # Update fields
    if user_data.email:
        db_user.email = user_data.email
    if user_data.full_name:
        db_user.full_name = user_data.full_name
    if user_data.password:
        db_user.hashed_password = get_password_hash(user_data.password)
    if user_data.school_id is not None:
        db_user.school_id = user_data.school_id
    if user_data.role:
        db_user.role = user_data.role
        db_user.is_admin = (user_data.role == UserRole.admin)
    
    db.commit()
    db.refresh(db_user)
    
    return serialize_user(db_user)


@router.get("/search", response_model=UserWithSchool)
async def search_user(
    q: str,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Search for a user by username or email (admin only)."""
    from sqlalchemy.orm import joinedload
    # Search by username or email
    user = db.query(User).options(joinedload(User.school)).filter(
        (User.username == q) | (User.email == q)
    ).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return serialize_user(user)


@router.put("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: int,
    password_data: dict,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Reset a user's password (admin only)."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_password = password_data.get("new_password")
    if not new_password:
        raise HTTPException(status_code=400, detail="New password is required")
    
    if len(new_password) < 6:
        raise HTTPException(
            status_code=400, 
            detail="Password must be at least 6 characters long"
        )
    
    # Update password
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password reset successfully"}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete a user (admin only)."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves
    if db_user.id == current_admin.id:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete your own account"
        )
    
    db.delete(db_user)
    db.commit()
    
    return None
