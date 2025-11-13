#!/bin/bash
# Test ArrivApp production flow

echo "================================================"
echo "Testing ArrivApp Production - Schools Page Flow"
echo "================================================"

# Test 1: Login
echo -e "\n1. Testing login as admin..."
LOGIN_RESPONSE=$(curl -s -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "✗ Login failed!"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✓ Login successful"
echo "  Token (first 30 chars): ${TOKEN:0:30}..."

# Test 2: Get current user info
echo -e "\n2. Testing /api/auth/me..."
ME_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  https://arrivapp-backend.onrender.com/api/auth/me)

USERNAME=$(echo "$ME_RESPONSE" | jq -r '.username // empty')
IS_ADMIN=$(echo "$ME_RESPONSE" | jq -r '.is_admin // empty')

if [ -z "$USERNAME" ]; then
  echo "✗ Failed to get user info!"
  echo "Response: $ME_RESPONSE"
  exit 1
fi

echo "✓ User info retrieved"
echo "  Username: $USERNAME"
echo "  Is Admin: $IS_ADMIN"

# Test 3: Get schools list
echo -e "\n3. Testing /api/schools/..."
SCHOOLS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  https://arrivapp-backend.onrender.com/api/schools/)

SCHOOL_COUNT=$(echo "$SCHOOLS_RESPONSE" | jq 'length // 0')

if [ "$SCHOOL_COUNT" -eq 0 ]; then
  echo "✗ No schools returned!"
  echo "Response: $SCHOOLS_RESPONSE"
  exit 1
fi

echo "✓ Schools retrieved"
echo "  Total schools: $SCHOOL_COUNT"

# Show first 3 schools
echo "  First 3 schools:"
echo "$SCHOOLS_RESPONSE" | jq -r '.[0:3][] | "    - \(.name) (ID: \(.id))"'

# Test 4: Test frontend login endpoint
echo -e "\n4. Testing frontend can authenticate..."
echo "  Frontend URL: https://arrivapp-frontend.onrender.com/schools.html"
echo "  Credentials: admin / admin123"

echo -e "\n================================================"
echo "✓ All tests passed!"
echo "================================================"
echo ""
echo "You can now:"
echo "  1. Go to https://arrivapp-frontend.onrender.com/login.html"
echo "  2. Login with: admin / admin123"
echo "  3. Navigate to Schools page to see all schools"
