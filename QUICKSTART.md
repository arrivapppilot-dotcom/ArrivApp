# 🚀 ArrivApp - Quick Start Guide

Get ArrivApp running in 5 minutes!

## Prerequisites

- Python 3.11+ OR Docker
- PostgreSQL 15+ (or use SQLite for testing)

## Step 1: Clone & Setup

```bash
cd "Desktop/AI projects/ArrivApp"
```

## Step 2: Configure Environment

```bash
cd backend
cp .env.example .env
```

Edit `.env` and configure at minimum:

```env
# For testing with SQLite (easiest):
DATABASE_URL=sqlite:///./arrivapp.db

# Email (use Gmail for testing):
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com
FROM_NAME=ArrivApp
ADMIN_EMAIL=your-email@gmail.com

# Security (generate a random key):
SECRET_KEY=your-super-secret-key-change-this
```

### Getting Gmail App Password:
1. Go to https://myaccount.google.com/apppasswords
2. Create new app password
3. Use that password (not your regular Gmail password)

## Step 3: Quick Start

### Option A: Using Script (Recommended)

**macOS/Linux:**
```bash
./start.sh
```

**Windows:**
```bash
start.bat
```

### Option B: Manual Start

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.init_db
uvicorn app.main:app --reload
```

**Frontend (new terminal):**
```bash
cd frontend
python -m http.server 8080
```

## Step 4: Access the System

1. **Login**: http://localhost:8080/login.html
   - Username: `admin`
   - Password: `admin123`

2. **Dashboard**: http://localhost:8080/dashboard.html

3. **API Docs**: http://localhost:8000/docs

4. **Check-in Station**: http://localhost:8080/checkin.html

## Step 5: Add Sample Students

```bash
cd backend
python add_sample_students.py
```

This creates 5 test students with QR codes.

## Step 6: Test Check-in

1. Open http://localhost:8080/checkin.html
2. Allow camera access
3. Download and print a student QR code:
   ```bash
   # Get student 1's QR code
   curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/students/1/qr \
     -o student_1.png
   ```
4. Scan the QR code
5. Check your email for notification!

## 🎉 You're Ready!

### What to do next:

1. **Change admin password**:
   - Login to dashboard
   - Use API to update password

2. **Add real students**:
   - Use API endpoints
   - Or build an admin UI

3. **Generate QR codes**:
   - Download from `/api/students/{id}/qr`
   - Print and laminate for students

4. **Setup check-in station**:
   - Use a tablet/phone at school entrance
   - Keep `checkin.html` open

5. **Deploy to production**:
   - See README.md for deployment guides
   - Use Railway, Render, or your VPS

## 📱 Mobile Testing

To test on mobile in the same network:

1. Find your computer's IP:
   ```bash
   # macOS/Linux
   ifconfig | grep "inet "
   
   # Windows
   ipconfig
   ```

2. Use that IP on mobile:
   - Backend: `http://YOUR_IP:8000`
   - Frontend: `http://YOUR_IP:8080`

3. Update `frontend/*.html` and `frontend/*.js` to use your IP instead of `localhost`

## 🔧 Troubleshooting

### Can't login
- Check backend is running: http://localhost:8000/health
- Verify database was initialized: `python -m app.init_db`

### Emails not sending
- Check SMTP credentials in `.env`
- For Gmail, must use App Password
- Check logs for errors

### Camera not working
- HTTPS required in production
- Allow camera permissions in browser
- Try different browser (Chrome recommended)

### Database errors
- SQLite: Delete `arrivapp.db` and run `init_db` again
- PostgreSQL: Check connection string

## 📚 Learn More

- **Full Documentation**: See README.md
- **API Reference**: http://localhost:8000/docs
- **Source Code**: Explore the `backend/app` directory

## 🆘 Need Help?

- Check logs: `docker-compose logs -f` or terminal output
- API errors: See http://localhost:8000/docs for endpoint details
- Issues: Create GitHub issue

---

**Happy tracking! 🎓✅**
