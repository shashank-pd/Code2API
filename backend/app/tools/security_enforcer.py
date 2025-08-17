from langchain.tools import tool
from typing import Dict, Any, List
import os
from pathlib import Path
from jinja2 import Template

@tool
def security_enforcer_tool(api_directory: str, security_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Apply security layers to the generated API including authentication, authorization, and security headers.
    
    Args:
        api_directory: Path to the generated API directory
        security_config: Optional security configuration
    
    Returns:
        Dictionary containing security implementation results
    """
    try:
        api_dir = Path(api_directory)
        if not api_dir.exists():
            return {"success": False, "error": "API directory not found"}
        
        # Default security configuration
        if not security_config:
            security_config = {
                "authentication": "jwt",
                "authorization": "rbac",
                "cors_origins": ["http://localhost:3000"],
                "rate_limiting": True,
                "security_headers": True,
                "input_validation": True
            }
        
        security_files = []
        
        # Generate authentication module
        auth_content = generate_auth_module(security_config)
        auth_file = api_dir / "auth.py"
        with open(auth_file, 'w', encoding='utf-8') as f:
            f.write(auth_content)
        security_files.append(str(auth_file))
        
        # Generate security middleware
        middleware_content = generate_security_middleware(security_config)
        middleware_file = api_dir / "security_middleware.py"
        with open(middleware_file, 'w', encoding='utf-8') as f:
            f.write(middleware_content)
        security_files.append(str(middleware_file))
        
        # Generate rate limiting module
        rate_limit_content = generate_rate_limiting(security_config)
        rate_limit_file = api_dir / "rate_limiting.py"
        with open(rate_limit_file, 'w', encoding='utf-8') as f:
            f.write(rate_limit_content)
        security_files.append(str(rate_limit_file))
        
        # Update main.py to include security features
        update_main_with_security(api_dir / "main.py", security_config)
        
        # Generate security configuration file
        security_config_content = generate_security_config()
        config_file = api_dir / "security_config.py"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(security_config_content)
        security_files.append(str(config_file))
        
        # Update requirements.txt with security dependencies
        update_requirements_with_security(api_dir / "requirements.txt")
        
        return {
            "success": True,
            "security_files": security_files,
            "features_applied": [
                "JWT Authentication",
                "Role-based Authorization", 
                "CORS Protection",
                "Rate Limiting",
                "Security Headers",
                "Input Validation",
                "Password Hashing"
            ],
            "security_config": security_config
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Security enforcement failed: {str(e)}"
        }

def generate_auth_module(security_config: Dict[str, Any]) -> str:
    """Generate authentication and authorization module"""
    
    template = Template("""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Security configuration
SECRET_KEY = "your-secret-key-change-this-in-production"  # TODO: Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()

# User models
class User(BaseModel):
    username: str
    email: Optional[str] = None
    roles: List[str] = []
    is_active: bool = True

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Dummy user database (replace with real database)
fake_users_db = {
    "demo": {
        "username": "demo",
        "email": "demo@example.com",
        "roles": ["user"],
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "is_active": True,
    },
    "admin": {
        "username": "admin", 
        "email": "admin@example.com",
        "roles": ["admin", "user"],
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "secret"
        "is_active": True,
    }
}

def verify_password(plain_password: str, hashed_password: str) -> bool:
    \"\"\"Verify a password against its hash\"\"\"
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    \"\"\"Hash a password\"\"\"
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    \"\"\"Get user from database\"\"\"
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    \"\"\"Authenticate a user\"\"\"
    user = get_user(username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    \"\"\"Create a JWT access token\"\"\"
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    \"\"\"Get current user from JWT token\"\"\"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return User(**user.dict())

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    \"\"\"Get current active user\"\"\"
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_roles(allowed_roles: List[str]):
    \"\"\"Dependency to require specific roles\"\"\"
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if not any(role in current_user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return role_checker

# Role-based access control decorators
def require_admin(current_user: User = Depends(get_current_active_user)):
    \"\"\"Require admin role\"\"\"
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
""")
    
    return template.render()

def generate_security_middleware(security_config: Dict[str, Any]) -> str:
    """Generate security middleware"""
    
    template = Template("""
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
from typing import Dict, List
import re

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    \"\"\"Add security headers to all responses\"\"\"
    
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
    \"\"\"Validate and sanitize input data\"\"\"
    
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
        \"\"\"Check if content contains malicious patterns\"\"\"
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
    \"\"\"Limit request size to prevent DoS attacks\"\"\"
    
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
""")
    
    return template.render()

def generate_rate_limiting(security_config: Dict[str, Any]) -> str:
    """Generate rate limiting module"""
    
    template = Template("""
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, Tuple
import asyncio
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    \"\"\"Rate limiting middleware using sliding window\"\"\"
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests: Dict[str, List[float]] = defaultdict(list)
        
    async def dispatch(self, request: Request, call_next):
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self.cleanup_old_requests(client_ip, current_time)
        
        # Check rate limits
        if self.is_rate_limited(client_ip, current_time):
            return self.rate_limit_response()
        
        # Record this request
        self.requests[client_ip].append(current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining_minute = max(0, self.requests_per_minute - self.count_requests_in_window(client_ip, current_time, 60))
        remaining_hour = max(0, self.requests_per_hour - self.count_requests_in_window(client_ip, current_time, 3600))
        
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining-Minute"] = str(remaining_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Remaining-Hour"] = str(remaining_hour)
        
        return response
    
    def get_client_ip(self, request: Request) -> str:
        \"\"\"Get client IP address\"\"\"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def cleanup_old_requests(self, client_ip: str, current_time: float):
        \"\"\"Remove requests older than 1 hour\"\"\"
        hour_ago = current_time - 3600
        self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] if req_time > hour_ago]
    
    def count_requests_in_window(self, client_ip: str, current_time: float, window_seconds: int) -> int:
        \"\"\"Count requests in the specified time window\"\"\"
        window_start = current_time - window_seconds
        return len([req_time for req_time in self.requests[client_ip] if req_time > window_start])
    
    def is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        \"\"\"Check if client is rate limited\"\"\"
        minute_count = self.count_requests_in_window(client_ip, current_time, 60)
        hour_count = self.count_requests_in_window(client_ip, current_time, 3600)
        
        return minute_count >= self.requests_per_minute or hour_count >= self.requests_per_hour
    
    def rate_limit_response(self):
        \"\"\"Return rate limit exceeded response\"\"\"
        return HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={
                "Retry-After": "60"
            }
        )

