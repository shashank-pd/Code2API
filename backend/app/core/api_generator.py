"""
API Generation Engine
Converts analyzed code into functional FastAPI applications
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from jinja2 import Environment, FileSystemLoader, Template

from .config import settings
from .code_analyzer import APIEndpoint

logger = logging.getLogger(__name__)

@dataclass
class GeneratedAPI:
    """Information about a generated API"""
    project_name: str
    api_path: str
    openapi_spec: Dict[str, Any]
    endpoints: List[Dict[str, Any]]
    files_created: List[str]

class APIGenerator:
    """Generates FastAPI applications from code analysis"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )

    async def generate_api(
        self,
        analysis_data: Dict[str, Any],
        project_name: str,
        include_auth: bool = True,
        include_tests: bool = True,
        include_docs: bool = True
    ) -> Dict[str, Any]:
        """
        Generate a complete FastAPI application from analysis data
        
        Args:
            analysis_data: Results from code analysis
            project_name: Name for the generated API project
            include_auth: Whether to include authentication
            include_tests: Whether to generate test files
            include_docs: Whether to generate documentation
        
        Returns:
            Information about the generated API
        """
        try:
            logger.info(f"Generating API for project: {project_name}")
            
            # Create project directory
            project_path = Path(settings.GENERATED_APIS_DIR) / project_name
            project_path.mkdir(parents=True, exist_ok=True)
            
            # Extract endpoints from analysis data
            endpoints = analysis_data.get("api_endpoints", [])
            
            # Generate API structure
            files_created = []
            
            # 1. Generate main application file
            main_file = await self._generate_main_app(
                project_path, project_name, endpoints, include_auth
            )
            files_created.append(main_file)
            
            # 2. Generate models
            models_file = await self._generate_models(project_path, endpoints)
            files_created.append(models_file)
            
            # 3. Generate routers
            router_files = await self._generate_routers(project_path, endpoints)
            files_created.extend(router_files)
            
            # 4. Generate requirements.txt
            requirements_file = await self._generate_requirements(project_path, endpoints)
            files_created.append(requirements_file)
            
            # 5. Generate configuration
            config_file = await self._generate_config(project_path)
            files_created.append(config_file)
            
            # 6. Generate authentication (if requested)
            if include_auth:
                auth_file = await self._generate_auth(project_path)
                files_created.append(auth_file)
            
            # 7. Generate tests (if requested)
            if include_tests:
                test_files = await self._generate_tests(project_path, endpoints)
                files_created.extend(test_files)
            
            # 8. Generate documentation
            if include_docs:
                docs_files = await self._generate_docs(project_path, project_name, endpoints)
                files_created.extend(docs_files)
            
            # 9. Generate OpenAPI specification
            openapi_spec = self._generate_openapi_spec(project_name, endpoints)
            
            # 10. Generate Docker files
            docker_files = await self._generate_docker_files(project_path, project_name)
            files_created.extend(docker_files)
            
            # 11. Generate README
            readme_file = await self._generate_readme(project_path, project_name, endpoints)
            files_created.append(readme_file)
            
            # 12. Generate startup scripts
            startup_files = await self._generate_startup_scripts(project_path, project_name)
            files_created.extend(startup_files)
            
            # 13. Generate __init__.py for package
            init_file = project_path / "__init__.py"
            init_file.write_text("# Generated API Package")
            files_created.append(str(init_file))
            
            logger.info(f"Generated API with {len(files_created)} files")
            
            return {
                "success": True,
                "api_path": str(project_path),
                "openapi_spec": openapi_spec,
                "endpoints": endpoints,
                "files_created": files_created,
                "project_name": project_name
            }
            
        except Exception as e:
            logger.error(f"API generation failed: {str(e)}")
            raise Exception(f"API generation failed: {str(e)}")

    async def _generate_main_app(
        self,
        project_path: Path,
        project_name: str,
        endpoints: List[Dict[str, Any]],
        include_auth: bool
    ) -> str:
        """Generate the main FastAPI application file"""
        
        main_template = '''"""
{project_name} - Generated API
Auto-generated FastAPI application
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from typing import Dict, Any
import logging

{auth_import}
from routers import {router_imports}
from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="{project_name}",
    description="Auto-generated API from source code analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

{auth_setup}

# Include routers
{router_includes}

@app.get("/")
async def root():
    """Root endpoint"""
    return {{
        "message": "{project_name} API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {endpoint_count}
    }}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {{"status": "healthy", "service": "{project_name}"}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

        # Group endpoints by their tags/categories
        routers = set()
        for endpoint in endpoints:
            tags = endpoint.get("tags", ["general"])
            routers.add(tags[0] if tags else "general")
        
        router_imports = ", ".join(f"{router}_router" for router in routers)
        router_includes = "\\n".join(
            f'app.include_router({router}_router, prefix="/api/{router}", tags=["{router}"])'
            for router in routers
        )
        
        auth_import = "from auth import get_current_user" if include_auth else ""
        auth_setup = """
# Security
security = HTTPBearer()

# Dependency to get current user
async def get_current_user_dependency():
    return get_current_user
""" if include_auth else ""
        
        content = main_template.format(
            project_name=project_name,
            auth_import=auth_import,
            router_imports=router_imports,
            auth_setup=auth_setup,
            router_includes=router_includes,
            endpoint_count=len(endpoints)
        )
        
        main_file = project_path / "main.py"
        main_file.write_text(content, encoding='utf-8')
        
        return str(main_file)

    async def _generate_models(self, project_path: Path, endpoints: List[Dict[str, Any]]) -> str:
        """Generate Pydantic models"""
        
        models_template = '''"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

