"""
Main API server for Code2API system
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, validator, Field
import tempfile
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import zipfile
import json
import logging
import time
import re
from starlette.middleware.base import BaseHTTPMiddleware

from ..parsers.code_parser import CodeParser
from ..ai.analyzer import AIAnalyzer
from ..generators.api_generator import APIGenerator
from ..github.repo_fetcher import GitHubRepoFetcher
from ..config import config
from ..cache import get_cache_stats, clear_all_caches, cleanup_caches

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security utilities
def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal attacks"""
    # Remove any path separators and dangerous characters
    clean_name = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
    clean_name = clean_name.replace('..', '').replace('/', '').replace('\\', '')
    
    # Limit length
    if len(clean_name) > 255:
        clean_name = clean_name[:255]
    
    # Ensure it's not empty after cleaning
    if not clean_name.strip():
        clean_name = "unnamed_file"
    
    return clean_name.strip()

def validate_project_name(project_name: str) -> str:
    """Validate and sanitize project name"""
    # Only allow alphanumeric characters, underscores, and hyphens
    clean_name = re.sub(r'[^a-zA-Z0-9_-]', '_', project_name)
    
    # Ensure it starts with a letter or number
    if clean_name and not clean_name[0].isalnum():
        clean_name = 'project_' + clean_name
    
    # Limit length
    if len(clean_name) > 100:
        clean_name = clean_name[:100]
    
    if not clean_name:
        clean_name = "generated_project"
    
    return clean_name

# Rate limiting storage (in production, use Redis or similar)
request_counts = {}

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old entries
        cutoff = current_time - self.period
        request_counts[client_ip] = [
            timestamp for timestamp in request_counts.get(client_ip, [])
            if timestamp > cutoff
        ]
        
        # Check rate limit
        if len(request_counts.get(client_ip, [])) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={"error": "Rate limit exceeded", "detail": f"Maximum {self.calls} requests per {self.period} seconds"}
            )
        
        # Add current request
        if client_ip not in request_counts:
            request_counts[client_ip] = []
        request_counts[client_ip].append(current_time)
        
        response = await call_next(request)
        return response

app = FastAPI(
    title="Code2API",
    description="AI-powered system that converts source code into APIs",
    version="1.0.0",
    docs_url="/docs" if config.API_DEBUG else None,
    redoc_url="/redoc" if config.API_DEBUG else None
)

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Configure properly in production
app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self'"
        )
        
        # Remove server header
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

# CORS middleware with more restrictive settings for production
allowed_origins = ["*"] if config.API_DEBUG else [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://code2api.example.com"  # Add your production domain
]

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Accept", "Accept-Language", "Content-Language", "Content-Type", "Authorization"],
    max_age=300,  # Cache preflight requests for 5 minutes
)

# Global error handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error for {request.url}: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": "Invalid input data",
            "errors": exc.errors(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error for {request.url}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "detail": exc.detail,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error for {request.url}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    )

# Initialize components
try:
    parser = CodeParser()
    analyzer = AIAnalyzer()
    generator = APIGenerator()
    github_fetcher = GitHubRepoFetcher()
    logger.info("All components initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize components: {e}")
    raise

class GitHubRepoRequest(BaseModel):
    repo_url: str = Field(..., min_length=1, description="GitHub repository URL")
    branch: str = Field(default="main", min_length=1, max_length=100, description="Git branch name")
    include_patterns: List[str] = Field(default=[".py", ".js", ".jsx", ".ts", ".tsx", ".java"], description="File extensions to analyze")
    max_files: int = Field(default=50, ge=1, le=200, description="Maximum number of files to analyze")
    
    @validator('repo_url')
    def validate_repo_url(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError('Repository URL is required')
        
        # Basic URL validation
        v = v.strip()
        if not (v.startswith('https://github.com/') or '/' in v):
            raise ValueError('Invalid GitHub repository URL format')
        
        return v
    
    @validator('include_patterns')
    def validate_patterns(cls, v):
        if not v:
            raise ValueError('At least one file pattern is required')
        
        valid_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rs', '.cpp', '.c', '.h']
        for pattern in v:
            if not pattern.startswith('.'):
                raise ValueError(f'Pattern must start with dot: {pattern}')
            if len(pattern) > 10:
                raise ValueError(f'Pattern too long: {pattern}')
        
        return v

class CodeAnalysisRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=100000, description="Source code to analyze")
    language: str = Field(..., description="Programming language")
    filename: str = Field(..., min_length=1, max_length=255, description="Filename")
    
    @validator('code')
    def validate_code(cls, v):
        if not v or not v.strip():
            raise ValueError('Code cannot be empty')
        
        # Basic security check for potentially dangerous code
        dangerous_patterns = ['eval(', 'exec(', '__import__', 'subprocess', 'os.system']
        code_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in code_lower:
                logging.warning(f"Potentially dangerous code pattern detected: {pattern}")
        
        return v.strip()
    
    @validator('language')
    def validate_language(cls, v):
        valid_languages = ['python', 'javascript', 'java', 'typescript']
        if v.lower() not in valid_languages:
            raise ValueError(f'Unsupported language: {v}. Supported: {valid_languages}')
        return v.lower()
    
    @validator('filename')
    def validate_filename(cls, v):
        if not v or not v.strip():
            raise ValueError('Filename cannot be empty')
        
        # Basic security check for filename
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '|', '?', '*']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f'Invalid character in filename: {char}')
        
        return v.strip()

