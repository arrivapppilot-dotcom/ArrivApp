# Local Staging Workflow Guide

## Setup for Local Testing Before Production

This guide helps you test changes locally before deploying to production.

---

## Prerequisites

Make sure you have the backend running locally:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 -c "from app.init_db import init_db; init_db()"
python3 app/main.py
```

Backend should run on: `http://localhost:8000`

---

## Frontend Development Workflow

### Option 1: Use Local Files Directly (Simplest)

1. **Open frontend files directly in browser:**
   ```bash
   # On Mac, open in browser
   open frontend/dashboard.html
   
   # Or just drag-and-drop to browser
   ```

2. **Make changes to files:**
   - Edit `frontend/dashboard.html`
   - Edit `frontend/dashboard.js`
   - Edit `frontend/styles.css`

3. **Test locally:**
   - Hard refresh browser: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
   - Open DevTools: `Cmd+Option+I` (Mac)
   - Check Console for errors
   - Verify API calls working

4. **Once tested and working:**
   - Commit changes: `git add frontend/dashboard.html frontend/dashboard.js`
   - Push to production: `git push`
   - Render auto-deploys

---

### Option 2: Run Local Web Server (Better)

If you want to test exactly like production:

```bash
# Install Python http server (or use Python's built-in)
cd frontend
python3 -m http.server 8080
```

Then open: `http://localhost:8080/dashboard.html`

---

## Testing Checklist

Before pushing changes:

### Local Testing:
- [ ] Backend running: `http://localhost:8000`
- [ ] Frontend accessible: `http://localhost:8080` or direct file
- [ ] API calls working (check DevTools Network tab)
- [ ] No console errors
- [ ] All features tested

### Browser DevTools Checklist:
```
1. Console tab:
   - No red errors
   - API URLs correct (localhost:8000)
   
2. Network tab:
   - API responses 200 OK
   - No CORS errors
   - Response data complete
   
3. Application tab:
   - localStorage has token
   - Cookies working
```

---

## Git Workflow for Staging

### 1. Create a feature branch (optional but recommended):
```bash
git checkout -b feature/dashboard-improvements
```

### 2. Make changes locally:
```bash
# Edit files
vim frontend/dashboard.html
vim frontend/dashboard.js
```

### 3. Test thoroughly:
- Open in browser
- Check all interactions
- Verify API calls
- Test on different screen sizes (DevTools)

### 4. Commit locally:
```bash
git add frontend/dashboard.html frontend/dashboard.js
git commit -m "Improve dashboard: [describe changes]"
```

### 5. Push to staging branch (optional):
```bash
git push origin feature/dashboard-improvements
```

### 6. When confident, merge to main:
```bash
# Switch to main
git checkout main
git pull origin main

# Merge feature branch
git merge feature/dashboard-improvements

# Push to production
git push origin main
```

---

## Testing API Integration

### Check if Backend is Responding:
```bash
# In terminal
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer YOUR_TOKEN"
```

### Check API in DevTools:
1. Open DevTools → Network tab
2. Make a request in the app
3. Click on the API call
4. Check:
   - Status: 200 (or expected code)
   - Response: Valid JSON
   - Headers: CORS headers present

---

## Common Issues & Solutions

### Problem: "Cannot reach backend"
**Solution:** 
```bash
# Make sure backend is running
cd backend
python3 app/main.py
# Check: http://localhost:8000 shows FastAPI docs
```

### Problem: "Blank page or errors"
**Solution:**
1. Hard refresh: `Cmd+Shift+R`
2. Check DevTools Console for errors
3. Check Network tab for failed requests
4. Verify localStorage has token

### Problem: "API 401 Unauthorized"
**Solution:**
1. Login first in app
2. Check token in localStorage (DevTools → Application)
3. Token should appear in API requests headers

### Problem: "CORS errors"
**Solution:**
- Backend CORS should handle `localhost:8080` and `localhost:8000`
- Check backend `main.py` CORS configuration
- Restart backend if changed

---

## Dashboard Testing Focus Areas

When testing dashboard changes, verify:

### Stats Display:
- [ ] Total present count correct
- [ ] Total absent count correct
- [ ] Total late count correct
- [ ] Percentages calculating correctly

### Charts:
- [ ] Daily trend chart loads
- [ ] Attendance distribution chart loads
- [ ] Data is accurate
- [ ] Charts responsive on mobile

### Tables:
- [ ] Check-in log loads
- [ ] Late students list accurate
- [ ] Absent students list accurate
- [ ] Filtering works

### Filters:
- [ ] School filter works (admin only)
- [ ] Date range filter works
- [ ] Data updates when filtering

### Real-time Updates:
- [ ] New check-ins appear
- [ ] Late status updates
- [ ] Email notifications sent

---

## Workflow Summary

```
1. Make changes locally
   ↓
2. Test in browser (localhost)
   ↓
3. Check DevTools (Console, Network)
   ↓
4. Test API integration
   ↓
5. If working: git commit
   ↓
6. If confident: git push to main
   ↓
7. Render auto-deploys
   ↓
8. Test on production site
```

---

## Quick Commands

```bash
# Start backend
cd backend && python3 app/main.py

# Start frontend server
cd frontend && python3 -m http.server 8080

# Git staging workflow
git checkout -b feature/my-changes
git add frontend/dashboard.html
git commit -m "Update dashboard"
git push origin feature/my-changes
git checkout main && git merge feature/my-changes && git push

# Check git status
git status

# View recent commits
git log --oneline -10

# Discard local changes
git checkout frontend/dashboard.html
```

---

## Next Steps

1. Make your dashboard changes
2. Test locally following checklist above
3. Once working, let me know and I'll help push
4. I'll verify on production before going live

Good luck! 🚀

