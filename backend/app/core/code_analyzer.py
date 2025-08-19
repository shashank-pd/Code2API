"""
AI-Powered Code Analysis Engine
Uses LLMs to understand code functionality and generate API suggestions
"""

import ast
import json
import asyncio
import time
import random
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
import logging

from groq import Groq
from .config import settings
from .repository_analyzer import FunctionInfo

logger = logging.getLogger(__name__)

@dataclass
class APIEndpoint:
    """Represents a suggested API endpoint"""
    function_name: str
    endpoint_path: str
    http_method: str
    description: str
    parameters: List[Dict[str, Any]]
    return_type: str
    needs_auth: bool
    class_name: Optional[str] = None
    tags: List[str] = None

@dataclass
class SecurityRecommendation:
    """Security recommendation for the code"""
    severity: str  # "high", "medium", "low"
    category: str  # "authentication", "input_validation", etc.
    description: str
    suggestion: str

@dataclass
class OptimizationSuggestion:
    """Code optimization suggestion"""
    category: str  # "performance", "maintainability", etc.
    description: str
    suggestion: str
    impact: str  # "high", "medium", "low"

class CodeAnalyzer:
    """AI-powered code analysis using LLMs with enhanced error handling and rate limiting"""
    
    def __init__(self, groq_api_key: Optional[str] = None):
        self.groq_api_key = groq_api_key
        self.groq_client = None
        
        # Rate limiting and retry configuration
        self.max_retries = 3
        self.base_delay = 1.0  # Base delay for exponential backoff
        self.max_delay = 30.0  # Maximum delay between retries
        
        if groq_api_key:
            try:
                self.groq_client = Groq(api_key=groq_api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {str(e)}")
        
        # AI prompts for different analysis tasks
        self.function_analysis_prompt = """
        Analyze this function and provide a detailed JSON response with the following structure:
        
        {
            "purpose": "Brief description of what this function does",
            "http_method": "GET|POST|PUT|DELETE|PATCH",
            "endpoint_path": "/suggested/api/path",
            "parameters": [
                {
                    "name": "param_name",
                    "type": "string|integer|boolean|array|object",
                    "required": true,
                    "description": "Parameter description",
                    "default": null
                }
            ],
            "return_type": "Description of what the function returns",
            "needs_authentication": true,
            "security_considerations": ["list", "of", "security", "concerns"],
            "optimization_suggestions": ["list", "of", "optimization", "ideas"],
            "api_tags": ["category1", "category2"]
        }
        
        Function code:
        ```{language}
        {code}
        ```
        
        Consider:
        1. Function name and parameters to determine appropriate HTTP method
        2. Whether the function modifies data (POST/PUT/DELETE) or retrieves data (GET)
        3. Security requirements based on function behavior
        4. RESTful API design principles
        
        Respond only with valid JSON.
        """

    async def _make_groq_request_with_retry(
        self, 
        messages: List[Dict[str, str]], 
        response_format: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[str]:
        """Make a Groq API request with exponential backoff retry logic"""
        if not self.groq_client:
            return None
            
        for attempt in range(self.max_retries + 1):
            try:
                request_params = {
                    "model": settings.GROQ_MODEL,
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.1),
                    "max_tokens": kwargs.get("max_tokens", 1000),
                }
                
                if response_format:
                    request_params["response_format"] = response_format
                
                response = self.groq_client.chat.completions.create(**request_params)
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error
                if "rate limit" in error_msg or "429" in error_msg:
                    if attempt < self.max_retries:
                        # Exponential backoff with jitter
                        delay = min(
                            self.base_delay * (2 ** attempt) + random.uniform(0, 1),
                            self.max_delay
                        )
                        logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {self.max_retries} retries")
                        return None
                
                # Check if it's a structured output error
                elif "json schema" in error_msg or "structured output" in error_msg:
                    logger.warning(f"Structured output error: {e}")
                    return None  # Will trigger fallback
                
                # Other errors
                else:
                    if attempt < self.max_retries:
                        delay = self.base_delay * (attempt + 1)
                        logger.warning(f"API error: {e}. Retrying in {delay}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        logger.error(f"API request failed after {self.max_retries} retries: {e}")
                        return None
        
        return None
        
        self.security_analysis_prompt = """
        Analyze this code for security vulnerabilities and provide recommendations.
        Return a JSON array of security issues found:
        
        [
            {
                "severity": "high|medium|low",
                "category": "authentication|authorization|input_validation|sql_injection|xss|csrf|etc",
                "description": "Description of the security issue",
                "suggestion": "How to fix this issue",
                "line_number": 123
            }
        ]
        
        Code to analyze:
        ```{language}
        {code}
        ```
        
        Focus on common security vulnerabilities like:
        - SQL injection possibilities
        - Input validation issues
        - Authentication/authorization problems
        - XSS vulnerabilities
        - CSRF issues
        - Insecure data handling
        """

    async def analyze_code(
        self, 
        code: str, 
        language: str, 
        filename: str
    ) -> Dict[str, Any]:
        """
        Analyze source code and generate API suggestions
        
        Args:
            code: Source code to analyze
            language: Programming language
            filename: Name of the source file
        
        Returns:
            Analysis results including API suggestions
        """
        try:
            logger.info(f"Analyzing {language} code from {filename}")
            
            # Parse code to extract functions
            functions = self._extract_functions_from_code(code, language, filename)
            
            # Analyze each function with AI
            api_endpoints = []
            security_recommendations = []
            optimization_suggestions = []
            
            for function in functions:
                try:
                    # Get function code snippet
                    function_code = self._get_function_code(code, function, language)
                    
                    # AI analysis
                    ai_result = await self._analyze_function_with_ai(
                        function_code, language, function
                    )
                    
                    if ai_result:
                        # Convert to API endpoint
                        endpoint = self._create_api_endpoint(function, ai_result)
                        api_endpoints.append(endpoint)
                        
                        # Extract security recommendations
                        if "security_considerations" in ai_result:
                            for concern in ai_result["security_considerations"]:
                                security_recommendations.append(
                                    SecurityRecommendation(
                                        severity="medium",
                                        category="general",
                                        description=concern,
                                        suggestion="Review and implement appropriate security measures"
                                    )
                                )
                        
                        # Extract optimization suggestions
                        if "optimization_suggestions" in ai_result:
                            for suggestion in ai_result["optimization_suggestions"]:
                                optimization_suggestions.append(
                                    OptimizationSuggestion(
                                        category="performance",
                                        description=suggestion,
                                        suggestion="Consider implementing this optimization",
                                        impact="medium"
                                    )
                                )
                
                except Exception as e:
                    logger.warning(f"Failed to analyze function {function.name}: {str(e)}")
                    continue
            
            return {
                "api_endpoints": [asdict(ep) for ep in api_endpoints],
                "security_recommendations": [sr.description for sr in security_recommendations],
                "optimization_suggestions": [os.description for os in optimization_suggestions],
                "functions_analyzed": len(functions),
                "language": language,
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Code analysis failed: {str(e)}")
            raise Exception(f"Code analysis failed: {str(e)}")

    async def analyze_repository_functions(
        self, 
        functions: List[FunctionInfo]
    ) -> Dict[str, Any]:
        """
        Analyze a list of functions extracted from a repository
        
        Args:
            functions: List of FunctionInfo objects
        
        Returns:
            Combined analysis results
        """
        try:
            logger.info(f"Analyzing {len(functions)} functions from repository")
            
            api_endpoints = []
            security_recommendations = []
            optimization_suggestions = []
            
            # Process functions in batches to avoid rate limits
            batch_size = 10
            for i in range(0, len(functions), batch_size):
                batch = functions[i:i+batch_size]
                
                # Process batch
                batch_results = await asyncio.gather(*[
                    self._analyze_function_info(func) for func in batch
                ], return_exceptions=True)
                
                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.warning(f"Function analysis failed: {str(result)}")
                        continue
                    
                    if result:
                        api_endpoints.extend(result.get("api_endpoints", []))
                        security_recommendations.extend(result.get("security_recommendations", []))
                        optimization_suggestions.extend(result.get("optimization_suggestions", []))
                
                # Add delay between batches to respect rate limits
                if i + batch_size < len(functions):
                    await asyncio.sleep(1)
            
            return {
                "api_endpoints": api_endpoints,
                "security_recommendations": security_recommendations,
                "optimization_suggestions": optimization_suggestions,
                "functions_analyzed": len(functions)
            }
            
        except Exception as e:
            logger.error(f"Repository function analysis failed: {str(e)}")
            raise Exception(f"Repository function analysis failed: {str(e)}")

    async def _analyze_function_info(self, function: FunctionInfo) -> Optional[Dict[str, Any]]:
        """Analyze a single FunctionInfo object"""
        try:
            # Create a simplified function representation for AI analysis
            function_code = f"""
def {function.name}({', '.join(function.args)}):
    \"\"\"{function.docstring or 'No docstring provided'}\"\"\"
    # Function implementation would be here
    pass
"""
            
            ai_result = await self._analyze_function_with_ai(
                function_code, "python", function
            )
            
            if ai_result:
                endpoint = self._create_api_endpoint(function, ai_result)
                return {
                    "api_endpoints": [asdict(endpoint)],
                    "security_recommendations": ai_result.get("security_considerations", []),
                    "optimization_suggestions": ai_result.get("optimization_suggestions", [])
                }
            
        except Exception as e:
            logger.warning(f"Failed to analyze function {function.name}: {str(e)}")
        
        return None

    def _extract_functions_from_code(
        self, 
        code: str, 
        language: str, 
        filename: str
    ) -> List[FunctionInfo]:
        """Extract function definitions from source code"""
        functions = []
        
        try:
            if language == "python":
                tree = ast.parse(code)
                
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        function_info = FunctionInfo(
                            name=node.name,
                            args=[arg.arg for arg in node.args.args],
                            docstring=ast.get_docstring(node),
                            return_annotation=self._get_annotation_string(node.returns),
                            line_number=node.lineno,
                            file_path=filename,
                            is_async=isinstance(node, ast.AsyncFunctionDef),
                            decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                            complexity=self._calculate_complexity(node)
                        )
                        functions.append(function_info)
            
            # Add support for other languages as needed
            
        except Exception as e:
            logger.warning(f"Failed to extract functions from {language} code: {str(e)}")
        
        return functions

    def _get_function_code(
        self, 
        full_code: str, 
        function: FunctionInfo, 
        language: str
    ) -> str:
        """Extract the specific function code from the full source"""
        try:
            lines = full_code.split('\n')
            start_line = function.line_number - 1
            
            # For Python, find the end of the function by indentation
            if language == "python":
                indent_level = len(lines[start_line]) - len(lines[start_line].lstrip())
                end_line = start_line + 1
                
                while end_line < len(lines):
                    line = lines[end_line]
                    if line.strip() and (len(line) - len(line.lstrip())) <= indent_level:
                        break
                    end_line += 1
                
                return '\n'.join(lines[start_line:end_line])
            
            # For other languages, return a reasonable snippet
            end_line = min(start_line + 20, len(lines))
            return '\n'.join(lines[start_line:end_line])
            
        except Exception:
            # Fallback: return function signature
            return f"def {function.name}({', '.join(function.args)}):\n    pass"

    async def _analyze_function_with_ai(
        self, 
        function_code: str, 
        language: str, 
        function: FunctionInfo
    ) -> Optional[Dict[str, Any]]:
        """Use AI to analyze a function and generate API suggestions"""
        if not self.groq_client:
            logger.warning("No AI client available for function analysis")
            return self._generate_fallback_analysis(function)
        
        try:
            # Simple and reliable approach using JSON object mode
            analysis_prompt = f"""
Analyze this {language} function from ANY programming language/framework for API conversion and generate ACTUAL implementation code:

Function: {function.name}
Arguments: {', '.join(function.args) if function.args else 'None'}
Docstring: {function.docstring or 'None'}
Language/Framework: {language}

Code:
```{language}
{function_code[:800]}
```

UNIVERSAL ANALYSIS - Handle ANY code type:
1. Web scraping functions → REST API endpoints for data extraction
2. Data processing functions → API endpoints for transformations
3. Mathematical calculations → Computation API endpoints
4. File operations → File management API endpoints
5. Database operations → Data API endpoints
6. Machine learning models → Prediction API endpoints
7. Authentication systems → Auth API endpoints
8. Utility functions → Helper API endpoints
9. Business logic → Domain-specific API endpoints
10. Integration functions → Third-party API bridges

Generate ACTUAL implementation (not placeholders):
- For math/calculations: implement real formulas
- For data processing: implement actual transformations
- For web scraping: implement actual extraction logic
- For ML models: implement prediction logic
- For file operations: implement file handling
- For databases: implement CRUD operations
- For utilities: implement helper functions

Return ONLY valid JSON:
{{
    "purpose": "detailed description of what function does and its real-world use case",
    "http_method": "GET|POST|PUT|DELETE",
    "endpoint_path": "/api/descriptive-path-based-on-function",
    "needs_authentication": false,
    "parameters": [
        {{"name": "param", "type": "number|string|boolean|array|object", "required": true, "description": "clear desc with examples"}}
    ],
    "return_type": "object|array|string|number|boolean",
    "api_suitable": true,
    "implementation_code": "complete FastAPI endpoint implementation with real logic",
    "security_considerations": ["specific security notes for this function type"],
    "optimization_notes": ["specific performance optimizations"],
    "dependencies": ["required packages/libraries for implementation"]
}}

"""
            
            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert code analyzer specializing in converting ANY programming language/framework code into REST APIs. You understand: Python, JavaScript, Java, C#, Go, Rust, PHP, Ruby, TypeScript, Kotlin, Swift, C++, and more. You can analyze web frameworks (Django, Flask, Express, Spring, Laravel), data science code (pandas, numpy, scikit-learn), automation scripts, utilities, business logic, and any other code type. Always generate REAL implementations, never placeholders. Return only valid JSON responses."
                },
                {"role": "user", "content": analysis_prompt}
            ]
            
            # Use simple JSON object mode (more reliable)
            result_text = await self._make_groq_request_with_retry(
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=800
            )
            
            if result_text:
                try:
                    # Parse the JSON response
                    analysis_result = json.loads(result_text)
                    
                    # Validate required fields
                    required_fields = [
                        "purpose", "http_method", "endpoint_path", "needs_authentication",
                        "parameters", "return_type", "api_suitable", "security_considerations",
                        "optimization_notes"
                    ]
                    
                    for field in required_fields:
                        if field not in analysis_result:
                            analysis_result[field] = self._get_default_value(field)
                    
                    logger.info(f"Successfully analyzed function {function.name}")
                    return analysis_result
                    
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed: {e}")
                    
            # If AI analysis fails, return fallback
            logger.info(f"Using fallback analysis for function {function.name}")
            return self._generate_fallback_analysis(function)
            
        except Exception as e:
            logger.error(f"Error analyzing function {function.name}: {e}")
            return self._generate_fallback_analysis(function)

    def _get_default_value(self, field: str) -> Any:
        """Get default values for missing fields"""
        defaults = {
            "purpose": "Function purpose not determined",
            "http_method": "POST",
            "endpoint_path": "/api/function",
            "needs_authentication": False,
            "parameters": [],
            "return_type": "object",
            "api_suitable": True,
            "security_considerations": [],
            "optimization_notes": []
        }
        return defaults.get(field, "")

    def _extract_json_from_response(self, response_text: str) -> Optional[str]:
        """Extract JSON content from AI response with various formatting"""
        try:
            # Remove markdown code blocks
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
                else:
                    response_text = response_text[start:].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
            
            # Find JSON object boundaries
            start_idx = response_text.find('{')
            if start_idx == -1:
                return None
            
            # Find matching closing brace using bracket counting
            brace_count = 0
            end_idx = -1
            for i, char in enumerate(response_text[start_idx:], start_idx):
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx == -1:
                return None
            
            return response_text[start_idx:end_idx]
            
        except Exception as e:
            logger.warning(f"Failed to extract JSON from response: {e}")
            return None

    def _generate_fallback_analysis(self, function: FunctionInfo) -> Dict[str, Any]:
        """Generate basic analysis when AI is unavailable"""
        # Determine HTTP method based on function name patterns
        name_lower = function.name.lower()
        
        if any(word in name_lower for word in ["get", "fetch", "find", "list", "search"]):
            http_method = "GET"
        elif any(word in name_lower for word in ["create", "add", "insert", "post"]):
            http_method = "POST"
        elif any(word in name_lower for word in ["update", "modify", "edit", "put"]):
            http_method = "PUT"
        elif any(word in name_lower for word in ["delete", "remove", "destroy"]):
            http_method = "DELETE"
        else:
            http_method = "POST"  # Default
        
        # Generate endpoint path
        endpoint_path = f"/{function.name.lower().replace('_', '-')}"
        if function.class_name:
            endpoint_path = f"/{function.class_name.lower()}{endpoint_path}"
        
        return {
            "purpose": function.docstring or f"Execute {function.name} function",
            "http_method": http_method,
            "endpoint_path": endpoint_path,
            "parameters": [
                {
                    "name": arg,
                    "type": "string",
                    "required": True,
                    "description": f"Parameter {arg}"
                } for arg in function.args if arg != "self"
            ],
            "return_type": "Response object",
            "needs_authentication": function.class_name is not None,
            "security_considerations": ["Validate input parameters", "Implement proper error handling"],
            "optimization_suggestions": ["Add input validation", "Consider caching if appropriate"],
            "api_tags": [function.class_name.lower()] if function.class_name else ["general"]
        }

    def _create_api_endpoint(
        self, 
        function: FunctionInfo, 
        ai_result: Dict[str, Any]
    ) -> APIEndpoint:
        """Create an APIEndpoint object from function info and AI analysis"""
        return APIEndpoint(
            function_name=function.name,
            endpoint_path=ai_result.get("endpoint_path", f"/{function.name}"),
            http_method=ai_result.get("http_method", "POST"),
            description=ai_result.get("purpose", function.docstring or "No description"),
            parameters=ai_result.get("parameters", []),
            return_type=ai_result.get("return_type", "object"),
            needs_auth=ai_result.get("needs_authentication", False),
            class_name=function.class_name,
            tags=ai_result.get("api_tags", [])
        )

    def _get_annotation_string(self, annotation) -> Optional[str]:
        """Convert AST annotation to string"""
        if annotation is None:
            return None
        try:
            return ast.unparse(annotation)
        except:
            return str(annotation)

    def _get_decorator_name(self, decorator) -> str:
        """Extract decorator name from AST node"""
        try:
            if isinstance(decorator, ast.Name):
                return decorator.id
            elif isinstance(decorator, ast.Attribute):
                return f"{decorator.value.id}.{decorator.attr}"
            else:
                return str(decorator)
        except:
            return "unknown"

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
