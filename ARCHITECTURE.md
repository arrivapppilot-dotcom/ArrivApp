# ArrivApp System Architecture

## 🏗️ System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         ArrivApp v2.0                        │
│              Sistema de Asistencia Escolar                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Check-in       │      │    Dashboard     │      │   Admin Panel   │
│   Station        │      │   (Teachers)     │      │  (Admin Only)   │
│  (Tablet/Kiosk)  │      │                  │      │                 │
│                  │      │                  │      │                 │
│  📱 QR Scanner   │      │  📊 Real-time    │      │  👥 Students    │
│  ✅ Check-in     │      │  📈 Stats        │      │  ⚙️  Settings   │
│  📸 Camera       │      │  🔍 Search       │      │  📥 Exports     │
└────────┬─────────┘      └────────┬─────────┘      └────────┬────────┘
         │                         │                         │
         │ HTTPS (no auth)         │  HTTPS + JWT           │  HTTPS + JWT (admin)
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      FastAPI Backend         │
                    │     (Python 3.11+)           │
                    ├──────────────────────────────┤
                    │  🔐 JWT Authentication       │
                    │  📡 REST API                 │
                    │  📧 Email Service            │
                    │  🎫 QR Code Generator        │
                    │  ⏰ Scheduler (Absent Check) │
                    └──────────┬───────────────────┘
                               │
                               ▼
                    ┌──────────────────────────────┐
                    │   PostgreSQL Database        │
                    │      (or SQLite)             │
                    ├──────────────────────────────┤
                    │  👤 Users                    │
                    │  👨‍🎓 Students                  │
                    │  ✅ Check-ins                │
                    │  ⚙️  Settings                │
                    └──────────────────────────────┘

                    ┌──────────────────────────────┐
                    │     External Services        │
                    ├──────────────────────────────┤
                    │  📧 SMTP (Gmail/SendGrid)    │
                    │  ☁️  Cloud Storage (Optional) │
                    └──────────────────────────────┘
```

## 📊 Data Flow

### 1. Check-in Flow
```
Student scans QR
      │
      ▼
Camera decodes QR → student_id
      │
      ▼
POST /api/checkin/scan?student_id=EST001
      │
      ▼
Backend validates student
      │
      ├─► Check if already checked in today
      ├─► Calculate if late (> 9:01)
      ├─► Create CheckIn record
      │
      ▼
Send email to parent (async)
      │
      ▼
Return success response
      │
      ▼
Display welcome message on kiosk
```

### 2. Dashboard Flow
```
Teacher opens dashboard
      │
      ▼
Login with credentials
      │
      ▼
Receive JWT token
      │
      ▼
Every 30 seconds:
  │
  ├─► GET /api/checkin/dashboard?date_filter=YYYY-MM-DD
  │   (with Authorization: Bearer TOKEN)
  │
  ▼
Backend aggregates data:
  ├─► Get all active students
  ├─► Get today's check-ins
  ├─► Calculate: present, absent, late
  │
  ▼
Return dashboard data
  │
  ▼
Frontend renders:
  ├─► Stats cards
  ├─► Check-in log table
  ├─► Late students table
  └─► Absent students list
```

### 3. Student Management Flow
```
Admin creates student
      │
      ▼
POST /api/students/
  {
    "student_id": "EST001",
    "name": "Juan Pérez",
    "class_name": "3ro A",
    "parent_email": "parent@email.com"
  }
      │
      ▼
Backend creates Student record
      │
      ▼
Generate unique QR code
  │
  ├─► QR contains: http://api.url/api/checkin/scan?student_id=EST001
  ├─► Save as PNG: qr_codes/student_EST001.png
  │
  ▼
Update student.qr_code_path
      │
      ▼
Return student with QR path
      │
      ▼
Admin downloads QR code
  GET /api/students/1/qr
      │
      ▼
Print and give to student
```

## 🔐 Security Model

### Authentication Layers

1. **Public Endpoints** (No auth required):
   - `POST /api/checkin/scan` - Check-in kiosk
   - `GET /health` - Health check

2. **Authenticated Endpoints** (JWT required):
   - `GET /api/checkin/dashboard` - Dashboard data
   - `GET /api/students/` - View students
   - `GET /api/students/{id}/qr` - Download QR

3. **Admin-Only Endpoints** (JWT + admin role):
   - `POST /api/students/` - Create student
   - `PUT /api/students/{id}` - Update student
   - `DELETE /api/students/{id}` - Delete student
   - `POST /api/auth/register` - Create user

### JWT Flow
```
1. Login:
   POST /api/auth/login
   { username, password }
   ↓
   Verify password (bcrypt)
   ↓
   Generate JWT (expires in 8 hours)
   ↓
   Return { access_token, token_type }

2. Protected Request:
   GET /api/students/
   Header: Authorization: Bearer <token>
   ↓
   Extract token from header
   ↓
   Decode and verify JWT
   ↓
   Check token expiration
   ↓
   Load user from database
   ↓
   Check user.is_active
   ↓
   Execute endpoint logic
