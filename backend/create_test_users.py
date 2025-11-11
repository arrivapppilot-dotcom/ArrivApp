#!/usr/bin/env python3
"""
Create test users with different roles for testing
"""
from app.core.database import SessionLocal
from app.models.models import User, School, UserRole
from app.core.security import get_password_hash

db = SessionLocal()

# Create test users
test_users = [
    {
        "username": "director_sj",
        "email": "director_sanjose@example.com",
        "password": "madrid123",
        "full_name": "Director San José",
        "role": UserRole.director,
        "school_name": "Colegio San José",
        "is_admin": False
    },
    {
        "username": "teacher1_sj",
        "email": "teacher1_sanjose@example.com",
        "password": "madrid123",
        "full_name": "Profesor 1 San José",
        "role": UserRole.teacher,
        "school_name": "Colegio San José",
        "is_admin": False
    },
    {
        "username": "director_norte",
        "email": "director_norte@example.com",
        "password": "madrid123",
        "full_name": "Director Escuela Norte",
        "role": UserRole.director,
        "school_name": "Escuela Primaria Norte",
        "is_admin": False
    },
]

print("\n🔄 Creating test users with different roles...\n")
print("="*60)

# Update existing admin user
admin = db.query(User).filter(User.username == "admin").first()
if admin:
    admin.role = UserRole.admin
    db.commit()
    print(f"✅ Updated admin user with role: {admin.role.value}")
else:
    print("⚠️  Admin user not found")

print("-"*60)

# Create new test users
for user_data in test_users:
    # Check if user already exists
    existing = db.query(User).filter(User.username == user_data["username"]).first()
    if existing:
        print(f"⚠️  User {user_data['username']} already exists, skipping...")
        continue
    
    # Find school
    school = db.query(School).filter(School.name == user_data["school_name"]).first()
    if not school:
        print(f"❌ School '{user_data['school_name']}' not found for user {user_data['username']}")
        continue
    
    # Create user
    new_user = User(
        username=user_data["username"],
        email=user_data["email"],
        hashed_password=get_password_hash(user_data["password"]),
        full_name=user_data["full_name"],
        role=user_data["role"],
        school_id=school.id,
        is_admin=user_data["is_admin"],
        is_active=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"✅ Created user: {new_user.username} ({new_user.role.value}) - School: {school.name}")

print("="*60)

# List all users
print("\n📋 All users in database:\n")
print("="*60)
users = db.query(User).all()
for user in users:
    school_name = user.school.name if user.school else "No school"
    print(f"Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Role: {user.role.value}")
    print(f"  School: {school_name}")
    print(f"  Is Admin: {user.is_admin}")
    print("-"*60)

db.close()

print("\n✨ Done! Test users created successfully.\n")
print("You can now login with:")
print("  - admin/madrid123 (Admin - access to everything)")
print("  - director_sj/madrid123 (Director - Colegio San José)")
print("  - director_norte/madrid123 (Director - Escuela Norte)")
print("  - teacher1_sj/madrid123 (Teacher - Colegio San José)")
print()
