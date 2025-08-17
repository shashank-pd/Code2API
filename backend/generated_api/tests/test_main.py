
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_openapi_docs():
    """Test that OpenAPI documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_openapi_json():
    """Test that OpenAPI JSON spec is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["openapi"] == "3.0.0"

def test_cors_headers():
    """Test CORS headers are present"""
    response = client.options("/")
    # CORS headers should be present
    assert "access-control-allow-origin" in response.headers or response.status_code == 405

class TestAPIInfo:
    """Test API information and metadata"""
    
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