```

## 📧 Email System

### Instant Parent Notification
```
Student checks in
      │
      ▼
Create CheckIn record
      │
      ▼
Trigger async email task
      │
      ▼
Format email:
  Subject: "ArrivApp: Juan Pérez ha llegado al cole"
  Body: "Juan Pérez (3ro A) registró entrada a las 08:45h"
      │
      ▼
Send via SMTP (Gmail/SendGrid)
      │
      ▼
Update CheckIn.email_sent = True
```

### Daily Absent Report (9:10 AM)
```
Scheduler triggers at 9:10 AM
      │
      ▼
Query all active students
      │
      ▼
Query today's check-ins
      │
      ▼
Calculate absent students:
  absent = all_students - checked_in_students
      │
      ▼
Format email with absent list
      │
      ▼
Send to ADMIN_EMAIL
```

## 🗄️ Database Schema

```sql
┌─────────────────────────────────────┐
│              users                  │
├─────────────────────────────────────┤
│ id (PK)                             │
│ email (unique)                      │
│ username (unique)                   │
│ hashed_password                     │
│ full_name                           │
│ is_active (boolean)                 │
│ is_admin (boolean)                  │
│ created_at                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│            students                 │
├─────────────────────────────────────┤
│ id (PK)                             │
│ student_id (unique)                 │
│ name                                │
│ class_name                          │
│ parent_email                        │
│ qr_code_path                        │
│ is_active (boolean)                 │
│ created_at                          │
└──────────────┬──────────────────────┘
               │
               │ 1:N
               │
┌──────────────▼──────────────────────┐
│            checkins                 │
├─────────────────────────────────────┤
│ id (PK)                             │
│ student_id (FK → students.id)       │
│ checkin_time                        │
│ checkout_time (nullable)            │
│ is_late (boolean)                   │
│ email_sent (boolean)                │
│ created_at                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│            settings                 │
├─────────────────────────────────────┤
│ id (PK)                             │
│ key (unique)                        │
│ value                               │
│ description                         │
│ updated_at                          │
└─────────────────────────────────────┘
```

## 🚀 Deployment Architecture

### Development
```
localhost:8000    → FastAPI backend
localhost:8080    → Frontend (Python HTTP server)
localhost:5432    → PostgreSQL (or SQLite file)
```

### Production (Railway/Render)
```
┌────────────────────────────────────────┐
│         Cloud Provider                 │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────────────────────┐     │
│  │   Web Service                │     │
│  │   - FastAPI app              │     │
│  │   - Uvicorn server           │     │
│  │   - Port: 8000               │     │
│  │   - Auto-deploy from Git     │     │
│  └──────────┬───────────────────┘     │
│             │                          │
│  ┌──────────▼───────────────────┐     │
│  │   PostgreSQL Database        │     │
│  │   - Managed instance         │     │
│  │   - Automatic backups        │     │
│  └──────────────────────────────┘     │
│                                        │
│  ┌──────────────────────────────┐     │
│  │   Static Files (Frontend)    │     │
│  │   - CDN or same server       │     │
│  └──────────────────────────────┘     │
│                                        │
└────────────────────────────────────────┘
         │
         ▼
   Custom Domain
   https://arrivapp.com
```

## 📱 Frontend Architecture

### Files Structure
```
frontend/
├── login.html          → Login page
├── dashboard.html      → Main dashboard
├── dashboard.js        → Dashboard logic
├── checkin.html        → Check-in kiosk
└── admin.html          → Admin panel (TODO)
```

### State Management
```javascript
// Local Storage
- arrivapp_token     → JWT token
- arrivapp_user      → Username

// Auto-refresh
- Dashboard: 30 seconds
- Clock: 1 second

// API calls with token
fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
})
```

## 🎯 Key Features Implementation

### Real-time Updates
- Dashboard polls API every 30 seconds
- WebSocket support (TODO for instant updates)

### QR Code System
- Unique QR per student
- Contains check-in URL with student_id
- Generated using python-qrcode library
- Stored in qr_codes/ directory

### Late Detection
- Configurable threshold (default: 9:01 AM)
- Calculated at check-in time
- Marked in database
- Highlighted in dashboard

### Email Reliability
- Async sending (doesn't block check-in)
- Retry logic (TODO)
- Failure tracking in CheckIn.email_sent
- Admin report for failed emails (TODO)

## 🔄 Future Enhancements

1. **Real-time with WebSocket**
   - Instant dashboard updates
   - Live check-in notifications

2. **Mobile Apps**
   - React Native for iOS/Android
   - Push notifications

3. **Advanced Analytics**
   - Attendance trends
   - Late patterns
   - Class comparisons

4. **Multi-school Support**
   - School management
   - Separate databases
   - White-label branding

5. **Check-out Tracking**
   - Exit scanning
   - Time spent in school
   - Pickup notifications

---

**Version**: 2.0.0  
**Last Updated**: November 2025  
**Author**: ArrivApp Team
