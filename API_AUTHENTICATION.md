# ArrivApp API Authentication Guide

## Quick Reference

| Property | Value |
|----------|-------|
| **Authentication Type** | Bearer Token |
| **Standard** | JWT (RFC 7519) |
| **Algorithm** | HS256 (HMAC SHA-256) |
| **RFC Compliance** | RFC 6750 (Bearer Token Usage) |
| **Token Lifetime** | 24 hours |
| **Refresh Support** | Optional refresh token endpoint |
| **Scheme** | `Authorization: Bearer {token}` |
| **Transport** | HTTPS only |

---

## Complete Authentication Flow

### Step 1: Login (Get Token)

**Endpoint:** `POST /api/auth/login`

**Request:**
```bash
curl -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your-password"
  }'
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsInNjaG9vbF9pZCI6bnVsbCwiZXhwIjoxNjM3NjQ4MDAwfQ.abc123...",
  "token_type": "bearer"
}
```

---

### Step 2: Use Token (Authenticated Requests)

**Header Format:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Example:**
```bash
curl -X GET https://arrivapp-backend.onrender.com/api/schools/ \
  -H "Authorization: Bearer {ACCESS_TOKEN}" \
  -H "Content-Type: application/json"
```

**Important Notes:**
- Always include `Bearer ` (with space) before the token
- Token is NOT base64-encoded in transmission
- Token is case-sensitive
- Token must be included in ALL authenticated endpoints

---

### Step 3: Handle Expiration

When token expires (after 24 hours):

**Response (401 Unauthorized):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Action Required:**
- User must login again
- Obtain new token
- Continue with new token

---

## JWT Token Structure

### Components

A JWT token consists of three base64url-encoded parts separated by dots:

```
Header.Payload.Signature
```

### Header (Decoded)
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload (Decoded)
```json
{
  "sub": "admin",              // Subject (username)
  "role": "admin",             // User role
  "school_id": null,           // Associated school (null for admin)
  "exp": 1637648000,           // Expiration time (Unix timestamp)
  "iat": 1637561600            // Issued at time (Unix timestamp)
}
```

### Signature
```
HMACSHA256(
  base64UrlEncode(header) + "." +
  base64UrlEncode(payload),
  secret_key
)
```

The signature is calculated using a secret key stored on the server. This ensures:
- Token authenticity (not forged)
- Token integrity (not modified)
- No tampering possible without secret key

---

## Implementation Examples

### JavaScript/Fetch

```javascript
// 1. Login
const loginResponse = await fetch(
  'https://arrivapp-backend.onrender.com/api/auth/login',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'admin',
      password: 'password123'
    })
  }
);

const { access_token } = await loginResponse.json();

// 2. Store token (browser)
localStorage.setItem('arrivapp_token', access_token);

// 3. Use token
const getResponse = await fetch(
  'https://arrivapp-backend.onrender.com/api/schools/',
  {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${access_token}`,
      'Content-Type': 'application/json'
    }
  }
);

const schools = await getResponse.json();
```

### Python/Requests

```python
import requests

# 1. Login
login_response = requests.post(
    'https://arrivapp-backend.onrender.com/api/auth/login',
    json={'username': 'admin', 'password': 'password123'}
)

token = login_response.json()['access_token']

# 2. Use token
headers = {'Authorization': f'Bearer {token}'}

schools_response = requests.get(
    'https://arrivapp-backend.onrender.com/api/schools/',
    headers=headers
)

