# Email Notifications Setup for Production

## Overview
ArrivApp has automated email notifications for:
- ✅ Student check-in confirmations
- ⚠️ Late arrival alerts
- 🚨 Absent student daily reports (sent at 9:10 AM)
- 🏃 Early checkout notifications

## Current SMTP Configuration (Gmail)

Your local setup uses Gmail with an App Password:
- **SMTP Server:** smtp.gmail.com
- **Port:** 587
- **Email:** arrivapp.pilot@gmail.com
- **App Password:** cbptzlaxecluoxsx

## Step-by-Step: Enable Email Notifications on Render

### 1. Add Environment Variables to Render

Go to your Render backend service dashboard and add these environment variables:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=arrivapp.pilot@gmail.com
SMTP_PASSWORD=cbptzlaxecluoxsx
FROM_EMAIL=arrivapp.pilot@gmail.com
FROM_NAME=ArrivApp
ADMIN_EMAIL=arrivapp.pilot@gmail.com
```

**How to add them:**
1. Go to https://dashboard.render.com
2. Click on your backend service (arrivapp-backend)
3. Go to "Environment" tab
4. Click "Add Environment Variable"
5. Add each variable one by one
6. Click "Save Changes"

### 2. Deploy the Updated Code

The scheduler has been enabled in `main.py`. Push the changes:

```bash
git add backend/app/main.py
git commit -m "Enable email notification scheduler"
git push
```

Render will automatically redeploy with the scheduler enabled.

### 3. How the Email System Works

#### Daily Absent Student Check
- **Time:** 9:10 AM (Europe/Madrid timezone)
- **Action:** Checks all students who haven't checked in
- **Emails sent to:**
  - Parent of each absent student
  - School contact email (if configured)
  - Admin users

#### Check-in Notifications
- **Trigger:** When student scans QR code to check in
- **Emails:**
  - ✅ Normal check-in confirmation
  - ⚠️ Late arrival alert (after 9:01 AM)

#### Checkout Notifications
- **Trigger:** When student scans QR code to check out
- **Emails:**
  - 🚨 Early dismissal alert (if before normal school hours)
  - ✅ Normal checkout confirmation

### 4. Email Templates

The system uses Spanish language templates. Example:

**Late Arrival Email:**
```
Subject: ⚠️ ArrivApp: [Student Name] ha llegado tarde al cole

¡Hola!

Te informamos que [Student Name] ([Class]) ha registrado su entrada 
en el colegio a las [Time]h.

⚠️ El horario normal de entrada es hasta las 09:00h

Este mensaje es automático.
Gracias,
ArrivApp
```

### 5. Testing Email Notifications

Once deployed, you can test by:

1. **Test Check-in Email:**
   - Go to checkin page
   - Scan a student QR code
   - Parent should receive check-in email

2. **Test Absent Student Email:**
   - Wait until 9:10 AM (or modify scheduler time for testing)
   - All students who haven't checked in will trigger emails

3. **Check Logs:**
   - Go to Render dashboard → Your backend service → Logs
   - Look for email sending confirmations

### 6. Scheduler Configuration

The scheduler runs these tasks:

```python
# Check for absent students at 9:10 AM every day
scheduler.add_job(
    check_absent_students,
    CronTrigger(hour=9, minute=10, timezone="Europe/Madrid"),
    id="check_absent_students",
    replace_existing=True
)
```

You can modify the time in `backend/app/services/scheduler.py` if needed.

### 7. Alternative SMTP Providers

If you want to use a different email service:

**SendGrid (Recommended for production):**
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key
FROM_EMAIL=your_verified_email@yourdomain.com
```

**Mailgun:**
```bash
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@your-domain.mailgun.org
SMTP_PASSWORD=your_mailgun_password
FROM_EMAIL=noreply@your-domain.com
```

**Office 365:**
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your_email@outlook.com
SMTP_PASSWORD=your_password
FROM_EMAIL=your_email@outlook.com
```

### 8. Troubleshooting

**Emails not sending?**
1. Check Render logs for error messages
2. Verify SMTP credentials are correct
3. Check if Gmail App Password is still valid
4. Ensure "Less secure app access" is enabled for Gmail (or use App Password)

**Scheduler not running?**
1. Check Render logs for scheduler start message: "Scheduler started successfully"
2. Verify timezone is correct in config
3. Check if service restarted properly after adding env vars

**Wrong timezone?**
- Update `TIMEZONE=Europe/Madrid` environment variable
- Scheduler uses this for scheduling tasks

### 9. Disable Email Notifications (if needed)

To temporarily disable without removing SMTP credentials:

Comment out scheduler in `backend/app/main.py`:
```python
# start_scheduler()  # Disabled
```

Or remove SMTP environment variables from Render.

### 10. Email Sending Limits

**Gmail:**
- Free: 500 emails/day
- Google Workspace: 2,000 emails/day

**SendGrid:**
- Free: 100 emails/day
- Paid: Unlimited

For 860 students, you may exceed Gmail limits during peak days. Consider upgrading to SendGrid or similar service.

## Next Steps

1. ✅ Add environment variables to Render (Step 1)
2. ✅ Push the code changes to enable scheduler
3. ✅ Monitor Render logs for successful deployment
4. ✅ Test with a check-in to verify emails are working
5. ✅ Wait for 9:10 AM to see absent student report emails

---

**Note:** The code is already committed. Just add the environment variables to Render and the system will work automatically!
