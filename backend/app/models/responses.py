"""
Response models for API endpoints
Defines the structure of outgoing responses
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

class ResponseStatus(str, Enum):
    """Response status types"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: Optional[str] = Field(default=None, description="Human-readable message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    error_code: Optional[str] = Field(default=None, description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")

class RepositoryInfo(BaseModel):
    """Repository information"""
    name: str
    url: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0
    size: int = 0
    default_branch: str = "main"

class FunctionInfo(BaseModel):
    """Information about a parsed function"""
    name: str
    args: List[str]
    docstring: Optional[str] = None
    return_annotation: Optional[str] = None
    line_number: int
    file_path: str
    class_name: Optional[str] = None
    decorators: List[str] = []
    is_async: bool = False
    complexity: int = 1

class APIEndpointInfo(BaseModel):
    """Information about a generated API endpoint"""
    function_name: str
    endpoint_path: str
    http_method: str
    description: str
    parameters: List[Dict[str, Any]] = []
    return_type: str = "object"
    needs_auth: bool = False
    class_name: Optional[str] = None
    tags: List[str] = []

class Statistics(BaseModel):
    """Analysis statistics"""
    total_files: int = 0
    total_lines: int = 0
    total_functions: int = 0
    languages: Dict[str, int] = {}
    functions_by_language: Dict[str, int] = {}
    average_complexity: float = 0.0
    files_with_functions: int = 0

class AnalysisResult(BaseModel):
    """Code analysis result"""
    repository_info: Optional[RepositoryInfo] = None
    api_endpoints: List[APIEndpointInfo] = []
    functions: List[FunctionInfo] = []
    statistics: Optional[Statistics] = None
    security_recommendations: List[str] = []
    optimization_suggestions: List[str] = []
    files_analyzed: int = 0
    language: Optional[str] = None
    filename: Optional[str] = None

class AnalysisResponse(BaseResponse):
    """Response for code/repository analysis"""
    analysis: Optional[AnalysisResult] = None

class APIGenerationResult(BaseModel):
    """API generation result"""
    project_name: str
    api_path: str
    openapi_spec: Dict[str, Any]
    endpoints: List[APIEndpointInfo]
    files_created: List[str]

class APIGenerationResponse(BaseResponse):
    """Response for API generation"""
    result: Optional[APIGenerationResult] = None

class TestResult(BaseModel):
    """Single test result"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None

class TestSummary(BaseModel):
    """Test suite summary"""
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    average_response_time: float
    security_score: int
    performance_score: int

class TestSuiteResult(BaseModel):
    """Complete test suite result"""
    summary: TestSummary
    results: List[TestResult]
    security_issues: List[str] = []
    performance_issues: List[str] = []
    recommendations: List[str] = []

class TestResultsResponse(BaseResponse):
    """Response for API testing"""
    test_results: Optional[TestSuiteResult] = None

class WorkflowStatus(str, Enum):
    """Workflow status types"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowStep(BaseModel):
    """Individual workflow step"""
    name: str
    status: WorkflowStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    progress_percentage: int = 0

class WorkflowResult(BaseModel):
    """Workflow execution result"""
    task_id: str
    status: WorkflowStatus
    steps: List[WorkflowStep]
    started_at: datetime
    completed_at: Optional[datetime] = None
    total_duration_seconds: Optional[float] = None
    analysis_result: Optional[AnalysisResult] = None
    api_generation_result: Optional[APIGenerationResult] = None
    test_results: Optional[TestSuiteResult] = None

class WorkflowResponse(BaseResponse):
    """Response for workflow operations"""
    workflow: Optional[WorkflowResult] = None
    task_id: Optional[str] = None
    status_url: Optional[str] = None

class FileUploadResult(BaseModel):
    """File upload result"""
    filename: str
    language: Optional[str] = None
    success: bool
    analysis: Optional[AnalysisResult] = None
    error: Optional[str] = None

class FileUploadResponse(BaseResponse):
    """Response for file upload and analysis"""
    files_processed: int
    results: List[FileUploadResult]

class UserInfo(BaseModel):
    """User information (without sensitive data)"""
    username: str
    email: str
    full_name: Optional[str] = None
    disabled: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AuthTokenResponse(BaseResponse):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds
    user: Optional[UserInfo] = None

class UserProfileResponse(BaseResponse):
    """User profile response"""
    user: Optional[UserInfo] = None

class APIKeyInfo(BaseModel):
    """API key information"""
    key_id: int
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True

class APIKeyResponse(BaseResponse):
    """API key response"""
    api_key: Optional[str] = None
    key_info: Optional[APIKeyInfo] = None

class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    services: Dict[str, bool] = {}
    version: str = "1.0.0"

class APIInfoResponse(BaseModel):
    """API information response"""
    name: str = "Code2API"
    version: str = "1.0.0"
    description: str = "AI-Powered Source Code to API Generator"
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"
    health_url: str = "/health"

class APIGenerationResponse(BaseResponse):
    """Response for API generation"""
    data: Optional[Dict[str, Any]] = Field(default=None, description="Generated API information")
    api_path: Optional[str] = Field(default=None, description="Path to generated API")
    openapi_spec: Optional[Dict[str, Any]] = Field(default=None, description="OpenAPI specification")
    endpoints: Optional[List[Dict[str, Any]]] = Field(default=None, description="Generated endpoints")
    files_created: Optional[List[str]] = Field(default=None, description="List of created files")
    project_name: Optional[str] = Field(default=None, description="Generated project name")
    
class DownloadResponse(BaseModel):
    """Download response information"""
    filename: str
    file_size: int
    download_url: str
    expires_at: Optional[datetime] = None

class ValidationErrorDetail(BaseModel):
    """Validation error detail"""
    field: str
    message: str
    invalid_value: Any

class ValidationErrorResponse(ErrorResponse):
    """Validation error response"""
    validation_errors: List[ValidationErrorDetail] = []

# Utility response models for common operations
class SimpleMessageResponse(BaseResponse):
    """Simple message response"""
    pass

class CountResponse(BaseResponse):
    """Response with a count value"""
    count: int

class ListResponse(BaseResponse):
    """Generic list response"""
    items: List[Any]
    total_count: int
    page: int = 1
    page_size: int = 100
    has_next: bool = False
    has_previous: bool = False
