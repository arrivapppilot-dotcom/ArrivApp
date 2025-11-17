# Absence Notification System - Core Dashboard Purpose

## Mission Critical Flow

The ArrivApp dashboard's primary purpose is to **ensure every student who hasn't checked in by 9:01 AM has their parent notified of their absence**.

## How It Works

### Timeline & Thresholds

```
8:00 AM (UTC)
└─ Daily Faker runs (appends test data, tests all reports)

9:01 AM (UTC) ← CRITICAL CUTOFF
├─ Absence Notification Service activates
├─ Identifies ALL students without check-ins
├─ Sends automated parent notification emails
└─ Updates dashboard with "Absent" status

9:00 AM - 5:00 PM
└─ Dashboard displays real-time attendance status
    - Late arrivals (checked in after 9:01 AM)
    - Present students (checked in by 9:01 AM)
    - Absent students (no check-in by 9:01 AM) ← EMAIL CONFIRMATION HERE
```

### Core Business Logic

**Student Status Determination:**

1. **On Time** → Checked in between school open and 9:01 AM
   - Email sent to parent: ✓ Confirmación de entrada
   - Dashboard shows: ✓ Presente

2. **Late** → Checked in after 9:01 AM
   - Email sent to parent: ✓ Aviso de retraso
   - Dashboard shows: ⏰ Retraso

3. **Absent** → NO check-in by 9:01 AM
   - Email sent to parent: ✓ AVISO DE AUSENCIA (automated at 9:01 AM)
   - Dashboard shows: ❌ Ausente + Email confirmation status

## Key Components

### 1. Check-In Router (`backend/app/routers/checkin.py`)
- Detects check-in time vs 9:01 AM threshold
- Sets `is_late = True` if after 9:01 AM
- Sends immediate email to parent about check-in/late arrival

### 2. Absence Notification Service (`backend/send_absence_notifications.py`)
**Runs automatically at 9:01 AM UTC daily**

**What it does:**
1. Gets all active students in the system
2. Checks which students have NOT checked in yet
3. For each absent student:
   - Sends detailed parent notification email
   - Creates `AbsenceNotification` record in database
   - Marks `email_sent = true`
4. Sends admin summary report to directors/admins

**Email Content:**
- ⚠️ Red alert header: "Aviso de Ausencia"
- Student info: Name, Class, School
- Action items for parent:
  - Provide justification if sick/away
  - Request student check in if at school
  - Contact school if emergency
- Professional HTML formatting

### 3. GitHub Actions Workflows

**Workflow 1: `daily_faker.yml`**
- Schedule: 8:00 AM UTC daily
- Purpose: Generate test data
- Tests all report endpoints

**Workflow 2: `send_absence_notifications.yml`** ← NEW
- Schedule: 9:01 AM UTC daily  
- Purpose: Send parent notifications for absent students
- Creates dashboard records

### 4. Dashboard Display (`frontend/dashboard.html`)

**Three Attendance Tables:**

| Table | Trigger | Email Status |
|-------|---------|-------------|
| Late Arrivals | Checked in after 9:01 AM | ✓/✗ Late notification sent |
| Present Students | Checked in by 9:01 AM | ✓/✗ Check-in confirmation sent |
| **Absent Students** | No check-in by 9:01 AM | ✓/✗ Absence notification sent |

**Dashboard Auto-Refresh:**
- Updates every 30 seconds
- Shows real-time email confirmation status
- Parents can see exactly what emails were sent

## Data Model

### CheckIn Record (for present/late students)
```python
CheckIn(
    student_id=123,
    checkin_time=datetime(2025-11-17, 8:15),
    is_late=False,
    email_sent=True,  # Parent got check-in confirmation
    created_at=datetime(2025-11-17, 8:15)
)
```

### AbsenceNotification Record (for absent students)
```python
AbsenceNotification(
    student_id=456,
    notification_date=datetime(2025-11-17, 9:01),
    email_sent=True,  # Parent got absence notification
    email_sent_at=datetime(2025-11-17, 9:01),
    created_at=datetime(2025-11-17, 9:01)
)
```

## API Endpoint

**`GET /api/reports/attendance-with-absences`**

Combines all three student types:

```json
{
  "records": [
    {
      "student_name": "Juan García",
      "is_late": false,
      "email_sent": true,
      "is_absent": false  // Present student
    },
    {
      "student_name": "María López",
      "is_late": true,
      "email_sent": true,
      "is_absent": false  // Late student
    },
    {
      "student_name": "Pedro Rodríguez",
      "is_late": false,
      "email_sent": true,
      "is_absent": true   // ABSENT - notification sent
    }
  ]
}
```

