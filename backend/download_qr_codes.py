"""
Download all student QR codes
Run with: python download_qr_codes.py
"""

import requests
import os
import sys

API_BASE_URL = "http://localhost:8000"
OUTPUT_DIR = "../qr_codes"


def login():
    """Login and get token."""
    print("🔐 Logging in...")
    response = requests.post(
        f"{API_BASE_URL}/api/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        sys.exit(1)
    
    token = response.json()["access_token"]
    print("✅ Login successful!")
    return token


def get_students(token):
    """Get all students."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_BASE_URL}/api/students/", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get students: {response.text}")
        sys.exit(1)
    
    return response.json()


def download_qr(token, student_id, student_name, student_code):
    """Download QR code for a student."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{API_BASE_URL}/api/students/{student_id}/qr",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"⚠️  No QR code for {student_name}")
        return False
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Save QR code
    filename = f"{student_code}_{student_name.replace(' ', '_')}.png"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, 'wb') as f:
        f.write(response.content)
    
    print(f"✅ Downloaded: {filename}")
    return True


def main():
    print("=" * 60)
    print("ArrivApp - Download All QR Codes")
    print("=" * 60)
    print()
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code != 200:
            raise Exception("API not healthy")
    except Exception as e:
        print("❌ Error: Cannot connect to API")
        print(f"   Make sure the backend is running at {API_BASE_URL}")
        sys.exit(1)
    
    # Login
    token = login()
    print()
    
    # Get students
    print("📋 Fetching students...")
    students = get_students(token)
    print(f"Found {len(students)} students")
    print()
    
    # Download QR codes
    print(f"📥 Downloading QR codes to {OUTPUT_DIR}/...")
    print()
    
    downloaded = 0
    for student in students:
        if download_qr(token, student['id'], student['name'], student['student_id']):
            downloaded += 1
    
    print()
    print("=" * 60)
    print(f"✅ Done! Downloaded {downloaded}/{len(students)} QR codes")
    print()
    print(f"📁 QR codes saved to: {os.path.abspath(OUTPUT_DIR)}/")
    print()
    print("Next steps:")
    print("  1. Print the QR codes")
    print("  2. Laminate them (recommended)")
    print("  3. Give them to students")
    print("  4. Test scanning at checkin.html")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
