#!/bin/bash

# Setup script for local GitHub backups on ArrivApp

echo "🔧 ArrivApp Local Backup Setup"
echo "================================"
echo ""

# Check if GITHUB_TOKEN is provided
if [ -z "$1" ]; then
    echo "❌ Usage: ./setup_local_backups.sh YOUR_GITHUB_TOKEN"
    echo ""
    echo "To get your GitHub token:"
    echo "1. Go to: https://github.com/settings/tokens"
    echo "2. Click 'Generate new token (classic)'"
    echo "3. Select 'Contents' scope only"
    echo "4. Copy the token"
    echo "5. Run: ./setup_local_backups.sh your_token_here"
    exit 1
fi

GITHUB_TOKEN="$1"
GITHUB_REPO="arrivapppilot-dotcom/ArrivApp"
BACKUP_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/backend"

# Create backup script
BACKUP_SCRIPT="$HOME/run_arrivapp_backup.sh"

cat > "$BACKUP_SCRIPT" << 'EOF'
#!/bin/bash
BACKUP_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/Desktop/AI projects/ArrivApp/backend"

# Load token from file
if [ -f ~/.arrivapp_backup_token ]; then
    export GITHUB_TOKEN=$(cat ~/.arrivapp_backup_token)
else
    echo "❌ Token file not found. Run setup again."
    exit 1
fi

export GITHUB_REPO="arrivapppilot-dotcom/ArrivApp"

cd "$BACKUP_SCRIPT_DIR"
python3 github_backup.py backup

# Log result
if [ $? -eq 0 ]; then
    echo "✅ Backup completed successfully" >> ~/arrivapp_backup.log
    echo "📅 $(date)" >> ~/arrivapp_backup.log
else
    echo "❌ Backup failed" >> ~/arrivapp_backup.log
    echo "📅 $(date)" >> ~/arrivapp_backup.log
fi
EOF

chmod +x "$BACKUP_SCRIPT"

# Save token securely
echo "$GITHUB_TOKEN" > ~/.arrivapp_backup_token
chmod 600 ~/.arrivapp_backup_token

echo "✅ Setup complete!"
echo ""
echo "📝 Token saved to: ~/.arrivapp_backup_token (chmod 600)"
echo "📜 Backup script created: $BACKUP_SCRIPT"
echo ""
echo "Next step: Add to crontab for weekly backups"
echo ""
echo "Run this command:"
echo "  crontab -e"
echo ""
echo "Then add this line (weekly on Sundays at 2 AM):"
echo "  0 2 * * 0 $BACKUP_SCRIPT"
echo ""
echo "Or for testing, run now:"
echo "  $BACKUP_SCRIPT"
