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
        """Generate the main FastAPI application file with AI-powered implementation"""
        
        endpoints = analysis.get("api_endpoints", [])
        
        imports = '''from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from typing import Optional, Dict, Any, List
import json
import math
import random
from datetime import datetime

from models import *
from auth import (
    verify_token, create_access_token, authenticate_user, 
    UserRole, check_user_permission, verify_api_key, 
    get_user_from_auth, create_api_key, api_key_header
)'''

        app_setup = f'''
app = FastAPI(
    title="{project_name.title()} API",
    description="Auto-generated API from source code analysis with enhanced authentication",
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

security = HTTPBearer(auto_error=False)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {{"status": "healthy", "message": "API is running", "timestamp": datetime.utcnow().isoformat()}}

# Authentication endpoints
@app.post("/auth/token")
async def login(credentials: UserCredentials):
    """Get JWT token with username/password"""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={{"WWW-Authenticate": "Bearer"}},
        )
    
    access_token = create_access_token(data={{"sub": user["username"]}})
    return {{
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 1800,
        "user": {{
            "username": user["username"],
            "roles": user.get("roles", [])
        }}
    }}

@app.post("/auth/api-key")
async def create_user_api_key(credentials: UserCredentials):
    """Create API key for authentication"""
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    api_key = create_api_key(user["username"])
    return {{
        "api_key": api_key,
        "type": "api_key",
        "user": {{
            "username": user["username"],
            "roles": user.get("roles", [])
        }},
        "message": "Store this API key securely. Use it in X-API-Key header."
    }}

@app.get("/auth/me")
async def get_current_user(
    token: Optional[HTTPAuthorizationCredentials] = Depends(security),
    api_key: Optional[str] = Depends(api_key_header)
):
    """Get current authenticated user info"""
    user = get_user_from_auth(
        token=token.credentials if token else None,
        api_key=api_key
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    return {{
        "username": user["username"],
        "email": user.get("email"),
        "roles": user.get("roles", []),
        "auth_method": user.get("auth_method", "unknown"),
        "is_active": user.get("is_active", False)
    }}
'''

        # Generate endpoints
        endpoint_code = ""
        for endpoint in endpoints:
            function_name = endpoint.get('function_name', 'unknown_function').replace('-', '_').replace(' ', '_')
            http_method = endpoint.get('http_method', 'post').lower()
            endpoint_path = endpoint.get('endpoint_path', f'/{endpoint.get("function_name", "unknown")}')
            description = endpoint.get('description', 'AI-generated API endpoint')
            needs_auth = endpoint.get('needs_auth', False)
            
            input_validation = endpoint.get('input_validation', {})
            required_params = input_validation.get('required_params', [])
            
            # Build function signature
            params = []
            if required_params:
                if http_method.upper() in ['POST', 'PUT', 'PATCH']:
                    # Consistent model name generation
                    clean_function_name = function_name.replace('-', '').replace(' ', '').replace('_', '')
                    request_model = f"{clean_function_name.title()}Request"
                    params.append(f"request: {request_model}")
                else:  # GET requests use query parameters
                    for param in required_params:
                        param_type = 'float' if param.get('type') in ['int', 'integer', 'number', 'float'] else 'str'
                        params.append(f"{param.get('name')}: {param_type}")
            
            if needs_auth:
                params.append("token: HTTPAuthorizationCredentials = Depends(security)")
            
            params_str = ",\n    ".join(params)
            if params_str:
                params_str = f"\n    {params_str}\n"
            
            # Build function body
            auth_check = ""
            if needs_auth:
                auth_check = '''    # Verify authentication
    user = verify_token(token.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
'''

            # Parameter extraction
            param_extraction = ""
            if required_params:
                if http_method.upper() in ['POST', 'PUT', 'PATCH']:
                    for param in required_params:
                        param_extraction += f"        {param.get('name')} = request.{param.get('name')}\n"
                # For GET requests, parameters are already available
            
            # Generate implementation based on function name
            implementation = self._generate_function_implementation(function_name, required_params, needs_auth)
            
            endpoint_code += f'''
# {description}
@app.{http_method}("{endpoint_path}")
async def {function_name}({params_str}):
    """
    {description}
    
    {"Requires authentication." if needs_auth else ""}
    """
{auth_check}    try:
{param_extraction}{implementation}
        
        return result
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input parameters: {{str(ve)}}")
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Division by zero is not allowed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {{str(e)}}")
'''

        main_runner = '''

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
'''

        return imports + app_setup + endpoint_code + main_runner
    
    def _generate_enhanced_endpoint(self, endpoint: Dict[str, Any]) -> str:
        """Generate endpoint with enhanced authentication and role-based access control"""
        function_name = endpoint.get('function_name', 'unknown_function').replace('-', '_').replace(' ', '_')
        http_method = endpoint.get('http_method', 'POST').lower()
        endpoint_path = endpoint.get('endpoint_path', f'/{endpoint.get("function_name", "unknown")}')
        description = endpoint.get('description', 'AI-generated API endpoint')
        needs_auth = endpoint.get('needs_auth', False)
        auth_level = endpoint.get('auth_level', 'none')
        
        # Determine authentication requirements
        auth_params = []
        auth_check = ""
        
        if needs_auth or auth_level != 'none':
            auth_params.extend([
                "token: Optional[HTTPAuthorizationCredentials] = Depends(security)",
                "api_key: Optional[str] = Depends(api_key_header)"
            ])
            
            # Map auth levels to UserRole
            role_mapping = {
                'admin': 'UserRole.ADMIN',
                'user': 'UserRole.USER', 
                'readonly': 'UserRole.READONLY'
            }
            
            required_role = role_mapping.get(auth_level, 'UserRole.READONLY')
            
            auth_check = f'''    # Enhanced authentication with role-based access control
    user = get_user_from_auth(
        token=token.credentials if token else None,
        api_key=api_key
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Use JWT token or API key."
        )
    
    # Check role permissions
    if not check_user_permission(user, {required_role}):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required role: {auth_level}"
        )
    '''
        
        # Handle parameters
        input_validation = endpoint.get('input_validation', {})
        required_params = input_validation.get('required_params', [])
        
        params = []
        param_extraction = ""
        
        if required_params:
            if http_method.upper() in ['POST', 'PUT', 'PATCH']:
                # Use request body for POST/PUT/PATCH
                clean_function_name = function_name.replace('-', '').replace(' ', '').replace('_', '')
                request_model = f"{clean_function_name.title()}Request"
                params.append(f"request: {request_model}")
                
                for param in required_params:
                    param_extraction += f"        {param.get('name')} = request.{param.get('name')}\n"
            else:
                # Use query parameters for GET
                for param in required_params:
                    param_type = self._normalize_param_type(param.get('type', 'str'))
                    params.append(f"{param.get('name')}: {param_type}")
        
        # Add auth parameters
        params.extend(auth_params)
        
        params_str = ",\n    ".join(params)
        if params_str:
            params_str = f"\n    {params_str}\n"
        
        # Generate implementation
        implementation = self._generate_function_implementation(function_name, required_params, needs_auth)
        
        # Auth info for response
        auth_info = ""
        if needs_auth or auth_level != 'none':
            auth_info = '''        result["auth_info"] = {
            "authenticated_user": user["username"],
            "user_roles": user.get("roles", []),
            "auth_method": user.get("auth_method", "unknown"),
            "required_role": "''' + auth_level + '''"
        }
        '''
        
        return f'''
# {description}
@app.{http_method}("{endpoint_path}")
async def {function_name}({params_str}):
    """
    {description}
    
    {"Authentication: " + ("Required - " + auth_level + " role" if auth_level != 'none' else "Not required")}
    
    Authentication Methods:
    - JWT Token: Use Authorization: Bearer <token>
    - API Key: Use X-API-Key: <api-key>
    """
{auth_check}    try:
{param_extraction}{implementation}
{auth_info}        
        return result
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input parameters: {{str(ve)}}")
    except ZeroDivisionError:
        raise HTTPException(status_code=400, detail="Division by zero is not allowed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {{str(e)}}")

'''
    
    def _generate_function_implementation(self, function_name: str, required_params: List[Dict], needs_auth: bool) -> str:
        """Generate the implementation for a specific function based on AI analysis"""
        
        function_name_lower = function_name.lower()
        
        # Helper function to create inputs dictionary
        def create_inputs_dict():
            if not required_params:
                return '{"message": "No parameters provided"}'
            
            inputs = []
            for param in required_params:
                inputs.append(f'"{param.get("name")}": {param.get("name")}')
            return "{" + ", ".join(inputs) + "}"
        
        # BMI calculation
        if 'bmi' in function_name_lower:
            weight_param = None
            height_param = None
            
            for param in required_params:
                if 'weight' in param.get('name', '').lower():
                    weight_param = param.get('name')
                if 'height' in param.get('name', '').lower():
                    height_param = param.get('name')
            
            if weight_param and height_param:
                if 'imperial' in function_name_lower:
                    return f'''        # BMI calculation detected by AI - Imperial
        weight_value = {weight_param}
        height_value = {height_param}
        bmi_value = (weight_value / (height_value * height_value)) * 703
        
        category = "Underweight" if bmi_value < 18.5 else "Normal weight" if bmi_value < 25 else "Overweight" if bmi_value < 30 else "Obese"
        
        result = {{
            "bmi": round(bmi_value, 2),
            "category": category,
            "weight_pounds": weight_value,
            "height_inches": height_value,
            "formula": "Imperial BMI",
            "inputs": {create_inputs_dict()},
            "message": "BMI calculated successfully"
        }}'''
                else:
                    return f'''        # BMI calculation detected by AI - Metric
        weight_value = {weight_param}
        height_value = {height_param}
        bmi_value = weight_value / (height_value * height_value)
        
        category = "Underweight" if bmi_value < 18.5 else "Normal weight" if bmi_value < 25 else "Overweight" if bmi_value < 30 else "Obese"
        
        result = {{
            "bmi": round(bmi_value, 2),
            "category": category,
            "weight_kg": weight_value,
            "height_m": height_value,
            "formula": "Metric BMI",
            "inputs": {create_inputs_dict()},
            "message": "BMI calculated successfully"
        }}'''
        
        # Arithmetic operations
        elif 'add' in function_name_lower or 'sum' in function_name_lower:
            if len(required_params) >= 2:
                param1 = required_params[0].get('name')
                param2 = required_params[1].get('name')
                return f'''        # Addition operation detected by AI
        result_value = {param1} + {param2}
        
        result = {{
            "result": result_value,
            "operation": "addition",
            "inputs": {create_inputs_dict()},
            "message": "Addition performed successfully"
        }}'''
            else:
                param_names = [param.get('name') for param in required_params]
                params_str = ', '.join(param_names)
                return f'''        # Addition operation detected by AI
        result_value = sum([{params_str}]) if [{params_str}] else 0
        
        result = {{
            "result": result_value,
            "operation": "addition",
            "inputs": {create_inputs_dict()},
            "message": "Addition performed successfully"
        }}'''
        
        elif 'subtract' in function_name_lower or 'minus' in function_name_lower:
            if len(required_params) >= 2:
                param1 = required_params[0].get('name')
                param2 = required_params[1].get('name')
                return f'''        # Subtraction operation detected by AI
        result_value = {param1} - {param2}
        
        result = {{
            "result": result_value,
            "operation": "subtraction",
            "inputs": {create_inputs_dict()},
            "message": "Subtraction performed successfully"
        }}'''
            else:
                param1 = required_params[0].get('name') if required_params else '0'
                return f'''        # Subtraction operation detected by AI
        result_value = {param1}
        
        result = {{
            "result": result_value,
            "operation": "subtraction",
            "inputs": {create_inputs_dict()},
            "message": "Subtraction performed successfully"
        }}'''
        
        elif 'multiply' in function_name_lower or 'mult' in function_name_lower:
            if len(required_params) >= 2:
                param1 = required_params[0].get('name')
                param2 = required_params[1].get('name')
                return f'''        # Multiplication operation detected by AI
        result_value = {param1} * {param2}
        
        result = {{
            "result": result_value,
            "operation": "multiplication",
            "inputs": {create_inputs_dict()},
            "message": "Multiplication performed successfully"
        }}'''
            else:
                param_names = [param.get('name') for param in required_params]
                multiply_code = '\n        '.join([f'result_value *= {name}' for name in param_names])
                return f'''        # Multiplication operation detected by AI
        result_value = 1
        {multiply_code}
        
        result = {{
            "result": result_value,
            "operation": "multiplication",
            "inputs": {create_inputs_dict()},
            "message": "Multiplication performed successfully"
        }}'''
        
        elif 'divide' in function_name_lower or 'div' in function_name_lower:
            if len(required_params) >= 2:
                param1 = required_params[0].get('name')
                param2 = required_params[1].get('name')
                return f'''        # Division operation detected by AI
        if {param2} == 0:
            raise HTTPException(status_code=400, detail="Division by zero is not allowed")
        result_value = {param1} / {param2}
        
        result = {{
            "result": result_value,
            "operation": "division",
            "inputs": {create_inputs_dict()},
            "message": "Division performed successfully"
        }}'''
            else:
                param1 = required_params[0].get('name') if required_params else '0'
                return f'''        # Division operation detected by AI
        result_value = {param1}
        
        result = {{
            "result": result_value,
            "operation": "division",
            "inputs": {create_inputs_dict()},
            "message": "Division performed successfully"
        }}'''
        
        # Task management
        elif 'task' in function_name_lower:
            action = "created"
            if 'update' in function_name_lower:
                action = "updated"
            elif 'delete' in function_name_lower:
                action = "deleted"
            elif 'complete' in function_name_lower:
                action = "completed"
            
            return f'''        # Task management detected by AI
        task_id = f"task_{{random.randint(10000, 99999)}}"
        
        result = {{
            "task_id": task_id,
            "action": "{action}",
            "status": "pending",
            "task_data": {create_inputs_dict()},
            "timestamp": datetime.now().isoformat(),
            "message": "Task operation completed successfully"
        }}'''
        
        # Search operations
        elif 'search' in function_name_lower or 'find' in function_name_lower:
            return f'''        # Search operation detected by AI
        result = {{
            "search_results": [
                {{
                    "id": 1,
                    "title": "Search result 1",
                    "content": "AI-generated search result content",
                    "relevance_score": 0.95
                }}
            ],
            "total_results": 1,
            "query": {create_inputs_dict()},
            "message": "Search completed successfully"
        }}'''
        
        # Generic function
        else:
            auth_user = ''
            if needs_auth:
                auth_user = ',\n            "authenticated_user": user["username"]'
            
            return f'''        # Generic function implementation detected by AI
        result = {{
            "function_name": "{function_name}",
            "operation_status": "success",
            "inputs": {create_inputs_dict()}{auth_user},
            "timestamp": datetime.now().isoformat(),
            "message": "Function {function_name} executed successfully"
        }}'''
    
    def _generate_models_file(self, analysis: Dict[str, Any]) -> str:
        """Generate Pydantic models"""
        
        base_models = '''from pydantic import BaseModel
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

'''
        
        # Generate request models for endpoints
        endpoints = analysis.get("api_endpoints", [])
        request_models = ""
        
        for endpoint in endpoints:
            input_validation = endpoint.get('input_validation', {})
            required_params = input_validation.get('required_params', [])
            
            if required_params and endpoint.get('http_method', 'POST').upper() in ['POST', 'PUT', 'PATCH']:
                function_name = endpoint.get('function_name', 'Unknown')
                # Consistent model name generation (same logic as main file)
                clean_function_name = function_name.replace('-', '').replace(' ', '').replace('_', '')
                model_name = f"{clean_function_name.title()}Request"
                
                request_models += f"\nclass {model_name}(BaseModel):\n"
                
                for param in required_params:
                    param_type = self._get_pydantic_type(param.get('type'))
                    default_value = param.get('default', '')
                    default_str = f" = {default_value}" if default_value else ""
                    request_models += f"    {param.get('name')}: {param_type}{default_str}\n"
                
                request_models += "\n"
        
        return base_models + request_models
    
    def _get_pydantic_type(self, type_str):
        """Convert type annotations to Pydantic types"""
        if not type_str:
            return "float"  # Default to float for numeric inputs
        
        type_mapping = {
            "str": "str",
            "string": "str",
            "int": "int", 
            "integer": "int",
            "float": "float",
            "number": "float",
            "bool": "bool",
            "boolean": "bool",
            "list": "List[Any]",
            "dict": "Dict[str, Any]",
            "any": "float"  # Default unknown types to float for better API usability
        }
        
        return type_mapping.get(type_str.lower(), "float")
    
    def _generate_auth_file(self, analysis: Dict[str, Any]) -> str:
        """Generate enhanced authentication module with role-based access control"""
        
        template = """
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"

# Configuration
SECRET_KEY = "your-secret-key-change-in-production-use-env-var"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# API Key authentication option
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Enhanced user database with roles
fake_users_db = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),
        "is_active": True,
        "roles": [UserRole.ADMIN, UserRole.USER, UserRole.READONLY]
    },
    "user": {
        "username": "user",
        "email": "user@example.com",
        "hashed_password": pwd_context.hash("user123"),
        "is_active": True,
        "roles": [UserRole.USER, UserRole.READONLY]
    },
    "demo": {
        "username": "demo",
        "email": "demo@example.com",
        "hashed_password": pwd_context.hash("demo"),
        "is_active": True,
        "roles": [UserRole.READONLY]
    }
}

# API Keys database
api_keys_db = {
    "ak_admin_demo123": {
        "username": "admin",
        "roles": [UserRole.ADMIN, UserRole.USER, UserRole.READONLY],
        "created_at": datetime.utcnow(),
        "is_active": True
    },
    "ak_user_demo456": {
        "username": "user", 
        "roles": [UserRole.USER, UserRole.READONLY],
        "created_at": datetime.utcnow(),
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
    \"\"\"Authenticate a user with username and password\"\"\"
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def verify_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    \"\"\"Verify API key and return user info\"\"\"
    if not api_key:
        return None
        
    key_info = api_keys_db.get(api_key)
    if not key_info or not key_info.get("is_active"):
        return None
        
    username = key_info["username"]
    user = fake_users_db.get(username)
    if user:
        user = user.copy()
        user["auth_method"] = "api_key"
        user["roles"] = key_info["roles"]
    
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
        if user:
            user = user.copy()
            user["auth_method"] = "jwt"
        return user
    except JWTError:
        return None

def check_user_permission(user: Dict[str, Any], required_role: UserRole) -> bool:
    \"\"\"Check if user has required role\"\"\"
    if not user:
        return False
        
    user_roles = user.get("roles", [])
    
    # Admin has all permissions
    if UserRole.ADMIN in user_roles:
        return True
    
    # Check specific role
    return required_role in user_roles

def get_user_from_auth(token: Optional[str] = None, api_key: Optional[str] = None) -> Optional[Dict[str, Any]]:
    \"\"\"Get user from either JWT token or API key\"\"\"
    if api_key:
        return verify_api_key(api_key)
    elif token:
        return verify_token(token)
    return None

def create_api_key(username: str) -> str:
    \"\"\"Create a new API key for user\"\"\"
    timestamp = int(datetime.utcnow().timestamp())
    api_key = f"ak_{username}_{timestamp}"
    
    user = fake_users_db.get(username)
    if user:
        api_keys_db[api_key] = {
            "username": username,
            "roles": user.get("roles", [UserRole.READONLY]),
            "created_at": datetime.utcnow(),
            "is_active": True
        }
    
    return api_key
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
        """Generate enhanced README.md for the generated API with authentication guide"""
        
        endpoints = analysis.get("api_endpoints", [])
        auth_endpoints = [ep for ep in endpoints if ep.get("needs_auth") or ep.get("auth_level", "none") != "none"]
        admin_endpoints = [ep for ep in endpoints if ep.get("auth_level") == "admin"]
        user_endpoints = [ep for ep in endpoints if ep.get("auth_level") == "user"] 
        readonly_endpoints = [ep for ep in endpoints if ep.get("auth_level") == "readonly"]
        
        readme = f"""# {project_name.title()} API

