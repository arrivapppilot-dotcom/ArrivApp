# 🎯 CORE MISSION - Dashboard Purpose

## The Essential Truth

```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│   DASHBOARD CORE PURPOSE:                                 │
│                                                            │
│   By 9:01 AM each school day, verify that EVERY           │
│   student who has not checked in has their PARENT         │
│   automatically notified of the absence.                  │
│                                                            │
│   NO EXCEPTIONS. NO DELAYS. AUTOMATED.                    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## The Daily Schedule

```
TIMELINE                 SERVICE                STATUS
────────────────────────────────────────────────────────────
8:00 AM UTC    →  Daily Faker Service        ✓ TEST DATA
               →  Creates test students       ✓ TESTS REPORTS
               →  Simulates check-ins         ✓ SENDS REPORTS
                                             
9:01 AM UTC    →  ABSENCE NOTIFICATION     ⚠️ CRITICAL ⚠️
               →  Identifies all absent      ✓ EMAILS PARENTS
               →  Creates DB records         ✓ DASHBOARD UPDATES
                                             
9:00-17:00     →  Dashboard Live            ✓ AUTO-REFRESH
               →  Shows 3 attendance tables  ✓ EMAIL STATUS
               →  Real-time parent alerts   ✓ SCHOOL OVERSIGHT
────────────────────────────────────────────────────────────
```

---

## What the Dashboard Shows

### Three Attendance Tables

```
┌─────────────────────────────────────────────────────────────┐
│ PRESENT STUDENTS (Checked in by 9:01 AM)                  │
├─────────────────┬──────────┬─────────┬──────────────┬──────┤
│ Alumno          │ Entrada  │ Salida  │Email Padres  │Estado│
├─────────────────┼──────────┼─────────┼──────────────┼──────┤
│ Juan García     │ 08:30    │ 16:45   │ ✓ Enviado    │Pres. │
│ María López     │ 08:45    │ -       │ ✓ Enviado    │Pres. │
└─────────────────┴──────────┴─────────┴──────────────┴──────┘

┌─────────────────────────────────────────────────────────────┐
│ LATE ARRIVALS (Checked in after 9:01 AM)                  │
├─────────────────┬──────────┬─────────┬──────────────┬──────┤
│ Alumno          │ Entrada  │ Retraso │Email Padres  │Justi.│
├─────────────────┼──────────┼─────────┼──────────────┼──────┤
│ Pedro Sánchez   │ 09:15    │ 5 min   │ ✓ Enviado    │-     │
│ Ana Martínez    │ 09:45    │ 10 min  │ ✓ Enviado    │✓ Sí  │
└─────────────────┴──────────┴─────────┴──────────────┴──────┘

┌─────────────────────────────────────────────────────────────┐
│ ABSENT STUDENTS (NO check-in by 9:01 AM) ← CRITICAL       │
├─────────────────┬───────────┬─────────┬──────────────┬──────┤
│ Alumno          │ Clase     │ Colegio │Email Padres  │Estado│
├─────────────────┼───────────┼─────────┼──────────────┼──────┤
│ Carlos Ruiz     │ 2A        │San José │ ✓ Enviado    │Ausen.│
│ Sofia García    │ 3B        │San José │ ✓ Enviado    │Ausen.│
│ Luis Mendez     │ 1C        │Norte    │ ✓ Enviado    │Ausen.│
└─────────────────┴───────────┴─────────┴──────────────┴──────┘
```

**KEY COLUMN: "Email Padres"**
- ✓ Enviado = Parent was notified ← GOAL ACHIEVED
- ✗ No enviado = Email failed (rare) ← NEEDS ATTENTION

---

## Email Types

### 1️⃣ Check-In Confirmation
```
TO: Parent
WHEN: Any time student checks in (before 9:01 AM)
SUBJECT: ✓ {Student} ha llegado a la escuela

"Tu hijo/a {Name} ha registrado su entrada en 
{School} a las 08:30 en la clase {Class}."

DASHBOARD: Shows in "Present" table with ✓ Enviado
```

### 2️⃣ Late Arrival Alert  
```
TO: Parent
WHEN: Student checks in after 9:01 AM
SUBJECT: ⏰ {Student} ha llegado tarde

"Tu hijo/a {Name} ha registrado su entrada después 
de las 9:01 AM a las 09:15. Se registra como RETRASO."

DASHBOARD: Shows in "Late Arrivals" table with ✓ Enviado
```

### 3️⃣ ABSENCE NOTIFICATION ← AUTOMATED AT 9:01 AM
```
TO: Parent
WHEN: Automatically at 9:01 AM for all absent students
SUBJECT: ⚠️ Ausencia de {Student}

"Tu hijo/a {Name} NO HA LLEGADO a {School} antes 
de las 9:01 AM. Por favor:
  • Proporciona una justificación
  • Confirma que está en la escuela
  • Contacta con la escuela si hay emergencia"

DASHBOARD: Shows in "Absent" table with ✓ Enviado
```

### 4️⃣ Director Summary Report
```
TO: School Director/Admin
WHEN: At 9:01 AM (after all parent emails sent)
SUBJECT: 📊 Resumen de Ausencias - {Date}

Total Absent: 5
Emails Sent: 5
List of all absent students with parent emails

DASHBOARD: Director can see all 5 in "Absent" table
```

---

## The 9:01 AM Critical Moment

```
9:00:59 AM  - Last second for check-in (ON TIME)
    ↓
