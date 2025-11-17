from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum


class UserRole(enum.Enum):
    admin = "admin"
    director = "director"
    teacher = "teacher"


class School(Base):
    __tablename__ = "schools"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    address = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    timezone = Column(String, default="Europe/Madrid")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    students = relationship("Student", back_populates="school")
    users = relationship("User", back_populates="school")
    
    def __repr__(self):
        return f"<School {self.name}>"


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)  # Kept for backward compatibility
    role = Column(Enum(UserRole), default=UserRole.teacher, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=True)  # Required for teachers/directors, optional for admins
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    school = relationship("School", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.username} ({self.role.value})>"


class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    class_name = Column(String, nullable=False)
    parent_email = Column(String, nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    qr_code_path = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    school = relationship("School", back_populates="students")
    checkins = relationship("CheckIn", back_populates="student")
    
    def __repr__(self):
        return f"<Student {self.name} ({self.student_id})>"


class CheckIn(Base):
    __tablename__ = "checkins"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    checkin_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    checkout_time = Column(DateTime, nullable=True)
    is_late = Column(Boolean, default=False)
    email_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    student = relationship("Student", back_populates="checkins")
    
    def __repr__(self):
        return f"<CheckIn {self.student_id} at {self.checkin_time}>"


class AbsenceNotification(Base):
    __tablename__ = "absence_notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    notification_date = Column(DateTime, default=datetime.utcnow, nullable=False)  # The date of absence
    email_sent = Column(Boolean, default=False)
    email_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    student = relationship("Student")
    
    def __repr__(self):
        return f"<AbsenceNotification for student {self.student_id} on {self.notification_date}>"


class JustificationType(enum.Enum):
    absence = "absence"  # Full day absence
    tardiness = "tardiness"  # Late arrival
    early_dismissal = "early_dismissal"  # Leaving early


class JustificationStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Justification(Base):
    __tablename__ = "justifications"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    justification_type = Column(Enum(JustificationType), nullable=False)
    date = Column(DateTime, nullable=False)  # The date being justified
    reason = Column(String, nullable=False)  # Explanation
    status = Column(Enum(JustificationStatus), default=JustificationStatus.pending)
    submitted_by = Column(String, nullable=False)  # Email of who submitted
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Staff who reviewed
    reviewed_at = Column(DateTime, nullable=True)
    notes = Column(String, nullable=True)  # Staff notes
    
    # Relationships
    student = relationship("Student")
    reviewer = relationship("User")
    
    def __repr__(self):
        return f"<Justification {self.justification_type.value} for student {self.student_id} on {self.date}>"


class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(String, nullable=False)
    description = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"


class StudentDietaryNeeds(Base):
    """Track dietary requirements and allergies for each student"""
    __tablename__ = "student_dietary_needs"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, unique=True)
    has_allergies = Column(Boolean, default=False)
    allergies_description = Column(String, nullable=True)  # E.g., "Peanut, Gluten"
    has_special_diet = Column(Boolean, default=False)
    special_diet_description = Column(String, nullable=True)  # E.g., "Vegetarian, Vegan, Kosher"
    notes = Column(String, nullable=True)  # Additional notes for kitchen
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    student = relationship("Student")
    
    def __repr__(self):
        return f"<StudentDietaryNeeds for student {self.student_id}>"


class KitchenAttendance(Base):
    """Daily snapshot of student attendance for kitchen meal planning - captured at 10 AM"""
    __tablename__ = "kitchen_attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    snapshot_date = Column(DateTime, nullable=False)  # Date of the snapshot (10 AM)
    class_name = Column(String, nullable=False)  # E.g., "5A", "4B"
    
    # Attendance counts
    total_students = Column(Integer, default=0)
    present = Column(Integer, default=0)  # Students who checked in
    absent = Column(Integer, default=0)  # Students who didn't check in (9:01 AM passed)
    will_arrive_later = Column(Integer, default=0)  # Students we expect to arrive later (inferred)
    
    # Dietary tracking
    with_allergies = Column(Integer, default=0)
    with_special_diet = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    school = relationship("School")
    
    def __repr__(self):
        return f"<KitchenAttendance {self.class_name} on {self.snapshot_date}>"
