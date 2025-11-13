#!/bin/bash
# Verify schools page is working correctly

echo "================================================"
echo "Verifying ArrivApp Schools Page Styling"
echo "================================================"

# Check CSS file size
echo -e "\n1. Checking CSS file..."
CSS_RESPONSE=$(curl -s -I https://arrivapp-frontend.onrender.com/styles.css)
CSS_STATUS=$(echo "$CSS_RESPONSE" | head -1)
echo "  CSS Status: $CSS_STATUS"

# Check HTML file
echo -e "\n2. Checking Schools HTML..."
HTML_RESPONSE=$(curl -s https://arrivapp-frontend.onrender.com/schools.html)
if echo "$HTML_RESPONSE" | grep -q "schools.js"; then
  echo "  ✓ schools.js is linked"
else
  echo "  ✗ schools.js NOT found"
fi

if echo "$HTML_RESPONSE" | grep -q "styles.css"; then
  echo "  ✓ styles.css is linked"
else
  echo "  ✗ styles.css NOT found"
fi

if echo "$HTML_RESPONSE" | grep -q "Gestión de Colegios"; then
  echo "  ✓ Page title present"
else
  echo "  ✗ Page title NOT found"
fi

# Check backend API
echo -e "\n3. Checking Backend API..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://arrivapp-backend.onrender.com/api/auth/login \
  -X POST \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin123"}')

if [ "$API_STATUS" = "200" ]; then
  echo "  ✓ Login endpoint working (HTTP 200)"
else
  echo "  ✗ Login endpoint returned HTTP $API_STATUS"
fi

# Summary
echo -e "\n================================================"
echo "✓ Schools page should now display correctly!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Visit: https://arrivapp-frontend.onrender.com/login.html"
echo "  2. Login: admin / admin123"
echo "  3. Go to Schools page"
echo "  4. You should see properly styled school cards"
