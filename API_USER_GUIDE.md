# ArrivApp API User Guide

## Overview

ArrivApp is a multi-school attendance management system with a comprehensive REST API. This guide explains how to retrieve and manage data using the ArrivApp API.

**Base URL:** `https://arrivapp-backend.onrender.com`

---

## Table of Contents

1. [Authentication](#authentication)
2. [Core Concepts](#core-concepts)
3. [Endpoints Overview](#endpoints-overview)
4. [Getting Started](#getting-started)
5. [Common Use Cases](#common-use-cases)
6. [Response Examples](#response-examples)
7. [Error Handling](#error-handling)

---

## Authentication

### Login & Get Access Token

All API requests require a JWT (JSON Web Token) authentication token, except for public endpoints.

**Endpoint:** `POST /api/auth/login`

**Request:**
```bash
curl -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "password": "your-password"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "full_name": "Administrator",
    "role": "admin",
    "school_id": null
  }
}
```

### Using the Token

Include the token in all subsequent requests:

```bash
curl -X GET https://arrivapp-backend.onrender.com/api/students/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### User Roles & Permissions

| Role | Can View | Can Create | Can Edit | Notes |
|------|----------|-----------|----------|-------|
| **admin** | All schools, all data | Everything | Everything | Full system access |
| **director** | Own school data | Students, users, justifications | Own school data | School administrator |
| **teacher** | Own school students | Check-ins, absences | Limited | Daily attendance operations |
| **comedor** | Own school students | Dietary/kitchen data | Kitchen data | Food service staff |
| **parent** | Own child's data | Justifications | Own justifications | View-only for attendance |

---

## Core Concepts

### Schools
- Each school is independent with its own students, teachers, and administrators
- Directors manage their specific school
- Admins can view all schools

### Students
- Linked to a specific school
- Each student has a parent email for notifications
- Identified by `student_id` (unique per school)

### Check-ins
- Records when a student arrives at school
- Can mark late arrivals (after 9:01 AM)
- Optional checkout time
- Timestamps stored in UTC

### Justifications
- Used to explain absences or late arrivals
- Can be pending, approved, or rejected
- Multiple justification types supported

### Absence Notifications
- Automatically generated when students don't check in
- Tracked for reporting purposes

---

## Endpoints Overview

### Authentication
- `POST /api/auth/login` - Login and get access token
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user info

### Schools
- `GET /api/schools/` - List all schools (or your school if director)
- `GET /api/schools/{id}` - Get specific school
- `POST /api/schools/` - Create school (admin only)
- `PUT /api/schools/{id}` - Update school (admin only)

### Students
- `GET /api/students/` - List students (filtered by school)
- `GET /api/students/{id}` - Get specific student
- `POST /api/students/` - Create student (director/admin)
- `PUT /api/students/{id}` - Update student (director/admin)
- `DELETE /api/students/{id}` - Delete student (admin only)

### Check-ins
- `GET /api/checkins/` - List check-ins (with filters)
- `GET /api/checkins/{id}` - Get specific check-in
- `POST /api/checkins/` - Create check-in (QR code scan)
- `PUT /api/checkins/{id}` - Update check-in (add checkout time)

### Justifications
- `GET /api/justifications/` - List justifications
- `GET /api/justifications/{id}` - Get specific justification
- `POST /api/justifications/` - Create justification (parent)
- `PUT /api/justifications/{id}` - Update justification (director/admin)

### Reports
- `GET /api/reports/attendance/` - Attendance report by date
- `GET /api/reports/absences/` - Absence report
- `GET /api/reports/summary/` - Overall statistics

### Users
- `GET /api/users/` - List users (admin only)
- `POST /api/users/` - Create user (admin/director)
- `PUT /api/users/{id}` - Update user (admin/director)
- `DELETE /api/users/{id}` - Delete user (admin only)

### Admin Tools
- `GET /api/admin/populate-test-data-simple` - Populate database with test data

---

## Getting Started

### Step 1: Authenticate

```bash
# Login
TOKEN=$(curl -s -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@test.com",
    "password": "admin"
  }' | jq -r '.access_token')

echo $TOKEN
```

### Step 2: Get Your Schools

```bash
curl -X GET https://arrivapp-backend.onrender.com/api/schools/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Colegio San José",
    "contact_email": "info@sanjose.es",
    "created_at": "2025-11-21T10:30:00"
  },
  {
    "id": 2,
    "name": "Instituto Técnico Madrid",
    "contact_email": "info@tecmadrid.es",
    "created_at": "2025-11-21T10:30:00"
  }
]
```

### Step 3: Get Students from a School

```bash
SCHOOL_ID=1

curl -X GET "https://arrivapp-backend.onrender.com/api/students/?school_id=$SCHOOL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

### Step 4: Get Today's Check-ins

```bash
SCHOOL_ID=1

curl -X GET "https://arrivapp-backend.onrender.com/api/checkins/?school_id=$SCHOOL_ID&date=2025-11-21" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

---

## Common Use Cases

### Use Case 1: Get Attendance Report for Today

```bash
#!/bin/bash

TOKEN="your_access_token"
SCHOOL_ID=1
TODAY=$(date +%Y-%m-%d)

# Get all students
STUDENTS=$(curl -s -X GET "https://arrivapp-backend.onrender.com/api/students/?school_id=$SCHOOL_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

# Get today's check-ins
CHECKINS=$(curl -s -X GET "https://arrivapp-backend.onrender.com/api/checkins/?school_id=$SCHOOL_ID&date=$TODAY" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

echo "Students: $(echo $STUDENTS | jq 'length')"
echo "Present: $(echo $CHECKINS | jq 'length')"
echo "Absent: $(($(echo $STUDENTS | jq 'length') - $(echo $CHECKINS | jq 'length')))"
```

### Use Case 2: Get List of Late Arrivals

```bash
TOKEN="your_access_token"
TODAY=$(date +%Y-%m-%d)

curl -X GET "https://arrivapp-backend.onrender.com/api/checkins/?date=$TODAY&is_late=true" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.[] | {name: .student.name, time: .checkin_time}'
```

### Use Case 3: Get Absences and Justifications

```bash
TOKEN="your_access_token"
SCHOOL_ID=1

# Get all pending justifications
curl -X GET "https://arrivapp-backend.onrender.com/api/justifications/?school_id=$SCHOOL_ID&status=pending" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" | jq '.[] | {student: .student.name, reason: .reason, date: .date}'
```

### Use Case 4: Create a Student

```bash
TOKEN="your_access_token"
SCHOOL_ID=1

curl -X POST https://arrivapp-backend.onrender.com/api/students/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "STU-001",
    "name": "Juan García López",
    "parent_email": "juan.padre@example.com",
    "class_name": "3A",
    "school_id": '$SCHOOL_ID'
  }'
```

### Use Case 5: Record a Check-in

```bash
TOKEN="your_access_token"
STUDENT_ID=1

curl -X POST https://arrivapp-backend.onrender.com/api/checkins/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": '$STUDENT_ID',
    "checkin_time": "2025-11-21T08:45:00Z"
  }'
```

### Use Case 6: Get Attendance Statistics

```bash
TOKEN="your_access_token"

curl -X GET "https://arrivapp-backend.onrender.com/api/reports/attendance/?date=2025-11-21" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "date": "2025-11-21",
  "total_students": 250,
  "present": 235,
  "absent": 15,
  "late": 8,
  "percentage_attendance": 94.0
}
```

---

## Response Examples

### Student Object

```json
{
  "id": 1,
  "student_id": "STU-001",
  "name": "Carlos García López",
  "class_name": "3A",
  "parent_email": "carlos.padre@example.com",
  "school_id": 1,
  "school": {
    "id": 1,
    "name": "Colegio San José"
  },
  "is_active": true,
  "created_at": "2025-11-20T10:30:00",
  "qr_code_path": "/qr_codes/STU-001.png"
}
```

### Check-in Object

```json
{
  "id": 42,
  "student_id": 1,
  "student": {
    "id": 1,
    "name": "Carlos García López",
    "class_name": "3A"
  },
  "checkin_time": "2025-11-21T08:45:30Z",
  "checkout_time": "2025-11-21T14:30:00Z",
  "is_late": false,
  "created_at": "2025-11-21T08:45:30Z"
}
```

### Justification Object

```json
{
  "id": 5,
  "student_id": 1,
  "student": {
    "id": 1,
    "name": "Carlos García López"
  },
  "date": "2025-11-21",
  "justification_type": "absence",
  "reason": "Mi hijo está enfermo",
  "submitted_by": "carlos.padre@example.com",
  "submitted_at": "2025-11-21T09:00:00Z",
  "status": "pending",
  "reviewed_by": null,
  "reviewed_at": null,
  "created_at": "2025-11-21T09:00:00Z"
}
```

---

## Query Parameters

### Common Filters

**By School:**
```
?school_id=1
```

**By Date:**
```
?date=2025-11-21
```

**By Date Range:**
```
?start_date=2025-11-01&end_date=2025-11-30
```

**By Status:**
```
?status=pending
?status=approved
?status=rejected
```

**By Class:**
```
?class_name=3A
```

**Pagination:**
```
?skip=0&limit=50
```

### Example: Complex Query

```bash
# Get all pending justifications from last 7 days for a specific school
curl -X GET "https://arrivapp-backend.onrender.com/api/justifications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "school_id": 1,
    "status": "pending",
    "days_back": 7
  }'
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Data retrieved successfully |
| 201 | Created | New resource created |
| 400 | Bad Request | Invalid data format |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Validation Error | Invalid field values |
| 500 | Server Error | Unexpected error |

### Error Response Format

```json
{
  "detail": "Only administrators can create schools"
}
```

### Common Errors

**1. Missing Authentication**
```json
{"detail": "Not authenticated"}
```
*Solution: Include `Authorization: Bearer TOKEN` header*

**2. Invalid Credentials**
```json
{"detail": "Incorrect email or password"}
```
*Solution: Check email and password*

**3. Insufficient Permissions**
```json
{"detail": "Director or admin privileges required"}
```
*Solution: Use an account with appropriate role*

**4. Token Expired**
```json
{"detail": "Token expired"}
```
*Solution: Refresh token or login again*

**5. Validation Error**
```json
{
  "detail": [
    {
      "loc": ["body", "student_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
*Solution: Check required fields in request*

---

## Rate Limiting

Currently, there are no rate limits on the ArrivApp API, but future versions may implement them. Plan your integrations accordingly.

---

## Timestamps

All timestamps in ArrivApp are stored and returned in **UTC (Coordinated Universal Time)**.

**Format:** ISO 8601 (`YYYY-MM-DDTHH:MM:SSZ`)

**Examples:**
- `2025-11-21T08:45:30Z` - 8:45:30 AM UTC
- `2025-11-21T14:30:00Z` - 2:30:00 PM UTC

To convert to your local timezone, parse the UTC time and apply your timezone offset.

---

## Best Practices

### 1. Store Tokens Securely
- Never expose tokens in client-side code
- Use environment variables for sensitive data
- Implement token refresh mechanism

### 2. Implement Caching
- Cache school and student data locally
- Reduce API calls for frequently accessed data
- Invalidate cache periodically (e.g., every hour)

### 3. Handle Errors Gracefully
- Implement retry logic for failed requests
- Log errors for debugging
- Provide user feedback on failures

### 4. Use Pagination
- Always implement pagination for large datasets
- Use `skip` and `limit` parameters
- Default limit is 50 items

### 5. Batch Operations
- Group related requests together
- Use POST endpoints for bulk operations when available
- Avoid excessive individual requests

---

## API Documentation

For interactive API documentation, visit:

**Swagger UI:** `https://arrivapp-backend.onrender.com/docs`

**ReDoc:** `https://arrivapp-backend.onrender.com/redoc`

These provide live testing capabilities and detailed endpoint information.

---

## Support & Contact

For API support or questions:
- **Email:** admin@arrivapp.com
- **GitHub Issues:** [ArrivApp Repository](https://github.com/arrivapppilot-dotcom/ArrivApp)
- **Dashboard:** `https://arrivapp-frontend.onrender.com`

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.3 | 2025-11-21 | Current version - Multi-school, email notifications, full attendance tracking |
| 2.0.0 | 2025-11-01 | Initial production release |

---

## Examples by Language

### Python

```python
import requests
import json

BASE_URL = "https://arrivapp-backend.onrender.com"

# Login
response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": "admin@test.com", "password": "admin"}
)
token = response.json()["access_token"]

# Get schools
headers = {"Authorization": f"Bearer {token}"}
schools = requests.get(f"{BASE_URL}/api/schools/", headers=headers).json()

print(f"Schools: {len(schools)}")
for school in schools:
    print(f"  - {school['name']}")
```

### JavaScript

```javascript
const BASE_URL = "https://arrivapp-backend.onrender.com";

// Login
const loginResponse = await fetch(`${BASE_URL}/api/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "admin@test.com", password: "admin" })
});

const { access_token } = await loginResponse.json();

// Get schools
const schoolsResponse = await fetch(`${BASE_URL}/api/schools/`, {
  headers: { "Authorization": `Bearer ${access_token}` }
});

const schools = await schoolsResponse.json();
console.log(`Schools: ${schools.length}`);
schools.forEach(school => console.log(`  - ${school.name}`));
```

### cURL

```bash
# Login and store token
TOKEN=$(curl -s -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin"}' \
  | jq -r '.access_token')

# Get schools
curl -s -X GET https://arrivapp-backend.onrender.com/api/schools/ \
  -H "Authorization: Bearer $TOKEN" | jq '.'
```

---

**Last Updated:** November 21, 2025
**API Version:** 2.0.3