class CodeAnalysisResponse(BaseModel):
    success: bool
    analysis: Dict[str, Any]
    generated_api_path: Optional[str] = None
    message: str
    timestamp: Optional[str] = None
    processing_time: Optional[float] = None

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str
    request_id: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to Code2API",
        "description": "AI-powered system that converts source code into APIs",
        "endpoints": {
            "analyze": "/analyze - Analyze code and generate API",
            "upload": "/upload - Upload source code files",
            "health": "/health - Health check",
            "docs": "/docs - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Code2API is running"}

@app.post("/analyze-repo", response_model=CodeAnalysisResponse)
async def analyze_github_repo(request: GitHubRepoRequest, background_tasks: BackgroundTasks):
    """Analyze a GitHub repository and generate APIs"""
    try:
        # Parse GitHub URL
        repo_info = github_fetcher.parse_github_url(request.repo_url)
        owner = repo_info["owner"]
        repo = repo_info["repo"]
        
        # Get repository information
        repo_data = github_fetcher.get_repo_info(owner, repo)
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Clone or download repository
            try:
                repo_path = github_fetcher.clone_repo(owner, repo, temp_dir, request.branch)
            except Exception:
                # Fallback to ZIP download
                zip_path = github_fetcher.download_repo_zip(owner, repo, request.branch)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                # Find the extracted directory
                extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir()]
                repo_path = str(extracted_dirs[0]) if extracted_dirs else temp_dir
                os.unlink(zip_path)
            
            # Extract supported files
            supported_files = github_fetcher.extract_supported_files(
                repo_path, request.include_patterns
            )
            
            # Limit number of files to analyze
            if len(supported_files) > request.max_files:
                supported_files = supported_files[:request.max_files]
            
            if not supported_files:
                raise HTTPException(
                    status_code=400, 
                    detail="No supported source code files found in repository"
                )
            
            # Get repository statistics
            repo_stats = github_fetcher.get_repo_statistics(supported_files)
            
            # Analyze all files
            all_endpoints = []
            all_security_recommendations = []
            all_optimization_suggestions = []
            
            for file_path in supported_files:
                try:
                    # Parse the file
                    parsed_code = parser.parse_file(file_path)
                    
                    # Skip files with no functions or classes
                    if not parsed_code.functions and not parsed_code.classes:
                        continue
                    
                    # Analyze with AI
                    analysis = analyzer.analyze_code(parsed_code)
                    
                    # Collect results
                    all_endpoints.extend(analysis.get("api_endpoints", []))
                    all_security_recommendations.extend(analysis.get("security_recommendations", []))
                    all_optimization_suggestions.extend(analysis.get("optimization_suggestions", []))
                    
                except Exception as e:
                    print(f"Error analyzing {file_path}: {e}")
                    continue
            
            # Combine all analysis results
            combined_analysis = {
                "api_endpoints": all_endpoints,
                "security_recommendations": list(set(all_security_recommendations)),
                "optimization_suggestions": list(set(all_optimization_suggestions)),
                "repository_info": {
                    "name": repo_data.get("name"),
                    "description": repo_data.get("description"),
                    "language": repo_data.get("language"),
                    "stars": repo_data.get("stargazers_count"),
                    "forks": repo_data.get("forks_count"),
                    "url": repo_data.get("html_url")
                },
                "statistics": repo_stats,
                "files_analyzed": len(supported_files)
            }
            
            # Generate documentation
            documentation = analyzer.generate_documentation(combined_analysis)
            combined_analysis["documentation"] = documentation
            
            # Generate API project
            project_name = f"{owner}_{repo}".replace("-", "_").replace(".", "_")
            api_path = generator.generate_api(combined_analysis, project_name)
            
            return CodeAnalysisResponse(
                success=True,
                analysis=combined_analysis,
                generated_api_path=api_path,
                message=f"Successfully analyzed {len(supported_files)} files from {owner}/{repo}"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing repository: {str(e)}")

@app.post("/analyze", response_model=CodeAnalysisResponse)
async def analyze_code(request: CodeAnalysisRequest, background_tasks: BackgroundTasks):
    """Analyze source code and generate API"""
    start_time = time.time()
    logger.info(f"Starting code analysis for language: {request.language}, filename: {request.filename}")
    
    try:
        # Create temporary file with proper extension
        language_extensions = {
            "python": ".py",
            "javascript": ".js", 
            "java": ".java"
        }
        extension = language_extensions.get(request.language, f".{request.language}")
        with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as temp_file:
            temp_file.write(request.code)
            temp_file_path = temp_file.name
        
        try:
            # Parse the code
            parsed_code = parser.parse_file(temp_file_path)
            
            # Analyze with AI
            analysis = analyzer.analyze_code(parsed_code)
            
            # Generate documentation
            documentation = analyzer.generate_documentation(analysis)
            analysis["documentation"] = documentation
            
            # Generate optimization suggestions
            optimizations = analyzer.suggest_optimizations(parsed_code)
            analysis["optimization_suggestions"] = optimizations
            
            # Generate API in background
            project_name = request.filename.replace('.', '_').replace('/', '_')
            api_path = generator.generate_api(analysis, project_name)
            
            processing_time = time.time() - start_time
            logger.info(f"Code analysis completed in {processing_time:.2f} seconds")
            
            return CodeAnalysisResponse(
                success=True,
                analysis=analysis,
                generated_api_path=api_path,
                message=f"Successfully analyzed {request.filename} and generated API",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                processing_time=round(processing_time, 2)
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing code: {str(e)}")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload and analyze multiple source code files"""
    start_time = time.time()
    logger.info(f"Starting file upload analysis for {len(files)} files")
    
    # Validate files
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")
    
    results = []
    
    for file in files:
        try:
            # Validate file size (max 1MB per file)
            if file.size and file.size > 1024 * 1024:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "File size exceeds 1MB limit"
                })
                continue
            
            # Read file content
            content = await file.read()
            
            # Validate file is not empty
            if not content:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "File is empty"
                })
                continue
            
            try:
                code = content.decode('utf-8')
            except UnicodeDecodeError:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "File is not valid UTF-8 text"
                })
                continue
            
            # Detect language from extension
            file_path = Path(file.filename)
            extension = file_path.suffix.lower()
            
            language_map = {
                '.py': 'python',
                '.js': 'javascript',
                '.jsx': 'javascript',
                '.ts': 'javascript',
                '.tsx': 'javascript',
                '.java': 'java'
            }
            
            language = language_map.get(extension)
            if not language:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": f"Unsupported file extension: {extension}"
                })
                continue
            
            # Create temporary file and analyze
            with tempfile.NamedTemporaryFile(mode='w', suffix=extension, delete=False) as temp_file:
                temp_file.write(code)
                temp_file_path = temp_file.name
            
            try:
                # Parse and analyze
                parsed_code = parser.parse_file(temp_file_path)
                analysis = analyzer.analyze_code(parsed_code)
                
                # Generate API
                project_name = file.filename.replace('.', '_').replace('/', '_')
                api_path = generator.generate_api(analysis, project_name)
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "analysis": analysis,
                    "api_path": api_path,
                    "endpoints_count": len(analysis.get("api_endpoints", [])),
                    "security_recommendations": len(analysis.get("security_recommendations", []))
                })
                
            finally:
                os.unlink(temp_file_path)
                
        except Exception as e:
            results.append({
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    processing_time = time.time() - start_time
    logger.info(f"File upload analysis completed in {processing_time:.2f} seconds")
    
    successful_uploads = sum(1 for r in results if r.get("success", False))
    
    return {
        "results": results, 
        "total_files": len(files),
        "successful_analyses": successful_uploads,
        "processing_time": round(processing_time, 2),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

@app.get("/download/{project_name}")
async def download_generated_api(project_name: str):
    """Download generated API as a ZIP file"""
    try:
        # Sanitize project name to prevent directory traversal
        clean_project_name = validate_project_name(project_name)
        if clean_project_name != project_name:
            logger.warning(f"Project name sanitized: {project_name} -> {clean_project_name}")
        
        api_path = config.GENERATED_DIR / clean_project_name
        
        # Verify the path is within the generated directory (security check)
        try:
            api_path.resolve().relative_to(config.GENERATED_DIR.resolve())
        except ValueError:
            logger.error(f"Potential directory traversal attempt: {project_name}")
            raise HTTPException(status_code=400, detail="Invalid project name")
        
        if not api_path.exists():
            raise HTTPException(status_code=404, detail="Generated API not found")
        
        if not api_path.is_dir():
            raise HTTPException(status_code=400, detail="Invalid project structure")
        
        # Create ZIP file with security checks
        zip_path = config.GENERATED_DIR / f"{clean_project_name}.zip"
        
        # Ensure zip path is also within generated directory
        try:
            zip_path.resolve().relative_to(config.GENERATED_DIR.resolve())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid zip path")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in api_path.rglob('*'):
                if file_path.is_file():
                    # Additional security check for each file
                    try:
                        file_path.resolve().relative_to(api_path.resolve())
                        zipf.write(file_path, file_path.relative_to(api_path))
                    except ValueError:
                        logger.warning(f"Skipping file outside project directory: {file_path}")
                        continue
        
        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f"{clean_project_name}.zip",
            headers={
                "Content-Disposition": f"attachment; filename=\"{clean_project_name}.zip\"",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except Exception as e:
        logger.error(f"Error in download endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Error creating download")

@app.get("/generated")
async def list_generated_apis():
    """List all generated APIs"""
    try:
        generated_apis = []
        
        if config.GENERATED_DIR.exists():
            for item in config.GENERATED_DIR.iterdir():
                if item.is_dir():
                    # Read main.py to get endpoint count
                    main_file = item / "main.py"
                    endpoint_count = 0
                    
                    if main_file.exists():
                        content = main_file.read_text()
                        endpoint_count = content.count("@app.")
                    
                    generated_apis.append({
                        "name": item.name,
                        "path": str(item),
                        "endpoint_count": endpoint_count,
                        "created": item.stat().st_ctime
                    })
        
        return {"generated_apis": generated_apis}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing APIs: {str(e)}")

@app.get("/languages")
async def get_supported_languages():
    """Get list of supported programming languages"""
    return {
        "supported_languages": config.SUPPORTED_LANGUAGES,
        "message": "Use these language identifiers when analyzing code"
    }

@app.post("/security-scan")
async def security_scan(request: CodeAnalysisRequest):
    """Perform security analysis on code"""
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{request.language}', delete=False) as temp_file:
            temp_file.write(request.code)
            temp_file_path = temp_file.name
        
        try:
            # Parse the code
            parsed_code = parser.parse_file(temp_file_path)
            
            # Security analysis
            security_recommendations = analyzer._analyze_security(parsed_code)
            
            return {
                "filename": request.filename,
                "security_recommendations": security_recommendations,
                "risk_level": "high" if len(security_recommendations) > 3 else "medium" if len(security_recommendations) > 0 else "low"
            }
            
        finally:
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in security scan: {str(e)}")

@app.get("/cache/stats")
async def get_cache_statistics():
    """Get cache statistics and performance metrics"""
    try:
        stats = get_cache_stats()
        return {
            "cache_stats": stats,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

@app.post("/cache/clear")
async def clear_cache():
    """Clear all caches (admin operation)"""
    try:
        clear_all_caches()
        logger.info("All caches cleared")
        return {
            "message": "All caches cleared successfully",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@app.post("/cache/cleanup")
async def cleanup_cache():
    """Clean up expired cache entries"""
    try:
        cleanup_caches()
        logger.info("Cache cleanup completed")
        return {
            "message": "Cache cleanup completed",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during cache cleanup: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
