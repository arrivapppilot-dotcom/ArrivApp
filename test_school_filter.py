#!/usr/bin/env python3
"""
Test to verify the school filter appears for admin users
"""
import requests
import time

API_URL = "https://arrivapp-backend.onrender.com/api"
FRONTEND_URL = "https://arrivapp-frontend.onrender.com"

def test_school_filter_display():
    print("=" * 60)
    print("Testing School Filter Display for Admin")
    print("=" * 60)
    
    # Step 1: Login as admin
    print("\n1. Logging in as admin...")
    login_response = requests.post(
        f"{API_URL}/auth/login",
        json={"username": "admin", "password": "Barcelona123!Madrid"},
        timeout=10
    )
    
    if login_response.status_code != 200:
        print(f"   ✗ Login failed: {login_response.status_code}")
        print(f"   {login_response.text}")
        return False
    
    token = login_response.json()['access_token']
    print(f"   ✓ Login successful")
    print(f"   Token: {token[:30]}...")
    
    # Step 2: Verify user is admin
    print("\n2. Verifying user role...")
    user_response = requests.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    if user_response.status_code != 200:
        print(f"   ✗ Failed to get user: {user_response.status_code}")
        return False
    
    user = user_response.json()
    role = user.get('role')
    print(f"   ✓ User: {user.get('username')}")
    print(f"   ✓ Role: {role}")
    
    if role != 'admin':
        print(f"   ✗ User is not admin, is {role}")
        return False
    
    # Step 3: Check frontend HTML
    print("\n3. Checking frontend dashboard.html...")
    frontend_response = requests.get(
        f"{FRONTEND_URL}/dashboard.html",
        timeout=10
    )
    
    if frontend_response.status_code != 200:
        print(f"   ✗ Failed to get dashboard: {frontend_response.status_code}")
        return False
    
    html = frontend_response.text
    
    # Check for school filter container
    if 'id="school-filter-container"' not in html:
        print("   ✗ school-filter-container NOT found in HTML")
        return False
    print("   ✓ school-filter-container element exists")
    
    # Check for hidden class
    if 'id="school-filter-container" class="hidden"' not in html:
        print("   ⚠ school-filter-container doesn't have initial 'hidden' class")
    else:
        print("   ✓ school-filter-container starts with 'hidden' class")
    
    # Check for checkPermissions function
    if 'async function checkPermissions()' not in html:
        print("   ✗ checkPermissions function NOT found")
        return False
    print("   ✓ checkPermissions function exists")
    
    # Check for code that shows filter for admin
    if 'schoolFilterContainer.classList.remove' not in html:
        print("   ✗ Code to show filter for admin NOT found")
        return False
    print("   ✓ Code to show filter for admin exists")
    
    # Check for loadSchools function
    if 'async function loadSchools()' not in html:
        print("   ✗ loadSchools function NOT found")
        return False
    print("   ✓ loadSchools function exists")
    
    # Step 4: Verify schools can be loaded
    print("\n4. Checking if schools endpoint works...")
    schools_response = requests.get(
        f"{API_URL}/schools/",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10
    )
    
    if schools_response.status_code != 200:
        print(f"   ✗ Failed to get schools: {schools_response.status_code}")
        return False
    
    schools = schools_response.json()
    print(f"   ✓ Schools endpoint works")
    print(f"   ✓ Number of schools: {len(schools)}")
    
    if schools:
        print(f"   ✓ Sample schools: {[s.get('name') for s in schools[:2]]}")
    
    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED - School filter should display for admin")
    print("=" * 60)
    print("\nHow to verify in browser:")
    print(f"1. Go to: {FRONTEND_URL}/dashboard.html")
    print("2. Login with admin credentials")
    print("3. School filter should appear between 'Clase' and 'Filtrar' buttons")
    print("4. Open browser console (F12) to see debug messages")
    return True

if __name__ == "__main__":
    try:
        test_school_filter_display()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
