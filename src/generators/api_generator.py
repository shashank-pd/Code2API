"""
API generation module - converts analyzed code into FastAPI applications
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Template, Environment, FileSystemLoader
from ..config import config

class APIGenerator:
    """Generates FastAPI applications from analyzed code"""
    
    def __init__(self):
        self.template_env = Environment(
            loader=FileSystemLoader(config.TEMPLATES_DIR),
            autoescape=True
        )
        config.ensure_directories()
    
    def generate_api(self, analysis: Dict[str, Any], project_name: str = "generated_api") -> str:
        """Generate a complete FastAPI application"""
        
        output_dir = config.GENERATED_DIR / project_name
        output_dir.mkdir(exist_ok=True)
        
        # Generate main API file
        main_file = self._generate_main_file(analysis, project_name)
        with open(output_dir / "main.py", "w") as f:
            f.write(main_file)
        
        # Generate models file
        models_file = self._generate_models_file(analysis)
        with open(output_dir / "models.py", "w") as f:
            f.write(models_file)
        
        # Generate authentication module
        auth_file = self._generate_auth_file(analysis)
        with open(output_dir / "auth.py", "w") as f:
            f.write(auth_file)
        
        # Generate requirements file
        requirements = self._generate_requirements(analysis)
        with open(output_dir / "requirements.txt", "w") as f:
            f.write(requirements)
        
        # Generate README
        readme = self._generate_readme(analysis, project_name)
        with open(output_dir / "README.md", "w") as f:
            f.write(readme)
        
        # Generate Docker files
        dockerfile = self._generate_dockerfile()
        with open(output_dir / "Dockerfile", "w") as f:
            f.write(dockerfile)
        
        docker_compose = self._generate_docker_compose(project_name)
        with open(output_dir / "docker-compose.yml", "w") as f:
            f.write(docker_compose)
        
        return str(output_dir)
    
    def _generate_main_file(self, analysis: Dict[str, Any], project_name: str) -> str:
        """Generate the main FastAPI application file"""
        
        template = """
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional, Dict, Any, List
import json

from models import *
from auth import verify_token, create_access_token

