
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Dict, List
import re

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

class InputValidationMiddleware(BaseHTTPMiddleware):
    """Validate and sanitize input data"""
    
    # Common attack patterns
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>.*?</iframe>',
    ]
    
    SQL_INJECTION_PATTERNS = [
        r'union\s+select',
        r'drop\s+table',
        r'insert\s+into',
        r'delete\s+from',
        r'update\s+.*\s+set',
        r'--',
        r';.*--',
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip validation for certain endpoints
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Validate query parameters
        for key, value in request.query_params.items():
            if self.contains_malicious_content(str(value)):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid input detected", "parameter": key}
                )
        
        # Validate request body for POST/PUT/PATCH requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body and self.contains_malicious_content(body.decode('utf-8')):
                    return JSONResponse(
                        status_code=400,
                        content={"error": "Invalid input detected in request body"}
                    )
            except:
                pass  # If we can't decode the body, let the endpoint handle it
        
        return await call_next(request)
    
    def contains_malicious_content(self, content: str) -> bool:
        """Check if content contains malicious patterns"""
        content_lower = content.lower()
        
        # Check for XSS patterns
        for pattern in self.XSS_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        # Check for SQL injection patterns
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, content_lower, re.IGNORECASE):
                return True
        
        return False

class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Limit request size to prevent DoS attacks"""
    
    def __init__(self, app, max_size: int = 1024 * 1024):  # 1MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        
        if content_length and int(content_length) > self.max_size:
            return JSONResponse(
                status_code=413,
                content={"error": "Request entity too large"}
            )
        
        return await call_next(request)