# Justification Notification System - ArrivApp

## Overview
The justification notification system automatically sends emails to parents at key stages of the justification workflow, keeping them informed about the status of their submitted justifications.

## Notification Types

### 1. Justification Submission Confirmation
**Trigger:** Parent submits a new justification  
**Recipients:** Parent email (from justification submission)  
**Timing:** Immediately after justification is created  

**Email Content:**
```
Subject: ArrivApp: Justificante enviado para [Student Name]

Hola,

Confirmamos que hemos recibido tu justificante para [Student Name].

Detalles:
- Estudiante: [Student Name]
- Tipo: [Ausencia | Retraso | Salida Anticipada]
- Fecha: [DD/MM/YYYY]
- Estado: Pendiente de revisión

Tu justificante ha sido enviado al colegio. La dirección o maestro lo revisará 
y te notificaremos sobre su aprobación o rechazo.

Si tienes preguntas, por favor contacta con el colegio.

Gracias por usar ArrivApp.
```

**Justification Types:**
- `absence`: Ausencia
- `tardiness`: Retraso
- `early_dismissal`: Salida Anticipada

---

### 2. Justification Review Notification (Approved)
**Trigger:** Staff member (teacher/director/admin) approves a justification  
**Recipients:** Parent email (from justification submission)  
**Timing:** Immediately after justification is approved  

**Email Content:**
```
Subject: ArrivApp: Justificante Aprobado para [Student Name]

✓ Hola,

Te informamos que tu justificante ha sido revisado.

Detalles:
- Estudiante: [Student Name]
- Tipo: [Ausencia | Retraso | Salida Anticipada]
- Fecha: [DD/MM/YYYY]
- Estado: Aprobado
- Observaciones: [If provided]

Tu justificante ha sido aprobado. Gracias por mantenernos informados.
```

---

### 3. Justification Review Notification (Rejected)
**Trigger:** Staff member (teacher/director/admin) rejects a justification  
**Recipients:** Parent email (from justification submission)  
**Timing:** Immediately after justification is rejected  

**Email Content:**
```
Subject: ArrivApp: Justificante Rechazado para [Student Name]

✗ Hola,

Te informamos que tu justificante ha sido revisado.

Detalles:
- Estudiante: [Student Name]
- Tipo: [Ausencia | Retraso | Salida Anticipada]
- Fecha: [DD/MM/YYYY]
- Estado: Rechazado
- Observaciones: [If provided]

Desafortunadamente, tu justificante ha sido rechazado. Por favor, contacta 
con el colegio si tienes preguntas al respecto.
```

---

## Implementation Details

### Email Service Functions

#### `send_justification_submitted_notification()`
Located in: `app/services/email_service.py`

```python
async def send_justification_submitted_notification(
    parent_email: str,
    student_name: str,
    justification_type: str,
    date_str: str
)
```

**Parameters:**
- `parent_email`: Parent's email address
- `student_name`: Name of the student
- `justification_type`: Type of justification ('absence', 'tardiness', 'early_dismissal')
- `date_str`: Formatted date string (DD/MM/YYYY)

**Returns:** Boolean indicating success/failure

---

#### `send_justification_reviewed_notification()`
Located in: `app/services/email_service.py`

```python
async def send_justification_reviewed_notification(
    parent_email: str,
    student_name: str,
    justification_type: str,
    date_str: str,
    status: str,
    notes: str = None
)
```

**Parameters:**
- `parent_email`: Parent's email address
- `student_name`: Name of the student
- `justification_type`: Type of justification ('absence', 'tardiness', 'early_dismissal')
- `date_str`: Formatted date string (DD/MM/YYYY)
- `status`: Approval status ('approved' or 'rejected')
- `notes`: Optional notes from the reviewer

**Returns:** Boolean indicating success/failure

---

### API Endpoints Integration

#### POST `/api/justifications/` (Create Justification)
When a parent submits a justification:
1. Creates the justification record in the database
2. Automatically sends `send_justification_submitted_notification()` email
3. Gracefully handles email failures (doesn't fail the request)

**Workflow:**
```
Parent submits form
     ↓
Validate parent email matches student
     ↓
Create justification (status: pending)
     ↓
Send confirmation email ✉️
     ↓
Return justification object
```

---

#### PUT `/api/justifications/{justification_id}` (Update Justification Status)
When staff approves/rejects a justification:
1. Updates justification status to approved/rejected
2. Records reviewer ID and timestamp
3. Automatically sends `send_justification_reviewed_notification()` email
4. Gracefully handles email failures (doesn't fail the request)

**Workflow:**
```
Staff clicks Approve/Reject
     ↓
Update status + reviewer info
     ↓
Send approval/rejection email ✉️
     ↓
Return updated justification object
```

---

## Email Configuration

The email system uses SMTP settings from environment variables:
- `SMTP_HOST`: SMTP server hostname
- `SMTP_PORT`: SMTP server port
- `SMTP_USER`: SMTP authentication username
- `SMTP_PASSWORD`: SMTP authentication password
- `FROM_NAME`: Display name for sender
- `FROM_EMAIL`: Email address sender

See `.env` file for current configuration.

---

## Error Handling

If an email fails to send:
- A warning is logged to console
- The API request continues normally (doesn't fail)
- Parents might not receive the notification but the data is saved

**Monitor logs for email failures:**
```
Warning: Failed to send justification submission email: [error details]
Warning: Failed to send justification review email: [error details]
```

---

## Testing Emails

To test the justification notification system:

### 1. Test Submission Email
```bash
# Create a justification
curl -X POST "http://localhost:8000/api/justifications/" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "justification_type": "absence",
    "date": "2025-11-22",
    "reason": "Medical appointment",
    "submitted_by": "parent@example.com"
  }'
```

Check email inbox for confirmation message.

### 2. Test Approval/Rejection Email
```bash
# Approve a justification
curl -X PUT "http://localhost:8000/api/justifications/1" \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "notes": "Appointment confirmation provided"
  }'
```

Check email inbox for approval message.

---

## Future Enhancements

Possible improvements:
1. **Email Templates:** Move to HTML email templates for better formatting
2. **Digest Emails:** Group multiple notifications into a single daily digest
3. **SMS Option:** Send SMS notifications for urgent updates
4. **Email Preferences:** Allow parents to choose notification frequency
5. **Retry Logic:** Automatically retry failed email sends
6. **Queue System:** Use message queue (Celery, RabbitMQ) for reliable delivery
7. **Read Receipts:** Track email open rates and link clicks
8. **Multi-language:** Support email notifications in different languages

---

## Support

For issues with email notifications:
1. Check SMTP configuration in `.env` file
2. Verify parent email is valid and accessible
3. Check server logs for warning/error messages
4. Contact system administrator if emails are not being sent
