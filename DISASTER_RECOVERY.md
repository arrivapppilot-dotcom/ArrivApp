# ArrivApp Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for ArrivApp, including backup strategies, restoration procedures, and business continuity planning.

## Backup Strategy

### Automated Backups

**Daily Backups (2:00 AM)**
- Full database backup (PostgreSQL dump)
- QR codes directory backup
- Configuration files backup
- Retention: 7 days for daily backups

**Weekly Backups (Sundays 3:00 AM)**
- Cleanup of old daily backups
- Retention: 30 days for weekly backups

**Monthly Backups**
- First-of-month backups retained for 365 days

### Backup Components

1. **Database Backup**
   - Format: PostgreSQL custom format (compressed)
   - Location: `/var/backups/arrivapp/database/`
   - Naming: `arrivapp_db_YYYYMMDD_HHMMSS.sql.gz`

2. **QR Codes Backup**
   - Format: tar.gz archive
   - Location: `/var/backups/arrivapp/qr_codes/`
   - Naming: `qr_codes_YYYYMMDD_HHMMSS.tar.gz`

3. **Configuration Backup**
   - Files: config.py, .env, requirements.txt, docker-compose.yml
   - Format: tar.gz archive
   - Location: `/var/backups/arrivapp/files/`
   - Naming: `config_YYYYMMDD_HHMMSS.tar.gz`

## Setup Instructions

### Initial Setup

```bash
# Navigate to backend directory
cd /path/to/ArrivApp/backend

# Make setup script executable
chmod +x setup_backup_automation.sh

# Run setup (creates directories, cron jobs, systemd services)
./setup_backup_automation.sh

# Configure database credentials
nano .env.backup
# Add your PostgreSQL credentials
```

### Environment Configuration

Create `.env.backup` file:

```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=arrivapp
DB_USER=postgres
DB_PASSWORD=your_secure_password

DAILY_RETENTION=7
WEEKLY_RETENTION=30
MONTHLY_RETENTION=365
```

### Verify Installation

```bash
# Check cron jobs
crontab -l

# Check systemd timer (if available)
sudo systemctl status arrivapp-backup.timer

# List current backups
python3 backup_system.py list

# View backup logs
tail -f /var/log/arrivapp/backup.log
```

## Manual Backup Procedures

### Full System Backup

```bash
cd /path/to/ArrivApp/backend

# Perform immediate full backup
python3 backup_system.py backup
```

### Database-Only Backup

```bash
# Using pg_dump directly
PGPASSWORD=your_password pg_dump -h localhost -U postgres -d arrivapp -F c -f backup_$(date +%Y%m%d).dump

# Compress the backup
gzip backup_$(date +%Y%m%d).dump
```

### QR Codes Backup

```bash
cd /path/to/ArrivApp/backend

# Create tar archive
tar -czf qr_codes_backup_$(date +%Y%m%d).tar.gz qr_codes/
```

## Disaster Recovery Procedures

### Scenario 1: Database Corruption/Loss

**Recovery Steps:**

1. **Stop the application**
   ```bash
   # Stop backend service
   lsof -ti:8000 | xargs kill -9
   
   # Or stop systemd service
   sudo systemctl stop arrivapp-backend
   ```

2. **Identify latest backup**
   ```bash
   python3 backup_system.py list
   
   # Or manually check
   ls -lht /var/backups/arrivapp/database/
   ```

3. **Restore database**
   ```bash
   # Using backup system
   python3 backup_system.py restore --restore-file /var/backups/arrivapp/database/arrivapp_db_20250111_020000.sql.gz
   
   # Or manually with pg_restore
   gunzip -c /var/backups/arrivapp/database/arrivapp_db_20250111_020000.sql.gz | pg_restore -h localhost -U postgres -d arrivapp -c
   ```

4. **Verify restoration**
   ```bash
   # Connect to database
   psql -h localhost -U postgres -d arrivapp
   
   # Check tables
   \dt
   
   # Verify data
   SELECT COUNT(*) FROM students;
   SELECT COUNT(*) FROM checkins;
   ```

