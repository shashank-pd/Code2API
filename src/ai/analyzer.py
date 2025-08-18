"""
AI-powered code analysis module
"""
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from ..parsers.code_parser import ParsedCode, Function, Class
from ..config import config

# Import Groq with error handling
try:
    from groq import Groq
except ImportError as e:
    raise ImportError(f"Groq package is required. Install with: pip install groq\nError: {e}")

class AIAnalyzer:
    """AI-powered code analysis using GroqCloud API"""
    
    def __init__(self, api_key: Optional[str] = None):
        api_key = api_key or config.GROQ_API_KEY or os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError(
                "Groq API key is required. Set it in .env file or GROQ_API_KEY environment variable. "
                "Get your API key from: https://console.groq.com/keys"
            )
        self.client = Groq(api_key=api_key)
        self.model = config.GROQ_MODEL
    
    def analyze_code(self, parsed_code: ParsedCode) -> Dict[str, Any]:
        """Analyze parsed code and generate API recommendations"""
        
        analysis = {
            "api_endpoints": [],
            "authentication_needed": [],
            "documentation": {},
            "security_recommendations": [],
            "optimization_suggestions": []
        }
        
        # Analyze functions
        for func in parsed_code.functions:
            endpoint_analysis = self._analyze_function_for_api(func, parsed_code.language)
            if endpoint_analysis:
                analysis["api_endpoints"].append(endpoint_analysis)
        
        # Analyze classes
        for cls in parsed_code.classes:
            class_analysis = self._analyze_class_for_api(cls, parsed_code.language)
            analysis["api_endpoints"].extend(class_analysis)
        
        # Security analysis
        security_analysis = self._analyze_security(parsed_code)
        analysis["security_recommendations"] = security_analysis
        
        return analysis
    
    def _analyze_function_for_api(self, func: Function, language: str) -> Optional[Dict[str, Any]]:
        """Analyze a function to determine if it should be an API endpoint - enhanced for GUI code"""
        
        # Skip private functions and common utility functions
        if func.name.startswith('_') or func.name in ['main', '__init__', 'setup', 'teardown']:
            return None
        
        prompt = f"""
        You are an expert code analyzer. Analyze this {language} function and determine if it contains business logic that can be converted to an API endpoint, even if it's currently mixed with GUI/UI code.

        Function Name: {func.name}
        Parameters: {func.parameters}
        Return Type: {func.return_type}
        Docstring: {func.docstring}
        Is Async: {func.is_async}
        Code Snippet: Available for analysis

        **Enhanced Analysis Instructions:**
        - Focus on extracting pure business logic from GUI/UI operations
        - Ignore GUI-specific operations (tkinter widgets, UI updates, DOM manipulation, etc.)
        - Identify mathematical calculations, data processing, and business rules
        - Extract potential input parameters (even if they come from UI widgets)
        - Determine what the function actually computes or processes
        - Consider what a pure function version would look like

        **Special Cases to Handle:**
        1. GUI Functions: Extract core calculations from UI event handlers
        2. Database Functions: Focus on CRUD operations
        3. File Operations: Consider file processing as API operations
        4. Calculations: Mathematical or algorithmic functions are perfect for APIs

        Please analyze and respond in JSON format:
        {{
            "has_api_potential": true/false,
            "function_name": "{func.name}",
            "http_method": "GET/POST/PUT/DELETE",
            "endpoint_path": "/suggested/path",
            "description": "What this API endpoint would do",
            "needs_auth": true/false,
            "input_validation": {{
                "required_params": [
                    {{"name": "param1", "type": "string", "description": "desc"}}
                ]
            }},
            "response_format": {{
                "content_type": "application/json",
                "body": {{"example": "response structure"}}
            }},
            "parameters": [
                {{"name": "param", "type": "string", "default": null}}
            ],
            "is_async": {func.is_async},
            "original_function": {{
                "name": "{func.name}",
                "parameters": {func.parameters},
                "return_type": "{func.return_type}",
                "docstring": "{func.docstring}",
                "line_number": {func.line_number},
                "is_async": {func.is_async},
                "decorators": {func.decorators},
                "visibility": "{func.visibility}"
            }}
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            
            content = response.choices[0].message.content
            
            # Handle JSON wrapped in markdown code blocks (common with Groq)
            if "```json" in content:
                json_start_marker = content.find("```json")
                json_end_marker = content.find("```", json_start_marker + 7)
                if json_end_marker != -1:
                    # Extract everything between the markers
                    between_markers = content[json_start_marker + 7:json_end_marker].strip()
                    # Find the actual JSON object within that content
                    json_start = between_markers.find('{')
                    if json_start != -1:
                        json_content = between_markers[json_start:]
                    else:
                        json_content = between_markers
                else:
                    # No closing marker found, take everything after ```json
                    after_marker = content[json_start_marker + 7:].strip()
                    json_start = after_marker.find('{')
                    if json_start != -1:
                        json_content = after_marker[json_start:]
                    else:
                        json_content = after_marker
            else:
                # Fallback to original method
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_content = content[json_start:json_end]
                else:
                    json_content = content
            
            if json_content:
                try:
                    analysis = json.loads(json_content)
                except json.JSONDecodeError as json_error:
                    print(f"JSON parsing error for function {func.name}: {json_error}")
                    print(f"Attempted to parse: {json_content[:500]}...")
                    # Try to extract JSON from the content more aggressively
                    try:
                        # Look for the first complete JSON object
                        brace_count = 0
                        start_idx = json_content.find('{')
                        if start_idx != -1:
                            for i, char in enumerate(json_content[start_idx:], start_idx):
                                if char == '{':
                                    brace_count += 1
                                elif char == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        # Found complete JSON object
                                        json_content = json_content[start_idx:i+1]
                                        break
                            analysis = json.loads(json_content)
                    except (json.JSONDecodeError, ValueError) as e:
                        print(f"Failed to extract valid JSON for function {func.name}: {e}")
                        return None
                
                # Check multiple possible field names for compatibility
                should_be_endpoint = (
                    analysis.get("should_be_api_endpoint", "").lower() == "yes" or
                    analysis.get("should_be_endpoint", "").lower() == "yes" or
                    analysis.get("expose_as_api_endpoint", "").lower() == "yes" or
                    analysis.get("should_expose_as_api", "").lower() == "yes" or
                    analysis.get("has_api_potential", False) == True
                )
                
                if should_be_endpoint:
                    return {
                        "function_name": func.name,
                        "http_method": analysis.get("http_method", "POST"),
                        "endpoint_path": analysis.get("endpoint_path", f"/{func.name}"),
                        "description": analysis.get("brief_description", analysis.get("description", "")),
                        "needs_auth": (
                            analysis.get("needs_authentication", "").lower() == "yes" or
                            analysis.get("authentication_required", "").lower() == "yes" or
                            analysis.get("requires_authentication", "").lower() == "yes"
                        ),
                        "input_validation": analysis.get("input_validation_requirements", analysis.get("input_validation", [])),
                        "response_format": analysis.get("expected_response_format", analysis.get("response_format", {})),
                        "parameters": func.parameters,
                        "is_async": func.is_async,
                        "original_function": asdict(func)
                    }
        except Exception as e:
            print(f"Error analyzing function {func.name}: {e}")
        
        return None
    
    def _analyze_class_for_api(self, cls: Class, language: str) -> List[Dict[str, Any]]:
        """Analyze a class to extract API endpoints from its methods"""
        endpoints = []
        
        # Skip certain classes
        if cls.name.lower() in ['test', 'config', 'exception', 'error']:
            return endpoints
        
        for method in cls.methods:
            # Skip private methods and constructors
            if method.name.startswith('_') or method.name in ['__init__', 'constructor']:
                continue
            
            # Create a modified function for analysis
            class_method = Function(
                name=f"{cls.name}_{method.name}",
                parameters=method.parameters,
                return_type=method.return_type,
                docstring=method.docstring,
                line_number=method.line_number,
                is_async=method.is_async,
                decorators=method.decorators,
                visibility=method.visibility
            )
            
            endpoint = self._analyze_function_for_api(class_method, language)
            if endpoint:
                endpoint["class_name"] = cls.name
                endpoint["method_name"] = method.name
                endpoints.append(endpoint)
        
        return endpoints
    
    def _analyze_security(self, parsed_code: ParsedCode) -> List[str]:
        """Analyze code for security considerations"""
        recommendations = []
        
        # Check for common security patterns
        security_keywords = [
            'password', 'secret', 'token', 'key', 'auth', 'login', 'user',
            'admin', 'root', 'sudo', 'execute', 'eval', 'exec'
        ]
        
        for func in parsed_code.functions:
            func_text = f"{func.name} {func.docstring or ''} {' '.join([p['name'] for p in func.parameters])}"
            
            for keyword in security_keywords:
                if keyword.lower() in func_text.lower():
                    recommendations.append(f"Function '{func.name}' may need authentication - contains security-related keyword: {keyword}")
                    break
        
        # Check for potentially dangerous operations
        dangerous_patterns = ['exec', 'eval', 'subprocess', 'os.system', 'shell']
        for func in parsed_code.functions:
            if any(pattern in func.name.lower() for pattern in dangerous_patterns):
                recommendations.append(f"Function '{func.name}' performs potentially dangerous operations - requires strict access control")
        
        return recommendations
    
    def generate_documentation(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate comprehensive API documentation"""
        docs = {}
        
        for endpoint in analysis["api_endpoints"]:
            prompt = f"""
            Generate comprehensive API documentation for this endpoint:
            
            Endpoint: {endpoint['http_method']} {endpoint['endpoint_path']}
            Function: {endpoint['function_name']}
            Description: {endpoint['description']}
            Parameters: {endpoint['parameters']}
            Authentication Required: {endpoint['needs_auth']}
            
            Please provide:
            1. Detailed description
            2. Request parameters documentation
            3. Response format documentation
            4. Example request
            5. Example response
            6. Error codes and messages
            """
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=config.MAX_TOKENS,
                    temperature=config.TEMPERATURE
                )
                
                docs[endpoint['endpoint_path']] = response.choices[0].message.content
            except Exception as e:
                print(f"Error generating documentation for {endpoint['endpoint_path']}: {e}")
                docs[endpoint['endpoint_path']] = endpoint['description']
        
        return docs
    
    def suggest_optimizations(self, parsed_code: ParsedCode) -> List[str]:
        """Suggest API optimizations"""
        suggestions = []
        
        # Check for functions that might benefit from caching
        for func in parsed_code.functions:
            if not func.parameters and func.return_type:
                suggestions.append(f"Function '{func.name}' with no parameters might benefit from caching")
        
        # Check for async functions that could be endpoints
        async_funcs = [f for f in parsed_code.functions if f.is_async]
        if async_funcs:
            suggestions.append(f"Found {len(async_funcs)} async functions - consider implementing async API endpoints for better performance")
        
        # Check for functions with many parameters
        complex_funcs = [f for f in parsed_code.functions if len(f.parameters) > 5]
        if complex_funcs:
            suggestions.append(f"Functions with many parameters found - consider using request body objects for complex inputs")
        
        return suggestions
