import requests
import json

API_URL = "https://arrivapp-backend.onrender.com/api"

# Login
login_response = requests.post(
    f"{API_URL}/auth/login",
    json={"username": "admin", "password": "Barcelona123!Madrid"}
)

if login_response.status_code == 200:
    data = login_response.json()
    token = data.get('access_token')
    print(f"✓ Login successful")
    print(f"Token: {token[:50]}...")
    
    # Check current user
    user_response = requests.get(
        f"{API_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if user_response.status_code == 200:
        user = user_response.json()
        print(f"✓ User info retrieved")
        print(f"  - Username: {user.get('username')}")
        print(f"  - Role: {user.get('role')}")
        print(f"  - School: {user.get('school_id')}")
    else:
        print(f"✗ Failed to get user: {user_response.status_code}")
        print(user_response.text)
else:
    print(f"✗ Login failed: {login_response.status_code}")
    print(login_response.text)
