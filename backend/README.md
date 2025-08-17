# AI Code-to-API Generator - Backend

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![LangChain](https://img.shields.io/badge/LangChain-0.1+-purple.svg)
![Groq](https://img.shields.io/badge/Groq-LLM-orange.svg)

Transform any GitHub repository into a production-ready REST API using AI agents powered by LangChain and Groq.

## 🚀 Features

- **Multi-Agent AI Pipeline**: Specialized agents for each step of the workflow
- **GitHub Integration**: Direct repository analysis and code fetching
- **FastAPI Generation**: Production-ready API code with proper structure
- **Comprehensive Security**: JWT auth, rate limiting, CORS, input validation
- **Automated Testing**: Complete test suites with coverage reporting
- **Beautiful Documentation**: Auto-generated docs with test badges
- **OpenAPI 3.0 Specs**: Industry-standard API specifications

## 🏗️ Architecture

The backend uses a multi-agent architecture with specialized tools:

```
┌─────────────────┐
│   MasterAgent   │ ← Orchestrates entire workflow
└─────────────────┘
         │
    ┌────┴────┐
    │ Tools:  │
    │         │
    ├─ CodeFetcher ────── Fetches code from GitHub
    ├─ CodeAnalyzer ───── Analyzes code structure
    ├─ APIDesigner ────── Creates OpenAPI specs
    ├─ APIGenerator ───── Generates FastAPI code
    ├─ SecurityEnforcer ─ Adds security layers
    ├─ APITester ──────── Creates test suites
    └─ DocGenerator ───── Generates documentation
```

## 🛠️ Setup

### Prerequisites

- Python 3.11+
- Groq API Key ([Get one here](https://console.groq.com/))
- GitHub Token (optional, for private repos)

### Installation

1. **Clone and enter the backend directory:**

```bash
cd backend
```

2. **Create virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
```

4. **Configure environment:**

```bash
cp example.env .env
# Edit .env with your API keys
```

5. **Start the server:**

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

Edit your `.env` file with the required configuration:

```env
# Required: Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# Optional: GitHub Token for private repos
GITHUB_TOKEN=your_github_token_here

# JWT Secret for authentication
SECRET_KEY=your-secret-key-here

# CORS origins (frontend URLs)
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 📡 API Endpoints

### Core Workflow

- **`POST /api/run-workflow`** - Execute complete code-to-API generation
- **`POST /api/upload`** - Upload code files for analysis
- **`GET /api/download/{project_name}`** - Download generated API

### Agent Management

- **`GET /api/agent/status`** - Get agent status and capabilities
- **`GET /api/agent/tools`** - List available tools
- **`POST /api/agent/run-tool/{tool_name}`** - Run individual tools

### Health & Monitoring

- **`GET /health`** - Health check with service status
- **`GET /`** - API information and status

## 🤖 Agent Tools

### CodeFetcher Tool

```python
# Fetches code from GitHub repositories
result = await code_fetcher_tool.ainvoke({
    "github_url": "https://github.com/user/repo",
    "branch": "main"
})
```

### CodeAnalyzer Tool

```python
# Analyzes code structure for API opportunities
result = await code_analyzer_tool.ainvoke({
    "code_directory": "/path/to/code",
    "language": "python"
})
```

### APIDesigner Tool

```python
# Creates OpenAPI 3.0 specifications
result = await api_designer_tool.ainvoke({
    "analysis_results": analysis_data,
    "api_title": "My API"
})
```

### APIGenerator Tool

```python
# Generates FastAPI application code
result = await api_generator_tool.ainvoke({
    "openapi_spec": openapi_data,
    "output_directory": "/path/to/output"
})
```

### SecurityEnforcer Tool

```python
# Adds comprehensive security layers
result = await security_enforcer_tool.ainvoke({
    "api_directory": "/path/to/api",
    "auth_method": "jwt"
})
```

### APITester Tool

```python
# Generates comprehensive test suites
result = await api_tester_tool.ainvoke({
    "api_directory": "/path/to/api",
    "test_types": ["unit", "integration", "security"]
})
```

### DocumentationGenerator Tool

```python
# Creates beautiful documentation
result = await documentation_generator_tool.ainvoke({
    "api_directory": "/path/to/api",
    "test_results": test_data,
    "openapi_spec": spec_data
})
```

## 🔄 Workflow Process

1. **Code Fetching**: Downloads repository from GitHub
2. **Code Analysis**: Identifies potential API endpoints
3. **API Design**: Creates OpenAPI 3.0 specification
4. **Code Generation**: Generates FastAPI application
5. **Security Enhancement**: Adds authentication and security
6. **Test Generation**: Creates comprehensive test suite
7. **Documentation**: Generates docs with test badges

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m "not slow"
```

## 📊 Example Usage

### Basic API Generation

```python
import httpx

# Start workflow
response = httpx.post("http://localhost:8000/api/run-workflow", json={
    "repo_url": "https://github.com/user/my-project",
    "branch": "main"
})

workflow_result = response.json()
print(f"Generated API at: {workflow_result['generated_api_path']}")
```

### Upload File Analysis

```python
# Upload and analyze files
with open("my_code.py", "rb") as f:
    files = {"files": ("my_code.py", f, "text/x-python")}
    response = httpx.post("http://localhost:8000/api/upload", files=files)

analysis_result = response.json()
```

## 🐳 Docker Deployment

```bash
# Build image
docker build -t code-to-api-backend .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
  code-to-api-backend
```

## 🔒 Security Features

- **JWT Authentication**: Secure token-based auth
- **Rate Limiting**: Configurable request limits
- **CORS Protection**: Cross-origin request handling
- **Input Validation**: Pydantic model validation
- **Security Headers**: OWASP recommended headers
- **File Upload Security**: Safe file handling

## 📈 Performance

- **Async Operations**: Full async/await support
- **Concurrent Processing**: Multi-agent parallel execution
- **Resource Management**: Automatic cleanup and optimization
- **Timeout Handling**: Configurable execution timeouts

## 🛠️ Development

### Project Structure

```
backend/
├── app/
│   ├── agents/           # AI agents
│   │   └── master_agent.py
│   ├── models/           # Pydantic models
│   │   └── schemas.py
│   ├── services/         # Business logic
│   │   └── file_service.py
│   └── tools/            # LangChain tools
│       ├── code_fetcher.py
│       ├── code_analyzer.py
│       ├── api_designer.py
│       ├── api_generator.py
│       ├── security_enforcer.py
│       ├── api_tester.py
│       └── documentation_generator.py
├── main.py              # FastAPI application
├── requirements.txt     # Dependencies
└── example.env         # Environment template
```

### Adding New Tools

1. Create tool in `app/tools/`
2. Import in `master_agent.py`
3. Add to tools list
4. Update documentation

### Code Quality

```bash
# Format code
black app/ main.py

# Sort imports
isort app/ main.py

# Type checking
mypy app/

# Linting
flake8 app/ main.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

## 🔮 Roadmap

- [ ] Support for more programming languages
- [ ] Database integration tools
- [ ] Custom deployment configurations
- [ ] Performance optimization tools
- [ ] Advanced security scanning
- [ ] API versioning support
- [ ] Monitoring and analytics

---

**Built with ❤️ using FastAPI, LangChain, and Groq**
