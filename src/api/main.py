"""
Main API server for Code2API system
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import tempfile
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import zipfile
import json

from ..parsers.code_parser import CodeParser
from ..ai.analyzer import AIAnalyzer
from ..generators.api_generator import APIGenerator
from ..github.repo_fetcher import GitHubRepoFetcher
from ..config import config

app = FastAPI(
    title="Code2API",
    description="AI-powered system that converts source code into APIs",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
parser = CodeParser()
analyzer = AIAnalyzer()
generator = APIGenerator()
github_fetcher = GitHubRepoFetcher(github_token=config.GITHUB_TOKEN)

class GitHubRepoRequest(BaseModel):
    repo_url: str
    branch: str = "main"
    include_patterns: List[str] = [".py", ".js", ".jsx", ".ts", ".tsx", ".java"]
    max_files: int = 50

class CodeAnalysisRequest(BaseModel):
    code: str
    language: str
    filename: str

class CodeAnalysisResponse(BaseModel):
    success: bool
    analysis: Dict[str, Any]
    generated_api_path: Optional[str] = None
    message: str

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
        
        # Get repository information (with fallback)
        try:
            repo_data = github_fetcher.get_repo_info(owner, repo)
        except ValueError as e:
            if "403" in str(e) or "429" in str(e) or "rate limit" in str(e).lower():
                # Use fallback method without API
                print(f"GitHub API access limited, using fallback: {e}")
                repo_data = github_fetcher.get_repo_info_fallback(owner, repo)
            else:
                raise e
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Try to clone/download repository (with fallback)
            try:
                # First try git clone (doesn't require API)
                repo_path = github_fetcher.clone_repo(owner, repo, temp_dir, request.branch)
            except Exception as clone_error:
                print(f"Git clone failed, trying direct ZIP download: {clone_error}")
                try:
                    # Try direct ZIP download (no API required)
                    zip_path = github_fetcher.download_repo_zip_direct(owner, repo, request.branch)
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    # Find the extracted directory
                    extracted_dirs = [d for d in Path(temp_dir).iterdir() if d.is_dir()]
                    repo_path = str(extracted_dirs[0]) if extracted_dirs else temp_dir
                    os.unlink(zip_path)
                except Exception as download_error:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Failed to download repository. Clone error: {clone_error}. Download error: {download_error}"
                    )
            
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
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{request.language}', delete=False) as temp_file:
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
            
            return CodeAnalysisResponse(
                success=True,
                analysis=analysis,
                generated_api_path=api_path,
                message=f"Successfully analyzed {request.filename} and generated API"
            )
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing code: {str(e)}")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload and analyze multiple source code files"""
    results = []
    
    for file in files:
        try:
            # Read file content
            content = await file.read()
            code = content.decode('utf-8')
            
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
    
    return {"results": results, "total_files": len(files)}

@app.get("/download/{project_name}")
async def download_generated_api(project_name: str):
    """Download generated API as a ZIP file"""
    try:
        api_path = config.GENERATED_DIR / project_name
        
        if not api_path.exists():
            raise HTTPException(status_code=404, detail="Generated API not found")
        
        # Create ZIP file
        zip_path = config.GENERATED_DIR / f"{project_name}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in api_path.rglob('*'):
                if file_path.is_file():
                    zipf.write(file_path, file_path.relative_to(api_path))
        
        return FileResponse(
            zip_path,
            media_type='application/zip',
            filename=f"{project_name}.zip"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating download: {str(e)}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.API_HOST, port=config.API_PORT)
