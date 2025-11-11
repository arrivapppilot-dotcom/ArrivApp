# 🔧 ArrivApp - Troubleshooting Guide

Common issues and their solutions.

## 🚨 Installation Issues

### Python Package Installation Fails

**Problem**: `pip install -r requirements.txt` fails

**Solutions**:
```bash
# Update pip first
pip install --upgrade pip

# Install build tools (macOS)
xcode-select --install

# Install build tools (Ubuntu/Debian)
sudo apt-get install python3-dev libpq-dev

# Try installing packages one by one to identify the problem
pip install fastapi
pip install uvicorn
# etc...
```

### Docker Compose Fails to Start

**Problem**: `docker-compose up` fails

**Solutions**:
```bash
# Check Docker is running
docker ps

# Check ports are not in use
lsof -i :8000
lsof -i :5432

# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up

# Check logs
docker-compose logs backend
docker-compose logs db
```

## 🔐 Authentication Issues

### Cannot Login - "Incorrect username or password"

**Problem**: Admin credentials don't work

**Solutions**:
```bash
# Re-initialize database
cd backend
python -m app.init_db

# Check if admin user exists
# Using SQLite:
sqlite3 arrivapp.db "SELECT * FROM users WHERE username='admin';"

# Using PostgreSQL:
docker-compose exec db psql -U arrivapp -c "SELECT * FROM users WHERE username='admin';"

# Default credentials should be:
# Username: admin
# Password: admin123
```

### Token Expired / 401 Unauthorized

**Problem**: Dashboard shows "Unauthorized" after some time

**Solution**:
- Tokens expire after 8 hours (configurable)
- Simply logout and login again
- Adjust `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env` if needed

### CORS Errors in Browser Console

**Problem**: "CORS policy blocked" errors

**Solution**:
```python
# In backend/app/main.py, update CORS origins:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "YOUR_DOMAIN"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📧 Email Issues

### Emails Not Sending

**Problem**: Check-in works but no email received

**Debug Steps**:

1. **Check backend logs**:
```bash
# Docker
docker-compose logs backend | grep -i email

# Manual
# Check terminal where uvicorn is running
```

2. **Verify SMTP settings in `.env`**:
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # NOT your regular password!
```

3. **Test SMTP connection**:
```bash
cd backend
python3 << EOF
import aiosmtplib
import asyncio
from email.mime.text import MIMEText

async def test():
    message = MIMEText("Test")
    message["From"] = "your-email@gmail.com"
    message["To"] = "recipient@email.com"
    message["Subject"] = "Test"
    
    await aiosmtplib.send(
        message,
        hostname="smtp.gmail.com",
        port=587,
        username="your-email@gmail.com",
        password="your-app-password",
        start_tls=True
    )
    print("Email sent successfully!")

asyncio.run(test())
EOF
```

### Gmail "Less Secure Apps" Error

**Problem**: Gmail rejects login

**Solution**:
- Don't use your regular Gmail password
- Create an App Password:
  1. Go to https://myaccount.google.com/apppasswords
  2. Generate new app password
  3. Use that 16-character password in `.env`

### Email Goes to Spam

**Problem**: Parents receive emails in spam folder

**Solutions**:
- Add sender email to contacts
- Use a custom domain email (not Gmail)
- Configure SPF/DKIM records (advanced)
- Ask parents to mark as "Not Spam"

## 🗄️ Database Issues

### "No such table" Error

**Problem**: Database tables don't exist

**Solution**:
```bash
cd backend
python -m app.init_db
```

### SQLite "Database is locked"

**Problem**: Multiple processes accessing SQLite

**Solution**:
- SQLite doesn't support concurrent writes well
- Use PostgreSQL for production
- Or ensure only one process accesses DB:
```bash
# Kill other processes
pkill -f uvicorn
# Restart
uvicorn app.main:app --reload
```

### PostgreSQL Connection Failed

**Problem**: Cannot connect to PostgreSQL