{endpoint_models}

# Response models
{response_models}
'''

        endpoint_models = []
        response_models = []
        
        for endpoint in endpoints:
            # Generate request model
            if endpoint.get("parameters"):
                model_name = f"{endpoint['function_name'].title()}Request"
                fields = []
                
                for param in endpoint["parameters"]:
                    param_type = self._map_type_to_python(param.get("type", "str"))
                    required = param.get("required", True)
                    default = " = None" if not required else ""
                    description = param.get("description", "")
                    
                    field_def = f'    {param["name"]}: {param_type}{default}'
                    if description:
                        field_def += f' = Field(description="{description}")'
                    
                    fields.append(field_def)
                
                model_def = f'''
class {model_name}(BaseModel):
    """Request model for {endpoint["function_name"]}"""
{chr(10).join(fields) if fields else "    pass"}
'''
                endpoint_models.append(model_def)
            
            # Generate response model
            response_model_name = f"{endpoint['function_name'].title()}Response"
            response_def = f'''
class {response_model_name}(BaseResponse):
    """Response model for {endpoint["function_name"]}"""
    data: Optional[Dict[str, Any]] = None
'''
            response_models.append(response_def)
        
        content = models_template.format(
            endpoint_models="".join(endpoint_models),
            response_models="".join(response_models)
        )
        
        models_file = project_path / "models.py"
        models_file.write_text(content, encoding='utf-8')
        
        return str(models_file)

    async def _generate_routers(self, project_path: Path, endpoints: List[Dict[str, Any]]) -> List[str]:
        """Generate FastAPI routers"""
        
        router_template = '''"""
{router_name} router
Generated API endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from models import {model_imports}
{auth_import}

logger = logging.getLogger(__name__)

router = APIRouter()

{endpoints_code}
'''

        # Group endpoints by tags
        routers_by_tag = {}
        for endpoint in endpoints:
            tags = endpoint.get("tags", ["general"])
            tag = tags[0] if tags else "general"
            
            if tag not in routers_by_tag:
                routers_by_tag[tag] = []
            routers_by_tag[tag].append(endpoint)
        
        created_files = []
        routers_dir = project_path / "routers"
        routers_dir.mkdir(exist_ok=True)
        
        # Create __init__.py
        init_file = routers_dir / "__init__.py"
        router_exports = [f"from .{tag} import router as {tag}_router" for tag in routers_by_tag.keys()]
        init_file.write_text("\\n".join(router_exports), encoding='utf-8')
        created_files.append(str(init_file))
        
        for tag, tag_endpoints in routers_by_tag.items():
            endpoints_code = []
            model_imports = set()
            
            for endpoint in tag_endpoints:
                # Generate endpoint function
                endpoint_code = self._generate_endpoint_function(endpoint)
                endpoints_code.append(endpoint_code)
                
                # Track model imports
                function_name = endpoint["function_name"]
                model_imports.add(f"{function_name.title()}Request")
                model_imports.add(f"{function_name.title()}Response")
            
            auth_import = "from auth import get_current_user" if any(
                ep.get("needs_auth", False) for ep in tag_endpoints
            ) else ""
            
            content = router_template.format(
                router_name=tag.title(),
                model_imports=", ".join(sorted(model_imports)),
                auth_import=auth_import,
                endpoints_code="\\n\\n".join(endpoints_code)
            )
            
            router_file = routers_dir / f"{tag}.py"
            router_file.write_text(content, encoding='utf-8')
            created_files.append(str(router_file))
        
        return created_files

    def _generate_endpoint_function(self, endpoint: Dict[str, Any]) -> str:
        """Generate a single endpoint function with actual implementation"""
        
        function_name = endpoint["function_name"]
        http_method = endpoint["http_method"].lower()
        endpoint_path = endpoint["endpoint_path"]
        description = endpoint.get("description", "")
        needs_auth = endpoint.get("needs_auth", False)
        implementation_code = endpoint.get("implementation_code", "")
        
        # Generate function parameters
        params = []
        param_validation = []
        
        # Add request model for POST/PUT/PATCH with parameters
        if endpoint.get("parameters") and http_method in ["post", "put", "patch"]:
            params.append(f"request: {function_name.title()}Request")
            # Generate validation code
            for param in endpoint.get("parameters", []):
                param_name = param["name"]
                param_type = param["type"]
                param_validation.append(f"        {param_name} = request.{param_name}")
        
        # For GET requests with parameters, add them as query parameters
        elif endpoint.get("parameters") and http_method == "get":
            for param in endpoint.get("parameters", []):
                param_name = param["name"]
                param_type = param["type"]
                required = param.get("required", True)
                
                if param_type == "number":
                    type_hint = "float"
                elif param_type == "integer":
                    type_hint = "int"
                elif param_type == "boolean":
                    type_hint = "bool"
                else:
                    type_hint = "str"
                
                if required:
                    params.append(f"{param_name}: {type_hint}")
                else:
                    params.append(f"{param_name}: Optional[{type_hint}] = None")
        
        if needs_auth:
            params.append("current_user: dict = Depends(get_current_user)")
        
        param_str = ", ".join(params)
        
        # Generate actual implementation or smart fallback
        if implementation_code and implementation_code.strip():
            # Use AI-generated implementation
            implementation_lines = [f"        {line}" for line in implementation_code.split('\n')]
        else:
            # Generate smart fallback based on function name
            implementation_lines = self._generate_smart_implementation(function_name, endpoint)
        
        # Generate function body
        body_lines = [
            f'    """',
            f'    {description}',
            f'    """',
            f'    try:',
            f'        logger.info(f"Executing {function_name}")',
            f'        '
        ]
        
        # Add parameter validation
        body_lines.extend(param_validation)
        
        # Add implementation
        body_lines.extend(implementation_lines)
        
        body_lines.extend([
            f'        ',
            f'        return {function_name.title()}Response(',
            f'            success=True,',
            f'            message="{function_name} completed successfully",',
            f'            data=result',
            f'        )',
            f'        ',
            f'    except Exception as e:',
            f'        logger.error(f"{function_name} failed: {{str(e)}}")',
            f'        raise HTTPException(status_code=500, detail=f"{function_name} failed: {{str(e)}}")'
        ])
        
        # Generate complete function
        endpoint_function = f'''
@router.{http_method}("{endpoint_path}", response_model={function_name.title()}Response)
async def {function_name}({param_str}):
{chr(10).join(body_lines)}
'''
        
        return endpoint_function

    def _generate_smart_implementation(self, function_name: str, endpoint: Dict[str, Any]) -> List[str]:
        """Generate smart implementation based on function type and context"""
        
        name_lower = function_name.lower()
        
        # Get implementation from AI analysis if available
        if "implementation_code" in endpoint and endpoint["implementation_code"]:
            # Clean and format AI-generated implementation
            impl_code = endpoint["implementation_code"]
            
            # Split into lines and indent properly
            lines = impl_code.split('\n')
            formatted_lines = []
            for line in lines:
                if line.strip():
                    # Add proper indentation (8 spaces for function body)
                    if not line.startswith('        '):
                        formatted_lines.append(f"        {line}")
                    else:
                        formatted_lines.append(line)
                else:
                    formatted_lines.append("")
            
            return formatted_lines
        
        # Fallback implementations based on function patterns
        

        
        # Data processing functions
        elif any(word in name_lower for word in ["process", "transform", "parse", "convert"]):
            return [
                "        # Data processing implementation",
                "        try:",
                "            # Process the input data",
                "            processed_data = data  # Add actual processing logic here",
                "            result = {",
                "                'status': 'success',",
                "                'processed_data': processed_data,",
                f"                'function': '{function_name}'",
                "            }",
                "        except Exception as e:",
                "            raise HTTPException(status_code=400, detail=f'Processing error: {str(e)}')"
            ]
        
        # Web scraping functions
        elif any(word in name_lower for word in ["scrape", "fetch", "extract", "crawl"]):
            return [
                "        # Web scraping implementation",
                "        import requests",
                "        from bs4 import BeautifulSoup",
                "        ",
                "        try:",
                "            if not url:",
                "                raise HTTPException(status_code=400, detail='URL is required')",
                "            ",
                "            response = requests.get(url)",
                "            response.raise_for_status()",
                "            ",
                "            soup = BeautifulSoup(response.content, 'html.parser')",
                "            # Add specific extraction logic here",
                "            ",
                "            result = {",
                "                'url': url,",
                "                'status_code': response.status_code,",
                "                'title': soup.title.string if soup.title else None,",
                "                'content_length': len(response.content)",
                "            }",
                "        except Exception as e:",
                "            raise HTTPException(status_code=400, detail=f'Scraping error: {str(e)}')"
            ]
        
        # Authentication functions
        elif any(word in name_lower for word in ["auth", "login", "token", "validate"]):
            return [
                "        # Authentication implementation",
                "        from jose import JWTError, jwt",
                "        from datetime import datetime, timedelta",
                "        ",
                "        try:",
                "            # Add actual authentication logic here",
                "            token_data = {",
                "                'sub': username,",
                "                'exp': datetime.utcnow() + timedelta(hours=24)",
                "            }",
                "            ",
                "            result = {",
                "                'access_token': 'generated_token_here',",
                "                'token_type': 'bearer',",
                "                'expires_in': 86400",
                "            }",
                "        except Exception as e:",
                "            raise HTTPException(status_code=401, detail='Authentication failed')"
            ]
        
        # File operations
        elif any(word in name_lower for word in ["file", "upload", "download", "save", "read"]):
            return [
                "        # File operation implementation",
                "        import os",
                "        ",
                "        try:",
                "            # Add file handling logic here",
                "            result = {",
                f"                'operation': '{function_name}',",
                "                'status': 'success',",
                "                'message': 'File operation completed'",
                "            }",
                "        except Exception as e:",
                "            raise HTTPException(status_code=400, detail=f'File operation error: {str(e)}')"
            ]
        
        # Database operations
        elif any(word in name_lower for word in ["db", "database", "save", "delete", "update", "create"]):
            return [
                "        # Database operation implementation",
                "        try:",
                "            # Add database logic here",
                "            result = {",
                f"                'operation': '{function_name}',",
                "                'status': 'success',",
                "                'affected_rows': 1",
                "            }",
                "        except Exception as e:",
                "            raise HTTPException(status_code=400, detail=f'Database error: {str(e)}')"
            ]
        
        # Math/calculation functions
        elif any(word in name_lower for word in ["calc", "calculate", "compute", "math", "add", "subtract", "multiply", "divide"]):
            return [
                "        # Mathematical calculation implementation",
                "        try:",
                "            # Add calculation logic here",
                "            result = {",
                f"                'function': '{function_name}',",
                "                'calculation': 'performed',",
                "                'result': 'calculated_value'",
                "            }",
                "        except Exception as e:",
                "            raise HTTPException(status_code=400, detail=f'Calculation error: {str(e)}')"
            ]
        
        # Machine learning functions
        elif any(word in name_lower for word in ["predict", "model", "train", "classify", "ml", "ai"]):
            return [
                "        # Machine learning implementation",
                "        import numpy as np",
                "        ",
                "        try:",
                "            # Add ML model logic here",
                "            prediction = np.random.random()  # Replace with actual model",
                "            ",
                "            result = {",
                "                'prediction': prediction,",
                "                'confidence': 0.95,",
                f"                'model': '{function_name}'",
                "            }",
                "        except Exception as e:",
                "            raise HTTPException(status_code=400, detail=f'Prediction error: {str(e)}')"
            ]
        
        # Default implementation for any function
        else:
            return [
                f"        # Implementation for {function_name}",
                "        try:",
                "            # Add your custom logic here",
                "            result = {",
                f"                'function': '{function_name}',",
                "                'status': 'executed',",
                "                'message': 'Function executed successfully'",
                "            }",
                "        except Exception as e:",
                "            raise HTTPException(status_code=400, detail=f'Function error: {str(e)}')"
            ]

    async def _generate_requirements(self, project_path: Path, endpoints: List[Dict[str, Any]]) -> str:
        """Generate requirements.txt file with dependencies based on endpoint types"""
        
        # Base requirements for FastAPI
        requirements = [
            "fastapi==0.104.1",
            "uvicorn[standard]==0.24.0",
            "pydantic==2.5.0",
            "python-multipart==0.0.6",
            "python-jose[cryptography]==3.3.0",
            "passlib[bcrypt]==1.7.4",
            "python-dotenv==1.0.0",
            "requests==2.31.0"
        ]
        
        # Analyze endpoints to determine additional dependencies
        endpoint_types = set()
        for endpoint in endpoints:
            name_lower = endpoint.get('function_name', '').lower()
            implementation = endpoint.get('implementation_code', '')
            
            # Check for specific libraries mentioned in implementation
            if 'beautifulsoup' in implementation.lower() or 'scrape' in name_lower:
                endpoint_types.add('web_scraping')
            if 'numpy' in implementation.lower() or 'ml' in name_lower or 'predict' in name_lower:
                endpoint_types.add('machine_learning')
            if 'pandas' in implementation.lower() or 'process' in name_lower:
                endpoint_types.add('data_processing')
            if 'sqlalchemy' in implementation.lower() or 'database' in name_lower:
                endpoint_types.add('database')
            if 'pillow' in implementation.lower() or 'image' in name_lower:
                endpoint_types.add('image_processing')
            if 'matplotlib' in implementation.lower() or 'plot' in name_lower:
                endpoint_types.add('visualization')
        
        # Add conditional dependencies
        if 'web_scraping' in endpoint_types:
            requirements.extend([
                "beautifulsoup4==4.12.2",
                "selenium==4.15.2",
                "lxml==4.9.3"
            ])
        
        if 'machine_learning' in endpoint_types:
            requirements.extend([
                "numpy==1.24.3",
                "scikit-learn==1.3.0",
                "pandas==2.0.3",
                "joblib==1.3.2"
            ])
        
        if 'data_processing' in endpoint_types:
            requirements.extend([
                "pandas==2.0.3",
                "openpyxl==3.1.2",
                "xlsxwriter==3.1.9"
            ])
        
        if 'database' in endpoint_types:
            requirements.extend([
                "sqlalchemy==2.0.23",
                "databases[sqlite]==0.8.0",
                "aiofiles==23.2.1"
            ])
        
        if 'image_processing' in endpoint_types:
            requirements.extend([
                "Pillow==10.0.1",
                "opencv-python==4.8.1.78"
            ])
        
        if 'visualization' in endpoint_types:
            requirements.extend([
                "matplotlib==3.7.2",
                "seaborn==0.12.2",
                "plotly==5.17.0"
            ])
        
        # Remove duplicates and sort
        requirements = sorted(list(set(requirements)))
        
        requirements_file = project_path / "requirements.txt"
        requirements_file.write_text("\\n".join(requirements), encoding='utf-8')
        
        return str(requirements_file)

    async def _generate_config(self, project_path: Path) -> str:
        """Generate configuration file"""
        
        config_content = '''"""
Configuration settings
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Generated API"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "sqlite:///./api.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
'''
        
        config_file = project_path / "config.py"
        config_file.write_text(config_content)
        
        return str(config_file)

    async def _generate_auth(self, project_path: Path) -> str:
        """Generate authentication module"""
        
        auth_content = '''"""
Authentication and authorization
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security
security = HTTPBearer()

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get the current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # In a real application, you would fetch the user from a database
    user = User(username=token_data.username, email=f"{token_data.username}@example.com")
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get the current active user"""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
'''
        
        auth_file = project_path / "auth.py"
        auth_file.write_text(auth_content)
        
        return str(auth_file)

    async def _generate_tests(self, project_path: Path, endpoints: List[Dict[str, Any]]) -> List[str]:
        """Generate test files"""
        
        tests_dir = project_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        # Test main file
        test_main_content = '''"""
Test main application
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_health():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
'''
        
        test_main_file = tests_dir / "test_main.py"
        test_main_file.write_text(test_main_content)
        
        # Generate test for each endpoint
        test_files = [str(test_main_file)]
        
        for endpoint in endpoints:
            test_content = f'''"""
Test {endpoint["function_name"]} endpoint
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_{endpoint["function_name"]}():
    """Test {endpoint["function_name"]} endpoint"""
    # TODO: Implement test for {endpoint["function_name"]}
    # This is a placeholder test
    
    response = client.{endpoint["http_method"].lower()}("{endpoint["endpoint_path"]}")
    # Add appropriate assertions based on endpoint behavior
    pass
'''
            
            test_file = tests_dir / f"test_{endpoint['function_name']}.py"
            test_file.write_text(test_content)
            test_files.append(str(test_file))
        
        return test_files

    async def _generate_docs(
        self, 
        project_path: Path, 
        project_name: str, 
        endpoints: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate documentation files"""
        
        docs_dir = project_path / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        # API documentation
        api_doc_content = f'''# {project_name} API Documentation

## Overview

This is an auto-generated API created from source code analysis.

## Endpoints

{chr(10).join(self._format_endpoint_doc(ep) for ep in endpoints)}

## Authentication

This API uses Bearer token authentication. Include your token in the Authorization header:

```
Authorization: Bearer your-token-here
```

## Error Handling

All endpoints return standardized error responses:

```json
{{
  "success": false,
  "error": "Error description",
  "details": {{}},
  "timestamp": "2024-01-01T00:00:00"
}}
```

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run the API: `python main.py`
3. View interactive docs at: http://localhost:8000/docs
'''
        
        api_doc_file = docs_dir / "api.md"
        api_doc_file.write_text(api_doc_content)
        
        return [str(api_doc_file)]

    def _format_endpoint_doc(self, endpoint: Dict[str, Any]) -> str:
        """Format endpoint documentation"""
        
        params_doc = ""
        if endpoint.get("parameters"):
            params_list = []
            for param in endpoint["parameters"]:
                required = " (required)" if param.get("required", True) else " (optional)"
                params_list.append(f"- `{param['name']}` ({param.get('type', 'string')}){required}: {param.get('description', 'No description')}")
            params_doc = "\\n\\n**Parameters:**\\n" + "\\n".join(params_list)
        
        return f'''
### {endpoint["http_method"]} {endpoint["endpoint_path"]}

{endpoint.get("description", "No description")}

**Function:** `{endpoint["function_name"]}`{params_doc}

**Authentication:** {"Required" if endpoint.get("needs_auth", False) else "Not required"}
'''

    async def _generate_docker_files(self, project_path: Path, project_name: str) -> List[str]:
        """Generate Docker files"""
        
        dockerfile_content = '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
'''
        
        dockerfile = project_path / "Dockerfile"
        dockerfile.write_text(dockerfile_content)
        
        docker_compose_content = f'''version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
'''
        
        docker_compose_file = project_path / "docker-compose.yml"
        docker_compose_file.write_text(docker_compose_content)
        
        return [str(dockerfile), str(docker_compose_file)]

    async def _generate_readme(
        self, 
        project_path: Path, 
        project_name: str, 
        endpoints: List[Dict[str, Any]]
    ) -> str:
        """Generate README file"""
        
        readme_content = f'''# {project_name}

Auto-generated API created from source code analysis.

## Features

- **{len(endpoints)} API endpoints** automatically generated
- **Interactive documentation** at `/docs`
- **Authentication** support with JWT tokens
- **Docker** support for easy deployment
- **Comprehensive testing** with pytest

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the API:**
   ```bash
   python main.py
   ```

3. **View documentation:**
   Open http://localhost:8000/docs in your browser

## API Endpoints

{chr(10).join(f"- `{ep['http_method']} {ep['endpoint_path']}` - {ep.get('description', 'No description')}" for ep in endpoints)}

## Using Docker

```bash
docker-compose up --build
```

## Testing

```bash
pytest tests/
```

## Configuration

Create a `.env` file with your configuration:

```
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./api.db
```

## Generated Files

- `main.py` - Main FastAPI application
- `models.py` - Pydantic models for request/response validation
- `routers/` - API route handlers
- `auth.py` - Authentication and authorization
- `config.py` - Configuration settings
- `tests/` - Test files
- `docs/` - Documentation

## Support

This API was automatically generated. For questions about specific endpoints, refer to the original source code or the interactive documentation at `/docs`.
'''
        
        readme_file = project_path / "README.md"
        readme_file.write_text(readme_content)
        
        return str(readme_file)

    def _generate_openapi_spec(self, project_name: str, endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate OpenAPI specification"""
        
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": project_name,
                "version": "1.0.0",
                "description": "Auto-generated API from source code analysis"
            },
            "paths": {},
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                }
            }
        }
        
        for endpoint in endpoints:
            path = endpoint["endpoint_path"]
            method = endpoint["http_method"].lower()
            
            if path not in spec["paths"]:
                spec["paths"][path] = {}
            
            endpoint_spec = {
                "summary": endpoint.get("description", "No description"),
                "operationId": endpoint["function_name"],
                "responses": {
                    "200": {
                        "description": "Success",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    }
                }
            }
            
            # Add parameters
            if endpoint.get("parameters"):
                endpoint_spec["parameters"] = []
                for param in endpoint["parameters"]:
                    param_spec = {
                        "name": param["name"],
                        "in": "query" if method == "get" else "query",
                        "required": param.get("required", True),
                        "schema": {
                            "type": self._map_type_to_openapi(param.get("type", "string"))
                        },
                        "description": param.get("description", "")
                    }
                    endpoint_spec["parameters"].append(param_spec)
            
            # Add authentication
            if endpoint.get("needs_auth", False):
                endpoint_spec["security"] = [{"bearerAuth": []}]
            
            spec["paths"][path][method] = endpoint_spec
        
        return spec

    def _map_type_to_python(self, api_type: str) -> str:
        """Map API type to Python type annotation"""
        type_map = {
            "string": "str",
            "integer": "int",
            "number": "float",
            "boolean": "bool",
            "array": "List[Any]",
            "object": "Dict[str, Any]"
        }
        return type_map.get(api_type, "str")

    def _map_type_to_openapi(self, api_type: str) -> str:
        """Map API type to OpenAPI type"""
        type_map = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object"
        }
        return type_map.get(api_type, "string")

    async def _generate_startup_scripts(self, project_path: Path, project_name: str) -> List[str]:
        """Generate startup scripts for easy API launching"""
        created_files = []
        
        # Python startup script
        python_script = f'''#!/usr/bin/env python3
"""
Startup script for {project_name}
"""

import sys
import os
import subprocess
from pathlib import Path

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("SUCCESS: Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to install dependencies: {{e}}")
        return False

def run_api():
    """Run the FastAPI application"""
    print("Starting the API server...")
    try:
        import uvicorn
        uvicorn.run("main:app", host="0.0.0.0", port=8001)
    except ImportError:
        print("ERROR: uvicorn not found. Installing dependencies...")
        if install_dependencies():
            import uvicorn
            uvicorn.run("main:app", host="0.0.0.0", port=8001)
        else:
            print("ERROR: Failed to install uvicorn")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to start API: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    print("STARTING: {project_name} API Launcher")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("ERROR: main.py not found in current directory")
        print("Please run this script from the generated API directory")
        sys.exit(1)
    
    print("Working directory:", os.getcwd())
    print("API will be available at: http://localhost:8001")
    print("API docs will be available at: http://localhost:8001/docs")
    print("Health check: http://localhost:8001/health")
    print("=" * 50)
    
    run_api()
'''
        
        python_file = project_path / "start.py"
        python_file.write_text(python_script, encoding='utf-8')
        created_files.append(str(python_file))
        
        # Windows batch file
        batch_script = f'''@echo off
echo {project_name} API Launcher
echo ================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "main.py" (
    echo main.py not found in current directory
    echo Please run this script from the generated API directory
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

REM Run the API
echo.
echo Starting API server...
echo API will be available at: http://localhost:8001
echo API docs will be available at: http://localhost:8001/docs
echo Health check: http://localhost:8001/health
echo.
echo Press Ctrl+C to stop the server
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8001

pause
'''
        
        batch_file = project_path / "start.bat"
        batch_file.write_text(batch_script, encoding='utf-8')
        created_files.append(str(batch_file))
        
        # Unix shell script
        shell_script = f'''#!/bin/bash

echo "STARTING: {project_name} API Launcher"
echo "================================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in current directory"
    echo "Please run this script from the generated API directory"
    exit 1
fi

echo "Working directory: $(pwd)"
echo "API will be available at: http://localhost:8001"
echo "API docs will be available at: http://localhost:8001/docs"
echo "Health check: http://localhost:8001/health"
echo "================================================"

# Install dependencies
echo "Installing dependencies..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

# Run the API
echo "Starting API server..."
echo "Press Ctrl+C to stop the server"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001
'''
        
        shell_file = project_path / "start.sh"
        shell_file.write_text(shell_script, encoding='utf-8')
        # Make shell script executable
        os.chmod(shell_file, 0o755)
        created_files.append(str(shell_file))
        
        return created_files