5. **Restart application**
   ```bash
   cd /path/to/ArrivApp/backend
   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

**Expected Downtime:** 15-30 minutes

### Scenario 2: Complete Server Failure

**Recovery Steps:**

1. **Provision new server**
   - Ubuntu 20.04+ or macOS
   - Minimum 2GB RAM, 20GB storage
   - Python 3.8+, PostgreSQL 12+

2. **Install dependencies**
   ```bash
   # Install PostgreSQL
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   
   # Install Python dependencies
   sudo apt install python3-pip
   pip3 install -r requirements.txt
   ```

3. **Create database**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE arrivapp;
   CREATE USER arrivapp_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE arrivapp TO arrivapp_user;
   \q
   ```

4. **Restore from backup**
   ```bash
   # Copy backups to new server
   scp -r old-server:/var/backups/arrivapp /var/backups/
   
   # Restore database
   gunzip -c /var/backups/arrivapp/database/latest_backup.sql.gz | pg_restore -h localhost -U postgres -d arrivapp
   
   # Restore QR codes
   cd /path/to/ArrivApp/backend
   tar -xzf /var/backups/arrivapp/qr_codes/latest_qr_backup.tar.gz
   
   # Restore configuration
   tar -xzf /var/backups/arrivapp/files/latest_config.tar.gz
   ```

5. **Configure application**
   ```bash
   # Update .env file with new server details
   nano /path/to/ArrivApp/backend/.env
   
   # Initialize database schema (if needed)
   python3 app/init_db.py
   ```

6. **Start services**
   ```bash
   # Backend
   cd /path/to/ArrivApp/backend
   nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
   
   # Frontend
   cd /path/to/ArrivApp/frontend
   nohup python3 -m http.server 3000 > /tmp/frontend.log 2>&1 &
   ```

7. **Verify system**
   ```bash
   # Test API
   curl http://localhost:8000/
   
   # Test login
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"admin"}'
   ```

**Expected Downtime:** 2-4 hours

### Scenario 3: QR Code Loss

**Recovery Steps:**

1. **Restore QR codes**
   ```bash
   cd /path/to/ArrivApp/backend
   
   # Extract backup
   tar -xzf /var/backups/arrivapp/qr_codes/qr_codes_20250111_020000.tar.gz
   ```

2. **Regenerate missing QR codes**
   ```bash
   # Run QR code generation script
   python3 download_qr_codes.py
   ```

**Expected Downtime:** 5-10 minutes

### Scenario 4: Configuration Loss

**Recovery Steps:**

1. **Restore configuration files**
   ```bash
   cd /path/to/ArrivApp/backend
   
   # Extract backup
   tar -xzf /var/backups/arrivapp/files/config_20250111_020000.tar.gz
   
   # Copy files to proper locations
   cp config_20250111/config.py app/core/
   cp config_20250111/.env ./
   cp config_20250111/requirements.txt ./
   ```

2. **Restart application**
   ```bash
   # Restart backend
   lsof -ti:8000 | xargs kill -9
   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

**Expected Downtime:** 5 minutes

## Remote Backup Strategy (Optional)

### Setup Remote Backup Server

```bash
# Add to backup_system.py or create sync script
#!/bin/bash

BACKUP_DIR="/var/backups/arrivapp"
REMOTE_HOST="backup-server.example.com"
REMOTE_USER="backup_user"
REMOTE_PATH="/backups/arrivapp"

# Sync to remote server
rsync -avz --delete \
  -e "ssh -i ~/.ssh/backup_key" \
  "$BACKUP_DIR/" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/"
```

### Cloud Backup Options

**AWS S3:**
```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Sync backups to S3
aws s3 sync /var/backups/arrivapp s3://arrivapp-backups/
```

**Google Cloud Storage:**
```bash
# Install gsutil
pip install gsutil

# Upload backups
gsutil -m rsync -r /var/backups/arrivapp gs://arrivapp-backups/
```

## Monitoring and Alerts

### Backup Verification Script

```bash
#!/bin/bash
# backup_monitor.sh

