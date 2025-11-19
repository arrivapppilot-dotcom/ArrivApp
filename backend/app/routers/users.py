from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_admin_user, get_current_director_or_admin
from app.models.models import User, School, UserRole, TeacherClassAssignment, Student
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


@router.get("/school/users")
async def list_school_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_director_or_admin)
):
    """List users in current user's school (admin or director)."""
    from sqlalchemy.orm import joinedload
    
    # Admins see all users, directors see only their school's users
    if current_user.role == UserRole.admin:
        users = db.query(User).options(joinedload(User.school)).offset(skip).limit(limit).all()
    elif current_user.role == UserRole.director:
        if not current_user.school_id:
            raise HTTPException(status_code=400, detail="Director must have a school assigned")
        users = db.query(User).options(joinedload(User.school)).filter(
            User.school_id == current_user.school_id
        ).offset(skip).limit(limit).all()
    else:
        raise HTTPException(status_code=403, detail="Only admins and directors can view users")
    
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


@router.post("/create-comedor", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_comedor_user(
    data: dict,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Create a comedor (kitchen manager) user (admin only)."""
    school_id = data.get("school_id")
    password = data.get("password", "kitchen2025")
    
    if not school_id:
        raise HTTPException(status_code=400, detail="school_id is required")
    
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Check if school exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=400, detail="School not found")
    
    # Check if comedor user already exists
    existing = db.query(User).filter(User.username == "comedor").first()
    if existing:
        raise HTTPException(status_code=400, detail="Comedor user already exists")
    
    # Create comedor user
    comedor_user = User(
        email="comedor@example.com",
        username="comedor",
        full_name="Kitchen Manager",
        hashed_password=get_password_hash(password),
        role=UserRole.comedor,
        school_id=school_id,
        is_active=True,
        is_admin=False
    )
    
    db.add(comedor_user)
    db.commit()
    db.refresh(comedor_user)
    
    return {
        "message": "Comedor user created successfully",
        "username": "comedor",
        "password": password,
        "email": "comedor@example.com",
        "school": school.name
    }


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


# ==================== Director-specific endpoints ====================

def get_current_director(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
) -> User:
    """Get current user if they are a director (or admin)."""
    from app.core.deps import get_current_user
    
    # For now, we check if user is admin or director
    if current_user.role not in [UserRole.admin, UserRole.director]:
        raise HTTPException(
            status_code=403,
            detail="Only directors and admins can manage teachers"
        )
    return current_user


@router.post("/create-teacher", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    data: dict,
    db: Session = Depends(get_db),
    current_director: User = Depends(get_current_director)
):
    """
    Create a teacher profile (director only).
    
    Expected data:
    {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "secure_password",
        "classes": ["5A", "5B"]  # Optional: assign to classes
    }
    """
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    classes = data.get("classes", [])
    
    # Validation
    if not full_name:
        raise HTTPException(status_code=400, detail="full_name is required")
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Valid email is required")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Check if email already exists
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Generate username from email
    username = email.split("@")[0]
    while db.query(User).filter(User.username == username).first():
        import random
        username = f"{email.split('@')[0]}{random.randint(100, 999)}"
    
    # Get director's school
    if current_director.role == UserRole.director:
        school_id = current_director.school_id
        if not school_id:
            raise HTTPException(status_code=400, detail="Director must have a school assigned")
    else:  # admin
        # For admin, school_id should be provided in data
        school_id = data.get("school_id")
        if not school_id:
            raise HTTPException(status_code=400, detail="school_id is required for admins")
    
    # Verify school exists
    school = db.query(School).filter(School.id == school_id).first()
    if not school:
        raise HTTPException(status_code=400, detail="School not found")
    
    # Create teacher user
    teacher = User(
        email=email,
        username=username,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        role=UserRole.teacher,
        school_id=school_id,
        is_active=True,
        is_admin=False
    )
    
    db.add(teacher)
    db.flush()  # Get the teacher ID without committing
    
    # Assign to classes if provided
    assigned_classes = []
    if classes and isinstance(classes, list):
        for class_name in classes:
            class_name = str(class_name).strip()
            if class_name:
                assignment = TeacherClassAssignment(
                    teacher_id=teacher.id,
                    school_id=school_id,
                    class_name=class_name
                )
                db.add(assignment)
                assigned_classes.append(class_name)
    
    db.commit()
    db.refresh(teacher)
    
    return {
        "message": "Teacher created successfully",
        "teacher_id": teacher.id,
        "username": username,
        "email": email,
        "full_name": full_name,
        "school": school.name,
        "assigned_classes": assigned_classes
    }


@router.get("/classes")
async def get_classes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_director_or_admin)
):
    """Get list of all classes in current user's school or all if admin."""
    from sqlalchemy import distinct
    import json
    
    # Query active classes
    query = db.query(distinct(Student.class_name)).filter(Student.is_active == True)
    
    # Filter by school if director
    if current_user.role == UserRole.director and current_user.school_id:
        query = query.filter(Student.school_id == current_user.school_id)
    
    classes = sorted([row[0] for row in query.all()])
    
    result = {
        "classes": classes,
        "school_id": current_user.school_id,
        "user_role": str(current_user.role)
    }
    
    # Return with explicit no-cache headers to bypass browser caching
    return Response(
        content=json.dumps(result),
        media_type="application/json",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
            "ETag": f'"{hash(str(classes))}"'
        }
    )


@router.get("/test/director-check")
async def test_director_check(
    current_user: User = Depends(get_current_director_or_admin)
):
    """Test endpoint to verify director auth works."""
    return {
        "status": "success",
        "message": "Director or admin can access this",
        "username": current_user.username,
        "role": str(current_user.role),
        "school_id": current_user.school_id
    }


@router.post("/{teacher_id}/assign-classes", response_model=dict)
async def assign_classes(
    teacher_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_director: User = Depends(get_current_director)
):
    """
    Assign or reassign classes to a teacher (director only).
    
    Expected data:
    {
        "classes": ["5A", "5B", "6A"]
    }
    """
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    # Verify teacher is in current director's school
    if current_director.role == UserRole.director:
        if teacher.school_id != current_director.school_id:
            raise HTTPException(status_code=403, detail="Cannot manage teachers from other schools")
    
    if teacher.role != UserRole.teacher:
        raise HTTPException(status_code=400, detail="User is not a teacher")
    
    classes = data.get("classes", [])
    if not isinstance(classes, list):
        raise HTTPException(status_code=400, detail="classes must be a list")
    
    # Delete existing assignments
    db.query(TeacherClassAssignment).filter(
        TeacherClassAssignment.teacher_id == teacher_id
    ).delete()
    
    # Add new assignments
    assigned_classes = []
    for class_name in classes:
        class_name = str(class_name).strip()
        if class_name:
            assignment = TeacherClassAssignment(
                teacher_id=teacher_id,
                school_id=teacher.school_id,
                class_name=class_name
            )
            db.add(assignment)
            assigned_classes.append(class_name)
    
    db.commit()
    
    return {
        "message": "Classes assigned successfully",
        "teacher_id": teacher_id,
        "teacher_name": teacher.full_name,
        "assigned_classes": assigned_classes
    }


@router.get("/{teacher_id}/assigned-classes")
async def get_teacher_classes(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Get classes assigned to a specific teacher."""
    teacher = db.query(User).filter(User.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Teacher not found")
    
    assignments = db.query(TeacherClassAssignment).filter(
        TeacherClassAssignment.teacher_id == teacher_id
    ).all()
    
    classes = [a.class_name for a in assignments]
    
    return {
        "teacher_id": teacher_id,
        "teacher_name": teacher.full_name,
        "assigned_classes": classes
    }
# Force redeploy at Tue Nov 18 20:13:41 CET 2025
