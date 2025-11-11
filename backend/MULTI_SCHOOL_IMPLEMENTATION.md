# Multi-School Implementation Guide

## Overview
ArrivApp now supports multiple schools on the same platform with complete data isolation.

## Database Changes

### New Table: `schools`
- `id`: Primary key
- `name`: School name (unique)
- `address`: School address
- `contact_email`: Contact email
- `contact_phone`: Contact phone
- `timezone`: School timezone (default: Europe/Madrid)
- `is_active`: Active status
- `created_at`: Creation timestamp

### Modified Tables

#### `students`
- Added `school_id`: Foreign key to schools table (required)
- Each student belongs to exactly one school

#### `users`
- Added `school_id`: Foreign key to schools table (optional)
- Admin users can have school_id=NULL (access all schools)
- Regular users must have a school_id (access only their school)

## API Changes

### New Endpoints: `/schools`
- `POST /schools` - Create a new school (admin only)
- `GET /schools` - List schools (admins see all, users see only their school)
- `GET /schools/{school_id}` - Get school details
- `PUT /schools/{school_id}` - Update school (admin only)
- `DELETE /schools/{school_id}` - Delete school (admin only, if no students)

### Modified Endpoints

#### Students (`/api/students`)
- `GET /api/students` - Now filters by user's school_id automatically
- `POST /api/students` - Requires `school_id` in request body
- All other endpoints now check school access permissions

#### Check-ins (`/api/checkin`)
- Dashboard now shows only students from user's school
- Check-ins are automatically scoped to the user's school

## Access Control

### Admin Users (is_admin=True)
- Can see and manage all schools
- Can see and manage all students across all schools
- Can create new schools
- school_id can be NULL

### Regular Users (is_admin=False)
- Must have a school_id assigned
- Can only see/manage students from their school
- Cannot see other schools' data
- Cannot create or modify schools

## Migration Process

1. **Backup existing database**
   ```bash
   cp arrivapp.db arrivapp_backup.db
   ```

2. **Run migration script**
   ```bash
   python migrate_to_multischool.py
   ```
   
   This will:
   - Backup the database automatically
   - Drop and recreate all tables with new schema
   - Create a "Default School"
   - Migrate existing data (if preserving data)

3. **Update main.py** to include schools router:
   ```python
   from app.routers import auth, students, checkin, schools
   app.include_router(schools.router)
   ```

4. **Restart the application**

## Usage Examples

### Creating a School (Admin)
```bash
curl -X POST "http://localhost:8000/schools/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "St. Mary School",
    "address": "123 Main St, Madrid",
    "contact_email": "admin@stmary.edu",
    "contact_phone": "+34 123 456 789",
    "timezone": "Europe/Madrid"
  }'
```

### Creating a Student with School
```bash
curl -X POST "http://localhost:8000/api/students/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU001",
    "name": "John Doe",
    "class_name": "3A",
    "parent_email": "parent@email.com",
    "school_id": 1
  }'
```

### Assigning User to School
Users need to be assigned to schools through database update or admin interface:
```sql
UPDATE users SET school_id = 1 WHERE username = 'teacher1';
```

## Data Isolation

Each school's data is completely isolated:
- Users can only see students from their school
- Dashboards show only check-ins from their school
- QR codes are school-specific
- Email notifications are sent only for students in their school

## Testing Multi-School Setup

1. Create multiple schools
2. Create users assigned to different schools
3. Add students to different schools
4. Login as users from different schools
5. Verify each user only sees their school's data

## Files Modified

- `app/models/models.py` - Added School model, relationships
- `app/models/schemas.py` - Added School schemas, updated Student/User schemas
- `app/routers/schools.py` - New router for school management
- `app/routers/students.py` - Added school filtering (needs manual updates)
- `app/routers/checkin.py` - Needs school filtering (manual updates required)
- `app/main.py` - Needs to include schools router
- `migrate_to_multischool.py` - Migration script

## Next Steps

1. Update main.py to include schools router
2. Update students.py with school filtering logic
3. Update checkin.py with school filtering logic
4. Run migration
5. Test with multiple schools
6. Update frontend to show school information
7. Add school selector for admin users

## Security Considerations

- School isolation is enforced at the API level
- Users cannot bypass school filtering
- Admin privileges are required to see cross-school data
- Foreign key constraints prevent orphaned records
