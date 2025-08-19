"""
Groq API Service
Handles all interactions with Groq Cloud API for AI-powered code analysis.
"""

import os
import asyncio
from typing import List, Dict, Any, Optional
from groq import Groq, AsyncGroq
import json
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class GroqService:
    """Service for interacting with Groq Cloud API"""
    
    def __init__(self):
        """Initialize Groq service with API credentials"""
        self.api_key = settings.GROQ_API_KEY
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        
        # Initialize synchronous and asynchronous clients
        self.client = Groq(api_key=self.api_key)
        self.async_client = AsyncGroq(api_key=self.api_key)
        
        # Default model from settings
        self.default_model = getattr(settings, 'GROQ_MODEL', 'openai/gpt-oss-120b')
        
        # Rate limiting parameters
        self.max_retries = 3
        self.retry_delay = 1.0

    async def analyze_function_code(self, function_code: str, language: str = "python") -> Dict[str, Any]:
        """
        Analyze a function's code using Groq AI to determine API-suitability
        
        Args:
            function_code: The source code of the function
            language: Programming language of the function
            
        Returns:
            Dictionary containing analysis results
        """
        prompt = f"""
        Analyze this {language} function and determine its suitability for API conversion.
        
        Function code:
        ```{language}
        {function_code}
        ```
        
        Please analyze and return a JSON response with the following structure:
        {{
            "function_name": "extracted_function_name",
            "purpose": "brief description of what the function does",
            "input_parameters": [
                {{
                    "name": "param_name",
                    "type": "param_type",
                    "description": "param description",
                    "required": true/false
                }}
            ],
            "return_type": "return_type_description",
            "return_description": "description of what is returned",
            "http_method": "GET/POST/PUT/DELETE",
            "api_endpoint": "suggested_endpoint_path",
            "authentication_required": true/false,
            "api_suitable": true/false,
            "api_suitability_reason": "reason why suitable/not suitable for API",
            "security_considerations": ["list", "of", "security", "concerns"],
            "example_request": "example API request",
            "example_response": "example API response",
            "complexity_score": 1-10,
            "dependencies": ["list", "of", "dependencies"]
        }}
        
        Focus on:
        1. Whether this function is suitable for API conversion
        2. Appropriate HTTP method based on function behavior
        3. Parameter validation requirements
        4. Security and authentication needs
        5. Potential edge cases or error conditions
        """

        try:
            response = await self._make_completion_request(prompt)
            
            # Try to extract JSON from response
            content = response.choices[0].message.content
            
            # Find JSON in response (handle cases where there's extra text)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            else:
                # Fallback: create structured response from text
                return self._parse_text_analysis(content, function_code)
                
        except Exception as e:
            logger.error(f"Error analyzing function with Groq: {e}")
            return self._create_fallback_analysis(function_code, language)

    async def generate_api_documentation(self, endpoints: List[Dict[str, Any]]) -> str:
        """
        Generate comprehensive API documentation using Groq AI
        
        Args:
            endpoints: List of endpoint definitions
            
        Returns:
            Markdown documentation string
        """
        prompt = f"""
        Generate comprehensive API documentation in Markdown format for the following endpoints:
        
        {json.dumps(endpoints, indent=2)}
        
        Include:
        1. API Overview and Introduction
        2. Base URL and Authentication
        3. Detailed endpoint documentation with:
           - Description
           - HTTP method and path
           - Request parameters
           - Request/Response examples
           - Error codes and responses
        4. Rate limiting information
        5. Usage examples in Python, JavaScript, and curl
        6. Common error scenarios and troubleshooting
        
        Make it professional and comprehensive like OpenAPI documentation.
        """

        try:
            response = await self._make_completion_request(prompt, max_tokens=4000)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating documentation with Groq: {e}")
            return "# API Documentation\n\nError generating documentation. Please try again."

    async def generate_test_cases(self, endpoint_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate test cases for an API endpoint using Groq AI
        
        Args:
            endpoint_info: Information about the endpoint
            
        Returns:
            List of test case definitions
        """
        prompt = f"""
        Generate comprehensive test cases for this API endpoint:
        
        {json.dumps(endpoint_info, indent=2)}
        
        Return a JSON array of test cases with this structure:
        [
            {{
                "test_name": "descriptive_test_name",
                "test_type": "positive/negative/edge_case",
                "description": "what this test validates",
                "method": "HTTP_METHOD",
                "endpoint": "/endpoint/path",
                "headers": {{"header": "value"}},
                "request_body": {{"key": "value"}},
                "expected_status": 200,
                "expected_response": {{"expected": "response"}},
                "assertions": ["list", "of", "things", "to", "check"]
            }}
        ]
        
        Include:
        1. Positive test cases (valid inputs)
        2. Negative test cases (invalid inputs) 
        3. Edge cases (boundary conditions)
        4. Authentication tests
        5. Error handling tests
        """

        try:
            response = await self._make_completion_request(prompt)
            content = response.choices[0].message.content
            
            # Extract JSON array from response
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error generating test cases with Groq: {e}")
            return []

    async def analyze_repository_structure(self, file_tree: Dict[str, Any], readme_content: str = "") -> Dict[str, Any]:
        """
        Analyze repository structure to understand project type and architecture
        
        Args:
            file_tree: Repository file structure
            readme_content: Content of README file if available
            
        Returns:
            Analysis of repository structure and recommendations
        """
        prompt = f"""
        Analyze this repository structure and provide insights:
        
        File Tree:
        {json.dumps(file_tree, indent=2)}
        
        README Content:
        {readme_content[:2000]}  # Limit README content
        
        Provide analysis in JSON format:
        {{
            "project_type": "web_app/library/script/microservice/etc",
            "primary_language": "detected_language",
            "framework": "detected_framework",
            "architecture_pattern": "mvc/microservices/monolith/etc",
            "api_potential": "high/medium/low",
            "recommended_endpoints": [
                {{
                    "path": "/suggested/path",
                    "method": "GET/POST/etc",
                    "description": "what this endpoint would do",
                    "source_files": ["file1.py", "file2.py"]
                }}
            ],
            "complexity_assessment": "simple/moderate/complex",
            "security_considerations": ["list", "of", "security", "aspects"],
            "deployment_recommendations": ["list", "of", "deployment", "suggestions"],
            "documentation_quality": "good/fair/poor",
            "test_coverage_estimate": "high/medium/low/none"
        }}
        """

        try:
            response = await self._make_completion_request(prompt)
            content = response.choices[0].message.content
            
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            else:
                return {"error": "Could not parse analysis response"}
                
        except Exception as e:
            logger.error(f"Error analyzing repository structure with Groq: {e}")
            return {"error": f"Analysis failed: {str(e)}"}

    async def _make_completion_request(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.3) -> Any:
        """
        Make a completion request to Groq API with retry logic
        
        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0-2)
            
        Returns:
            Groq API response
        """
        for attempt in range(self.max_retries):
            try:
                response = await self.async_client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert software engineer and API designer. Provide accurate, helpful analysis and always return valid JSON when requested."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    model=self.default_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=0.9
                )
                return response
                
            except Exception as e:
                logger.warning(f"Groq API request attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    raise e

    def _parse_text_analysis(self, content: str, function_code: str) -> Dict[str, Any]:
        """Fallback parser for non-JSON responses"""
        return {
            "function_name": "unknown_function",
            "purpose": "Analysis failed - unable to parse response",
            "input_parameters": [],
            "return_type": "unknown",
            "return_description": "Could not determine return type",
            "http_method": "POST",
            "api_endpoint": "/unknown",
            "authentication_required": True,
            "api_suitable": False,
            "api_suitability_reason": "Analysis failed",
            "security_considerations": ["Manual review required"],
            "example_request": "N/A",
            "example_response": "N/A",
            "complexity_score": 5,
            "dependencies": [],
            "original_response": content
        }

    def _create_fallback_analysis(self, function_code: str, language: str) -> Dict[str, Any]:
        """Create basic fallback analysis when AI analysis fails"""
        return {
            "function_name": "extracted_function",
            "purpose": f"Function written in {language}",
            "input_parameters": [],
            "return_type": "unknown",
            "return_description": "Could not analyze return type",
            "http_method": "POST",
            "api_endpoint": "/api/function",
            "authentication_required": True,
            "api_suitable": True,
            "api_suitability_reason": "Basic analysis - manual review recommended",
            "security_considerations": ["Manual security review required"],
            "example_request": "Manual testing required",
            "example_response": "Manual testing required", 
            "complexity_score": 5,
            "dependencies": [],
            "analysis_status": "fallback"
        }

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        Get list of available Groq models
        
        Returns:
            List of available models with their details
        """
        try:
            response = await self.async_client.models.list()
            return [
                {
                    "id": model.id,
                    "object": model.object,
                    "created": model.created,
                    "owned_by": model.owned_by,
                    "active": model.active,
                    "context_window": getattr(model, 'context_window', None)
                }
                for model in response.data
            ]
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")
            return []

# Global instance
groq_service = GroqService()
