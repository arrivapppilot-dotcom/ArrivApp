# 📚 ArrivApp Documentation Index

Welcome to ArrivApp v2.0! Use this index to find what you need.

## 🚀 Getting Started

**New to ArrivApp? Start here:**

1. 📖 **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
2. 📋 **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Understand what was built
3. 🏗️ **[ARCHITECTURE.md](ARCHITECTURE.md)** - Learn how it works

## 📖 Main Documentation

### For Developers

- **[README.md](README.md)** - Complete technical documentation
  - Installation instructions (Docker & Manual)
  - Configuration guide
  - API endpoints reference
  - Deployment guides
  - Feature overview

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
  - System overview diagrams
  - Data flow explanations
  - Database schema
  - Security model
  - Deployment architecture

### For Users

- **[QUICKSTART.md](QUICKSTART.md)** - Quick setup guide
  - Prerequisites
  - 5-minute setup
  - First login
  - Adding students
  - Testing check-in

- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project overview
  - What was built
  - Feature comparison
  - Benefits
  - Cost analysis
  - Success metrics

### For Troubleshooting

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problem solving
  - Installation issues
  - Authentication problems
  - Email configuration
  - Database errors
  - QR scanner issues
  - Docker problems
  - Emergency recovery

## 🗂️ Code Documentation

### Backend (FastAPI)

```
backend/
├── app/
│   ├── main.py              # Application entry point
│   ├── init_db.py           # Database initialization
│   │
│   ├── core/                # Core functionality
│   │   ├── config.py        # Configuration management
│   │   ├── database.py      # Database connection
│   │   ├── security.py      # JWT & password handling
│   │   └── deps.py          # Dependencies (auth)
│   │
│   ├── models/              # Data models
│   │   ├── models.py        # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas (API)
│   │
│   ├── routers/             # API endpoints
│   │   ├── auth.py          # /api/auth/* - Authentication
│   │   ├── students.py      # /api/students/* - Student management
│   │   └── checkin.py       # /api/checkin/* - Check-in & dashboard
│   │
│   └── services/            # Business logic
│       ├── qr_service.py    # QR code generation
│       └── email_service.py # Email notifications
│
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
├── Dockerfile              # Container image
├── docker-compose.yml      # Multi-container setup
│
└── Utility Scripts:
    ├── add_sample_students.py    # Create test data
    └── download_qr_codes.py      # Download all QR codes
```

### Frontend (HTML + JS)

```
frontend/
├── login.html              # Login page
│   └── Features: JWT auth, form validation, error handling
│
├── dashboard.html          # Main dashboard
│   └── Features: Stats cards, tables, search, filters
│
├── dashboard.js            # Dashboard logic
│   └── Features: API calls, auth, auto-refresh, CSV export
│
└── checkin.html            # Check-in kiosk
    └── Features: QR scanner, camera access, success feedback
```

## 🔍 Quick Reference

### API Endpoints

**Authentication:**
- `POST /api/auth/login` - Login & get JWT token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/logout` - Logout

**Students:**
- `GET /api/students/` - List all students
- `POST /api/students/` - Create student (admin)
- `GET /api/students/{id}` - Get student details
- `PUT /api/students/{id}` - Update student (admin)
- `DELETE /api/students/{id}` - Soft delete student (admin)
- `GET /api/students/{id}/qr` - Download QR code
- `POST /api/students/{id}/regenerate-qr` - Regenerate QR (admin)

**Check-in:**
- `POST /api/checkin/scan?student_id={id}` - Check-in (no auth)
- `GET /api/checkin/dashboard?date_filter={date}` - Dashboard data
- `GET /api/checkin/` - List check-ins

**Health:**
- `GET /` - API info
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

### Configuration

**Environment Variables (.env):**
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Security  
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=arrivapp@domain.com
ADMIN_EMAIL=admin@domain.com

# App
LATE_THRESHOLD_HOUR=9
LATE_THRESHOLD_MINUTE=1
FRONTEND_URL=http://localhost:8080
```

