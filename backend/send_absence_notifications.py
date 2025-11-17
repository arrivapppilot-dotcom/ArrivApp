#!/usr/bin/env python3
"""
Absence Notification Service
Runs at 9:01 AM (or on-demand) to identify students who haven't checked in
and sends absence notification emails to their parents.
"""

import os
import sys
import smtplib
from datetime import datetime, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import and_
from typing import List, Dict

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.models import Student, CheckIn, School, AbsenceNotification
from app.core.config import get_settings

settings = get_settings()


class AbsenceNotificationService:
    """Service to send absence notifications at 9:01 AM"""
    
    def __init__(self):
        self.db = SessionLocal()
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.sender_email = settings.SMTP_USERNAME
        self.sender_password = settings.SMTP_PASSWORD
        self.admin_email = settings.ADMIN_EMAIL
        self.results = {
            "total_absent": 0,
            "emails_sent": 0,
            "emails_failed": 0,
            "absent_students": []
        }
    
    def get_absent_students_by_school(self) -> Dict[int, List[Dict]]:
        """Get list of students who haven't checked in by 9:01 AM, grouped by school"""
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_time = datetime.now().replace(hour=9, minute=1, second=0, microsecond=0)
        
        # Check if we're past 9:01 AM
        if datetime.now() < cutoff_time:
            print(f"⏰ Current time {datetime.now().strftime('%H:%M:%S')} is before 9:01 AM. Skipping absence notifications.")
            return {}
        
        # Get all active students
        all_students = self.db.query(Student).filter(Student.is_active == True).all()
        
        # Get students who have checked in today (at any time)
        checkins_today = self.db.query(CheckIn).filter(
            CheckIn.checkin_time >= today
        ).all()
        
        checked_in_ids = set(c.student_id for c in checkins_today)
        
        # Find absent students
        absent_by_school = {}
        
        for student in all_students:
            if student.id not in checked_in_ids:
                # This student hasn't checked in
                if student.school_id not in absent_by_school:
                    absent_by_school[student.school_id] = []
                
                absent_by_school[student.school_id].append({
                    "id": student.id,
                    "name": student.name,
                    "class_name": student.class_name,
                    "parent_email": student.parent_email,
                    "school": student.school
                })
                
                self.results["absent_students"].append({
                    "name": student.name,
                    "class": student.class_name,
                    "school": student.school.name if student.school else "Unknown"
                })
        
        self.results["total_absent"] = len(self.results["absent_students"])
        return absent_by_school
    
    def send_absence_notification_email(self, parent_email: str, student_name: str, 
                                       school_name: str, class_name: str) -> bool:
        """Send absence notification email to parent"""
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"⚠️ Ausencia de {student_name} - {school_name}"
            msg["From"] = self.sender_email
            msg["To"] = parent_email
            
            # HTML email template
            html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }}
                        .header {{ background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); color: white; padding: 2rem; text-align: center; }}
                        .header h1 {{ margin: 0; font-size: 1.5rem; }}
                        .content {{ padding: 2rem; }}
                        .alert-box {{ background: #fef2f2; border-left: 4px solid #dc2626; padding: 1rem; margin: 1rem 0; border-radius: 4px; }}
                        .student-info {{ background: #f9fafb; padding: 1rem; border-radius: 4px; margin: 1rem 0; }}
                        .student-info p {{ margin: 0.5rem 0; }}
                        .label {{ font-weight: 600; color: #374151; }}
                        .footer {{ background: #f9fafb; padding: 1rem; text-align: center; font-size: 0.875rem; color: #6b7280; border-top: 1px solid #e5e7eb; }}
                        .action-btn {{ background: #dc2626; color: white; padding: 0.75rem 1.5rem; border-radius: 4px; text-decoration: none; display: inline-block; margin-top: 1rem; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>⚠️ Aviso de Ausencia</h1>
                        </div>
                        <div class="content">
                            <p>Estimado/a Padre/Madre/Tutor,</p>
                            
                            <div class="alert-box">
                                <strong>Se ha registrado una ausencia en la escuela.</strong>
                            </div>
                            
                            <p>Información del alumno/a que no ha llegado a la escuela:</p>
                            
                            <div class="student-info">
                                <p><span class="label">Nombre:</span> {student_name}</p>
                                <p><span class="label">Clase:</span> {class_name}</p>
                                <p><span class="label">Escuela:</span> {school_name}</p>
                                <p><span class="label">Hora del aviso:</span> {datetime.now().strftime('%H:%M')} (No ha registrado entrada antes de las 9:01 AM)</p>
                            </div>
                            
                            <p><strong>Acción requerida:</strong></p>
                            <ul>
                                <li>Si su hijo/a está enfermo/a o no puede asistir, por favor proporcione una justificación.</li>
                                <li>Si ya está en la escuela, por favor solicite que se registre la entrada.</li>
                                <li>Si hay un problema, contacte inmediatamente con la escuela.</li>
                            </ul>
                            
                            <p>Gracias por su atención.</p>
                            <p>Sistema de Asistencia ArrivApp</p>
                        </div>
                        <div class="footer">
                            <p>Este es un mensaje automático. No responda a este correo electrónico.</p>
                            <p>© 2025 ArrivApp - Sistema de Control de Asistencia</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            part = MIMEText(html, "html")
            msg.attach(part)
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"  ✓ Email sent to {parent_email} for {student_name}")
            return True
        
        except Exception as e:
            print(f"  ✗ Failed to send email to {parent_email}: {e}")
            return False
    
    def send_admin_summary(self, absent_data: Dict[int, List[Dict]]) -> bool:
        """Send summary email to admin about absent students"""
        
        if not absent_data or self.results["total_absent"] == 0:
            return True
        
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"📊 Resumen de Ausencias - {datetime.now().strftime('%Y-%m-%d')}"
            msg["From"] = self.sender_email
            msg["To"] = self.admin_email
            
            # Build summary table
            summary_html = "<table style='width: 100%; border-collapse: collapse;'>"
            summary_html += "<tr style='background: #f3f4f6;'><th style='border: 1px solid #d1d5db; padding: 0.5rem;'>Escuela</th><th style='border: 1px solid #d1d5db; padding: 0.5rem;'>Alumno</th><th style='border: 1px solid #d1d5db; padding: 0.5rem;'>Clase</th><th style='border: 1px solid #d1d5db; padding: 0.5rem;'>Email Padres</th></tr>"
            
            for school_id, students in absent_data.items():
                school_name = students[0]["school"].name if students and students[0]["school"] else "Unknown"
                for student in students:
                    summary_html += f"""
                    <tr style='border-bottom: 1px solid #e5e7eb;'>
                        <td style='border: 1px solid #d1d5db; padding: 0.5rem;'>{school_name}</td>
                        <td style='border: 1px solid #d1d5db; padding: 0.5rem;'>{student['name']}</td>
                        <td style='border: 1px solid #d1d5db; padding: 0.5rem;'>{student['class_name']}</td>
                        <td style='border: 1px solid #d1d5db; padding: 0.5rem;'>{student['parent_email']}</td>
                    </tr>
                    """
            
            summary_html += "</table>"
            
            html = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }}
                        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); overflow: hidden; }}
                        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; text-align: center; }}
                        .header h1 {{ margin: 0; }}
                        .content {{ padding: 2rem; }}
                        .stats {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin: 1.5rem 0; }}
                        .stat-card {{ background: #f9fafb; border-left: 4px solid #667eea; padding: 1rem; border-radius: 4px; }}
                        .stat-value {{ font-size: 2rem; font-weight: 700; color: #667eea; }}
                        .stat-label {{ font-size: 0.875rem; color: #6b7280; }}
                        .footer {{ background: #f9fafb; padding: 1rem; text-align: center; font-size: 0.875rem; color: #6b7280; border-top: 1px solid #e5e7eb; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h1>📊 Resumen de Ausencias</h1>
                            <p>{datetime.now().strftime('%d de %B de %Y')}</p>
                        </div>
                        <div class="content">
                            <p>Estimado Administrador,</p>
                            
                            <div class="stats">
                                <div class="stat-card">
                                    <div class="stat-value">{self.results["total_absent"]}</div>
                                    <div class="stat-label">Total de Ausencias</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">{self.results["emails_sent"]}</div>
                                    <div class="stat-label">Emails Enviados</div>
                                </div>
                            </div>
                            
                            <h3>Alumnos sin marcar entrada (antes de 9:01 AM):</h3>
                            {summary_html}
                            
                            <p style='margin-top: 2rem; color: #6b7280; font-size: 0.875rem;'>
                                Los padres de los alumnos listados han sido notificados automáticamente.
                            </p>
                        </div>
                        <div class="footer">
                            <p>Este es un mensaje automático del Sistema ArrivApp</p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            part = MIMEText(html, "html")
            msg.attach(part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            print(f"\n✓ Admin summary sent to {self.admin_email}")
            return True
        
        except Exception as e:
            print(f"✗ Failed to send admin summary: {e}")
            return False
    
    def create_absence_records(self, absent_data: Dict[int, List[Dict]]) -> None:
        """Create AbsenceNotification records in database"""
        
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for school_id, students in absent_data.items():
            for student_data in students:
                # Check if notification already exists for today
                existing = self.db.query(AbsenceNotification).filter(
                    and_(
                        AbsenceNotification.student_id == student_data["id"],
                        AbsenceNotification.notification_date >= today
                    )
                ).first()
                
                if not existing:
                    absence_notif = AbsenceNotification(
                        student_id=student_data["id"],
                        notification_date=datetime.now(),
                        email_sent=True,
                        email_sent_at=datetime.now()
                    )
                    self.db.add(absence_notif)
        
        self.db.commit()
    
    def run(self) -> Dict:
        """Main execution method"""
        
        print("\n" + "="*70)
        print("🔔 ArrivApp - Absence Notification Service")
        print("="*70)
        print(f"Current time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"Checking for students who haven't checked in by 9:01 AM...")
        print("="*70 + "\n")
        
        try:
            # Get absent students grouped by school
            absent_data = self.get_absent_students_by_school()
            
            if not absent_data:
                print("✓ No absent students or current time is before 9:01 AM")
                self.db.close()
                return self.results
            
            print(f"\n📧 Found {self.results['total_absent']} absent students. Sending notifications...\n")
            
            # Send individual emails to parents
            for school_id, students in absent_data.items():
                print(f"\n🏫 {students[0]['school'].name if students[0]['school'] else 'Unknown School'}:")
                
                for student in students:
                    email_sent = self.send_absence_notification_email(
                        student["parent_email"],
                        student["name"],
                        student["school"].name if student["school"] else "Unknown",
                        student["class_name"]
                    )
                    
                    if email_sent:
                        self.results["emails_sent"] += 1
                    else:
                        self.results["emails_failed"] += 1
            
            # Create records in database
            self.create_absence_records(absent_data)
            
            # Send admin summary
            self.send_admin_summary(absent_data)
            
            # Print summary
            print("\n" + "="*70)
            print("📊 Summary")
            print("="*70)
            print(f"Total absent students: {self.results['total_absent']}")
            print(f"✓ Emails sent: {self.results['emails_sent']}")
            print(f"✗ Emails failed: {self.results['emails_failed']}")
            print("="*70 + "\n")
            
            return self.results
        
        finally:
            self.db.close()


if __name__ == "__main__":
    service = AbsenceNotificationService()
    results = service.run()
