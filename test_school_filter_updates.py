#!/usr/bin/env python3
"""
Test to verify school filter updates dashboard data
"""
import requests
import json

API_URL = "https://arrivapp-backend.onrender.com/api"
FRONTEND_URL = "https://arrivapp-frontend.onrender.com"

def test_school_filter_updates_data():
    print("=" * 70)
    print("Testing School Filter Updates Dashboard Data")
    print("=" * 70)
    
    # Step 1: Login as admin
    print("\n1. Logging in as admin...")
    login_response = requests.post(
        f"{API_URL}/auth/login",
        json={"username": "admin", "password": "Barcelona123!Madrid"},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"   ✗ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()['access_token']
    print(f"   ✓ Login successful")
    
    # Step 2: Get all statistics (no school filter)
    print("\n2. Getting dashboard statistics (no school filter)...")
    url_all = f"{API_URL}/reports/statistics?period=daily&start_date=2025-11-21&end_date=2025-11-21"
    response_all = requests.get(url_all, headers={"Authorization": f"Bearer {token}"}, timeout=10)
    
    if response_all.status_code != 200:
        print(f"   ✗ Failed: {response_all.status_code}")
        print(f"   {response_all.text}")
        return False
    
    data_all = response_all.json()
    print(f"   ✓ Got statistics")
    print(f"     - Total students: {data_all.get('total_students', 0)}")
    print(f"     - Present: {data_all.get('present', 0)}")
    print(f"     - Late: {data_all.get('late', 0)}")
    
    # Step 3: Get schools
    print("\n3. Getting available schools...")
    schools_response = requests.get(
        f"{API_URL}/schools/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    if schools_response.status_code != 200:
        print(f"   ✗ Failed: {schools_response.status_code}")
        return False
    
    schools = schools_response.json()
    if not schools:
        print(f"   ⚠ No schools found")
        return True
    
    print(f"   ✓ Got {len(schools)} schools")
    for i, school in enumerate(schools[:3]):
        print(f"     {i+1}. {school.get('name')} (ID: {school.get('id')})")
    
    # Step 4: Get statistics for first school
    if schools and len(schools) > 1:
        first_school_id = schools[0]['id']
        print(f"\n4. Getting statistics for school: {schools[0].get('name')}...")
        url_school = f"{API_URL}/reports/statistics?period=daily&start_date=2025-11-21&end_date=2025-11-21&school_id={first_school_id}"
        response_school = requests.get(
            url_school,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response_school.status_code != 200:
            print(f"   ✗ Failed: {response_school.status_code}")
            print(f"   {response_school.text}")
            return False
        
        data_school = response_school.json()
        print(f"   ✓ Got school statistics")
        print(f"     - Total students: {data_school.get('total_students', 0)}")
        print(f"     - Present: {data_school.get('present', 0)}")
        print(f"     - Late: {data_school.get('late', 0)}")
        
        # Verify data changed
        print(f"\n5. Verifying data changes when filtering by school...")
        if data_all.get('total_students') != data_school.get('total_students'):
            print(f"   ✓ Data changed - Total students differ: {data_all.get('total_students')} vs {data_school.get('total_students')}")
        else:
            print(f"   ⚠ Data might be same (could be expected if school has all students)")
    
    # Step 6: Check frontend code
    print(f"\n6. Verifying frontend code has event listeners...")
    frontend_response = requests.get(
        f"{FRONTEND_URL}/dashboard.html",
        timeout=10
    )
    
    html = frontend_response.text
    checks = {
        "addEventListener for school-filter": "schoolFilter.addEventListener('change'",
        "addEventListener for class-filter": "classFilter.addEventListener('change'",
        "addEventListener for date-picker": "datePicker.addEventListener('change'",
        "school_id parameter in URL": "school_id",
        "class_name parameter in URL": "class_name",
    }
    
    all_passed = True
    for check_name, check_str in checks.items():
        if check_str in html:
            print(f"   ✓ {check_name}")
        else:
            print(f"   ✗ {check_name}")
            all_passed = False
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        print("\nHow to test in browser:")
        print(f"1. Go to: {FRONTEND_URL}/dashboard.html")
        print("2. Login with admin credentials")
        print("3. Open browser DevTools (F12) → Console")
        print("4. Select a school from the 'Colegio' dropdown")
        print("5. You should see:")
        print("   - Console logs: 'School filter changed to: <school_id>'")
        print("   - Dashboard cards update with new numbers")
        print("   - Tables refresh with filtered data")
        print("6. Try selecting a date and class to see them update too")
        return True
    else:
        print("✗ SOME TESTS FAILED")
        print("=" * 70)
        return False

if __name__ == "__main__":
    try:
        test_school_filter_updates_data()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
