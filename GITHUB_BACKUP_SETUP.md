# GitHub-Based Backup System

## Overview

ArrivApp now has a **FREE, automated backup system** using GitHub Releases for cloud storage. Backups are created daily and stored indefinitely (keeping the latest 5).

**Cost: $0/month** ✅

## Features

- 📦 **Automated Daily Backups** - Runs at 2 AM UTC via GitHub Actions
- ☁️ **Free Cloud Storage** - Uses GitHub Releases (no storage limits)
- 🔄 **Easy Restore** - Download and restore any backup with one command
- 🧹 **Auto Cleanup** - Keeps only latest 5 backups to save space
- 📊 **Full Backups** - Database + QR codes in each backup
- 📝 **Audit Trail** - All backups tagged with timestamp

## Setup Instructions

### 1. Create GitHub Personal Access Token

1. Go to https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. **Token name**: `ArrivApp Backup Token`
4. **Expiration**: 90 days (you'll need to renew periodically)
5. **Scopes**: Check only:
   - ✅ `repo` (Full control of private repositories)
6. Click "Generate token"
7. **Copy the token** (you won't see it again!)

### 2. Add Token to Render

1. Go to your Render backend service dashboard
2. Click "Environment"
3. Add new environment variable:
   - **Key**: `GITHUB_TOKEN`
   - **Value**: Paste your token from step 1
4. Click "Save Changes"

### 3. Verify Setup

Test the backup script locally:

```bash
cd backend
export GITHUB_TOKEN="your_token_here"
export GITHUB_REPO="arrivapppilot-dotcom/ArrivApp"
export DATABASE_PATH="arrivapp.db"
export QR_CODES_DIR="qr_codes"

# Test backup
python3 github_backup.py backup

# List backups
python3 github_backup.py list

# Cleanup old backups (keep 5)
python3 github_backup.py cleanup
```

## Usage

### Manual Backup

```bash
# From your local machine
cd backend
python3 github_backup.py backup
```

### List Backups

```bash
python3 github_backup.py list
```

Output:
```
📋 Available Backups:

📌 backup-20251113_140000
   Created: 2025-11-13T14:00:00Z
   Files: 2, Total Size: 145.32 MB
   - arrivapp_db_20251113_140000.sqlite.gz (95.10 MB)
   - qr_codes_20251113_140000.tar.gz (50.22 MB)

📌 backup-20251113_020000
   ...
```

### Restore Backup

```bash
# Download a specific backup
python3 github_backup.py restore backup-20251113_140000

# Restore the files
gunzip -c arrivapp_db_20251113_140000.sqlite.gz > arrivapp.db
tar -xzf qr_codes_20251113_140000.tar.gz
```

### Cleanup Old Backups

```bash
# Keep only the latest 5 backups
python3 github_backup.py cleanup
```

## Automated Backups via GitHub Actions

The `.github/workflows/backup.yml` file sets up:
- ✅ Daily backups at **2:00 AM UTC**
- ✅ Automatic cleanup (keeps 5 latest)
- ✅ Email notifications on failure

### To Enable Automation:

1. **Commit the files:**
   ```bash
   git add backend/github_backup.py .github/workflows/backup.yml
   git commit -m "Add GitHub-based backup system"
   git push
   ```

2. **GitHub Actions will automatically:**
   - Run daily at 2 AM UTC
   - Create backup and upload to Releases
   - Clean up old backups
   - Notify on failure

3. **Monitor backups:** Go to your repository → "Releases" tab

## Disaster Recovery Procedure

### If Database is Lost or Corrupted

1. **List available backups:**
   ```bash
   python3 github_backup.py list
   ```

2. **Restore specific backup:**
   ```bash
   python3 github_backup.py restore backup-20251113_140000
   ```

3. **Replace database:**
   ```bash
   gunzip -c arrivapp_db_20251113_140000.sqlite.gz > /path/to/arrivapp.db
   ```

4. **Restart backend service**

### If QR Codes are Lost

1. **Restore from backup:**
   ```bash
   python3 github_backup.py restore backup-20251113_140000
   ```

2. **Extract QR codes:**
   ```bash
   tar -xzf qr_codes_20251113_140000.tar.gz
   ```

3. **Copy to correct location:**
   ```bash
   cp -r qr_codes/* /path/to/qr_codes/
   ```

## Backup Storage Info

### On GitHub Releases

Each backup release contains:

```
backup-20251113_140000/
├── arrivapp_db_20251113_140000.sqlite.gz (Database)
└── qr_codes_20251113_140000.tar.gz (QR Codes)
```

### Storage Limits

- **Per file**: 2 GB (more than enough for database)
- **Total**: Unlimited releases
- **Keep policy**: Latest 5 backups (auto-cleanup)
- **Estimated storage**: ~150-300 MB per backup

### Access Backups via GitHub UI

1. Go to your repository
2. Click "Releases" → "Tags" on the right
3. Find backup with desired date
4. Download files directly

## Environment Variables

The backup script uses these environment variables:

| Variable | Purpose | Example |
|----------|---------|---------|
| `GITHUB_TOKEN` | GitHub authentication | `ghp_xxxxxxxxxxxx` |
| `GITHUB_REPO` | Target repository | `arrivapppilot-dotcom/ArrivApp` |
| `DATABASE_PATH` | Database file location | `/data/arrivapp.db` |
| `QR_CODES_DIR` | QR codes directory | `/data/qr_codes` |

## Troubleshooting

### "GITHUB_TOKEN environment variable is required"

**Solution**: Set the environment variable
```bash
export GITHUB_TOKEN="your_token_here"
```

### "Failed to create release: 422"

**Cause**: Release tag already exists

**Solution**: Wait a moment (backup includes timestamp) or manually delete old release

### "Failed to upload asset: 413"

**Cause**: File too large (>2 GB)

**Solution**: Database shouldn't exceed this. Check for corrupted files.

### Backup didn't run on schedule

**Check**:
1. Go to repository → "Actions" tab
2. Check "Daily Backup" workflow
3. Look for any errors in the logs

## Token Renewal

GitHub tokens expire after 90 days. To renew:

1. Create a new token (see "Setup" section)
2. Update `GITHUB_TOKEN` in Render environment
3. Delete the old token from GitHub settings

## Security Notes

- ✅ Token has minimal permissions (`repo` scope only)
- ✅ Token only works for your repository
- ✅ Releases are in your private repository
- ✅ Tokens can be revoked at any time
- ⚠️ Never commit tokens to git (use environment variables)

## Monitoring

### Check Backup Status

```bash
# List all backups
python3 github_backup.py list

# View specific release
# https://github.com/arrivapppilot-dotcom/ArrivApp/releases/tag/backup-20251113_140000
```

### Set Up Email Alerts

1. Go to GitHub repository settings
2. Enable email notifications for release events
3. You'll get notified when backups are created

## FAQ

**Q: How much storage does this use?**
A: Approximately 150-300 MB per daily backup. Latest 5 kept = ~1-1.5 GB total.

**Q: Can I keep more than 5 backups?**
A: Yes! Edit `cleanup_old_backups(keep_count=5)` to a higher number.

**Q: What if the token expires?**
A: Backups will fail. Renew the token as described above.

**Q: Can I restore to a different location?**
A: Yes! Download the backup files and extract manually.

**Q: What if GitHub is down?**
A: You can't create new backups, but existing ones remain accessible.

## Support

For issues or questions:
1. Check GitHub Actions logs (repository → Actions tab)
2. Verify `GITHUB_TOKEN` is set in Render
3. Ensure `GITHUB_REPO` is correct format
4. Test manually with `python3 github_backup.py backup`

