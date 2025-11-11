# This file makes the models directory a Python package
from app.models.models import User, Student, CheckIn, Settings
from app.models.schemas import (
    UserCreate, UserUpdate, User as UserSchema,
    StudentCreate, StudentUpdate, Student as StudentSchema,
    CheckInCreate, CheckIn as CheckInSchema,
    Token, LoginRequest, DashboardData
)

__all__ = [
    "User", "Student", "CheckIn", "Settings",
    "UserCreate", "UserUpdate", "UserSchema",
    "StudentCreate", "StudentUpdate", "StudentSchema",
    "CheckInCreate", "CheckInSchema",
    "Token", "LoginRequest", "DashboardData"
]
