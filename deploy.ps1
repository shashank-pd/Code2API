# Code2API Setup and Deployment Script for Windows
# PowerShell version of deploy.sh

param(
    [Parameter(Position=0)]
    [ValidateSet("setup", "test", "build", "start", "deploy", "demo", "help")]
    [string]$Action = "help"
)

Write-Host "🚀 Code2API Setup and Deployment Script (Windows)" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green

function Test-CommandExists {
    param($Command)
    $null = Get-Command $Command -ErrorAction SilentlyContinue
    return $?
}

function Install-PythonDependencies {
    Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
    
    if (Test-CommandExists "pip") {
        pip install -r requirements.txt
    } elseif (Test-CommandExists "pip3") {
        pip3 install -r requirements.txt
    } else {
        Write-Host "❌ Error: pip not found. Please install Python and pip first." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Python dependencies installed successfully" -ForegroundColor Green
}

function Install-NodeDependencies {
    Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Yellow
    
    if (Test-CommandExists "npm") {
        Set-Location frontend
        npm install
        Set-Location ..
    } elseif (Test-CommandExists "yarn") {
        Set-Location frontend
        yarn install
        Set-Location ..
    } else {
        Write-Host "❌ Error: npm or yarn not found. Please install Node.js first." -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Node.js dependencies installed successfully" -ForegroundColor Green
}

function Setup-Environment {
    Write-Host "🔧 Setting up environment..." -ForegroundColor Yellow
    
    # Create .env file if it doesn't exist
    if (-not (Test-Path ".env")) {
        Write-Host "Creating .env file..." -ForegroundColor Yellow
        @"
# OpenAI API Key (required for AI analysis)
OPENAI_API_KEY=your-openai-api-key-here

# API Configuration
API_HOST=localhost
API_PORT=8000

# Security
SECRET_KEY=your-secret-key-change-in-production

# Database (optional)
POSTGRES_PASSWORD=code2api_password
"@ | Out-File -FilePath ".env" -Encoding UTF8
        Write-Host "✅ .env file created. Please update it with your API keys." -ForegroundColor Green
    } else {
        Write-Host "✅ .env file already exists" -ForegroundColor Green
    }
    
    # Create required directories
    if (-not (Test-Path "generated")) { New-Item -ItemType Directory -Path "generated" }
    if (-not (Test-Path "templates")) { New-Item -ItemType Directory -Path "templates" }
    Write-Host "✅ Required directories created" -ForegroundColor Green
}

function Run-Tests {
    Write-Host "🧪 Running tests..." -ForegroundColor Yellow
    
    if (Test-CommandExists "pytest") {
        pytest tests/ -v
        Write-Host "✅ All tests passed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  pytest not found. Installing..." -ForegroundColor Yellow
        pip install pytest pytest-asyncio
        pytest tests/ -v
        Write-Host "✅ All tests passed" -ForegroundColor Green
    }
}

function Build-Frontend {
    Write-Host "🏗️  Building frontend..." -ForegroundColor Yellow
    
    Set-Location frontend
    if (Test-CommandExists "npm") {
        npm run build
    } elseif (Test-CommandExists "yarn") {
        yarn build
    } else {
        Write-Host "❌ Error: npm or yarn not found" -ForegroundColor Red
        exit 1
    }
    Set-Location ..
    Write-Host "✅ Frontend built successfully" -ForegroundColor Green
}

function Start-Services {
    Write-Host "🚀 Starting Code2API services..." -ForegroundColor Yellow
    
    # Check if Docker is available
    if ((Test-CommandExists "docker") -and (Test-CommandExists "docker-compose")) {
        Write-Host "🐳 Using Docker Compose..." -ForegroundColor Cyan
        docker-compose up -d
        Write-Host "✅ Services started with Docker" -ForegroundColor Green
    } else {
        Write-Host "📝 Starting services manually..." -ForegroundColor Yellow
        
        # Start backend
        Write-Host "Starting backend server..." -ForegroundColor Yellow
        Start-Process -FilePath "python" -ArgumentList "-m", "src.api.main" -NoNewWindow
        
        # Wait for backend to start
        Start-Sleep -Seconds 5
        
        # Start frontend
        Write-Host "Starting frontend server..." -ForegroundColor Yellow
        Set-Location frontend
        if (Test-CommandExists "npm") {
            Start-Process -FilePath "npm" -ArgumentList "start" -NoNewWindow
        } elseif (Test-CommandExists "yarn") {
            Start-Process -FilePath "yarn" -ArgumentList "start" -NoNewWindow
        }
        Set-Location ..
        
        Write-Host "✅ Services started manually" -ForegroundColor Green
    }
    
    Write-Host ""
    Write-Host "🌐 Frontend: http://localhost:3000" -ForegroundColor Cyan
    Write-Host "🔧 Backend API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
}

function Deploy-Production {
    Write-Host "🚀 Deploying to production..." -ForegroundColor Yellow
    
    # Build Docker images
    Write-Host "🐳 Building Docker images..." -ForegroundColor Yellow
    docker build -t code2api:latest .
    docker build -t code2api-frontend:latest ./frontend
    
    # Deploy with Docker Compose
    Write-Host "🚀 Deploying with Docker Compose..." -ForegroundColor Yellow
    docker-compose -f docker-compose.yml up -d
    
    Write-Host "✅ Production deployment complete" -ForegroundColor Green
    Write-Host "🌐 Application available at: http://your-domain.com" -ForegroundColor Cyan
}

function Run-Demo {
    Write-Host "🎯 Running Code2API Demo..." -ForegroundColor Yellow
    
    # Check if OpenAI API key is set
    if ((Get-Content ".env" -ErrorAction SilentlyContinue) -match "your-openai-api-key-here") {
        Write-Host "⚠️  Warning: Please set your OpenAI API key in .env file for full functionality" -ForegroundColor Yellow
        Write-Host "   For demo purposes, we'll run without AI analysis" -ForegroundColor Yellow
    }
    
    Write-Host "📁 Analyzing sample Python file..." -ForegroundColor Yellow
    python cli.py analyze examples/sample_python.py --output demo_api
    
    Write-Host "🔒 Running security scan..." -ForegroundColor Yellow
    python cli.py security-scan examples/sample_python.py
    
    Write-Host "📊 Listing generated APIs..." -ForegroundColor Yellow
    python cli.py list-generated
    
    Write-Host "✅ Demo completed! Check the 'generated/demo_api' directory for results." -ForegroundColor Green
}

function Show-Usage {
    Write-Host "Usage: .\deploy.ps1 [OPTION]" -ForegroundColor White
    Write-Host ""
    Write-Host "Options:" -ForegroundColor Yellow
    Write-Host "  setup       Setup environment and install dependencies" -ForegroundColor White
    Write-Host "  test        Run tests" -ForegroundColor White
    Write-Host "  build       Build frontend" -ForegroundColor White
    Write-Host "  start       Start development services" -ForegroundColor White
    Write-Host "  deploy      Deploy to production" -ForegroundColor White
    Write-Host "  demo        Run a demo analysis" -ForegroundColor White
    Write-Host "  help        Show this help message" -ForegroundColor White
    Write-Host ""
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  .\deploy.ps1 setup     # Setup everything" -ForegroundColor White
    Write-Host "  .\deploy.ps1 start     # Start development environment" -ForegroundColor White
    Write-Host "  .\deploy.ps1 deploy    # Deploy to production" -ForegroundColor White
}

# Main script logic
switch ($Action) {
    "setup" {
        Write-Host "🔧 Setting up Code2API development environment..." -ForegroundColor Green
        Setup-Environment
        Install-PythonDependencies
        Install-NodeDependencies
        Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Yellow
        Write-Host "1. Update .env file with your OpenAI API key" -ForegroundColor White
        Write-Host "2. Run '.\deploy.ps1 start' to start the services" -ForegroundColor White
    }
    "test" {
        Run-Tests
    }
    "build" {
        Build-Frontend
    }
    "start" {
        Start-Services
    }
    "deploy" {
        Deploy-Production
    }
    "demo" {
        Run-Demo
    }
    "help" {
        Show-Usage
    }
    default {
        Write-Host "❌ Unknown option: $Action" -ForegroundColor Red
        Show-Usage
        exit 1
    }
}