schools = schools_response.json()
```

### cURL

```bash
# 1. Login and extract token
TOKEN=$(curl -s -X POST \
  https://arrivapp-backend.onrender.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"

# 2. Use token
curl -X GET https://arrivapp-backend.onrender.com/api/schools/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

---

## Error Responses

### 401 Unauthorized - Missing Token

**Request:**
```bash
curl -X GET https://arrivapp-backend.onrender.com/api/schools/
```

**Response:**
```json
{
  "detail": "Not authenticated"
}
```

**Solution:** Include Authorization header with valid token

### 401 Unauthorized - Invalid Token

**Request:**
```bash
curl -X GET https://arrivapp-backend.onrender.com/api/schools/ \
  -H "Authorization: Bearer invalid_token_here"
```

**Response:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Solution:** 
- Verify token is correct
- Verify token includes `Bearer ` prefix
- Get new token if expired

### 401 Unauthorized - Expired Token

**Response:**
```json
{
  "detail": "Could not validate credentials"
}
```

**Solution:** Login again to get new token

### 403 Forbidden - Insufficient Permissions

**Response:**
```json
{
  "detail": "Not enough permissions"
}
```

**Solution:** Check user role and permissions

---

## Security Best Practices

### 1. Token Storage

**Browser/Frontend:**
- ❌ Don't store in plain text localStorage (vulnerable to XSS)
- ✅ Use secure HTTP-only cookies (httpOnly flag)
- ✅ Use session storage with cleanup on logout
- ✅ Consider memory-based storage for SPAs

**Server/Backend:**
- ✅ Encrypt tokens in database if storing
- ✅ Use environment variables for secret key
- ✅ Rotate secret key periodically
- ✅ Use secure database credentials

### 2. Token Transmission

- ✅ Always use HTTPS (never HTTP)
- ✅ Include token in Authorization header
- ❌ Never send token in URL query parameters
- ❌ Never send token in cookies without secure flags
- ✅ Verify SSL/TLS certificate validity

### 3. Token Validation

- ✅ Verify token signature on each request
- ✅ Check token expiration time
- ✅ Validate token claims (role, user_id, etc.)
- ✅ Reject tokens with invalid format
- ✅ Log failed authentication attempts

### 4. Token Expiration

- ✅ Set reasonable expiration (24 hours recommended)
- ✅ Implement refresh token mechanism if needed
- ✅ Force re-authentication on permission changes
- ✅ Clear tokens on logout
- ✅ Monitor for suspicious token usage patterns

### 5. User Account Security

- ✅ Use strong passwords (min 8 chars, mixed case, numbers)
- ✅ Hash passwords with bcrypt (never store plain text)
- ✅ Implement rate limiting on login attempts
- ✅ Implement account lockout after failed attempts
- ✅ Require password change on first login
- ✅ Log all authentication events

### 6. API Security

- ✅ Validate all inputs on backend
- ✅ Implement request rate limiting
- ✅ Use CORS headers correctly
- ✅ Implement CSRF protection if needed
- ✅ Log all API access
- ✅ Monitor for unusual patterns

---

## Common Issues & Solutions

### Issue: "Not authenticated"

**Problem:** Request missing Authorization header

**Solution:**
```bash
# Before: ❌
curl -X GET https://arrivapp-backend.onrender.com/api/schools/

# After: ✅
curl -X GET https://arrivapp-backend.onrender.com/api/schools/ \
  -H "Authorization: Bearer $TOKEN"
```

### Issue: "Could not validate credentials"

**Problem:** Token is invalid, expired, or malformed

**Solution:**
1. Verify token is correct: `echo $TOKEN`
2. Check token includes "Bearer " prefix
3. Login again if expired: `curl -X POST .../api/auth/login ...`
4. Verify you're using HTTPS (not HTTP)

### Issue: "Not enough permissions"

**Problem:** User role doesn't have access to resource

**Solution:**
1. Check user role: GET `/api/auth/me`
2. Verify user is admin for admin operations
3. Verify user has required school assignment
4. Ask admin to elevate permissions

### Issue: Token keeps expiring

**Problem:** Token expires after 24 hours

**Solution:**
1. Implement automatic re-login
2. Store credentials securely (only in backend)
3. Implement refresh token endpoint
4. Notify user to login again

---

## Compliance & Standards

### RFC 7519 - JSON Web Token (JWT)
- Defines JWT structure and claims
- Specifies signature algorithms
- Provides security considerations

### RFC 6750 - Bearer Token Usage
- Defines Bearer token authentication scheme
- Specifies header format: `Authorization: Bearer {token}`
- Provides error codes and security guidance

### HS256 Algorithm
- HMAC with SHA-256
- Symmetric key (secret key on both sides)
- Fast but key must be kept secret
- Used by ArrivApp for internal use cases

---

## References

- [JWT.io](https://jwt.io) - JWT introduction and debugger
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - JWT Specification
- [RFC 6750](https://tools.ietf.org/html/rfc6750) - Bearer Token Usage
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [ArrivApp API User Guide](./API_USER_GUIDE.md)
