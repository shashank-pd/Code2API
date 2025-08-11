# Code2API - AI-Powered Source Code to API Generator
An AI-powered system that automatically converts source code into production-ready APIs with documentation and authentication.

## How to Run

### Prerequisites
- Python 3.8+
- Node.js 16+
- Groq API key

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/shashank-pd/Code2API.git
   cd Code2API
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your Groq API key
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

5. **Start the application**
   ```bash
   # Terminal 1: Start backend
   python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2: Start frontend
   cd frontend && npm start
   ```

6. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

### Docker Alternative

```bash
# Quick start with Docker Compose
docker-compose up --build
```

### CLI Usage

```bash
# Analyze a single file
python cli.py analyze-file path/to/your/code.py

# Analyze a repository
python cli.py analyze-repo https://github.com/user/repo
```

## Usage Flow

1. **Code Analysis Mode**
   - Paste your source code in the Monaco editor
   - Select language (Python, JavaScript, Java)
   - Click "Analyze Code"
   - Review generated API endpoints

2. **Repository Analysis Mode**
   - Enter GitHub repository URL
   - Click "Analyze Repository"
   - Download generated API project

**💾 Download Options:**
- Complete FastAPI project
- Docker configuration
- API documentation
- Test files

### Demo Repositories:
Try these example repositories:
```
https://github.com/pallets/flask
https://github.com/psf/requests
https://github.com/thakare-om03/Basic-Task-Manager
```
