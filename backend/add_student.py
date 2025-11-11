#!/usr/bin/env python3
"""
Quick script to add a student via API
Usage: python add_student.py
"""
import requests
import json

# API Configuration
API_BASE = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin123"

def login():
    """Login and get JWT token"""
    response = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def add_student(token, student_id, name, class_name, parent_email):
    """Add a new student"""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "student_id": student_id,
        "name": name,
        "class_name": class_name,
        "parent_email": parent_email
    }
    
    response = requests.post(
        f"{API_BASE}/api/students/",
        headers=headers,
        json=data
    )
    
    if response.status_code in [200, 201]:
        student = response.json()
        print(f"✅ Student added successfully!")
        print(f"   ID: {student['id']}")
        print(f"   Student ID: {student['student_id']}")
        print(f"   Name: {student['name']}")
        print(f"   Class: {student['class_name']}")
        print(f"   Parent Email: {student['parent_email']}")
        print(f"   QR Code Path: {student['qr_code_path']}")
        return student
    else:
        print(f"❌ Failed to add student: {response.text}")
        return None

def main():
    print("🎓 ArrivApp - Add Student\n")
    
    # Get token
    print("🔐 Logging in...")
    token = login()
    if not token:
        return
    
    print("✅ Logged in successfully!\n")
    
    # Get student details
    print("Enter student details:")
    student_id = input("  Student ID (e.g., S001): ").strip()
    name = input("  Name: ").strip()
    class_name = input("  Class (e.g., 5A): ").strip()
    parent_email = input("  Parent Email: ").strip()
    
    if not student_id or not name or not class_name or not parent_email:
        print("❌ All fields are required!")
        return
    
    # Add student
    print(f"\n📝 Adding student...")
    student = add_student(token, student_id, name, class_name, parent_email)
    
    if student:
        print(f"\n💡 QR code saved at: backend/qr_codes/{student['id']}.png")
        print(f"   You can download it from: http://localhost:8000/qr_codes/{student['id']}.png")

if __name__ == "__main__":
    main()
