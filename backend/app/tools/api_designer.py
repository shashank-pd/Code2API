from langchain.tools import tool
from typing import Dict, Any, List
import json
import yaml

@tool
def api_designer_tool(analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced API designer that creates domain-specific OpenAPI specifications
    based on repository purpose and business logic analysis.
    
    Args:
        analysis_result: Enhanced results from code_analyzer_tool
    
    Returns:
        Dictionary containing domain-specific OpenAPI specification and design decisions
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
        
        # Extract enhanced analysis data
        repo_purpose = analysis_result.get("repo_purpose", "general_utility")
        api_endpoints = analysis_result.get("api_endpoints", [])
        repo_language = analysis_result.get("language", "python")
        main_functionality = analysis_result.get("main_functionality", [])
        data_models = analysis_result.get("data_models", [])
        
        print(f"[DEBUG] Designing {repo_purpose} API with {len(api_endpoints)} endpoints for {repo_language}")
        
        # If no endpoints found, create domain-specific ones
        if not api_endpoints:
            print(f"[DEBUG] No endpoints found, creating {repo_purpose}-specific API")
            api_endpoints = create_domain_specific_endpoints(repo_purpose, main_functionality, data_models)
        
        # Create domain-specific OpenAPI specification
        openapi_spec = create_enhanced_openapi_spec(
            repo_purpose, api_endpoints, main_functionality, data_models, repo_language
        )
        
        # Generate paths from endpoints
        for endpoint in api_endpoints:
            path = endpoint["path"]
            method = endpoint["method"].lower()
            
            if path not in openapi_spec["paths"]:
                openapi_spec["paths"][path] = {}
            
            openapi_spec["paths"][path][method] = generate_operation(endpoint)
        
        # Generate domain-specific design decisions
        design_decisions = generate_domain_specific_design_decisions(
            repo_purpose, api_endpoints, analysis_result
        )
        
        return {
            "success": True,
            "openapi_spec": openapi_spec,
            "design_decisions": design_decisions,
            "endpoints_count": len(api_endpoints),
            "paths_generated": len(openapi_spec["paths"]),
            "repo_purpose": repo_purpose,
            "domain_specific_features": get_domain_specific_features(repo_purpose),
            "business_logic_mapping": extract_business_logic_mapping(main_functionality)
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

def create_domain_specific_endpoints(repo_purpose: str, main_functionality: List[Dict], data_models: List[Dict]) -> List[Dict[str, Any]]:
    """Create domain-specific API endpoints based on repository purpose and functionality"""
    if repo_purpose == "data_analysis":
        return create_data_analysis_endpoints(main_functionality)
    elif repo_purpose == "machine_learning":
        return create_ml_endpoints(main_functionality)
    elif repo_purpose == "file_processing":
        return create_file_processing_endpoints(main_functionality)
    elif repo_purpose == "web_scraping":
        return create_web_scraping_endpoints(main_functionality)
    elif repo_purpose == "database":
        return create_database_endpoints(data_models)
    elif repo_purpose == "automation":
        return create_automation_endpoints(main_functionality)
    elif repo_purpose == "security":
        return create_security_endpoints(main_functionality)
    elif repo_purpose == "social_media":
        return create_social_media_endpoints(main_functionality)
    elif repo_purpose == "crypto":
        return create_crypto_endpoints(main_functionality)
    elif repo_purpose == "game":
        return create_game_endpoints(main_functionality)
    elif repo_purpose == "cli_tool":
        return create_cli_endpoints(main_functionality)
    else:
        return create_default_task_api_endpoints()

def create_data_analysis_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for data analysis repositories"""
    endpoints = [
        {
            "path": "/analyze",
            "method": "POST",
            "function_name": "analyze_data",
            "description": "Analyze uploaded dataset using repository's analysis functions",
            "parameters": [{"name": "data", "type": "object", "required": True}, {"name": "analysis_type", "type": "string", "required": False}],
            "return_type": "object"
        },
        {
            "path": "/visualize",
            "method": "POST",
            "function_name": "create_visualization",
            "description": "Generate visualizations from data",
            "parameters": [{"name": "data", "type": "object", "required": True}, {"name": "chart_type", "type": "string", "required": False}],
            "return_type": "object"
        },
        {
            "path": "/report",
            "method": "POST",
            "function_name": "generate_report",
            "description": "Generate comprehensive analysis report",
            "parameters": [{"name": "analysis_id", "type": "string", "required": True}],
            "return_type": "object"
        }
    ]
    
    # Add function-specific endpoints
    for func in main_functionality:
        if func["type"] == "function" and any(keyword in func["name"].lower() for keyword in ["process", "calculate", "analyze", "compute"]):
            endpoints.append({
                "path": f"/{func['name'].replace('_', '-')}",
                "method": "POST",
                "function_name": func["name"],
                "description": func["description"],
                "parameters": [{"name": "input_data", "type": "object", "required": True}],
                "return_type": "object"
            })
    
    return endpoints

def create_ml_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for machine learning repositories"""
    endpoints = [
        {
            "path": "/predict",
            "method": "POST",
            "function_name": "predict",
            "description": "Make predictions using the trained model",
            "parameters": [{"name": "input_features", "type": "object", "required": True}, {"name": "model_version", "type": "string", "required": False}],
            "return_type": "object"
        },
        {
            "path": "/train",
            "method": "POST",
            "function_name": "train_model",
            "description": "Train or retrain the machine learning model",
            "parameters": [{"name": "training_data", "type": "object", "required": True}, {"name": "hyperparameters", "type": "object", "required": False}],
            "return_type": "object"
        },
        {
            "path": "/evaluate",
            "method": "POST",
            "function_name": "evaluate_model",
            "description": "Evaluate model performance",
            "parameters": [{"name": "test_data", "type": "object", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/models",
            "method": "GET",
            "function_name": "list_models",
            "description": "List available models",
            "parameters": [],
            "return_type": "array"
        }
    ]
    
    # Add specific ML function endpoints
    for func in main_functionality:
        if func["type"] == "function":
            func_name = func["name"].lower()
            if any(keyword in func_name for keyword in ["preprocess", "feature", "transform", "encode"]):
                endpoints.append({
                    "path": f"/preprocess/{func['name'].replace('_', '-')}",
                    "method": "POST",
                    "function_name": func["name"],
                    "description": f"Data preprocessing: {func['description']}",
                    "parameters": [{"name": "data", "type": "object", "required": True}],
                    "return_type": "object"
                })
    
    return endpoints

def create_file_processing_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for file processing repositories"""
    endpoints = [
        {
            "path": "/upload",
            "method": "POST",
            "function_name": "upload_file",
            "description": "Upload file for processing",
            "parameters": [{"name": "file", "type": "file", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/process",
            "method": "POST",
            "function_name": "process_file",
            "description": "Process uploaded file using repository logic",
            "parameters": [{"name": "file_id", "type": "string", "required": True}, {"name": "options", "type": "object", "required": False}],
            "return_type": "object"
        },
        {
            "path": "/convert",
            "method": "POST",
            "function_name": "convert_file",
            "description": "Convert file to different format",
            "parameters": [{"name": "file_id", "type": "string", "required": True}, {"name": "target_format", "type": "string", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/download/{file_id}",
            "method": "GET",
            "function_name": "download_file",
            "description": "Download processed file",
            "parameters": [{"name": "file_id", "type": "string", "required": True}],
            "return_type": "file"
        }
    ]
    
    # Add specific processing function endpoints
    for func in main_functionality:
        if func["type"] == "function" and any(keyword in func["name"].lower() for keyword in ["parse", "extract", "transform", "validate"]):
            endpoints.append({
                "path": f"/operations/{func['name'].replace('_', '-')}",
                "method": "POST",
                "function_name": func["name"],
                "description": func["description"],
                "parameters": [{"name": "input", "type": "object", "required": True}],
                "return_type": "object"
            })
    
    return endpoints

def create_web_scraping_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for web scraping repositories"""
    return [
        {
            "path": "/scrape",
            "method": "POST",
            "function_name": "scrape_url",
            "description": "Scrape data from a URL",
            "parameters": [{"name": "url", "type": "string", "required": True}, {"name": "selectors", "type": "object", "required": False}],
            "return_type": "object"
        },
        {
            "path": "/scrape/batch",
            "method": "POST",
            "function_name": "scrape_multiple",
            "description": "Scrape data from multiple URLs",
            "parameters": [{"name": "urls", "type": "array", "required": True}],
            "return_type": "array"
        },
        {
            "path": "/extract",
            "method": "POST",
            "function_name": "extract_data",
            "description": "Extract specific data from scraped content",
            "parameters": [{"name": "content", "type": "string", "required": True}, {"name": "extraction_rules", "type": "object", "required": True}],
            "return_type": "object"
        }
    ]

def create_database_endpoints(data_models: List[Dict]) -> List[Dict[str, Any]]:
    """Create CRUD endpoints for database repositories"""
    endpoints = []
    
    if not data_models:
        # Create generic database endpoints
        return [
            {
                "path": "/records",
                "method": "GET",
                "function_name": "get_records",
                "description": "Get all records",
                "parameters": [{"name": "limit", "type": "integer", "required": False}, {"name": "offset", "type": "integer", "required": False}],
                "return_type": "array"
            },
            {
                "path": "/records",
                "method": "POST",
                "function_name": "create_record",
                "description": "Create new record",
                "parameters": [{"name": "data", "type": "object", "required": True}],
                "return_type": "object"
            }
        ]
    
    # Create CRUD endpoints for each data model
    for model in data_models:
        model_name = model["name"].lower()
        endpoints.extend([
            {
                "path": f"/{model_name}s",
                "method": "GET",
                "function_name": f"get_{model_name}s",
                "description": f"Get all {model_name} records",
                "parameters": [{"name": "limit", "type": "integer", "required": False}, {"name": "offset", "type": "integer", "required": False}],
                "return_type": "array"
            },
            {
                "path": f"/{model_name}s",
                "method": "POST",
                "function_name": f"create_{model_name}",
                "description": f"Create new {model_name}",
                "parameters": [{"name": model_name, "type": "object", "required": True}],
                "return_type": "object"
            },
            {
                "path": f"/{model_name}s/{{id}}",
                "method": "GET",
                "function_name": f"get_{model_name}",
                "description": f"Get {model_name} by ID",
                "parameters": [{"name": "id", "type": "string", "required": True}],
                "return_type": "object"
            },
            {
                "path": f"/{model_name}s/{{id}}",
                "method": "PUT",
                "function_name": f"update_{model_name}",
                "description": f"Update {model_name}",
                "parameters": [{"name": "id", "type": "string", "required": True}, {"name": model_name, "type": "object", "required": True}],
                "return_type": "object"
            },
            {
                "path": f"/{model_name}s/{{id}}",
                "method": "DELETE",
                "function_name": f"delete_{model_name}",
                "description": f"Delete {model_name}",
                "parameters": [{"name": "id", "type": "string", "required": True}],
                "return_type": "object"
            }
        ])
    
    return endpoints

def create_automation_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for automation repositories"""
    return [
        {
            "path": "/tasks/schedule",
            "method": "POST",
            "function_name": "schedule_task",
            "description": "Schedule an automation task",
            "parameters": [{"name": "task_config", "type": "object", "required": True}, {"name": "schedule", "type": "string", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/tasks/execute",
            "method": "POST",
            "function_name": "execute_task",
            "description": "Execute automation task immediately",
            "parameters": [{"name": "task_id", "type": "string", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/tasks",
            "method": "GET",
            "function_name": "list_tasks",
            "description": "List all automation tasks",
            "parameters": [],
            "return_type": "array"
        }
    ]

def create_security_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for security repositories"""
    return [
        {
            "path": "/encrypt",
            "method": "POST",
            "function_name": "encrypt_data",
            "description": "Encrypt sensitive data",
            "parameters": [{"name": "data", "type": "string", "required": True}, {"name": "algorithm", "type": "string", "required": False}],
            "return_type": "object"
        },
        {
            "path": "/decrypt",
            "method": "POST",
            "function_name": "decrypt_data",
            "description": "Decrypt encrypted data",
            "parameters": [{"name": "encrypted_data", "type": "string", "required": True}, {"name": "key", "type": "string", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/hash",
            "method": "POST",
            "function_name": "hash_data",
            "description": "Generate secure hash",
            "parameters": [{"name": "data", "type": "string", "required": True}, {"name": "algorithm", "type": "string", "required": False}],
            "return_type": "object"
        }
    ]

def create_social_media_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for social media repositories"""
    return [
        {
            "path": "/posts",
            "method": "GET",
            "function_name": "get_posts",
            "description": "Get social media posts",
            "parameters": [{"name": "platform", "type": "string", "required": False}, {"name": "limit", "type": "integer", "required": False}],
            "return_type": "array"
        },
        {
            "path": "/posts",
            "method": "POST",
            "function_name": "create_post",
            "description": "Create new social media post",
            "parameters": [{"name": "content", "type": "string", "required": True}, {"name": "platform", "type": "string", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/analyze",
            "method": "POST",
            "function_name": "analyze_engagement",
            "description": "Analyze social media engagement",
            "parameters": [{"name": "post_id", "type": "string", "required": True}],
            "return_type": "object"
        }
    ]

def create_crypto_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for cryptocurrency repositories"""
    return [
        {
            "path": "/wallet/balance",
            "method": "GET",
            "function_name": "get_balance",
            "description": "Get wallet balance",
            "parameters": [{"name": "address", "type": "string", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/transaction",
            "method": "POST",
            "function_name": "create_transaction",
            "description": "Create new transaction",
            "parameters": [{"name": "from_address", "type": "string", "required": True}, {"name": "to_address", "type": "string", "required": True}, {"name": "amount", "type": "number", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/price",
            "method": "GET",
            "function_name": "get_price",
            "description": "Get cryptocurrency price",
            "parameters": [{"name": "symbol", "type": "string", "required": True}],
            "return_type": "object"
        }
    ]

def create_game_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for game repositories"""
    return [
        {
            "path": "/game/start",
            "method": "POST",
            "function_name": "start_game",
            "description": "Start new game session",
            "parameters": [{"name": "player_id", "type": "string", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/game/move",
            "method": "POST",
            "function_name": "make_move",
            "description": "Make game move",
            "parameters": [{"name": "game_id", "type": "string", "required": True}, {"name": "move", "type": "object", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/leaderboard",
            "method": "GET",
            "function_name": "get_leaderboard",
            "description": "Get game leaderboard",
            "parameters": [{"name": "limit", "type": "integer", "required": False}],
            "return_type": "array"
        }
    ]

def create_cli_endpoints(main_functionality: List[Dict]) -> List[Dict[str, Any]]:
    """Create endpoints for CLI tool repositories"""
    return [
        {
            "path": "/execute",
            "method": "POST",
            "function_name": "execute_command",
            "description": "Execute CLI command via API",
            "parameters": [{"name": "command", "type": "string", "required": True}, {"name": "arguments", "type": "array", "required": False}],
            "return_type": "object"
        },
        {
            "path": "/help",
            "method": "GET",
            "function_name": "get_help",
            "description": "Get available commands and usage",
            "parameters": [],
            "return_type": "object"
        }
    ]

def create_enhanced_openapi_spec(repo_purpose: str, api_endpoints: List[Dict], main_functionality: List[Dict], data_models: List[Dict], repo_language: str) -> Dict[str, Any]:
    """Create enhanced OpenAPI specification based on repository purpose"""
    
    # Determine API title and description based on purpose
    title_mapping = {
        "data_analysis": "Data Analysis API",
        "machine_learning": "Machine Learning API",
        "file_processing": "File Processing API",
        "web_scraping": "Web Scraping API",
        "database": "Database Management API",
        "automation": "Automation API",
        "security": "Security Tools API",
        "social_media": "Social Media API",
        "crypto": "Cryptocurrency API",
        "game": "Gaming API",
        "cli_tool": "CLI Tool API",
        "web_api": "Web Service API"
    }
    
    description_mapping = {
        "data_analysis": "API for data analysis, visualization, and reporting functionalities",
        "machine_learning": "API for machine learning model training, prediction, and evaluation",
        "file_processing": "API for file upload, processing, conversion, and download operations",
        "web_scraping": "API for web scraping, data extraction, and content analysis",
        "database": "API for database operations, CRUD functionality, and data management",
        "automation": "API for task automation, scheduling, and workflow management",
        "security": "API for encryption, decryption, hashing, and security operations",
        "social_media": "API for social media management, posting, and analytics",
        "crypto": "API for cryptocurrency operations, wallet management, and blockchain interactions",
        "game": "API for game mechanics, player management, and leaderboards",
        "cli_tool": "API wrapper for command-line tool functionality",
        "web_api": "Web service API with business logic endpoints"
    }
    
    title = title_mapping.get(repo_purpose, "Auto-Generated API")
    description = description_mapping.get(repo_purpose, "REST API automatically generated from source code analysis")
    
    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": "1.0.0",
            "description": description,
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
            "schemas": generate_enhanced_schemas(api_endpoints, data_models, repo_purpose),
            "securitySchemes": get_security_schemes(repo_purpose)
        },
        "security": get_security_requirements(repo_purpose)
    }
    
    # Generate paths from endpoints
    for endpoint in api_endpoints:
        path = endpoint["path"]
        method = endpoint["method"].lower()
        
        if path not in openapi_spec["paths"]:
            openapi_spec["paths"][path] = {}
        
        openapi_spec["paths"][path][method] = generate_enhanced_operation(endpoint, repo_purpose)
    
    return openapi_spec

def generate_domain_specific_design_decisions(repo_purpose: str, api_endpoints: List[Dict], analysis_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate domain-specific design decisions"""
    
    base_decisions = {
        "authentication_strategy": "JWT Bearer token",
        "error_handling": "Standard HTTP status codes with JSON error responses",
        "content_type": "application/json",
        "cors_enabled": True,
        "repo_purpose": repo_purpose
    }
    
    # Add purpose-specific decisions
    if repo_purpose == "machine_learning":
        base_decisions.update({
            "model_versioning": "Semantic versioning for model endpoints",
            "async_processing": "Long-running training jobs use async patterns",
            "data_validation": "Strict input validation for ML features",
            "rate_limiting": {"enabled": True, "requests_per_minute": 50}
        })
    elif repo_purpose == "file_processing":
        base_decisions.update({
            "file_upload": "Multipart form data for file uploads",
            "streaming": "Streaming responses for large file downloads",
            "file_size_limits": "Max 100MB per file upload",
            "rate_limiting": {"enabled": True, "requests_per_minute": 20}
        })
    elif repo_purpose == "data_analysis":
        base_decisions.update({
            "pagination": "Cursor-based pagination for large datasets",
            "caching": "Result caching for expensive computations",
            "batch_processing": "Batch endpoints for multiple analyses",
            "rate_limiting": {"enabled": True, "requests_per_minute": 30}
        })
    elif repo_purpose == "security":
        base_decisions.update({
            "enhanced_auth": "Multi-factor authentication for sensitive operations",
            "audit_logging": "Comprehensive audit trail for all operations",
            "encryption": "All data encrypted at rest and in transit",
            "rate_limiting": {"enabled": True, "requests_per_minute": 10}
        })
    else:
        base_decisions.update({
            "pagination": "Offset-based pagination for list endpoints",
            "versioning": "URL path versioning (v1, v2, etc.)",
            "rate_limiting": {"enabled": True, "requests_per_minute": 100}
        })
    
    return base_decisions

def get_domain_specific_features(repo_purpose: str) -> List[str]:
    """Get domain-specific features for the API"""
    features_mapping = {
        "data_analysis": ["Data visualization", "Statistical analysis", "Report generation", "Data export"],
        "machine_learning": ["Model training", "Batch prediction", "Model evaluation", "Feature engineering"],
        "file_processing": ["File upload/download", "Format conversion", "Batch processing", "File validation"],
        "web_scraping": ["URL scraping", "Content extraction", "Rate limiting", "Data cleaning"],
        "database": ["CRUD operations", "Query optimization", "Data relationships", "Transaction support"],
        "automation": ["Task scheduling", "Workflow management", "Event triggers", "Status monitoring"],
        "security": ["Encryption/Decryption", "Secure hashing", "Key management", "Audit logging"],
        "social_media": ["Post management", "Engagement analytics", "Multi-platform support", "Content scheduling"],
        "crypto": ["Wallet management", "Transaction processing", "Price tracking", "Blockchain integration"],
        "game": ["Game state management", "Player statistics", "Leaderboards", "Match making"],
        "cli_tool": ["Command execution", "Parameter validation", "Help system", "Output formatting"]
    }
    
    return features_mapping.get(repo_purpose, ["General purpose API", "RESTful design", "JSON responses"])

def extract_business_logic_mapping(main_functionality: List[Dict]) -> Dict[str, Any]:
    """Extract business logic mapping from functionality analysis"""
    mapping = {
        "core_functions": [],
        "data_operations": [],
        "utility_functions": [],
        "integration_points": []
    }
    
    for func in main_functionality:
        func_name = func.get("name", "").lower()
        func_type = func.get("type", "function")
        
        if any(keyword in func_name for keyword in ["process", "analyze", "calculate", "compute"]):
            mapping["core_functions"].append(func["name"])
        elif any(keyword in func_name for keyword in ["get", "set", "save", "load", "fetch"]):
            mapping["data_operations"].append(func["name"])
        elif any(keyword in func_name for keyword in ["validate", "format", "convert", "transform"]):
            mapping["utility_functions"].append(func["name"])
        elif any(keyword in func_name for keyword in ["api", "client", "request", "response"]):
            mapping["integration_points"].append(func["name"])
    
    return mapping

def get_security_schemes(repo_purpose: str) -> Dict[str, Any]:
    """Get appropriate security schemes based on repository purpose"""
    base_schemes = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    
    if repo_purpose == "security":
        base_schemes["apiKey"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
        base_schemes["oauth2"] = {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://example.com/oauth/authorize",
                    "tokenUrl": "https://example.com/oauth/token",
                    "scopes": {
                        "read": "Read access",
                        "write": "Write access",
                        "admin": "Admin access"
                    }
                }
            }
        }
    elif repo_purpose in ["crypto", "file_processing"]:
        base_schemes["apiKey"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key"
        }
    
    return base_schemes

def get_security_requirements(repo_purpose: str) -> List[Dict[str, List[str]]]:
    """Get security requirements based on repository purpose"""
    if repo_purpose == "security":
        return [{"bearerAuth": []}, {"apiKey": []}, {"oauth2": ["read", "write"]}]
    elif repo_purpose in ["crypto", "file_processing"]:
        return [{"bearerAuth": []}, {"apiKey": []}]
    else:
        return [{"bearerAuth": []}]

def generate_enhanced_schemas(api_endpoints: List[Dict], data_models: List[Dict], repo_purpose: str) -> Dict[str, Any]:
    """Generate enhanced schemas based on endpoints and data models"""
    schemas = {
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "description": "Error message"},
                "detail": {"type": "string", "description": "Detailed error information"},
                "code": {"type": "integer", "description": "Error code"},
                "timestamp": {"type": "string", "format": "date-time", "description": "Error timestamp"}
            },
            "required": ["error", "timestamp"]
        },
        "SuccessResponse": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "description": "Success message"},
                "data": {"description": "Response data"},
                "timestamp": {"type": "string", "format": "date-time", "description": "Response timestamp"}
            },
            "required": ["message", "timestamp"]
        }
    }
    
    # Add purpose-specific schemas
    if repo_purpose == "machine_learning":
        schemas.update({
            "PredictionRequest": {
                "type": "object",
                "properties": {
                    "input_features": {"type": "object", "description": "Input features for prediction"},
                    "model_version": {"type": "string", "description": "Model version to use"}
                },
                "required": ["input_features"]
            },
            "PredictionResponse": {
                "type": "object",
                "properties": {
                    "prediction": {"description": "Model prediction"},
                    "confidence": {"type": "number", "description": "Prediction confidence score"},
                    "model_version": {"type": "string", "description": "Model version used"}
                }
            }
        })
    elif repo_purpose == "file_processing":
        schemas.update({
            "FileUploadResponse": {
                "type": "object",
                "properties": {
                    "file_id": {"type": "string", "description": "Unique file identifier"},
                    "filename": {"type": "string", "description": "Original filename"},
                    "size": {"type": "integer", "description": "File size in bytes"},
                    "mime_type": {"type": "string", "description": "File MIME type"}
                }
            }
        })
    
    # Add schemas for data models
    for model in data_models:
        model_name = model["name"]
        schemas[model_name] = {
            "type": "object",
            "description": f"Data model for {model_name}",
            "properties": {
                "id": {"type": "string", "description": f"{model_name} identifier"},
                "created_at": {"type": "string", "format": "date-time", "description": "Creation timestamp"},
                "updated_at": {"type": "string", "format": "date-time", "description": "Last update timestamp"}
            }
        }
    
    return schemas

def generate_enhanced_operation(endpoint: Dict[str, Any], repo_purpose: str) -> Dict[str, Any]:
    """Generate enhanced OpenAPI operation with domain-specific features"""
    operation = {
        "summary": endpoint.get("description") or f"{endpoint['method']} {endpoint['function_name']}",
        "description": endpoint.get("description") or f"Automatically generated endpoint for {endpoint['function_name']}",
        "operationId": endpoint["function_name"].replace(".", "_"),
        "tags": [get_enhanced_tag_from_path(endpoint["path"], repo_purpose)],
        "responses": generate_enhanced_responses(endpoint, repo_purpose)
    }
    
    # Add parameters
    if endpoint["method"] == "GET" or endpoint.get("parameters"):
        operation["parameters"] = generate_enhanced_parameters(endpoint)
    
    # Add request body for non-GET requests
    if endpoint["method"] in ["POST", "PUT", "PATCH"]:
        operation["requestBody"] = generate_enhanced_request_body(endpoint, repo_purpose)
    
    # Add domain-specific operation features
    if repo_purpose == "machine_learning" and "predict" in endpoint["function_name"]:
        operation["x-ml-operation"] = True
        operation["x-response-time"] = "Usually < 1s for inference"
    elif repo_purpose == "file_processing" and "upload" in endpoint["function_name"]:
        operation["x-upload-operation"] = True
        operation["x-max-file-size"] = "100MB"
    
    return operation

def generate_enhanced_responses(endpoint: Dict[str, Any], repo_purpose: str) -> Dict[str, Any]:
    """Generate enhanced response schemas"""
    responses = {
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
    
    # Add domain-specific response codes
    if repo_purpose == "file_processing":
        responses["413"] = {
            "description": "File too large",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        }
    elif repo_purpose == "machine_learning":
        responses["422"] = {
            "description": "Invalid input features",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                }
            }
        }
    
    return responses

def generate_enhanced_parameters(endpoint: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate enhanced parameters with validation"""
    parameters = []
    
    # Add path parameters
    path_params = extract_path_parameters(endpoint["path"])
    for param in path_params:
        parameters.append({
            "name": param,
            "in": "path",
            "required": True,
            "schema": {"type": "string", "minLength": 1},
            "description": f"The {param} identifier"
        })
    
    # Add query parameters from function parameters
    for param in endpoint.get("parameters", []):
        if endpoint["method"] == "GET":
            param_schema = {"type": map_type_to_openapi(param["type"])}
            
            # Add validation rules
            if param["type"] == "integer":
                param_schema["minimum"] = 0
            elif param["type"] == "string":
                param_schema["minLength"] = 1
                param_schema["maxLength"] = 1000
            
            parameters.append({
                "name": param["name"],
                "in": "query",
                "required": param.get("required", False),
                "schema": param_schema,
                "description": f"The {param['name']} parameter"
            })
    
    return parameters

def generate_enhanced_request_body(endpoint: Dict[str, Any], repo_purpose: str) -> Dict[str, Any]:
    """Generate enhanced request body with validation"""
    if "file" in [p.get("type") for p in endpoint.get("parameters", [])]:
        # File upload endpoint
        return {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "file": {
                                "type": "string",
                                "format": "binary",
                                "description": "File to upload"
                            }
                        },
                        "required": ["file"]
                    }
                }
            }
        }
    else:
        # JSON request body
        properties = {}
        required = []
        
        for param in endpoint.get("parameters", []):
            properties[param["name"]] = {
                "type": map_type_to_openapi(param["type"]),
                "description": f"The {param['name']} value"
            }
            if param.get("required", False):
                required.append(param["name"])
        
        # Add default properties if none specified
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
        
        return {
            "required": True,
            "content": {
                "application/json": {
                    "schema": schema
                }
            }
        }

def get_enhanced_tag_from_path(path: str, repo_purpose: str) -> str:
    """Generate enhanced tag name from API path and purpose"""
    parts = path.strip("/").split("/")
    if parts and parts[0]:
        base_tag = parts[0].capitalize()
        
        # Add purpose-specific tag prefix
        purpose_prefixes = {
            "machine_learning": "ML",
            "data_analysis": "Analytics",
            "file_processing": "Files",
            "web_scraping": "Scraping",
            "security": "Security",
            "automation": "Tasks"
        }
        
        prefix = purpose_prefixes.get(repo_purpose, "")
        if prefix:
            return f"{prefix} - {base_tag}"
        return base_tag
    return repo_purpose.replace("_", " ").title()
