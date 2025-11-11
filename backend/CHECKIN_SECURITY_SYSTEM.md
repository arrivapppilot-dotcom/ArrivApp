# Check-In/Check-Out Security System

## Overview
ArrivApp implements a comprehensive security system to prevent accidental scans, system abuse, and data confusion in the check-in/check-out process.

## Security Rules

### 1. Duplicate Check-In Prevention (10-minute window)
**Problem:** Student accidentally scans QR code twice in quick succession  
**Solution:** System blocks second scan within 10 minutes of initial check-in

**Example:**
- 8:45 AM: Student scans → ✅ Check-in successful
- 8:48 AM: Student scans again → ⚠️ **BLOCKED** - "Ya registró entrada hace 3 minutos"

**Technical Details:**
- Time window: 10 minutes
- Error code: `duplicate_scan`
- Response includes: `minutes_ago`, `minutes_remaining`

**User Experience:**
- Yellow warning message displayed
- Shows how long ago check-in occurred
- Explains need to wait 10 minutes for checkout
- Display duration: 5 seconds (longer than normal)

---

### 2. Minimum Stay Time (30-minute rule)
**Problem:** Student checks in then immediately checks out (accidental scan or leaving early)  
**Solution:** System requires minimum 30 minutes between check-in and check-out

**Example:**
- 8:45 AM: Student scans → ✅ Check-in successful
- 9:00 AM: Student scans → ⚠️ **BLOCKED** - "Debes permanecer al menos 30 minutos"
- 9:20 AM: Student scans → ✅ Check-out successful

**Technical Details:**
- Minimum duration: 30 minutes
- Error code: `too_early_checkout`
- Response includes: `minutes_since_checkin`, `minutes_remaining`

**User Experience:**
- Yellow warning message with clock emoji
- Shows current time in school
- Shows how many more minutes required
- Display duration: 5 seconds

---

### 3. Already Completed Prevention
**Problem:** Student tries to scan after completing both check-in and check-out  
**Solution:** System informs that today's cycle is complete

**Example:**
- 8:45 AM: Check-in ✅
- 3:30 PM: Check-out ✅
- 4:00 PM: Scan again → ℹ️ "Ya completó entrada y salida hoy"

**Technical Details:**
- Error code: `already_completed`
- Response includes: `checkin_time`, `checkout_time`

**User Experience:**
- Blue info message
- Shows both check-in and check-out times
- Clear indication day is complete
- Display duration: 3 seconds

---

## System Flow

### Normal Daily Flow

```
┌─────────────────────────────────────────────────┐
│                    NEW DAY                       │
│            No records for today                  │
└─────────────────────────────────────────────────┘
                        │
                        ▼
                  ┌─────────┐
                  │ 1st SCAN │
                  └─────────┘
                        │
                        ▼
              ✅ CHECK-IN SUCCESSFUL
              • Record created
              • Email sent to parent
              • Late flag set if after 9:01 AM
                        │
                   [Wait 30+ min]
                        │
                        ▼
                  ┌─────────┐
                  │ 2nd SCAN │
                  └─────────┘
                        │
                        ▼
              ✅ CHECK-OUT SUCCESSFUL
              • Checkout time recorded
              • Email sent with summary
              • Duration calculated
                        │
                        ▼
              ┌──────────────────┐
              │   DAY COMPLETE   │
              │  Further scans   │
              │ show info only   │
              └──────────────────┘
```

### Error Cases

```
CHECK-IN PHASE (before 10 minutes):
  Scan #1 → ✅ Check-in
  Scan #2 → ⚠️ DUPLICATE_SCAN error
  Wait → 10 min passes
  Scan #3 → ⚠️ TOO_EARLY_CHECKOUT (still < 30 min)
  Wait → 30 min passes
  Scan #4 → ✅ Check-out

CHECK-OUT PHASE (after both complete):
  Scan #N → ℹ️ ALREADY_COMPLETED info
```

---

## Time Thresholds

| Rule | Duration | Purpose |
|------|----------|---------|
| **Duplicate Check-in Window** | 10 minutes | Prevent accidental double scans |
| **Minimum Stay Time** | 30 minutes | Prevent immediate checkout |
| **Late Threshold** | 9:01 AM | Determine if arrival is late |
| **Daily Reset** | Midnight | Start fresh each day |

---

## Email Notifications

### Check-In Email
**Sent when:** First scan of the day  
**Recipients:** Parent email  
**Includes:**
- Student name and class
- Check-in time
- On-time or late status
- Welcome message

### Check-Out Email
**Sent when:** Valid checkout (30+ min after check-in)  
**Recipients:** Parent email  
**Includes:**
- Student name and class
- Check-in time
- Check-out time
- Total duration (hours and minutes)
- Goodbye message

### No Email Cases
- Duplicate scans (blocked by security)
- Too-early checkout attempts (blocked)
- Already completed attempts (info only)

---

## Edge Cases Handled

### 1. Student Forgets to Check Out
**What happens:** Record shows check-in only  
**Dashboard display:** "En el colegio" (still in school)  
**Next day:** New check-in allowed (daily reset at midnight)

### 2. Multiple Scans During Error Windows
**What happens:** Each scan shows appropriate error  
**System behavior:** No database changes during error states  
**User feedback:** Clear messages about timing

