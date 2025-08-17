"""
Tests for the API generator module
"""
import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.generators.api_generator import APIGenerator
from src.config import config


class TestAPIGenerator:
    """Test API generation functionality"""
    
    def setup_method(self):
        """Setup test generator"""
        self.generator = APIGenerator()
    
    def test_initialization(self):
        """Test generator initialization"""
        assert self.generator is not None
        assert hasattr(self.generator, 'template_env')
    
    def test_generate_api_basic(self):
        """Test basic API generation"""
        # Sample analysis data
        analysis = {
            "api_endpoints": [
                {
                    "function_name": "test_function",
                    "http_method": "GET",
                    "endpoint_path": "/test",
                    "description": "Test endpoint",
                    "needs_auth": False,
                    "parameters": [{"name": "param1", "type": "str"}],
                    "is_async": False
                }
            ],
            "security_recommendations": ["Use HTTPS"],
            "optimization_suggestions": ["Add caching"]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                result_path = self.generator.generate_api(analysis, "test_project")
                
                # Check that files were generated
                generated_path = Path(result_path)
                assert generated_path.exists()
                assert (generated_path / "main.py").exists()
                assert (generated_path / "models.py").exists()
                assert (generated_path / "auth.py").exists()
                assert (generated_path / "requirements.txt").exists()
                assert (generated_path / "README.md").exists()
                assert (generated_path / "Dockerfile").exists()
                assert (generated_path / "docker-compose.yml").exists()
    
    def test_generate_main_file(self):
        """Test main API file generation"""
        analysis = {
            "api_endpoints": [
                {
                    "function_name": "get_users",
                    "http_method": "GET",
                    "endpoint_path": "/users",
                    "description": "Get all users",
                    "needs_auth": True,
                    "parameters": [{"name": "limit", "type": "int", "default": "10"}],
                    "is_async": True
                },
                {
                    "function_name": "create_user",
                    "http_method": "POST",
                    "endpoint_path": "/users",
                    "description": "Create a new user",
                    "needs_auth": True,
                    "parameters": [{"name": "username", "type": "str"}, {"name": "email", "type": "str"}],
                    "is_async": False
                }
            ]
        }
        
        result = self.generator._generate_main_file(analysis, "test_api")
        
        # Check that the generated code contains expected elements
        assert "from fastapi import FastAPI" in result
        assert "from models import *" in result
        assert "from auth import verify_token" in result
        assert 'title="Test_api API"' in result
        assert "@app.get(\"/users\")" in result
        assert "@app.post(\"/users\")" in result
        assert "async def get_users" in result
        assert "def create_user" in result
        assert "verify_token(token.credentials)" in result  # Auth check
    
    def test_generate_models_file(self):
        """Test models file generation"""
        analysis = {
            "api_endpoints": [
                {
                    "function_name": "test_function",
                    "parameters": [
                        {"name": "param1", "type": "str"},
                        {"name": "param2", "type": "int", "default": "0"}
                    ]
                }
            ]
        }
        
        result = self.generator._generate_models_file(analysis)
        
        # Check that Pydantic models are generated
        assert "from pydantic import BaseModel" in result
        assert "class UserCredentials(BaseModel):" in result
        assert "class Token(BaseModel):" in result
        assert "class APIResponse(BaseModel):" in result
        assert "class TestFunctionRequest(BaseModel):" in result
    
    def test_generate_auth_file(self):
        """Test authentication file generation"""
        analysis = {"api_endpoints": []}
        
        result = self.generator._generate_auth_file(analysis)
        
        # Check that auth components are present
        assert "from jose import JWTError, jwt" in result
        assert "from passlib.context import CryptContext" in result
        assert "def verify_password" in result
        assert "def create_access_token" in result
        assert "def verify_token" in result
        assert "fake_users_db" in result
    
    def test_generate_requirements(self):
        """Test requirements file generation"""
        analysis = {
            "api_endpoints": [
                {"is_async": True},
                {"is_async": False}
            ]
        }
        
        result = self.generator._generate_requirements(analysis)
        
        # Check that essential packages are included
        assert "fastapi" in result
        assert "uvicorn" in result
        assert "pydantic" in result
        assert "python-jose" in result
        assert "passlib" in result
        # Should include aiofiles for async endpoints
        assert "aiofiles" in result
    
    def test_generate_readme(self):
        """Test README generation"""
        analysis = {
            "api_endpoints": [
                {
                    "http_method": "GET",
                    "endpoint_path": "/test",
                    "description": "Test endpoint",
                    "needs_auth": False
                },
                {
                    "http_method": "POST",
                    "endpoint_path": "/secure",
                    "description": "Secure endpoint",
                    "needs_auth": True
                }
            ],
            "security_recommendations": ["Use HTTPS", "Validate input"],
            "optimization_suggestions": ["Add caching", "Use async"]
        }
        
        result = self.generator._generate_readme(analysis, "test_project")
        
        # Check README content
        assert "# Test_project API" in result
        assert "2 API endpoints" in result
        assert "Authentication" in result
        assert "Quick Start" in result
        assert "| GET | `/test`" in result
        assert "| POST | `/secure`" in result
        assert "Use HTTPS" in result
        assert "Add caching" in result
    
    def test_generate_dockerfile(self):
        """Test Dockerfile generation"""
        result = self.generator._generate_dockerfile()
        
        # Check Dockerfile content
        assert "FROM python:3.11-slim" in result
        assert "WORKDIR /app" in result
        assert "COPY requirements.txt ." in result
        assert "RUN pip install" in result
        assert "EXPOSE 8000" in result
        assert "CMD [\"uvicorn\", \"main:app\"" in result
    
    def test_generate_docker_compose(self):
        """Test docker-compose.yml generation"""
        result = self.generator._generate_docker_compose("test_project")
        
        # Check docker-compose content
        assert "version: '3.8'" in result
        assert "services:" in result
        assert "api:" in result
        assert "ports:" in result
        assert "- \"8000:8000\"" in result
        assert "test_project_api" in result
    
    def test_generate_api_with_empty_analysis(self):
        """Test API generation with empty analysis"""
        analysis = {
            "api_endpoints": [],
            "security_recommendations": [],
            "optimization_suggestions": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                result_path = self.generator.generate_api(analysis, "empty_project")
                
                # Should still generate all files even with empty analysis
                generated_path = Path(result_path)
                assert generated_path.exists()
                assert (generated_path / "main.py").exists()
                
                # Check that main.py doesn't have endpoint definitions
                main_content = (generated_path / "main.py").read_text()
                assert "def " not in main_content or "health_check" in main_content  # Only health check
    
    def test_generate_api_with_complex_endpoints(self):
        """Test API generation with complex endpoint configurations"""
        analysis = {
            "api_endpoints": [
                {
                    "function_name": "UserManager_create_user",
                    "http_method": "POST",
                    "endpoint_path": "/api/v1/users",
                    "description": "Create a new user account with validation",
                    "needs_auth": True,
                    "parameters": [
                        {"name": "username", "type": "str"},
                        {"name": "email", "type": "str"},
                        {"name": "password", "type": "str"},
                        {"name": "is_admin", "type": "bool", "default": "False"}
                    ],
                    "is_async": True,
                    "class_name": "UserManager",
                    "method_name": "create_user"
                }
            ],
            "security_recommendations": [
                "Hash passwords before storing",
                "Validate email format",
                "Implement rate limiting"
            ],
            "optimization_suggestions": [
                "Use database connection pooling",
                "Add response caching for GET requests"
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                result_path = self.generator.generate_api(analysis, "complex_project")
                
                generated_path = Path(result_path)
                main_content = (generated_path / "main.py").read_text()
                
                # Check complex endpoint generation
                assert "async def UserManager_create_user" in main_content
                assert "@app.post(\"/api/v1/users\")" in main_content
                assert "is_admin: bool = False" in main_content
                assert "class_name\": \"UserManager\"" in main_content
                
                # Check README includes security recommendations
                readme_content = (generated_path / "README.md").read_text()
                assert "Hash passwords before storing" in readme_content
                assert "Use database connection pooling" in readme_content


class TestAPIGeneratorErrorHandling:
    """Test error handling in API generator"""
    
    def setup_method(self):
        """Setup test generator"""
        self.generator = APIGenerator()
    
    def test_generate_api_invalid_project_name(self):
        """Test API generation with invalid project name"""
        analysis = {"api_endpoints": []}
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                # Should handle special characters in project name
                result_path = self.generator.generate_api(analysis, "test-project.with.dots")
                assert Path(result_path).exists()
    
    def test_generate_api_no_write_permission(self):
        """Test API generation when directory is not writable"""
        analysis = {"api_endpoints": []}
        
        # Try to write to a non-existent directory
        with patch.object(config, 'GENERATED_DIR', Path("/non/existent/directory")):
            # Should handle the error gracefully or raise appropriate exception
            with pytest.raises((OSError, FileNotFoundError, PermissionError)):
                self.generator.generate_api(analysis, "test_project")
    
    def test_malformed_analysis_data(self):
        """Test handling of malformed analysis data"""
        # Missing required fields
        malformed_analysis = {
            "api_endpoints": [
                {
                    "function_name": "test",
                    # Missing http_method, endpoint_path, etc.
                }
            ]
        }
        
        # Should handle gracefully without crashing
        try:
            result = self.generator._generate_main_file(malformed_analysis, "test")
            # Should generate something even with missing data
            assert "FastAPI" in result
        except (KeyError, TypeError):
            # Acceptable if it raises an error for malformed data
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])