# Dependency for additional rate limiting on specific endpoints
class EndpointRateLimit:
    def __init__(self, requests_per_minute: int = 10):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def __call__(self, request: Request):
        client_ip = self.get_client_ip(request)
        current_time = time.time()
        
        # Clean old requests
        minute_ago = current_time - 60
        self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] if req_time > minute_ago]
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded for this endpoint: {self.requests_per_minute} requests per minute",
                headers={"Retry-After": "60"}
            )
        
        # Record request
        self.requests[client_ip].append(current_time)
        return True
    
    def get_client_ip(self, request: Request) -> str:
        \"\"\"Get client IP address\"\"\"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

# Predefined rate limiters for different endpoint types
strict_rate_limit = EndpointRateLimit(requests_per_minute=5)   # For sensitive operations
normal_rate_limit = EndpointRateLimit(requests_per_minute=30)  # For normal operations
loose_rate_limit = EndpointRateLimit(requests_per_minute=100)  # For read-only operations
""")
    
    return template.render()

def generate_security_config() -> str:
    """Generate security configuration"""
    
    return """
import os
from typing import List

class SecurityConfig:
    \"\"\"Security configuration class\"\"\"
    
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
"""

def update_main_with_security(main_file_path: Path, security_config: Dict[str, Any]):
    """Update main.py to include security features"""
    
    if not main_file_path.exists():
        return
    
    # Read current content
    with open(main_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add security imports and middleware
    security_additions = """
# Security imports
from auth import get_current_active_user, require_admin, create_access_token, authenticate_user, Token
from security_middleware import SecurityHeadersMiddleware, InputValidationMiddleware, RequestSizeMiddleware
from rate_limiting import RateLimitMiddleware
from security_config import security_config
from fastapi import Form
from datetime import timedelta

"""
    
    # Add middleware configuration after app creation
    middleware_config = """
# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(RequestSizeMiddleware, max_size=security_config.MAX_REQUEST_SIZE)
app.add_middleware(RateLimitMiddleware, 
                  requests_per_minute=security_config.RATE_LIMIT_REQUESTS_PER_MINUTE,
                  requests_per_hour=security_config.RATE_LIMIT_REQUESTS_PER_HOUR)

"""
    
    # Add authentication endpoints
    auth_endpoints = """
@app.post("/auth/login", response_model=Token)
async def login(username: str = Form(...), password: str = Form(...)):
    \"\"\"Authenticate user and return JWT token\"\"\"
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=security_config.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/auth/me")
async def read_users_me(current_user = Depends(get_current_active_user)):
    \"\"\"Get current user information\"\"\"
    return current_user

"""
    
    # Insert the security additions
    lines = content.split('\n')
    
    # Find where to insert imports (after existing imports)
    import_insert_line = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            import_insert_line = i + 1
    
    # Insert security imports
    lines.insert(import_insert_line, security_additions)
    
    # Find where to insert middleware (after app creation)
    middleware_insert_line = 0
    for i, line in enumerate(lines):
        if 'FastAPI(' in line:
            # Find the end of the app creation
            for j in range(i, len(lines)):
                if ')' in lines[j] and 'app' in lines[j-5:j]:
                    middleware_insert_line = j + 1
                    break
            break
    
    if middleware_insert_line > 0:
        lines.insert(middleware_insert_line, middleware_config)
    
    # Find where to insert auth endpoints (before the main block)
    auth_insert_line = len(lines) - 3  # Before if __name__ == "__main__"
    for i in range(len(lines) - 1, -1, -1):
        if 'if __name__' in lines[i]:
            auth_insert_line = i - 1
            break
    
    lines.insert(auth_insert_line, auth_endpoints)
    
    # Write updated content
    with open(main_file_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

def update_requirements_with_security(requirements_file: Path):
    """Update requirements.txt with security dependencies"""
    
    if not requirements_file.exists():
        return
    
    with open(requirements_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    security_deps = """
# Security dependencies
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
cryptography==41.0.7
"""
    
    if "python-jose" not in content:
        with open(requirements_file, 'a', encoding='utf-8') as f:
            f.write(security_deps)
