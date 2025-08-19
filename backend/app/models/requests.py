"""
Request models for API endpoints
Defines the structure of incoming requests
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from enum import Enum

class SupportedLanguage(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"
    GO = "go"
    RUST = "rust"
    PHP = "php"
    RUBY = "ruby"

class CodeAnalysisRequest(BaseModel):
    """Request for analyzing source code directly"""
    code: str = Field(..., description="Source code to analyze", min_length=1)
    language: SupportedLanguage = Field(..., description="Programming language of the code")
    filename: str = Field(..., description="Name of the source file", min_length=1)
    
    @validator('code')
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError('Code cannot be empty')
        return v

class RepositoryAnalysisRequest(BaseModel):
    """Request for analyzing a GitHub repository"""
    repo_url: str = Field(
        ..., 
        description="GitHub repository URL or owner/repo format",
        min_length=1
    )
    branch: str = Field(
        default="main", 
        description="Branch to analyze"
    )
    include_private: bool = Field(
        default=False, 
        description="Whether to include private repositories"
    )
    max_files: Optional[int] = Field(
        default=1000,
        description="Maximum number of files to analyze",
        ge=1,
        le=5000
    )
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        # Basic validation for GitHub URL format
        if not v.strip():
            raise ValueError('Repository URL cannot be empty')
        
        # Accept both full URLs and owner/repo format
        if v.startswith('http'):
            if 'github.com' not in v:
                raise ValueError('Only GitHub repositories are supported')
        else:
            # Validate owner/repo format
            parts = v.split('/')
            if len(parts) != 2 or not all(part.strip() for part in parts):
                raise ValueError('Repository must be in "owner/repo" format')
        
        return v.strip()

class APIGenerationRequest(BaseModel):
    """Request for generating API from analysis results"""
    analysis_data: Dict[str, Any] = Field(
        ..., 
        description="Analysis results from code/repository analysis"
    )
    project_name: str = Field(
        ..., 
        description="Name for the generated API project",
        min_length=1,
        max_length=100
    )
    include_auth: bool = Field(
        default=True,
        description="Whether to include authentication in the generated API"
    )
    include_tests: bool = Field(
        default=True,
        description="Whether to generate test files"
    )
    include_docs: bool = Field(
        default=True,
        description="Whether to generate documentation"
    )
    
    @validator('project_name')
    def validate_project_name(cls, v):
        # Ensure project name is valid for filesystem
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Project name can only contain letters, numbers, underscores, and hyphens')
        return v.lower().replace(' ', '_')

class WorkflowRequest(BaseModel):
    """Request for running complete workflow"""
    repo_url: str = Field(..., description="GitHub repository URL")
    branch: str = Field(default="main", description="Branch to analyze")
    project_name: Optional[str] = Field(
        default=None,
        description="Custom project name (auto-generated if not provided)"
    )
    include_auth: bool = Field(default=True, description="Include authentication")
    include_tests: bool = Field(default=True, description="Include test generation")
    include_docs: bool = Field(default=True, description="Include documentation")
    
    @validator('project_name')
    def validate_project_name(cls, v):
        if v is None:
            return v
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Project name can only contain letters, numbers, underscores, and hyphens')
        return v.lower().replace(' ', '_')

class TestAPIRequest(BaseModel):
    """Request for testing a generated API"""
    api_path: str = Field(..., description="Path to the generated API")
    base_url: str = Field(
        default="http://localhost:8000",
        description="Base URL for testing the API"
    )
    include_security_tests: bool = Field(
        default=True,
        description="Whether to run security tests"
    )
    include_performance_tests: bool = Field(
        default=True,
        description="Whether to run performance tests"
    )
    timeout_seconds: int = Field(
        default=10,
        description="Timeout for API requests in seconds",
        ge=1,
        le=60
    )

class AuthLoginRequest(BaseModel):
    """Request for user authentication"""
    username: str = Field(..., description="Username", min_length=1)
    password: str = Field(..., description="Password", min_length=1)

class AuthRegisterRequest(BaseModel):
    """Request for user registration"""
    username: str = Field(
        ..., 
        description="Unique username",
        min_length=3,
        max_length=50
    )
    email: str = Field(..., description="Email address")
    password: str = Field(
        ..., 
        description="Password",
        min_length=6
    )
    full_name: Optional[str] = Field(
        default=None,
        description="Full name",
        max_length=100
    )
    
    @validator('username')
    def validate_username(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v.lower()
    
    @validator('email')
    def validate_email(cls, v):
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class PasswordChangeRequest(BaseModel):
    """Request for changing password"""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ..., 
        description="New password",
        min_length=6
    )
    confirm_password: str = Field(..., description="Confirm new password")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class UserUpdateRequest(BaseModel):
    """Request for updating user information"""
    email: Optional[str] = Field(default=None, description="New email address")
    full_name: Optional[str] = Field(default=None, description="New full name")
    
    @validator('email')
    def validate_email(cls, v):
        if v is None:
            return v
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

class FileUploadMetadata(BaseModel):
    """Metadata for uploaded files"""
    original_filename: str
    file_size: int
    mime_type: str
    language_detected: Optional[str] = None

class APIGenerationRequest(BaseModel):
    """Request for generating API from analysis results"""
    analysis_data: Dict[str, Any] = Field(..., description="Analysis results from code analysis")
    project_name: str = Field(..., description="Name for the generated API project", min_length=1)
    include_auth: bool = Field(default=True, description="Include authentication in generated API")
    include_tests: bool = Field(default=True, description="Include test files in generated API")
    include_docs: bool = Field(default=True, description="Include documentation in generated API")
    
    @validator('project_name')
    def validate_project_name(cls, v):
        import re
        # Ensure project name is valid for file system
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Project name can only contain letters, numbers, underscores, and hyphens')
        return v
