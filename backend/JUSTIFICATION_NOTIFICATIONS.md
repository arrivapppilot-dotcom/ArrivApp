# Justification Notification System - ArrivApp

## Overview
The justification notification system automatically sends emails to parents at key stages of the justification workflow, keeping them informed about the status of their submitted justifications. Teachers, directors, and admins can review and approve/reject justifications.

## Access Levels

### Parents (Public)
- **Submit** justifications via parent portal (public endpoint)
- **View** their own submitted justifications
- **Receive** email notifications when status changes

### Teachers
- **View** justifications for students in their **assigned classes** only (school-scoped)
- **Approve/Reject** justifications for students in their assigned classes
- **Add notes** when reviewing justifications
- **Submit** justifications for students in their assigned classes (on behalf of parents)
- **Delete** justifications for students in their assigned classes
- **Access** via Justifications page with full access to all three tabs

### Directors
- **View** all justifications for students in their school
- **Approve/Reject** justifications for students in their school
- **Add notes** when reviewing justifications
- **Manage** teachers and class assignments
- **Access** via Justifications page with "Revisar (Staff)" tab

### Admins
- **View** all justifications across all schools
- **Approve/Reject** any justification
- **Filter** by school, student, type, status, and date
- **Access** via Justifications page with "Revisar (Staff)" tab

---

## Teacher Justifications Workflow

### Workflow for Teachers

1. **Login** with teacher credentials
2. **Navigate** to Justifications page
3. **Available Tabs (All Functional for Teachers):**
   - **Nueva Justificación:** Submit justifications for students in their assigned classes
   - **Ver Justificaciones:** View all justifications for students in their assigned classes
   - **Revisar (Staff):** Review and approve/reject pending justifications

### Three Main Teacher Actions:

#### 1. Submit Justifications
- Navigate to "Nueva Justificación" tab
- Select a student from their **assigned classes only**
- Fill in type (Ausencia, Retraso, Salida Anticipada), date, and reason
- Submit the justification
- **Parent receives confirmation email**
- Example use case: Teacher submits absence justification for a student's medical appointment

#### 2. Review & Approve/Reject
- Go to "Revisar (Staff)" tab
- See all pending justifications for their assigned classes
- Click "Revisar" on any pending justification
- Review details and add optional notes
- Select "Aprobado" or "Rechazado"
- Submit decision
- **Parent receives approval/rejection email immediately**

#### 3. Delete Justifications
- Go to "Ver Justificaciones" tab
- Find the justification (filters available)
- Click delete/remove (if UI supports it)
- Justification is removed from system

### Teacher Class Scope
- Teachers ONLY see students from their **assigned classes**
- When created/updated, teachers are assigned specific classes (e.g., "3A", "4B")
- All operations (view, submit, review, delete) respect this class assignment
- Cannot see or interact with students outside their classes
- Cannot see justifications from other teachers' classes

### Teacher Permissions
- ✅ Can view justifications for students in their assigned classes
- ✅ Can submit justifications for students in their assigned classes
- ✅ Can approve/reject justifications for students in their assigned classes
- ✅ Can delete justifications for students in their assigned classes
- ✅ Can add notes/observations when reviewing
- ✅ Can filter by status, type, date range
- ❌ Cannot see students outside their assigned classes
- ❌ Cannot modify student records
- ❌ Cannot see other schools' data

### Email Notifications for Teachers
Teachers do NOT receive emails for justifications. However, when they approve/reject a justification, the **parent** receives an email notification immediately.

---

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