### 3. Student Leaves Early (< 30 min)
**What happens:** Checkout blocked with clear message  
**Override:** Not available (enforced security rule)  
**Alternative:** Manual adjustment by admin if needed

### 4. Scan at Exactly 10 or 30 Minutes
**Behavior:** Uses `<` comparison, so:
- 9.9 minutes → Duplicate error
- 10.0 minutes → Too-early checkout error
- 29.9 minutes → Too-early checkout error
- 30.0 minutes → ✅ Checkout allowed

---

## Configuration

Located in: `app/core/config.py`

```python
# Late arrival threshold
LATE_THRESHOLD_HOUR = 9
LATE_THRESHOLD_MINUTE = 1

# Security thresholds (hardcoded in checkin.py)
DUPLICATE_SCAN_WINDOW = 10  # minutes
MINIMUM_STAY_TIME = 30      # minutes
```

---

## Testing Scenarios

### Test Case 1: Normal Flow
```
1. Scan at 8:45 AM → ✅ Check-in
2. Wait 31 minutes
3. Scan at 9:16 AM → ✅ Check-out
4. Verify email sent twice
```

### Test Case 2: Duplicate Scan
```
1. Scan at 8:45 AM → ✅ Check-in
2. Scan at 8:47 AM → ⚠️ Duplicate (2 min ago)
3. Wait 10 minutes
4. Scan at 8:57 AM → ⚠️ Too early (12 min)
```

### Test Case 3: Quick Checkout Attempt
```
1. Scan at 8:45 AM → ✅ Check-in
2. Scan at 9:00 AM → ⚠️ Too early (15 min, need 15 more)
3. Scan at 9:15 AM → ✅ Check-out (30 min elapsed)
```

### Test Case 4: Post-Completion Scan
```
1. Complete full cycle (check-in + check-out)
2. Scan again → ℹ️ Already completed
3. Shows both times
```

---

## Frontend Implementation

### File: `frontend/checkin.html`

**Status Types:**
- `success` (green) - Valid check-in or check-out
- `warning` (yellow) - Security violations (duplicate, too early)
- `info` (blue) - Already completed
- `error` (red) - Student not found or system error

**Display Durations:**
- Success: 3 seconds
- Warning: 5 seconds (longer to read details)
- Info: 3 seconds
- Error: 3 seconds

**Message Format:**
```javascript
// Warning example
showStatus('warning', '⚠️', 'Escaneo Duplicado!', 
    `${name} ya registró entrada hace ${min} minutos\n\nEspera ${remaining} minutos más`);
```

---

## API Response Structure

### Check-In Success
```json
{
  "message": "¡Bienvenido/a, Juan Pérez!",
  "action": "checkin",
  "student_name": "Juan Pérez",
  "class": "3º Primaria",
  "checkin_time": "2025-11-10T08:45:00",
  "is_late": false,
  "email_sent": true
}
```

### Check-Out Success
```json
{
  "message": "¡Hasta luego, Juan Pérez!",
  "action": "checkout",
  "student_name": "Juan Pérez",
  "class": "3º Primaria",
  "checkin_time": "2025-11-10T08:45:00",
  "checkout_time": "2025-11-10T15:30:00",
  "duration_minutes": 405
}
```

### Duplicate Scan Error
```json
{
  "error": "duplicate_scan",
  "message": "⚠️ Juan Pérez ya ha registrado entrada hace 3 minutos",
  "student_name": "Juan Pérez",
  "checkin_time": "2025-11-10T08:45:00",
  "minutes_ago": 3
}
```

### Too Early Checkout Error
```json
{
  "error": "too_early_checkout",
  "message": "⏱️ Debe esperar al menos 30 minutos...",
  "student_name": "Juan Pérez",
  "checkin_time": "2025-11-10T08:45:00",
  "minutes_since_checkin": 15,
  "minutes_remaining": 15
}
```

### Already Completed
```json
{
  "error": "already_completed",
  "message": "✅ Juan Pérez ya completó entrada y salida hoy...",
  "already_completed": true,
  "student_name": "Juan Pérez",
  "checkin_time": "2025-11-10T08:45:00",
  "checkout_time": "2025-11-10T15:30:00"
}
```

---

## Benefits

✅ **Prevents Accidental Double Scans** - 10-minute protection window  
✅ **Ensures Meaningful Stays** - 30-minute minimum prevents immediate checkout  
✅ **Clear User Feedback** - Specific error messages with countdowns  
✅ **Protects Data Integrity** - No duplicate or invalid records  
✅ **Parent Confidence** - Only valid actions trigger notifications  
✅ **Audit Trail** - Every scan attempt logged with appropriate response  

---

## Future Enhancements (Optional)

1. **Admin Override** - Allow manual checkout before 30 minutes with reason
2. **Configurable Thresholds** - Move 10-min and 30-min to settings
3. **Early Dismissal Flag** - Track checkouts before 12:00 PM
4. **Multiple Checkouts** - Support re-entry same day (e.g., field trips)
5. **Grace Period** - Allow 5-minute window after check-in for correction
6. **Statistics** - Track how often security rules are triggered

---

Last Updated: November 10, 2025  
Version: 1.0
