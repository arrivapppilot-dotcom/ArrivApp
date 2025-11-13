from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from typing import List
import pandas as pd
import io
from app.core.database import get_db
from app.core.deps import get_current_user, get_current_admin_user, get_current_school_user, get_current_director_or_admin
from app.models.models import Student, User, UserRole, School
from app.models.schemas import StudentCreate, StudentUpdate, Student as StudentSchema, StudentWithSchool
from app.services.qr_service import generate_qr_code, delete_qr_code

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("/", response_model=List[StudentWithSchool])
async def get_students(
    skip: int = 0,
    limit: int = 10000,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_school_user)
):
    """Get students filtered by user's school (unless admin)."""
    query = db.query(Student).options(joinedload(Student.school))
    
    # Filter by school for non-admin users
    if current_user.role != UserRole.admin:
        if not current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User must be associated with a school"
            )
        query = query.filter(Student.school_id == current_user.school_id)
    
    students = query.offset(skip).limit(limit).all()
    return students


@router.get("/{student_id}", response_model=StudentWithSchool)
async def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_school_user)
):
    """Get a specific student by ID (filtered by school)."""
    student = db.query(Student).options(joinedload(Student.school)).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if user has access to this student's school
    if current_user.role != UserRole.admin:
        if student.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this student"
            )
    
    return student


@router.post("/", response_model=StudentSchema, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_director_or_admin)
):
    """Create a new student (director or admin only)."""
    # Check if student ID already exists
    if db.query(Student).filter(Student.student_id == student_data.student_id).first():
        raise HTTPException(status_code=400, detail="Student ID already exists")
    
    # For directors, ensure they're adding to their own school
    if current_user.role == UserRole.director:
        if student_data.school_id != current_user.school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Directors can only add students to their own school"
            )
    
    # Create student
    db_student = Student(
        student_id=student_data.student_id,
        name=student_data.name,
        class_name=student_data.class_name,
        parent_email=student_data.parent_email,
        school_id=student_data.school_id,
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    
    # Generate QR code
    qr_path = generate_qr_code(db_student)
    db_student.qr_code_path = qr_path
    db.commit()
    db.refresh(db_student)
    
    return db_student


@router.put("/{student_id}", response_model=StudentSchema)
async def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_director_or_admin)
):
    """Update a student (director or admin only)."""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update fields
    if student_data.name is not None:
        db_student.name = student_data.name
    if student_data.class_name is not None:
        db_student.class_name = student_data.class_name
    if student_data.parent_email is not None:
        db_student.parent_email = student_data.parent_email
    if student_data.is_active is not None:
        db_student.is_active = student_data.is_active
    
    db.commit()
    db.refresh(db_student)
    return db_student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Delete a student (admin only) - soft delete."""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Soft delete
    db_student.is_active = False
    db.commit()
    
    return None


@router.get("/{student_id}/qr")
async def get_student_qr(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get student QR code - generates on-the-fly if not found."""
    from fastapi.responses import StreamingResponse
    import os
    import io
    import qrcode
    
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Create QR code data - the URL that will be scanned
    qr_data = f"https://arrivapp-backend.onrender.com/api/checkin/scan?student_id={student.student_id}"
    
    # Generate QR code in memory
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    content = img_bytes.getvalue()
    
    return StreamingResponse(
        iter([content]),
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename=qr_student_{student_id}.png",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@router.post("/{student_id}/regenerate-qr", response_model=StudentSchema)
async def regenerate_qr(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Regenerate QR code for a student (admin only)."""
    db_student = db.query(Student).filter(Student.id == student_id).first()
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Delete old QR code
    if db_student.qr_code_path:
        delete_qr_code(db_student.qr_code_path)
    
    # Generate new QR code
    qr_path = generate_qr_code(db_student)
    db_student.qr_code_path = qr_path
    db.commit()
    db.refresh(db_student)
    
    return db_student


@router.post("/upload-excel", status_code=status.HTTP_201_CREATED)
@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_students_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Upload students via Excel file (admin only).
    
    Expected columns: student_id, name, class (or class_name), school_id, parent_email
    """
    # Validate file type
    if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an Excel file (.xlsx, .xls) or CSV (.csv)"
        )
    
    try:
        # Read file
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
        
        # Validate required columns (support both 'class' and 'class_name')
        required_columns = ['student_id', 'name', 'school_id', 'parent_email']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        # Check for class column (either 'class' or 'class_name')
        has_class = 'class' in df.columns or 'class_name' in df.columns
        if not has_class:
            missing_columns.append('class or class_name')
        
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}"
            )
        
        # Standardize column name
        if 'class' in df.columns and 'class_name' not in df.columns:
            df['class_name'] = df['class']
        
        # Process students
        created_students = []
        errors = []
        skipped = []
        
        for index, row in df.iterrows():
            try:
                student_id = str(row['student_id']).strip()
                name = str(row['name']).strip()
                class_name = str(row['class_name']).strip()
                school_id = int(row['school_id'])
                parent_email = str(row['parent_email']).strip().lower()
                
                # Validate required fields
                if not all([student_id, name, class_name, parent_email]):
                    errors.append(f"Row {index + 2}: Missing required fields")
                    continue
                
                # Validate school exists
                school = db.query(School).filter(School.id == school_id).first()
                if not school:
                    errors.append(f"Row {index + 2}: School ID {school_id} not found")
                    continue
                
                # Check if student already exists
                existing = db.query(Student).filter(Student.student_id == student_id).first()
                if existing:
                    skipped.append(f"Row {index + 2}: Student ID '{student_id}' already exists")
                    continue
                
                # Create student
                db_student = Student(
                    student_id=student_id,
                    name=name,
                    class_name=class_name,
                    school_id=school_id,
                    parent_email=parent_email,
                )
                db.add(db_student)
                db.commit()
                db.refresh(db_student)
                
                # Generate QR code
                qr_path = generate_qr_code(db_student)
                db_student.qr_code_path = qr_path
                db.commit()
                
                created_students.append(db_student.student_id)
                
            except Exception as e:
                errors.append(f"Row {index + 2}: {str(e)}")
                continue
        
        return {
            "success": True,
            "created": len(created_students),
            "skipped": len(skipped),
            "errors": len(errors),
            "details": {
                "created_ids": created_students,
                "skipped_reasons": skipped,
                "error_messages": errors
            }
        }
        
    except pd.errors.EmptyDataError:
        raise HTTPException(status_code=400, detail="Excel file is empty")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
