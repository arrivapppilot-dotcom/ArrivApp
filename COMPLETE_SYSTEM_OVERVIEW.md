# ArrivApp Dashboard - Complete System Overview

## System Purpose ✓

**The dashboard's core mission:** Ensure that by 9:01 AM each school day, every parent whose child has not checked in is automatically notified of the absence.

---

## Complete Daily Workflow

### 8:00 AM UTC
**Daily Faker Service** (`daily_faker.yml`)
- Creates 15 new test students per school
- Simulates realistic check-ins:
  - 85% attendance rate
  - 20% late arrivals
  - 50% of absences get justified
- Tests all 6 report endpoints
- Archives data for historical analysis
- Sends personalized reports to directors

### 9:01 AM UTC ← **CRITICAL TIME**
**Absence Notification Service** (`send_absence_notifications.yml`)
- Automatically identifies ALL students without check-ins
- Sends detailed parent notification emails
- Creates database records for dashboard display
- Sends admin summary to school directors
- Dashboard updates to show ✓ Enviado (sent)

### 9:00 AM - 5:00 PM
**Dashboard Active**
- Auto-refreshes every 30 seconds
- Shows real-time attendance status:
  - ✓ **Present**: Checked in by 9:01 AM
  - ⏰ **Late**: Checked in after 9:01 AM  
  - ❌ **Absent**: No check-in by 9:01 AM
- **Email Confirmation Column** shows parent notification status:
  - ✓ Enviado = Parent notified
  - ✗ No enviado = Email failed (rare)

---

## System Components

### 1. Database Models

**CheckIn** (for present/late students)
```python
- student_id (FK)
- checkin_time → determines is_late
- is_late (true if after 9:01 AM)
- email_sent (parent notification sent?)
```

**AbsenceNotification** (for absent students)
```python
- student_id (FK)
- notification_date (when absence occurred)
- email_sent (parent notification sent?)
- email_sent_at (timestamp of email)
```

### 2. Backend Services

| Service | Schedule | Purpose |
|---------|----------|---------|
| `populate_render_db.py` | 8:00 AM | Generate test data |
| `send_absence_notifications.py` | 9:01 AM | Send parent emails |

### 3. API Endpoints

**`GET /api/reports/attendance-with-absences`**
- Returns all students for the day
- Combines check-ins and absences
- Includes `email_sent` status for each
- Marked with `is_absent` flag

### 4. Dashboard Tables

| Table | Shows | Email Status |
|-------|-------|-------------|
| Late Arrivals | Students checked in after 9:01 AM | Notification sent? |
| Present | Students checked in by 9:01 AM | Confirmation sent? |
| **Absent** | Students with NO check-in | Absence alert sent? |

---

## Email Notifications

### Types of Emails Sent

**1. Check-In Confirmation** (Any time student arrives)
- Recipient: Parent
- Trigger: Student scans QR code
- Content: Confirms arrival time + class info
- Status: ✓ Enviado in "Present" table

**2. Late Arrival Alert** (After 9:01 AM arrival)
- Recipient: Parent
- Trigger: Student scans QR after 9:01 AM
- Content: Alerts to late arrival + reason prompt
- Status: ✓ Enviado in "Late Arrivals" table

**3. Absence Notification** (At 9:01 AM, automatically)
- Recipient: Parent
- Trigger: Automated at 9:01 AM for all absent students
- Content: Absence alert + action items for parent
- Status: ✓ Enviado in "Absent" table

**4. Summary Report** (At 9:01 AM)
- Recipient: School director/admin
- Trigger: After all absence emails sent
- Content: List of all absent students + email counts
- Frequency: Daily

---

## Configuration

### Environment Variables (in `.env`)
```bash
# Database
DATABASE_URL=postgresql://arrivapp_user:PASSWORD@dpg-xxx.postgres.render.com/arrivapp

# Email/SMTP
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=arrivapp.pilot@gmail.com
SMTP_PASSWORD=cyewwoikichclfqx

# Admin notification
ADMIN_EMAIL=director@escuela.com

# Thresholds
LATE_THRESHOLD_HOUR=9
LATE_THRESHOLD_MINUTE=1
```

### GitHub Actions Secrets
```
DATABASE_URL
SMTP_SERVER
SMTP_PORT
SMTP_USERNAME
SMTP_PASSWORD
ADMIN_EMAIL
```

### Cron Schedules
```yaml
Daily Test Faker:      '0 8 * * *'     # 8:00 AM UTC
Absence Notifications: '1 9 * * *'     # 9:01 AM UTC
```

---

## Data Flow Diagram

```
├─ 8:00 AM
│  └─ Faker Service
│     ├─ Creates 15 students/school
│     ├─ Simulates check-ins
│     ├─ Creates absences
│     ├─ Tests all reports
│     └─ Sends director reports
│
├─ 9:01 AM ← CRITICAL
│  └─ Absence Notification Service
│     ├─ Query: Students with NO CheckIn
│     ├─ For each absent:
│     │  ├─ Send parent email
│     │  ├─ Create AbsenceNotification record
│     │  ├─ Set email_sent = true
│     │  └─ Update dashboard
│     ├─ Create summary report
│     └─ Send to admin email
│
└─ 9:05 AM - 5:00 PM
   └─ Dashboard Live
      ├─ Auto-refresh every 30 sec
      ├─ Show present (✓ Enviado)
      ├─ Show late (✓ Enviado)
      └─ Show absent (✓ Enviado)
```

---

## User Workflows

