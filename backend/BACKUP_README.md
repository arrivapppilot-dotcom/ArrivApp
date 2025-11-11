# ArrivApp Backup & Recovery System

Complete automated backup and disaster recovery solution for ArrivApp.

## Features

✅ **Automated Daily Backups**
- PostgreSQL database dumps (compressed)
- QR codes directory archives
- Configuration files backup
- Retention policies (7 days daily, 30 days weekly, 365 days monthly)

✅ **Disaster Recovery**
- One-command restoration
- Complete recovery procedures
- Tested recovery scenarios
- RTO/RPO documented

✅ **Monitoring**
- Backup verification scripts
- Alert system integration
- Comprehensive logging

## Quick Start

### 1. Test the Backup System

```bash
cd backend
python3 test_backup_system.py
```

This will:
- Create test backups
- Verify all components work
- Show you what files will be backed up

### 2. Configure Database Credentials

Create `.env.backup` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=arrivapp
DB_USER=postgres
DB_PASSWORD=your_password_here
```

Or use your existing `.env` file - the backup system will read from it.

### 3. Setup Automated Backups

```bash
cd backend
./setup_backup_automation.sh
```

This installs:
- Daily backup cron job (2:00 AM)
- Weekly cleanup cron job (3:00 AM Sundays)
- Systemd timer (optional)
- Log files in `/var/log/arrivapp/`

### 4. Verify Installation

```bash
# Check cron jobs are installed
crontab -l

# List existing backups
python3 backup_system.py list

# View backup logs
tail -f /var/log/arrivapp/backup.log
```

## Manual Operations

### Create Backup Now

```bash
cd backend
python3 backup_system.py backup
```

Output example:
```
2025-01-11 14:30:00 - INFO - Starting database backup
2025-01-11 14:30:05 - INFO - Database backup completed: 45.23 MB
2025-01-11 14:30:05 - INFO - Starting QR codes backup
2025-01-11 14:30:06 - INFO - QR codes backup completed: 12.45 MB
2025-01-11 14:30:06 - INFO - Starting configuration backup
2025-01-11 14:30:07 - INFO - Configuration backup completed: 0.05 MB
```

### List All Backups

```bash
python3 backup_system.py list
```

### Cleanup Old Backups

```bash
python3 backup_system.py cleanup
```

### Restore Database

```bash
# Find the backup you want to restore
python3 backup_system.py list

# Restore specific backup
python3 backup_system.py restore --restore-file /var/backups/arrivapp/database/arrivapp_db_20250111_020000.sql.gz
```

## Backup Locations

```
/var/backups/arrivapp/
├── database/
│   ├── arrivapp_db_20250111_020000.sql.gz
│   ├── arrivapp_db_20250111_020000.json (metadata)
│   └── ...
├── qr_codes/
│   ├── qr_codes_20250111_020000.tar.gz
│   ├── qr_codes_20250111_020000.json (metadata)
│   └── ...
└── files/
    ├── config_20250111_020000.tar.gz
    ├── config_20250111_020000.json (metadata)
    └── ...
```

## Disaster Recovery Scenarios

Full procedures documented in [DISASTER_RECOVERY.md](../DISASTER_RECOVERY.md)

### Scenario 1: Database Corruption

**Recovery Time:** 15-30 minutes

```bash
# 1. Stop application
lsof -ti:8000 | xargs kill -9

# 2. Restore database
python3 backup_system.py restore --restore-file /var/backups/arrivapp/database/latest_backup.sql.gz

# 3. Restart application
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Scenario 2: Complete Server Failure

**Recovery Time:** 2-4 hours

1. Provision new server
2. Install dependencies (PostgreSQL, Python)
3. Copy backups from old server or cloud storage
4. Restore database, QR codes, configuration
5. Start services

### Scenario 3: Lost QR Codes

**Recovery Time:** 5-10 minutes

```bash
cd backend
tar -xzf /var/backups/arrivapp/qr_codes/latest_qr_backup.tar.gz
# Or regenerate: python3 download_qr_codes.py
```

## Backup Schedule

| Type | Frequency | Time | Retention |
|------|-----------|------|-----------|
| Full backup | Daily | 2:00 AM | 7 days |
| Cleanup | Weekly | Sunday 3:00 AM | - |
| Weekly backup | Sunday | 2:00 AM | 30 days |
| Monthly backup | 1st of month | 2:00 AM | 365 days |

## Monitoring

### Check Backup Status

