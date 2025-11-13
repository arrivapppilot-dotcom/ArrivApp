# GitHub Backup Setup - Quick Start

## ⏱️ 5-Minute Setup

### Step 1: Create GitHub Token (2 min)

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Fill in:
   - **Token name**: `ArrivApp Backup`
   - **Expiration**: 90 days
   - **Scope**: Check `✅ repo`
4. Click "Generate token"
5. **COPY THE TOKEN** (you won't see it again)

### Step 2: Add Token to Render (2 min)

1. Go to Render dashboard → Your Backend Service
2. Click "Environment"
3. Add variable:
   ```
   GITHUB_TOKEN = ghp_xxxxxxxxxxxxxxxxxxxx
   ```
4. Click "Save Changes"

### Step 3: Verify (1 min)

Test the backup script:

```bash
cd backend
export GITHUB_TOKEN="your_token_here"
export GITHUB_REPO="arrivapppilot-dotcom/ArrivApp"
python3 github_backup.py list
```

Should show your repository backups!

## ✅ That's It!

Your backups are now:
- 🔄 **Automated** - Daily at 2 AM UTC via GitHub Actions
- ☁️ **Cloud stored** - In GitHub Releases
- 🆓 **Free** - $0/month
- 📋 **Manageable** - Auto-cleanup keeps only 5 latest

## 📚 For More Details

See `GITHUB_BACKUP_SETUP.md` for:
- How to manually backup
- How to restore from backup
- Troubleshooting
- Security notes

## 🆘 Quick Commands

```bash
# List all backups
python3 github_backup.py list

# Create backup now
python3 github_backup.py backup

# Restore a backup
python3 github_backup.py restore backup-20251113_140000

# Clean up old backups
python3 github_backup.py cleanup
```

## ✨ All Done!

Your ArrivApp database is now safely backed up to GitHub Releases every day!
