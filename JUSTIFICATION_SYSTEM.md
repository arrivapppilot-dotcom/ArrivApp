# Justification/Excuse System Implementation

## Overview
The justification system allows parents to report absences in advance and track excused vs unexcused absences.

## Features Implemented

### Backend API
✅ New database model `Justification` with:
- student_id
- justification_type (absence, tardiness, early_dismissal)
- date
- reason
- status (pending, approved, rejected)
- submitted_by (parent email)
- reviewed_by (staff user ID)
- notes (staff notes)

✅ API Endpoints (`/api/justifications/`):
- POST `/` - Parents can submit justifications (must match parent email)
- GET `/` - Staff can view all justifications (filtered by school)
- GET `/{id}` - View specific justification
- PUT `/{id}` - Staff can approve/reject and add notes
- DELETE `/{id}` - Staff can delete justifications
- GET `/student/{student_id}/pending` - View pending justifications for a student

### Security
- Parents can only submit for their own children (email verification)
- Staff can only view/manage justifications for their school
- Admins can access all justifications

## Database Migration
Run this SQL to create the table (auto-created on next server start):

```sql
CREATE TABLE justifications (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    justification_type VARCHAR NOT NULL,
    date TIMESTAMP NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR NOT NULL DEFAULT 'pending',
    submitted_by VARCHAR NOT NULL,
    submitted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id),
    reviewed_at TIMESTAMP,
    notes TEXT
);
```

## Next Steps (Frontend)
1. Create a justification submission form for parents
2. Add a staff interface to review/approve justifications
3. Show justified absences differently in reports
4. Add email notifications when justifications are approved/rejected

## Example Usage

### Parent submits absence:
```json
POST /api/justifications/
{
  "student_id": 1,
  "justification_type": "absence",
  "date": "2025-11-11T00:00:00",
  "reason": "Medical appointment",
  "submitted_by": "parent@email.com"
}
```

### Staff approves:
```json
PUT /api/justifications/123
{
  "status": "approved",
  "notes": "Valid medical excuse provided"
}
```
