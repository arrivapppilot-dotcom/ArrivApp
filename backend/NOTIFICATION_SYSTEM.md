# Email Notification System - ArrivApp

## Overview
ArrivApp has a comprehensive email notification system that keeps parents, schools, and admins informed about student attendance.

## Notification Types

### 1. ✅ On-Time Check-In Notification
**Trigger:** Student checks in before 9:01 AM  
**Recipients:** Parent email (from student record)  
**Content:**
- Confirmation message
- Check-in time
- Student name and class

**Example:**
```
Subject: ✅ ArrivApp: María García ha llegado al cole

¡Hola!

Buenas noticias.

María García (3º A) ha registrado su entrada en el colegio a las 08:45h.

Gracias por participar en el programa piloto de ArrivApp.
```

### 2. ⚠️ Late Check-In Notification
**Trigger:** Student checks in at or after 9:01 AM  
**Recipients:** Parent email (from student record)  
**Content:**
- Warning about late arrival
- Check-in time
- Request to justify if necessary

**Example:**
```
Subject: ⚠️ ArrivApp: María García ha llegado tarde al cole

¡Hola!

Te informamos que María García (3º A) ha registrado su entrada en el colegio a las 09:15h.

⚠️ AVISO: La entrada se ha registrado después del horario establecido (9:01h).

Si hay alguna razón justificada para el retraso, por favor contacta con el colegio.
```

### 3. 📋 Absent Student Report (Daily at 9:10 AM)
**Trigger:** Automated daily at 9:10 AM  
**Recipients:**
- Parent of each absent student
- School contact email
- All admin users

#### 3a. Parent Notification
**Content:**
- Alert that student hasn't checked in
- Date and time of report
- School contact information

**Example:**
```
Subject: ⚠️ ArrivApp: María García no ha registrado su entrada

Hola,

Te informamos que María García (3º A) NO ha registrado su entrada en el colegio hoy.

Fecha: 10/11/2025
Hora del reporte: 09:10

Si tu hijo/a está en el colegio, por favor contacta con la administración.
Si está ausente, te agradeceríamos que informes al colegio.

Colegio: Colegio San José
Contacto: admin@sanjose.edu
```

#### 3b. School Notification
**Content:**
- List of all absent students for that school
- Parent contact information
- Total count

**Example:**
```
Subject: 📋 ArrivApp - Alumnos Ausentes (Colegio San José)

Hola,

Reporte de ausencias para Colegio San José:

Fecha: 10/11/2025
Hora del reporte: 09:10

Alumnos que NO han registrado entrada:

• María García (3º A) - Email padre: padre@email.com
• Juan Pérez (2º B) - Email padre: madre@email.com

Total: 2 alumnos ausentes

Por favor, verifica estas ausencias y contacta a los padres si es necesario.
```

#### 3c. Admin Notification
**Content:**
- List of absent students by school
- Student IDs and parent contacts
- Detailed breakdown

**Example:**
```
Subject: 📋 ArrivApp Admin - Ausencias en Colegio San José

Hola Admin,

Reporte automático de ausencias:

Colegio: Colegio San José
Fecha: 10/11/2025
Hora: 09:10

Alumnos ausentes (2):

• María García (3º A)
  Padre: padre@email.com
  ID Alumno: MAR2024001

• Juan Pérez (2º B)
  Padre: madre@email.com
  ID Alumno: JUA2024002

Total: 2 ausentes en Colegio San José
```

## Configuration

### Email Settings (.env file)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=arrivapp.pilot@gmail.com
SMTP_PASSWORD=cbpt zlax eclu oxsx
FROM_EMAIL=arrivapp.pilot@gmail.com
FROM_NAME=ArrivApp
ADMIN_EMAIL=arrivapp.pilot@gmail.com
```

### Timing Configuration
- **Late Threshold:** 9:01 AM (`LATE_THRESHOLD_HOUR=9`, `LATE_THRESHOLD_MINUTE=1`)
- **Absent Check Time:** 9:10 AM (`CHECK_ABSENT_TIME=09:10`)

## Technical Implementation

### Services
1. **email_service.py** - Handles SMTP email sending
   - `send_email()` - Core email function
   - `send_checkin_notification()` - Check-in emails (on-time and late)

2. **scheduler.py** - Background task scheduler
   - Uses `APScheduler` for daily tasks
   - `check_absent_students()` - Runs daily at 9:10 AM
   - Groups students by school
   - Sends separate emails to parents, schools, and admins

### Database Fields
- `Student.parent_email` - Required for parent notifications
- `School.contact_email` - Optional school contact
- `CheckIn.is_late` - Automatically set based on time
- `CheckIn.email_sent` - Tracks if notification was sent

## Testing

### Test Individual Check-In Notifications
Use the check-in station at `http://localhost:8080/checkin.html` and scan a student QR code.

### Test Absent Notifications Manually
```bash
cd backend
source venv/bin/activate
python test_absent_notifications.py
```

This will immediately run the absent check without waiting for 9:10 AM.

## Scheduler Status

The scheduler automatically starts when the FastAPI application starts (via `lifespan` event in `main.py`).

**To verify scheduler is running:**
Check the console logs when starting the backend:
```
🚀 Scheduler started. Absent check will run daily at 09:10
```

## Email Delivery Status

All email attempts are logged:
- ✅ Success: `✉️ Email sent to...`
- ❌ Failure: `❌ Failed to send email...`

Check the backend console or logs for delivery status.

## Troubleshooting

### Emails Not Sending
1. Check SMTP credentials in `.env`
2. Verify Gmail app password is correct
3. Check firewall/network allows SMTP port 587
4. Review logs for specific error messages

### Scheduler Not Running
1. Ensure `start_scheduler()` is called in `main.py`
2. Check `CHECK_ABSENT_TIME` format is "HH:MM"
3. Verify timezone settings match server timezone

### Wrong Recipients
1. Verify `Student.parent_email` is correct
2. Check `School.contact_email` is set
3. Ensure admin users have `role = UserRole.admin`

## Multi-School Support

The system handles multiple schools:
- Absent reports are grouped by school
- Each school receives only their students' report
- Admins receive reports for ALL schools
- Parents only receive info about their own children

## Future Enhancements

Potential improvements:
- SMS notifications
- WhatsApp integration
- Customizable notification times per school
- Weekly summary reports
- Attendance trend alerts
