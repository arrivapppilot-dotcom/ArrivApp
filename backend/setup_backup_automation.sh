#!/bin/bash
# Setup automated backup system for ArrivApp

echo "🔧 Setting up ArrivApp Backup Automation"
echo "========================================"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKUP_DIR="/var/backups/arrivapp"

# Create backup directory with proper permissions
echo "📁 Creating backup directory: $BACKUP_DIR"
sudo mkdir -p "$BACKUP_DIR"
sudo chown -R $USER:$USER "$BACKUP_DIR"
chmod 750 "$BACKUP_DIR"

# Create log directory
sudo mkdir -p /var/log/arrivapp
sudo chown -R $USER:$USER /var/log/arrivapp

# Setup cron job for automated backups
echo "⏰ Setting up cron jobs..."

# Add to user's crontab
(crontab -l 2>/dev/null | grep -v "arrivapp backup"; cat <<EOF
# ArrivApp Automated Backups
# Daily backup at 2 AM
0 2 * * * cd $SCRIPT_DIR && /usr/bin/python3 backup_system.py backup --backup-dir $BACKUP_DIR >> /var/log/arrivapp/backup.log 2>&1

# Weekly cleanup at 3 AM on Sundays
0 3 * * 0 cd $SCRIPT_DIR && /usr/bin/python3 backup_system.py cleanup --backup-dir $BACKUP_DIR >> /var/log/arrivapp/cleanup.log 2>&1
EOF
) | crontab -

echo "✅ Cron jobs installed:"
echo "   - Daily backup: 2:00 AM"
echo "   - Weekly cleanup: 3:00 AM (Sundays)"

# Create systemd service (optional, for immediate execution)
if [ -d "/etc/systemd/system" ]; then
    echo "🔧 Creating systemd service..."
    
    sudo tee /etc/systemd/system/arrivapp-backup.service > /dev/null <<EOF
[Unit]
Description=ArrivApp Backup Service
After=postgresql.service

[Service]
Type=oneshot
User=$USER
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/backup_system.py backup --backup-dir $BACKUP_DIR
StandardOutput=append:/var/log/arrivapp/backup.log
StandardError=append:/var/log/arrivapp/backup.log

[Install]
WantedBy=multi-user.target
EOF

    sudo tee /etc/systemd/system/arrivapp-backup.timer > /dev/null <<EOF
[Unit]
Description=ArrivApp Daily Backup Timer
Requires=arrivapp-backup.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable arrivapp-backup.timer
    sudo systemctl start arrivapp-backup.timer
    
    echo "✅ Systemd timer enabled"
fi

# Create environment file template
if [ ! -f "$SCRIPT_DIR/.env.backup" ]; then
    cat > "$SCRIPT_DIR/.env.backup" <<EOF
# Database Backup Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=arrivapp
DB_USER=postgres
DB_PASSWORD=your_password_here

# Backup Retention (days)
DAILY_RETENTION=7
WEEKLY_RETENTION=30
MONTHLY_RETENTION=365

# Optional: Remote backup location
# REMOTE_BACKUP_HOST=backup-server.example.com
# REMOTE_BACKUP_PATH=/backups/arrivapp
# REMOTE_BACKUP_USER=backup_user
EOF
    echo "📝 Created .env.backup template - please configure database credentials"
fi

# Test backup system
echo ""
echo "🧪 Testing backup system..."
python3 "$SCRIPT_DIR/backup_system.py" list --backup-dir "$BACKUP_DIR"

echo ""
echo "✅ Backup automation setup complete!"
echo ""
echo "📋 Summary:"
echo "   - Backup directory: $BACKUP_DIR"
echo "   - Log directory: /var/log/arrivapp"
echo "   - Daily backups: 2:00 AM"
echo "   - Weekly cleanup: 3:00 AM (Sundays)"
echo ""
echo "🔧 Manual commands:"
echo "   Run backup now:  python3 backup_system.py backup"
echo "   List backups:    python3 backup_system.py list"
echo "   Cleanup old:     python3 backup_system.py cleanup"
echo "   Restore DB:      python3 backup_system.py restore --restore-file <file>"
echo ""
echo "📊 View cron jobs:  crontab -l"
echo "📄 View logs:       tail -f /var/log/arrivapp/backup.log"
echo ""