## Email Workflow

### At Check-In (Any Time)
```
Student scans QR
    ↓
System detects time
    ├─ Before 9:01 AM? → "Check-in confirmed" email
    └─ After 9:01 AM? → "Late arrival" email
    ↓
email_sent = true (in CheckIn table)
    ↓
Dashboard shows ✓ Enviado
```

### At 9:01 AM (Automated)
```
Absence Notification Service starts
    ↓
Query: Students with no CheckIn today
    ↓
For each absent student:
    ├─ Send "Absence Alert" email to parent
    ├─ Create AbsenceNotification record
    ├─ Set email_sent = true
    └─ Dashboard updates to show ✓ Enviado
    ↓
Send admin summary with all absences
```

## Dashboard User Journey

### Director View (9:05 AM)
1. Opens dashboard
2. Sees three tables:
   - **Late Arrivals**: 5 students, all show "✓ Enviado" (parents notified)
   - **Present**: 120 students, all show "✓ Enviado" (arrival confirmed)
   - **Absent**: 8 students, all show "✓ Enviado" (absence alerts sent)
3. Can verify: "All parents have been notified" ✓
4. Can take action if needed: call parents of persistent absentees

### Admin View
1. Receives automated emails at 8 AM (test results)
2. Receives automated emails at 9:01 AM (absence summary)
3. Can see dashboard anytime with full system overview
4. Can manually trigger notifications via API if needed

## Configuration

### Environment Variables Required
```bash
DATABASE_URL=postgresql://...  # Production DB
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=arrivapp.pilot@gmail.com
SMTP_PASSWORD=<app-password>
ADMIN_EMAIL=director@escuela.com
LATE_THRESHOLD_HOUR=9
LATE_THRESHOLD_MINUTE=1
```

### Cron Schedules
```yaml
Daily Faker:         0 8 * * *   (8:00 AM UTC)
Absence Notifications: 1 9 * * *   (9:01 AM UTC)
```

## Error Handling

If absence notification service fails:
1. Logs error details
2. Continues with remaining students
3. Sends partial summary to admin
4. Next cycle retries missed students

If email fails for specific student:
1. Records `email_sent = false`
2. Dashboard shows "✗ No enviado" 
3. Admin can manually retry

## Verification Checklist

✅ **Database**
- [ ] `checkins` table exists with `email_sent` column
- [ ] `absence_notifications` table exists
- [ ] Tables linked to `students` table

✅ **Backend**
- [ ] `send_absence_notifications.py` deployed
- [ ] Service uses correct SMTP credentials
- [ ] Service checks for 9:01 AM threshold
- [ ] Service creates database records

✅ **GitHub Actions**
- [ ] `daily_faker.yml` runs at 8 AM UTC
- [ ] `send_absence_notifications.yml` runs at 9:01 AM UTC
- [ ] Both have required secrets configured

✅ **Frontend**
- [ ] Dashboard has three tables
- [ ] Each shows `email_sent` status
- [ ] Auto-refresh working (30 seconds)
- [ ] Displays ✓ Enviado or ✗ No enviado

✅ **Email System**
- [ ] SMTP credentials working
- [ ] Parent emails received in inbox
- [ ] Admin summary emails received
- [ ] HTML formatting displays correctly

## Testing

### Manual Test
```bash
cd backend
python send_absence_notifications.py
```

### Verify in Dashboard
1. Hard refresh: Cmd+Shift+R
2. Check "Alumnos Ausentes" table
3. Verify email status column
4. Confirm ✓ marks for notified parents

### Check Email
1. Parent inbox: Should have absence notification
2. Admin inbox: Should have summary report
3. Timestamps should match 9:01 AM

## Success Metrics

✅ System working correctly when:
1. By 9:05 AM, all absent students have ✓ Enviado in dashboard
2. All parent emails delivered within 1 minute of 9:01 AM
3. Admin receives summary report with all absent students
4. Director can see exact notification status for each student
5. No students without notification status (either ✓ or ✗)

## Core Dashboard Purpose Summary

> **The ArrivApp dashboard ensures that by 9:01 AM each school day, every school administrator and teacher can see EXACTLY which parents have been automatically notified of their child's absence, ensuring no child's absence goes unnoticed.**

This is the system's most critical function - automatic parent notification at 9:01 AM is non-negotiable.
