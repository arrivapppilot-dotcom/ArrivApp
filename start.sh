#!/bin/bash

# ArrivApp Quick Start Script
# This script helps you get ArrivApp running quickly

set -e

echo "🚀 ArrivApp Quick Start"
echo "======================="
echo ""

# Check if Docker is installed
if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
    echo "✅ Docker detected"
    USE_DOCKER=true
else
    echo "⚠️  Docker not found. Will use manual setup."
    USE_DOCKER=false
fi

cd backend

# Setup environment
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  IMPORTANT: Edit backend/.env with your SMTP credentials!"
    echo ""
fi

if [ "$USE_DOCKER" = true ]; then
    # Docker setup
    echo "🐳 Starting with Docker..."
    docker-compose up -d
    
    echo "⏳ Waiting for database..."
    sleep 5
    
    echo "🔧 Initializing database..."
    docker-compose exec backend python -m app.init_db
    
    echo ""
    echo "✅ ArrivApp is running!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📡 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo "🏥 Health: http://localhost:8000/health"
    echo ""
    echo "To access frontend:"
    echo "  cd ../frontend"
    echo "  python3 -m http.server 8080"
    echo "  Open: http://localhost:8080/login.html"
    echo ""
    echo "Default credentials:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
else
    # Manual setup
    echo "🔧 Manual setup..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 not found. Please install Python 3.11+"
        exit 1
    fi
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    
    # Initialize database
    echo "🔧 Initializing database..."
    python -m app.init_db
    
    echo ""
    echo "✅ Setup complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "To start the backend:"
    echo "  source venv/bin/activate"
    echo "  uvicorn app.main:app --reload"
    echo ""
    echo "To start the frontend:"
    echo "  cd ../frontend"
    echo "  python3 -m http.server 8080"
    echo ""
    echo "Then open: http://localhost:8080/login.html"
    echo ""
    echo "Default credentials:"
    echo "  Username: admin"
    echo "  Password: admin123"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

echo ""
echo "📖 For more info, see README.md"
echo "⚠️  Remember to configure SMTP settings in backend/.env"
