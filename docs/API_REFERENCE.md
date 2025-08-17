# Code2API - API Reference

This document provides comprehensive documentation for the Code2API backend API.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: Configure according to your deployment

## Authentication

Some endpoints require authentication. Use the `/auth/token` endpoint to obtain a JWT token.

### Authentication Flow

1. **Obtain Token**
   ```bash
   curl -X POST "http://localhost:8000/auth/token" \
     -H "Content-Type: application/json" \
     -d '{"username": "demo", "password": "demo"}'
   ```

2. **Use Token in Requests**
   ```bash
   curl -X GET "http://localhost:8000/protected-endpoint" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

## Core Endpoints

### 1. Health Check

**GET** `/health`

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "message": "Code2API is running"
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/health"
```

---

### 2. Analyze Source Code

**POST** `/analyze`

Analyze source code and generate API endpoints.

**Request Body:**
```json
{
  "code": "def hello_world():\n    return 'Hello, World!'",
  "language": "python",
  "filename": "example.py"
}
```

**Parameters:**
- `code` (string, required): Source code to analyze (max 100,000 characters)
- `language` (string, required): Programming language (`python`, `javascript`, `java`, `typescript`)
- `filename` (string, required): Filename (max 255 characters, no dangerous characters)

**Response:**
```json
{
  "success": true,
  "analysis": {
    "api_endpoints": [
      {
        "function_name": "hello_world",
        "http_method": "GET",
        "endpoint_path": "/hello-world",
        "description": "Returns a greeting message",
        "needs_auth": false,
        "parameters": [],
        "is_async": false
      }
    ],
    "security_recommendations": ["Use HTTPS in production"],
    "optimization_suggestions": ["Add response caching"]
  },
  "generated_api_path": "/generated/example_py",
  "message": "Successfully analyzed example.py and generated API",
  "timestamp": "2024-01-20 10:30:45",
  "processing_time": 2.35
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def calculate_tax(amount, rate):\n    return amount * rate",
    "language": "python",
    "filename": "tax_calculator.py"
  }'
```

---

### 3. Analyze GitHub Repository

**POST** `/analyze-repo`

Analyze a GitHub repository and generate APIs from multiple files.

**Request Body:**
```json
{
  "repo_url": "https://github.com/owner/repository",
  "branch": "main",
  "include_patterns": [".py", ".js", ".java"],
  "max_files": 50
}
```

**Parameters:**
- `repo_url` (string, required): GitHub repository URL
- `branch` (string, optional): Git branch name (default: "main")
- `include_patterns` (array, optional): File extensions to analyze
- `max_files` (integer, optional): Maximum files to analyze (1-200, default: 50)

**Response:**
```json
{
  "success": true,
  "analysis": {
    "api_endpoints": [...],
    "security_recommendations": [...],
    "optimization_suggestions": [...],
    "repository_info": {
      "name": "my-project",
      "description": "A sample project",
      "language": "Python",
      "stars": 100,
      "forks": 20,
      "url": "https://github.com/owner/repository"
    },
    "statistics": {
      "languages": {"Python": 10, "JavaScript": 5},
      "total_lines": 5000
    },
    "files_analyzed": 15
  },
  "generated_api_path": "/generated/owner_repository",
  "message": "Successfully analyzed 15 files from owner/repository"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/analyze-repo" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/pallets/flask",
    "branch": "main",
    "max_files": 20
  }'
```

---

### 4. Upload and Analyze Files

**POST** `/upload`

Upload multiple source code files for analysis.

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `files` (multiple files)

**Constraints:**
- Maximum 10 files per upload
- Maximum 1MB per file
- Files must be valid UTF-8 text

**Response:**
```json
{
  "results": [
    {
      "filename": "app.py",
      "success": true,
      "analysis": {...},
      "api_path": "/generated/app_py",
      "endpoints_count": 5,
      "security_recommendations": 2
    }
  ],
  "total_files": 1,
  "successful_analyses": 1,
  "processing_time": 3.45,
  "timestamp": "2024-01-20 10:35:20"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "files=@app.py" \
  -F "files=@utils.py"
```

---

### 5. Download Generated API

**GET** `/download/{project_name}`

Download a generated API as a ZIP file.

**Parameters:**
- `project_name` (string): Name of the generated project

**Response:**
- Content-Type: `application/zip`
- ZIP file containing the complete FastAPI project

**Example:**
```bash
curl -X GET "http://localhost:8000/download/my_project" \
  -o my_project.zip
```

---

### 6. List Generated APIs

**GET** `/generated`

List all generated API projects.

