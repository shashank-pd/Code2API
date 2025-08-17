
import os
from typing import List

class SecurityConfig:
    """Security configuration class"""
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://yourdomain.com"
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_REQUESTS_PER_HOUR: int = 1000
    
    # Request Size Limits
    MAX_REQUEST_SIZE: int = 1024 * 1024  # 1MB
    
    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = True
    
    # Input Validation
    ENABLE_INPUT_VALIDATION: bool = True
    
    # API Key Configuration (optional)
    API_KEY_HEADER: str = "X-API-Key"
    VALID_API_KEYS: List[str] = [
        os.getenv("API_KEY_1", "demo-api-key-1"),
        os.getenv("API_KEY_2", "demo-api-key-2")
    ]

# Global security config instance
security_config = SecurityConfig()
