# 🔗 ArrivApp ↔ Alexia Integration Guide

## Executive Summary

**YES, ArrivApp can integrate with Alexia via API.** This document provides a complete integration strategy for schools using both systems.

---

## 1. Integration Architecture

### Use Case: Alexia as Primary Platform + ArrivApp as Attendance Specialist

```
┌─────────────────────────────────────────────────────────┐
│              Alexia (Education Suite)                    │
│  (Grades, Curriculum, Billing, Academic Management)    │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ↓                         ↑
    ┌─────────────────────────────────────┐
    │  API GATEWAY / SYNC SERVICE         │
    │  (Middleware/Adapter Layer)         │
    │                                     │
    │  • Authentication Sync              │
    │  • Student Data Sync                │
    │  • Attendance Data Export           │
    │  • Real-time Webhook Updates        │
    └─────────────────────────────────────┘
        ↑                         │
        │                         ↓
┌──────────────────────────────────────────┐
│    ArrivApp (Attendance Specialist)      │
│  (QR Check-in, Absence Alerts, Reports)│
└──────────────────────────────────────────┘
```

---

## 2. Available API Endpoints for Integration

### **Authentication (Alexia Sync)**
```
POST   /api/auth/login              → Get JWT token for API calls
GET    /api/auth/me                 → Verify token & current user
```

### **Students Management (Bi-directional)**
```
GET    /api/students                → List all students (filter by school, class)
GET    /api/students/{id}           → Get specific student
POST   /api/students                → Create student
PUT    /api/students/{id}           → Update student
GET    /api/students/{id}/qr        → Download QR code image
```

### **Attendance Data (Primary Integration Point)**
```
GET    /api/reports/attendance-history         → All check-ins with timestamps
GET    /api/reports/attendance-with-absences   → Combined present/late/absent
GET    /api/reports/statistics                 → Attendance stats (daily/weekly/monthly)
GET    /api/reports/tardiness-analysis         → Late arrival patterns
GET    /api/reports/historical-analytics       → Trends & chronic absenteeism
GET    /api/reports/export-pdf                 → Download PDF report
```

### **Justifications (Alexia → ArrivApp)**
```
POST   /api/justifications          → Parents submit absence reasons
GET    /api/justifications          → List all justifications
PUT    /api/justifications/{id}     → Approve/reject justification
```

### **Schools Management**
```
GET    /api/schools                 → List all schools
POST   /api/schools                 → Create new school
GET    /api/schools/{id}            → Get school details
PUT    /api/schools/{id}            → Update school
```

### **Users Management**
```
GET    /api/users                   → List all users (admin only)
POST   /api/users                   → Create new user
PUT    /api/users/{id}              → Update user
PUT    /api/users/{id}/reset-password → Change password
```

---

## 3. Integration Scenarios

### **Scenario A: Read-Only Integration (Alexia → ArrivApp)**

**Use Case**: Alexia imports ArrivApp attendance data for reporting

```
┌─────────────────┐
│    Alexia       │
│  Dashboard      │
│                 │
│ "Show me        │
│  attendance"    │
└────────┬────────┘
         │
         │ API Call
         ↓
    GET /api/reports/attendance-with-absences?school_id=1&start_date=2025-11-17
         │
         │ Response
         ↓
┌───────────────────────────────────────┐
│ {                                     │
│   "records": [                        │
│     {                                 │
│       "student_name": "Juan",         │
│       "class_name": "5A",             │
│       "checkin_time": "2025-11-17...", │
│       "is_late": true,                │
│       "email_sent": true,             │
│       "is_absent": false              │
│     },                                │
│     {                                 │
│       "student_name": "María",        │
│       "is_absent": true,              │
│       "email_sent": true              │
│     }                                 │
│   ]                                   │
│ }                                     │
└───────────────────────────────────────┘
```

**Implementation**: 
- Create scheduled job in Alexia (daily/hourly)
- Call ArrivApp API with authentication
- Parse attendance data
- Update Alexia's attendance records
- Display in Alexia dashboard

---

### **Scenario B: Student Sync (Bi-directional)**

**Use Case**: Keep student lists synchronized

```
FLOW 1: New student created in Alexia
  Alexia → (Webhook) → ArrivApp
    POST /api/students
    {
      "name": "Carlos García",
      "email": "carlos@example.com",
      "class_name": "3B",
      "school_id": 1,
      "parent_email": "padre@example.com"
    }
    ↓
  ArrivApp creates student + generates QR
    ↓
  Webhook response confirms creation

FLOW 2: Student info updated in Alexia
  Alexia → (Webhook) → ArrivApp
    PUT /api/students/{id}
    {
      "name": "Carlos García Pérez",
      "class_name": "4A",
      "parent_email": "padre_nuevo@example.com"
    }
    ↓
  ArrivApp updates student record
```

