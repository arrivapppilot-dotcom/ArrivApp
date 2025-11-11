# ArrivApp - Render.com Deployment Guide

## 🚀 Quick Deployment Steps

### Prerequisites
- GitHub account
- Render.com account (free tier available)
- Your code pushed to a GitHub repository

### Step 1: Push Code to GitHub
```bash
cd /Users/lucaalice/Desktop/AI\ projects/ArrivApp
git init
git add .
git commit -m "Initial commit for Render deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/arrivapp.git
git push -u origin main
```

### Step 2: Deploy on Render.com

1. **Sign up/Login to Render.com**
   - Go to https://render.com
   - Sign up with your GitHub account

2. **Create New Web Service (Backend)**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name**: `arrivapp-backend`
     - **Region**: Frankfurt (or closest to you)
     - **Branch**: `main`
     - **Root Directory**: `backend`
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Free

3. **Add Environment Variables (Backend)**
   Click "Environment" tab and add:
   ```
   SECRET_KEY=your_secret_key_here_generate_a_strong_random_string
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   DATABASE_URL=sqlite:///./arrivapp.db
   
   # Email Configuration (optional but recommended)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=your_app_password
   SMTP_FROM_EMAIL=your_email@gmail.com
   
   # Frontend URL (update after deploying frontend)
   FRONTEND_URL=https://arrivapp-frontend.onrender.com
   ```

4. **Create Static Site (Frontend)**
   - Click "New +" → "Static Site"
   - Connect same GitHub repository
   - Configure:
     - **Name**: `arrivapp-frontend`
     - **Branch**: `main`
     - **Root Directory**: Leave empty
     - **Build Command**: `echo "No build needed"`
     - **Publish Directory**: `frontend`
     - **Plan**: Free

5. **Update Frontend API URL**
   After backend is deployed, update the API URL in frontend files:
   - Edit `frontend/dashboard.js`, `frontend/login.html`, etc.
   - Replace `http://localhost:8000` with your backend URL:
     `https://arrivapp-backend.onrender.com`

## 🔐 Generate SECRET_KEY

Run this command to generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 📧 Email Configuration (Gmail)

1. Enable 2-Factor Authentication on your Gmail
2. Generate an App Password:
   - Go to Google Account → Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use this password in `SMTP_PASSWORD` environment variable

## 🗄️ Database Options

### Option 1: SQLite (Simple, Free)
- Already configured in the setup
- Good for testing and small deployments
- Limitations: Data resets on each deployment

### Option 2: PostgreSQL (Recommended for Production)
- Render offers free PostgreSQL database
- Steps:
  1. Create PostgreSQL database on Render
  2. Copy the "Internal Database URL"
  3. Update `DATABASE_URL` environment variable
  4. Update `backend/core/database.py` to use PostgreSQL

## 📱 Access Your App

After deployment:
- **Frontend**: `https://arrivapp-frontend.onrender.com`
- **Backend API**: `https://arrivapp-backend.onrender.com`
- **API Docs**: `https://arrivapp-backend.onrender.com/docs`

## ⚠️ Important Notes

1. **Free Tier Limitations**:
   - Services spin down after 15 minutes of inactivity
   - First request after spin-down takes 30-60 seconds
   - 750 hours/month of runtime per service

2. **Keep Services Active** (optional):
   - Use a service like UptimeRobot to ping your app every 14 minutes

3. **Data Persistence**:
   - With SQLite, data is stored on disk but may reset on redeployment
   - For production, use PostgreSQL database

## 🔄 Update Deployment

Push changes to GitHub:
```bash
git add .
git commit -m "Update message"
git push
```

Render will automatically redeploy!

## 🐛 Troubleshooting

### Backend won't start:
- Check logs in Render dashboard
- Verify all environment variables are set
- Ensure `requirements.txt` has all dependencies

### Frontend API calls fail:
- Check CORS settings in backend
- Verify API_URL is correct in frontend files
- Check browser console for errors

### Database errors:
- For SQLite: Check if `arrivapp.db` is created
- For PostgreSQL: Verify DATABASE_URL is correct

## 💡 Alternative: Vercel (Frontend Only)

If you want to use Vercel for frontend and Render for backend:

1. **Deploy Backend on Render** (follow steps above)
2. **Deploy Frontend on Vercel**:
   ```bash
   npm install -g vercel
   cd frontend
   vercel
   ```
3. Update API URLs in frontend to point to Render backend

## 🎉 Success!

Your ArrivApp is now live and accessible worldwide! 🌍
