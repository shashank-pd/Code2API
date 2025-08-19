"""
API router initialization
Imports and configures all API routes for the application
"""

from fastapi import APIRouter
from .groq_routes import router as groq_router

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all route modules
api_router.include_router(groq_router)

# Export for use in main.py
__all__ = ["api_router"]
