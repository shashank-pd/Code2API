"""
Configuration settings for Code2API application
Handles environment variables and application settings
"""

from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Code2API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-Powered Source Code to API Generator"
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # AI/LLM Configuration
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    OPENAI_API_KEY: Optional[str] = None
    GOOGLE_AI_API_KEY: Optional[str] = None
    
    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./code2api.db"
    
    # File Storage
    UPLOAD_DIR: str = "./uploads"
    GENERATED_APIS_DIR: str = "./generated"
    TEMP_DIR: str = "./temp"
    
    # Repository Analysis
    MAX_REPO_SIZE_MB: int = 500
    MAX_FILES_ANALYZE: int = 1000
    SUPPORTED_LANGUAGES: List[str] = [
        "python", "javascript", "typescript", "java", 
        "cpp", "c", "go", "rust", "php", "ruby"
    ]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8080"
    ]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "code2api.log"
    
    # Docker/Production
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create necessary directories
        for directory in [self.UPLOAD_DIR, self.GENERATED_APIS_DIR, self.TEMP_DIR]:
            Path(directory).mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()

# Configuration validation
def validate_config():
    """Validate that required configuration is present"""
    warnings = []
    errors = []
    
    # Check AI API keys
    if not settings.GROQ_API_KEY and not settings.OPENAI_API_KEY and not settings.GOOGLE_AI_API_KEY:
        errors.append("At least one AI API key must be configured (GROQ_API_KEY, OPENAI_API_KEY, or GOOGLE_AI_API_KEY)")
    
    # Check GitHub token for repository analysis
    if not settings.GITHUB_TOKEN:
        warnings.append("GITHUB_TOKEN not set - repository analysis will be limited to public repos")
    
    # Check secret key in production
    if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == "your-secret-key-change-this-in-production":
        errors.append("SECRET_KEY must be changed in production environment")
    
    return warnings, errors

# Development configuration
class DevelopmentSettings(Settings):
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENVIRONMENT: str = "development"

# Production configuration
class ProductionSettings(Settings):
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"
    
    # Override with production values
    HOST: str = "0.0.0.0"
    PORT: int = 8000

# Test configuration
class TestSettings(Settings):
    DATABASE_URL: str = "sqlite:///./test.db"
    ENVIRONMENT: str = "testing"
    DEBUG: bool = True

def get_settings():
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestSettings()
    else:
        return DevelopmentSettings()

# Export the configured settings
settings = get_settings()
