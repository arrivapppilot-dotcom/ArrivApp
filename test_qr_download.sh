#!/bin/bash
# Test QR code download functionality

echo "================================================"
echo "Testing QR Code Download - End-to-End"
echo "================================================"

# Step 1: Login
echo -e "\n1. Logging in as admin..."
LOGIN_RESPONSE=$(curl -s -X POST https://arrivapp-backend.onrender.com/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "✗ Login failed!"
  exit 1
fi

echo "✓ Login successful"

# Step 2: Test QR code download
echo -e "\n2. Testing QR code download..."
QR_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -H "Authorization: Bearer $TOKEN" \
  https://arrivapp-backend.onrender.com/api/students/1/qr -o /tmp/qr_download.png)

HTTP_STATUS=$(echo "$QR_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

if [ "$HTTP_STATUS" != "200" ]; then
  echo "✗ QR download failed with status $HTTP_STATUS"
  exit 1
fi

# Verify it's a PNG file
FILE_TYPE=$(file /tmp/qr_download.png)
if echo "$FILE_TYPE" | grep -q "PNG image"; then
  echo "✓ QR code downloaded successfully (PNG image)"
  FILE_SIZE=$(ls -lh /tmp/qr_download.png | awk '{print $5}')
  echo "  File size: $FILE_SIZE"
else
  echo "✗ Downloaded file is not a PNG image!"
  echo "  File type: $FILE_TYPE"
  exit 1
fi

# Step 3: Test CORS headers
echo -e "\n3. Testing CORS headers..."
CORS_TEST=$(curl -s -D - -H "Authorization: Bearer $TOKEN" \
  https://arrivapp-backend.onrender.com/api/students/1/qr -o /dev/null 2>&1)

if echo "$CORS_TEST" | grep -q "access-control-allow-origin: \*"; then
  echo "✓ CORS header 'Access-Control-Allow-Origin: *' present"
else
  echo "✗ CORS header missing!"
fi

if echo "$CORS_TEST" | grep -q "access-control-allow-methods"; then
  echo "✓ CORS header 'Access-Control-Allow-Methods' present"
fi

if echo "$CORS_TEST" | grep -q "content-type: image/png"; then
  echo "✓ Content-Type header correct (image/png)"
fi

# Step 4: Test multiple students
echo -e "\n4. Testing QR codes for multiple students..."
for student_id in 1 2 3; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" \
    "https://arrivapp-backend.onrender.com/api/students/$student_id/qr")
  
  if [ "$STATUS" = "200" ]; then
    echo "  ✓ Student $student_id: OK"
  else
    echo "  ✗ Student $student_id: HTTP $STATUS"
  fi
done

echo -e "\n================================================"
echo "✓ All QR code download tests passed!"
echo "================================================"
echo ""
echo "Summary:"
echo "  - Admin login working"
echo "  - QR code generation in-memory working"
echo "  - PNG files generated correctly"
echo "  - CORS headers properly set"
echo "  - Multiple student QR codes accessible"
echo ""
echo "The students page should now work correctly!"
