# Environment Variables for Render.com Deployment

## Required Environment Variables

### Backend Service Environment Variables

```bash
# Security (REQUIRED)
SECRET_KEY=<generate-using-command-below>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (REQUIRED)
DATABASE_URL=sqlite:///./arrivapp.db
# OR for PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:port/database

# Email Configuration (OPTIONAL but recommended for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password
SMTP_FROM_EMAIL=your_email@gmail.com

# Frontend URL (REQUIRED - update after frontend deployment)
FRONTEND_URL=https://your-frontend-url.onrender.com

# CORS Origins (OPTIONAL - defaults to FRONTEND_URL)
CORS_ORIGINS=https://your-frontend-url.onrender.com,https://www.your-domain.com
```

## Generate SECRET_KEY

Run this command to generate a secure random key:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and use it as your `SECRET_KEY`.

## Setting Variables in Render

1. Go to your service dashboard
2. Click "Environment" tab
3. Click "Add Environment Variable"
4. Add each variable with its value
5. Click "Save Changes"

## Email Setup (Gmail)

To use Gmail for sending notifications:

1. Enable 2-Factor Authentication on your Google Account
2. Go to: https://myaccount.google.com/apppasswords
3. Generate a new app password for "Mail"
4. Use this 16-character password as `SMTP_PASSWORD`
5. Use your Gmail address as `SMTP_USERNAME` and `SMTP_FROM_EMAIL`

## PostgreSQL Database (Recommended for Production)

Instead of SQLite, use Render's free PostgreSQL:

1. In Render dashboard, click "New +" → "PostgreSQL"
2. Name it (e.g., `arrivapp-db`)
3. Select Free plan
4. After creation, copy the "Internal Database URL"
5. Set it as `DATABASE_URL` in your backend service

## Testing Environment Variables

After setting variables, your backend should start successfully. Check:
- Logs for any missing variable errors
- `/docs` endpoint should be accessible
- Test login functionality
