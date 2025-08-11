#!/bin/bash

# Code2API Setup and Deployment Script
set -e

echo "🚀 Code2API Setup and Deployment Script"
echo "========================================"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python dependencies
install_python_deps() {
    echo "📦 Installing Python dependencies..."
    if command_exists pip; then
        pip install -r requirements.txt
    elif command_exists pip3; then
        pip3 install -r requirements.txt
    else
        echo "❌ Error: pip not found. Please install Python and pip first."
        exit 1
    fi
    echo "✅ Python dependencies installed successfully"
}

# Function to install Node.js dependencies
install_node_deps() {
    echo "📦 Installing Node.js dependencies..."
    if command_exists npm; then
        cd frontend
        npm install
        cd ..
    elif command_exists yarn; then
        cd frontend
        yarn install
        cd ..
    else
        echo "❌ Error: npm or yarn not found. Please install Node.js first."
        exit 1
    fi
    echo "✅ Node.js dependencies installed successfully"
}

# Function to setup environment
setup_environment() {
    echo "🔧 Setting up environment..."
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo "Creating .env file..."
        cat > .env << EOF
# OpenAI API Key (required for AI analysis)
OPENAI_API_KEY=your-openai-api-key-here

# API Configuration
API_HOST=localhost
API_PORT=8000

# Security
SECRET_KEY=your-secret-key-change-in-production

# Database (optional)
POSTGRES_PASSWORD=code2api_password
EOF
        echo "✅ .env file created. Please update it with your API keys."
    else
        echo "✅ .env file already exists"
    fi
    
    # Create required directories
    mkdir -p generated templates
    echo "✅ Required directories created"
}

# Function to run tests
run_tests() {
    echo "🧪 Running tests..."
    if command_exists pytest; then
        pytest tests/ -v
        echo "✅ All tests passed"
    else
        echo "⚠️  pytest not found. Installing..."
        pip install pytest pytest-asyncio
        pytest tests/ -v
        echo "✅ All tests passed"
    fi
}

# Function to build frontend
build_frontend() {
    echo "🏗️  Building frontend..."
    cd frontend
    if command_exists npm; then
        npm run build
    elif command_exists yarn; then
        yarn build
    else
        echo "❌ Error: npm or yarn not found"
        exit 1
    fi
    cd ..
    echo "✅ Frontend built successfully"
}

# Function to start services
start_services() {
    echo "🚀 Starting Code2API services..."
    
    # Check if Docker is available
    if command_exists docker && command_exists docker-compose; then
        echo "🐳 Using Docker Compose..."
        docker-compose up -d
        echo "✅ Services started with Docker"
        echo "🌐 Frontend: http://localhost:3000"
        echo "🔧 Backend API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
    else
        echo "📝 Starting services manually..."
        
        # Start backend in background
        echo "Starting backend server..."
        python -m src.api.main &
        BACKEND_PID=$!
        
        # Wait a bit for backend to start
        sleep 5
        
        # Start frontend in background
        echo "Starting frontend server..."
        cd frontend
        if command_exists npm; then
            npm start &
        elif command_exists yarn; then
            yarn start &
        fi
        FRONTEND_PID=$!
        cd ..
        
        echo "✅ Services started manually"
        echo "🌐 Frontend: http://localhost:3000"
        echo "🔧 Backend API: http://localhost:8000"
        echo "📚 API Docs: http://localhost:8000/docs"
        echo ""
        echo "To stop services:"
        echo "  Backend PID: $BACKEND_PID"
        echo "  Frontend PID: $FRONTEND_PID"
        echo "  Use: kill $BACKEND_PID $FRONTEND_PID"
    fi
}

# Function to deploy to production
deploy_production() {
    echo "🚀 Deploying to production..."
    
    # Build Docker images
    echo "🐳 Building Docker images..."
    docker build -t code2api:latest .
    docker build -t code2api-frontend:latest ./frontend
    
    # Deploy with Docker Compose
    echo "🚀 Deploying with Docker Compose..."
    docker-compose -f docker-compose.yml up -d
    
    echo "✅ Production deployment complete"
    echo "🌐 Application available at: http://your-domain.com"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  setup       Setup environment and install dependencies"
    echo "  test        Run tests"
    echo "  build       Build frontend"
    echo "  start       Start development services"
    echo "  deploy      Deploy to production"
    echo "  demo        Run a demo analysis"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup     # Setup everything"
    echo "  $0 start     # Start development environment"
    echo "  $0 deploy    # Deploy to production"
}

# Function to run demo
run_demo() {
    echo "🎯 Running Code2API Demo..."
    
    # Check if OpenAI API key is set
    if grep -q "your-openai-api-key-here" .env 2>/dev/null; then
        echo "⚠️  Warning: Please set your OpenAI API key in .env file for full functionality"
        echo "   For demo purposes, we'll run without AI analysis"
    fi
    
    echo "📁 Analyzing sample Python file..."
    python cli.py analyze examples/sample_python.py --output demo_api
    
    echo "🔒 Running security scan..."
    python cli.py security-scan examples/sample_python.py
    
    echo "📊 Listing generated APIs..."
    python cli.py list-generated
    
    echo "✅ Demo completed! Check the 'generated/demo_api' directory for results."
}

# Main script logic
case "${1:-help}" in
    setup)
        echo "🔧 Setting up Code2API development environment..."
        setup_environment
        install_python_deps
        install_node_deps
        echo "✅ Setup completed successfully!"
        echo ""
        echo "Next steps:"
        echo "1. Update .env file with your OpenAI API key"
        echo "2. Run './deploy.sh start' to start the services"
        ;;
    test)
        run_tests
        ;;
    build)
        build_frontend
        ;;
    start)
        start_services
        ;;
    deploy)
        deploy_production
        ;;
    demo)
        run_demo
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo "❌ Unknown option: $1"
        show_usage
        exit 1
        ;;
esac
