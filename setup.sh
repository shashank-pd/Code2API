#!/bin/bash

# Code2API Setup Script
echo "🚀 Setting up Code2API - AI-Powered Source Code to API Generator"
echo "================================================================"

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -o '[0-9]*\.[0-9]*\.[0-9]*')
if [[ -z "$python_version" ]]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi
echo "✅ Python $python_version found"

# Check Node.js version
echo "📋 Checking Node.js version..."
node_version=$(node --version 2>&1 | grep -o '[0-9]*\.[0-9]*\.[0-9]*')
if [[ -z "$node_version" ]]; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    exit 1
fi
echo "✅ Node.js $node_version found"

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies"
    exit 1
fi
echo "✅ Python dependencies installed"

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Node.js dependencies"
    exit 1
fi
cd ..
echo "✅ Node.js dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << EOF
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# JWT Secret Key (generate a secure random key)
SECRET_KEY=your_secure_secret_key_here

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000"]
EOF
    echo "✅ .env file created. Please update with your OpenAI API key."
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs temp generated_apis

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with your OpenAI API key"
echo "2. Start the backend: python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000"
echo "3. Start the frontend: cd frontend && npm start"
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "Or use Docker: docker-compose up -d"
echo ""
echo "Happy coding! 🚀"