**Solutions**:
```bash
# Check if PostgreSQL is running
docker-compose ps

# Check connection string in .env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Try connecting manually
docker-compose exec db psql -U arrivapp

# Reset PostgreSQL
docker-compose down -v  # WARNING: Deletes data!
docker-compose up -d
python -m app.init_db
```

## 📱 QR Scanner Issues

### Camera Not Working

**Problem**: QR scanner doesn't show camera feed

**Solutions**:

1. **Check browser permissions**:
   - Chrome: Click 🔒 in address bar → Camera → Allow
   - Safari: Settings → Privacy → Camera → Allow

2. **HTTPS requirement**:
   - Browsers require HTTPS for camera access
   - In production, use HTTPS (Let's Encrypt)
   - For local testing: use `http://localhost` (allowed)

3. **Try different browser**:
   - Chrome/Edge (recommended)
   - Safari (iOS)
   - Firefox

4. **Check camera is not in use**:
   - Close other apps using camera
   - Zoom, Teams, etc.

### QR Code Not Scanning

**Problem**: Scanner doesn't detect QR code

**Solutions**:
- Ensure good lighting
- Hold steady for 2-3 seconds
- Try zooming camera closer/farther
- Check QR code is not damaged
- Regenerate QR code if needed:
  ```bash
  POST /api/students/{id}/regenerate-qr
  ```

### "Student not found" After Scanning

**Problem**: QR scans but returns error

**Debug**:
1. Check what the QR code contains:
   - Use any QR reader app
   - Should be: `http://api.url/api/checkin/scan?student_id=EST001`

2. Verify student exists:
   ```bash
   curl http://localhost:8000/api/students/ \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. Check student is active:
   ```sql
   SELECT * FROM students WHERE student_id='EST001';
   ```

## 🖥️ Frontend Issues

### Dashboard Stuck on "Loading..."

**Problem**: Dashboard loads but shows no data

**Debug**:

1. **Check browser console** (F12):
   - Look for errors
   - Check API responses

2. **Verify API is running**:
   ```bash
   curl http://localhost:8000/health
   ```

3. **Check token is valid**:
   - Open browser console (F12)
   - Type: `localStorage.getItem('arrivapp_token')`
   - If null or expired, logout and login again

4. **Check API_BASE_URL**:
   ```javascript
   // In dashboard.js
   const API_BASE_URL = 'http://localhost:8000';
   ```

### Login Page Doesn't Redirect

**Problem**: Login succeeds but stays on login page

**Solution**:
```javascript
// Check browser console for errors
// Verify dashboard.html exists in same directory
// Check localStorage:
localStorage.getItem('arrivapp_token')  // Should have token
localStorage.getItem('arrivapp_user')   // Should have username
```

### Dashboard Shows Wrong Data

**Problem**: Stats or lists are incorrect

**Debug**:
1. Check date filter
2. Refresh page (Ctrl+R)
3. Check API response:
   ```bash
   curl http://localhost:8000/api/checkin/dashboard?date_filter=2025-11-09 \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
4. Check database directly:
   ```sql
   SELECT * FROM checkins WHERE DATE(checkin_time) = '2025-11-09';
   ```

## 🐳 Docker Issues

### Port Already in Use

**Problem**: "Address already in use" error

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000
# or
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 PID

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Use 8001 instead
```

### Container Keeps Restarting

**Problem**: Backend container restarts in loop

**Debug**:
```bash
# Check logs
docker-compose logs backend

# Common issues:
# 1. Database connection failed
# 2. Missing .env file
# 3. Python syntax error

# Run container interactively to debug
docker-compose run backend /bin/bash
python -m app.main
```

### Database Data Lost

**Problem**: Data disappears after `docker-compose down`

**Solution**:
```bash
# Don't use -v flag (deletes volumes)
docker-compose down      # Good
docker-compose down -v   # Bad - deletes data!

# To preserve data, use named volumes (already in docker-compose.yml)
volumes:
  postgres_data:
```

## 🚀 Deployment Issues

### Railway Deployment Fails

**Problem**: Railway build fails

**Solutions**:

1. **Check build logs** in Railway dashboard

2. **Verify Dockerfile**:
   ```dockerfile
   # Should expose port 8000
   EXPOSE 8000
   ```

3. **Set environment variables**:
   - Go to Railway → Variables
   - Add all vars from `.env`
   - Especially `DATABASE_URL` (auto-set if using Railway DB)

4. **Check Python version**:
   ```dockerfile
   FROM python:3.11-slim  # Use specific version
   ```

### App Works Locally but Not in Production

**Problem**: Different behavior in production

**Common Causes**:
1. **Environment variables**:
   - Check all `.env` vars are set in production
   - Use production SMTP credentials
   - Update `FRONTEND_URL` to your domain

2. **Database differences**:
   - Local: SQLite
   - Production: PostgreSQL
   - Run migrations in production

3. **CORS issues**:
   ```python
   # Update allowed origins
   allow_origins=[
       "https://yourdomain.com",
       "http://localhost:8080"  # Keep for testing
   ]
   ```

4. **HTTPS required**:
   - Camera access needs HTTPS
   - Use Let's Encrypt or Railway's auto-SSL

## 📊 Performance Issues

### Dashboard Slow to Load

**Problem**: Dashboard takes >5 seconds to load

**Solutions**:

1. **Add database indexes**:
   ```python
   # In models.py
   checkin_time = Column(DateTime, default=datetime.utcnow, index=True)
   ```

2. **Reduce refresh interval**:
   ```javascript
   // In dashboard.js
   setInterval(fetchDashboardData, 60000); // 60s instead of 30s
   ```

3. **Optimize queries**:
   ```python
   # Use .join() instead of separate queries
   # Add .limit() to large queries
   ```

### Check-in Takes Too Long

**Problem**: QR scan to response >5 seconds

**Debug**:
1. Check email sending is async
2. Database indexes on student_id
3. Check network latency
4. Profile slow queries:
   ```bash
   # Enable SQL logging
   echo 'SQLALCHEMY_ECHO=True' >> .env
   ```

## 🆘 Emergency Recovery

### Complete System Reset

**If everything is broken**:

```bash
# 1. Stop everything
docker-compose down -v  # WARNING: Deletes data!
# or
pkill -f uvicorn

# 2. Clean up
cd backend
rm -rf venv/
rm arrivapp.db  # If using SQLite
rm -rf __pycache__/

# 3. Fresh start
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m app.init_db

# 4. Start
uvicorn app.main:app --reload

# 5. Re-add data
python add_sample_students.py
```

### Forgot Admin Password

**Problem**: Can't login as admin

**Solution**:
```bash
cd backend
python3 << EOF
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.models import User

db = SessionLocal()
admin = db.query(User).filter(User.username == "admin").first()
admin.hashed_password = get_password_hash("newpassword123")
db.commit()
print("Password reset to: newpassword123")
EOF
```

## 📞 Still Having Issues?

1. **Check the logs**:
   - Backend: Terminal or `docker-compose logs`
   - Frontend: Browser console (F12)
   - Database: Query logs

2. **Search documentation**:
   - README.md
   - ARCHITECTURE.md
   - API docs: http://localhost:8000/docs

3. **Ask for help**:
   - Email: luca.alice@gmail.com
   - Include:
     - Error message
     - Logs
     - What you tried
     - OS and versions

## 🔍 Useful Commands

```bash
# Check what's running
docker-compose ps
ps aux | grep uvicorn

# View logs
docker-compose logs -f backend
tail -f /var/log/arrivapp.log

# Database shell
sqlite3 arrivapp.db
docker-compose exec db psql -U arrivapp

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Check Python environment
which python
python --version
pip list

# Network debugging
netstat -an | grep 8000
lsof -i :8000

# Process management
ps aux | grep python
kill -9 PID
```

---

**Remember**: When in doubt, check the logs first! 📝
