# ArrivApp API - Error Codes Reference

## Overview

This document provides a complete reference of all error codes returned by the ArrivApp API, along with their meanings, causes, and solutions.

**Base URL:** `https://arrivapp-backend.onrender.com`

---

## Error Response Format

All error responses follow this standard format:

```json
{
  "detail": "Error message explaining what went wrong"
}
```

For validation errors:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "error description",
      "type": "error_type"
    }
  ]
}
```

---

## HTTP Status Codes

### 2xx Success Codes

| Code | Name | Meaning |
|------|------|---------|
| 200 | OK | Request successful, data returned |
| 201 | Created | New resource successfully created |
| 204 | No Content | Request successful, no content to return |

---

### 4xx Client Error Codes

#### 400 - Bad Request

**Generic Error:**
```json
{
  "detail": "Invalid request"
}
```

**Common Causes & Solutions:**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Invalid JSON format` | Malformed JSON in request body | Check JSON syntax, use JSON validator |
| `Missing required field: {field}` | Required field not provided | Include all required fields in request |
| `School with this name already exists` | Duplicate school name | Use a unique school name |
| `Student with this ID already exists` | Duplicate student ID | Use a unique student_id |
| `Invalid date format` | Date not in ISO 8601 format | Use `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SSZ` |

**Example:**
```bash
curl -X POST https://arrivapp-backend.onrender.com/api/students/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "John"}'  # Missing required fields
```

**Response:**
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

---

#### 401 - Unauthorized

**Generic Error:**
```json
{
  "detail": "Not authenticated"
}
```

**Common Causes & Solutions:**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Not authenticated` | Missing `Authorization` header | Add `Authorization: Bearer TOKEN` header |
| `Invalid authentication credentials` | Missing Bearer token | Include token after "Bearer " |
| `Incorrect email or password` | Wrong login credentials | Verify email and password |
| `Token expired` | JWT token has expired | Login again to get new token |
| `Invalid token` | Malformed or corrupted token | Ensure token is complete and valid |

**Example 1: Missing Header**
```bash
curl -X GET https://arrivapp-backend.onrender.com/api/students/
# Missing Authorization header
```

**Response:**
```json
{
  "detail": "Not authenticated"
}
```

**Example 2: Invalid Credentials**
```bash
curl -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "wrong@example.com", "password": "wrong"}'
```

**Response:**
```json
{
  "detail": "Incorrect email or password"
}
```

---

#### 403 - Forbidden

**Generic Error:**
```json
{
  "detail": "Access denied"
}
```

**Common Causes & Solutions:**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Only administrators can create schools` | Non-admin trying to create school | Use admin account |
| `Only administrators can update schools` | Non-admin trying to update school | Use admin account |
| `Only administrators can delete schools` | Non-admin trying to delete school | Use admin account |
| `Director or admin privileges required` | Insufficient role | Use director or admin account |
| `Only administrators can create users` | Non-admin trying to create user | Use admin account |
| `Admin privileges required` | Insufficient permissions | Use admin account |
| `Access denied to this school` | Director trying to access different school | Access your own school only |
| `Cannot modify users from other schools` | Director trying to modify user from different school | Manage users within your school |

**Example 1: Non-Admin Creating School**
```bash
curl -X POST https://arrivapp-backend.onrender.com/api/schools/ \
  -H "Authorization: Bearer TEACHER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "New School", "contact_email": "info@school.es"}'
```

**Response:**
```json
{
  "detail": "Only administrators can create schools"
}
```

**Example 2: Director Accessing Wrong School**
```bash
curl -X GET https://arrivapp-backend.onrender.com/api/students/?school_id=2 \
  -H "Authorization: Bearer DIRECTOR_SCHOOL_1_TOKEN"
# Director from school 1 trying to access school 2
```

**Response:**
```json
{
  "detail": "Access denied to this school"
}
```

---

#### 404 - Not Found

**Generic Error:**
```json
{
  "detail": "Resource not found"
}
```

**Common Causes & Solutions:**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `School not found` | School ID doesn't exist | Use valid school ID |
| `Student not found` | Student ID doesn't exist | Use valid student ID |
| `Check-in not found` | Check-in ID doesn't exist | Use valid check-in ID |
| `Justification not found` | Justification ID doesn't exist | Use valid justification ID |
| `User not found` | User ID doesn't exist | Use valid user ID |

**Example:**
```bash
curl -X GET https://arrivapp-backend.onrender.com/api/students/99999 \
  -H "Authorization: Bearer TOKEN"
# Student with ID 99999 doesn't exist
```

**Response:**
```json
{
  "detail": "Student not found"
}
```

---

#### 422 - Unprocessable Entity

**Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

**Common Causes & Solutions:**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `invalid email format` | Email doesn't match pattern | Use valid email like `user@example.com` |
| `ensure this value has at most X characters` | Field exceeds max length | Use shorter value |
| `ensure this value has at least X characters` | Field below min length | Use longer value |
| `value is not a valid integer` | Expected integer, got string | Provide numeric value |
| `value is not a valid list` | Expected array, got single item | Provide array format |

