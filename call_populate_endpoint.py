#!/usr/bin/env python3
"""
Call the admin populate endpoint on Render to populate the production database.
"""
import requests
import json
import sys

# Render backend URL
BACKEND_URL = "https://arrivapp-backend.onrender.com"

# Token for populate endpoint (if needed, can be set via ADMIN_POPULATE_TOKEN env var)
POPULATE_TOKEN = ""

def populate_database():
    """Call the populate endpoint"""
    print("📊 Populating Render database with test data...")
    
    # Try with token endpoint (no auth required if token is empty)
    response = requests.post(
        f"{BACKEND_URL}/api/admin/populate-test-data-token",
        json={"token": POPULATE_TOKEN}
    )
    
    if response.status_code != 200:
        print(f"❌ Populate failed: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    print(f"✅ Populate successful!\n")
    
    # Show summary
    result = data.get("data", {})
    print("📊 Summary:")
    print(f"   Total students: {result.get('total_students', 'N/A')}")
    print(f"   Total check-ins: {result.get('total_checkins', 'N/A')}")
    print(f"   Today's check-ins: {result.get('today_checkins', 'N/A')}")
    print(f"   Old test students deleted: {result.get('old_test_students_deleted', 'N/A')}")
    print()
    
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 Populate Render Production Database")
    print("=" * 70 + "\n")
    
    try:
        success = populate_database()
        if success:
            print("=" * 70)
            print("✅ Done! Hard refresh dashboard to see new test data")
            print("=" * 70 + "\n")
        else:
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