### Default Credentials

```
Username: admin
Password: admin123
```
⚠️ **Change immediately in production!**

## 🛠️ Common Tasks

### Setup & Installation
→ See [QUICKSTART.md](QUICKSTART.md)

### Add Students
```bash
# Via script
python backend/add_sample_students.py

# Via API (see README.md)
curl -X POST http://localhost:8000/api/students/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"student_id":"EST001","name":"Juan","class_name":"3A","parent_email":"parent@email.com"}'
```

### Generate QR Codes
```bash
# All students
python backend/download_qr_codes.py

# Single student
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/students/1/qr -o qr.png
```

### Backup Database
```bash
# PostgreSQL
docker-compose exec db pg_dump -U arrivapp arrivapp > backup.sql

# SQLite
cp backend/arrivapp.db backup.db
```

### View Logs
```bash
# Docker
docker-compose logs -f backend

# Manual
# Check terminal where uvicorn is running
```

### Reset Admin Password
→ See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#forgot-admin-password)

## 📋 Checklists

### Pre-deployment Checklist
- [ ] Change admin password
- [ ] Set strong SECRET_KEY
- [ ] Configure production SMTP
- [ ] Set up PostgreSQL
- [ ] Enable HTTPS
- [ ] Set CORS origins
- [ ] Test all features
- [ ] Configure backups
- [ ] Set up monitoring

### Daily Operations Checklist
- [ ] Check absent report (9:10 AM)
- [ ] Monitor dashboard for issues
- [ ] Verify emails are sending
- [ ] Check system health endpoint
- [ ] Review logs for errors

### Troubleshooting Checklist
- [ ] Check logs (backend & browser)
- [ ] Verify environment variables
- [ ] Test database connection
- [ ] Confirm SMTP settings
- [ ] Check API health endpoint
- [ ] Verify authentication works
- [ ] Test with sample data

## 🔗 External Resources

### Technologies Used
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [JWT Introduction](https://jwt.io/introduction)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Deployment Platforms
- [Railway](https://railway.app/)
- [Render](https://render.com/)
- [Fly.io](https://fly.io/)
- [DigitalOcean](https://www.digitalocean.com/)

### Email Services
- [Gmail App Passwords](https://myaccount.google.com/apppasswords)
- [SendGrid](https://sendgrid.com/)
- [Mailgun](https://www.mailgun.com/)

## 🆘 Getting Help

### Self-Service
1. Check this index for relevant documentation
2. Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Check logs for error messages
4. Try [QUICKSTART.md](QUICKSTART.md) for fresh setup

### Support Channels
- **Email**: luca.alice@gmail.com
- **GitHub Issues**: Create an issue with:
  - Error message
  - Steps to reproduce
  - Environment details (OS, Python version, etc.)
  - Relevant logs

### Before Asking for Help
Please include:
- What you're trying to do
- What you expected to happen
- What actually happened
- Error messages (full text)
- Relevant logs
- What you've already tried

## 📝 Contributing

Want to improve ArrivApp?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

See [README.md](README.md#contributing) for details.

## 📄 License

MIT License - See LICENSE file for details.

## 🎯 Version History

- **v2.0.0** (November 2025)
  - Complete rewrite from Google Sheets
  - FastAPI backend
  - JWT authentication
  - QR code system
  - Real-time dashboard
  - Email notifications
  - Docker support

- **v1.0.0** (Previous)
  - Google Sheets + Apps Script
  - Basic functionality

## 🙏 Acknowledgments

Built for the ArrivApp Barcelona pilot program.

Thanks to:
- FastAPI & Uvicorn teams
- SQLAlchemy developers
- Open source community

---

**Last Updated**: November 2025  
**Version**: 2.0.0  
**Status**: Production Ready ✅

For the most up-to-date information, always check the [main README.md](README.md).
