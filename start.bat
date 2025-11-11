@echo off
REM ArrivApp Quick Start Script for Windows

echo =============================
echo ArrivApp Quick Start
echo =============================
echo.

cd backend

REM Setup environment
if not exist .env (
    echo Creating .env file...
    copy .env.example .env
    echo WARNING: Edit backend\.env with your SMTP credentials!
    echo.
)

REM Check for Docker
docker --version >nul 2>&1
if %errorlevel% == 0 (
    echo Docker detected. Starting with Docker...
    docker-compose up -d
    
    echo Waiting for database...
    timeout /t 5 /nobreak >nul
    
    echo Initializing database...
    docker-compose exec backend python -m app.init_db
    
    echo.
    echo ArrivApp is running!
    echo ================================
    echo Backend API: http://localhost:8000
    echo API Docs: http://localhost:8000/docs
    echo.
    echo To access frontend:
    echo   cd ..\frontend
    echo   python -m http.server 8080
    echo   Open: http://localhost:8080/login.html
    echo.
    echo Default credentials:
    echo   Username: admin
    echo   Password: admin123
    echo ================================
    
) else (
    echo Docker not found. Using manual setup...
    
    REM Create virtual environment
    if not exist venv (
        echo Creating virtual environment...
        python -m venv venv
    )
    
    REM Activate virtual environment
    call venv\Scripts\activate.bat
    
    REM Install dependencies
    echo Installing dependencies...
    pip install -r requirements.txt
    
    REM Initialize database
    echo Initializing database...
    python -m app.init_db
    
    echo.
    echo Setup complete!
    echo ================================
    echo To start the backend:
    echo   venv\Scripts\activate
    echo   uvicorn app.main:app --reload
    echo.
    echo To start the frontend:
    echo   cd ..\frontend
    echo   python -m http.server 8080
    echo.
    echo Then open: http://localhost:8080/login.html
    echo.
    echo Default credentials:
    echo   Username: admin
    echo   Password: admin123
    echo ================================
)

echo.
echo For more info, see README.md
echo Remember to configure SMTP settings in backend\.env
pause
