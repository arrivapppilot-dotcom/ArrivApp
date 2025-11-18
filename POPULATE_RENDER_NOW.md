# Populate Render Database Now

## Problem Solved ✅

The `populate_render_db.py` script now includes a **cleanup step** that:
- Deletes all old TEST students (those with ID like `TEST%`)
- Clears their associated check-ins
- Then creates fresh test data

This prevents the `UNIQUE constraint failed` error that was blocking data refresh.

## The Fix

**File Updated:** `backend/populate_render_db.py`

**Commit:** `129f79d` - "Fix: Add cleanup step to populate_render_db.py to prevent duplicate constraint errors"

**What Changed:**
- Added cleanup logic before data generation
- Deletes old TEST data to avoid duplicate student_id conflicts
- Then creates 135 fresh students (15 per school)
- Simulates 850+ check-ins for today

## How to Trigger

### Option 1: GitHub Actions (Recommended)

1. Go to GitHub: https://github.com/arrivapppilot-dotcom/ArrivApp
2. Click **Actions** tab
3. Find **"Populate Render DB Now"** workflow
4. Click **"Run workflow"** button (on the right)
5. Select **main** branch
6. Click green **"Run workflow"** button

The workflow will:
- Connect to Render's PostgreSQL database
- Clean up old TEST data
- Generate fresh test data
- Simulate attendance for today
- Return in ~2-3 minutes

### Option 2: Render Shell (Direct)

If you have Render access:

1. Go to https://dashboard.render.com
2. Select **arrivapp-backend** service
3. Click **Shell** tab
4. Paste this command:
   ```bash
   cd /app && python backend/populate_render_db.py
   ```
5. Wait for completion (2-3 minutes)

### Option 3: Local Test

To test locally first:

```bash
cd backend
python populate_render_db.py
```

This will use your local .env DATABASE_URL (or Render's if you set it).

## What Gets Created

After running the populate script:

- **Students:** 135 new test students created (15 per school)
- **Check-ins:** ~850 simulated for today (2025-11-18)
- **Data:** Present (on-time), Late, and Absent scenarios
- **Cleanup:** All old TEST data removed to avoid duplicates

## Verify Success

### In Dashboard

1. Go to https://arrivapp-frontend.onrender.com/dashboard.html
2. Hard refresh: `Cmd+Shift+R` (Mac) or `Ctrl+Shift+R` (Windows)
3. Should see:
   - **Present:** ~774
   - **Late:** ~180
   - **Absent:** ~41

### In Database

Check Render logs for output showing:
```
✅ Deleted X old TEST students and their check-ins
📊 Total students created today: 135
  ✓ Simulated 845 check-ins, 150 absences
✅ Production database populated successfully!
```

## Dashboard Issue Status

**Current Status:** 🔧 Under Investigation

The dashboard was showing `total=1061, present=0, late=0, absent=1061` because:
1. ❌ API endpoint was returning wrong data (only 1061 students vs 1580)
2. ✅ **FIXED:** Dashboard URL had double `/api` prefix (now fixed in commit 13d8614)
3. 🔧 **IN PROGRESS:** Render database had incomplete data

**Next Steps:**
1. Run populate script to refresh Render database with correct data
2. Dashboard will automatically show correct attendance statistics

## Recent Commits

| Commit | Change |
|--------|--------|
| `129f79d` | Fix: Add cleanup to populate_render_db.py |
| `d72f180` | Add: Debug logging to statistics endpoint |
| `13d8614` | Fix: Remove double /api prefix in dashboard |

## Questions?

If the dashboard still shows wrong data after running populate:

1. Check Render logs for `[DEBUG STATS]` output
2. Hard refresh dashboard (Cmd+Shift+R)
3. Check browser console for any errors (F12 → Console tab)

---

**TL;DR:** Run the GitHub Actions workflow "Populate Render DB Now" to refresh test data. The script is now fixed and will clean up old duplicate data automatically.