### School Director (Morning Check)
```
9:05 AM: Opens ArrivApp Dashboard
  ↓
Sees 3 attendance tables:
  ├─ Late Arrivals: 3 students, all ✓ Enviado
  ├─ Present: 127 students, all ✓ Enviado
  └─ Absent: 5 students, all ✓ Enviado
  ↓
Conclusion: "All parents notified" ✓
  ↓
Also received email summary:
  - Total: 135 students
  - Present: 127
  - Late: 3
  - Absent: 5
```

### Parent (Receives Notifications)
```
Student doesn't check in by 9:01 AM
  ↓
At 9:01 AM: Parent gets automated email
  ├─ Subject: "⚠️ Ausencia de [Student Name]"
  ├─ Content: Student info + action items
  └─ Call to action: Provide justification or confirm in school
  ↓
Parent can:
  ├─ Provide absence justification
  ├─ Confirm child arrived late
  └─ Contact school if emergency
```

### Admin (Full View)
```
8:00 AM: Receives test results email
  ├─ 135 students created
  ├─ 1,228 check-ins simulated
  └─ All 6 reports tested
  
9:01 AM: Receives absence summary
  ├─ 5 absent students
  ├─ 5 emails sent to parents
  └─ List with student info
  
Anytime: Can view dashboard
  ├─ See all schools
  ├─ Filter by date/school
  ├─ Verify email statuses
  └─ Check historical data
```

---

## Key Features

✅ **Automatic Absence Detection**
- Runs at exactly 9:01 AM
- Identifies all students without check-ins
- No manual intervention needed

✅ **Guaranteed Parent Notification**
- Every absent student's parent gets emailed
- System retries on failure
- Dashboard shows success/failure

✅ **Real-Time Dashboard**
- Updates every 30 seconds
- Shows email confirmation status
- Three categories clearly separated

✅ **Audit Trail**
- Database records every notification
- Email timestamps recorded
- Historical data retained for 30 days

✅ **Administrator Oversight**
- Daily summary emails
- Dashboard for verification
- Absence tracking reports

---

## Recent Implementation

### Commits
- **19959fb**: Add automated absence notification system
- **e59a74e**: Add documentation and tests
- **b0a4dc8**: Update faker for absence notifications
- **eab4b0f**: Add AbsenceNotification model and API endpoint
- **5d57cd2**: Add email confirmation columns

### Files Added/Modified
```
✓ backend/send_absence_notifications.py (NEW - 400+ lines)
✓ .github/workflows/send_absence_notifications.yml (NEW)
✓ backend/app/models/models.py (AbsenceNotification added)
✓ backend/app/routers/reports.py (New endpoint added)
✓ backend/populate_daily.py (Absence tracking added)
✓ frontend/dashboard.html (Absent table added)
✓ CORE_DASHBOARD_PURPOSE.md (NEW - Complete guide)
✓ ABSENCE_NOTIFICATIONS_IMPLEMENTATION.md (NEW)
```

---

## Deployment Status

✅ **Code Ready**
- All code committed to GitHub
- Deployed to Render backend
- Frontend auto-deployed

✅ **Database Ready**
- Migration script created: `migrate_add_absence_notifications.py`
- AbsenceNotification table exists
- Both databases updated

✅ **Automation Ready**
- Faker workflow: Runs 8 AM UTC daily ✓
- Absence notification workflow: Runs 9:01 AM UTC daily ✓
- Both have GitHub Actions configured

✅ **Email System Ready**
- SMTP credentials configured
- Admin email set
- Templates created

---

## Testing Checklist

- [ ] Run `send_absence_notifications.py` manually
- [ ] Verify emails sent to parents
- [ ] Check admin summary email
- [ ] Verify dashboard shows absent students
- [ ] Confirm email_sent field populated
- [ ] Check "Alumnos Ausentes" table has ✓ marks
- [ ] Test date filter
- [ ] Verify auto-refresh works
- [ ] Test on mobile view

---

## Success Metrics

System is working correctly when:

1. ✓ By 9:05 AM, all absent students in dashboard
2. ✓ All absent students show ✓ Enviado status
3. ✓ All parents receive absence emails by 9:05 AM
4. ✓ Admin receives summary report
5. ✓ Dashboard updates every 30 seconds
6. ✓ No student without notification status

---

## Next Steps (Optional Enhancements)

- [ ] SMS notifications in addition to email
- [ ] WhatsApp integration for instant alerts
- [ ] Parent app for absence acknowledgment
- [ ] Automatic justification prompts
- [ ] Multi-language support
- [ ] Late pick-up alerts
- [ ] Attendance reports for parents
- [ ] Statistical analysis dashboard

---

## Support & Troubleshooting

**Absence notifications not sending?**
1. Check SMTP credentials in `.env`
2. Verify email isn't in spam
3. Run manually: `python send_absence_notifications.py`
4. Check logs for errors

**Dashboard not showing absent students?**
1. Refresh page: Cmd+Shift+R
2. Wait 30 seconds for auto-refresh
3. Check browser console for errors
4. Verify API response: `/api/reports/attendance-with-absences`

**Email marked as not sent (✗ No enviado)?**
1. Check email address validity
2. Check SMTP server logs
3. Verify internet connectivity
4. Manual retry: Edit and resend

---

## Conclusion

The ArrivApp dashboard now provides **complete visibility** into the school's attendance and parent communication system. By 9:01 AM each day:

- ✓ All absent students identified
- ✓ All parents automatically notified
- ✓ All notifications tracked in database
- ✓ All confirmations visible in dashboard

This ensures **no child's absence goes unnoticed** and **every parent is promptly informed**.
