@echo off
echo 🚀 Setting up Code2API - AI-Powered Source Code to API Generator
echo ================================================================

REM Check Python version
echo 📋 Checking Python version...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)
echo ✅ Python found

REM Check Node.js version
echo 📋 Checking Node.js version...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    pause
    exit /b 1
)
echo ✅ Node.js found

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)
echo ✅ Python dependencies installed

REM Install Node.js dependencies
echo 📦 Installing Node.js dependencies...
cd frontend
call npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install Node.js dependencies
    pause
    exit /b 1
)
cd ..
echo ✅ Node.js dependencies installed

REM Create .env file if it doesn't exist
if not exist .env (
    echo 🔧 Creating .env file...
    (
        echo # OpenAI API Configuration
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo.
        echo # JWT Secret Key (generate a secure random key^)
        echo SECRET_KEY=your_secure_secret_key_here
        echo.
        echo # API Configuration
        echo API_HOST=0.0.0.0
        echo API_PORT=8000
        echo.
        echo # Frontend Configuration
        echo REACT_APP_API_URL=http://localhost:8000
        echo.
        echo # CORS Configuration
        echo CORS_ORIGINS=["http://localhost:3000"]
    ) > .env
    echo ✅ .env file created. Please update with your OpenAI API key.
) else (
    echo ✅ .env file already exists
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist logs mkdir logs
if not exist temp mkdir temp
if not exist generated_apis mkdir generated_apis

echo.
echo 🎉 Setup completed successfully!
echo.
echo Next steps:
echo 1. Update your .env file with your OpenAI API key
echo 2. Start the backend: python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
echo 3. Start the frontend: cd frontend ^&^& npm start
echo 4. Open http://localhost:3000 in your browser
echo.
echo Or use Docker: docker-compose up -d
echo.
echo Happy coding! 🚀
pause
