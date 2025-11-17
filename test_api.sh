#!/bin/bash

# Get auth token
TOKEN=$(curl -s -X POST "https://arrivapp-backend.onrender.com/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"

if [ -z "$TOKEN" ]; then
  echo "Failed to get token"
  exit 1
fi

# Test attendance-history endpoint
TODAY=$(date +%Y-%m-%d)
echo "Today: $TODAY"

curl -s "https://arrivapp-backend.onrender.com/api/reports/attendance-history?start_date=$TODAY&end_date=$TODAY" \
  -H "Authorization: Bearer $TOKEN" | head -200