**Example 1: Invalid Email**
```bash
curl -X POST https://arrivapp-backend.onrender.com/api/users/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"email": "invalid-email", "password": "pass123"}'
```

**Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "invalid email format",
      "type": "value_error.email"
    }
  ]
}
```

**Example 2: Value Too Long**
```bash
curl -X POST https://arrivapp-backend.onrender.com/api/students/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"student_id": "STU-0001", "name": "A' | head -c 300, "parent_email": "test@example.com"}'
```

**Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "name"],
      "msg": "ensure this value has at most 100 characters",
      "type": "value_error.string.max_length"
    }
  ]
}
```

---

### 5xx Server Error Codes

#### 500 - Internal Server Error

**Generic Error:**
```json
{
  "detail": "Internal server error"
}
```

**Common Causes & Solutions:**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `Database connection failed` | Database unreachable | Contact support |
| `Email service unavailable` | SMTP server not responding | Retry later or contact support |
| `Unexpected error processing request` | Bug in server code | Contact support with error ID |
| `Error: {specific error}` | Specific exception occurred | Check error message and contact support |

**Example:**
```bash
curl -X GET https://arrivapp-backend.onrender.com/api/students/ \
  -H "Authorization: Bearer TOKEN"
# Server experiences database connection issue
```

**Response:**
```json
{
  "detail": "Database connection failed"
}
```

---

## Specific Error Codes by Feature

### Authentication Errors

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Not authenticated | 401 | Missing/invalid token | Login and get new token |
| Token expired | 401 | Token older than 480 minutes | Refresh or login again |
| Incorrect email or password | 401 | Wrong credentials | Verify login info |
| Invalid token | 401 | Corrupted/tampered token | Login again |
| User not found | 404 | Email not in system | Create new account or verify email |

### School Errors

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Only admins can create schools | 403 | Insufficient role | Use admin account |
| School with this name already exists | 400 | Duplicate name | Use unique name |
| School not found | 404 | ID doesn't exist | Use valid school ID |
| Access denied to this school | 403 | Director accessing wrong school | Access your own school |

### Student Errors

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Student not found | 404 | ID doesn't exist | Use valid student ID |
| Student with this ID already exists | 400 | Duplicate ID | Use unique student_id |
| Only directors/admins can create students | 403 | Insufficient role | Use director or admin account |
| Student is not active | 400 | Student marked inactive | Reactivate student or use active student |

### Check-in Errors

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Check-in not found | 404 | ID doesn't exist | Use valid check-in ID |
| Invalid date format | 400 | Date malformed | Use ISO 8601 format |
| Student already checked in today | 400 | Duplicate check-in | Use existing check-in or different date |
| Checkout time before checkin time | 400 | Logical error | Ensure checkout is after checkin |

### Justification Errors

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Justification not found | 404 | ID doesn't exist | Use valid justification ID |
| Invalid justification type | 422 | Unknown type | Use valid type: `absence`, `late` |
| Invalid status | 422 | Unknown status | Use valid status: `pending`, `approved`, `rejected` |
| Cannot modify approved justification | 403 | Already processed | Create new justification instead |

### User Errors

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| User not found | 404 | ID doesn't exist | Use valid user ID |
| Email already in use | 400 | Duplicate email | Use unique email |
| Invalid role | 422 | Unknown role | Use valid role: `admin`, `director`, `teacher`, `comedor` |
| Cannot delete last admin | 403 | System requirement | Keep at least one admin |

---

## Error Code Examples & Solutions

### Example 1: Complete Authentication Flow with Error Handling

```bash
#!/bin/bash

API="https://arrivapp-backend.onrender.com"

# Try to login
echo "Attempting login..."
LOGIN_RESPONSE=$(curl -s -X POST $API/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@test.com", "password": "admin"}')

# Check if response contains error
if echo "$LOGIN_RESPONSE" | grep -q "detail"; then
  ERROR=$(echo "$LOGIN_RESPONSE" | jq -r '.detail')
  echo "❌ Login failed: $ERROR"
  exit 1
fi

# Extract token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
echo "✅ Login successful"

# Try to get schools
echo "Fetching schools..."
SCHOOLS=$(curl -s -X GET $API/api/schools/ \
  -H "Authorization: Bearer $TOKEN")

if echo "$SCHOOLS" | grep -q "Not authenticated"; then
  echo "❌ Token invalid or expired"
  exit 1
fi

echo "✅ Schools retrieved: $(echo $SCHOOLS | jq 'length') schools"
```

### Example 2: Creating Student with Error Handling

```bash
#!/bin/bash

API="https://arrivapp-backend.onrender.com"
TOKEN="your_token"

# Create student with validation
STUDENT_DATA='{
  "student_id": "STU-001",
  "name": "Juan García",
  "parent_email": "juan@example.com",
  "class_name": "3A",
  "school_id": 1
}'

echo "Creating student..."
RESPONSE=$(curl -s -X POST $API/api/students/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$STUDENT_DATA")

# Check for errors
if echo "$RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
  ERROR=$(echo "$RESPONSE" | jq '.detail')
  
  if [[ "$ERROR" == *"Not authenticated"* ]]; then
    echo "❌ Authentication failed: Get new token"
  elif [[ "$ERROR" == *"already exists"* ]]; then
    echo "❌ Student already exists: Use different ID"
  elif [[ "$ERROR" == *"admin"* ]]; then
    echo "❌ Permission denied: Use director/admin account"
  else
    echo "❌ Error: $ERROR"
  fi
  exit 1
fi

# Success
STUDENT_ID=$(echo "$RESPONSE" | jq '.id')
echo "✅ Student created successfully: ID $STUDENT_ID"
```

