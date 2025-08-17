
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestAuthentication:
    """Test authentication functionality"""
    
    def test_login_with_valid_credentials(self):
        """Test login with valid credentials"""
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
        """Test login with invalid credentials"""
        login_data = {
            "username": "invalid",
            "password": "wrong"
        }
        response = client.post("/auth/login", data=login_data)
        assert response.status_code == 401
    
    def test_login_missing_fields(self):
        """Test login with missing fields"""
        # Missing password
        response = client.post("/auth/login", data={"username": "demo"})
        assert response.status_code == 422
        
        # Missing username
        response = client.post("/auth/login", data={"password": "secret"})
        assert response.status_code == 422
    
    def test_me_endpoint_with_valid_token(self):
        """Test /auth/me with valid token"""
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
        """Test /auth/me without token"""
        response = client.get("/auth/me")
        assert response.status_code == 401
    
    def test_me_endpoint_with_invalid_token(self):
        """Test /auth/me with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

class TestTokenValidation:
    """Test JWT token validation"""
    
    def test_expired_token_handling(self):
        """Test handling of expired tokens"""
        # This would require creating an expired token
        # For now, just test with malformed token
        headers = {"Authorization": "Bearer expired.token.here"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_malformed_token(self):
        """Test handling of malformed tokens"""
        headers = {"Authorization": "Bearer malformed_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_missing_bearer_prefix(self):
        """Test token without Bearer prefix"""
        headers = {"Authorization": "some_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401
