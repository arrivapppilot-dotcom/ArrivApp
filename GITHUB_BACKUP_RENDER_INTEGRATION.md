# GitHub Backup - Render Integration Guide

## ⚠️ Important Note

The GitHub Actions workflow can upload backups to releases, but **it cannot access the database on Render**. 

For production backups, you have two options:

## Option 1: Run Backups Manually from Your Machine ✅ **RECOMMENDED**

This is the simplest and most reliable method:

```bash
cd backend

# Set environment variables
export GITHUB_TOKEN="your_token_here"
export GITHUB_REPO="arrivapppilot-dotcom/ArrivApp"
export DATABASE_PATH="arrivapp.db"  # Local database or downloaded from Render
export QR_CODES_DIR="qr_codes"

# Create and upload backup
python3 github_backup.py backup
```

**Best Practice:** Run this weekly on your local machine

### Schedule on Your Local Machine

**macOS/Linux:**
Add to crontab:
```bash
crontab -e
# Add this line to run every Sunday at 2 AM:
0 2 * * 0 cd /path/to/ArrivApp/backend && export GITHUB_TOKEN="..." && python3 github_backup.py backup
```

**Windows:**
Use Task Scheduler to run the backup script weekly

## Option 2: Deploy Backup Script to Render ✅ **ADVANCED**

If you want fully automated backups on Render:

1. Add a backup endpoint to your FastAPI app
2. Create a Render background job to call it daily
3. Background job calls the backup script with proper environment

**This requires more setup but is fully automated**

## Option 3: GitHub Actions (Limited) ⚠️

The workflow we created works for:
- ✅ Testing the script
- ✅ Uploading pre-made backups
- ❌ Accessing Render database directly

It cannot automatically backup your production database because the workflow runner doesn't have access to Render.

## Recommended Workflow for ArrivApp

### For Production:

**Weekly Manual Backup** (Recommended)
```bash
cd backend
python3 github_backup.py backup
```

**Setup:**
1. Schedule on your laptop/server weekly
2. Takes ~2-3 minutes
3. Stores in GitHub Releases automatically
4. No additional costs

### For Development:

Test the script locally anytime:
```bash
python3 github_backup.py backup
```

## Quick Backup Commands

```bash
# List all backups
python3 github_backup.py list

# Create manual backup
python3 github_backup.py backup

# Restore a backup
python3 github_backup.py restore backup-20251114_020000

# Cleanup old backups
python3 github_backup.py cleanup
```

## Monitoring Your Backups

1. Go to your GitHub repository
2. Click "Releases" tab
3. Look for releases with `backup-` prefix
4. Download any backup to restore

## Next Steps

Choose your approach:

- **Option 1 (Manual Weekly)**: Best for small systems
  - No setup needed
  - Run: `python3 github_backup.py backup`
  
- **Option 2 (Fully Automated)**: Best for production
  - Requires adding backup endpoint to FastAPI
  - More complex setup

- **Option 3 (GitHub Actions)**: Testing only
  - Already set up
  - Good for testing restore procedures

## Setting Up Weekly Backups on macOS

**Prerequisites:**
1. Create a GitHub Personal Access Token with **repo** scope (not "Contents")
   - Go to: https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Select **repo** scope only
   - Copy token

**Setup (5 minutes):**

1. Run the setup script:
```bash
cd /Users/lucaalice/Desktop/AI\ projects/ArrivApp
./setup_local_backups.sh your_github_token_here
```

This will:
- ✅ Store token securely in `~/.arrivapp_backup_token` (chmod 600)
- ✅ Create backup script at `~/run_arrivapp_backup.sh`
- ✅ Show you how to add to crontab

2. Add to crontab:
```bash
crontab -e
# Add this line (runs every Sunday at 2 AM):
0 2 * * 0 ~/run_arrivapp_backup.sh
```

3. Test it now:
```bash
~/run_arrivapp_backup.sh
```

## Summary

Your ArrivApp is protected! Choose:
- 🟢 **Manual Weekly**: Simple, reliable
- 🟡 **Automated on Render**: Complex but fire-and-forget
- 🔴 **GitHub Actions**: Good for testing

All backups go to GitHub Releases (FREE, unlimited storage).

