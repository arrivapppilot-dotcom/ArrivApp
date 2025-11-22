#!/usr/bin/env python3
"""
Simplified test to verify ArrivApp features work correctly
"""

import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://127.0.0.1:8000/api"

def test_login():
    """Test login with correct credentials"""
    print("\n" + "=" * 60)
    print("TEST 1: LOGIN")
    print("=" * 60)
    
    # Try to login with admin
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✅ Login successful! Token: {token[:20]}...")
        return token
    else:
        print("❌ Login failed")
        return None

def test_get_users(token):
    """Test fetching users"""
    print("\n" + "=" * 60)
    print("TEST 2: GET USERS")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/users", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        users = response.json()
        print(f"✅ Retrieved {len(users)} users")
        print(f"First 3 users: {json.dumps(users[:3], indent=2)[:500]}")
        return users
    else:
        print(f"❌ Failed to get users: {response.text[:500]}")
        return None

def test_get_schools(token):
    """Test fetching schools"""
    print("\n" + "=" * 60)
    print("TEST 3: GET SCHOOLS")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/schools", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        schools = response.json()
        print(f"✅ Retrieved {len(schools)} schools")
        if schools:
            print(f"First school: {json.dumps(schools[0], indent=2)[:500]}")
        return schools
    else:
        print(f"❌ Failed to get schools: {response.text[:500]}")
        return None

def test_get_students(token):
    """Test fetching students"""
    print("\n" + "=" * 60)
    print("TEST 4: GET STUDENTS")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/students", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        students = response.json()
        print(f"✅ Retrieved {len(students)} students")
        if students:
            print(f"First student: {json.dumps(students[0], indent=2)[:500]}")
        return students
    else:
        print(f"❌ Failed to get students: {response.text[:500]}")
        return None

def test_get_justifications(token):
    """Test fetching justifications"""
    print("\n" + "=" * 60)
    print("TEST 5: GET JUSTIFICATIONS")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/justifications", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        justifications = response.json()
        print(f"✅ Retrieved {len(justifications)} justifications")
        if justifications:
            print(f"First justification: {json.dumps(justifications[0], indent=2)[:500]}")
        return justifications
    else:
        print(f"❌ Failed to get justifications: {response.text[:500]}")
        return None

def test_dashboard_stats(token):
    """Test dashboard statistics"""
    print("\n" + "=" * 60)
    print("TEST 6: DASHBOARD STATISTICS")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/reports/statistics", headers=headers)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ Retrieved statistics:")
        print(json.dumps(stats, indent=2)[:500])
        return stats
    else:
        print(f"❌ Failed to get statistics: {response.text[:500]}")
        return None

def test_api_health():
    """Test API is responding"""
    print("\n" + "=" * 60)
    print("TEST 0: API HEALTH CHECK")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/auth/login", timeout=5)
        print(f"✅ API is responding (status: {response.status_code})")
        return True
    except Exception as e:
        print(f"❌ API is not responding: {e}")
        return False

if __name__ == "__main__":
    print("\n🧪 STARTING ARRIVAPP TEST SUITE")
    
    # Check API health first
    if not test_api_health():
        print("\n❌ Cannot connect to API. Make sure backend is running on http://127.0.0.1:8000")
        exit(1)
    
    # Login
    token = test_login()
    if not token:
        print("\n❌ Cannot login. Tests cannot continue.")
        exit(1)
    
    # Run other tests
    users = test_get_users(token)
    schools = test_get_schools(token)
    students = test_get_students(token)
    justifications = test_get_justifications(token)
    stats = test_dashboard_stats(token)
    
    print("\n" + "=" * 60)
    print("✅ ALL BASIC TESTS COMPLETED")
    print("=" * 60)
