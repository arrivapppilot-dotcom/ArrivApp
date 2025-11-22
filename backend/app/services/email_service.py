import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from datetime import datetime
from app.core.config import get_settings

settings = get_settings()


async def send_email(to_email: str, subject: str, body: str):
    """Send an email via SMTP."""
    message = MIMEMultipart()
    message["From"] = f"{settings.FROM_NAME} <{settings.FROM_EMAIL}>"
    message["To"] = to_email
    message["Subject"] = subject
    
    message.attach(MIMEText(body, "plain"))
    
    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False


async def send_checkin_notification(
    parent_email: str, 
    student_name: str, 
    class_name: str, 
    checkin_time: datetime,
    is_late: bool = False
):
    """Send check-in notification to parent."""
    formatted_time = checkin_time.strftime("%H:%M")
    
    if is_late:
        subject = f"⚠️ ArrivApp: {student_name} ha llegado tarde al cole"
        body = f"""¡Hola!

Te informamos que {student_name} ({class_name}) ha registrado su entrada en el colegio a las {formatted_time}h.

⚠️ AVISO: La entrada se ha registrado después del horario establecido (9:01h).

Si hay alguna razón justificada para el retraso, por favor contacta con el colegio.

Gracias por participar en el programa piloto de ArrivApp.

---
Este es un mensaje automático. Por favor no responder.
"""
    else:
        subject = f"✅ ArrivApp: {student_name} ha llegado al cole"
        body = f"""¡Hola!

Buenas noticias.

{student_name} ({class_name}) ha registrado su entrada en el colegio a las {formatted_time}h.

Gracias por participar en el programa piloto de ArrivApp.

---
Este es un mensaje automático. Por favor no responder.
"""
    
    return await send_email(parent_email, subject, body)


async def send_absent_report(absent_students: List[tuple], admin_email: str):
    """Send daily absent report to admin."""
    if not absent_students:
        return True
    
    current_time = datetime.now().strftime('%H:%M')
    current_date = datetime.now().strftime('%d/%m/%Y')
    
    subject = f"📋 ArrivApp - Reporte de Ausencias ({current_date})"
    body = f"""Hola,

A las {current_time}, los siguientes alumnos NO han realizado el check-in hoy:

"""
    
    for name, class_name, parent_email in absent_students:
        body += f"• {name} ({class_name}) - Email padre: {parent_email}\n"
    
    body += f"\n\nTotal de ausentes: {len(absent_students)} alumnos\n"
    body += "\nEste es un reporte automático generado por ArrivApp.\n"
    body += "Por favor, verifica estas ausencias y contacta a los padres si es necesario.\n\n"
    body += "---\nArrivApp v2.0"
    
    return await send_email(admin_email, subject, body)


async def send_justification_submitted_notification(
    parent_email: str,
    student_name: str,
    justification_type: str,
    date_str: str
):
    """Send confirmation email when parent submits a justification."""
    type_labels = {
        'absence': 'Ausencia',
        'tardiness': 'Retraso',
        'early_dismissal': 'Salida Anticipada'
    }
    
    justification_label = type_labels.get(justification_type, justification_type)
    
    subject = f"ArrivApp: Justificante enviado para {student_name}"
    body = f"""Hola,

Confirmamos que hemos recibido tu justificante para {student_name}.

Detalles:
- Estudiante: {student_name}
- Tipo: {justification_label}
- Fecha: {date_str}
- Estado: Pendiente de revisión

Tu justificante ha sido enviado al colegio. La dirección o maestro lo revisará y te notificaremos sobre su aprobación o rechazo.

Si tienes preguntas, por favor contacta con el colegio.

Gracias por usar ArrivApp.

---
Este es un mensaje automático. Por favor no responder.
"""
    
    return await send_email(parent_email, subject, body)


async def send_justification_reviewed_notification(
    parent_email: str,
    student_name: str,
    justification_type: str,
    date_str: str,
    status: str,
    notes: str = None
):
    """Send notification when justification is approved or rejected."""
    type_labels = {
        'absence': 'Ausencia',
        'tardiness': 'Retraso',
        'early_dismissal': 'Salida Anticipada'
    }
    
    status_labels = {
        'approved': 'Aprobado',
        'rejected': 'Rechazado'
    }
    
    justification_label = type_labels.get(justification_type, justification_type)
    status_label = status_labels.get(status, status)
    status_icon = "✓" if status == "approved" else "✗"
    
    subject = f"ArrivApp: Justificante {status_label} para {student_name}"
    body = f"""{status_icon} Hola,

Te informamos que tu justificante ha sido revisado.

Detalles:
- Estudiante: {student_name}
- Tipo: {justification_label}
- Fecha: {date_str}
- Estado: {status_label}
"""
    
    if notes:
        body += f"- Observaciones: {notes}\n"
    
    if status == "approved":
        body += "\nTu justificante ha sido aprobado. Gracias por mantenernos informados.\n"
    else:
        body += "\nDesafortunadamente, tu justificante ha sido rechazado. "
        body += "Por favor, contacta con el colegio si tienes preguntas al respecto.\n"
    
    body += "\n---\nEste es un mensaje automático. Por favor no responder."
    
    return await send_email(parent_email, subject, body)
