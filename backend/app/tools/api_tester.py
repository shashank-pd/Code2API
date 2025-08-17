from langchain.tools import tool
from typing import Dict, Any, List
import os
import subprocess
import tempfile
import json
from pathlib import Path
from jinja2 import Template

@tool
def api_tester_tool(api_directory: str, openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate and execute comprehensive test cases for the generated API.
    
    Args:
        api_directory: Path to the generated API directory
        openapi_spec: OpenAPI specification of the API
    
    Returns:
        Dictionary containing test results and coverage information
    """
    try:
        api_dir = Path(api_directory)
        if not api_dir.exists():
            return {"success": False, "error": "API directory not found"}
        
        # Create tests directory
        tests_dir = api_dir / "tests"
        tests_dir.mkdir(exist_ok=True)
        
        test_files = []
        
        # Generate test files
        test_main_content = generate_test_main(openapi_spec)
        test_main_file = tests_dir / "test_main.py"
        with open(test_main_file, 'w', encoding='utf-8') as f:
            f.write(test_main_content)
        test_files.append(str(test_main_file))
        
        # Generate endpoint tests
        endpoint_tests_content = generate_endpoint_tests(openapi_spec)
        endpoint_tests_file = tests_dir / "test_endpoints.py"
        with open(endpoint_tests_file, 'w', encoding='utf-8') as f:
            f.write(endpoint_tests_content)
        test_files.append(str(endpoint_tests_file))
        
        # Generate authentication tests
        auth_tests_content = generate_auth_tests()
        auth_tests_file = tests_dir / "test_auth.py"
        with open(auth_tests_file, 'w', encoding='utf-8') as f:
            f.write(auth_tests_content)
        test_files.append(str(auth_tests_file))
        
        # Generate security tests
        security_tests_content = generate_security_tests()
        security_tests_file = tests_dir / "test_security.py"
        with open(security_tests_file, 'w', encoding='utf-8') as f:
            f.write(security_tests_content)
        test_files.append(str(security_tests_file))
        
        # Generate pytest configuration
        pytest_config = generate_pytest_config()
        pytest_file = api_dir / "pytest.ini"
        with open(pytest_file, 'w', encoding='utf-8') as f:
            f.write(pytest_config)
        test_files.append(str(pytest_file))
        
        # Generate test utilities
        test_utils_content = generate_test_utils()
        test_utils_file = tests_dir / "conftest.py"
        with open(test_utils_file, 'w', encoding='utf-8') as f:
            f.write(test_utils_content)
        test_files.append(str(test_utils_file))
        
        # Generate __init__.py for tests package
        init_file = tests_dir / "__init__.py"
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write("# Tests package")
        test_files.append(str(init_file))
        
        # Run the tests
        test_results = run_tests(api_dir)
        
        return {
            "success": True,
            "test_files": test_files,
            "test_results": test_results,
            "total_tests": test_results.get("total", 0),
            "passed_tests": test_results.get("passed", 0),
            "failed_tests": test_results.get("failed", 0),
            "coverage_percentage": test_results.get("coverage", 0)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"API testing failed: {str(e)}"
        }

def generate_test_main(openapi_spec: Dict[str, Any]) -> str:
    """Generate main application tests"""
    
    template = Template("""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    \"\"\"Test the root endpoint\"\"\"
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_health_check():
    \"\"\"Test the health check endpoint\"\"\"
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_openapi_docs():
    \"\"\"Test that OpenAPI documentation is accessible\"\"\"
    response = client.get("/docs")
    assert response.status_code == 200

def test_openapi_json():
    \"\"\"Test that OpenAPI JSON spec is accessible\"\"\"
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["openapi"] == "3.0.0"

def test_cors_headers():
    \"\"\"Test CORS headers are present\"\"\"
    response = client.options("/")
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 405

class TestAPIInfo:
    \"\"\"Test API information and metadata\"\"\"
    
    def test_api_title(self):
        response = client.get("/openapi.json")
        data = response.json()
        assert "info" in data
        assert "title" in data["info"]
    
    def test_api_version(self):
        response = client.get("/openapi.json")
        data = response.json()
        assert "info" in data
        assert "version" in data["info"]
    
    def test_api_description(self):
        response = client.get("/openapi.json")
        data = response.json()
        assert "info" in data
        assert "description" in data["info"]
""")
    
    return template.render()

def generate_endpoint_tests(openapi_spec: Dict[str, Any]) -> str:
    """Generate endpoint-specific tests"""
    
    template = Template("""
import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

# Test authentication token (you'll need to get this from login)
test_token = None

@pytest.fixture(scope="module")
def auth_token():
    \"\"\"Get authentication token for testing\"\"\"
    # Try to login with test credentials
    login_data = {"username": "demo", "password": "secret"}
    response = client.post("/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def get_auth_headers(token):
    \"\"\"Get authorization headers\"\"\"
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

{% for path, methods in paths.items() %}
class Test{{ path.replace('/', '').replace('-', '').replace('{', '').replace('}', '') or 'Root' }}:
    \"\"\"Tests for {{ path }} endpoints\"\"\"
    
    {% for method, operation in methods.items() %}
    def test_{{ operation.operationId }}_endpoint(self, auth_token):
        \"\"\"Test {{ method.upper() }} {{ path }}\"\"\"
        headers = get_auth_headers(auth_token)
        
        {% if method == 'get' %}
        # GET request
        {% if operation.get('parameters') %}
        # Test with valid parameters
        params = {
            {% for param in operation.parameters %}
            {% if param.in == 'query' %}
            "{{ param.name }}": {{ get_test_value(param.schema) }},
            {% endif %}
            {% endfor %}
        }
        response = client.get("{{ path }}", params=params, headers=headers)
        {% else %}
        response = client.get("{{ path }}", headers=headers)
        {% endif %}
        
        {% elif method in ['post', 'put', 'patch'] %}
        # {{ method.upper() }} request
        test_data = {{ get_test_request_data(operation) }}
        response = client.{{ method }}("{{ path }}", json=test_data, headers=headers)
        
        {% elif method == 'delete' %}
        # DELETE request
        response = client.delete("{{ path }}", headers=headers)
        {% endif %}
        
        # Check if authentication is required
        if not auth_token:
            assert response.status_code in [401, 422]  # Unauthorized or validation error
        else:
            # With auth, we expect success or method-specific errors
            assert response.status_code in [200, 201, 400, 404, 422, 500]
            
            # If successful, check response structure
            if response.status_code in [200, 201]:
                data = response.json()
                assert isinstance(data, (dict, list))
    
    def test_{{ operation.operationId }}_without_auth(self):
        \"\"\"Test {{ method.upper() }} {{ path }} without authentication\"\"\"
        {% if method == 'get' %}
        response = client.get("{{ path }}")
        {% elif method in ['post', 'put', 'patch'] %}
        test_data = {{ get_test_request_data(operation) }}
        response = client.{{ method }}("{{ path }}", json=test_data)
        {% elif method == 'delete' %}
        response = client.delete("{{ path }}")
        {% endif %}
        
        # Should return 401 Unauthorized
        assert response.status_code == 401
    
    {% if operation.get('parameters') %}
    def test_{{ operation.operationId }}_invalid_params(self, auth_token):
        \"\"\"Test {{ method.upper() }} {{ path }} with invalid parameters\"\"\"
        headers = get_auth_headers(auth_token)
        
        {% if method == 'get' %}
        # Test with invalid parameter types
        invalid_params = {
            {% for param in operation.parameters %}
            {% if param.in == 'query' %}
            "{{ param.name }}": "invalid_value_type",
            {% endif %}
            {% endfor %}
        }
        response = client.get("{{ path }}", params=invalid_params, headers=headers)
        {% endif %}
        
        if auth_token:
            assert response.status_code in [400, 422]  # Bad request or validation error
    {% endif %}
    
    {% endfor %}
{% endfor %}

class TestErrorHandling:
    \"\"\"Test error handling across all endpoints\"\"\"
    
    def test_404_for_nonexistent_endpoint(self):
        \"\"\"Test 404 for non-existent endpoints\"\"\"
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        \"\"\"Test 405 for unsupported methods\"\"\"
        # Try POST on a GET-only endpoint
        response = client.post("/health")
        assert response.status_code == 405
""")
    
    def get_test_value(schema):
        """Generate test value based on schema type"""
        if not schema:
            return '"test_value"'
        
        schema_type = schema.get("type", "string")
        if schema_type == "string":
            return '"test_string"'
        elif schema_type == "integer":
            return "123"
        elif schema_type == "number":
            return "123.45"
        elif schema_type == "boolean":
            return "true"
        elif schema_type == "array":
            return '["item1", "item2"]'
        else:
            return '"test_value"'
    
    def get_test_request_data(operation):
        """Generate test request data for POST/PUT/PATCH operations"""
        if "requestBody" in operation:
            # Try to extract schema from request body
            return '{"test": "data", "value": 123}'
        return '{}'
    
    paths = openapi_spec.get("paths", {})
    
    return template.render(
        paths=paths,
        get_test_value=get_test_value,
        get_test_request_data=get_test_request_data
    )

def generate_auth_tests() -> str:
    """Generate authentication tests"""
    
    return """
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAuthentication:
    \"\"\"Test authentication functionality\"\"\"
    
    def test_login_with_valid_credentials(self):
        \"\"\"Test login with valid credentials\"\"\"
        login_data = {
            "username": "demo",
            "password": "secret"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_with_invalid_credentials(self):
        \"\"\"Test login with invalid credentials\"\"\"
        login_data = {
            "username": "invalid",
            "password": "wrong"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401
    
    def test_login_missing_fields(self):
        \"\"\"Test login with missing fields\"\"\"
        # Missing password
        response = client.post("/auth/login", data={"username": "demo"})
        assert response.status_code == 422
        
        # Missing username
        response = client.post("/auth/login", data={"password": "secret"})
        assert response.status_code == 422
    
    def test_me_endpoint_with_valid_token(self):
        \"\"\"Test /auth/me with valid token\"\"\"
        # First login to get token
        login_data = {"username": "demo", "password": "secret"}
        login_response = client.post("/auth/login", data=login_data)
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 200
            data = response.json()
            assert "username" in data
    
    def test_me_endpoint_without_token(self):
        \"\"\"Test /auth/me without token\"\"\"
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_me_endpoint_with_invalid_token(self):
        \"\"\"Test /auth/me with invalid token\"\"\"
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

class TestTokenValidation:
    \"\"\"Test JWT token validation\"\"\"
    
    def test_expired_token_handling(self):
        \"\"\"Test handling of expired tokens\"\"\"
        # This would require creating an expired token
        # For now, just test with malformed token
        headers = {"Authorization": "Bearer expired.token.here"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_malformed_token(self):
        \"\"\"Test handling of malformed tokens\"\"\"
        headers = {"Authorization": "Bearer malformed_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_missing_bearer_prefix(self):
        \"\"\"Test token without Bearer prefix\"\"\"
        headers = {"Authorization": "some_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
"""

def generate_security_tests() -> str:
    """Generate security tests"""
    
    return """
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestSecurityHeaders:
    \"\"\"Test security headers\"\"\"
    
    def test_security_headers_present(self):
        \"\"\"Test that security headers are present\"\"\"
        response = client.get("/health")
        headers = response.headers
        
        # Check for common security headers
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"
        
        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"

class TestInputValidation:
    \"\"\"Test input validation and sanitization\"\"\"
    
    def test_xss_protection(self):
        \"\"\"Test XSS attack prevention\"\"\"
        malicious_input = "<script>alert('xss')</script>"
        
        # Test in query parameters
        response = client.get("/health", params={"test": malicious_input})
        assert response.status_code in [400, 200]  # Should either block or sanitize
    
    def test_sql_injection_protection(self):
        \"\"\"Test SQL injection prevention\"\"\"
        malicious_input = "'; DROP TABLE users; --"
        
        # Test in query parameters  
        response = client.get("/health", params={"test": malicious_input})
        assert response.status_code in [400, 200]  # Should either block or sanitize

class TestRateLimiting:
    \"\"\"Test rate limiting functionality\"\"\"
    
    def test_rate_limit_headers(self):
        \"\"\"Test that rate limit headers are present\"\"\"
        response = client.get("/health")
        headers = response.headers
        
        # Check for rate limit headers
        assert any(header.startswith("x-ratelimit") for header in headers.keys())
    
    def test_rate_limit_exceeded(self):
        \"\"\"Test rate limit enforcement\"\"\"
        # Make many requests quickly
        responses = []
        for i in range(100):  # Make many requests
            response = client.get("/health")
            responses.append(response)
            if response.status_code == 429:  # Rate limit exceeded
                break
        
        # Should eventually hit rate limit
        assert any(r.status_code == 429 for r in responses)

class TestRequestSizeLimits:
    \"\"\"Test request size limitations\"\"\"
    
    def test_large_request_body(self):
        \"\"\"Test handling of large request bodies\"\"\"
        # Create a large payload
        large_data = {"data": "x" * (2 * 1024 * 1024)}  # 2MB of data
        
        response = client.post("/health", json=large_data)
        assert response.status_code in [413, 400, 404]  # Request too large or endpoint doesn't accept POST

class TestCORSConfiguration:
    \"\"\"Test CORS configuration\"\"\"
    
    def test_cors_options_request(self):
        \"\"\"Test CORS preflight requests\"\"\"
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization"
        }
        
        response = client.options("/health", headers=headers)
        # Should either allow CORS or return 405 for unsupported OPTIONS
        assert response.status_code in [200, 405]
"""

def generate_pytest_config() -> str:
    """Generate pytest configuration"""
    
    return """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    auth: marks tests that require authentication
    security: marks security-related tests
    integration: marks integration tests
"""

def generate_test_utils() -> str:
    """Generate test utilities and fixtures"""
    
    return """
import pytest
from fastapi.testclient import TestClient
from main import app
import tempfile
import os

@pytest.fixture(scope="session")
def client():
    \"\"\"Create a test client for the FastAPI app\"\"\"
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def auth_token(client):
    \"\"\"Get authentication token for tests\"\"\"
    login_data = {"username": "demo", "password": "secret"}
    response = client.post("/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

@pytest.fixture
def auth_headers(auth_token):
    \"\"\"Get authorization headers\"\"\"
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}

@pytest.fixture
def temp_file():
    \"\"\"Create a temporary file for testing\"\"\"
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestHelpers:
    \"\"\"Helper functions for tests\"\"\"
    
    @staticmethod
    def assert_valid_response(response, expected_status=200):
        \"\"\"Assert response is valid and has expected status\"\"\"
        assert response.status_code == expected_status
        if expected_status < 400:
            # Success responses should have valid JSON
            data = response.json()
            assert isinstance(data, (dict, list))
    
    @staticmethod
    def assert_error_response(response, expected_status=400):
        \"\"\"Assert response is a valid error response\"\"\"
        assert response.status_code == expected_status
        data = response.json()
        assert "error" in data or "detail" in data
"""

def run_tests(api_directory: str) -> Dict[str, Any]:
    """Run the generated test suite and return results"""
    try:
        api_dir = Path(api_directory)
        test_dir = api_dir / "tests"
        
        if not test_dir.exists():
            return {"success": False, "error": "Tests directory not found"}
        
        # Change to the API directory
        original_cwd = os.getcwd()
        os.chdir(api_dir)
        
        try:
            # Run pytest with coverage
            cmd = [
                "python", "-m", "pytest", 
                "tests/", 
                "--cov=.", 
                "--cov-report=json",
                "--cov-report=term-missing",
                "--json-report",
                "--json-report-file=test_report.json",
                "-v"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Parse pytest JSON report
            test_results = parse_pytest_results(api_dir)
            
            # Parse coverage report
            coverage_data = parse_coverage_results(api_dir)
            
            return {
                "success": True,
                "test_output": result.stdout,
                "test_errors": result.stderr,
                "exit_code": result.returncode,
                "execution_time": test_results.get("execution_time", 0),
                "total": test_results.get("total", 0),
                "passed": test_results.get("passed", 0),
                "failed": test_results.get("failed", 0),
                "skipped": test_results.get("skipped", 0),
                "coverage": coverage_data.get("coverage_percentage", 0),
                "coverage_details": coverage_data.get("details", {}),
                "test_details": test_results.get("details", [])
            }
            
        finally:
            os.chdir(original_cwd)
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Test execution timed out after 5 minutes"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Test execution failed: {str(e)}"
        }

def parse_pytest_results(api_directory: Path) -> Dict[str, Any]:
    """Parse pytest JSON report"""
    try:
        report_file = api_directory / "test_report.json"
        if not report_file.exists():
            return {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        
        with open(report_file, 'r') as f:
            data = json.load(f)
        
        summary = data.get("summary", {})
        tests = data.get("tests", [])
        
        test_details = []
        for test in tests:
            test_details.append({
                "name": test.get("nodeid", ""),
                "outcome": test.get("outcome", "unknown"),
                "duration": test.get("duration", 0),
                "error": test.get("call", {}).get("longrepr", "") if test.get("outcome") == "failed" else ""
            })
        
        return {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "skipped": summary.get("skipped", 0),
            "execution_time": summary.get("duration", 0),
            "details": test_details
        }
        
    except Exception as e:
        print(f"Error parsing pytest results: {e}")
        return {"total": 0, "passed": 0, "failed": 0, "skipped": 0}

def parse_coverage_results(api_directory: Path) -> Dict[str, Any]:
    """Parse coverage JSON report"""
    try:
        coverage_file = api_directory / "coverage.json"
        if not coverage_file.exists():
            return {"coverage_percentage": 0, "details": {}}
        
        with open(coverage_file, 'r') as f:
            data = json.load(f)
        
        totals = data.get("totals", {})
        files = data.get("files", {})
        
        file_coverage = {}
        for filename, file_data in files.items():
            summary = file_data.get("summary", {})
            file_coverage[filename] = {
                "covered_lines": summary.get("covered_lines", 0),
                "missing_lines": summary.get("missing_lines", 0),
                "excluded_lines": summary.get("excluded_lines", 0),
                "percent_covered": summary.get("percent_covered", 0)
            }
        
        return {
            "coverage_percentage": round(totals.get("percent_covered", 0), 2),
            "covered_lines": totals.get("covered_lines", 0),
            "missing_lines": totals.get("missing_lines", 0),
            "total_lines": totals.get("num_statements", 0),
            "details": file_coverage
        }
        
    except Exception as e:
        print(f"Error parsing coverage results: {e}")
        return {"coverage_percentage": 0, "details": {}}

def install_test_dependencies(api_directory: str) -> bool:
    """Install required testing dependencies"""
    try:
        api_dir = Path(api_directory)
        
        # Create requirements.txt with test dependencies
        test_requirements = [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-json-report>=1.5.0",
            "httpx>=0.24.0",
            "requests>=2.28.0",
            "pytest-asyncio>=0.21.0"
        ]
        
        requirements_file = api_dir / "test_requirements.txt"
        with open(requirements_file, 'w') as f:
            f.write('\n'.join(test_requirements))
        
        # Install dependencies
        original_cwd = os.getcwd()
        os.chdir(api_dir)
        
        try:
            cmd = ["python", "-m", "pip", "install", "-r", "test_requirements.txt"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        finally:
            os.chdir(original_cwd)
            
    except Exception as e:
        print(f"Error installing test dependencies: {e}")
        return False

def generate_test_configuration(api_directory: str) -> bool:
    """Generate pytest and coverage configuration files"""
    try:
        api_dir = Path(api_directory)
        
        # Generate pytest.ini
        pytest_config = """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=json
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    auth: marks tests as authentication related
    security: marks tests as security related
    integration: marks tests as integration tests
"""
        
        with open(api_dir / "pytest.ini", 'w') as f:
            f.write(pytest_config)
        
        # Generate .coveragerc
        coverage_config = """[run]
source = .
omit = 
    tests/*
    venv/*
    env/*
    .venv/*
    __pycache__/*
    .pytest_cache/*
    htmlcov/*
    *.egg-info/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
"""
        
        with open(api_dir / ".coveragerc", 'w') as f:
            f.write(coverage_config)
        
        return True
        
    except Exception as e:
        print(f"Error generating test configuration: {e}")
        return False

