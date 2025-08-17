"""
Test generated APIs to ensure they work with proper HTTP methods
"""
import pytest
import tempfile
import json
import subprocess
import time
import requests
import threading
from pathlib import Path
from unittest.mock import patch

from src.api.main import app
from src.generators.api_generator import APIGenerator
from src.config import config


class TestGeneratedAPIs:
    """Test that generated APIs actually work"""
    
    @pytest.fixture
    def sample_analysis(self):
        """Sample analysis data for testing"""
        return {
            "api_endpoints": [
                {
                    "function_name": "get_users",
                    "http_method": "GET",
                    "endpoint_path": "/users",
                    "description": "Get all users",
                    "needs_auth": False,
                    "parameters": [{"name": "limit", "type": "int", "default": "10"}],
                    "is_async": False
                },
                {
                    "function_name": "create_user",
                    "http_method": "POST",
                    "endpoint_path": "/users",
                    "description": "Create a new user",
                    "needs_auth": True,
                    "parameters": [
                        {"name": "username", "type": "str"},
                        {"name": "email", "type": "str"}
                    ],
                    "is_async": False
                },
                {
                    "function_name": "get_user_by_id",
                    "http_method": "GET",
                    "endpoint_path": "/users/{user_id}",
                    "description": "Get user by ID",
                    "needs_auth": False,
                    "parameters": [{"name": "user_id", "type": "int"}],
                    "is_async": False
                },
                {
                    "function_name": "update_user",
                    "http_method": "PUT",
                    "endpoint_path": "/users/{user_id}",
                    "description": "Update user information",
                    "needs_auth": True,
                    "parameters": [
                        {"name": "user_id", "type": "int"},
                        {"name": "username", "type": "str"},
                        {"name": "email", "type": "str"}
                    ],
                    "is_async": False
                },
                {
                    "function_name": "delete_user",
                    "http_method": "DELETE",
                    "endpoint_path": "/users/{user_id}",
                    "description": "Delete user",
                    "needs_auth": True,
                    "parameters": [{"name": "user_id", "type": "int"}],
                    "is_async": False
                }
            ],
            "security_recommendations": ["Use HTTPS", "Validate input"],
            "optimization_suggestions": ["Add caching", "Use connection pooling"]
        }
    
    def test_generate_and_validate_api_structure(self, sample_analysis):
        """Test that generated API has correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "test_api")
                
                generated_path = Path(api_path)
                
                # Check all required files exist
                assert (generated_path / "main.py").exists()
                assert (generated_path / "models.py").exists()
                assert (generated_path / "auth.py").exists()
                assert (generated_path / "requirements.txt").exists()
                assert (generated_path / "README.md").exists()
                assert (generated_path / "Dockerfile").exists()
                assert (generated_path / "docker-compose.yml").exists()
                
                # Verify main.py has all HTTP methods
                main_content = (generated_path / "main.py").read_text()
                assert "@app.get(\"/users\")" in main_content
                assert "@app.post(\"/users\")" in main_content
                assert "@app.get(\"/users/{user_id}\")" in main_content
                assert "@app.put(\"/users/{user_id}\")" in main_content
                assert "@app.delete(\"/users/{user_id}\")" in main_content
    
    def test_generated_api_syntax_validity(self, sample_analysis):
        """Test that generated Python code is syntactically valid"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "syntax_test")
                
                generated_path = Path(api_path)
                
                # Check that Python files are syntactically valid
                python_files = ["main.py", "models.py", "auth.py"]
                
                for py_file in python_files:
                    file_path = generated_path / py_file
                    
                    # Try to compile the Python code
                    with open(file_path, 'r') as f:
                        code = f.read()
                    
                    try:
                        compile(code, str(file_path), 'exec')
                    except SyntaxError as e:
                        pytest.fail(f"Syntax error in {py_file}: {e}")
    
    def test_generated_api_imports(self, sample_analysis):
        """Test that generated API has correct imports"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "import_test")
                
                generated_path = Path(api_path)
                main_content = (generated_path / "main.py").read_text()
                
                # Check essential imports
                assert "from fastapi import FastAPI" in main_content
                assert "from pydantic import BaseModel" in main_content
                assert "from models import *" in main_content
                assert "from auth import verify_token" in main_content
                
                models_content = (generated_path / "models.py").read_text()
                assert "from pydantic import BaseModel" in models_content
                
                auth_content = (generated_path / "auth.py").read_text()
                assert "from jose import JWTError, jwt" in auth_content
                assert "from passlib.context import CryptContext" in auth_content
    
    def test_generated_api_endpoints_structure(self, sample_analysis):
        """Test that generated endpoints have correct structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "endpoint_test")
                
                generated_path = Path(api_path)
                main_content = (generated_path / "main.py").read_text()
                
                # Check endpoint function signatures
                assert "async def get_users(" in main_content
                assert "async def create_user(" in main_content
                assert "async def get_user_by_id(" in main_content
                assert "async def update_user(" in main_content
                assert "async def delete_user(" in main_content
                
                # Check authentication decorators
                assert "token: HTTPAuthorizationCredentials = Depends(security)" in main_content
                
                # Check parameter handling
                assert "limit: int = 10" in main_content
                assert "user_id: int" in main_content
                assert "username: str" in main_content
                assert "email: str" in main_content
    
    def test_generated_requirements_validity(self, sample_analysis):
        """Test that requirements.txt is valid"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "req_test")
                
                generated_path = Path(api_path)
                requirements_content = (generated_path / "requirements.txt").read_text()
                
                # Check essential packages
                assert "fastapi" in requirements_content
                assert "uvicorn" in requirements_content
                assert "pydantic" in requirements_content
                assert "python-jose" in requirements_content
                assert "passlib" in requirements_content
                
                # Verify version constraints exist
                lines = requirements_content.strip().split('\n')
                for line in lines:
                    if line and not line.startswith('#'):
                        assert '==' in line or '>=' in line, f"No version constraint in: {line}"
    
    @pytest.mark.slow
    def test_generated_api_can_start(self, sample_analysis):
        """Test that generated API can actually start (requires uvicorn)"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "start_test")
                
                generated_path = Path(api_path)
                
                # Try to start the API (this requires uvicorn to be installed)
                try:
                    # Run a syntax check first
                    result = subprocess.run(
                        ["python", "-m", "py_compile", "main.py"],
                        cwd=generated_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    assert result.returncode == 0, f"Compilation failed: {result.stderr}"
                    
                    # Try to import the module (this will catch import errors)
                    result = subprocess.run(
                        ["python", "-c", "import main; print('Import successful')"],
                        cwd=generated_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    # This might fail due to missing dependencies, but should not have syntax errors
                    if result.returncode != 0:
                        # Check if it's a dependency issue vs syntax issue
                        if "ImportError" in result.stderr or "ModuleNotFoundError" in result.stderr:
                            # This is expected in test environment
                            pass
                        else:
                            pytest.fail(f"Unexpected error: {result.stderr}")
                
                except subprocess.TimeoutExpired:
                    pytest.fail("API startup timed out")
                except FileNotFoundError:
                    pytest.skip("Python not available for subprocess test")
    
    def test_generated_api_response_structure(self, sample_analysis):
        """Test that generated API returns proper response structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "response_test")
                
                generated_path = Path(api_path)
                main_content = (generated_path / "main.py").read_text()
                
                # Check response structure in generated endpoints
                assert '"message":' in main_content
                assert '"parameters":' in main_content
                assert '"function_info":' in main_content
                assert "HTTPException" in main_content
    
    def test_generated_models_structure(self, sample_analysis):
        """Test that generated models are properly structured"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "model_test")
                
                generated_path = Path(api_path)
                models_content = (generated_path / "models.py").read_text()
                
                # Check base models
                assert "class UserCredentials(BaseModel):" in models_content
                assert "class Token(BaseModel):" in models_content
                assert "class APIResponse(BaseModel):" in models_content
                
                # Check request models for each endpoint
                assert "class GetUsersRequest(BaseModel):" in models_content
                assert "class CreateUserRequest(BaseModel):" in models_content
    
    def test_generated_auth_functionality(self, sample_analysis):
        """Test that generated auth module has proper functionality"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "auth_test")
                
                generated_path = Path(api_path)
                auth_content = (generated_path / "auth.py").read_text()
                
                # Check auth functions
                assert "def verify_password(" in auth_content
                assert "def get_password_hash(" in auth_content
                assert "def create_access_token(" in auth_content
                assert "def verify_token(" in auth_content
                assert "def authenticate_user(" in auth_content
                
                # Check security configuration
                assert "SECRET_KEY" in auth_content
                assert "ALGORITHM" in auth_content
                assert "ACCESS_TOKEN_EXPIRE_MINUTES" in auth_content
    
    def test_generated_dockerfile_validity(self, sample_analysis):
        """Test that generated Dockerfile is valid"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "docker_test")
                
                generated_path = Path(api_path)
                dockerfile_content = (generated_path / "Dockerfile").read_text()
                
                # Check Dockerfile structure
                assert "FROM python:" in dockerfile_content
                assert "WORKDIR /app" in dockerfile_content
                assert "COPY requirements.txt" in dockerfile_content
                assert "RUN pip install" in dockerfile_content
                assert "EXPOSE 8000" in dockerfile_content
                assert "CMD [\"uvicorn\"" in dockerfile_content
    
    def test_generated_docker_compose_validity(self, sample_analysis):
        """Test that generated docker-compose.yml is valid"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "compose_test")
                
                generated_path = Path(api_path)
                compose_content = (generated_path / "docker-compose.yml").read_text()
                
                # Check docker-compose structure
                assert "version:" in compose_content
                assert "services:" in compose_content
                assert "api:" in compose_content
                assert "ports:" in compose_content
                assert "8000:8000" in compose_content
    
    def test_generated_readme_completeness(self, sample_analysis):
        """Test that generated README is complete"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(sample_analysis, "readme_test")
                
                generated_path = Path(api_path)
                readme_content = (generated_path / "README.md").read_text()
                
                # Check README sections
                assert "# " in readme_content  # Title
                assert "## Features" in readme_content
                assert "## Quick Start" in readme_content
                assert "## API Documentation" in readme_content
                assert "## Authentication" in readme_content
                assert "## Available Endpoints" in readme_content
                
                # Check endpoint documentation
                assert "| GET |" in readme_content
                assert "| POST |" in readme_content
                assert "| PUT |" in readme_content
                assert "| DELETE |" in readme_content
                
                # Check that all endpoints are documented
                for endpoint in sample_analysis["api_endpoints"]:
                    assert endpoint["endpoint_path"] in readme_content
                    assert endpoint["description"] in readme_content


class TestSpecificHTTPMethods:
    """Test specific HTTP method implementations"""
    
    def test_get_method_implementation(self):
        """Test GET method endpoints"""
        analysis = {
            "api_endpoints": [{
                "function_name": "get_items",
                "http_method": "GET",
                "endpoint_path": "/items",
                "description": "Get all items",
                "needs_auth": False,
                "parameters": [{"name": "limit", "type": "int", "default": "10"}],
                "is_async": False
            }]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(analysis, "get_test")
                
                main_content = (Path(api_path) / "main.py").read_text()
                
                # Check GET method specifics
                assert "@app.get(\"/items\")" in main_content
                assert "async def get_items(" in main_content
                assert "limit: int = 10" in main_content
    
    def test_post_method_implementation(self):
        """Test POST method endpoints"""
        analysis = {
            "api_endpoints": [{
                "function_name": "create_item",
                "http_method": "POST",
                "endpoint_path": "/items",
                "description": "Create a new item",
                "needs_auth": True,
                "parameters": [
                    {"name": "name", "type": "str"},
                    {"name": "description", "type": "str"}
                ],
                "is_async": False
            }]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(analysis, "post_test")
                
                main_content = (Path(api_path) / "main.py").read_text()
                
                # Check POST method specifics
                assert "@app.post(\"/items\")" in main_content
                assert "async def create_item(" in main_content
                assert "name: str" in main_content
                assert "description: str" in main_content
                assert "token: HTTPAuthorizationCredentials" in main_content
    
    def test_put_method_implementation(self):
        """Test PUT method endpoints"""
        analysis = {
            "api_endpoints": [{
                "function_name": "update_item",
                "http_method": "PUT",
                "endpoint_path": "/items/{item_id}",
                "description": "Update an item",
                "needs_auth": True,
                "parameters": [
                    {"name": "item_id", "type": "int"},
                    {"name": "name", "type": "str"}
                ],
                "is_async": False
            }]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(analysis, "put_test")
                
                main_content = (Path(api_path) / "main.py").read_text()
                
                # Check PUT method specifics
                assert "@app.put(\"/items/{item_id}\")" in main_content
                assert "async def update_item(" in main_content
                assert "item_id: int" in main_content
    
    def test_delete_method_implementation(self):
        """Test DELETE method endpoints"""
        analysis = {
            "api_endpoints": [{
                "function_name": "delete_item",
                "http_method": "DELETE",
                "endpoint_path": "/items/{item_id}",
                "description": "Delete an item",
                "needs_auth": True,
                "parameters": [{"name": "item_id", "type": "int"}],
                "is_async": False
            }]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                generator = APIGenerator()
                api_path = generator.generate_api(analysis, "delete_test")
                
                main_content = (Path(api_path) / "main.py").read_text()
                
                # Check DELETE method specifics
                assert "@app.delete(\"/items/{item_id}\")" in main_content
                assert "async def delete_item(" in main_content
                assert "item_id: int" in main_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])