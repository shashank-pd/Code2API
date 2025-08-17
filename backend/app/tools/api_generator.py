from langchain.tools import tool
from typing import Dict, Any, List
import os
import json
from jinja2 import Template
from pathlib import Path

@tool
def api_generator_tool(openapi_spec: Dict[str, Any], analysis_result: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    """
    Generate FastAPI server code from OpenAPI specification and analysis results.
    
    Args:
        openapi_spec: OpenAPI 3.0 specification
        analysis_result: Original code analysis results
        output_dir: Directory to output the generated API
    
    Returns:
        Dictionary containing generation results and file paths
    """
    try:
        # Handle nested parameter structure from LangChain agent
        if isinstance(openapi_spec, dict) and 'function_name' in openapi_spec:
            # Extract the actual OpenAPI spec from the nested structure
            # This happens when LangChain passes tool results as parameters
            print(f"[DEBUG] Received nested openapi_spec structure: {type(openapi_spec)}")
            return {
                "success": False,
                "error": "Received nested parameter structure instead of OpenAPI spec",
                "debug_info": str(openapi_spec)[:500]
            }
        
        # Ensure we have a valid OpenAPI spec structure
        if not isinstance(openapi_spec, dict) or 'info' not in openapi_spec:
            print(f"[DEBUG] Invalid OpenAPI spec structure: {openapi_spec}")
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
        
        # Create output directory
        api_dir = Path(output_dir)
        api_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Generate main FastAPI application
        main_content = generate_main_app(openapi_spec, analysis_result)
        main_file = api_dir / "main.py"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
        generated_files.append(str(main_file))
        
        # Generate models (Pydantic schemas)
        models_content = generate_models(openapi_spec)
        models_file = api_dir / "models.py"
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(models_content)
        generated_files.append(str(models_file))
        
        # Generate routers
        routers_dir = api_dir / "routers"
        routers_dir.mkdir(exist_ok=True)
        router_files = generate_routers(openapi_spec, analysis_result, routers_dir)
        generated_files.extend(router_files)
        
        # Generate requirements.txt
        requirements_content = generate_requirements()
        requirements_file = api_dir / "requirements.txt"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write(requirements_content)
        generated_files.append(str(requirements_file))
        
        # Generate Dockerfile
        dockerfile_content = generate_dockerfile()
        dockerfile = api_dir / "Dockerfile"
        with open(dockerfile, 'w', encoding='utf-8') as f:
            f.write(dockerfile_content)
        generated_files.append(str(dockerfile))
        
        # Generate docker-compose.yml
        docker_compose_content = generate_docker_compose()
        docker_compose_file = api_dir / "docker-compose.yml"
        with open(docker_compose_file, 'w', encoding='utf-8') as f:
            f.write(docker_compose_content)
        generated_files.append(str(docker_compose_file))
        
        # Generate README.md
        readme_content = generate_readme(openapi_spec, analysis_result)
        readme_file = api_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        generated_files.append(str(readme_file))
        
        # Save OpenAPI spec as JSON
        spec_file = api_dir / "openapi.json"
        with open(spec_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_spec, f, indent=2)
        generated_files.append(str(spec_file))
        
        return {
            "success": True,
            "generated_files": generated_files,
            "output_directory": str(api_dir),
            "endpoints_count": len(openapi_spec.get("paths", {})),
            "files_created": len(generated_files)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"API generation failed: {str(e)}"
        }

def generate_main_app(openapi_spec: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
    """Generate main FastAPI application file"""
    
    template = Template("""
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
import uvicorn
import json
from pathlib import Path

# Import routers
{% for tag in tags %}
from routers import {{ tag.lower() }}
{% endfor %}

# Import models
from models import *

# Security
security = HTTPBearer()

# Create FastAPI app
app = FastAPI(
    title="{{ title }}",
    description="{{ description }}",
    version="{{ version }}",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    # TODO: Implement proper JWT validation
    # For now, just check if token exists
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    return {"user_id": "demo_user"}

# Include routers
{% for tag in tags %}
app.include_router({{ tag.lower() }}.router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
{% endfor %}

@app.get("/")
async def root():
    return {"message": "{{ title }} is running", "docs": "/docs"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "{{ version }}"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
""")
    
    # Extract tags from OpenAPI spec
    tags = set()
    for path_info in openapi_spec.get("paths", {}).values():
        for operation in path_info.values():
            if "tags" in operation:
                tags.update(operation["tags"])
    
    return template.render(
        title=openapi_spec["info"]["title"],
        description=openapi_spec["info"]["description"],
        version=openapi_spec["info"]["version"],
        tags=sorted(tags)
    )

def generate_models(openapi_spec: Dict[str, Any]) -> str:
    """Generate Pydantic models from OpenAPI schemas"""
    
    template = Template("""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Base response models
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[int] = Field(None, description="Error code")

class SuccessResponse(BaseModel):
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")

# Generated models from OpenAPI schemas
{% for schema_name, schema in schemas.items() %}
{% if schema_name not in ['ErrorResponse', 'SuccessResponse'] %}
class {{ schema_name }}(BaseModel):
    {% if schema.get('properties') %}
    {% for prop_name, prop_schema in schema.properties.items() %}
    {{ prop_name }}: {{ get_python_type(prop_schema) }} = Field({{ get_field_params(prop_schema, prop_name in schema.get('required', [])) }})
    {% endfor %}
    {% else %}
    # TODO: Define properties for {{ schema_name }}
    pass
    {% endif %}

{% endif %}
{% endfor %}
""")
    
    def get_python_type(prop_schema):
        if prop_schema.get("type") == "string":
            return "str"
        elif prop_schema.get("type") == "integer":
            return "int"
        elif prop_schema.get("type") == "number":
            return "float"
        elif prop_schema.get("type") == "boolean":
            return "bool"
        elif prop_schema.get("type") == "array":
            return "List[Any]"
        elif prop_schema.get("type") == "object":
            return "Dict[str, Any]"
        else:
            return "Any"
    
    def get_field_params(prop_schema, required):
        params = []
        if required:
            params.append("...")
        else:
            params.append("None")
        
        if "description" in prop_schema:
            params.append(f'description="{prop_schema["description"]}"')
        
        return ", ".join(params)
    
    schemas = openapi_spec.get("components", {}).get("schemas", {})
    
    return template.render(
        schemas=schemas,
        get_python_type=get_python_type,
        get_field_params=get_field_params
    )

def generate_routers(openapi_spec: Dict[str, Any], analysis_result: Dict[str, Any], routers_dir: Path) -> List[str]:
    """Generate FastAPI routers grouped by tags"""
    
    generated_files = []
    
    # Group paths by tags
    paths_by_tag = {}
    for path, path_info in openapi_spec.get("paths", {}).items():
        for method, operation in path_info.items():
            tags = operation.get("tags", ["default"])
            for tag in tags:
                if tag not in paths_by_tag:
                    paths_by_tag[tag] = []
                paths_by_tag[tag].append({
                    "path": path,
                    "method": method,
                    "operation": operation
                })
    
    # Generate router for each tag
    for tag, paths in paths_by_tag.items():
        router_content = generate_single_router(tag, paths, analysis_result)
        router_file = routers_dir / f"{tag.lower()}.py"
        with open(router_file, 'w', encoding='utf-8') as f:
            f.write(router_content)
        generated_files.append(str(router_file))
    
    # Generate __init__.py for routers package
    init_file = routers_dir / "__init__.py"
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write("# Routers package")
    generated_files.append(str(init_file))
    
    return generated_files

def generate_single_router(tag: str, paths: List[Dict[str, Any]], analysis_result: Dict[str, Any]) -> str:
    """Generate a single router file for a tag"""
    
    template = Template("""
from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import Optional, List, Dict, Any
from models import *

router = APIRouter(tags=["{{ tag }}"])

{% for path_info in paths %}
@router.{{ path_info.method }}("{{ path_info.path }}")
async def {{ path_info.operation.operationId }}(
    {% for param in path_info.operation.get('parameters', []) %}
    {% if param.in == 'path' %}
    {{ param.name }}: {{ get_param_type(param) }} = Path(..., description="{{ param.description }}"),
    {% elif param.in == 'query' %}
    {{ param.name }}: {{ get_param_type(param, param.required) }} = Query({{ 'None' if not param.required else '...' }}, description="{{ param.description }}"),
    {% endif %}
    {% endfor %}
    {% if path_info.operation.get('requestBody') %}
    request_data: Dict[str, Any],
    {% endif %}
):
    \"\"\"
    {{ path_info.operation.summary }}
    
    {{ path_info.operation.description }}
    \"\"\"
    try:
        # TODO: Implement the actual logic for {{ path_info.operation.operationId }}
        # This is a placeholder implementation
        
        {% if path_info.method == 'get' %}
        # GET operation - return sample data
        return {
            "message": "{{ path_info.operation.operationId }} executed successfully",
            "data": {
                {% for param in path_info.operation.get('parameters', []) %}
                "{{ param.name }}": {{ param.name }},
                {% endfor %}
            }
        }
        {% else %}
        # {{ path_info.method.upper() }} operation - process and return result
        return {
            "message": "{{ path_info.operation.operationId }} executed successfully",
            {% if path_info.operation.get('requestBody') %}
            "processed_data": request_data,
            {% endif %}
            "result": "Operation completed"
        }
        {% endif %}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in {{ path_info.operation.operationId }}: {str(e)}")

{% endfor %}
""")
    
    def get_param_type(param, required=True):
        schema = param.get("schema", {})
        param_type = schema.get("type", "str")
        
        type_map = {
            "string": "str",
            "integer": "int", 
            "number": "float",
            "boolean": "bool"
        }
        
        python_type = type_map.get(param_type, "str")
        
        if not required:
            python_type = f"Optional[{python_type}]"
        
        return python_type
    
    return template.render(
        tag=tag,
        paths=paths,
        get_param_type=get_param_type
    )

def generate_requirements() -> str:
    """Generate requirements.txt for the API"""
    return """fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
"""

def generate_dockerfile() -> str:
    """Generate Dockerfile for the API"""
    return """FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

def generate_docker_compose() -> str:
    """Generate docker-compose.yml for the API"""
    return """version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=development
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""

def generate_readme(openapi_spec: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
    """Generate README.md for the API"""
    
    template = Template("""
# {{ title }}

{{ description }}

## Overview

This API was automatically generated from source code analysis using AI agents.

**Generated from:** {{ source_info }}
**API Version:** {{ version }}
**Generated on:** {{ timestamp }}

## Features

- 🚀 FastAPI-based REST API
- 📝 Automatic OpenAPI documentation
- 🔒 JWT authentication ready
- 🐳 Docker support
- 📊 Built-in health checks

## Quick Start

### Using Docker

```bash
docker-compose up --build
```

### Manual Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API:
```bash
uvicorn main:app --reload
```

3. Visit the documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

{% for path, methods in paths.items() %}
### `{{ path }}`
{% for method, operation in methods.items() %}
- **{{ method.upper() }}** - {{ operation.summary }}
{% endfor %}
{% endfor %}

## Authentication

This API uses JWT Bearer token authentication. Include your token in the Authorization header:

```
Authorization: Bearer YOUR_TOKEN_HERE
```

## Development

### Project Structure

```
.
├── main.py              # Main FastAPI application
├── models.py            # Pydantic models
├── routers/             # API route handlers
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose setup
└── README.md           # This file
```

### Generated Statistics

- **Total Endpoints:** {{ endpoints_count }}
- **Functions Analyzed:** {{ functions_analyzed }}
- **Classes Analyzed:** {{ classes_analyzed }}

## Security Recommendations

{% for recommendation in security_recommendations %}
- {{ recommendation }}
{% endfor %}

## License

MIT License - Feel free to use and modify as needed.

---

*This API was generated automatically by AI Code-to-API Generator*
""")
    
    from datetime import datetime
    
    return template.render(
        title=openapi_spec["info"]["title"],
        description=openapi_spec["info"]["description"],
        version=openapi_spec["info"]["version"],
        source_info=f"{analysis_result.get('functions_analyzed', 0)} functions from {analysis_result.get('language', 'unknown')} source code",
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        paths=openapi_spec.get("paths", {}),
        endpoints_count=len(openapi_spec.get("paths", {})),
        functions_analyzed=analysis_result.get("functions_analyzed", 0),
        classes_analyzed=analysis_result.get("classes_analyzed", 0),
        security_recommendations=analysis_result.get("security_recommendations", [])
    )