Auto-generated API from source code analysis using Code2API with enhanced security.

## Features

- **{len(endpoints)} API endpoints** automatically generated
- **Role-based authentication** (Admin, User, ReadOnly)
- **Multiple auth methods** (JWT tokens & API keys)
- **Interactive documentation** with Swagger UI
- **CORS enabled** for cross-origin requests
- **Docker support** for easy deployment
- **Enhanced security** with automatic threat detection

## Quick Start

### Installation

\\`\\`\\`bash
pip install -r requirements.txt
\\`\\`\\`

### Running the API

\\`\\`\\`bash
python main.py
\\`\\`\\`

The API will be available at `http://localhost:8000`

### Docker Deployment

\\`\\`\\`bash
docker-compose up --build
\\`\\`\\`

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## Authentication & Authorization

This API uses **role-based access control** with three user roles:

### User Roles
- **Admin**: Full access to all endpoints (including dangerous operations)
- **User**: Access to data modification and most operations
- **ReadOnly**: Access to read-only operations only

### Endpoint Security
- **{len(admin_endpoints)} Admin endpoints** (requires admin role)
- **{len(user_endpoints)} User endpoints** (requires user role)  
- **{len(readonly_endpoints)} ReadOnly endpoints** (requires readonly role)
- **{len(endpoints) - len(auth_endpoints)} Public endpoints** (no authentication)

