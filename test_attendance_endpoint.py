#!/usr/bin/env python3
"""
Test the new attendance-with-absences endpoint
"""
import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Change to backend directory
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

API_URL = os.getenv("API_URL", "http://localhost:8000/api")
TOKEN = os.getenv("TEST_TOKEN", None)

def test_endpoint():
    """Test the attendance-with-absences endpoint"""
    
    print("Testing attendance-with-absences endpoint...")
    
    # Get today's date
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Make request
    url = f"{API_URL}/reports/attendance-with-absences"
    params = {
        "start_date": today,
        "end_date": today
    }
    
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        print(f"\nResponse status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            records = data.get("records", [])
            
            print(f"Total records: {len(records)}")
            
            # Count by type
            present = sum(1 for r in records if not r.get("is_absent") and not r.get("is_late"))
            late = sum(1 for r in records if r.get("is_late"))
            absent = sum(1 for r in records if r.get("is_absent"))
            
            print(f"\nBreakdown:")
            print(f"  Present: {present}")
            print(f"  Late: {late}")
            print(f"  Absent: {absent}")
            
            # Check email_sent field
            with_email = sum(1 for r in records if r.get("email_sent"))
            without_email = len(records) - with_email
            
            print(f"\nEmail notifications:")
            print(f"  Sent: {with_email}")
            print(f"  Not sent: {without_email}")
            
            # Show sample absent students with email status
            absent_records = [r for r in records if r.get("is_absent")]
            if absent_records:
                print(f"\nSample absent students:")
                for record in absent_records[:3]:
                    email_status = "✓ Enviado" if record.get("email_sent") else "✗ No enviado"
                    print(f"  - {record.get('student_name')}: {email_status}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_endpoint()
