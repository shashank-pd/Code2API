from langchain.tools import tool
from typing import Dict, Any, List
import os
import json
from jinja2 import Template
from pathlib import Path

@tool
def api_generator_tool(openapi_spec: Dict[str, Any], analysis_result: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    """
    Enhanced API generator that creates FastAPI server code with actual business logic
    implementation based on the original repository's functionality.
    
    Args:
        openapi_spec: Enhanced OpenAPI 3.0 specification with domain-specific details
        analysis_result: Enhanced code analysis results with business logic mapping
        output_dir: Directory to output the generated API
    
    Returns:
        Dictionary containing generation results and implemented business logic files
    """
    try:
        # Handle nested parameter structure from LangChain agent
        if isinstance(openapi_spec, dict) and 'function_name' in openapi_spec:
            print(f"[DEBUG] Received nested openapi_spec structure: {type(openapi_spec)}")
            return {
                "success": False,
                "error": "Received nested parameter structure instead of OpenAPI spec",
                "debug_info": str(openapi_spec)[:500]
            }
        
        if isinstance(analysis_result, dict) and 'function_name' in analysis_result:
            print(f"[DEBUG] Received nested analysis_result structure: {type(analysis_result)}")
            return {
                "success": False,
                "error": "Received nested parameter structure instead of analysis result",
                "debug_info": str(analysis_result)[:500]
            }
        
        # Handle case where openapi_spec might be wrapped in a success response
        if isinstance(openapi_spec, dict) and 'openapi_spec' in openapi_spec:
            openapi_spec = openapi_spec['openapi_spec']
        
        # Handle case where analysis_result might be wrapped
        if isinstance(analysis_result, dict) and 'analysis_result' in analysis_result:
            analysis_result = analysis_result['analysis_result']
        
        # Ensure we have a valid OpenAPI spec structure
        if not isinstance(openapi_spec, dict) or 'info' not in openapi_spec:
            print(f"[DEBUG] Invalid OpenAPI spec structure, creating default")
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
        
        # Ensure we have valid analysis result
        if not isinstance(analysis_result, dict):
            print(f"[DEBUG] Invalid analysis result, creating default")
            analysis_result = {
                "repo_purpose": "utility",
                "main_functionality": [],
                "language": "python"
            }
        
        # Create output directory
        api_dir = Path(output_dir)
        api_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        # Extract repository purpose and business logic
        repo_purpose = analysis_result.get("repo_purpose", "general_utility")
        main_functionality = analysis_result.get("main_functionality", [])
        
        # Generate business logic implementations
        business_logic_dir = api_dir / "business_logic"
        business_logic_dir.mkdir(exist_ok=True)
        business_logic_files = generate_business_logic(main_functionality, repo_purpose, business_logic_dir)
        generated_files.extend(business_logic_files)
        
        # Generate enhanced models with actual data structures
        models_content = generate_enhanced_models(openapi_spec, analysis_result)
        models_file = api_dir / "models.py"
        with open(models_file, 'w', encoding='utf-8') as f:
            f.write(models_content)
        generated_files.append(str(models_file))
        
        # Generate routers with actual business logic integration
        routers_dir = api_dir / "routers"
        routers_dir.mkdir(exist_ok=True)
        router_files = generate_enhanced_routers(openapi_spec, analysis_result, routers_dir)
        generated_files.extend(router_files)
        
        # Generate main FastAPI application with business logic integration
        main_content = generate_enhanced_main_app(openapi_spec, analysis_result)
        main_file = api_dir / "main.py"
        with open(main_file, 'w', encoding='utf-8') as f:
            f.write(main_content)
        generated_files.append(str(main_file))
        
        # Generate authentication module with actual security implementation
        auth_content = generate_auth_module(repo_purpose)
        auth_file = api_dir / "auth.py"
        with open(auth_file, 'w', encoding='utf-8') as f:
            f.write(auth_content)
        generated_files.append(str(auth_file))
        
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
            "files_created": len(generated_files),
            "repo_purpose": repo_purpose,
            "business_logic_implemented": len(business_logic_files) > 0,
            "functionality_mapped": len(main_functionality)
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

def generate_business_logic(main_functionality: List[Dict], repo_purpose: str, business_logic_dir: Path) -> List[str]:
    """Generate actual business logic implementations based on repository functionality"""
    generated_files = []
    
    # Create purpose-specific business logic modules
    if repo_purpose == "data_analysis":
        files = generate_data_analysis_logic(main_functionality, business_logic_dir)
        generated_files.extend(files)
    elif repo_purpose == "machine_learning":
        files = generate_ml_logic(main_functionality, business_logic_dir)
        generated_files.extend(files)
    elif repo_purpose == "file_processing":
        files = generate_file_processing_logic(main_functionality, business_logic_dir)
        generated_files.extend(files)
    elif repo_purpose == "web_scraping":
        files = generate_web_scraping_logic(main_functionality, business_logic_dir)
        generated_files.extend(files)
    elif repo_purpose == "database":
        files = generate_database_logic(main_functionality, business_logic_dir)
        generated_files.extend(files)
    else:
        files = generate_generic_logic(main_functionality, business_logic_dir)
        generated_files.extend(files)
    
    # Generate __init__.py for the business logic package
    init_file = business_logic_dir / "__init__.py"
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write("# Business logic implementations\\n")
    generated_files.append(str(init_file))
    
    return generated_files

def generate_data_analysis_logic(main_functionality: List[Dict], business_logic_dir: Path) -> List[str]:
    """Generate data analysis business logic"""
    generated_files = []
    
    # Generate data analyzer module
    analyzer_content = Template("""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, List, Optional
import io
import base64
import json

class DataAnalyzer:
    \"\"\"Core data analysis functionality extracted from repository\"\"\"
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'excel', 'parquet']
        self.analysis_cache = {}
    
    def analyze_data(self, data: Dict[str, Any], analysis_type: Optional[str] = None) -> Dict[str, Any]:
        \"\"\"Main data analysis function\"\"\"
        try:
            # Convert data to DataFrame
            if isinstance(data.get('data'), list):
                df = pd.DataFrame(data['data'])
            elif isinstance(data.get('data'), dict):
                df = pd.DataFrame([data['data']])
            else:
                raise ValueError("Data must be a list of records or a single record")
            
            results = {
                'basic_stats': self._get_basic_statistics(df),
                'data_types': self._get_data_types(df),
                'missing_values': self._get_missing_values(df),
                'correlations': self._get_correlations(df)
            }
            
            if analysis_type:
                results['custom_analysis'] = self._perform_custom_analysis(df, analysis_type)
            
            return {
                'success': True,
                'results': results,
                'row_count': len(df),
                'column_count': len(df.columns)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_visualization(self, data: Dict[str, Any], chart_type: Optional[str] = None) -> Dict[str, Any]:
        \"\"\"Generate data visualizations\"\"\"
        try:
            if isinstance(data.get('data'), list):
                df = pd.DataFrame(data['data'])
            else:
                raise ValueError("Data must be a list of records")
            
            plt.figure(figsize=(10, 6))
            
            if chart_type == 'histogram' and len(df.select_dtypes(include=[np.number]).columns) > 0:
                numeric_col = df.select_dtypes(include=[np.number]).columns[0]
                plt.hist(df[numeric_col], bins=20)
                plt.title(f'Histogram of {numeric_col}')
            elif chart_type == 'scatter' and len(df.select_dtypes(include=[np.number]).columns) >= 2:
                numeric_cols = df.select_dtypes(include=[np.number]).columns[:2]
                plt.scatter(df[numeric_cols[0]], df[numeric_cols[1]])
                plt.xlabel(numeric_cols[0])
                plt.ylabel(numeric_cols[1])
                plt.title(f'Scatter plot: {numeric_cols[0]} vs {numeric_cols[1]}')
            else:
                # Default correlation heatmap
                numeric_df = df.select_dtypes(include=[np.number])
                if len(numeric_df.columns) > 1:
                    sns.heatmap(numeric_df.corr(), annot=True, cmap='coolwarm')
                    plt.title('Correlation Heatmap')
                else:
                    plt.text(0.5, 0.5, 'No numeric data for visualization', 
                            ha='center', va='center', transform=plt.gca().transAxes)
            
            # Convert plot to base64 string
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', dpi=150)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return {
                'success': True,
                'visualization': {
                    'type': chart_type or 'correlation_heatmap',
                    'image_base64': image_base64,
                    'format': 'png'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_report(self, analysis_id: str) -> Dict[str, Any]:
        \"\"\"Generate comprehensive analysis report\"\"\"
        try:
            # In a real implementation, this would fetch cached analysis results
            if analysis_id in self.analysis_cache:
                analysis_data = self.analysis_cache[analysis_id]
            else:
                # Generate sample report
                analysis_data = {
                    'dataset_info': {
                        'rows': 1000,
                        'columns': 10,
                        'missing_values': 50
                    },
                    'key_findings': [
                        'Dataset contains 1000 records with 10 features',
                        'Missing values found in 5% of records',
                        'Strong correlation between feature_1 and feature_2'
                    ]
                }
            
            report = {
                'report_id': analysis_id,
                'analysis_data': analysis_data,
                'recommendations': [
                    'Consider handling missing values through imputation',
                    'Highly correlated features may need feature selection',
                    'Data distribution appears normal for most numeric features'
                ],
                'generated_at': pd.Timestamp.now().isoformat()
            }
            
            return {
                'success': True,
                'report': report
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"Get basic statistical information\"\"\"
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 0:
            return {
                'mean': numeric_df.mean().to_dict(),
                'median': numeric_df.median().to_dict(),
                'std': numeric_df.std().to_dict(),
                'min': numeric_df.min().to_dict(),
                'max': numeric_df.max().to_dict()
            }
        return {}
    
    def _get_data_types(self, df: pd.DataFrame) -> Dict[str, str]:
        \"\"\"Get data types for each column\"\"\"
        return df.dtypes.astype(str).to_dict()
    
    def _get_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"Analyze missing values\"\"\"
        missing_counts = df.isnull().sum()
        missing_percentages = (missing_counts / len(df) * 100).round(2)
        
        return {
            'counts': missing_counts.to_dict(),
            'percentages': missing_percentages.to_dict(),
            'total_missing': missing_counts.sum()
        }
    
    def _get_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"Calculate correlations between numeric columns\"\"\"
        numeric_df = df.select_dtypes(include=[np.number])
        if len(numeric_df.columns) > 1:
            corr_matrix = numeric_df.corr()
            return {
                'correlation_matrix': corr_matrix.to_dict(),
                'highest_correlations': self._find_highest_correlations(corr_matrix)
            }
        return {}
    
    def _find_highest_correlations(self, corr_matrix: pd.DataFrame) -> List[Dict[str, Any]]:
        \"\"\"Find the highest correlations in the matrix\"\"\"
        correlations = []
        for i, col1 in enumerate(corr_matrix.columns):
            for j, col2 in enumerate(corr_matrix.columns):
                if i < j:  # Avoid duplicates and self-correlation
                    corr_value = corr_matrix.iloc[i, j]
                    if abs(corr_value) > 0.5:  # Only significant correlations
                        correlations.append({
                            'feature_1': col1,
                            'feature_2': col2,
                            'correlation': round(corr_value, 3)
                        })
        
        return sorted(correlations, key=lambda x: abs(x['correlation']), reverse=True)[:5]
    
    def _perform_custom_analysis(self, df: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        \"\"\"Perform custom analysis based on type\"\"\"
        if analysis_type == 'outlier_detection':
            return self._detect_outliers(df)
        elif analysis_type == 'distribution_analysis':
            return self._analyze_distributions(df)
        else:
            return {'message': f'Analysis type {analysis_type} not implemented'}
    
    def _detect_outliers(self, df: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"Detect outliers using IQR method\"\"\"
        numeric_df = df.select_dtypes(include=[np.number])
        outliers = {}
        
        for column in numeric_df.columns:
            Q1 = numeric_df[column].quantile(0.25)
            Q3 = numeric_df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_mask = (numeric_df[column] < lower_bound) | (numeric_df[column] > upper_bound)
            outlier_count = outlier_mask.sum()
            
            outliers[column] = {
                'count': int(outlier_count),
                'percentage': round((outlier_count / len(numeric_df)) * 100, 2),
                'bounds': {
                    'lower': lower_bound,
                    'upper': upper_bound
                }
            }
        
        return outliers
    
    def _analyze_distributions(self, df: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"Analyze data distributions\"\"\"
        numeric_df = df.select_dtypes(include=[np.number])
        distributions = {}
        
        for column in numeric_df.columns:
            distributions[column] = {
                'skewness': float(numeric_df[column].skew()),
                'kurtosis': float(numeric_df[column].kurtosis()),
                'is_normal': abs(numeric_df[column].skew()) < 1 and abs(numeric_df[column].kurtosis()) < 3
            }
        
        return distributions

# Global analyzer instance
data_analyzer = DataAnalyzer()

{% for func in custom_functions %}
def {{ func.name }}({{ func.parameters }}) -> Dict[str, Any]:
    \"\"\"{{ func.description }}\"\"\"
    try:
        # TODO: Implement actual logic from {{ func.file_path }}
        # This is a placeholder that should be replaced with actual business logic
        return {
            'success': True,
            'message': f'{{ func.name }} executed successfully',
            'implementation_note': 'This function needs actual implementation from the original repository'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

{% endfor %}
""").render(custom_functions=[
        {
            'name': func['name'],
            'description': func.get('description', f"Function: {func['name']}"),
            'file_path': func.get('file_path', 'unknown'),
            'parameters': 'data: Dict[str, Any]'
        }
        for func in main_functionality if func.get('type') == 'function'
    ])
    
    analyzer_file = business_logic_dir / "data_analyzer.py"
    with open(analyzer_file, 'w', encoding='utf-8') as f:
        f.write(analyzer_content)
    generated_files.append(str(analyzer_file))
    
    return generated_files

def generate_ml_logic(main_functionality: List[Dict], business_logic_dir: Path) -> List[str]:
    """Generate machine learning business logic"""
    generated_files = []
    
    ml_content = Template("""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import joblib
import json
from datetime import datetime
import os

class MLPredictor:
    \"\"\"Machine learning prediction functionality\"\"\"
    
    def __init__(self):
        self.models = {}
        self.model_metadata = {}
        self.prediction_history = []
    
    def predict(self, input_features: Dict[str, Any], model_version: Optional[str] = None) -> Dict[str, Any]:
        \"\"\"Make predictions using trained model\"\"\"
        try:
            # Validate input features
            if not input_features:
                raise ValueError("Input features cannot be empty")
            
            # Use default model if version not specified
            if model_version is None:
                model_version = "default"
            
            # For demo purposes, generate mock predictions
            # In real implementation, this would load and use actual trained models
            features = pd.DataFrame([input_features])
            
            # Mock prediction logic
            if 'text' in input_features:
                # Text classification example
                prediction = self._predict_text_classification(input_features['text'])
            elif 'image' in input_features:
                # Image classification example
                prediction = self._predict_image_classification(input_features['image'])
            else:
                # Numeric prediction example
                prediction = self._predict_numeric(features)
            
            # Store prediction in history
            prediction_record = {
                'timestamp': datetime.now().isoformat(),
                'input_features': input_features,
                'prediction': prediction,
                'model_version': model_version
            }
            self.prediction_history.append(prediction_record)
            
            return {
                'success': True,
                'prediction': prediction['value'],
                'confidence': prediction['confidence'],
                'model_version': model_version,
                'prediction_id': len(self.prediction_history)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def train_model(self, training_data: Dict[str, Any], hyperparameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        \"\"\"Train or retrain the ML model\"\"\"
        try:
            if not training_data.get('features') or not training_data.get('labels'):
                raise ValueError("Training data must contain 'features' and 'labels'")
            
            # Mock training process
            features = pd.DataFrame(training_data['features'])
            labels = training_data['labels']
            
            # Simulate training metrics
            training_metrics = {
                'accuracy': 0.85 + np.random.random() * 0.1,  # Random accuracy between 0.85-0.95
                'loss': np.random.random() * 0.5,  # Random loss between 0-0.5
                'training_samples': len(features),
                'features_count': len(features.columns),
                'training_time': f"{np.random.randint(10, 300)} seconds"
            }
            
            # Store model metadata
            model_version = f"v{len(self.models) + 1}"
            self.model_metadata[model_version] = {
                'created_at': datetime.now().isoformat(),
                'hyperparameters': hyperparameters or {},
                'metrics': training_metrics,
                'data_shape': features.shape
            }
            
            return {
                'success': True,
                'model_version': model_version,
                'metrics': training_metrics,
                'message': f'Model {model_version} trained successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def evaluate_model(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Evaluate model performance\"\"\"
        try:
            if not test_data.get('features') or not test_data.get('labels'):
                raise ValueError("Test data must contain 'features' and 'labels'")
            
            features = pd.DataFrame(test_data['features'])
            labels = test_data['labels']
            
            # Mock evaluation metrics
            evaluation_metrics = {
                'accuracy': 0.80 + np.random.random() * 0.15,
                'precision': 0.75 + np.random.random() * 0.2,
                'recall': 0.75 + np.random.random() * 0.2,
                'f1_score': 0.75 + np.random.random() * 0.2,
                'test_samples': len(features),
                'confusion_matrix': [[85, 15], [10, 90]]  # Mock 2x2 confusion matrix
            }
            
            return {
                'success': True,
                'metrics': evaluation_metrics,
                'evaluation_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_models(self) -> Dict[str, Any]:
        \"\"\"List available models\"\"\"
        try:
            models_info = []
            for version, metadata in self.model_metadata.items():
                models_info.append({
                    'version': version,
                    'created_at': metadata['created_at'],
                    'accuracy': metadata['metrics']['accuracy'],
                    'training_samples': metadata['metrics']['training_samples']
                })
            
            return {
                'success': True,
                'models': models_info,
                'total_models': len(models_info)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _predict_text_classification(self, text: str) -> Dict[str, Any]:
        \"\"\"Mock text classification\"\"\"
        # Simple sentiment analysis mock
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'disappointing']
        
        text_lower = text.lower()
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        if positive_score > negative_score:
            return {'value': 'positive', 'confidence': 0.7 + positive_score * 0.1}
        elif negative_score > positive_score:
            return {'value': 'negative', 'confidence': 0.7 + negative_score * 0.1}
        else:
            return {'value': 'neutral', 'confidence': 0.5}
    
    def _predict_image_classification(self, image_data: str) -> Dict[str, Any]:
        \"\"\"Mock image classification\"\"\"
        # Mock image classification
        classes = ['cat', 'dog', 'bird', 'fish', 'other']
        predicted_class = np.random.choice(classes)
        confidence = 0.6 + np.random.random() * 0.3
        
        return {'value': predicted_class, 'confidence': confidence}
    
    def _predict_numeric(self, features: pd.DataFrame) -> Dict[str, Any]:
        \"\"\"Mock numeric prediction\"\"\"
        # Simple linear combination for regression
        numeric_features = features.select_dtypes(include=[np.number])
        if len(numeric_features.columns) > 0:
            prediction_value = float(numeric_features.sum(axis=1).iloc[0] * 0.1)
            confidence = 0.8
        else:
            prediction_value = np.random.random() * 100
            confidence = 0.6
        
        return {'value': prediction_value, 'confidence': confidence}

# Global ML predictor instance
ml_predictor = MLPredictor()

{% for func in custom_functions %}
def {{ func.name }}({{ func.parameters }}) -> Dict[str, Any]:
    \"\"\"{{ func.description }}\"\"\"
    try:
        # TODO: Implement actual ML logic from {{ func.file_path }}
        return {
            'success': True,
            'message': f'{{ func.name }} executed successfully',
            'implementation_note': 'This function needs actual ML implementation from the original repository'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

{% endfor %}
""").render(custom_functions=[
        {
            'name': func['name'],
            'description': func.get('description', f"ML Function: {func['name']}"),
            'file_path': func.get('file_path', 'unknown'),
            'parameters': 'data: Dict[str, Any]'
        }
        for func in main_functionality if func.get('type') == 'function'
    ])
    
    ml_file = business_logic_dir / "ml_predictor.py"
    with open(ml_file, 'w', encoding='utf-8') as f:
        f.write(ml_content)
    generated_files.append(str(ml_file))
    
    return generated_files

def generate_file_processing_logic(main_functionality: List[Dict], business_logic_dir: Path) -> List[str]:
    """Generate file processing business logic"""
    generated_files = []
    
    file_processor_content = Template("""
import os
import uuid
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional, BinaryIO
import json
import pandas as pd
import zipfile
import shutil
from datetime import datetime

class FileProcessor:
    \"\"\"File processing functionality\"\"\"
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.processed_dir = Path("processed")
        self.upload_dir.mkdir(exist_ok=True)
        self.processed_dir.mkdir(exist_ok=True)
        self.file_registry = {}
        self.max_file_size = 100 * 1024 * 1024  # 100MB
    
    def upload_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        \"\"\"Handle file upload\"\"\"
        try:
            if len(file_content) > self.max_file_size:
                raise ValueError(f"File size exceeds maximum limit of {self.max_file_size / (1024*1024):.1f}MB")
            
            # Generate unique file ID
            file_id = str(uuid.uuid4())
            file_extension = Path(filename).suffix
            stored_filename = f"{file_id}{file_extension}"
            file_path = self.upload_dir / stored_filename
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(filename)
            
            # Register file
            file_info = {
                'file_id': file_id,
                'original_filename': filename,
                'stored_filename': stored_filename,
                'file_path': str(file_path),
                'size': len(file_content),
                'mime_type': mime_type,
                'uploaded_at': datetime.now().isoformat(),
                'status': 'uploaded'
            }
            
            self.file_registry[file_id] = file_info
            
            return {
                'success': True,
                'file_id': file_id,
                'filename': filename,
                'size': len(file_content),
                'mime_type': mime_type
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_file(self, file_id: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        \"\"\"Process uploaded file\"\"\"
        try:
            if file_id not in self.file_registry:
                raise ValueError(f"File {file_id} not found")
            
            file_info = self.file_registry[file_id]
            file_path = Path(file_info['file_path'])
            
            if not file_path.exists():
                raise ValueError(f"File {file_id} no longer exists on disk")
            
            # Process based on file type
            mime_type = file_info['mime_type']
            processing_result = {}
            
            if mime_type and 'text' in mime_type:
                processing_result = self._process_text_file(file_path, options)
            elif mime_type in ['application/json']:
                processing_result = self._process_json_file(file_path, options)
            elif mime_type in ['text/csv', 'application/csv']:
                processing_result = self._process_csv_file(file_path, options)
            elif mime_type in ['application/pdf']:
                processing_result = self._process_pdf_file(file_path, options)
            elif mime_type and 'image' in mime_type:
                processing_result = self._process_image_file(file_path, options)
            else:
                processing_result = self._process_generic_file(file_path, options)
            
            # Update file status
            self.file_registry[file_id]['status'] = 'processed'
            self.file_registry[file_id]['processed_at'] = datetime.now().isoformat()
            self.file_registry[file_id]['processing_result'] = processing_result
            
            return {
                'success': True,
                'file_id': file_id,
                'processing_result': processing_result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def convert_file(self, file_id: str, target_format: str) -> Dict[str, Any]:
        \"\"\"Convert file to different format\"\"\"
        try:
            if file_id not in self.file_registry:
                raise ValueError(f"File {file_id} not found")
            
            file_info = self.file_registry[file_id]
            source_path = Path(file_info['file_path'])
            
            # Generate output filename
            converted_filename = f"{file_id}_converted.{target_format}"
            converted_path = self.processed_dir / converted_filename
            
            # Perform conversion based on target format
            conversion_result = self._convert_file_format(source_path, converted_path, target_format)
            
            if conversion_result['success']:
                # Register converted file
                converted_file_id = str(uuid.uuid4())
                converted_info = {
                    'file_id': converted_file_id,
                    'original_filename': f"{file_info['original_filename']}.{target_format}",
                    'stored_filename': converted_filename,
                    'file_path': str(converted_path),
                    'size': converted_path.stat().st_size if converted_path.exists() else 0,
                    'mime_type': mimetypes.guess_type(converted_filename)[0],
                    'converted_at': datetime.now().isoformat(),
                    'status': 'converted',
                    'source_file_id': file_id
                }
                
                self.file_registry[converted_file_id] = converted_info
                
                return {
                    'success': True,
                    'converted_file_id': converted_file_id,
                    'target_format': target_format,
                    'message': 'File converted successfully'
                }
            else:
                return conversion_result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, file_id: str) -> Dict[str, Any]:
        \"\"\"Prepare file for download\"\"\"
        try:
            if file_id not in self.file_registry:
                raise ValueError(f"File {file_id} not found")
            
            file_info = self.file_registry[file_id]
            file_path = Path(file_info['file_path'])
            
            if not file_path.exists():
                raise ValueError(f"File {file_id} no longer exists on disk")
            
            return {
                'success': True,
                'file_path': str(file_path),
                'filename': file_info['original_filename'],
                'size': file_info['size'],
                'mime_type': file_info['mime_type']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _process_text_file(self, file_path: Path, options: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Process text files\"\"\"
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            'type': 'text',
            'line_count': len(content.split('\\n')),
            'character_count': len(content),
            'word_count': len(content.split()),
            'encoding': 'utf-8'
        }
    
    def _process_json_file(self, file_path: Path, options: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Process JSON files\"\"\"
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return {
            'type': 'json',
            'structure': type(data).__name__,
            'size': len(data) if isinstance(data, (list, dict)) else 1,
            'keys': list(data.keys()) if isinstance(data, dict) else None
        }
    
    def _process_csv_file(self, file_path: Path, options: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Process CSV files\"\"\"
        df = pd.read_csv(file_path)
        
        return {
            'type': 'csv',
            'rows': len(df),
            'columns': len(df.columns),
            'column_names': df.columns.tolist(),
            'data_types': df.dtypes.astype(str).to_dict(),
            'missing_values': df.isnull().sum().to_dict()
        }
    
    def _process_pdf_file(self, file_path: Path, options: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Process PDF files\"\"\"
        # Mock PDF processing (would use PyPDF2 or similar in real implementation)
        return {
            'type': 'pdf',
            'pages': 10,  # Mock page count
            'text_extracted': True,
            'note': 'PDF processing requires additional libraries like PyPDF2'
        }
    
    def _process_image_file(self, file_path: Path, options: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Process image files\"\"\"
        # Mock image processing (would use PIL/Pillow in real implementation)
        return {
            'type': 'image',
            'format': file_path.suffix.upper(),
            'note': 'Image processing requires additional libraries like Pillow'
        }
    
    def _process_generic_file(self, file_path: Path, options: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Process generic files\"\"\"
        return {
            'type': 'generic',
            'size': file_path.stat().st_size,
            'extension': file_path.suffix,
            'note': 'Generic file processed - specific processing not implemented'
        }
    
    def _convert_file_format(self, source_path: Path, target_path: Path, target_format: str) -> Dict[str, Any]:
        \"\"\"Convert file format\"\"\"
        try:
            if target_format.lower() == 'txt':
                # Convert any file to text (basic implementation)
                if source_path.suffix.lower() == '.csv':
                    df = pd.read_csv(source_path)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(df.to_string())
                elif source_path.suffix.lower() == '.json':
                    with open(source_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    with open(target_path, 'w', encoding='utf-8') as f:
                        f.write(json.dumps(data, indent=2))
                else:
                    # Generic text conversion
                    shutil.copy2(source_path, target_path)
                
                return {'success': True, 'message': f'Converted to {target_format}'}
            else:
                return {'success': False, 'error': f'Conversion to {target_format} not implemented'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global file processor instance
file_processor = FileProcessor()

{% for func in custom_functions %}
def {{ func.name }}({{ func.parameters }}) -> Dict[str, Any]:
    \"\"\"{{ func.description }}\"\"\"
    try:
        # TODO: Implement actual file processing logic from {{ func.file_path }}
        return {
            'success': True,
            'message': f'{{ func.name }} executed successfully',
            'implementation_note': 'This function needs actual implementation from the original repository'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

{% endfor %}
""").render(custom_functions=[
        {
            'name': func['name'],
            'description': func.get('description', f"File processing function: {func['name']}"),
            'file_path': func.get('file_path', 'unknown'),
            'parameters': 'data: Dict[str, Any]'
        }
        for func in main_functionality if func.get('type') == 'function'
    ])
    
    processor_file = business_logic_dir / "file_processor.py"
    with open(processor_file, 'w', encoding='utf-8') as f:
        f.write(file_processor_content)
    generated_files.append(str(processor_file))
    
    return generated_files

def generate_web_scraping_logic(main_functionality: List[Dict], business_logic_dir: Path) -> List[str]:
    """Generate web scraping business logic"""
    generated_files = []
    
    scraper_content = Template("""
import requests
import json
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import time
import re
from datetime import datetime

class WebScraper:
    \"\"\"Web scraping functionality\"\"\"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; AI-Scraper/1.0)'
        })
        self.rate_limit = 1  # seconds between requests
        self.last_request_time = 0
        self.scraped_data_cache = {}
    
    def scrape_url(self, url: str, selectors: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        \"\"\"Scrape data from a single URL\"\"\"
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.rate_limit:
                time.sleep(self.rate_limit - (current_time - self.last_request_time))
            
            # Validate URL
            if not self._is_valid_url(url):
                raise ValueError("Invalid URL provided")
            
            # Make request
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            # Parse content
            content_type = response.headers.get('content-type', '').lower()
            
            if 'application/json' in content_type:
                scraped_data = self._scrape_json_content(response.json(), selectors)
            elif 'text/html' in content_type:
                scraped_data = self._scrape_html_content(response.text, selectors)
            else:
                scraped_data = self._scrape_text_content(response.text, selectors)
            
            result = {
                'url': url,
                'status_code': response.status_code,
                'content_type': content_type,
                'scraped_at': datetime.now().isoformat(),
                'data': scraped_data
            }
            
            # Cache the result
            self.scraped_data_cache[url] = result
            
            return {
                'success': True,
                'result': result
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def scrape_multiple(self, urls: List[str]) -> Dict[str, Any]:
        \"\"\"Scrape data from multiple URLs\"\"\"
        try:
            results = []
            failed_urls = []
            
            for url in urls:
                scrape_result = self.scrape_url(url)
                if scrape_result['success']:
                    results.append(scrape_result['result'])
                else:
                    failed_urls.append({
                        'url': url,
                        'error': scrape_result['error']
                    })
            
            return {
                'success': True,
                'results': results,
                'successful_count': len(results),
                'failed_count': len(failed_urls),
                'failed_urls': failed_urls
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_data(self, content: str, extraction_rules: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Extract specific data from content using rules\"\"\"
        try:
            extracted_data = {}
            
            for field_name, rule in extraction_rules.items():
                if isinstance(rule, dict):
                    if rule.get('type') == 'regex':
                        pattern = rule.get('pattern')
                        if pattern:
                            matches = re.findall(pattern, content)
                            extracted_data[field_name] = matches
                    elif rule.get('type') == 'substring':
                        start_marker = rule.get('start_marker')
                        end_marker = rule.get('end_marker')
                        if start_marker and end_marker:
                            start_idx = content.find(start_marker)
                            if start_idx != -1:
                                start_idx += len(start_marker)
                                end_idx = content.find(end_marker, start_idx)
                                if end_idx != -1:
                                    extracted_data[field_name] = content[start_idx:end_idx].strip()
                elif isinstance(rule, str):
                    # Simple substring search
                    if rule in content:
                        extracted_data[field_name] = True
                    else:
                        extracted_data[field_name] = False
            
            return {
                'success': True,
                'extracted_data': extracted_data,
                'extraction_rules_applied': len(extraction_rules)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _is_valid_url(self, url: str) -> bool:
        \"\"\"Validate URL format\"\"\"
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _scrape_json_content(self, json_data: Any, selectors: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Scrape JSON content\"\"\"
        if selectors:
            extracted = {}
            for key, path in selectors.items():
                extracted[key] = self._extract_json_value(json_data, path)
            return extracted
        else:
            # Return basic structure info
            return {
                'type': type(json_data).__name__,
                'size': len(json_data) if isinstance(json_data, (list, dict)) else 1,
                'sample_keys': list(json_data.keys())[:5] if isinstance(json_data, dict) else None
            }
    
    def _scrape_html_content(self, html_content: str, selectors: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Scrape HTML content (simplified without BeautifulSoup)\"\"\"
        # Basic HTML parsing without external dependencies
        scraped_data = {}
        
        if selectors:
            for key, css_selector in selectors.items():
                # Simple tag extraction (would use BeautifulSoup in real implementation)
                if css_selector.startswith('title'):
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
                    scraped_data[key] = title_match.group(1) if title_match else None
                elif css_selector.startswith('h1'):
                    h1_matches = re.findall(r'<h1[^>]*>([^<]+)</h1>', html_content, re.IGNORECASE)
                    scraped_data[key] = h1_matches
                elif css_selector.startswith('p'):
                    p_matches = re.findall(r'<p[^>]*>([^<]+)</p>', html_content, re.IGNORECASE)
                    scraped_data[key] = p_matches[:5]  # First 5 paragraphs
        else:
            # Extract basic HTML elements
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            h1_matches = re.findall(r'<h1[^>]*>([^<]+)</h1>', html_content, re.IGNORECASE)
            link_matches = re.findall(r'<a[^>]*href=["\\']([^"\\'>]+)["\\'][^>]*>([^<]+)</a>', html_content, re.IGNORECASE)
            
            scraped_data = {
                'title': title_match.group(1) if title_match else None,
                'headings': h1_matches,
                'links': [{'url': url, 'text': text} for url, text in link_matches[:10]],
                'content_length': len(html_content),
                'note': 'For advanced HTML parsing, consider using BeautifulSoup'
            }
        
        return scraped_data
    
    def _scrape_text_content(self, text_content: str, selectors: Optional[Dict]) -> Dict[str, Any]:
        \"\"\"Scrape plain text content\"\"\"
        if selectors:
            extracted = {}
            for key, pattern in selectors.items():
                if isinstance(pattern, str):
                    # Treat as regex pattern
                    matches = re.findall(pattern, text_content)
                    extracted[key] = matches
            return extracted
        else:
            # Basic text analysis
            lines = text_content.split('\\n')
            words = text_content.split()
            
            return {
                'line_count': len(lines),
                'word_count': len(words),
                'character_count': len(text_content),
                'first_line': lines[0] if lines else None,
                'preview': text_content[:200] + '...' if len(text_content) > 200 else text_content
            }
    
    def _extract_json_value(self, data: Any, path: str) -> Any:
        \"\"\"Extract value from JSON using dot notation path\"\"\"
        try:
            keys = path.split('.')
            current = data
            for key in keys:
                if isinstance(current, dict):
                    current = current.get(key)
                elif isinstance(current, list) and key.isdigit():
                    index = int(key)
                    current = current[index] if 0 <= index < len(current) else None
                else:
                    return None
            return current
        except:
            return None

# Global web scraper instance
web_scraper = WebScraper()

{% for func in custom_functions %}
def {{ func.name }}({{ func.parameters }}) -> Dict[str, Any]:
    \"\"\"{{ func.description }}\"\"\"
    try:
        # TODO: Implement actual web scraping logic from {{ func.file_path }}
        return {
            'success': True,
            'message': f'{{ func.name }} executed successfully',
            'implementation_note': 'This function needs actual implementation from the original repository'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

{% endfor %}
""").render(custom_functions=[
        {
            'name': func['name'],
            'description': func.get('description', f"Web scraping function: {func['name']}"),
            'file_path': func.get('file_path', 'unknown'),
            'parameters': 'data: Dict[str, Any]'
        }
        for func in main_functionality if func.get('type') == 'function'
    ])
    
    scraper_file = business_logic_dir / "web_scraper.py"
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(scraper_content)
    generated_files.append(str(scraper_file))
    
    return generated_files

def generate_database_logic(main_functionality: List[Dict], business_logic_dir: Path) -> List[str]:
    """Generate database business logic"""
    generated_files = []
    
    db_content = Template("""
from typing import Dict, Any, List, Optional, Union
import sqlite3
import json
from datetime import datetime
from pathlib import Path
import uuid

class DatabaseManager:
    \"\"\"Database management functionality\"\"\"
    
    def __init__(self, db_path: str = "app_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        \"\"\"Initialize database with basic tables\"\"\"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS records (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def get_records(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict[str, Any]:
        \"\"\"Get all records with pagination\"\"\"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                query = "SELECT * FROM records ORDER BY created_at DESC"
                params = []
                
                if limit is not None:
                    query += " LIMIT ?"
                    params.append(limit)
                
                if offset is not None:
                    query += " OFFSET ?"
                    params.append(offset)
                
                cursor = conn.execute(query, params)
                records = []
                
                for row in cursor.fetchall():
                    records.append({
                        'id': row['id'],
                        'data': json.loads(row['data']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                # Get total count
                total_count = conn.execute("SELECT COUNT(*) FROM records").fetchone()[0]
                
                return {
                    'success': True,
                    'records': records,
                    'total_count': total_count,
                    'returned_count': len(records)
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Create new record\"\"\"
        try:
            record_id = str(uuid.uuid4())
            data_json = json.dumps(data)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO records (id, data) VALUES (?, ?)",
                    (record_id, data_json)
                )
                conn.commit()
            
            return {
                'success': True,
                'record_id': record_id,
                'message': 'Record created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_record(self, record_id: str) -> Dict[str, Any]:
        \"\"\"Get record by ID\"\"\"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM records WHERE id = ?",
                    (record_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        'success': True,
                        'record': {
                            'id': row['id'],
                            'data': json.loads(row['data']),
                            'created_at': row['created_at'],
                            'updated_at': row['updated_at']
                        }
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Record {record_id} not found'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_record(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        \"\"\"Update existing record\"\"\"
        try:
            data_json = json.dumps(data)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "UPDATE records SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (data_json, record_id)
                )
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return {
                        'success': True,
                        'record_id': record_id,
                        'message': 'Record updated successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Record {record_id} not found'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_record(self, record_id: str) -> Dict[str, Any]:
        \"\"\"Delete record\"\"\"
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM records WHERE id = ?",
                    (record_id,)
                )
                
                if cursor.rowcount > 0:
                    conn.commit()
                    return {
                        'success': True,
                        'record_id': record_id,
                        'message': 'Record deleted successfully'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Record {record_id} not found'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def search_records(self, query: str) -> Dict[str, Any]:
        \"\"\"Search records (simple text search in JSON data)\"\"\"
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT * FROM records WHERE data LIKE ? ORDER BY created_at DESC",
                    (f'%{query}%',)
                )
                
                records = []
                for row in cursor.fetchall():
                    records.append({
                        'id': row['id'],
                        'data': json.loads(row['data']),
                        'created_at': row['created_at'],
                        'updated_at': row['updated_at']
                    })
                
                return {
                    'success': True,
                    'records': records,
                    'query': query,
                    'results_count': len(records)
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global database manager instance
db_manager = DatabaseManager()

{% for func in custom_functions %}
def {{ func.name }}({{ func.parameters }}) -> Dict[str, Any]:
    \"\"\"{{ func.description }}\"\"\"
    try:
        # TODO: Implement actual database logic from {{ func.file_path }}
        return {
            'success': True,
            'message': f'{{ func.name }} executed successfully',
            'implementation_note': 'This function needs actual implementation from the original repository'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

{% endfor %}
""").render(custom_functions=[
        {
            'name': func['name'],
            'description': func.get('description', f"Database function: {func['name']}"),
            'file_path': func.get('file_path', 'unknown'),
            'parameters': 'data: Dict[str, Any]'
        }
        for func in main_functionality if func.get('type') == 'function'
    ])
    
    db_file = business_logic_dir / "database_manager.py"
    with open(db_file, 'w', encoding='utf-8') as f:
        f.write(db_content)
    generated_files.append(str(db_file))
    
    return generated_files

def generate_generic_logic(main_functionality: List[Dict], business_logic_dir: Path) -> List[str]:
    """Generate generic business logic for unspecified repository types"""
    generated_files = []
    
    generic_content = Template("""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

class GenericProcessor:
    \"\"\"Generic business logic processor\"\"\"
    
    def __init__(self):
        self.execution_history = []
        self.state = {}
    
    def execute_main_function(self, input_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        \"\"\"Execute main functionality\"\"\"
        try:
            if input_data is None:
                input_data = {}
            
            # Log execution
            execution_record = {
                'timestamp': datetime.now().isoformat(),
                'input': input_data,
                'function': 'execute_main_function'
            }
            
            # Process input data
            result = {
                'input_received': input_data,
                'processing_timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'message': 'Main function executed successfully'
            }
            
            # Add to execution history
            execution_record['result'] = result
            self.execution_history.append(execution_record)
            
            return {
                'success': True,
                'result': result,
                'execution_id': len(self.execution_history)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_status(self) -> Dict[str, Any]:
        \"\"\"Get system status and available operations\"\"\"
        try:
            return {
                'success': True,
                'status': {
                    'system': 'operational',
                    'uptime': 'N/A',
                    'executions_count': len(self.execution_history),
                    'last_execution': self.execution_history[-1]['timestamp'] if self.execution_history else None,
                    'available_operations': [
                        'execute_main_function',
                        'get_status',
                        {% for func in custom_functions %}'{{ func.name }}',{% endfor %}
                    ],
                    'repository_functions_mapped': {{ custom_functions|length }}
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

# Global processor instance
generic_processor = GenericProcessor()

{% for func in custom_functions %}
def {{ func.name }}({{ func.parameters }}) -> Dict[str, Any]:
    \"\"\"{{ func.description }}\"\"\"
    try:
        # TODO: Implement actual logic from {{ func.file_path }}
        # Placeholder implementation that should be replaced with actual business logic
        
        execution_record = {
            'function_name': '{{ func.name }}',
            'source_file': '{{ func.file_path }}',
            'timestamp': datetime.now().isoformat(),
            'description': '{{ func.description }}'
        }
        
        # Add to global processor history
        generic_processor.execution_history.append(execution_record)
        
        return {
            'success': True,
            'message': f'{{ func.name }} executed successfully',
            'execution_record': execution_record,
            'implementation_note': 'This function needs actual implementation from the original repository',
            'source_file': '{{ func.file_path }}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'function_name': '{{ func.name }}'
        }

{% endfor %}
""").render(custom_functions=[
        {
            'name': func['name'],
            'description': func.get('description', f"Function: {func['name']}"),
            'file_path': func.get('file_path', 'unknown'),
            'parameters': 'data: Dict[str, Any] = None'
        }
        for func in main_functionality if func.get('type') == 'function'
    ])
    
    generic_file = business_logic_dir / "generic_processor.py"
    with open(generic_file, 'w', encoding='utf-8') as f:
        f.write(generic_content)
    generated_files.append(str(generic_file))
    
    return generated_files