---

### **Scenario C: Justifications (ArrivApp → Alexia)**

**Use Case**: Parent submits absence justification in ArrivApp, syncs to Alexia

```
FLOW:
1. Parent views absence notification email from ArrivApp
2. Parent clicks "Justify Absence" link
3. Opens ArrivApp justification form
   POST /api/justifications
   {
     "student_id": 123,
     "absence_date": "2025-11-17",
     "reason": "Doctor appointment",
     "document_url": "s3://..."
   }
   ↓
4. ArrivApp stores justification
5. Alexia polls or receives webhook
   GET /api/justifications?student_id=123&status=pending
   ↓
6. Alexia displays in Attendance module
7. Director approves in Alexia
   PUT /api/justifications/{id}
   {"status": "approved"}
   ↓
8. ArrivApp updates justification status
```

---

### **Scenario D: Real-time Webhooks (Advanced)**

**Use Case**: Instant updates without polling

```
ArrivApp sends webhook when:
  • Student checks in
  • Absence notification sent
  • Tardiness detected
  • Justification submitted

Webhook URL (configured in ArrivApp):
  POST https://alexia.educaria.com/webhooks/arrivapp

Payload:
  {
    "event": "checkin",
    "timestamp": "2025-11-17T09:15:00Z",
    "student_id": 123,
    "student_name": "Juan García",
    "school_id": 1,
    "is_late": false,
    "checkin_time": "2025-11-17T09:15:00Z"
  }

Alexia receives → Updates immediately → Shows in real-time dashboard
```

---

## 4. Step-by-Step Integration Implementation

### **Phase 1: Setup (1-2 hours)**

**Step 1.1**: Get ArrivApp API Credentials
```bash
# Contact ArrivApp admin to generate API key
# Or use standard JWT authentication

API_KEY=your_api_key_here
API_BASE_URL=https://arrivapp-backend.onrender.com
```

**Step 1.2**: Configure CORS in ArrivApp
```bash
# Add Alexia domain to allowed origins in .env
ALLOWED_ORIGINS=https://alexia.educaria.com

# ArrivApp backend will allow requests from Alexia
```

**Step 1.3**: Document API for Alexia Developers
```
Authentication: Bearer {JWT_TOKEN}
Base URL: https://arrivapp-backend.onrender.com/api
Content-Type: application/json
```

---

### **Phase 2: Student Data Sync (2-3 hours)**

**Step 2.1**: Create data mapping
```
Alexia Field → ArrivApp Field
─────────────────────────────
student_id   → student_id
name         → name
email        → email
class        → class_name
school_id    → school_id
parent_email → parent_email
document_id  → internal_id (custom field)
```

**Step 2.2**: Implement sync job
```python
# Pseudocode for Alexia integration service

class ArrivAppSync:
    def sync_students_to_arrivapp(self):
        """Push new/updated students from Alexia to ArrivApp"""
        
        # 1. Get list of students from Alexia
        alexia_students = self.get_students_from_alexia()
        
        # 2. For each student, check if exists in ArrivApp
        for student in alexia_students:
            try:
                # Check if already exists
                response = self.api_call(
                    'GET',
                    f'/api/students/{student["id"]}'
                )
                
                if response.status_code == 404:
                    # Create new student
                    self.api_call(
                        'POST',
                        '/api/students',
                        {
                            'name': student['name'],
                            'email': student['email'],
                            'class_name': student['class'],
                            'school_id': student['school_id'],
                            'parent_email': student['parent_email']
                        }
                    )
                else:
                    # Update existing student
                    self.api_call(
                        'PUT',
                        f'/api/students/{student["id"]}',
                        {
                            'name': student['name'],
                            'class_name': student['class']
                        }
                    )
            except Exception as e:
                logger.error(f"Error syncing student {student['id']}: {e}")
    
    def get_attendance_from_arrivapp(self, school_id, date):
        """Pull attendance data from ArrivApp"""
        
        response = self.api_call(
            'GET',
            '/api/reports/attendance-with-absences',
            params={
                'school_id': school_id,
                'start_date': date,
                'end_date': date
            }
        )
        
        return response.json()['records']
    
    def api_call(self, method, endpoint, data=None, params=None):
        """Make API call to ArrivApp"""
        
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.base_url}{endpoint}"
        
        return requests.request(
            method,
            url,
            json=data,
            params=params,
            headers=headers
        )
```

**Step 2.3**: Test sync
```bash
# Test with one school first
curl -X GET https://arrivapp-backend.onrender.com/api/reports/attendance-with-absences \
  -H "Authorization: Bearer {TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"school_id": 1, "start_date": "2025-11-17"}'
```

---

### **Phase 3: Attendance Data Integration (3-4 hours)**

