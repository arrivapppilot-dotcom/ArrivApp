#!/usr/bin/env python3
"""
Test absence notification functionality
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Change to backend directory and load environment
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

# Load environment from backend/.env
env_path = os.path.join(backend_dir, '.env')
load_dotenv(env_path)

from app.core.database import SessionLocal
from app.models.models import Student, AbsenceNotification, CheckIn

def test_absence_notifications():
    """Test that absence notifications are being created correctly"""
    db = SessionLocal()
    
    try:
        # Get today's date
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Count total students
        total_students = db.query(Student).filter(Student.is_active == True).count()
        print(f"Total active students: {total_students}")
        
        # Count students who checked in today
        checkins_today = db.query(CheckIn).filter(
            CheckIn.checkin_time >= today
        ).all()
        checked_in_ids = set(c.student_id for c in checkins_today)
        print(f"Students who checked in today: {len(checked_in_ids)}")
        
        # Count absence notifications created today
        absence_notifs = db.query(AbsenceNotification).filter(
            AbsenceNotification.notification_date >= today
        ).all()
        print(f"Absence notifications created today: {len(absence_notifs)}")
        
        # Count how many of those have email_sent = True
        emails_sent = sum(1 for n in absence_notifs if n.email_sent)
        emails_not_sent = len(absence_notifs) - emails_sent
        
        print(f"\nAbsence Notification Breakdown:")
        print(f"  ✓ Emails sent: {emails_sent}")
        print(f"  ✗ Emails not sent: {emails_not_sent}")
        
        # Show sample absence notifications
        if absence_notifs:
            print(f"\nSample absence notifications:")
            for notif in absence_notifs[:3]:
                student = db.query(Student).filter(Student.id == notif.student_id).first()
                print(f"  - {student.name}: email_sent={notif.email_sent}")
        
        # Count absent students (not in checkins)
        absent_students = total_students - len(checked_in_ids)
        print(f"\nAbsent students (no check-in): {absent_students}")
        print(f"Absence notifications should match absent students")
        
        if len(absence_notifs) == absent_students:
            print("✓ Correct! All absent students have notifications")
        else:
            print(f"⚠ Mismatch: {len(absence_notifs)} notifications vs {absent_students} absent students")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_absence_notifications()