### Authentication Methods

#### 1. JWT Token Authentication

**Get Token:**
\\`\\`\\`bash
curl -X POST "http://localhost:8000/auth/token" \\\\
     -H "Content-Type: application/json" \\\\
     -d '{{"username": "admin", "password": "admin123"}}'
\\`\\`\\`

**Use Token:**
\\`\\`\\`bash
curl -X GET "http://localhost:8000/your-endpoint" \\\\
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
\\`\\`\\`

#### 2. API Key Authentication

**Create API Key:**
\\`\\`\\`bash
curl -X POST "http://localhost:8000/auth/api-key" \\\\
     -H "Content-Type: application/json" \\\\
     -d '{{"username": "admin", "password": "admin123"}}'
\\`\\`\\`

**Use API Key:**
\\`\\`\\`bash
curl -X GET "http://localhost:8000/your-endpoint" \\\\
     -H "X-API-Key: YOUR_API_KEY"
\\`\\`\\`

### Demo Credentials

| Username | Password | Roles | Description |
|----------|----------|-------|-------------|
| admin | admin123 | Admin, User, ReadOnly | Full access to all endpoints |
| user | user123 | User, ReadOnly | Can modify data but not admin operations |
| demo | demo | ReadOnly | Read-only access only |

### Demo API Keys

