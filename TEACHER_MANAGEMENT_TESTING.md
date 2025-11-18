# Teacher Management System - Testing Guide

## Overview
Directors can now create teacher profiles and assign them to one or more classes.

## Features Implemented

### Backend
- ✅ `TeacherClassAssignment` model to track teacher-class mappings
- ✅ `POST /api/users/create-teacher` - Create new teacher with optional class assignment
- ✅ `GET /api/users/classes` - List available classes in school
- ✅ `POST /api/users/{teacher_id}/assign-classes` - Reassign classes to teacher
- ✅ `GET /api/users/{teacher_id}/assigned-classes` - Get teacher's assigned classes

### Frontend
- ✅ "👨‍🏫 Crear Profesor" button visible only to directors/admins
- ✅ Modal form with fields:
  - Full Name (required)
  - Email (required, validated)
  - Password (required, min 6 chars)
  - Classes (multi-select dropdown)
- ✅ Show school name in form
- ✅ Class list dynamically loaded from database

## Step-by-Step Testing

### 1. Login as Director
1. Go to: https://arrivapp-frontend.onrender.com/login.html
2. Login with director credentials (or create one via admin panel)
3. Navigate to Users page: https://arrivapp-frontend.onrender.com/users.html

### 2. Verify UI
- ✅ You should see a purple button "👨‍🏫 Crear Profesor"
- ✅ If you see it, you have director/admin role
- ✅ Other buttons visible: "🍽️ Crear Comedor", "➕ Añadir Usuario"

### 3. Create a Teacher
1. Click "👨‍🏫 Crear Profesor" button
2. Fill in the modal:
   - **Nombre Completo:** John Doe
   - **Email:** john.doe@school.com
   - **Contraseña:** secure123
   - **Clases:** Select "5A" and "5B" (Ctrl+Click or Cmd+Click for multiple)
3. Click "Crear Profesor"
4. Should see success message with teacher details

### 4. Verify in Database
```bash
# Connect to local database
cd backend
python -c "
from app.core.database import SessionLocal
from app.models.models import User, TeacherClassAssignment

db = SessionLocal()

# Find teacher
teacher = db.query(User).filter(User.email == 'john.doe@school.com').first()
if teacher:
    print(f'✅ Teacher found: {teacher.full_name}')
    print(f'   ID: {teacher.id}')
    print(f'   Role: {teacher.role}')
    print(f'   School: {teacher.school_id}')
    
    # Check assigned classes
    assignments = db.query(TeacherClassAssignment).filter(
        TeacherClassAssignment.teacher_id == teacher.id
    ).all()
    
    classes = [a.class_name for a in assignments]
    print(f'   Assigned Classes: {classes}')
else:
    print('❌ Teacher not found')

db.close()
"
```

### 5. Teacher Login
1. Go to login page
2. Login with teacher credentials:
   - Email: john.doe@school.com
   - Password: secure123
3. Should redirect to dashboard
4. Should be able to see attendance for assigned classes (5A, 5B)

### 6. Reassign Classes
1. As director, go to users.html
2. In user table, find the teacher you created
3. Click action menu (if available) or use API directly:

```bash
# Using curl to reassign classes
curl -X POST https://arrivapp-backend.onrender.com/api/users/123/assign-classes \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"classes": ["6A", "6B", "6C"]}'
```

### 7. List Teachers' Classes
```bash
curl https://arrivapp-backend.onrender.com/api/users/123/assigned-classes \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Expected Responses

### Create Teacher - Success (200)
```json
{
  "message": "Teacher created successfully",
  "teacher_id": 123,
  "username": "john.doe",
  "email": "john.doe@school.com",
  "full_name": "John Doe",
  "school": "Colegio San José",
  "assigned_classes": ["5A", "5B"]
}
```

### Create Teacher - Errors
- Missing email: `{"detail": "Valid email is required"}`
- Email exists: `{"detail": "Email already exists"}`
- Password too short: `{"detail": "Password must be at least 6 characters"}`
- Not a director: `{"detail": "Only directors and admins can manage teachers"}`

### Get Classes - Success (200)
```json
{
  "classes": ["1A", "1B", "2A", "2B", "3A", "3B", "4A", "4B", "5A", "5B", "6A"],
  "school_id": 1
}
```

### Assign Classes - Success (200)
```json
{
  "message": "Classes assigned successfully",
  "teacher_id": 123,
  "teacher_name": "John Doe",
  "assigned_classes": ["6A", "6B", "6C"]
}
```

## Permission Matrix

| Action | Admin | Director | Teacher | Comedor |
|--------|-------|----------|---------|---------|
| Create Teacher | ✅ | ✅ (own school) | ❌ | ❌ |
| List Classes | ✅ | ✅ (own school) | ❌ | ❌ |
| Assign Classes | ✅ | ✅ (own school) | ❌ | ❌ |
| View Teachers | ✅ | ✅ (own school) | ❌ | ❌ |

## Troubleshooting

### "Create Teacher" button not showing
- Make sure you're logged in as a director or admin
- Check browser console (F12) for errors
- Hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

### Classes dropdown is empty
- Check that students exist with assigned `class_name` values
- Verify students have `is_active = True` in database
- Run populate script to generate test data

### "Only directors and admins can create teachers"
- Your role is not director or admin
- Contact an admin to change your role or verify login

### Teacher can't see their assigned classes
- Verify class assignments exist in database
- Check that teacher's `school_id` matches the classes' `school_id`
- Refresh page or clear browser cache

## Database Schema

### TeacherClassAssignment Table
```
id (PK)
teacher_id (FK → users.id)
school_id (FK → schools.id)
class_name (String) - e.g., "5A"
assigned_at (DateTime)
```

### Users Table (Updated)
- Added relationship: `assigned_classes` → TeacherClassAssignment

## Deployment Notes

- Render will auto-deploy on git push
- New database migrations handled by SQLAlchemy ORM
- TeacherClassAssignment table created automatically on first run
- Backward compatible - existing data unaffected

---

**Commits Related:**
- `6634c53` - Add teacher-class mapping model and backend endpoints
- `90f4b6b` - Add director UI for creating teachers

**Test Date:** 2025-11-18
**Status:** Ready for testing
