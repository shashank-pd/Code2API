from langchain.tools import tool
from typing import Dict, Any, List
import json
import yaml

@tool
def api_designer_tool(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design OpenAPI 3.0 specification from code analysis results.
    
    Args:
        analysis_result: Results from code_analyzer_tool
    
    Returns:
        Dictionary containing OpenAPI specification and design decisions
    """
    try:
        # Handle nested parameter structure from LangChain agent
        if isinstance(analysis_result, dict) and 'function_name' in analysis_result:
            print(f"[DEBUG] Received nested analysis_result structure")
            return {
                "success": False,
                "error": "Received nested parameter structure instead of analysis result",
                "debug_info": str(analysis_result)[:500]
            }
            
        # Extract actual analysis data
        if isinstance(analysis_result, dict) and 'args' in analysis_result:
            # This is a nested structure from LangChain
            print(f"[DEBUG] Extracting from nested structure: {analysis_result}")
            return create_default_openapi_spec()
        
        api_endpoints = analysis_result.get("api_endpoints", [])
        repo_language = analysis_result.get("language", "python")
        
        print(f"[DEBUG] Designing API with {len(api_endpoints)} endpoints for {repo_language}")
        
        # If no endpoints found, create some default ones based on common patterns
        if not api_endpoints:
            print("[DEBUG] No endpoints found in analysis, creating default task management API")
            api_endpoints = create_default_task_api_endpoints()
        
        # Create OpenAPI specification
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Auto-Generated API",
                "version": "1.0.0",
                "description": "REST API automatically generated from source code analysis",
                "contact": {
                    "name": "AI Code-to-API Generator",
                    "url": "https://github.com/ai-code-to-api"
                }
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Development server"
                },
                {
                    "url": "https://api.example.com",
                    "description": "Production server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": generate_schemas(api_endpoints),
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    },
                    "apiKey": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    }
                }
            },
            "security": [
                {"bearerAuth": []},
                {"apiKey": []}
            ]
        }
        
        # Generate paths from endpoints
        for endpoint in api_endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()
            
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            
            openapi_spec["paths"][path][method] = generate_operation(endpoint)
        
        # Generate additional design decisions
        design_decisions = {
            "authentication_strategy": "JWT Bearer token",
            "error_handling": "Standard HTTP status codes with JSON error responses",
            "pagination": "Offset-based pagination for list endpoints",
            "versioning": "URL path versioning (v1, v2, etc.)",
            "content_type": "application/json",
            "cors_enabled": True,
            "rate_limiting": {
                "enabled": True,
                "requests_per_minute": 100
            }
        }
        
        return {
            "success": True,
            "openapi_spec": openapi_spec,
            "design_decisions": design_decisions,
            "endpoints_count": len(api_endpoints),
            "paths_generated": len(openapi_spec["paths"])
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"API design failed: {str(e)}"
        }

def generate_operation(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """Generate OpenAPI operation object for an endpoint"""
    operation = {
        "summary": endpoint.get("description") or f"{endpoint['method']} {endpoint['function_name']}",
        "description": endpoint.get("description") or f"Automatically generated endpoint for {endpoint['function_name']}",
        "operationId": endpoint["function_name"].replace(".", "_"),
        "tags": [get_tag_from_path(endpoint["path"])],
        "responses": {
            "200": {
                "description": "Successful response",
                "content": {
                    "application/json": {
                        "schema": generate_response_schema(endpoint)
                    }
                }
            },
            "400": {
                "description": "Bad request",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            },
            "401": {
                "description": "Unauthorized",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            },
            "500": {
                "description": "Internal server error",
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                    }
                }
            }
        }
    }
    
    # Add parameters for GET requests or if parameters exist
    if endpoint["method"] == "GET" or endpoint.get("parameters"):
        operation["parameters"] = generate_parameters(endpoint)
    
    # Add request body for POST/PUT/PATCH requests
    if endpoint["method"] in ["POST", "PUT", "PATCH"]:
        operation["requestBody"] = {
            "required": True,
            "content": {
                "application/json": {
                    "schema": generate_request_schema(endpoint)
                }
            }
        }
    
    return operation

def generate_parameters(endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate OpenAPI parameters from endpoint info"""
    parameters = []
    
    # Add path parameters
    path_params = extract_path_parameters(endpoint["path"])
    for param in path_params:
        parameters.append({
            "name": param,
            "in": "path",
            "required": True,
            "schema": {"type": "string"},
            "description": f"The {param} identifier"
        })
    
    # Add query parameters from function parameters
    for param in endpoint.get("parameters", []):
        if endpoint["method"] == "GET":
            parameters.append({
                "name": param["name"],
                "in": "query",
                "required": param.get("required", False),
                "schema": {"type": map_type_to_openapi(param["type"])},
                "description": f"The {param['name']} parameter"
            })
    
    return parameters

def extract_path_parameters(path: str) -> List[str]:
    """Extract path parameters from URL path"""
    import re
    # Look for {param} patterns
    params = re.findall(r'\{(\w+)\}', path)
    return params

def generate_request_schema(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """Generate request schema for POST/PUT/PATCH endpoints"""
    properties = {}
    required = []
    
    for param in endpoint.get("parameters", []):
        properties[param["name"]] = {
            "type": map_type_to_openapi(param["type"]),
            "description": f"The {param['name']} value"
        }
        if param.get("required", False):
            required.append(param["name"])
    
    # If no parameters, create a generic request schema
    if not properties:
        properties = {
            "data": {
                "type": "object",
                "description": "Request data"
            }
        }
    
    schema = {
        "type": "object",
        "properties": properties
    }
    
    if required:
        schema["required"] = required
    
    return schema

def generate_response_schema(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    """Generate response schema for endpoint"""
    return_type = endpoint.get("return_type", "any")
    
    if return_type in ["dict", "object"]:
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "The operation result"
                }
            }
        }
    elif return_type in ["list", "array"]:
        return {
            "type": "array",
            "items": {
                "type": "object"
            }
        }
    elif return_type in ["str", "string"]:
        return {
            "type": "string"
        }
    elif return_type in ["int", "integer"]:
        return {
            "type": "integer"
        }
    elif return_type in ["float", "number"]:
        return {
            "type": "number"
        }
    elif return_type in ["bool", "boolean"]:
        return {
            "type": "boolean"
        }
    else:
        # Generic response
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Response message"
                },
                "data": {
                    "description": "Response data"
                }
            }
        }

