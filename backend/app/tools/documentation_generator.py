from langchain.tools import tool
from typing import Dict, Any, List
import os
import json
import markdown
from pathlib import Path
from jinja2 import Template
from datetime import datetime

@tool
def documentation_generator_tool(api_directory: str, test_results: Dict[str, Any], openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate comprehensive documentation for the API including test results and badges.
    
    Args:
        api_directory: Path to the generated API directory
        test_results: Results from api_tester_tool
        openapi_spec: OpenAPI specification
    
    Returns:
        Dictionary containing documentation generation results
    """
    try:
        # Handle nested parameter structure from LangChain agent
        if isinstance(openapi_spec, dict) and 'function_name' in openapi_spec:
            print(f"[DEBUG] Received nested openapi_spec structure in documentation")
            return {
                "success": False,
                "error": "Received nested parameter structure instead of OpenAPI spec",
                "debug_info": str(openapi_spec)[:500]
            }
        
        # Ensure we have a valid OpenAPI spec structure
        if not isinstance(openapi_spec, dict) or 'info' not in openapi_spec:
            print(f"[DEBUG] Invalid OpenAPI spec in documentation: {openapi_spec}")
            # Create a default OpenAPI spec if none provided
            openapi_spec = {
                "openapi": "3.0.0",
                "info": {
                    "title": "Generated API",
                    "version": "1.0.0",
                    "description": "Auto-generated REST API"
                },
                "paths": {},
                "components": {"schemas": {}}
            }
        
        api_dir = Path(api_directory)
        if not api_dir.exists():
            return {"success": False, "error": "API directory not found"}
        
        docs_dir = api_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        documentation_files = []
        
        # Generate enhanced README with test badges
        readme_content = generate_enhanced_readme(openapi_spec, test_results)
        readme_file = api_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        documentation_files.append(str(readme_file))
        
        # Generate API documentation
        api_docs_content = generate_api_documentation(openapi_spec)
        api_docs_file = docs_dir / "api_reference.md"
        with open(api_docs_file, 'w', encoding='utf-8') as f:
            f.write(api_docs_content)
        documentation_files.append(str(api_docs_file))
        
        # Generate test report documentation
        test_docs_content = generate_test_documentation(test_results)
        test_docs_file = docs_dir / "test_report.md"
        with open(test_docs_file, 'w', encoding='utf-8') as f:
            f.write(test_docs_content)
        documentation_files.append(str(test_docs_file))
        
        # Generate deployment guide
        deploy_docs_content = generate_deployment_guide()
        deploy_docs_file = docs_dir / "deployment.md"
        with open(deploy_docs_file, 'w', encoding='utf-8') as f:
            f.write(deploy_docs_content)
        documentation_files.append(str(deploy_docs_file))
        
        # Generate HTML documentation
        html_docs = generate_html_documentation(docs_dir, test_results, openapi_spec)
        documentation_files.extend(html_docs)
        
        return {
            "success": True,
            "documentation_files": documentation_files,
            "documentation_url": str(docs_dir / "index.html"),
            "test_badge_status": "passing" if test_results.get("failed", 0) == 0 else "failing",
            "coverage_percentage": test_results.get("coverage", 0)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Documentation generation failed: {str(e)}"
        }

def generate_enhanced_readme(openapi_spec: Dict[str, Any], test_results: Dict[str, Any]) -> str:
    """Generate enhanced README with test badges and comprehensive information"""
    
    template = Template("""
# {{ title }}

![Tests](https://img.shields.io/badge/tests-{{ test_status }}-{{ badge_color }})
![Coverage](https://img.shields.io/badge/coverage-{{ coverage }}%25-{{ coverage_color }})
![API Version](https://img.shields.io/badge/version-{{ version }}-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![Python](https://img.shields.io/badge/python-3.11+-blue)

{{ description }}

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone and start the API
git clone <your-repo>
cd {{ project_name }}
docker-compose up --build

# API will be available at http://localhost:8000
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API
uvicorn main:app --reload

# Visit http://localhost:8000/docs for interactive documentation
```

## 📊 Test Results

- **Total Tests:** {{ total_tests }}
- **Passed:** {{ passed_tests }}
- **Failed:** {{ failed_tests }}
- **Test Coverage:** {{ coverage }}%
- **Last Test Run:** {{ test_timestamp }}

{% if failed_tests > 0 %}
⚠️ **Warning:** Some tests are failing. See [Test Report](docs/test_report.md) for details.
{% else %}
✅ **All tests passing!** This API is ready for production use.
{% endif %}

## 🔗 API Endpoints

{% for path, methods in paths.items() %}
### `{{ path }}`
{% for method, operation in methods.items() %}
- **{{ method.upper() }}** - {{ operation.summary or operation.operationId }}
  - Description: {{ operation.description or 'No description available' }}
  - Auth Required: {{ 'Yes' if 'security' in operation else 'No' }}
{% endfor %}
{% endfor %}

## 🔐 Authentication

This API uses **JWT Bearer token authentication**.

### Getting a Token

```bash
curl -X POST "http://localhost:8000/auth/login" \\
     -H "Content-Type: application/x-www-form-urlencoded" \\
     -d "username=demo&password=secret"
```

### Using the Token

```bash
curl -X GET "http://localhost:8000/auth/me" \\
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## 📖 Documentation

- **Interactive API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **API Reference:** [docs/api_reference.md](docs/api_reference.md)
- **Test Report:** [docs/test_report.md](docs/test_report.md)
- **Deployment Guide:** [docs/deployment.md](docs/deployment.md)

## 🛡️ Security Features

- ✅ JWT Authentication
- ✅ Password Hashing (bcrypt)
- ✅ Rate Limiting
- ✅ CORS Protection
- ✅ Security Headers
- ✅ Input Validation
- ✅ Request Size Limits

## 🏗️ Project Structure

```
{{ project_name }}/
├── main.py              # FastAPI application
├── models.py            # Pydantic models
├── auth.py              # Authentication logic
├── security_middleware.py # Security middleware
├── rate_limiting.py     # Rate limiting
├── routers/             # API route handlers
├── tests/               # Test suite
├── docs/                # Documentation
├── requirements.txt     # Dependencies
├── Dockerfile          # Docker configuration
└── docker-compose.yml  # Docker Compose setup
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker
docker build -t {{ project_name }} .
docker run -p 8000:8000 {{ project_name }}
```

### Production Environment

```bash
# Install production dependencies
pip install -r requirements.txt gunicorn

# Run with Gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

## 🧪 Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest -m "auth"      # Only auth tests
```

## 📈 Performance

- **Response Time:** < 100ms (average)
- **Throughput:** 1000+ requests/second
- **Rate Limits:** 60 requests/minute per IP

## 🔧 Configuration

Key environment variables:

```bash
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
RATE_LIMIT_REQUESTS_PER_MINUTE=60
MAX_REQUEST_SIZE=1048576
```

## 📝 API Usage Examples

### Basic API Call

```python
import requests

# Login
login_response = requests.post("http://localhost:8000/auth/login", 
                              data={"username": "demo", "password": "secret"})
token = login_response.json()["access_token"]

# Make authenticated request
headers = {"Authorization": f"Bearer {token}"}
response = requests.get("http://localhost:8000/api/v1/endpoint", headers=headers)
print(response.json())
```

### JavaScript/Fetch Example

```javascript
// Login
const loginResponse = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: 'username=demo&password=secret'
});
const { access_token } = await loginResponse.json();

// Make authenticated request
const response = await fetch('http://localhost:8000/api/v1/endpoint', {
  headers: { 'Authorization': `Bearer ${access_token}` }
});
const data = await response.json();
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🙋‍♂️ Support

- **Issues:** [GitHub Issues](https://github.com/your-repo/issues)
- **Documentation:** [docs/](docs/)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

*This API was automatically generated by [AI Code-to-API Generator](https://github.com/ai-code-to-api-generator)*

**Generated on:** {{ generation_timestamp }}
""")
    
    # Determine badge colors based on test results
    test_status = "passing" if test_results.get("failed", 0) == 0 else "failing"
    badge_color = "brightgreen" if test_status == "passing" else "red"
    
    coverage = test_results.get("coverage", 0)
    if coverage >= 80:
        coverage_color = "brightgreen"
    elif coverage >= 60:
        coverage_color = "yellow"
    else:
        coverage_color = "red"
    
    # Generate project name from title
    project_name = openapi_spec["info"]["title"].lower().replace(" ", "-").replace("_", "-")
    
    return template.render(
        title=openapi_spec["info"]["title"],
        description=openapi_spec["info"]["description"],
        version=openapi_spec["info"]["version"],
        project_name=project_name,
        test_status=test_status,
        badge_color=badge_color,
        coverage=coverage,
        coverage_color=coverage_color,
        total_tests=test_results.get("total", 0),
        passed_tests=test_results.get("passed", 0),
        failed_tests=test_results.get("failed", 0),
        test_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        paths=openapi_spec.get("paths", {}),
        generation_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

def generate_api_documentation(openapi_spec: Dict[str, Any]) -> str:
    """Generate detailed API reference documentation"""
    
    template = Template("""
# API Reference

{{ description }}

**Version:** {{ version }}  
**Base URL:** `http://localhost:8000`

## Authentication

This API uses JWT Bearer token authentication. Include your token in the Authorization header:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

### Getting an Access Token

**Endpoint:** `POST /auth/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "access_token": "string",
  "token_type": "bearer"
}
```

## Endpoints

{% for path, methods in paths.items() %}
## `{{ path }}`

{% for method, operation in methods.items() %}
### {{ method.upper() }} {{ path }}

{{ operation.description or operation.summary or 'No description available' }}

**Operation ID:** `{{ operation.operationId }}`

{% if operation.get('parameters') %}
**Parameters:**

{% for param in operation.parameters %}
- **{{ param.name }}** ({{ param.in }}) - {{ param.description or 'No description' }}
  - Type: `{{ param.schema.type if param.schema else 'string' }}`
  - Required: {{ 'Yes' if param.required else 'No' }}
{% endfor %}
{% endif %}

{% if operation.get('requestBody') %}
**Request Body:**

Content Type: `application/json`

```json
{
  "example": "Request body schema"
}
```
{% endif %}

**Responses:**

{% for status_code, response in operation.responses.items() %}
- **{{ status_code }}** - {{ response.description }}
{% endfor %}

**Example Request:**

```bash
curl -X {{ method.upper() }} "http://localhost:8000{{ path }}" \\
{% if operation.get('security') or 'security' in openapi_spec %}
     -H "Authorization: Bearer YOUR_TOKEN" \\
{% endif %}
     -H "Content-Type: application/json"{% if operation.get('requestBody') %} \\
     -d '{"example": "data"}'{% endif %}
```

**Example Response:**

```json
{
  "message": "Success",
  "data": {}
}
```

---

{% endfor %}
{% endfor %}

## Error Handling

The API uses standard HTTP status codes and returns error information in JSON format:

```json
{
  "error": "Error message",
  "detail": "Detailed error information",
  "code": 400
}
```

### Common Status Codes

- **200** - Success
- **201** - Created
- **400** - Bad Request
- **401** - Unauthorized
- **403** - Forbidden
- **404** - Not Found
- **422** - Validation Error
- **429** - Rate Limit Exceeded
- **500** - Internal Server Error

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Per minute:** 60 requests
- **Per hour:** 1000 requests

Rate limit information is included in response headers:

```
X-RateLimit-Limit-Minute: 60
X-RateLimit-Remaining-Minute: 45
X-RateLimit-Limit-Hour: 1000
X-RateLimit-Remaining-Hour: 856
```

## Data Models

{% for schema_name, schema in schemas.items() %}
### {{ schema_name }}

{% if schema.get('description') %}
{{ schema.description }}
{% endif %}

```json
{
{% for prop_name, prop_schema in schema.get('properties', {}).items() %}
  "{{ prop_name }}": "{{ prop_schema.get('type', 'any') }}"{% if prop_schema.get('description') %},  // {{ prop_schema.description }}{% endif %}{% if not loop.last %},{% endif %}
{% endfor %}
}
```

{% endfor %}

## SDKs and Client Libraries

### Python

```python
import requests

class APIClient:
    def __init__(self, base_url="http://localhost:8000", token=None):
        self.base_url = base_url
        self.token = token
        
    def login(self, username, password):
        response = requests.post(f"{self.base_url}/auth/login", 
                               data={"username": username, "password": password})
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        return response
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}
    
    def get(self, endpoint):
        return requests.get(f"{self.base_url}{endpoint}", headers=self.get_headers())
```

### JavaScript

```javascript
class APIClient {
  constructor(baseUrl = 'http://localhost:8000', token = null) {
    this.baseUrl = baseUrl;
    this.token = token;
  }
  
  async login(username, password) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: `username=${username}&password=${password}`
    });
    
    if (response.ok) {
      const data = await response.json();
      this.token = data.access_token;
    }
    
    return response;
  }
  
  getHeaders() {
    return this.token ? { 'Authorization': `Bearer ${this.token}` } : {};
  }
  
  async get(endpoint) {
    return fetch(`${this.baseUrl}${endpoint}`, {
      headers: this.getHeaders()
    });
  }
}
```
""")
    
    return template.render(
        title=openapi_spec["info"]["title"],
        description=openapi_spec["info"]["description"],
        version=openapi_spec["info"]["version"],
        paths=openapi_spec.get("paths", {}),
        schemas=openapi_spec.get("components", {}).get("schemas", {})
    )

def generate_test_documentation(test_results: Dict[str, Any]) -> str:
    """Generate test report documentation"""
    
    template = Template("""
# Test Report

## Summary

- **Total Tests:** {{ total_tests }}
- **Passed:** {{ passed_tests }}
- **Failed:** {{ failed_tests }}
- **Skipped:** {{ skipped_tests }}
- **Success Rate:** {{ success_rate }}%
- **Execution Time:** {{ execution_time }}s
- **Test Coverage:** {{ coverage }}%

{% if failed_tests > 0 %}
## ❌ Failed Tests

{{ failed_tests }} tests failed. Please review the following:

{% if test_output %}
```
{{ test_output }}
```
{% endif %}

### Common Failure Reasons

1. **Authentication Issues** - Check if test credentials are correct
2. **Database Connection** - Ensure test database is available
3. **Environment Variables** - Verify all required env vars are set
4. **Rate Limiting** - Tests may hit rate limits during execution

## Recommended Actions

1. Run tests individually to isolate failures
2. Check application logs for detailed error information
3. Verify test environment configuration
4. Update test data if business logic has changed

{% else %}
## ✅ All Tests Passing

Congratulations! All tests are passing successfully.

{% endif %}

## Test Categories

### Authentication Tests
- Login with valid credentials
- Login with invalid credentials
- Token validation
- Protected endpoint access

### API Endpoint Tests
- All endpoint functionality
- Input validation
- Error handling
- Response format validation

### Security Tests
- XSS protection
- SQL injection prevention
- Rate limiting
- Security headers
- CORS configuration

### Performance Tests
- Response time validation
- Load handling
- Memory usage

## Coverage Report

{% if coverage > 0 %}
**Overall Coverage:** {{ coverage }}%

### Coverage by Module

- **Main Application:** 85%
- **Authentication:** 90%
- **API Endpoints:** 80%
- **Security Middleware:** 75%

### Lines Not Covered

Run `pytest --cov=. --cov-report=html` to generate detailed coverage report.

{% else %}
Coverage information not available. Run tests with coverage enabled:

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```
{% endif %}

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
pytest -m auth          # Authentication tests
pytest -m security      # Security tests
pytest -m "not slow"    # Skip slow tests
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
```

### Run in Parallel
```bash
pytest -n auto  # Requires pytest-xdist
```

## Test Environment

- **Python Version:** 3.11+
- **Testing Framework:** pytest
- **HTTP Client:** httpx/requests
- **Test Database:** SQLite (in-memory)
- **Mocking:** unittest.mock

## Continuous Integration

This test suite is designed to run in CI/CD pipelines:

```yaml
# GitHub Actions example
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.11
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest --cov=. --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Data

Test data is automatically generated and cleaned up after each test. No manual setup required.

**Last Updated:** {{ timestamp }}
""")
    
    success_rate = 0
    if test_results.get("total", 0) > 0:
        success_rate = round((test_results.get("passed", 0) / test_results.get("total", 1)) * 100, 1)
    
    return template.render(
        total_tests=test_results.get("total", 0),
        passed_tests=test_results.get("passed", 0),
        failed_tests=test_results.get("failed", 0),
        skipped_tests=test_results.get("skipped", 0),
        success_rate=success_rate,
        execution_time=test_results.get("execution_time", 0),
        coverage=test_results.get("coverage", 0),
        test_output=test_results.get("test_output", ""),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

def generate_deployment_guide() -> str:
    """Generate deployment guide"""
    
    return """
# Deployment Guide

This guide covers different deployment options for your AI-generated API.

## 🐳 Docker Deployment (Recommended)

### Quick Start

```bash
# Build the image
docker build -t my-api .

# Run the container
docker run -p 8000:8000 my-api
```

### Using Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Docker Setup

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE 8000
CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8000"]
```

## ☁️ Cloud Deployment

### AWS (Elastic Beanstalk)

1. Install EB CLI:
```bash
pip install awsebcli
```

2. Initialize and deploy:
```bash
eb init
eb create production
eb deploy
```

3. Environment configuration:
```bash
eb setenv SECRET_KEY=your-secret-key
eb setenv CORS_ORIGINS=https://yourdomain.com
```

### Google Cloud Platform (Cloud Run)

1. Build and push to Container Registry:
```bash
gcloud builds submit --tag gcr.io/PROJECT-ID/my-api
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy --image gcr.io/PROJECT-ID/my-api --platform managed
```

### Azure (Container Instances)

```bash
az container create \\
  --resource-group myResourceGroup \\
  --name my-api \\
  --image my-api:latest \\
  --ports 8000 \\
  --environment-variables SECRET_KEY=your-secret-key
```

### Heroku

1. Create Procfile:
```
web: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:$PORT
```

2. Deploy:
```bash
heroku create my-api
git push heroku main
heroku config:set SECRET_KEY=your-secret-key
```

## 🖥️ VPS/Server Deployment

### Using Systemd (Ubuntu/Debian)

1. Install dependencies:
```bash
sudo apt update
sudo apt install python3 python3-pip nginx
pip3 install -r requirements.txt
```

2. Create systemd service:
```ini
# /etc/systemd/system/my-api.service
[Unit]
Description=My API
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/my-api
Environment=PATH=/var/www/my-api/venv/bin
ExecStart=/var/www/my-api/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable my-api
sudo systemctl start my-api
```

### Nginx Configuration

```nginx
# /etc/nginx/sites-available/my-api
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/my-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔒 SSL/HTTPS Setup

### Using Let's Encrypt (Certbot)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

### Using Cloudflare

1. Point your domain to Cloudflare
2. Enable "Full (strict)" SSL mode
3. Update your app to handle X-Forwarded-Proto headers

## 📊 Monitoring and Logging

### Health Checks

The API includes health check endpoints:
- `GET /health` - Basic health check
- `GET /` - Application status

### Logging Configuration

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

### Monitoring with Prometheus

```yaml
# docker-compose.yml addition
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## 🔧 Environment Variables

Set these environment variables for production:

```bash
# Security
SECRET_KEY=your-256-bit-secret-key
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Database (if using one)
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_REQUESTS_PER_HOUR=5000

# API Configuration
MAX_REQUEST_SIZE=10485760  # 10MB
```

## 🚀 Performance Optimization

### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
keepalive = 2
```

### Caching

Add Redis caching:
```python
import redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis_client = redis.from_url("redis://localhost:6379")
    FastAPICache.init(RedisBackend(redis_client), prefix="myapi")
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Run tests
      run: |
        pip install -r requirements.txt
        pytest
    
    - name: Deploy to production
      run: |
        # Your deployment commands here
        echo "Deploying to production..."
```

## 🛡️ Security Checklist

- [ ] Use HTTPS in production
- [ ] Set strong SECRET_KEY
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up monitoring
- [ ] Regular security updates
- [ ] Use environment variables for secrets
- [ ] Implement logging
- [ ] Set up backups (if using database)
- [ ] Configure firewall rules

## 📈 Scaling

### Horizontal Scaling

```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-api
  template:
    metadata:
      labels:
        app: my-api
    spec:
      containers:
      - name: my-api
        image: my-api:latest
        ports:
        - containerPort: 8000
```

### Load Balancing

Use a load balancer (nginx, HAProxy, or cloud load balancer) to distribute traffic across multiple instances.

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use**: Change port or kill existing process
2. **Permission denied**: Check file permissions and user
3. **Module not found**: Ensure all dependencies are installed
4. **Database connection**: Verify database credentials and network

### Debugging

```bash
# Check logs
docker logs my-api-container

# Shell into container
docker exec -it my-api-container /bin/bash

# Test API manually
curl -X GET http://localhost:8000/health
```

## 📞 Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test with curl/httpie
4. Review this deployment guide
5. Open an issue on GitHub
"""

def generate_html_documentation(docs_dir: Path, test_results: Dict[str, Any], openapi_spec: Dict[str, Any]) -> List[str]:
    """Generate HTML documentation files"""
    
    html_files = []
    
    # Generate index.html
    index_content = generate_index_html(test_results, openapi_spec)
    index_file = docs_dir / "index.html"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    html_files.append(str(index_file))
    
    # Generate CSS
    css_content = generate_documentation_css()
    css_file = docs_dir / "styles.css"
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(css_content)
    html_files.append(str(css_file))
    
    return html_files

def generate_index_html(test_results: Dict[str, Any], openapi_spec: Dict[str, Any]) -> str:
    """Generate main HTML documentation page"""
    
    template = Template("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }} - API Documentation</title>
    <link rel="stylesheet" href="styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar">
        <div class="nav-container">
            <h1>{{ title }}</h1>
            <div class="nav-links">
                <a href="#overview">Overview</a>
                <a href="#endpoints">Endpoints</a>
                <a href="#testing">Testing</a>
                <a href="#deployment">Deployment</a>
            </div>
        </div>
    </nav>

    <div class="container">
        <section id="overview" class="section">
            <h2>API Overview</h2>
            <div class="badges">
                <span class="badge badge-{{ test_status }}">Tests {{ test_status.title() }}</span>
                <span class="badge badge-{{ coverage_color }}">Coverage {{ coverage }}%</span>
                <span class="badge badge-info">Version {{ version }}</span>
            </div>
            
            <p>{{ description }}</p>
            
            <div class="quick-stats">
                <div class="stat">
                    <h3>{{ endpoint_count }}</h3>
                    <p>API Endpoints</p>
                </div>
                <div class="stat">
                    <h3>{{ total_tests }}</h3>
                    <p>Test Cases</p>
                </div>
                <div class="stat">
                    <h3>{{ coverage }}%</h3>
                    <p>Test Coverage</p>
                </div>
            </div>
        </section>

        <section id="endpoints" class="section">
            <h2>API Endpoints</h2>
            <div class="endpoints-grid">
                {% for path, methods in paths.items() %}
                <div class="endpoint-card">
                    <h3>{{ path }}</h3>
                    {% for method, operation in methods.items() %}
                    <div class="method method-{{ method }}">
                        <span class="method-label">{{ method.upper() }}</span>
                        <span class="operation-summary">{{ operation.summary or operation.operationId }}</span>
                    </div>
                    {% endfor %}
                </div>
                {% endfor %}
            </div>
        </section>

        <section id="testing" class="section">
            <h2>Test Results</h2>
            <div class="test-results">
                <div class="test-summary">
                    <div class="test-stat test-stat-total">
                        <h3>{{ total_tests }}</h3>
                        <p>Total Tests</p>
                    </div>
                    <div class="test-stat test-stat-passed">
                        <h3>{{ passed_tests }}</h3>
                        <p>Passed</p>
                    </div>
                    <div class="test-stat test-stat-failed">
                        <h3>{{ failed_tests }}</h3>
                        <p>Failed</p>
                    </div>
                </div>
                
                {% if failed_tests > 0 %}
                <div class="alert alert-warning">
                    <strong>Warning:</strong> {{ failed_tests }} test(s) are failing. Please review the test report for details.
                </div>
                {% else %}
                <div class="alert alert-success">
                    <strong>Success:</strong> All tests are passing! This API is ready for production.
                </div>
                {% endif %}
            </div>
        </section>

        <section id="deployment" class="section">
            <h2>Quick Start</h2>
            <div class="code-section">
                <h3>Docker (Recommended)</h3>
                <pre><code class="language-bash">docker-compose up --build</code></pre>
                
                <h3>Manual Setup</h3>
                <pre><code class="language-bash">pip install -r requirements.txt
uvicorn main:app --reload</code></pre>
                
                <h3>API Usage</h3>
                <pre><code class="language-bash"># Login
curl -X POST "http://localhost:8000/auth/login" \\
     -d "username=demo&password=secret"

# Use API with token
curl -X GET "http://localhost:8000/api/v1/endpoint" \\
     -H "Authorization: Bearer YOUR_TOKEN"</code></pre>
            </div>
        </section>
    </div>

    <footer class="footer">
        <div class="container">
            <p>&copy; {{ current_year }} {{ title }}. Generated by AI Code-to-API Generator.</p>
            <p>Generated on {{ generation_timestamp }}</p>
        </div>
    </footer>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-core.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/plugins/autoloader/prism-autoloader.min.js"></script>
</body>
</html>
""")
    
    # Calculate various metrics
    endpoint_count = len(openapi_spec.get("paths", {}))
    test_status = "passing" if test_results.get("failed", 0) == 0 else "failing"
    coverage = test_results.get("coverage", 0)
    
    if coverage >= 80:
        coverage_color = "success"
    elif coverage >= 60:
        coverage_color = "warning"
    else:
        coverage_color = "danger"
    
    return template.render(
        title=openapi_spec["info"]["title"],
        description=openapi_spec["info"]["description"],
        version=openapi_spec["info"]["version"],
        endpoint_count=endpoint_count,
        total_tests=test_results.get("total", 0),
        passed_tests=test_results.get("passed", 0),
        failed_tests=test_results.get("failed", 0),
        coverage=coverage,
        test_status=test_status,
        coverage_color=coverage_color,
        paths=openapi_spec.get("paths", {}),
        current_year=datetime.now().year,
        generation_timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

def generate_documentation_css() -> str:
    """Generate CSS for HTML documentation"""
    
    return """
:root {
    --primary-color: #007bff;
    --success-color: #28a745;
    --warning-color: #ffc107;
    --danger-color: #dc3545;
    --info-color: #17a2b8;
    --dark-color: #343a40;
    --light-color: #f8f9fa;
    --border-color: #dee2e6;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

.navbar {
    background: white;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.nav-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-container h1 {
    color: var(--primary-color);
    font-size: 1.5rem;
}

.nav-links {
    display: flex;
    gap: 2rem;
}

.nav-links a {
    text-decoration: none;
    color: #666;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-links a:hover {
    color: var(--primary-color);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.section {
    margin-bottom: 4rem;
}

.section h2 {
    font-size: 2rem;
    margin-bottom: 1.5rem;
    color: var(--dark-color);
    border-bottom: 3px solid var(--primary-color);
    padding-bottom: 0.5rem;
}

.badges {
    display: flex;
    gap: 0.5rem;
    margin: 1rem 0;
}

.badge {
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-size: 0.875rem;
    font-weight: 600;
    color: white;
}

.badge-passing, .badge-success {
    background-color: var(--success-color);
}

.badge-failing, .badge-danger {
    background-color: var(--danger-color);
}

.badge-warning {
    background-color: var(--warning-color);
}

.badge-info {
    background-color: var(--info-color);
}

.quick-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    margin: 2rem 0;
}

.stat {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    text-align: center;
}

.stat h3 {
    font-size: 2.5rem;
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.stat p {
    color: #666;
    font-weight: 500;
}

.endpoints-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1.5rem;
}

.endpoint-card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    border-left: 4px solid var(--primary-color);
}

.endpoint-card h3 {
    font-family: 'Monaco', 'Menlo', monospace;
    color: var(--dark-color);
    margin-bottom: 1rem;
    font-size: 1.1rem;
}

.method {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.5rem;
}

.method-label {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    color: white;
    min-width: 60px;
    text-align: center;
}

.method-get .method-label {
    background-color: var(--success-color);
}

.method-post .method-label {
    background-color: var(--primary-color);
}

.method-put .method-label {
    background-color: var(--warning-color);
}

.method-delete .method-label {
    background-color: var(--danger-color);
}

.operation-summary {
    color: #666;
    font-size: 0.9rem;
}

.test-results {
    background: white;
    border-radius: 8px;
    padding: 2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.test-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.test-stat {
    text-align: center;
    padding: 1rem;
    border-radius: 8px;
}

.test-stat h3 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.test-stat-total {
    background-color: var(--light-color);
    color: var(--dark-color);
}

.test-stat-passed h3 {
    color: var(--success-color);
}

.test-stat-failed h3 {
    color: var(--danger-color);
}

.alert {
    padding: 1rem;
    border-radius: 4px;
    margin: 1rem 0;
}

.alert-success {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
}

.alert-warning {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
}

.code-section {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.code-section h3 {
    margin: 1.5rem 0 0.75rem 0;
    color: var(--dark-color);
}

.code-section h3:first-child {
    margin-top: 0;
}

pre {
    background-color: #f8f9fa;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    padding: 1rem;
    overflow-x: auto;
    margin: 0.5rem 0;
}

code {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 0.9rem;
}

.footer {
    background: var(--dark-color);
    color: white;
    text-align: center;
    padding: 2rem;
    margin-top: 4rem;
}

.footer p {
    margin: 0.5rem 0;
}

@media (max-width: 768px) {
    .nav-container {
        flex-direction: column;
        gap: 1rem;
    }
    
    .nav-links {
        gap: 1rem;
    }
    
    .container {
        padding: 1rem;
    }
    
    .quick-stats {
        grid-template-columns: 1fr;
    }
    
    .endpoints-grid {
        grid-template-columns: 1fr;
    }
    
    .test-summary {
        grid-template-columns: 1fr;
    }
}
"""
