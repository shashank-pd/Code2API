from langchain.tools import tool
from typing import Dict, Any, List
import tree_sitter_languages
import tree_sitter as ts
import re
import ast
import inspect

@tool
def code_analyzer_tool(files_data: Dict[str, Any], repo_language: str) -> Dict[str, Any]:
    """
    Analyze code files to identify potential API endpoints using AST parsing.
    
    Args:
        files_data: Dictionary of file paths and their contents
        repo_language: Primary programming language of the repository
    
    Returns:
        Dictionary containing detected API endpoints and analysis results
    """
    try:
        # Handle nested parameter structure from LangChain agent
        if isinstance(files_data, dict) and 'function_name' in files_data:
            print(f"[DEBUG] Received nested files_data structure: {type(files_data)}")
            return {
                "success": False,
                "error": "Received nested parameter structure instead of files data",
                "debug_info": str(files_data)[:500]
            }
        
        # Handle case where files_data might be coming from code_fetcher result
        if isinstance(files_data, dict) and 'files_data' in files_data:
            actual_files = files_data['files_data']
        else:
            actual_files = files_data
            
        print(f"[DEBUG] Analyzing files: {list(actual_files.keys()) if isinstance(actual_files, dict) else 'Invalid structure'}")
        
        api_endpoints = []
        functions_analyzed = 0
        classes_analyzed = 0
        
        if not isinstance(actual_files, dict):
            return {
                "success": False,
                "error": f"Expected dict for files_data, got {type(actual_files)}",
                "debug_info": str(actual_files)[:500]
            }
        
        for file_path, file_info in actual_files.items():
            if not isinstance(file_info, dict) or "content" not in file_info:
                continue
                
            content = file_info["content"]
            language = file_info.get("language", repo_language)
            
            # Analyze based on language
            if language == "python":
                file_endpoints = analyze_python_file(content, file_path)
                api_endpoints.extend(file_endpoints)
                
                # Count functions and classes
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions_analyzed += 1
                        elif isinstance(node, ast.ClassDef):
                            classes_analyzed += 1
                except:
                    pass
                    
            elif language in ["javascript", "typescript"]:
                file_endpoints = analyze_javascript_file(content, file_path)
                api_endpoints.extend(file_endpoints)
                functions_analyzed += content.count("function ")
                classes_analyzed += content.count("class ")
                
            elif language == "java":
                file_endpoints = analyze_java_file(content, file_path)
                api_endpoints.extend(file_endpoints)
                functions_analyzed += len(re.findall(r'\b(public|private|protected)\s+\w+\s+\w+\s*\(', content))
                classes_analyzed += content.count("class ")
        
        # Generate security recommendations
        security_recommendations = generate_security_recommendations(api_endpoints, repo_language)
        
        return {
            "success": True,
            "api_endpoints": api_endpoints,
            "functions_analyzed": functions_analyzed,
            "classes_analyzed": classes_analyzed,
            "security_recommendations": security_recommendations,
            "language": repo_language
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Code analysis failed: {str(e)}"
        }

def analyze_python_file(content: str, file_path: str) -> List[Dict[str, Any]]:
    """Analyze Python file for potential API endpoints"""
    endpoints = []
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Skip private functions and __init__
                if node.name.startswith('_'):
                    continue
                
                # Extract function information
                endpoint = {
                    "path": f"/{node.name.replace('_', '-')}",
                    "method": infer_http_method(node.name, content),
                    "function_name": node.name,
                    "description": get_docstring(node) or f"Execute {node.name} operation",
                    "parameters": extract_python_parameters(node),
                    "return_type": extract_python_return_type(node),
                    "source_file": file_path
                }
                endpoints.append(endpoint)
                
            elif isinstance(node, ast.ClassDef):
                # Analyze class methods for CRUD-like operations
                class_name = node.name.lower()
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                        # Map common method names to HTTP methods
                        method_name = item.name
                        
                        # Create RESTful endpoints for common patterns
                        if method_name in ['get', 'find', 'list', 'view', 'show']:
                            path = f"/{class_name}s"
                            method = "GET"
                        elif method_name in ['add', 'create', 'new']:
                            path = f"/{class_name}s"
                            method = "POST"
                        elif method_name in ['update', 'edit', 'modify']:
                            path = f"/{class_name}s/{{id}}"
                            method = "PUT"
                        elif method_name in ['delete', 'remove', 'destroy']:
                            path = f"/{class_name}s/{{id}}"
                            method = "DELETE"
                        elif method_name in ['save', 'load']:
                            path = f"/{class_name}s/{method_name}"
                            method = "POST"
                        else:
                            path = f"/{class_name}s/{method_name.replace('_', '-')}"
                            method = infer_http_method(method_name, content)
                        
                        endpoint = {
                            "path": path,
                            "method": method,
                            "function_name": f"{node.name}.{item.name}",
                            "description": get_docstring(item) or f"{method} {class_name} - {method_name}",
                            "parameters": extract_python_parameters(item),
                            "return_type": extract_python_return_type(item),
                            "source_file": file_path,
                            "class_name": node.name
                        }
                        endpoints.append(endpoint)
    
    except Exception as e:
        print(f"Error analyzing Python file {file_path}: {e}")
    
    return endpoints

