#!/bin/bash
# Direct script to run populate_render_db.py on Render
# This connects to Render's PostgreSQL and refreshes test data

echo "=================================="
echo "🚀 Running populate on Render"
echo "=================================="
echo ""
echo "To run this on Render:"
echo "1. Go to https://dashboard.render.com/services/srv-..."
echo "2. Click 'Shell' tab at the top"
echo "3. Paste this command:"
echo ""
echo "cd /app && python backend/populate_render_db.py"
echo ""
echo "This will:"
echo "✓ Connect to Render's PostgreSQL database"
echo "✓ Delete old TEST students to avoid duplicates"
echo "✓ Generate fresh test data for today"
echo "✓ Create 135 new students (15 per school)"
echo "✓ Simulate 850+ check-ins for today"
echo ""
echo "=================================="
