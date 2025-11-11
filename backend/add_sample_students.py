"""
Add sample students for testing
Run with: python add_sample_students.py
"""

import requests
import sys

API_BASE_URL = "http://localhost:8000"

# Sample students data
SAMPLE_STUDENTS = [
    {
        "student_id": "EST001",
        "name": "María García López",
        "class_name": "3ro A",
        "parent_email": "maria.parent@example.com"
    },
    {
        "student_id": "EST002",
        "name": "Juan Pérez Martín",
        "class_name": "3ro A",
        "parent_email": "juan.parent@example.com"
    },
    {
        "student_id": "EST003",
        "name": "Ana Rodríguez Silva",
        "class_name": "3ro B",
        "parent_email": "ana.parent@example.com"
    },
    {
        "student_id": "EST004",
        "name": "Carlos Sánchez Torres",
        "class_name": "3ro B",
        "parent_email": "carlos.parent@example.com"
    },
    {
        "student_id": "EST005",
        "name": "Laura Fernández Ruiz",
        "class_name": "4to A",
        "parent_email": "laura.parent@example.com"
    },
]


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


def create_student(token, student_data):
    """Create a student."""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{API_BASE_URL}/api/students/",
        json=student_data,
        headers=headers
    )
    
    if response.status_code == 201:
        student = response.json()
        print(f"✅ Created: {student['name']} (ID: {student['student_id']})")
        return True
    elif response.status_code == 400 and "already exists" in response.text:
        print(f"⚠️  Skipped: {student_data['name']} (already exists)")
        return False
    else:
        print(f"❌ Failed to create {student_data['name']}: {response.text}")
        return False


def main():
    print("=" * 50)
    print("ArrivApp - Add Sample Students")
    print("=" * 50)
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
    
    # Create students
    print(f"📝 Creating {len(SAMPLE_STUDENTS)} sample students...")
    print()
    
    created = 0
    for student_data in SAMPLE_STUDENTS:
        if create_student(token, student_data):
            created += 1
    
    print()
    print("=" * 50)
    print(f"✅ Done! Created {created} students")
    print()
    print("Next steps:")
    print("  1. Download QR codes from the API")
    print("  2. Print them for students")
    print("  3. Open checkin.html to test scanning")
    print()
    print("Download QR codes:")
    print(f"  curl -H 'Authorization: Bearer {token}' \\")
    print(f"    {API_BASE_URL}/api/students/1/qr -o student_1.png")
    print("=" * 50)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
