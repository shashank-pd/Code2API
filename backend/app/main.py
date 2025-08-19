"""
AI-Powered Source Code to API Generator
Main FastAPI Application Module

This module sets up the FastAPI application with all necessary components:
- API routes and endpoints
- Authentication middleware
- CORS configuration
- Database connections
- Error handling
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse, JSONResponse
from typing import List, Optional, Dict, Any
import os
import uvicorn
from pathlib import Path
import tempfile
import shutil
import zipfile
import asyncio
import logging

from .core.config import settings
from .core.repository_analyzer import RepositoryAnalyzer
from .core.code_analyzer import CodeAnalyzer
from .core.api_generator import APIGenerator
from .core.auth import AuthManager
from .core.test_engine import APITester
from .models.requests import (
    CodeAnalysisRequest,
    RepositoryAnalysisRequest,
    APIGenerationRequest
)
from .models.responses import (
    AnalysisResponse,
    APIGenerationResponse,
    TestResultsResponse
)
from .services.workflow_service import WorkflowService
from .database.database import get_database
from .utils.file_utils import FileManager
from .api import api_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Code2API - AI-Powered Source Code to API Generator",
    description="""
    An advanced AI-powered system that analyzes source code repositories, 
    converts them into functional APIs, and generates comprehensive documentation.
    
    ## Features
    
    * **Repository Analysis**: Clone and analyze GitHub repositories
    * **Code Parsing**: Multi-language AST analysis and function extraction
    * **AI Analysis**: LLM-powered code understanding and API design
    * **API Generation**: Automatic FastAPI endpoint creation
    * **Authentication**: JWT-based security system
    * **Testing**: Automated API testing and validation
    * **Documentation**: OpenAPI specification generation
    
    ## Supported Languages
    
    * Python
    * JavaScript/TypeScript
    * Java
    * And more...
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Security
security = HTTPBearer()
auth_manager = AuthManager()

# Initialize services
repo_analyzer = RepositoryAnalyzer(settings.GITHUB_TOKEN)
code_analyzer = CodeAnalyzer(settings.GROQ_API_KEY)
api_generator = APIGenerator()
api_tester = APITester()
workflow_service = WorkflowService()
file_manager = FileManager()

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = auth_manager.verify_token(credentials.credentials)
        return payload
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Code2API - AI-Powered Source Code to API Generator",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "groq_api": bool(settings.GROQ_API_KEY),
            "github_api": bool(settings.GITHUB_TOKEN),
            "database": True
        }
    }

@app.post("/api/analyze-code", response_model=AnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest):
    """
    Analyze source code directly and generate API suggestions
    
    This endpoint accepts source code directly and performs:
    1. AST parsing and function extraction
    2. AI-powered code analysis
    3. API endpoint suggestions
    4. Security recommendations
    """
    try:
        logger.info(f"Analyzing code for language: {request.language}")
        
        # Parse and analyze code
        analysis_result = await code_analyzer.analyze_code(
            code=request.code,
            language=request.language,
            filename=request.filename
        )
        
        return AnalysisResponse(
            success=True,
            analysis=analysis_result,
            message="Code analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Code analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/analyze-repository", response_model=AnalysisResponse)
async def analyze_repository(request: RepositoryAnalysisRequest):
    """
    Analyze a GitHub repository and generate comprehensive API suggestions
    
    This endpoint performs:
    1. Repository cloning and structure analysis
    2. Multi-file code parsing
    3. Dependency analysis
    4. AI-powered function understanding
    5. API endpoint generation suggestions
    """
    try:
        logger.info(f"Analyzing repository: {request.repo_url}")
        
        # Analyze repository
        analysis_result = await repo_analyzer.analyze_repository(
            repo_url=request.repo_url,
            branch=request.branch,
            include_private=request.include_private
        )
        
        # AI analysis of extracted functions
        ai_analysis = await code_analyzer.analyze_repository_functions(
            analysis_result["functions"]
        )
        
        # Combine results
        combined_result = {
            **analysis_result,
            **ai_analysis
        }
        
        return AnalysisResponse(
            success=True,
            analysis=combined_result,
            message="Repository analysis completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Repository analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Repository analysis failed: {str(e)}")

@app.post("/api/generate-api", response_model=APIGenerationResponse)
async def generate_api(request: APIGenerationRequest):
    """
    Generate a complete FastAPI application from analysis results
    
    This endpoint creates:
    1. FastAPI application structure
    2. Endpoint implementations
    3. Pydantic models
    4. Authentication middleware
    5. OpenAPI documentation
    6. Test suite
    """
    try:
        logger.info(f"Generating API for project: {request.project_name}")
        
        # Generate API
        api_result = await api_generator.generate_api(
            analysis_data=request.analysis_data,
            project_name=request.project_name,
            include_auth=request.include_auth,
            include_tests=request.include_tests
        )
        
        return APIGenerationResponse(
            success=True,
            api_path=api_result["api_path"],
            openapi_spec=api_result["openapi_spec"],
            endpoints=api_result["endpoints"],
            message="API generated successfully"
        )
        
    except Exception as e:
        logger.error(f"API generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API generation failed: {str(e)}")

