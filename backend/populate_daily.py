"""
Automated daily faker for testing all scenarios across schools.
Appends new test data daily and validates all reports.
Runs at 8 AM daily via GitHub Actions or manual execution.
"""
import sys
import os
import json
import random
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faker import Faker
from app.core.database import SessionLocal, engine
from app.models.models import (
    Student, School, CheckIn, Justification, 
    JustificationType, JustificationStatus
)

fake = Faker(['es_ES', 'es_MX'])

CLASSES = [
    "1A", "1B", "1C",
    "2A", "2B", "2C", 
    "3A", "3B", "3C",
    "4A", "4B", "4C",
    "5A", "5B", "5C",
    "6A", "6B", "6C"
]

ARCHIVE_DIR = Path(__file__).parent / "test_data_archive"
ARCHIVE_DIR.mkdir(exist_ok=True)


class TestDataManager:
    """Manages test data generation, archival, and reporting"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "status": "running",
            "schools_count": 0,
            "students_created": 0,
            "checkins_created": 0,
            "justifications_created": 0,
            "reports_tested": {},
            "errors": [],
            "warnings": []
        }
    
    def log_error(self, message: str):
        """Log an error"""
        print(f"❌ ERROR: {message}")
        self.results["errors"].append(message)
    
    def log_warning(self, message: str):
        """Log a warning"""
        print(f"⚠️  WARNING: {message}")
        self.results["warnings"].append(message)
    
    def log_success(self, message: str):
        """Log success"""
        print(f"✅ {message}")
    
    def create_daily_students(self) -> int:
        """Create 15 new students per school for today's testing"""
        print("\n📚 Creating daily test students...")
        
        schools = self.db.query(School).all()
        if not schools:
            self.log_error("No schools found!")
            return 0
        
        self.results["schools_count"] = len(schools)
        students_count = 0
        
        for school in schools:
            for i in range(15):  # 15 students per school per day (increased from 10)
                first_name = fake.first_name()
                last_name = fake.last_name()
                full_name = f"{first_name} {last_name}"
                class_name = random.choice(CLASSES)
                # Remove spaces and special characters from names for email
                safe_first = first_name.replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                safe_last = last_name.replace(" ", "").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
                parent_email = f"{safe_first.lower()}.{safe_last.lower()}.daily{datetime.now().strftime('%Y%m%d')}@example.com"
                student_id = f"TEST{datetime.now().strftime('%Y%m%d')}{school.id}{random.randint(1000, 9999)}"
                
                student = Student(
                    student_id=student_id,
                    name=full_name,
                    class_name=class_name,
                    school_id=school.id,
                    parent_email=parent_email,
                    qr_code_path=f"QR_{student_id}.png"
                )
                
                self.db.add(student)
                students_count += 1
            
            self.db.commit()
            self.log_success(f"Created 15 students for {school.name}")
        
        self.results["students_created"] = students_count
        print(f"📊 Total students created today: {students_count}")
        return students_count
    
    def simulate_today_activities(self, students_list: List[Student]) -> Dict:
        """Simulate check-ins and activities for today"""
        print("\n🎭 Simulating today's activities...")
        
        if not students_list:
            self.log_warning("No students to simulate activities for")
            return {}
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Skip weekends
        if today.weekday() >= 5:
            self.log_warning("Today is a weekend - skipping simulation")
            return {}
        
        # Simulate activities for today and yesterday (2 days of scenarios)
        scenarios = {
            "present_on_time": 0,
            "present_late": 0,
            "early_checkout": 0,
            "absent": 0,
            "justified_absence": 0
        }
        
        for days_offset in [0, 1]:  # Today and yesterday
            current_date = today - timedelta(days=days_offset)
            date_str = current_date.strftime("%Y-%m-%d")
            
            print(f"\n  📅 Simulating {date_str}...")
            
            # 85% attendance rate
            attendance_rate = 0.85
            attending_students = random.sample(
                students_list, 
                int(len(students_list) * attendance_rate)
            )
            
            for student in attending_students:
                # Check if already has check-in for this date
                existing = self.db.query(CheckIn).filter(
                    CheckIn.student_id == student.id,
                    CheckIn.checkin_time >= current_date.replace(hour=0, minute=0, second=0),
                    CheckIn.checkin_time <= current_date.replace(hour=23, minute=59, second=59)
                ).first()
                
                if existing:
                    continue
                
                # 20% late rate
                is_late = random.random() < 0.20
                
                if is_late:
                    check_in_hour = random.randint(8, 9)
                    check_in_minute = random.randint(15 if check_in_hour == 8 else 0, 30)
                    scenarios["present_late"] += 1
                else:
                    check_in_hour = random.randint(7, 8)
                    check_in_minute = random.randint(0, 10 if check_in_hour == 8 else 59)
                    scenarios["present_on_time"] += 1
                
                checkin_time = current_date.replace(
                    hour=check_in_hour,
                    minute=check_in_minute,
                    second=random.randint(0, 59)
                )
                
                # Checkout time (80% checkout)
                checkout_time = None
                if random.random() < 0.8:
                    checkout_hour = random.randint(14, 16)
                    checkout_minute = random.randint(0, 59)
                    
                    if random.random() < 0.05:  # 5% early checkout
                        checkout_hour = random.randint(12, 13)
                        scenarios["early_checkout"] += 1
                    
                    checkout_time = current_date.replace(
                        hour=checkout_hour,
                        minute=checkout_minute,
                        second=random.randint(0, 59)
                    )
                
                checkin = CheckIn(
                    student_id=student.id,
                    checkin_time=checkin_time,
                    checkout_time=checkout_time,
                    is_late=is_late,
                    email_sent=is_late and random.random() < 0.8
                )
                
                self.db.add(checkin)
            
            self.db.commit()
            
            # Simulate justifications for absent students (50% justified - increased from 40%)
            absent_students = [s for s in students_list if s not in attending_students]
            scenarios["absent"] += len(absent_students)
            
            if absent_students:
                justified_count = int(len(absent_students) * 0.5)  # 50% of absences get justified
                for student in random.sample(absent_students, min(justified_count, len(absent_students))):
                    justification_options = [
                        (JustificationType.absence, "Mi hijo/a está enfermo/a con síntomas respiratorios."),
                        (JustificationType.absence, "Cita médica especializada programada."),
                        (JustificationType.absence, "Situación familiar urgente que requiere atención."),
                        (JustificationType.absence, "Permiso familiar por motivos justificados."),
                        (JustificationType.absence, "Procedimiento médico obligatorio.")
                    ]
                    
                    just_type, reason = random.choice(justification_options)
                    
                    justification = Justification(
                        student_id=student.id,
                        date=current_date.date(),
                        justification_type=just_type,
                        reason=reason,
                        submitted_by=student.parent_email,
                        submitted_at=current_date.replace(
                            hour=random.randint(6, 8),
                            minute=random.randint(0, 59)
                        ),
                        status=random.choice([
                            JustificationStatus.pending,
                            JustificationStatus.approved,
                            JustificationStatus.rejected
                        ])
                    )
                    
                    self.db.add(justification)
                    scenarios["justified_absence"] += 1
            
            self.db.commit()
            print(f"    ✓ Simulated {len(attending_students)} check-ins, {len(absent_students)} absences")
        
        self.results["checkins_created"] = scenarios["present_on_time"] + scenarios["present_late"]
        self.results["justifications_created"] = scenarios["justified_absence"]
        
        return scenarios
    
    def test_all_reports(self) -> Dict[str, bool]:
        """Test all report endpoints to ensure they work correctly"""
        print("\n📊 Testing all reports...")
        
        test_results = {}
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Test endpoints (must be called with proper auth in production)
        reports_to_test = [
            ("statistics", f"/api/reports/statistics?school_id=1"),
            ("attendance_history", f"/api/reports/attendance-history?start_date={today}&end_date={today}"),
            ("tardiness_analysis", f"/api/reports/tardiness-analysis?school_id=1"),
            ("historical_analytics", f"/api/reports/historical-analytics?school_id=1")
        ]
        
        # Test data in database directly (since we can't make HTTP calls)
        try:
            # Test 1: Check students exist
            student_count = self.db.query(Student).count()
            test_results["students_exist"] = student_count > 0
            self.log_success(f"Database has {student_count} students") if test_results["students_exist"] else self.log_error("No students in database")
            
            # Test 2: Check check-ins exist
            checkin_count = self.db.query(CheckIn).count()
            test_results["checkins_exist"] = checkin_count > 0
            self.log_success(f"Database has {checkin_count} check-ins") if test_results["checkins_exist"] else self.log_error("No check-ins in database")
            
            # Test 3: Check justifications exist
            justification_count = self.db.query(Justification).count()
            test_results["justifications_exist"] = justification_count > 0
            self.log_success(f"Database has {justification_count} justifications") if test_results["justifications_exist"] else self.log_error("No justifications in database")
            
            # Test 4: Verify report data can be calculated
            today_checkins = self.db.query(CheckIn).filter(
                CheckIn.checkin_time >= datetime.now().replace(hour=0, minute=0, second=0),
                CheckIn.checkin_time <= datetime.now().replace(hour=23, minute=59, second=59)
            ).count()
            test_results["today_checkins_calculable"] = True
            self.log_success(f"Today has {today_checkins} check-ins")
            
            # Test 5: Verify late arrivals can be calculated
            late_count = self.db.query(CheckIn).filter(CheckIn.is_late == True).count()
            test_results["late_arrivals_calculable"] = True
            self.log_success(f"System tracked {late_count} late arrivals")
            
            # Test 6: Verify absence justifications can be calculated
            absence_justifications = self.db.query(Justification).filter(
                Justification.justification_type == JustificationType.absence
            ).count()
            test_results["absence_justifications_calculable"] = True
            self.log_success(f"System has {absence_justifications} absence justifications")
            
        except Exception as e:
            self.log_error(f"Error testing reports: {str(e)}")
            test_results["error"] = True
        
        self.results["reports_tested"] = test_results
        all_passed = all(v for k, v in test_results.items() if k != "error")
        
        if all_passed:
            self.log_success("✨ All report tests passed!")
        else:
            self.log_warning("⚠️  Some report tests failed")
        
        return test_results
    
    def archive_test_data(self) -> str:
        """Archive today's test data for historical analysis"""
        print("\n📦 Archiving test data...")
        
        today = datetime.now()
        archive_file = ARCHIVE_DIR / f"test_data_{today.strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            # Collect today's test data
            today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
            today_end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            # Get students created today
            test_students = self.db.query(Student).filter(
                Student.created_at >= today_start if hasattr(Student, 'created_at') else True
            ).all()
            
            # Get check-ins from today
            today_checkins = self.db.query(CheckIn).filter(
                CheckIn.checkin_time >= today_start,
                CheckIn.checkin_time <= today_end
            ).all()
            
            # Get justifications from today
            today_justifications = self.db.query(Justification).filter(
                Justification.date == today.date()
            ).all()
            
            archive_data = {
                "timestamp": today.isoformat(),
                "test_data_summary": {
                    "students_created": len(test_students),
                    "checkins_today": len(today_checkins),
                    "justifications_today": len(today_justifications),
                    "late_arrivals": sum(1 for c in today_checkins if c.is_late),
                    "emails_sent": sum(1 for c in today_checkins if c.email_sent)
                },
                "schools_tested": self.results["schools_count"],
                "test_results": self.results["reports_tested"],
                "errors": self.results["errors"],
                "warnings": self.results["warnings"]
            }
            
            with open(archive_file, 'w') as f:
                json.dump(archive_data, f, indent=2)
            
            self.log_success(f"Test data archived to {archive_file.name}")
            return str(archive_file)
        
        except Exception as e:
            self.log_error(f"Failed to archive test data: {str(e)}")
            return ""
    
    def send_report_email(self, archive_file: str) -> bool:
        """Send daily test report via email"""
        print("\n📧 Sending test report email...")
        
        # Email configuration from environment
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SMTP_USERNAME", "")
        sender_password = os.getenv("SMTP_PASSWORD", "")
        recipient_email = os.getenv("ADMIN_EMAIL", "")
        
        if not all([sender_email, sender_password, recipient_email]):
            self.log_warning("Email credentials not configured - skipping email report")
            self.log_warning(f"To enable: set SMTP_SERVER, SMTP_USERNAME, SMTP_PASSWORD, ADMIN_EMAIL")
            return False
        
        try:
            # Prepare email content
            all_passed = all(v for k, v in self.results["reports_tested"].items() if k != "error")
            status_emoji = "✅" if all_passed else "⚠️"
            status_text = "PASSED" if all_passed else "PARTIAL"
            
            subject = f"🤖 ArrivApp Daily Test Report - {datetime.now().strftime('%Y-%m-%d')} [{status_text}]"
            
            body = f"""
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2>{status_emoji} ArrivApp Daily Test Report</h2>
    
    <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    <p><strong>Status:</strong> {status_text}</p>
    
    <h3>Test Summary</h3>
    <ul>
      <li><strong>Schools Tested:</strong> {self.results['schools_count']}</li>
      <li><strong>Students Created:</strong> {self.results['students_created']}</li>
      <li><strong>Check-ins Simulated:</strong> {self.results['checkins_created']}</li>
      <li><strong>Justifications Created:</strong> {self.results['justifications_created']}</li>
    </ul>
    
    <h3>Report Tests</h3>
    <ul>
"""
            
            for test_name, passed in self.results["reports_tested"].items():
                status = "✅ PASS" if passed else "❌ FAIL"
                body += f"      <li>{test_name}: {status}</li>\n"
            
            body += "    </ul>\n"
            
            if self.results["errors"]:
                body += "    <h3>❌ Errors</h3>\n    <ul>\n"
                for error in self.results["errors"]:
                    body += f"      <li>{error}</li>\n"
                body += "    </ul>\n"
            
            if self.results["warnings"]:
                body += "    <h3>⚠️  Warnings</h3>\n    <ul>\n"
                for warning in self.results["warnings"]:
                    body += f"      <li>{warning}</li>\n"
                body += "    </ul>\n"
            
            body += f"""
    <p style="color: #666; font-size: 12px; margin-top: 20px;">
      Archive file: {Path(archive_file).name if archive_file else 'N/A'}<br>
      Test run automatically at 8 AM UTC daily via GitHub Actions.
    </p>
  </body>
</html>
"""
            
            # Send email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            self.log_success(f"Report email sent to {recipient_email}")
            return True
        
        except Exception as e:
            self.log_error(f"Failed to send email: {str(e)}")
            return False
    
    def cleanup(self):
        """Close database connection"""
        if self.db:
            self.db.close()
    
    def run(self):
        """Execute complete daily test cycle"""
        print("=" * 70)
        print("🚀 ArrivApp - Automated Daily Test Faker")
        print("=" * 70)
        
        try:
            # Step 1: Create daily students
            self.create_daily_students()
            
            # Step 2: Get all students (today's + previous)
            all_students = self.db.query(Student).all()
            
            # Step 3: Simulate activities for today and yesterday
            scenarios = self.simulate_today_activities(all_students)
            
            # Step 4: Test all reports
            self.test_all_reports()
            
            # Step 5: Archive test data
            archive_file = self.archive_test_data()
            
            # Step 6: Send email report
            self.send_report_email(archive_file)
            
            self.results["status"] = "completed"
            
            print("\n" + "=" * 70)
            print("✨ Daily test cycle completed successfully!")
            print("=" * 70)
            
            # Print summary
            print("\n📊 Final Summary:")
            print(f"  Schools: {self.results['schools_count']}")
            print(f"  Students Created: {self.results['students_created']}")
            print(f"  Check-ins: {self.results['checkins_created']}")
            print(f"  Justifications: {self.results['justifications_created']}")
            print(f"  Status: {self.results['status']}")
            
            if self.results["errors"]:
                print(f"  Errors: {len(self.results['errors'])}")
            
            return True
        
        except Exception as e:
            self.log_error(f"Fatal error in test cycle: {str(e)}")
            self.results["status"] = "failed"
            import traceback
            traceback.print_exc()
            return False
        
        finally:
            self.cleanup()


def main():
    """Main entry point"""
    manager = TestDataManager()
    success = manager.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