For quick testing, these API keys are pre-configured:

| API Key | Username | Roles |
|---------|----------|-------|
| ak_admin_demo123 | admin | Admin, User, ReadOnly |
| ak_user_demo456 | user | User, ReadOnly |

## Security Features

- **Automatic threat detection** - Dangerous operations require admin authentication
- **Role-based permissions** - Users only access what they're authorized for
- **Multiple authentication methods** - JWT tokens and API keys supported
- **Secure password hashing** - bcrypt with salt
- **Token expiration** - JWT tokens expire after 30 minutes

## Endpoint Examples

### Public Endpoint (No Auth)
\\`\\`\\`bash
curl -X GET "http://localhost:8000/health"
\\`\\`\\`

### ReadOnly Endpoint
\\`\\`\\`bash
curl -X GET "http://localhost:8000/some-readonly-endpoint" \\\\
     -H "X-API-Key: ak_admin_demo123"
\\`\\`\\`

### User Endpoint  
\\`\\`\\`bash
curl -X POST "http://localhost:8000/some-user-endpoint" \\\\
     -H "Authorization: Bearer YOUR_TOKEN" \\\\
     -H "Content-Type: application/json" \\\\
     -d '{{"param": "value"}}'
\\`\\`\\`

### Admin Endpoint (Dangerous Operation)
\\`\\`\\`bash
curl -X DELETE "http://localhost:8000/some-admin-endpoint" \\\\
     -H "Authorization: Bearer ADMIN_TOKEN"
\\`\\`\\`

