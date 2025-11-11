#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Python dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Create necessary directories
mkdir -p backend/qr_codes
mkdir -p backend/test_backups/database
mkdir -p backend/test_backups/files
mkdir -p backend/test_backups/qr_codes

# Initialize database
cd backend
python -m app.init_db

echo "Build completed successfully!"
