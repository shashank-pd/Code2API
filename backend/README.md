# AI-Powered Source Code to API Generator - Backend

## Overview

This is the backend API server for Code2API, an AI-powered system that analyzes source code repositories and automatically generates functional APIs with comprehensive documentation.

## Features

- **Repository Analysis**: Clone and analyze GitHub repositories
- **Multi-language Support**: Python, JavaScript, Java, C++, Go, Rust, and more
- **AI-Powered Analysis**: Uses Groq/OpenAI for intelligent code understanding
- **API Generation**: Automatic FastAPI application creation
- **Authentication**: JWT-based security system
- **Testing**: Automated API testing and validation
- **Documentation**: OpenAPI specification generation

## Quick Start

### 1. Installation

```bash
# Clone the repository
cd backend

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
GROQ_API_KEY=your-groq-api-key-here
GITHUB_TOKEN=your-github-token-here
SECRET_KEY=your-secret-key-here
```

### 3. Run the Server

```bash
# Development mode
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main module
python app/main.py
```

The API will be available at:

- API: http://localhost:8000
- Interactive Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc

## API Endpoints

### Core Analysis

- `POST /api/analyze-code` - Analyze source code directly
- `POST /api/analyze-repository` - Analyze GitHub repository
- `POST /api/generate-api` - Generate API from analysis
- `POST /api/run-workflow` - Run complete workflow

### File Operations

- `POST /api/upload` - Upload and analyze files
- `GET /api/download/{project_name}` - Download generated API

### Testing

- `POST /api/test-api` - Test generated API

### Authentication

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/user/profile` - Get user profile

### Utilities

- `GET /` - API information
- `GET /health` - Health check

## Architecture

```
app/
├── main.py              # FastAPI application
├── core/                # Core business logic
│   ├── config.py        # Configuration management
│   ├── repository_analyzer.py  # GitHub repo analysis
│   ├── code_analyzer.py       # AI-powered code analysis
│   ├── api_generator.py       # FastAPI generation
│   ├── auth.py               # Authentication
│   └── test_engine.py        # API testing
├── models/              # Pydantic models
│   ├── requests.py      # Request models
│   └── responses.py     # Response models
├── services/            # Business services
│   └── workflow_service.py   # Workflow orchestration
├── utils/               # Utility functions
│   └── file_utils.py    # File operations
└── database/            # Database layer
    └── database.py      # SQLite database
```

## Configuration

### Environment Variables

| Variable       | Description                  | Default                   |
| -------------- | ---------------------------- | ------------------------- |
| `GROQ_API_KEY` | Groq API key for AI analysis | Required                  |
| `GITHUB_TOKEN` | GitHub token for repo access | Optional                  |
| `SECRET_KEY`   | JWT secret key               | Required                  |
| `DATABASE_URL` | Database connection string   | `sqlite:///./code2api.db` |
| `HOST`         | Server host                  | `0.0.0.0`                 |
| `PORT`         | Server port                  | `8000`                    |

### AI Providers

The system supports multiple AI providers:

1. **Groq** (Recommended - Free tier available)

   - Fast inference with OpenAI models
   - Set `GROQ_API_KEY`

2. **OpenAI** (Alternative)

   - GPT models for code analysis
   - Set `OPENAI_API_KEY`

3. **Google AI** (Alternative)
   - Gemini models
   - Set `GOOGLE_AI_API_KEY`

## Usage Examples

### Analyze Repository

```bash
curl -X POST "http://localhost:8000/api/analyze-repository" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "fastapi/fastapi",
    "branch": "main"
  }'
```

### Run Complete Workflow

```bash
curl -X POST "http://localhost:8000/api/run-workflow" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "microsoft/vscode",
    "branch": "main"
  }'
```

### Upload Files for Analysis

```bash
curl -X POST "http://localhost:8000/api/upload" \
  -F "files=@example.py" \
  -F "files=@another_file.js"
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest tests/
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/

# Type checking
mypy app/
```

### Docker Deployment

```bash
# Build image
docker build -t code2api-backend .

# Run container
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your-key \
  -e GITHUB_TOKEN=your-token \
  code2api-backend
```

## API Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "timestamp": "2024-01-01T00:00:00",
  "data": {
    /* Response data */
  }
}
```

Error responses:

```json
{
  "success": false,
  "error": "Error description",
  "details": {
    /* Error details */
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

## Security

- JWT-based authentication
- Input validation with Pydantic
- Rate limiting (configurable)
- CORS configuration
- SQL injection prevention
- File upload restrictions

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Metrics

The API provides basic metrics:

- Request counts
- Response times
- Error rates
- Active workflows

## Troubleshooting

### Common Issues

1. **AI API Key Not Working**

   - Verify your API key is correct
   - Check rate limits and quotas
   - Try alternative AI providers

2. **GitHub Repository Access**

   - Ensure repository is public or provide valid token
   - Check network connectivity
   - Verify repository URL format

3. **File Upload Errors**
   - Check file size limits
   - Verify supported file types
   - Ensure sufficient disk space

### Logs

Check logs for detailed error information:

```bash
tail -f code2api.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)
- Documentation: [Full docs](https://your-docs-site.com)
- Email: support@code2api.com
