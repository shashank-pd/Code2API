"""
Main configuration module for Code2API
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "localhost")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_VERSION = "v1"
    
    # AI Configuration - Using GroqCloud
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    
    # Legacy OpenAI support (for backwards compatibility)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # GitHub Configuration
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    
    # File paths
    ROOT_DIR = Path(__file__).parent.parent
    TEMPLATES_DIR = ROOT_DIR / "templates"
    GENERATED_DIR = ROOT_DIR / "generated"
    EXAMPLES_DIR = ROOT_DIR / "examples"
    
    # Supported languages
    SUPPORTED_LANGUAGES = {
        "python": {
            "extensions": [".py"],
            "tree_sitter": "python",
            "comment_style": "#"
        },
        "javascript": {
            "extensions": [".js", ".jsx", ".ts", ".tsx"],
            "tree_sitter": "javascript",
            "comment_style": "//"
        },
        "java": {
            "extensions": [".java"],
            "tree_sitter": "java",
            "comment_style": "//"
        }
    }
    
    # AI Analysis settings
    MAX_TOKENS = 2000
    TEMPERATURE = 0.3
    
    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        cls.GENERATED_DIR.mkdir(exist_ok=True)
        cls.TEMPLATES_DIR.mkdir(exist_ok=True)
        cls.EXAMPLES_DIR.mkdir(exist_ok=True)

config = Config()