BACKUP_DIR="/var/backups/arrivapp"
MAX_AGE_HOURS=30  # Alert if no backup in 30 hours

# Find latest backup
LATEST=$(find "$BACKUP_DIR/database" -name "*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
LATEST_TIME=$(stat -c %Y "$LATEST")
CURRENT_TIME=$(date +%s)
AGE_HOURS=$(( ($CURRENT_TIME - $LATEST_TIME) / 3600 ))

if [ $AGE_HOURS -gt $MAX_AGE_HOURS ]; then
  echo "⚠️  WARNING: Latest backup is $AGE_HOURS hours old!"
  # Send alert (email, Slack, etc.)
  # mail -s "ArrivApp Backup Alert" admin@example.com <<< "Latest backup is $AGE_HOURS hours old"
else
  echo "✅ Backup system healthy. Latest backup: $AGE_HOURS hours ago"
fi
```

### Add to Cron

```bash
# Check backup status every 6 hours
0 */6 * * * /path/to/backup_monitor.sh >> /var/log/arrivapp/monitor.log 2>&1
```

## Testing Procedures

### Monthly Disaster Recovery Drill

**Schedule:** First Monday of each month

1. **Restore to test environment**
   - Provision temporary database
   - Restore latest backup
   - Verify data integrity

2. **Document results**
   - Restoration time
   - Data completeness
   - Issues encountered

3. **Update procedures**
   - Fix any identified issues
   - Update documentation
   - Train team members

### Backup Verification Checklist

- [ ] Database backup exists and is complete
- [ ] Backup file is not corrupted (test restore)
- [ ] QR codes backup contains all files
- [ ] Configuration backup is up to date
- [ ] Backup logs show no errors
- [ ] Backup size is reasonable (not 0 bytes)
- [ ] Remote backup sync is working (if configured)

## Recovery Time Objectives (RTO)

| Scenario | Target RTO | Maximum RTO |
|----------|------------|-------------|
| Database corruption | 15 minutes | 30 minutes |
| QR code loss | 5 minutes | 10 minutes |
| Configuration loss | 5 minutes | 10 minutes |
| Complete server failure | 2 hours | 4 hours |
| Data center failure | 4 hours | 8 hours |

## Recovery Point Objectives (RPO)

| Data Type | Target RPO |
|-----------|------------|
| Database transactions | 24 hours |
| QR codes | 24 hours |
| Configuration | 24 hours |

## Contact Information

### Emergency Contacts

- System Administrator: [Your Name/Team]
- Database Administrator: [DBA Contact]
- Hosting Provider Support: [Provider Contact]
- Backup System Vendor: [Vendor Contact]

### Escalation Path

1. On-call engineer (immediate)
2. Lead developer (15 minutes)
3. Technical manager (30 minutes)
4. CTO/VP Engineering (1 hour)

## Appendix

### Useful Commands

```bash
# Check backup disk usage
du -sh /var/backups/arrivapp/*

# Count backup files
find /var/backups/arrivapp -name "*.sql.gz" | wc -l

# Find backups older than 30 days
find /var/backups/arrivapp -name "*.sql.gz" -mtime +30

# Test PostgreSQL connection
psql -h localhost -U postgres -d arrivapp -c "SELECT 1"

# Check database size
psql -h localhost -U postgres -d arrivapp -c "SELECT pg_size_pretty(pg_database_size('arrivapp'))"

# List all tables with row counts
psql -h localhost -U postgres -d arrivapp -c "\dt+" -c "SELECT schemaname,relname,n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC"
```

### Log Locations

- Backup logs: `/var/log/arrivapp/backup.log`
- Cleanup logs: `/var/log/arrivapp/cleanup.log`
- Monitor logs: `/var/log/arrivapp/monitor.log`
- Backend logs: `/tmp/backend.log`
- Frontend logs: `/tmp/frontend.log`
- PostgreSQL logs: `/var/log/postgresql/postgresql-*.log`

---

**Last Updated:** 2025-01-11  
**Document Version:** 1.0  
**Next Review Date:** 2025-04-11
