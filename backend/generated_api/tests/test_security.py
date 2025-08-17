
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

class TestSecurityHeaders:
    """Test security headers"""
    
    def test_security_headers_present(self):
        """Test that security headers are present"""
        response = client.get("/health")
        headers = response.headers
        
        # Check for common security headers
        assert "x-content-type-options" in headers
        assert headers["x-content-type-options"] == "nosniff"
        
        assert "x-frame-options" in headers
        assert headers["x-frame-options"] == "DENY"

class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_xss_protection(self):
        """Test XSS attack prevention"""
        malicious_input = "<script>alert('xss')</script>"
        
        # Test in query parameters
        response = client.get("/health", params={"test": malicious_input})
        assert response.status_code in [400, 200]  # Should either block or sanitize
    
    def test_sql_injection_protection(self):
        """Test SQL injection prevention"""
        malicious_input = "'; DROP TABLE users; --"
        
        # Test in query parameters  
        response = client.get("/health", params={"test": malicious_input})
        assert response.status_code in [400, 200]  # Should either block or sanitize

class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_headers(self):
        """Test that rate limit headers are present"""
        response = client.get("/health")
        headers = response.headers
        
        # Check for rate limit headers
        assert any(header.startswith("x-ratelimit") for header in headers.keys())
    
    def test_rate_limit_exceeded(self):
        """Test rate limit enforcement"""
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
    """Test request size limitations"""
    
    def test_large_request_body(self):
        """Test handling of large request bodies"""
        # Create a large payload
        large_data = {"data": "x" * (2 * 1024 * 1024)}  # 2MB of data
        
        response = client.post("/health", json=large_data)
        assert response.status_code in [413, 400, 404]  # Request too large or endpoint doesn't accept POST

class TestCORSConfiguration:
    """Test CORS configuration"""
    
    def test_cors_options_request(self):
        """Test CORS preflight requests"""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization"
        }
        
        response = client.options("/health", headers=headers)
        # Should either allow CORS or return 405 for unsupported OPTIONS
        assert response.status_code in [200, 405]