9:01:00 AM  - **CUTOFF TIME**
    ├─ Students checked in = PRESENT ✓
    └─ Students NOT checked in = ABSENT ❌
    ↓
9:01:01 AM  - Absence Notification Service ACTIVATES
    ├─ Scans database for absent students
    ├─ Finds: 5 students haven't checked in
    ├─ For each: SEND EMAIL TO PARENT
    ├─ Creates database record
    ├─ Sets email_sent = true
    └─ Dashboard updates live
    ↓
9:02:00 AM  - All 5 parents have emails
    ↓
9:05:00 AM  - Director opens dashboard
    │
    └─ Sees "Ausentes" table:
       - Carlos (✓ Enviado)
       - Sofia (✓ Enviado)
       - Luis (✓ Enviado)
       
    Director: "Todos los padres han sido notificados" ✓
```

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    GITHUB ACTIONS (Cloud)                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Daily Faker          Absence Notification                  │
│  8:00 AM UTC          9:01 AM UTC                           │
│  ────────────────     ────────────────                      │
│  - Create students    - Query absent students               │
│  - Simulate checkins  - Send parent emails                  │
│  - Test reports       - Create DB records                   │
│  - Send director      - Send admin summary                  │
│    reports                                                   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  RENDER (Prod)  │
                    │  ┌───────────┐  │
                    │  │PostgreSQL │  │
                    │  │  Database │  │
                    │  └───────────┘  │
                    │  ┌───────────┐  │
                    │  │  Backend  │  │
                    │  │  (FastAPI)│  │
                    │  └───────────┘  │
                    └─────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  Frontend HTML  │
                    │  ┌───────────┐  │
                    │  │Dashboard  │  │
                    │  │(3 Tables) │  │
                    │  │Auto-Ref   │  │
                    │  │30 sec     │  │
                    │  └───────────┘  │
                    └─────────────────┘
```

---

## Success: What You'll See

### ✅ System Working Correctly

**At 9:05 AM, Dashboard Shows:**

```
PRESENT STUDENTS: 127 ✓ Enviado each
LATE ARRIVALS: 3 ✓ Enviado each
ABSENT: 5 ✓ Enviado each

TOTAL: 135 students
CONFIRMED: 135 parents have emails ✓
STATUS: ALL NOTIFICATIONS SENT ✓
```

**Director Email (also at 9:01 AM):**
```
📊 RESUMEN DE AUSENCIAS
Ausentes: 5
Emails Enviados: 5
✓ Carlos Ruiz - email@... ✓ Enviado
✓ Sofia García - email@... ✓ Enviado  
✓ Luis Mendez - email@... ✓ Enviado
[... etc ...]
```

**Parent Inbox (contains 3 emails):**
1. ✓ Check-in confirmation (if arrived by 9:01)
2. OR ⏰ Late arrival alert (if arrived after 9:01)
3. OR ⚠️ Absence notification (if absent all day)

---

## Failure: What to Fix

### ❌ Problem: Dashboard shows ✗ No enviado

**Cause:** Email failed to send
**Fix:** Check SMTP credentials in `.env`
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=arrivapp.pilot@gmail.com
SMTP_PASSWORD=<app-password>
```

### ❌ Problem: Absent table is empty at 9:05 AM

**Cause:** Service didn't run
**Fix:** 
1. Check GitHub Actions logs
2. Verify cron: `1 9 * * *` is correct
3. Run manually: `python send_absence_notifications.py`

### ❌ Problem: Missing some absent students

**Cause:** Database sync issue
**Fix:**
1. Verify DATABASE_URL is correct
2. Check timezone (UTC vs local)
3. Test API: `/api/reports/attendance-with-absences`

---

## The Bottom Line

```
┌──────────────────────────────────────────────────┐
│                                                  │
│  ✓ Student late to school?                      │
│    → Parent gets email at check-in time        │
│                                                  │
│  ✓ Student absent all day?                      │
│    → Parent gets email AUTOMATICALLY at 9:01 AM│
│                                                  │
│  ✓ Director wants confirmation?                 │
│    → Dashboard shows email status (✓ sent)     │
│                                                  │
│  NO ONE GOES UNNOTICED. AUTOMATED. ALWAYS.     │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

## Files You Need to Know

```
CRITICAL FILES:
├── backend/send_absence_notifications.py  (The 9:01 AM service)
├── .github/workflows/send_absence_notifications.yml (The trigger)
├── backend/app/models/models.py  (AbsenceNotification table)
├── backend/app/routers/reports.py (API /attendance-with-absences)
├── frontend/dashboard.html  (Three tables shown here)
└── CORE_DASHBOARD_PURPOSE.md (This purpose, in detail)

DOCUMENTATION:
├── COMPLETE_SYSTEM_OVERVIEW.md
├── ABSENCE_NOTIFICATIONS_IMPLEMENTATION.md
├── CORE_DASHBOARD_PURPOSE.md ← READ THIS FIRST
└── QUICKSTART.md
```

---

## One-Minute Understanding

1. **Goal:** Every absent student's parent gets an email by 9:01 AM
2. **How:** Automated service runs at 9:01 AM, scans for students with no check-in, sends emails
3. **Proof:** Dashboard shows email status (✓ = success) for all students
4. **Owner:** School director sees real-time dashboard with all confirmations

**That's it. That's the entire purpose of this system.**

---

**Deployed:** ✓ GitHub  
**Live:** ✓ Render Backend  
**Working:** ✓ GitHub Actions (8 AM + 9:01 AM daily)  
**Ready:** ✓ Production use  
