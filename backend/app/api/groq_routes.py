"""
API endpoints for testing Groq integration and analyzing code
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging

from ..services.groq_service import groq_service
from ..core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/groq", tags=["groq"])

class CodeAnalysisRequest(BaseModel):
    """Request model for code analysis"""
    code: str
    language: str = "python"
    
class FunctionAnalysisResponse(BaseModel):
    """Response model for function analysis"""
    function_name: str
    purpose: str
    input_parameters: List[Dict[str, Any]]
    return_type: str
    return_description: str
    http_method: str
    api_endpoint: str
    authentication_required: bool
    api_suitable: bool
    api_suitability_reason: str
    security_considerations: List[str]
    example_request: str
    example_response: str
    complexity_score: int
    dependencies: List[str]

class DocumentationRequest(BaseModel):
    """Request model for documentation generation"""
    endpoints: List[Dict[str, Any]]

class TestCaseRequest(BaseModel):
    """Request model for test case generation"""
    endpoint_info: Dict[str, Any]

@router.get("/models")
async def list_groq_models():
    """Get list of available Groq models"""
    try:
        models = await groq_service.list_available_models()
        return {
            "success": True,
            "models": models,
            "current_model": settings.GROQ_MODEL
        }
    except Exception as e:
        logger.error(f"Error fetching Groq models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-code")
async def analyze_code(request: CodeAnalysisRequest):
    """Analyze code function for API conversion suitability"""
    try:
        # Validate inputs
        if not request.code.strip():
            raise HTTPException(status_code=400, detail="Code cannot be empty")
        
        if len(request.code) > 10000:  # Limit code size
            raise HTTPException(status_code=400, detail="Code too long (max 10,000 characters)")
        
        # Analyze with Groq
        analysis = await groq_service.analyze_function_code(
            function_code=request.code,
            language=request.language
        )
        
        return {
            "success": True,
            "analysis": analysis,
            "language": request.language
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing code: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/generate-documentation")
async def generate_documentation(request: DocumentationRequest):
    """Generate API documentation for endpoints"""
    try:
        if not request.endpoints:
            raise HTTPException(status_code=400, detail="Endpoints list cannot be empty")
        
        documentation = await groq_service.generate_api_documentation(request.endpoints)
        
        return {
            "success": True,
            "documentation": documentation,
            "format": "markdown"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating documentation: {e}")
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")

@router.post("/generate-tests")
async def generate_test_cases(request: TestCaseRequest):
    """Generate test cases for an API endpoint"""
    try:
        if not request.endpoint_info:
            raise HTTPException(status_code=400, detail="Endpoint info cannot be empty")
        
        test_cases = await groq_service.generate_test_cases(request.endpoint_info)
        
        return {
            "success": True,
            "test_cases": test_cases,
            "count": len(test_cases)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating test cases: {e}")
        raise HTTPException(status_code=500, detail=f"Test generation failed: {str(e)}")

@router.post("/analyze-repository")
async def analyze_repository_structure(
    file_tree: Dict[str, Any],
    readme_content: Optional[str] = None
):
    """Analyze repository structure for API potential"""
    try:
        if not file_tree:
            raise HTTPException(status_code=400, detail="File tree cannot be empty")
        
        analysis = await groq_service.analyze_repository_structure(
            file_tree=file_tree,
            readme_content=readme_content or ""
        )
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        raise HTTPException(status_code=500, detail=f"Repository analysis failed: {str(e)}")

@router.get("/health")
async def groq_health_check():
    """Check if Groq service is working"""
    try:
        # Test with a simple request
        test_analysis = await groq_service.analyze_function_code(
            function_code="def hello(): return 'world'",
            language="python"
        )
        
        return {
            "success": True,
            "groq_service": "operational",
            "model": settings.GROQ_MODEL,
            "test_response": "passed" if test_analysis else "failed"
        }
        
    except Exception as e:
        logger.error(f"Groq health check failed: {e}")
        return {
            "success": False,
            "groq_service": "error",
            "error": str(e)
        }

@router.get("/usage-examples")
async def get_usage_examples():
    """Get examples of how to use the Groq API endpoints"""
    examples = {
        "analyze_code": {
            "description": "Analyze a function to determine API suitability",
            "endpoint": "/groq/analyze-code",
            "method": "POST",
            "example_request": {
                "code": "def calculate_fibonacci(n):\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)",
                "language": "python"
            }
        },
        "generate_documentation": {
            "description": "Generate API documentation for endpoints",
            "endpoint": "/groq/generate-documentation", 
            "method": "POST",
            "example_request": {
                "endpoints": [
                    {
                        "path": "/api/fibonacci",
                        "method": "GET",
                        "description": "Calculate fibonacci number",
                        "parameters": [{"name": "n", "type": "integer", "required": True}]
                    }
                ]
            }
        },
        "analyze_repository": {
            "description": "Analyze repository structure for API conversion potential",
            "endpoint": "/groq/analyze-repository",
            "method": "POST",
            "example_request": {
                "file_tree": {
                    "src/": {
                        "main.py": "file",
                        "utils.py": "file",
                        "models/": {
                            "user.py": "file"
                        }
                    },
                    "README.md": "file"
                },
                "readme_content": "This is a sample Python project for data processing..."
            }
        }
    }
    
    return {
        "success": True,
        "examples": examples,
        "documentation": "Use these examples to test the Groq API integration"
    }
