
import pytest
from fastapi.testclient import TestClient
from main import app
import tempfile
import os

@pytest.fixture(scope="session")
def client():
    """Create a test client for the FastAPI app"""
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(scope="session")
def auth_token(client):
    """Get authentication token for tests"""
    login_data = {"username": "demo", "password": "secret"}
    response = client.post("/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

@pytest.fixture
def auth_headers(auth_token):
    """Get authorization headers"""
    if auth_token:
        return {"Authorization": f"Bearer {auth_token}"}
    return {}

@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

class TestHelpers:
    """Helper functions for tests"""
    
    @staticmethod
    def assert_valid_response(response, expected_status=200):
        """Assert response is valid and has expected status"""
        assert response.status_code == expected_status
        if expected_status < 400:
            # Success responses should have valid JSON
            data = response.json()
            assert isinstance(data, (dict, list))
    
    @staticmethod
    def assert_error_response(response, expected_status=400):
        """Assert response is a valid error response"""
        assert response.status_code == expected_status
        data = response.json()
        assert "error" in data or "detail" in data
