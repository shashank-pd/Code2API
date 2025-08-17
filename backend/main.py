from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import asyncio
import json
import zipfile
import tempfile
import shutil
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

from app.agents.master_agent import MasterAgent
from app.models.schemas import (
    WorkflowRequest, 
    WorkflowResponse, 
    UploadResponse, 
    FileAnalysisResult
)
from app.services.file_service import FileService

# Initialize FastAPI app
app = FastAPI(
    title="AI Code-to-API Generator",
    description="Transform GitHub repositories into fully functional REST APIs using AI agents",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services - will be properly initialized in startup event
master_agent = None
file_service = FileService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Code-to-API Generator Backend", "status": "running"}

@app.post("/api/run-workflow", response_model=WorkflowResponse)
async def run_workflow(request: WorkflowRequest, background_tasks: BackgroundTasks):
    """
    Main workflow endpoint that orchestrates the AI agent pipeline:
    1. Fetch code from GitHub
    2. Analyze code structure
    3. Design API endpoints
    4. Generate FastAPI code
    5. Apply security layers
    6. Generate tests
    7. Create documentation
    """
    try:
        # Check if master_agent is initialized
        if not master_agent:
            raise HTTPException(
                status_code=503, 
                detail="AI Agent not initialized. Please check GROQ_API_KEY configuration."
            )
        
        # Validate GitHub URL
        if not request.repo_url or not request.repo_url.startswith(('https://github.com/', 'http://github.com/')):
            raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")
        
        # Run the AI agent workflow
        result = await master_agent.execute_workflow(
            repo_url=request.repo_url,
            branch=request.branch or "main"
        )
        
        return WorkflowResponse(
            success=True,
            message="API generation completed successfully",
            analysis=result["analysis"],
            generated_api_path=result["api_path"],
            test_results=result["test_results"],
            documentation_url=result["documentation_url"]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload", response_model=UploadResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple code files for analysis
    """
    try:
        # Check if master_agent is initialized
        if not master_agent:
            raise HTTPException(
                status_code=503, 
                detail="AI Agent not initialized. Please check GROQ_API_KEY configuration."
            )
        
        results = []
        
        for file in files:
            if not file.filename:
                continue
                
            # Save uploaded file temporarily
            temp_path = await file_service.save_uploaded_file(file)
            
            try:
                # Analyze the file
                analysis_result = await master_agent.analyze_single_file(temp_path, file.filename)
                
                results.append(FileAnalysisResult(
                    filename=file.filename,
                    success=True,
                    analysis=analysis_result["analysis"],
                    api_path=analysis_result["api_path"]
                ))
                
            except Exception as e:
                results.append(FileAnalysisResult(
                    filename=file.filename,
                    success=False,
                    error=str(e)
                ))
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        return UploadResponse(
            success=True,
            message=f"Processed {len(files)} files",
            results=results
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download-by-path")
async def download_api_by_path(path: str):
    """
    Download generated API as ZIP file by path
    """
    try:
        logger.info(f"Download request for path: {path}")
        
        # Validate path
        if not path or ".." in path:
            raise HTTPException(status_code=400, detail="Invalid path")
        
        # Create ZIP file of the generated API
        zip_path = await file_service.create_api_zip(path)
        logger.info(f"Created ZIP at: {zip_path}")
        
        if not os.path.exists(zip_path):
            raise HTTPException(status_code=404, detail="API package not found")
        
        # Extract a safe filename from the path
        safe_filename = path.replace('/tmp/generated_apis/', '').replace('/tmp/', '').replace('/', '_').replace('\\', '_')
        if not safe_filename:
            safe_filename = "generated_api"
        
        # Return the ZIP file
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename=f"{safe_filename}.zip"
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found for path {path}: {e}")
        raise HTTPException(status_code=404, detail=f"API not found: {str(e)}")
    except Exception as e:
        logger.error(f"Error downloading API at path {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/download-current")
async def download_current_api():
    """
    Download the current generated API as ZIP file
    """
    try:
        # Use the current generated_api directory
        zip_path = await file_service.create_api_zip("generated_api")
        logger.info(f"Created current API ZIP at: {zip_path}")
        
        if not os.path.exists(zip_path):
            raise HTTPException(status_code=404, detail="No API generated yet")
        
        # Return the ZIP file
        return FileResponse(
            zip_path,
            media_type="application/zip",
            filename="generated_api.zip"
        )
        
    except FileNotFoundError as e:
        logger.error(f"No generated API found: {e}")
        raise HTTPException(status_code=404, detail="No API has been generated yet")
    except Exception as e:
        logger.error(f"Error downloading current API: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Detailed health check with service status"""
    try:
        # Check if all services are working
        health_status = {
            "status": "healthy" if master_agent else "degraded",
            "services": {
                "master_agent": "running" if master_agent else "not_initialized",
                "file_service": "running",
                "groq_api": await master_agent.check_groq_connection() if master_agent else "not_available",
                "github_api": await master_agent.check_github_connection() if master_agent else "not_available"
            }
        }
        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global master_agent
    try:
        master_agent = MasterAgent()
        await master_agent.initialize()
        print("✅ AI Code-to-API Generator Backend started successfully")
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        print("⚠️ Backend will run with limited functionality")
        # Don't raise to allow the server to start even without AI capabilities

@app.on_event("shutdown") 
async def shutdown_event():
    """Cleanup on shutdown"""
    await file_service.cleanup_temp_files()
    print("🔄 Backend shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
