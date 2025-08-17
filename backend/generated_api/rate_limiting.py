
from fastapi import Request, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
import time
from typing import Dict, Tuple
import asyncio
from collections import defaultdict

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using sliding window"""
    
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
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def cleanup_old_requests(self, client_ip: str, current_time: float):
        """Remove requests older than 1 hour"""
        hour_ago = current_time - 3600
        self.requests[client_ip] = [req_time for req_time in self.requests[client_ip] if req_time > hour_ago]
    
    def count_requests_in_window(self, client_ip: str, current_time: float, window_seconds: int) -> int:
        """Count requests in the specified time window"""
        window_start = current_time - window_seconds
        return len([req_time for req_time in self.requests[client_ip] if req_time > window_start])
    
    def is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client is rate limited"""
        minute_count = self.count_requests_in_window(client_ip, current_time, 60)
        hour_count = self.count_requests_in_window(client_ip, current_time, 3600)
        
        return minute_count >= self.requests_per_minute or hour_count >= self.requests_per_hour
    
    def rate_limit_response(self):
        """Return rate limit exceeded response"""
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
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

# Predefined rate limiters for different endpoint types
strict_rate_limit = EndpointRateLimit(requests_per_minute=5)   # For sensitive operations
normal_rate_limit = EndpointRateLimit(requests_per_minute=30)  # For normal operations
loose_rate_limit = EndpointRateLimit(requests_per_minute=100)  # For read-only operations