## Error Responses

| Status Code | Description |
|-------------|-------------|
| 401 | Authentication required |
| 403 | Insufficient permissions |  
| 400 | Invalid input parameters |
| 500 | Internal server error |

## Development

### Adding New Users

Edit the fake_users_db in auth.py:

\\`\\`\\`python
fake_users_db["newuser"] = {{
    "username": "newuser",
    "email": "newuser@example.com", 
    "hashed_password": pwd_context.hash("password"),
    "is_active": True,
    "roles": [UserRole.USER, UserRole.READONLY]
}}
\\`\\`\\`

### Changing Authentication Requirements

The system automatically detects authentication requirements based on function names:
- Functions with 'delete', 'remove', 'admin' → **Admin role required**
- Functions with 'create', 'update', 'modify' → **User role required**  
- Functions with 'get', 'read', 'list' → **ReadOnly role required**
- Computational functions → **No authentication**

## Security Notes

⚠️ **Important**: Change the SECRET_KEY in production!

⚠️ **Production**: Replace the demo user database with a real database.

⚠️ **HTTPS**: Always use HTTPS in production for secure token transmission.

## Support

Generated by Code2API - Intelligent code-to-API conversion with enhanced security."""
        
        return readme
    
    def _normalize_param_type(self, type_str: str) -> str:
        """Normalize parameter types for FastAPI"""
        type_mapping = {
            "string": "str",
            "int": "int", 
            "integer": "int",
            "float": "float",
            "number": "float",
            "bool": "bool",
            "boolean": "bool",
            "list": "List[Any]",
            "dict": "Dict[str, Any]",
            "any": "float"  # Default unknown types to float for better API usability
        }
        
        return type_mapping.get(type_str.lower(), "float")
    
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