**Step 3.1**: Create daily sync job
```python
# Schedule this to run daily at 9:15 AM
def sync_attendance_daily():
    schools = alexia_db.query(School).all()
    
    for school in schools:
        # Get today's attendance from ArrivApp
        attendance = arrivapp.get_attendance_from_arrivapp(
            school_id=school.id,
            date=datetime.now().date()
        )
        
        # Update Alexia's attendance module
        for record in attendance:
            update_alexia_attendance(
                student_id=record['student_id'],
                checkin_time=record['checkin_time'],
                is_late=record['is_late'],
                is_absent=record['is_absent'],
                email_sent=record['email_sent']
            )
```

**Step 3.2**: Implement real-time updates (optional)
```python
# Webhook endpoint in Alexia
@app.post("/webhooks/arrivapp")
async def receive_arrivapp_webhook(payload: dict):
    """Receive real-time updates from ArrivApp"""
    
    event_type = payload['event']
    student_id = payload['student_id']
    
    if event_type == 'checkin':
        # Update attendance immediately
        update_attendance(
            student_id=student_id,
            checkin_time=payload['checkin_time'],
            is_late=payload['is_late']
        )
        
        # Trigger notifications if needed
        send_notification_to_director(
            f"Student {payload['student_name']} checked in at {payload['checkin_time']}"
        )
    
    elif event_type == 'absence':
        # Flag as absent
        mark_as_absent(student_id, payload['absence_date'])
    
    return {"status": "received"}
```

---

### **Phase 4: Testing & Validation (2-3 hours)**

**Test Cases**:
```
✓ Test 1: Login and authentication
  curl -X POST https://arrivapp-backend.onrender.com/api/auth/login \
    -H "Content-Type: application/json" \
    -d '{
      "username": "admin",
      "password": "madrid123"
    }'

✓ Test 2: Retrieve students
  curl -X GET https://arrivapp-backend.onrender.com/api/students \
    -H "Authorization: Bearer {TOKEN}"

✓ Test 3: Retrieve attendance
  curl -X GET "https://arrivapp-backend.onrender.com/api/reports/attendance-with-absences?school_id=1&start_date=2025-11-17" \
    -H "Authorization: Bearer {TOKEN}"

✓ Test 4: Create new student in ArrivApp
  curl -X POST https://arrivapp-backend.onrender.com/api/students \
    -H "Authorization: Bearer {TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "Test Student",
      "email": "test@school.com",
      "class_name": "5A",
      "school_id": 1,
      "parent_email": "parent@school.com"
    }'

✓ Test 5: Compare data in both systems
  Verify student lists match
  Verify attendance records sync
  Verify absence notifications correlate
```

---

## 5. API Response Examples

### **Get Attendance Data**
```bash
GET /api/reports/attendance-with-absences?school_id=1&start_date=2025-11-17&class_name=5A
```

**Response**:
```json
{
  "records": [
    {
      "id": 1001,
      "student_id": 123,
      "student_name": "Juan García",
      "class_name": "5A",
      "school_id": 1,
      "school_name": "Colegio Central",
      "checkin_time": "2025-11-17T08:45:00Z",
      "checkout_time": "2025-11-17T16:30:00Z",
      "is_late": false,
      "email_sent": true,
      "is_absent": false
    },
    {
      "id": null,
      "student_id": 124,
      "student_name": "María López",
      "class_name": "5A",
      "school_id": 1,
      "school_name": "Colegio Central",
      "checkin_time": null,
      "is_late": null,
      "email_sent": true,
      "is_absent": true
    }
  ],
  "total": 2
}
```

### **Get Attendance Statistics**
```bash
GET /api/reports/statistics?period=monthly&school_id=1&class_name=5A
```

**Response**:
```json
{
  "total_attendance": 450,
  "present": 420,
  "late": 30,
  "checked_out": 410,
  "attendance_rate": 93.33,
  "late_rate": 6.67,
  "daily_breakdown": [
    {
      "date": "2025-11-17",
      "present": 28,
      "late": 2,
      "absent": 0
    }
  ]
}
```

### **Get Tardiness Analysis**
```bash
GET /api/reports/tardiness-analysis?school_id=1&class_name=5A
```

**Response**:
```json
{
  "students_analysis": [
    {
      "student_id": 123,
      "student_name": "Juan García",
      "total_attendance": 20,
      "late_count": 3,
      "late_percentage": 15.0,
      "late_dates": ["2025-11-10", "2025-11-12", "2025-11-15"]
    }
  ],
  "overall_late_rate": 12.5
}
```

---

## 6. Data Formats & Schemas

### **Student Schema** (for creation/updates)
```json
{
  "name": "string (required)",
  "email": "string (required, email format)",
  "class_name": "string (required)",
  "school_id": "integer (required)",
  "parent_email": "string (required, email format)",
  "is_active": "boolean (default: true)",
  "internal_id": "string (optional, for external reference)"
}
```