### Example 3: Handling All Error Types

```python
import requests
import json
from datetime import datetime

class ArrivAppAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def handle_error(self, response):
        """Central error handling"""
        try:
            error_data = response.json()
            detail = error_data.get('detail', 'Unknown error')
            
            # Handle different status codes
            if response.status_code == 401:
                print(f"❌ Authentication Error: {detail}")
                print("   Action: Login again to get new token")
            
            elif response.status_code == 403:
                print(f"❌ Permission Error: {detail}")
                print("   Action: Use account with sufficient privileges")
            
            elif response.status_code == 404:
                print(f"❌ Not Found: {detail}")
                print("   Action: Verify resource ID exists")
            
            elif response.status_code == 400:
                print(f"❌ Bad Request: {detail}")
                print("   Action: Check request format and fields")
            
            elif response.status_code == 422:
                if isinstance(detail, list):
                    print(f"❌ Validation Error:")
                    for error in detail:
                        field = error.get('loc', [])[-1]
                        msg = error.get('msg')
                        print(f"   - {field}: {msg}")
                else:
                    print(f"❌ Validation Error: {detail}")
                print("   Action: Fix field values and retry")
            
            elif response.status_code >= 500:
                print(f"❌ Server Error: {detail}")
                print("   Action: Contact support or retry later")
            
            return False
        
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def create_student(self, student_data):
        """Create student with error handling"""
        response = requests.post(
            f"{self.base_url}/api/students/",
            headers=self.headers,
            json=student_data
        )
        
        if response.status_code == 201:
            print("✅ Student created successfully")
            return response.json()
        else:
            self.handle_error(response)
            return None

# Usage
api = ArrivAppAPI("https://arrivapp-backend.onrender.com", "YOUR_TOKEN")

student = api.create_student({
    "student_id": "STU-001",
    "name": "Juan García",
    "parent_email": "juan@example.com",
    "class_name": "3A",
    "school_id": 1
})
```

---

## Common Error Scenarios

### Scenario 1: Expired Token

**Symptom:** All requests return 401

**Flow:**
1. User has been idle for >480 minutes
2. Make API request with old token
3. Server returns: `{"detail": "Token expired"}`

**Solution:**
```bash
# Logout and login again
TOKEN=$(curl -s -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}' | jq -r '.access_token')

# Or refresh if implemented
curl -X POST https://arrivapp-backend.onrender.com/api/auth/refresh \
  -H "Authorization: Bearer $OLD_TOKEN"
```

### Scenario 2: Insufficient Permissions

**Symptom:** Get 403 on school/user management endpoints

**Flow:**
1. Teacher tries to create user
2. Server checks role
3. Server returns: `{"detail": "Only administrators can create users"}`

**Solution:** Use account with appropriate role (admin or director for school management)

### Scenario 3: Duplicate Resource

**Symptom:** 400 error saying resource already exists

**Flow:**
1. Try to create student with ID that already exists
2. Server checks database
3. Server returns: `{"detail": "Student with this ID already exists"}`

**Solution:** Use unique identifier (student_id, email, etc.)

### Scenario 4: Invalid Data Format

**Symptom:** 422 validation error

**Flow:**
1. Send request with invalid email format
2. Server validates schema
3. Server returns detailed validation error

**Solution:** Check field requirements and data types in API guide

---

## Debugging Tips

### 1. Enable Verbose Logging

```bash
# cURL with verbose output
curl -v -X GET https://arrivapp-backend.onrender.com/api/students/ \
  -H "Authorization: Bearer TOKEN"
```

### 2. Pretty Print JSON Errors

```bash
# Use jq to format error responses
curl -s -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test", "password": "test"}' | jq '.'
```

### 3. Check Response Headers

```bash
# Include response headers for debugging
curl -i -X GET https://arrivapp-backend.onrender.com/api/students/ \
  -H "Authorization: Bearer TOKEN"
```

### 4. Test in Swagger UI

Visit: `https://arrivapp-backend.onrender.com/docs`

- No need to manage tokens manually
- See real-time responses
- Interactive endpoint testing

---

## Support

If you encounter an error not listed here:

1. **Check this guide** - Most errors are documented above
2. **Review API Guide** - See `API_USER_GUIDE.md` for endpoint details
3. **Test in Swagger** - Try endpoint in interactive docs
4. **Contact Support** - admin@arrivapp.com with:
   - Error message
   - HTTP status code
   - Request details (without sensitive info)
   - Timestamp of error

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.0.3 | 2025-11-21 | Comprehensive error code reference |
| 2.0.0 | 2025-11-01 | Initial error handling |

---

**Last Updated:** November 21, 2025
**API Version:** 2.0.3