```bash
# View recent logs
tail -20 /var/log/arrivapp/backup.log

# Check disk usage
du -sh /var/backups/arrivapp/*

# Count backups
find /var/backups/arrivapp -name "*.sql.gz" | wc -l
```

### Setup Alerts

Add email/Slack notifications by editing `backup_system.py`:

```python
def send_alert(message):
    # Email
    subprocess.run(['mail', '-s', 'Backup Alert', 'admin@example.com'], 
                   input=message.encode())
    
    # Or Slack
    import requests
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    requests.post(webhook_url, json={"text": message})
```

## Remote/Cloud Backup

### Sync to Remote Server

```bash
# Add to cron after local backup
rsync -avz /var/backups/arrivapp/ user@backup-server:/backups/arrivapp/
```

### AWS S3 Backup

```bash
# Install AWS CLI
pip install awscli

# Configure
aws configure

# Add to cron
aws s3 sync /var/backups/arrivapp s3://your-bucket/arrivapp-backups/
```

### Google Cloud Storage

```bash
# Install gsutil
pip install gsutil

# Authenticate
gcloud auth login

# Add to cron
gsutil -m rsync -r /var/backups/arrivapp gs://your-bucket/arrivapp-backups/
```

## Testing

### Monthly DR Drill

**Schedule:** First Monday of each month

```bash
# 1. Create test database
createdb arrivapp_test

# 2. Restore to test database
gunzip -c /var/backups/arrivapp/database/latest.sql.gz | \
  pg_restore -d arrivapp_test

# 3. Verify data
psql arrivapp_test -c "SELECT COUNT(*) FROM students;"

# 4. Document results
echo "DR Test $(date): Success" >> /var/log/arrivapp/dr_tests.log

# 5. Cleanup
dropdb arrivapp_test
```

## Troubleshooting

### Backup Fails: "pg_dump: command not found"

Install PostgreSQL client tools:
```bash
# macOS
brew install postgresql

# Ubuntu/Debian
sudo apt install postgresql-client

# Check version
pg_dump --version
```

### Backup Fails: "Permission denied"

Fix backup directory permissions:
```bash
sudo chown -R $USER:$USER /var/backups/arrivapp
chmod 750 /var/backups/arrivapp
```

### Backup Size is 0 bytes

Check database connection:
```bash
psql -h localhost -U postgres -d arrivapp -c "SELECT 1"
```

Verify credentials in `.env.backup`

### Restore Fails

Check backup file integrity:
```bash
gunzip -t /var/backups/arrivapp/database/backup.sql.gz
```

Verify PostgreSQL is running:
```bash
pg_isready -h localhost
```

### Cron Job Not Running

Check cron service:
```bash
# macOS
sudo launchctl list | grep cron

# Linux
sudo systemctl status cron
```

Verify cron logs:
```bash
# macOS
tail -f /var/mail/$USER

# Linux
grep CRON /var/log/syslog
```

## Best Practices

1. **Test Restores Monthly** - Ensure backups are actually restorable
2. **Monitor Disk Space** - Keep backup disk usage under 80%
3. **Offsite Backups** - Store copies in different physical location
4. **Encrypt Backups** - Add encryption for sensitive data
5. **Document Changes** - Update DR plan when system changes
6. **Train Team** - Ensure multiple people can perform restores

## Security Considerations

### Encrypt Backups

```bash
# Encrypt backup with GPG
gpg --symmetric --cipher-algo AES256 backup.sql.gz

# Decrypt when needed
gpg --decrypt backup.sql.gz.gpg > backup.sql.gz
```

### Secure Backup Storage

```bash
# Set restrictive permissions
chmod 600 /var/backups/arrivapp/database/*.sql.gz
chmod 700 /var/backups/arrivapp
```

### Rotate Encryption Keys

Store encryption keys separately from backups. Rotate annually.

## Resources

- [DISASTER_RECOVERY.md](../DISASTER_RECOVERY.md) - Complete DR procedures
- [backup_system.py](backup_system.py) - Main backup script
- [setup_backup_automation.sh](setup_backup_automation.sh) - Automation setup
- [test_backup_system.py](test_backup_system.py) - Test suite

## Support

For issues or questions:
1. Check logs: `/var/log/arrivapp/backup.log`
2. Run test: `python3 test_backup_system.py`
3. Review [TROUBLESHOOTING.md](../TROUBLESHOOTING.md)
4. Contact system administrator

---

**Last Updated:** 2025-01-11  
**Version:** 1.0