**Response:**
```json
{
  "generated_apis": [
    {
      "name": "my_project",
      "path": "/generated/my_project",
      "endpoint_count": 5,
      "created": 1642678245.123
    }
  ]
}
```

**Example:**
```bash
curl -X GET "http://localhost:8000/generated"
```

---

### 7. Security Scan

**POST** `/security-scan`

Perform security analysis on source code.

**Request Body:**
```json
{
  "code": "def login(username, password):\n    if username == 'admin' and password == 'admin':\n        return True\n    return False",
  "language": "python",
  "filename": "auth.py"
}
```

**Response:**
```json
{
  "filename": "auth.py",
  "security_recommendations": [
    "Avoid hardcoded credentials",
    "Use secure password hashing",
    "Implement rate limiting for login attempts"
  ],
  "risk_level": "high"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/security-scan" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "import subprocess\ndef run_cmd(cmd):\n    subprocess.run(cmd, shell=True)",
    "language": "python",
    "filename": "dangerous.py"
  }'
```

---

### 8. Get Supported Languages

**GET** `/languages`

Get list of supported programming languages.

**Response:**
```json
{
  "supported_languages": {
    "python": {
      "extensions": [".py"],
      "tree_sitter": "python",
      "comment_style": "#"
    },
    "javascript": {
      "extensions": [".js", ".jsx", ".ts", ".tsx"],
      "tree_sitter": "javascript",
      "comment_style": "//"
    },
    "java": {
      "extensions": [".java"],
      "tree_sitter": "java",
      "comment_style": "//"
    }
  },
  "message": "Use these language identifiers when analyzing code"
}
```

## Cache Management Endpoints

### 9. Get Cache Statistics

**GET** `/cache/stats`

Get cache performance statistics.

**Response:**
```json
{
  "cache_stats": {
    "code_analysis": {
      "memory": {
        "size": 45,
        "max_size": 100,
        "hit_ratio": 0.75,
        "total_accesses": 150,
        "ttl": 1800
      },
      "disk_files": 23,
      "cache_dir": "/app/cache"
    },
    "ai_response": {
      "size": 78,
      "max_size": 500,
      "hit_ratio": 0.82,
      "total_accesses": 245,
      "ttl": 7200
    }
  },
  "timestamp": "2024-01-20 10:40:15"
}
```

### 10. Clear Cache

**POST** `/cache/clear`

Clear all cache entries (admin operation).

**Response:**
```json
{
  "message": "All caches cleared successfully",
  "timestamp": "2024-01-20 10:41:00"
}
```

### 11. Cleanup Cache

**POST** `/cache/cleanup`

Clean up expired cache entries.

**Response:**
```json
{
  "message": "Cache cleanup completed",
  "timestamp": "2024-01-20 10:41:30"
}
```

## Error Responses

All endpoints return structured error responses:

```json
{
  "error": "Validation Error",
  "detail": "Invalid input data",
  "timestamp": "2024-01-20 10:42:00",
  "errors": [
    {
      "loc": ["body", "language"],
      "msg": "Unsupported language: invalid_language. Supported: ['python', 'javascript', 'java', 'typescript']",
      "type": "value_error"
    }
  ]
}
```

### Common HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **404**: Not Found (resource doesn't exist)
- **422**: Validation Error (invalid input data)
- **429**: Rate Limit Exceeded
- **500**: Internal Server Error

## Rate Limiting

The API implements rate limiting:
- **Default**: 100 requests per 60 seconds per IP address
- **Headers**: Check `X-RateLimit-*` headers for current status

## Content Security

- All uploaded files are scanned for dangerous patterns
- File paths are sanitized to prevent directory traversal
- Input validation prevents code injection attacks
- Security headers are added to all responses

## Generated API Structure

When you download a generated API, you get:

```
project_name/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── auth.py              # Authentication module
├── requirements.txt     # Python dependencies
├── README.md            # Documentation
├── Dockerfile           # Docker configuration
└── docker-compose.yml   # Docker Compose setup
```

## Best Practices

1. **Security**
   - Always use HTTPS in production
   - Validate all input data
   - Implement proper authentication
   - Regular security scans

2. **Performance**
   - Use caching for repeated requests
   - Implement rate limiting
   - Monitor API performance
   - Optimize large file uploads

3. **Error Handling**
   - Check response status codes
   - Handle validation errors gracefully
   - Implement retry logic for transient errors
   - Log errors for debugging

4. **Development**
   - Use the sandbox environment for testing
   - Validate generated APIs before deployment
   - Review security recommendations
   - Test with realistic data volumes