def analyze_javascript_file(content: str, file_path: str) -> List[Dict[str, Any]]:
    """Analyze JavaScript/TypeScript file for potential API endpoints"""
    endpoints = []
    
    # Simple regex-based analysis for JavaScript functions
    function_patterns = [
        r'function\s+(\w+)\s*\([^)]*\)',
        r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
        r'(\w+)\s*:\s*function\s*\([^)]*\)',
        r'async\s+function\s+(\w+)\s*\([^)]*\)'
    ]
    
    for pattern in function_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE)
        for match in matches:
            func_name = match.group(1)
            if not func_name.startswith('_'):
                endpoint = {
                    "path": f"/{func_name.replace('_', '-')}",
                    "method": infer_http_method(func_name, content),
                    "function_name": func_name,
                    "description": extract_js_comment(content, match.start()),
                    "parameters": [],  # Would need more sophisticated parsing
                    "return_type": "any",
                    "source_file": file_path
                }
                endpoints.append(endpoint)
    
    return endpoints

def analyze_java_file(content: str, file_path: str) -> List[Dict[str, Any]]:
    """Analyze Java file for potential API endpoints"""
    endpoints = []
    
    # Look for public methods
    method_pattern = r'public\s+(\w+)\s+(\w+)\s*\([^)]*\)'
    matches = re.finditer(method_pattern, content, re.MULTILINE)
    
    for match in matches:
        return_type = match.group(1)
        method_name = match.group(2)
        
        if not method_name.startswith('_'):
            endpoint = {
                "path": f"/{method_name.replace('_', '-')}",
                "method": infer_http_method(method_name, content),
                "function_name": method_name,
                "description": extract_java_comment(content, match.start()),
                "parameters": [],  # Would need more sophisticated parsing
                "return_type": return_type,
                "source_file": file_path
            }
            endpoints.append(endpoint)
    
    return endpoints

def infer_http_method(function_name: str, content: str) -> str:
    """Infer HTTP method from function name and context"""
    name_lower = function_name.lower()
    
    # Check for explicit method indicators
    if any(keyword in name_lower for keyword in ['get', 'fetch', 'retrieve', 'find', 'list']):
        return "GET"
    elif any(keyword in name_lower for keyword in ['create', 'add', 'post', 'insert']):
        return "POST"
    elif any(keyword in name_lower for keyword in ['update', 'modify', 'edit', 'put']):
        return "PUT"
    elif any(keyword in name_lower for keyword in ['delete', 'remove', 'destroy']):
        return "DELETE"
    elif any(keyword in name_lower for keyword in ['patch']):
        return "PATCH"
    else:
        # Default to POST for actions, GET for others
        if any(keyword in name_lower for keyword in ['calculate', 'process', 'execute', 'run']):
            return "POST"
        return "GET"

def get_docstring(node) -> str:
    """Extract docstring from AST node"""
    if (node.body and 
        isinstance(node.body[0], ast.Expr) and 
        isinstance(node.body[0].value, ast.Constant) and 
        isinstance(node.body[0].value.value, str)):
        return node.body[0].value.value.strip()
    return ""

def extract_python_parameters(node) -> List[Dict[str, Any]]:
    """Extract parameters from Python function AST node"""
    parameters = []
    
    for arg in node.args.args:
        param_type = "any"
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                param_type = arg.annotation.id
            elif isinstance(arg.annotation, ast.Constant):
                param_type = str(arg.annotation.value)
        
        parameters.append({
            "name": arg.arg,
            "type": param_type,
            "required": True  # Simplified assumption
        })
    
    return parameters

def extract_python_return_type(node) -> str:
    """Extract return type from Python function AST node"""
    if node.returns:
        if isinstance(node.returns, ast.Name):
            return node.returns.id
        elif isinstance(node.returns, ast.Constant):
            return str(node.returns.value)
    return "any"

def extract_js_comment(content: str, position: int) -> str:
    """Extract comment above JavaScript function"""
    lines = content[:position].split('\n')
    for i in range(len(lines) - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith('/*') or line.startswith('//'):
            return line.replace('//', '').replace('/*', '').replace('*/', '').strip()
        elif line and not line.startswith(' '):
            break
    return ""

def extract_java_comment(content: str, position: int) -> str:
    """Extract comment above Java method"""
    return extract_js_comment(content, position)  # Similar logic

def generate_security_recommendations(endpoints: List[Dict[str, Any]], language: str) -> List[str]:
    """Generate security recommendations based on detected endpoints"""
    recommendations = [
        "Implement authentication and authorization for all endpoints",
        "Add input validation and sanitization",
        "Use HTTPS for all API communications",
        "Implement rate limiting to prevent abuse",
        "Add logging and monitoring for security events"
    ]
    
    # Add language-specific recommendations
    if language == "python":
        recommendations.extend([
            "Use SQLAlchemy or similar ORM to prevent SQL injection",
            "Validate all input data using Pydantic models",
            "Use secrets module for generating secure tokens"
        ])
    elif language in ["javascript", "typescript"]:
        recommendations.extend([
            "Use helmet.js for security headers",
            "Sanitize inputs to prevent XSS attacks",
            "Use bcrypt for password hashing"
        ])
    elif language == "java":
        recommendations.extend([
            "Use Spring Security for authentication",
            "Validate inputs using Bean Validation annotations",
            "Use prepared statements for database queries"
        ])
    
    return recommendations