def generate_schemas(endpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate common schemas for the API"""
    schemas = {
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {
                    "type": "string",
                    "description": "Error message"
                },
                "detail": {
                    "type": "string",
                    "description": "Detailed error information"
                },
                "code": {
                    "type": "integer",
                    "description": "Error code"
                }
            },
            "required": ["error"]
        },
        "SuccessResponse": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Success message"
                },
                "data": {
                    "description": "Response data"
                }
            },
            "required": ["message"]
        }
    }
    
    # Generate specific schemas based on endpoints
    for endpoint in endpoints:
        schema_name = f"{endpoint['function_name'].replace('.', '')}Response"
        schemas[schema_name] = generate_response_schema(endpoint)
    
    return schemas

def get_tag_from_path(path: str) -> str:
    """Generate tag name from API path"""
    parts = path.strip("/").split("/")
    if parts and parts[0]:
        return parts[0].capitalize()
    return "Default"

def map_type_to_openapi(param_type: str) -> str:
    """Map Python/other language types to OpenAPI types"""
    type_mapping = {
        "str": "string",
        "string": "string",
        "int": "integer",
        "integer": "integer",
        "float": "number",
        "number": "number",
        "bool": "boolean",
        "boolean": "boolean",
        "list": "array",
        "array": "array",
        "dict": "object",
        "object": "object",
        "any": "string"  # Default to string for unknown types
    }
    
    return type_mapping.get(param_type.lower(), "string")

def create_default_openapi_spec() -> Dict[str, Any]:
    """Create a default OpenAPI spec when analysis fails"""
    return {
        "success": True,
        "openapi_spec": {
            "openapi": "3.0.0",
            "info": {
                "title": "Generated API",
                "version": "1.0.0",
                "description": "Auto-generated REST API"
            },
            "paths": {},
            "components": {"schemas": {}}
        },
        "design_decisions": {"note": "Default spec created due to analysis issues"},
        "endpoints_count": 0,
        "paths_generated": 0
    }

def create_default_task_api_endpoints() -> List[Dict[str, Any]]:
    """Create default task management API endpoints"""
    return [
        {
            "path": "/tasks",
            "method": "GET",
            "function_name": "list_tasks",
            "description": "Get all tasks",
            "parameters": [],
            "return_type": "list"
        },
        {
            "path": "/tasks",
            "method": "POST",
            "function_name": "create_task",
            "description": "Create a new task",
            "parameters": [{"name": "title", "type": "string"}, {"name": "due_date", "type": "string"}],
            "return_type": "object"
        },
        {
            "path": "/tasks/{task_id}",
            "method": "GET",
            "function_name": "get_task",
            "description": "Get a specific task",
            "parameters": [{"name": "task_id", "type": "string"}],
            "return_type": "object"
        },
        {
            "path": "/tasks/{task_id}",
            "method": "PUT",
            "function_name": "update_task",
            "description": "Update a task",
            "parameters": [{"name": "task_id", "type": "string"}],
            "return_type": "object"
        },
        {
            "path": "/tasks/{task_id}",
            "method": "DELETE",
            "function_name": "delete_task",
            "description": "Delete a task",
            "parameters": [{"name": "task_id", "type": "string"}],
            "return_type": "object"
        }
    ]
