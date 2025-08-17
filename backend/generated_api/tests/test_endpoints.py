
import pytest
from fastapi.testclient import TestClient
from main import app
import json

client = TestClient(app)

# Test authentication token (you'll need to get this from login)
test_token = None

@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token for testing"""
    # Try to login with test credentials
    login_data = {"username": "demo", "password": "secret"}
    response = client.post("/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def get_auth_headers(token):
    """Get authorization headers"""
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}



class TestErrorHandling:
    """Test error handling across all endpoints"""
    
    def test_404_for_nonexistent_endpoint(self):
        """Test 404 for non-existent endpoints"""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test 405 for unsupported methods"""
        # Try POST on a GET-only endpoint
        response = client.post("/health")
        assert response.status_code == 405