from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class WorkflowRequest(BaseModel):
    """Request model for the main workflow"""
    repo_url: str = Field(..., description="GitHub repository URL")
    branch: Optional[str] = Field("main", description="Git branch to analyze")

class APIEndpoint(BaseModel):
    """Model for a detected API endpoint"""
    path: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    function_name: str = Field(..., description="Source function name")
    description: Optional[str] = Field(None, description="Endpoint description")
    parameters: List[Dict[str, Any]] = Field(default_factory=list, description="Function parameters")
    return_type: Optional[str] = Field(None, description="Return type")
    
class AnalysisResult(BaseModel):
    """Model for code analysis results"""
    repo_name: str = Field(..., description="Repository name")
    language: str = Field(..., description="Primary programming language")
    api_endpoints: List[APIEndpoint] = Field(default_factory=list, description="Detected API endpoints")
    functions_analyzed: int = Field(0, description="Number of functions analyzed")
    classes_analyzed: int = Field(0, description="Number of classes analyzed")
    security_recommendations: List[str] = Field(default_factory=list, description="Security recommendations")
    
class TestResult(BaseModel):
    """Model for test execution results"""
    test_name: str = Field(..., description="Test name")
    status: str = Field(..., description="Test status (passed/failed)")
    execution_time: float = Field(..., description="Execution time in seconds")
    error_message: Optional[str] = Field(None, description="Error message if failed")

class WorkflowResponse(BaseModel):
    """Response model for the main workflow"""
    success: bool = Field(..., description="Whether the workflow succeeded")
    message: str = Field(..., description="Status message")
    analysis: AnalysisResult = Field(..., description="Code analysis results")
    generated_api_path: str = Field(..., description="Path to generated API")
    test_results: List[TestResult] = Field(default_factory=list, description="Test execution results")
    documentation_url: Optional[str] = Field(None, description="URL to generated documentation")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")

class FileAnalysisResult(BaseModel):
    """Model for individual file analysis results"""
    filename: str = Field(..., description="Name of the analyzed file")
    success: bool = Field(..., description="Whether analysis succeeded")
    analysis: Optional[AnalysisResult] = Field(None, description="Analysis results if successful")
    api_path: Optional[str] = Field(None, description="Path to generated API if successful")
    error: Optional[str] = Field(None, description="Error message if failed")

class UploadResponse(BaseModel):
    """Response model for file upload endpoint"""
    success: bool = Field(..., description="Whether upload succeeded")
    message: str = Field(..., description="Status message")
    results: List[FileAnalysisResult] = Field(..., description="Results for each uploaded file")

class AgentStep(BaseModel):
    """Model for individual agent execution step"""
    step_name: str = Field(..., description="Name of the step")
    status: str = Field(..., description="Step status (running/completed/failed)")
    output: Optional[Dict[str, Any]] = Field(None, description="Step output")
    error: Optional[str] = Field(None, description="Error message if failed")
    execution_time: Optional[float] = Field(None, description="Execution time in seconds")

class WorkflowProgress(BaseModel):
    """Model for workflow progress tracking"""
    workflow_id: str = Field(..., description="Unique workflow identifier")
    current_step: str = Field(..., description="Current step being executed")
    completed_steps: List[AgentStep] = Field(default_factory=list, description="Completed steps")
    progress_percentage: float = Field(0.0, description="Progress percentage (0-100)")
    estimated_remaining_time: Optional[float] = Field(None, description="Estimated remaining time in seconds")