@app.post("/api/upload", response_model=Dict[str, Any])
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple source code files for analysis
    
    Supports:
    - Multiple file upload
    - Various programming languages
    - Automatic language detection
    - Batch processing
    """
    try:
        logger.info(f"Processing {len(files)} uploaded files")
        
        results = []
        temp_dir = tempfile.mkdtemp()
        
        try:
            for file in files:
                # Save uploaded file
                file_path = os.path.join(temp_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Detect language and analyze
                language = file_manager.detect_language(file.filename)
                if language:
                    with open(file_path, "r", encoding="utf-8") as f:
                        code_content = f.read()
                    
                    analysis = await code_analyzer.analyze_code(
                        code=code_content,
                        language=language,
                        filename=file.filename
                    )
                    
                    results.append({
                        "filename": file.filename,
                        "language": language,
                        "success": True,
                        "analysis": analysis
                    })
                else:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": "Unsupported file type"
                    })
        
        finally:
            # Cleanup temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        return {
            "success": True,
            "files_processed": len(files),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"File upload processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File processing failed: {str(e)}")

@app.post("/api/run-workflow")
async def run_complete_workflow(
    request: RepositoryAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Run the complete Code2API workflow
    
    This endpoint orchestrates the entire process:
    1. Repository analysis
    2. AI-powered code understanding
    3. API generation
    4. Testing
    5. Documentation creation
    """
    try:
        logger.info(f"Starting complete workflow for: {request.repo_url}")
        
        # Run workflow in background
        task_id = await workflow_service.start_workflow(
            repo_url=request.repo_url,
            branch=request.branch,
            include_auth=True,
            include_tests=True
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "Workflow started successfully",
            "status_url": f"/api/workflow-status/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"Workflow startup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

@app.get("/api/workflow-status/{task_id}")
async def get_workflow_status(task_id: str):
    """Get the status of a running workflow"""
    try:
        status = await workflow_service.get_workflow_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail="Workflow not found")

@app.post("/api/test-api", response_model=TestResultsResponse)
async def test_generated_api(api_path: str, base_url: str = "http://localhost:8000"):
    """
    Test a generated API automatically
    
    Performs:
    1. Endpoint discovery
    2. Test case generation
    3. Response validation
    4. Performance testing
    5. Security testing
    """
    try:
        logger.info(f"Testing API at: {api_path}")
        
        test_results = await api_tester.test_api(
            api_path=api_path,
            base_url=base_url
        )
        
        return TestResultsResponse(
            success=True,
            test_results=test_results,
            message="API testing completed"
        )
        
    except Exception as e:
        logger.error(f"API testing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API testing failed: {str(e)}")

@app.get("/api/download/{project_name}")
async def download_generated_api(project_name: str):
    """Download a generated API as a ZIP file"""
    try:
        api_path = os.path.join(settings.GENERATED_APIS_DIR, project_name)
        
        if not os.path.exists(api_path):
            raise HTTPException(status_code=404, detail="Generated API not found")
        
        # Create ZIP file
        zip_path = f"{api_path}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(api_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, api_path)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{project_name}.zip"
        )
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/download-by-path")
async def download_by_path(path: str):
    """Download a generated API by its path"""
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Path not found")
        
        # Get project name from path
        project_name = os.path.basename(path)
        
        # Create ZIP file
        zip_path = f"{path}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, path)
                    zipf.write(file_path, arcname)
        
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{project_name}.zip"
        )
        
    except Exception as e:
        logger.error(f"Download by path failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.post("/api/generate-api", response_model=APIGenerationResponse)
async def generate_api_endpoint(request: APIGenerationRequest):
    """
    Generate a complete FastAPI application from analysis results
    """
    try:
        logger.info(f"Generating API: {request.project_name}")
        
        # Generate the API
        generation_result = await api_generator.generate_api(
            analysis_data=request.analysis_data,
            project_name=request.project_name,
            include_auth=request.include_auth,
            include_tests=request.include_tests,
            include_docs=request.include_docs
        )
        
        return APIGenerationResponse(
            success=True,
            data=generation_result,
            message="API generated successfully"
        )
        
    except Exception as e:
        logger.error(f"API generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API generation failed: {str(e)}")

@app.post("/api/start-generated-api")
async def start_generated_api(request: dict):
    """
    Start a generated API server
    """
    try:
        api_path = request.get("api_path")
        if not api_path:
            raise HTTPException(status_code=400, detail="api_path is required")
        
        logger.info(f"Starting generated API at: {api_path}")
        
        # Start the API using the startup script
        import subprocess
        import os
        
        # Change to the API directory
        startup_script = os.path.join(api_path, "start.py")
        
        if not os.path.exists(startup_script):
            raise HTTPException(status_code=404, detail="Startup script not found")
        
        # Start the API in background
        process = subprocess.Popen(
            ["python", startup_script],
            cwd=api_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Give it a moment to start
        await asyncio.sleep(2)
        
        return {
            "success": True,
            "message": "Generated API started successfully",
            "api_url": "http://localhost:8001",
            "docs_url": "http://localhost:8001/docs",
            "process_id": process.pid
        }
        
    except Exception as e:
        logger.error(f"Failed to start generated API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start API: {str(e)}")

# Authentication endpoints
@app.post("/api/auth/login")
async def login(username: str, password: str):
    """Authenticate user and return JWT token"""
    try:
        token = auth_manager.authenticate_user(username, password)
        if token:
            return {"access_token": token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Authentication failed")

@app.post("/api/auth/register")
async def register(username: str, email: str, password: str):
    """Register a new user"""
    try:
        success = auth_manager.create_user(username, email, password)
        if success:
            return {"message": "User created successfully"}
        else:
            raise HTTPException(status_code=400, detail="User creation failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/api/user/profile")
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