app = FastAPI(
    title="{{ project_name | title }} API",
    description="Auto-generated API from source code analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

# Authentication endpoint
@app.post("/auth/token")
async def login(credentials: UserCredentials):
    # Simple demo authentication - replace with your logic
    if credentials.username == "demo" and credentials.password == "demo":
        token = create_access_token(data={"sub": credentials.username})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

{% for endpoint in endpoints %}
# {{ endpoint.description }}
@app.{{ endpoint.http_method.lower() }}("{{ endpoint.endpoint_path }}")
async def {{ endpoint.function_name | replace('-', '_') }}(
    {% if endpoint.parameters %}
    {% for param in endpoint.parameters %}
    {% if param.name != 'self' %}
    {{ param.name }}: {{ get_python_type(param.type) or 'Any' }}{% if param.default %} = {{ param.default }}{% endif %},
    {% endif %}
    {% endfor %}
    {% endif %}
    {% if endpoint.needs_auth %}
    token: HTTPAuthorizationCredentials = Depends(security)
    {% endif %}
):
    \"\"\"
    {{ endpoint.description }}
    
    {% if endpoint.needs_auth %}
    Requires authentication.
    {% endif %}
    \"\"\"
    {% if endpoint.needs_auth %}
    # Verify authentication
    user = verify_token(token.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    {% endif %}
    
    try:
        # TODO: Implement actual function logic
        # This is a placeholder that returns the input parameters
        result = {
            "message": "Function {{ endpoint.function_name }} called successfully",
            "parameters": {
                {% for param in endpoint.parameters %}
                {% if param.name != 'self' %}
                "{{ param.name }}": {{ param.name }},
                {% endif %}
                {% endfor %}
            },
            {% if endpoint.needs_auth %}
            "authenticated_user": user["username"],
            {% endif %}
            "function_info": {
                "name": "{{ endpoint.function_name }}",
                "is_async": {{ "True" if endpoint.is_async else "False" }},
                "class_name": "{{ endpoint.get('class_name', '') }}"
            }
        }
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

{% endfor %}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
        
        jinja_template = Template(template)
        
        def get_python_type(type_str):
            """Convert type annotations to Python types"""
            if not type_str:
                return "Any"
            
            type_mapping = {
                "str": "str",
                "string": "str",
                "int": "int",
                "integer": "int",
                "float": "float",
                "bool": "bool",
                "boolean": "bool",
                "list": "List[Any]",
                "dict": "Dict[str, Any]",
                "any": "Any"
            }
            
            return type_mapping.get(type_str.lower(), "Any")
        
        return jinja_template.render(
            project_name=project_name,
            endpoints=analysis.get("api_endpoints", []),
            get_python_type=get_python_type
        )
    
    def _generate_models_file(self, analysis: Dict[str, Any]) -> str:
        """Generate Pydantic models"""
        
        template = """
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class UserCredentials(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    username: str
    email: Optional[str] = None
    is_active: bool = True

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime

{% for endpoint in endpoints %}
{% if endpoint.parameters %}
class {{ endpoint.function_name | title }}Request(BaseModel):
    {% for param in endpoint.parameters %}
    {% if param.name != 'self' %}
    {{ param.name }}: {{ get_pydantic_type(param.type) }}{% if param.default %} = {{ param.default }}{% endif %}
    {% endif %}
    {% endfor %}

{% endif %}
{% endfor %}
"""
        
        jinja_template = Template(template)
        
        def get_pydantic_type(type_str):
            """Convert type annotations to Pydantic types"""
            if not type_str:
                return "Any"
            
            type_mapping = {
                "str": "str",
                "string": "str",
                "int": "int",
                "integer": "int",
                "float": "float",
                "bool": "bool",
                "boolean": "bool",
                "list": "List[Any]",
                "dict": "Dict[str, Any]",
                "any": "Any"
            }
            
            return type_mapping.get(type_str.lower(), "Any")
        
        return jinja_template.render(
            endpoints=analysis.get("api_endpoints", []),
            get_pydantic_type=get_pydantic_type
        )
    
    def _generate_auth_file(self, analysis: Dict[str, Any]) -> str:
        """Generate authentication module"""
        
        template = """
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

# Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Fake user database for demo
fake_users_db = {
    "demo": {
        "username": "demo",
        "email": "demo@example.com",
        "hashed_password": pwd_context.hash("demo"),
        "is_active": True
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    \"\"\"Verify a password against its hash\"\"\"
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    \"\"\"Hash a password\"\"\"
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    \"\"\"Authenticate a user\"\"\"
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    \"\"\"Create a JWT access token\"\"\"
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    \"\"\"Verify and decode a JWT token\"\"\"
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        user = fake_users_db.get(username)
        return user
    except JWTError:
        return None
"""
        
        return template
    
    def _generate_requirements(self, analysis: Dict[str, Any]) -> str:
        """Generate requirements.txt for the generated API"""
        
        requirements = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "python-multipart==0.0.6"
        ]
        
        # Add additional requirements based on analysis
        endpoints = analysis.get("api_endpoints", [])
        if any(ep.get("is_async") for ep in endpoints):
            requirements.append("aiofiles==23.2.1")
        
        return "\n".join(requirements)
    
    def _generate_readme(self, analysis: Dict[str, Any], project_name: str) -> str:
        """Generate README.md for the generated API"""
        
        endpoints = analysis.get("api_endpoints", [])
        auth_endpoints = [ep for ep in endpoints if ep.get("needs_auth")]
        
        readme = f"""# {project_name.title()} API

Auto-generated API from source code analysis using Code2API.

## Features

- **{len(endpoints)} API endpoints** automatically generated
- **Authentication** using JWT tokens
- **Interactive documentation** with Swagger UI
- **CORS enabled** for cross-origin requests
- **Docker support** for easy deployment

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running the API

```bash
python main.py
```

The API will be available at `http://localhost:8000`

### Docker Deployment

```bash
docker-compose up --build
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Authentication

{len(auth_endpoints)} endpoints require authentication.

### Getting a Token

```bash
curl -X POST "http://localhost:8000/auth/token" \\
     -H "Content-Type: application/json" \\
     -d '{{"username": "demo", "password": "demo"}}'
```

### Using the Token

```bash
curl -X GET "http://localhost:8000/protected-endpoint" \\
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Available Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
"""
        
        for endpoint in endpoints:
            auth_required = "✅" if endpoint.get("needs_auth") else "❌"
            readme += f"| {endpoint['http_method']} | `{endpoint['endpoint_path']}` | {endpoint['description']} | {auth_required} |\n"
        
        readme += f"""
## Security Recommendations

{chr(10).join(f"- {rec}" for rec in analysis.get("security_recommendations", []))}

## Optimization Suggestions

{chr(10).join(f"- {sug}" for sug in analysis.get("optimization_suggestions", []))}

## Generated by Code2API

This API was automatically generated from source code analysis. 
Modify the functions in `main.py` to implement your actual business logic.
"""
        
        return readme
    
    def _generate_dockerfile(self) -> str:
        """Generate Dockerfile"""
        
        return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    def _generate_docker_compose(self, project_name: str) -> str:
        """Generate docker-compose.yml"""
        
        return f"""version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=your-production-secret-key
    restart: unless-stopped
    container_name: {project_name}_api
    
  # Optional: Add database, Redis, etc.
  # postgres:
  #   image: postgres:15
  #   environment:
  #     POSTGRES_DB: {project_name}
  #     POSTGRES_USER: user
  #     POSTGRES_PASSWORD: password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data

# volumes:
#   postgres_data:
"""