### **Check-in Record Schema**
```json
{
  "id": "integer",
  "student_id": "integer",
  "student_name": "string",
  "class_name": "string",
  "school_id": "integer",
  "school_name": "string",
  "checkin_time": "ISO 8601 datetime",
  "checkout_time": "ISO 8601 datetime or null",
  "is_late": "boolean",
  "is_absent": "boolean",
  "email_sent": "boolean",
  "email_sent_at": "ISO 8601 datetime or null"
}
```

### **Justification Schema**
```json
{
  "id": "integer",
  "student_id": "integer",
  "absence_date": "date",
  "reason": "string",
  "status": "pending|approved|rejected",
  "created_at": "ISO 8601 datetime",
  "submitted_by_parent": "boolean",
  "document_url": "string (optional)"
}
```

---

## 7. Authentication & Security

### **JWT Token Method** (Recommended)
```bash
# 1. Get token
POST /api/auth/login
{
  "username": "admin",
  "password": "madrid123"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}

# 2. Use token in subsequent requests
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Security Considerations**
```
✓ Always use HTTPS (not HTTP)
✓ Store tokens securely (environment variables)
✓ Rotate tokens regularly
✓ Use firewall rules to limit API access
✓ Implement rate limiting
✓ Log all API calls
✓ Validate all incoming data
✓ Use IP whitelisting for Alexia servers
```

---

## 8. Error Handling & Troubleshooting

### **Common Errors**

```
401 Unauthorized
→ Check token is valid and not expired
→ Verify credentials

403 Forbidden
→ Check user has required role (admin/director)
→ Verify school_id ownership

404 Not Found
→ Verify resource exists
→ Check ID parameters

400 Bad Request
→ Validate JSON format
→ Check required fields
→ Verify data types

500 Internal Server Error
→ Check server logs
→ Verify database connection
→ Contact support
```

### **Debugging Steps**
```bash
# 1. Test connectivity
curl -X GET https://arrivapp-backend.onrender.com/api/schools \
  -H "Authorization: Bearer {TOKEN}" \
  -v

# 2. Check response headers
# 3. Verify JWT token expiration
# 4. Check server logs at https://dashboard.render.com

# 5. Test with simple curl first before Alexia integration
```

---

## 9. Cost & Deployment Considerations

### **Infrastructure**
```
ArrivApp Backend: $20-50/month (Render)
Database: $15/month (PostgreSQL on Render)
Email Service: Free (Gmail) or $10/month (SendGrid)
Total: ~$50-75/month

Alexia: €500-5000+/month depending on tier
```

### **Integration Cost**
```
Development: 20-30 hours (one-time)
Testing: 5-10 hours (one-time)
Maintenance: 2-5 hours/month
Support: Included
```

---

## 10. Roadmap & Future Enhancements

### **Short-term** (Next 30 days)
- ✅ Read-only attendance data integration
- ✅ Student list sync
- ✅ Basic webhook support

### **Medium-term** (Next 3-6 months)
- 📋 Two-way justification sync
- 📋 Real-time webhook updates
- 📋 Advanced filtering & analytics
- 📋 Scheduled report generation

### **Long-term** (6+ months)
- 🚀 Native Alexia plugin
- 🚀 Single sign-on (SSO) integration
- 🚀 Unified mobile app
- 🚀 Machine learning for attendance patterns

---

## 11. Support & Contact

### **ArrivApp API Support**
```
Repository: https://github.com/arrivapppilot-dotcom/ArrivApp
Issues: https://github.com/arrivapppilot-dotcom/ArrivApp/issues
Email: support@arrivapp.com (TBD)
Documentation: /docs endpoint in API
```

### **Integration Checklist**
```
☐ Get API credentials from ArrivApp
☐ Set up CORS/firewall rules
☐ Configure API base URL
☐ Test authentication
☐ Map data schemas
☐ Implement student sync
☐ Implement attendance sync
☐ Set up error handling
☐ Test all endpoints
☐ Load testing
☐ Go live with monitoring
☐ Document for Alexia admins
```

---

## Conclusion

**ArrivApp and Alexia can work together beautifully:**

- ✅ ArrivApp handles **attendance** (fast, specialized, automated)
- ✅ Alexia handles **academics** (comprehensive, integrated, professional)
- ✅ Integration is **straightforward** via REST API
- ✅ No data loss, **bi-directional** sync possible
- ✅ Can be done in **2-3 weeks** with proper planning

**The perfect stack for modern schools:**

```
Attendance Management    →  ArrivApp (fast, free, specialized)
Academic Management     →  Alexia (comprehensive, supported)
Unified Reporting       →  Both systems (complementary data)
```

---

**Version**: 1.0  
**Date**: November 17, 2025  
**Status**: Ready for Implementation
