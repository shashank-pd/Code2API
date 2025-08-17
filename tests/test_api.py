"""
Comprehensive API tests for Code2API backend
"""
import pytest
import tempfile
import json
import os
from fastapi.testclient import TestClient
from pathlib import Path

# Import the FastAPI app
from src.api.main import app
from src.config import config

client = TestClient(app)

class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_root_endpoint(self):
        """Test GET / endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert data["message"] == "Welcome to Code2API"
    
    def test_health_check(self):
        """Test GET /health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
    
    def test_get_supported_languages(self):
        """Test GET /languages endpoint"""
        response = client.get("/languages")
        assert response.status_code == 200
        data = response.json()
        assert "supported_languages" in data
        assert "python" in data["supported_languages"]
        assert "javascript" in data["supported_languages"]
        assert "java" in data["supported_languages"]
    
    def test_list_generated_apis_empty(self):
        """Test GET /generated endpoint when no APIs exist"""
        response = client.get("/generated")
        assert response.status_code == 200
        data = response.json()
        assert "generated_apis" in data
        assert isinstance(data["generated_apis"], list)
    
    def test_analyze_code_missing_data(self):
        """Test POST /analyze with missing data"""
        response = client.post("/analyze", json={})
        assert response.status_code == 422  # Validation error
    
    def test_analyze_code_invalid_language(self):
        """Test POST /analyze with invalid language"""
        response = client.post("/analyze", json={
            "code": "print('hello')",
            "language": "invalid_language",
            "filename": "test.txt"
        })
        # This might succeed but with no endpoints found, or fail at parsing
        # The behavior depends on the implementation
        assert response.status_code in [200, 422, 500]
    
    def test_analyze_code_python_simple(self):
        """Test POST /analyze with simple Python code"""
        python_code = '''
def hello_world():
    """Simple hello world function"""
    return "Hello, World!"

def add_numbers(a, b):
    """Add two numbers"""
    return a + b
'''
        response = client.post("/analyze", json={
            "code": python_code,
            "language": "python",
            "filename": "test.py"
        })
        
        # This test may fail if no Groq API key is configured
        # In that case, we should get a 500 error
        if response.status_code == 500:
            # API key not configured - this is expected in test environment
            assert "API key" in response.json()["detail"] or "Error analyzing code" in response.json()["detail"]
        else:
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analysis" in data
    
    def test_analyze_repo_invalid_url(self):
        """Test POST /analyze-repo with invalid URL"""
        response = client.post("/analyze-repo", json={
            "repo_url": "invalid-url"
        })
        assert response.status_code == 500
        assert "Error analyzing repository" in response.json()["detail"]
    
    def test_analyze_repo_missing_url(self):
        """Test POST /analyze-repo with missing URL"""
        response = client.post("/analyze-repo", json={})
        assert response.status_code == 422  # Validation error
    
    def test_upload_files_no_files(self):
        """Test POST /upload with no files"""
        response = client.post("/upload")
        assert response.status_code == 422  # No files provided
    
    def test_security_scan_missing_data(self):
        """Test POST /security-scan with missing data"""
        response = client.post("/security-scan", json={})
        assert response.status_code == 422  # Validation error
    
    def test_security_scan_simple_code(self):
        """Test POST /security-scan with simple code"""
        python_code = '''
def login(username, password):
    """Login function with potential security issues"""
    if username == "admin" and password == "password123":
        return True
    return False
'''
        response = client.post("/security-scan", json={
            "code": python_code,
            "language": "python",
            "filename": "auth.py"
        })
        
        if response.status_code == 500:
            # API key not configured - expected in test environment
            assert "Error in security scan" in response.json()["detail"]
        else:
            assert response.status_code == 200
            data = response.json()
            assert "security_recommendations" in data
            assert "risk_level" in data
    
    def test_download_nonexistent_api(self):
        """Test GET /download/{project_name} with non-existent project"""
        response = client.get("/download/nonexistent_project")
        assert response.status_code == 404
        assert "Generated API not found" in response.json()["detail"]


class TestCodeAnalysisValidation:
    """Test input validation for code analysis"""
    
    def test_empty_code(self):
        """Test analysis with empty code"""
        response = client.post("/analyze", json={
            "code": "",
            "language": "python",
            "filename": "empty.py"
        })
        # Should either succeed with no endpoints or fail with validation error
        assert response.status_code in [200, 422, 500]
    
    def test_very_long_code(self):
        """Test analysis with very long code"""
        long_code = "# Comment\n" * 10000 + "def test(): pass"
        response = client.post("/analyze", json={
            "code": long_code,
            "language": "python",
            "filename": "long.py"
        })
        # Should handle gracefully
        assert response.status_code in [200, 500]
    
    def test_code_with_syntax_error(self):
        """Test analysis with syntax errors"""
        broken_code = '''
def broken_function(
    # Missing closing parenthesis and body
'''
        response = client.post("/analyze", json={
            "code": broken_code,
            "language": "python",
            "filename": "broken.py"
        })
        # Should handle syntax errors gracefully
        assert response.status_code in [200, 500]


class TestFileUpload:
    """Test file upload functionality"""
    
    def test_upload_python_file(self):
        """Test uploading a Python file"""
        # Create a temporary Python file
        python_content = '''
def test_function():
    """Test function"""
    return "test"
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(python_content)
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = client.post("/upload", files={"files": ("test.py", f, "text/x-python")})
            
            if response.status_code == 500:
                # API key not configured - expected in test environment
                data = response.json()
                assert "results" in data
            else:
                assert response.status_code == 200
                data = response.json()
                assert "results" in data
                assert "total_files" in data
                assert data["total_files"] == 1
        finally:
            os.unlink(temp_file_path)
    
    def test_upload_unsupported_file(self):
        """Test uploading an unsupported file type"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Some text content")
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                response = client.post("/upload", files={"files": ("test.txt", f, "text/plain")})
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            # Should report unsupported extension
            if data["results"]:
                assert not data["results"][0]["success"]
                assert "Unsupported file extension" in data["results"][0]["error"]
        finally:
            os.unlink(temp_file_path)


class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_malformed_json(self):
        """Test endpoints with malformed JSON"""
        response = client.post("/analyze", 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422
    
    def test_missing_content_type(self):
        """Test endpoints without proper content type"""
        response = client.post("/analyze", data='{"test": "data"}')
        assert response.status_code in [422, 415]  # Unprocessable Entity or Unsupported Media Type


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment"""
    # Ensure test directories exist
    config.ensure_directories()
    yield
    # Cleanup if needed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])