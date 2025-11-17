from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    admin = "admin"
    director = "director"
    teacher = "teacher"


# School Schemas
class SchoolBase(BaseModel):
    name: str
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    timezone: str = "Europe/Madrid"


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class School(SchoolBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.teacher


class UserCreate(UserBase):
    password: str
    school_id: Optional[int] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    school_id: Optional[int] = None
    role: Optional[UserRole] = None


class User(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    role: UserRole
    school_id: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserWithSchool(User):
    school: Optional[School] = None


# Student Schemas
class StudentBase(BaseModel):
    student_id: str
    name: str
    class_name: str
    parent_email: Optional[str] = None  # Changed from EmailStr to allow invalid emails from faker


class StudentCreate(StudentBase):
    school_id: int


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    class_name: Optional[str] = None
    parent_email: Optional[str] = None  # Changed from EmailStr to allow invalid emails from faker
    is_active: Optional[bool] = None
    school_id: Optional[int] = None


class Student(StudentBase):
    id: int
    school_id: int
    qr_code_path: Optional[str] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class StudentWithSchool(Student):
    school: School


# CheckIn Schemas
class CheckInBase(BaseModel):
    student_id: int


class CheckInCreate(BaseModel):
    student_id_code: str  # The student ID from QR code


class CheckIn(BaseModel):
    id: int
    student_id: int
    checkin_time: datetime
    checkout_time: Optional[datetime] = None
    is_late: bool
    email_sent: bool
    
    class Config:
        from_attributes = True


class CheckInWithStudent(CheckIn):
    student: Student


# Auth Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    school_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str
    password: str


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_present: int
    total_absent: int
    total_late: int
    date: str


class CheckInLog(BaseModel):
    checkin_time: str
    student_name: str
    school_name: str
    checkout_time: Optional[str] = None


class LateStudent(BaseModel):
    name: str
    time: str
    school_name: str
    email_sent: bool


class AbsentStudent(BaseModel):
    id: int
    name: str
    class_name: str
    school_name: str
    email_sent: bool = False


class DashboardData(BaseModel):
    stats: DashboardStats
    checkins: list[CheckInLog]
    late_students: list[LateStudent]
    absent_students: list[AbsentStudent]


# Justification Schemas
class JustificationBase(BaseModel):
    student_id: int
    justification_type: str  # "absence", "tardiness", "early_dismissal"
    date: datetime
    reason: str


class JustificationCreate(JustificationBase):
    submitted_by: str  # Email of submitter


class JustificationUpdate(BaseModel):
    status: Optional[str] = None  # "pending", "approved", "rejected"
    notes: Optional[str] = None


class Justification(JustificationBase):
    id: int
    status: str
    submitted_by: str
    submitted_at: datetime
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None
    student_name: Optional[str] = None
    
    class Config:
        from_attributes = True
