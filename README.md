# Code2API - AI-Powered Source Code to API Generator

<div align="center">

![Code2API Banner](https://img.shields.io/badge/Code2API-AI%20Powered-blue?style=for-the-badge&logo=python)
![Work in Progress](https://img.shields.io/badge/🚧-Work%20in%20Progress-orange?style=for-the-badge)

**Transform your source code into production-ready APIs with AI-powered analysis and generation**

[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18.2+-61DAFB?style=flat-square&logo=react)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.114+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)

</div>

## ✨ Features

- 🤖 **AI-Powered Analysis** - Leverages Groq Cloud API for intelligent code understanding
- 🚀 **Multi-Language Support** - Python, JavaScript, Java with extensible architecture
- 📊 **Interactive Dashboard** - Real-time code analysis with beautiful visualizations
- 🔧 **Auto-Generated APIs** - Creates production-ready FastAPI endpoints
- 📖 **Swagger Documentation** - Automatic API documentation generation
- 🔒 **Security Analysis** - Built-in security recommendations and best practices
- 🐙 **GitHub Integration** - Analyze entire repositories with one click
- 🎨 **Modern UI** - Sleek interface with animations and responsive design

## 🎥 UI Showcase

<div align="center">


https://github.com/user-attachments/assets/8f2f8dd9-abed-4922-8fa0-e94aaabe9af7



</div>

## 🛠️ Tech Stack

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.114.1 | High-performance API framework |
| **Python** | 3.8+ | Core backend language |
| **Uvicorn** | 0.30.6 | ASGI server for FastAPI |
| **Pydantic** | 2.8.2 | Data validation and serialization |
| **Tree-sitter** | 0.25.1 | Multi-language code parsing |
| **Groq** | 0.4.1 | AI-powered code analysis |
| **GitPython** | 3.1.45 | Git repository interaction |
| **PyJWT** | 2.10.1 | JWT authentication |
| **Jinja2** | 3.1.2 | Template engine for code generation |

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18.2.0 | Modern UI framework |
| **TypeScript** | Latest | Type-safe JavaScript |
| **Tailwind CSS** | 3.4.0 | Utility-first CSS framework |
| **Framer Motion** | 10.16.16 | Smooth animations |
| **Monaco Editor** | 0.44.0 | VS Code-like code editor |
| **Swagger UI** | 5.9.0 | Interactive API documentation |
| **Axios** | 1.6.0 | HTTP client for API calls |
| **Lucide React** | 0.303.0 | Beautiful icons |

### Code Analysis
| Language | Parser | Version |
|----------|--------|---------|
| **Python** | tree-sitter-python | 0.23.6 |
| **JavaScript** | tree-sitter-javascript | 0.23.1 |
| **Java** | tree-sitter-java | 0.23.5 |
| **Syntax Highlighting** | Pygments | 2.18.0 |

### Development & Testing
| Tool | Version | Purpose |
|------|---------|---------|
| **Pytest** | 8.0.0 | Testing framework |
| **Black** | 23.11.0 | Code formatting |
| **Flake8** | 6.1.0 | Code linting |
| **Bandit** | 1.7.5 | Security analysis |
| **MyPy** | 1.7.0 | Static type checking |

### Infrastructure
| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Server** | Nginx | Production web server |
| **Process Manager** | PM2 | Production process management |
| **CORS** | FastAPI CORS Middleware | Cross-origin requests |

## 🚀 Quick Start

### Prerequisites
- **Python 3.8+** - [Download Python](https://python.org/downloads/)
- **Node.js 16+** - [Download Node.js](https://nodejs.org/)
- **Groq API Key** - [Get API Key](https://console.groq.com/keys)

### 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/shashank-pd/Code2API.git
   cd Code2API
   ```

2. **Set up environment variables**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys (Groq API key required)
   ```

3. **Install dependencies**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Install frontend dependencies
   cd frontend && npm install && cd ..
   ```

### 🏃‍♂️ Running the Application

#### Development Mode (Main Code2API Application)
```bash
# Terminal 1: Start backend
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd frontend && npm start
```

#### Running Generated API Projects
After analyzing a repository and generating APIs:

```bash
# Navigate to the generated project
cd generated/{your-analyzed-repo-name}

# Run the generated API server
python main.py
```

The generated API will run on **port 8001** where you can test the analyzed repository's APIs.

### 🌐 Access Points

#### Main Code2API Application
- **Frontend:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Docs:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### Generated Repository APIs
- **Generated API Server:** [http://localhost:8001](http://localhost:8001)
- **Test Generated APIs:** [http://localhost:8001/docs](http://localhost:8001/docs)

## 💻 Usage Guide

### 📝 Code Analysis Mode
1. Open the application in your browser
2. Select **Code Editor** mode
3. Choose your programming language (Python/JavaScript/Java)
4. Paste your source code in the Monaco editor
5. Click **"Analyze Code"** to generate API endpoints
6. Review the generated API documentation and endpoints

### 🐙 Repository Analysis Mode
1. Switch to **GitHub Repository** mode
2. Enter a GitHub repository URL (e.g., `https://github.com/user/repo`)
3. Specify the branch (default: `main`)
4. Click **"Analyze Repository"**
5. Download the generated FastAPI project

### 📥 Download Options
- **Complete FastAPI Project** - Ready-to-deploy API server
- **API Documentation** - Swagger/OpenAPI specifications
- **Test Files** - Automated test suites

## 🔧 CLI Usage

```bash
# Analyze a single file
python cli.py analyze-file path/to/your/code.py

# Analyze a GitHub repository
python cli.py analyze-repo https://github.com/user/repo
```

## 🎯 Demo Repositories

Try these example repositories to see Code2API in action:

| Repository | Description | Language |
|------------|-------------|----------|
| [Python Calculator](https://github.com/inforkgodara/python-calculator) | Simple calculator with basic operations | Python |
| [BMI Calculator](https://github.com/Raveesh1505/BMI-Calculator) | Body Mass Index calculator application | Python |

> 📝 **Note:** More demo repositories will be added soon to showcase different programming languages and use cases!

---

<div align="center">
  <strong>Made with ❤️ by the Code2API Team</strong>
</div>
