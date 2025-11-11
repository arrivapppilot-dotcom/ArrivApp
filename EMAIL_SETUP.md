# 📧 Email Setup Guide for ArrivApp

## Gmail Configuration

### Step 1: Enable 2-Factor Authentication
1. Go to your Google Account: https://myaccount.google.com/
2. Click **Security** in the left menu
3. Under "How you sign in to Google", click **2-Step Verification**
4. Follow the steps to enable it (if not already enabled)

### Step 2: Generate App Password
1. Go to https://myaccount.google.com/apppasswords
2. Select app: **Mail**
3. Select device: **Other (Custom name)**
4. Enter name: **ArrivApp**
5. Click **Generate**
6. Copy the 16-character password (no spaces)
7. **Save this password securely** - you won't see it again!

### Step 3: Update .env File
Open `backend/.env` and update these lines:

```bash
# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com          # Your Gmail address
SMTP_PASSWORD=xxxx xxxx xxxx xxxx        # The 16-char app password
FROM_EMAIL=your-email@gmail.com          # Same as SMTP_USER
FROM_NAME=ArrivApp Notifications         # Display name in emails
ADMIN_EMAIL=admin-email@gmail.com        # Where to send absent reports
```

### Example Configuration:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=school@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
FROM_EMAIL=school@gmail.com
FROM_NAME=Colegio El Ejemplo - ArrivApp
ADMIN_EMAIL=director@gmail.com
```

---

## Alternative Email Providers

### Outlook/Hotmail
```bash
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### Office 365
```bash
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@yourschool.edu
SMTP_PASSWORD=your-password
```

### Yahoo Mail
```bash
SMTP_HOST=smtp.mail.yahoo.com
SMTP_PORT=587
SMTP_USER=your-email@yahoo.com
SMTP_PASSWORD=app-specific-password
```

---

## Email Notifications

### 1. Regular Check-In Email (Before 9:01)
**To**: Parent email
**Subject**: ✅ ArrivApp: [Student Name] ha llegado al cole
**When**: Immediately when student scans QR
**Content**: Confirmation with arrival time

### 2. Late Arrival Email (After 9:01)
**To**: Parent email
**Subject**: ⚠️ ArrivApp: [Student Name] ha llegado tarde al cole
**When**: Immediately when late student scans QR
**Content**: Warning message with arrival time

### 3. Absent Students Report
**To**: Admin email (configured in ADMIN_EMAIL)
**Subject**: 📋 ArrivApp - Reporte de Ausencias ([Date])
**When**: Daily at 9:10 AM (configured in CHECK_ABSENT_TIME)
**Content**: List of all students who haven't checked in

---

## Testing Email Setup

### Test 1: Check Configuration
```bash
cd backend
source venv/bin/activate
python -c "from app.core.config import get_settings; s = get_settings(); print(f'SMTP: {s.SMTP_USER} -> {s.FROM_EMAIL}')"
```

### Test 2: Send Test Email
Create a file `test_email.py` in backend/:

```python
import asyncio
from app.services.email_service import send_email

async def test():
    result = await send_email(
        to_email="your-test@email.com",
        subject="Test from ArrivApp",
        body="If you receive this, email is working!"
    )
    print("Email sent!" if result else "Email failed!")

asyncio.run(test())
```

Run:
```bash
python test_email.py
```

### Test 3: Manual Absent Report
```bash
cd backend
source venv/bin/activate
python -c "import asyncio; from app.services.scheduler import run_absent_check_now; asyncio.run(run_absent_check_now())"
```

---

## Troubleshooting

### Error: "Authentication failed"
**Cause**: Wrong email or password
**Solution**: 
- Verify SMTP_USER matches your Gmail
- Regenerate app password
- Remove spaces from password in .env

### Error: "Connection timed out"
**Cause**: Port blocked or wrong SMTP server
**Solution**:
- Check SMTP_HOST is correct
- Try port 465 instead of 587
- Check firewall settings

### Error: "Sender address rejected"
**Cause**: FROM_EMAIL doesn't match SMTP_USER
**Solution**: Set FROM_EMAIL = SMTP_USER

### Emails not arriving
**Check**:
1. Spam/junk folder
2. Email logs: Check backend console for errors
3. Gmail "Less secure apps" is NOT needed (using app password)
4. Daily sending limits (Gmail: ~500/day, Office365: ~300/day)

---

## Security Best Practices

1. ✅ **Use App Passwords** - Never use your main Gmail password
2. ✅ **Keep .env secure** - Never commit .env to git
3. ✅ **Rotate passwords** - Change app password every 6 months
4. ✅ **Monitor usage** - Check Gmail sent folder regularly
5. ✅ **Use school email** - Create dedicated email for school notifications

---

## Scheduler Configuration

### Current Settings (in .env):
```bash
CHECK_ABSENT_TIME=09:10        # Time to send absent report (HH:MM)
LATE_THRESHOLD_HOUR=9          # Hour for late detection
LATE_THRESHOLD_MINUTE=1        # Minute for late detection
TIMEZONE=Europe/Madrid         # Timezone for scheduling
```

### Customization:
- Change `CHECK_ABSENT_TIME` to when you want the daily report
- Change `LATE_THRESHOLD` to adjust when students are considered late
- Reports run automatically every school day

---

## Production Recommendations

### For Small Schools (<100 students):
- Gmail with app password is sufficient
- Monitor daily sending limits

### For Medium Schools (100-500 students):
- Consider Google Workspace (higher limits)
- Or use dedicated email service (SendGrid, Mailgun)

### For Large Schools (500+ students):
- Use transactional email service
- Update email_service.py to use their API
- Much higher sending limits and better deliverability

---

## Need Help?

1. Check backend logs for detailed error messages
2. Test with a single student first
3. Verify all .env settings are correct
4. Check spam folder for test emails
5. Review Gmail "Less secure apps" settings (not needed with app password)

---

**Once configured, restart the backend server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

The scheduler will start automatically and run the absent check daily at the configured time!
