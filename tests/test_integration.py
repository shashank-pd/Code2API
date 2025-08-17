"""
Integration tests for the complete Code2API pipeline
"""
import pytest
import tempfile
import os
import json
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api.main import app
from src.parsers.code_parser import CodeParser
from src.ai.analyzer import AIAnalyzer
from src.generators.api_generator import APIGenerator
from src.config import config

client = TestClient(app)

class TestCompleteCodeAnalysisPipeline:
    """Test the complete code analysis pipeline from start to finish"""
    
    @pytest.fixture
    def sample_python_code(self):
        return '''
def calculate_average(numbers):
    """Calculate the average of a list of numbers"""
    if not numbers:
        return 0
    return sum(numbers) / len(numbers)

def get_user_info(user_id):
    """Get user information by ID"""
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com"
    }

class UserManager:
    def create_user(self, username, email, password):
        """Create a new user account"""
        return {"message": "User created successfully", "username": username}
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        return {"authenticated": True, "token": "sample_token"}
'''
    
    @pytest.fixture
    def mock_groq_response(self):
        """Mock Groq API response for testing"""
        return {
            "should_expose_as_api_endpoint": "yes",
            "http_method": "GET",
            "endpoint_path": "/test-endpoint",
            "description": "Test endpoint description",
            "requires_authentication": "no",
            "input_validation_requirements": "Basic validation",
            "expected_response_format": {"status": "success", "data": {}}
        }
    
    def test_parser_analyzer_generator_integration(self, sample_python_code, mock_groq_response):
        """Test integration between parser, analyzer, and generator"""
        # Step 1: Parse code
        parser = CodeParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(sample_python_code)
            temp_file_path = f.name
        
        try:
            parsed_code = parser.parse_file(temp_file_path)
            
            # Verify parsing results
            assert parsed_code.language == "python"
            assert len(parsed_code.functions) >= 2  # calculate_average, get_user_info
            assert len(parsed_code.classes) >= 1   # UserManager
            
            # Step 2: Analyze with AI (mocked)
            with patch('src.ai.analyzer.Groq') as mock_groq:
                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.choices[0].message.content = json.dumps(mock_groq_response)
                mock_client.chat.completions.create.return_value = mock_response
                mock_groq.return_value = mock_client
                
                analyzer = AIAnalyzer()
                analysis = analyzer.analyze_code(parsed_code)
                
                # Verify analysis results
                assert "api_endpoints" in analysis
                assert "security_recommendations" in analysis
                assert isinstance(analysis["api_endpoints"], list)
            
            # Step 3: Generate API
            with tempfile.TemporaryDirectory() as temp_dir:
                with patch.object(config, 'GENERATED_DIR', Path(temp_dir)):
                    generator = APIGenerator()
                    api_path = generator.generate_api(analysis, "test_integration")
                    
                    # Verify generated files
                    generated_path = Path(api_path)
                    assert generated_path.exists()
                    assert (generated_path / "main.py").exists()
                    assert (generated_path / "models.py").exists()
                    assert (generated_path / "auth.py").exists()
                    assert (generated_path / "requirements.txt").exists()
                    
                    # Verify main.py contains FastAPI code
                    main_content = (generated_path / "main.py").read_text()
                    assert "from fastapi import FastAPI" in main_content
                    assert "app = FastAPI" in main_content
        
        finally:
            os.unlink(temp_file_path)
    
    def test_full_api_endpoint_integration(self, sample_python_code, mock_groq_response):
        """Test the complete API endpoint from request to response"""
        
        # Mock the AI analyzer to avoid requiring API keys
        with patch('src.ai.analyzer.AIAnalyzer.analyze_code') as mock_analyze:
            mock_analyze.return_value = {
                "api_endpoints": [
                    {
                        "function_name": "calculate_average",
                        "http_method": "POST",
                        "endpoint_path": "/calculate-average",
                        "description": "Calculate average of numbers",
                        "needs_auth": False,
                        "parameters": [{"name": "numbers", "type": "list"}],
                        "is_async": False
                    }
                ],
                "security_recommendations": ["Validate input arrays"],
                "optimization_suggestions": ["Add input validation"]
            }
            
            # Test the /analyze endpoint
            response = client.post("/analyze", json={
                "code": sample_python_code,
                "language": "python",
                "filename": "test.py"
            })
            
            # Verify response structure
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "analysis" in data
            assert "generated_api_path" in data
            assert "timestamp" in data
            assert "processing_time" in data
            
            # Verify analysis content
            analysis = data["analysis"]
            assert len(analysis["api_endpoints"]) == 1
            assert analysis["api_endpoints"][0]["function_name"] == "calculate_average"
    
    def test_repository_analysis_integration(self, mock_groq_response):
        """Test repository analysis integration"""
        
        # Mock GitHub fetcher and AI analyzer
        with patch('src.github.repo_fetcher.GitHubRepoFetcher.get_repo_info') as mock_repo_info, \
             patch('src.github.repo_fetcher.GitHubRepoFetcher.clone_repo') as mock_clone, \
             patch('src.github.repo_fetcher.GitHubRepoFetcher.extract_supported_files') as mock_files, \
             patch('src.ai.analyzer.AIAnalyzer.analyze_code') as mock_analyze:
            
            # Mock repository information
            mock_repo_info.return_value = {
                "name": "test-repo",
                "description": "Test repository",
                "language": "Python",
                "stargazers_count": 100,
                "forks_count": 20,
                "html_url": "https://github.com/test/repo"
            }
            
            # Mock file extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                test_file = Path(temp_dir) / "test.py"
                test_file.write_text("def test(): pass")
                mock_files.return_value = [str(test_file)]
                mock_clone.return_value = temp_dir
                
                # Mock analysis
                mock_analyze.return_value = {
                    "api_endpoints": [],
                    "security_recommendations": [],
                    "optimization_suggestions": []
                }
                
                # Test repository analysis
                response = client.post("/analyze-repo", json={
                    "repo_url": "https://github.com/test/repo",
                    "branch": "main"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "repository_info" in data["analysis"]
                assert data["analysis"]["repository_info"]["name"] == "test-repo"
    
    def test_file_upload_integration(self, sample_python_code, mock_groq_response):
        """Test file upload and analysis integration"""
        
        with patch('src.ai.analyzer.AIAnalyzer.analyze_code') as mock_analyze:
            mock_analyze.return_value = {
                "api_endpoints": [{
                    "function_name": "test_function",
                    "http_method": "GET",
                    "endpoint_path": "/test",
                    "description": "Test function",
                    "needs_auth": False
                }],
                "security_recommendations": [],
                "optimization_suggestions": []
            }
            
            # Create test file
            test_file_content = sample_python_code.encode('utf-8')
            
            # Upload file
            response = client.post(
                "/upload",
                files={"files": ("test.py", test_file_content, "text/x-python")}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_files"] == 1
            assert data["successful_analyses"] == 1
            assert len(data["results"]) == 1
            assert data["results"][0]["success"] is True
    
    def test_generated_api_download_integration(self, sample_python_code, mock_groq_response):
        """Test the complete flow including API generation and download"""
        
        with patch('src.ai.analyzer.AIAnalyzer.analyze_code') as mock_analyze:
            mock_analyze.return_value = {
                "api_endpoints": [{
                    "function_name": "test_function",
                    "http_method": "GET",
                    "endpoint_path": "/test",
                    "description": "Test function"
                }],
                "security_recommendations": [],
                "optimization_suggestions": []
            }
            
            # First, analyze code to generate API
            response = client.post("/analyze", json={
                "code": sample_python_code,
                "language": "python",
                "filename": "test.py"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Extract project name from generated path
            generated_path = data["generated_api_path"]
            project_name = Path(generated_path).name
            
            # Try to download the generated API
            download_response = client.get(f"/download/{project_name}")
            
            # Should get a ZIP file
            assert download_response.status_code == 200
            assert download_response.headers["content-type"] == "application/zip"
    
    def test_error_handling_integration(self):
        """Test error handling throughout the pipeline"""
        
        # Test with invalid code
        response = client.post("/analyze", json={
            "code": "",  # Empty code
            "language": "python",
            "filename": "empty.py"
        })
        
        assert response.status_code == 422  # Validation error
        
        # Test with invalid language
        response = client.post("/analyze", json={
            "code": "print('hello')",
            "language": "invalid_language",
            "filename": "test.py"
        })
        
        assert response.status_code == 422  # Validation error
        
        # Test with invalid repository URL
        response = client.post("/analyze-repo", json={
            "repo_url": "invalid-url"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_security_validation_integration(self):
        """Test security validation throughout the pipeline"""
        
        # Test with potentially dangerous code
        dangerous_code = '''
import subprocess
def run_command(cmd):
    return subprocess.run(cmd, shell=True)
'''
        
        # Should still process but log warning
        with patch('src.ai.analyzer.AIAnalyzer.analyze_code') as mock_analyze:
            mock_analyze.return_value = {
                "api_endpoints": [],
                "security_recommendations": ["Avoid using subprocess with shell=True"],
                "optimization_suggestions": []
            }
            
            response = client.post("/analyze", json={
                "code": dangerous_code,
                "language": "python",
                "filename": "dangerous.py"
            })
            
            # Should succeed with warnings
            assert response.status_code == 200
    
    def test_performance_monitoring_integration(self, sample_python_code):
        """Test that performance monitoring works throughout the pipeline"""
        
        with patch('src.ai.analyzer.AIAnalyzer.analyze_code') as mock_analyze:
            mock_analyze.return_value = {
                "api_endpoints": [],
                "security_recommendations": [],
                "optimization_suggestions": []
            }
            
            response = client.post("/analyze", json={
                "code": sample_python_code,
                "language": "python",
                "filename": "test.py"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Should include timing information
            assert "processing_time" in data
            assert "timestamp" in data
            assert isinstance(data["processing_time"], (int, float))
            assert data["processing_time"] >= 0


class TestEndToEndScenarios:
    """Test realistic end-to-end scenarios"""
    
    def test_web_application_scenario(self):
        """Test analyzing a typical web application structure"""
        
        web_app_code = '''
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    return jsonify({"users": []})

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    data = request.json
    return jsonify({"message": "User created", "id": 123})

class UserService:
    def validate_user(self, user_data):
        """Validate user data"""
        return True
    
    def save_user(self, user_data):
        """Save user to database"""
        return {"id": 123}
'''
        
        with patch('src.ai.analyzer.AIAnalyzer.analyze_code') as mock_analyze:
            mock_analyze.return_value = {
                "api_endpoints": [
                    {
                        "function_name": "get_users",
                        "http_method": "GET",
                        "endpoint_path": "/api/users",
                        "description": "Get all users",
                        "needs_auth": False
                    },
                    {
                        "function_name": "create_user",
                        "http_method": "POST",
                        "endpoint_path": "/api/users",
                        "description": "Create a new user",
                        "needs_auth": True
                    }
                ],
                "security_recommendations": [
                    "Implement input validation",
                    "Add authentication to POST endpoints"
                ],
                "optimization_suggestions": [
                    "Add database connection pooling",
                    "Implement response caching"
                ]
            }
            
            response = client.post("/analyze", json={
                "code": web_app_code,
                "language": "python",
                "filename": "app.py"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify comprehensive analysis
            analysis = data["analysis"]
            assert len(analysis["api_endpoints"]) == 2
            assert len(analysis["security_recommendations"]) == 2
            assert len(analysis["optimization_suggestions"]) == 2
    
    def test_microservice_scenario(self):
        """Test analyzing a microservice codebase"""
        
        microservice_code = '''
import asyncio
from typing import List, Optional

class PaymentService:
    async def process_payment(self, amount: float, card_token: str):
        """Process a payment"""
        # Simulate async payment processing
        await asyncio.sleep(0.1)
        return {"transaction_id": "tx123", "status": "completed"}
    
    async def refund_payment(self, transaction_id: str):
        """Refund a payment"""
        await asyncio.sleep(0.1)
        return {"refund_id": "rf456", "status": "refunded"}

async def get_payment_status(transaction_id: str) -> dict:
    """Get payment status by transaction ID"""
    return {"transaction_id": transaction_id, "status": "completed"}

async def list_transactions(user_id: int, limit: int = 10) -> List[dict]:
    """List transactions for a user"""
    return [{"id": "tx123", "amount": 99.99}]
'''
        
        with patch('src.ai.analyzer.AIAnalyzer.analyze_code') as mock_analyze:
            mock_analyze.return_value = {
                "api_endpoints": [
                    {
                        "function_name": "process_payment",
                        "http_method": "POST",
                        "endpoint_path": "/payments",
                        "description": "Process a payment",
                        "needs_auth": True,
                        "is_async": True
                    },
                    {
                        "function_name": "get_payment_status",
                        "http_method": "GET",
                        "endpoint_path": "/payments/{transaction_id}",
                        "description": "Get payment status",
                        "needs_auth": True,
                        "is_async": True
                    }
                ],
                "security_recommendations": [
                    "Encrypt sensitive payment data",
                    "Implement strong authentication for payment endpoints",
                    "Add rate limiting for payment operations"
                ],
                "optimization_suggestions": [
                    "Use async operations for all I/O",
                    "Implement payment result caching",
                    "Add connection pooling for external services"
                ]
            }
            
            response = client.post("/analyze", json={
                "code": microservice_code,
                "language": "python",
                "filename": "payment_service.py"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            # Verify async handling and security focus
            analysis = data["analysis"]
            assert any(ep.get("is_async") for ep in analysis["api_endpoints"])
            assert any("payment" in rec.lower() for rec in analysis["security_recommendations"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])