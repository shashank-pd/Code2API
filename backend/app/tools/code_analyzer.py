from langchain.tools import tool
from typing import Dict, Any, List, Optional, Tuple
import tree_sitter_languages
import tree_sitter as ts
import re
import ast
import inspect
import os
from pathlib import Path
from langchain_groq import ChatGroq
import json

@tool
def code_analyzer_tool(files_data: Dict[str, Any], repo_language: str) -> Dict[str, Any]:
    """
    Enhanced code analyzer that performs deep analysis to extract business logic,
    understand repository purpose, and identify meaningful API opportunities.
    
    Args:
        files_data: Dictionary of file paths and their contents
        repo_language: Primary programming language of the repository
    
    Returns:
        Dictionary containing detailed analysis with business logic mapping
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
        
        if not isinstance(actual_files, dict):
            return {
                "success": False,
                "error": f"Expected dict for files_data, got {type(actual_files)}",
                "debug_info": str(actual_files)[:500]
            }
        
        # Perform enhanced analysis
        analysis_result = perform_enhanced_analysis(actual_files, repo_language)
        
        return analysis_result
        
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Code analysis failed: {str(e)}"
        }

def perform_enhanced_analysis(files_data: Dict[str, Any], repo_language: str) -> Dict[str, Any]:
    """Perform comprehensive analysis of repository files"""
    try:
        # Initialize analysis results
        analysis = {
            "success": True,
            "repo_purpose": "",
            "main_functionality": [],
            "data_models": [],
            "api_endpoints": [],
            "business_logic": {},
            "entry_points": [],
            "dependencies": [],
            "functions_analyzed": 0,
            "classes_analyzed": 0,
            "security_recommendations": [],
            "language": repo_language,
            "file_structure": {},
            "complexity_score": 0
        }
        
        # Analyze repository structure first
        analysis["file_structure"] = analyze_file_structure(files_data)
        
        # Detect repository purpose using content analysis
        analysis["repo_purpose"] = detect_repository_purpose(files_data, repo_language)
        
        # Extract business logic and functionality
        for file_path, file_info in files_data.items():
            if not isinstance(file_info, dict) or "content" not in file_info:
                continue
                
            content = file_info["content"]
            language = file_info.get("language", repo_language)
            
            # Perform deep analysis based on language
            if language == "python":
                file_analysis = analyze_python_file_enhanced(content, file_path)
                merge_file_analysis(analysis, file_analysis)
                
            elif language in ["javascript", "typescript"]:
                file_analysis = analyze_javascript_file_enhanced(content, file_path)
                merge_file_analysis(analysis, file_analysis)
                
            elif language == "java":
                file_analysis = analyze_java_file_enhanced(content, file_path)
                merge_file_analysis(analysis, file_analysis)
        
        # Generate intelligent API endpoints based on business logic
        analysis["api_endpoints"] = generate_intelligent_endpoints(analysis)
        
        # Generate enhanced security recommendations
        analysis["security_recommendations"] = generate_enhanced_security_recommendations(analysis)
        
        # Calculate complexity score
        analysis["complexity_score"] = calculate_complexity_score(analysis)
        
        return analysis
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Enhanced analysis failed: {str(e)}"
        }

def analyze_file_structure(files_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze repository file structure to understand organization"""
    structure = {
        "total_files": len(files_data),
        "file_types": {},
        "directories": set(),
        "key_files": [],
        "config_files": [],
        "test_files": [],
        "main_files": []
    }
    
    for file_path in files_data.keys():
        # Extract directory structure
        path_parts = Path(file_path).parts
        if len(path_parts) > 1:
            structure["directories"].update(path_parts[:-1])
        
        # Categorize files
        file_name = Path(file_path).name.lower()
        file_ext = Path(file_path).suffix
        
        # Count file types
        structure["file_types"][file_ext] = structure["file_types"].get(file_ext, 0) + 1
        
        # Identify key files
        if file_name in ["main.py", "app.py", "index.js", "main.js", "main.java", "app.java"]:
            structure["main_files"].append(file_path)
        elif file_name in ["requirements.txt", "package.json", "pom.xml", "build.gradle", "dockerfile"]:
            structure["config_files"].append(file_path)
        elif "test" in file_name or file_name.endswith("_test.py") or file_name.endswith(".test.js"):
            structure["test_files"].append(file_path)
        elif any(keyword in file_name for keyword in ["readme", "license", "changelog"]):
            structure["key_files"].append(file_path)
    
    structure["directories"] = list(structure["directories"])
    return structure

def detect_repository_purpose(files_data: Dict[str, Any], repo_language: str) -> str:
    """Detect the main purpose of the repository using content analysis and LLM"""
    try:
        # First, try keyword-based analysis
        keyword_purpose = detect_purpose_by_keywords(files_data)
        
        # Then, enhance with LLM-powered analysis
        llm_purpose = analyze_purpose_with_llm(files_data, repo_language)
        
        # Combine both approaches
        if llm_purpose and llm_purpose != "unknown":
            return llm_purpose
        elif keyword_purpose and keyword_purpose != "general_utility":
            return keyword_purpose
        else:
            return "general_utility"
            
    except Exception as e:
        print(f"Error detecting repository purpose: {e}")
        return detect_purpose_by_keywords(files_data)

def detect_purpose_by_keywords(files_data: Dict[str, Any]) -> str:
    """Detect repository purpose using keyword analysis"""
    purpose_indicators = {
        "web_api": ["fastapi", "flask", "django", "express", "spring", "@app.route", "@RequestMapping"],
        "data_analysis": ["pandas", "numpy", "matplotlib", "seaborn", "sklearn", "tensorflow", "pytorch"],
        "machine_learning": ["model", "train", "predict", "classification", "regression", "neural", "deep learning"],
        "web_scraping": ["beautifulsoup", "scrapy", "selenium", "requests", "urllib"],
        "automation": ["schedule", "cron", "automate", "script", "task"],
        "database": ["sqlalchemy", "mongoose", "prisma", "database", "crud", "migration"],
        "utility": ["util", "helper", "tool", "library"],
        "game": ["pygame", "unity", "game", "player", "score"],
        "crypto": ["bitcoin", "ethereum", "blockchain", "crypto", "wallet"],
        "social_media": ["twitter", "facebook", "instagram", "social", "post", "comment"],
        "file_processing": ["file", "csv", "json", "xml", "parse", "convert"],
        "security": ["encrypt", "decrypt", "auth", "security", "password", "token"],
        "testing": ["test", "mock", "assert", "verify", "pytest", "junit"],
        "cli_tool": ["argparse", "click", "command", "cli", "terminal"]
    }
    
    # Analyze all file contents for purpose indicators
    content_text = ""
    for file_info in files_data.values():
        if isinstance(file_info, dict) and "content" in file_info:
            content_text += file_info["content"].lower() + " "
    
    # Count occurrences of purpose indicators
    purpose_scores = {}
    for purpose, indicators in purpose_indicators.items():
        score = sum(content_text.count(indicator) for indicator in indicators)
        if score > 0:
            purpose_scores[purpose] = score
    
    # Return the most likely purpose
    if purpose_scores:
        return max(purpose_scores, key=purpose_scores.get)
    return "general_utility"

def analyze_purpose_with_llm(files_data: Dict[str, Any], repo_language: str) -> str:
    """Use LLM to analyze repository purpose based on code content"""
    try:
        # Get Groq API key
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            return "unknown"
        
        # Initialize Groq LLM
        llm = ChatGroq(
            api_key=groq_api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=100,
            timeout=30
        )
        
        # Prepare context from repository files
        context = prepare_repository_context(files_data, repo_language)
        
        # Create prompt for purpose analysis
        prompt = f"""Analyze this {repo_language} repository and determine its main purpose.

Repository Context:
{context}

Based on the code structure, imports, functions, and overall content, what is the primary purpose of this repository?

Choose from these categories:
- web_api: REST API or web service
- data_analysis: Data processing and analysis
- machine_learning: ML models and training
- web_scraping: Data scraping and extraction
- automation: Scripts and automation tools
- database: Database operations and management
- file_processing: File manipulation and conversion
- security: Encryption, authentication, security tools
- cli_tool: Command line interface application
- game: Gaming application
- utility: General utility or library
- social_media: Social media related functionality
- crypto: Cryptocurrency or blockchain

Respond with only the category name, nothing else."""

        # Get LLM response
        response = llm.invoke(prompt)
        purpose = response.content.strip().lower()
        
        # Validate response
        valid_purposes = [
            "web_api", "data_analysis", "machine_learning", "web_scraping", 
            "automation", "database", "file_processing", "security", 
            "cli_tool", "game", "utility", "social_media", "crypto"
        ]
        
        if purpose in valid_purposes:
            return purpose
        else:
            return "unknown"
            
    except Exception as e:
        print(f"Error using LLM for purpose analysis: {e}")
        return "unknown"

def prepare_repository_context(files_data: Dict[str, Any], repo_language: str) -> str:
    """Prepare a concise context summary of the repository for LLM analysis"""
    context_parts = []
    
    # Add file structure overview
    file_names = [Path(path).name for path in files_data.keys()]
    context_parts.append(f"Files: {', '.join(file_names[:10])}")  # First 10 files
    
    # Add key imports and dependencies
    imports = set()
    main_functions = []
    class_names = []
    
    for file_path, file_info in files_data.items():
        if not isinstance(file_info, dict) or "content" not in file_info:
            continue
            
        content = file_info["content"]
        
        # Extract imports (first 500 chars to avoid too much content)
        if repo_language == "python":
            import_matches = re.findall(r'import\s+(\w+)|from\s+(\w+)', content[:500])
            for match in import_matches:
                imports.add(match[0] or match[1])
                
            # Extract function names
            func_matches = re.findall(r'def\s+(\w+)', content[:1000])
            main_functions.extend(func_matches[:5])  # First 5 functions
            
            # Extract class names
            class_matches = re.findall(r'class\s+(\w+)', content[:1000])
            class_names.extend(class_matches[:3])  # First 3 classes
            
        elif repo_language in ["javascript", "typescript"]:
            import_matches = re.findall(r'require\([\'"](\w+)[\'"]\)|import.*from\s*[\'"](\w+)[\'"]', content[:500])
            for match in import_matches:
                imports.add(match[0] or match[1])
                
        # Limit to avoid too much content
        if len(imports) > 10:
            break
    
    # Build context string
    if imports:
        context_parts.append(f"Key imports: {', '.join(list(imports)[:10])}")
    if main_functions:
        context_parts.append(f"Functions: {', '.join(main_functions[:5])}")
    if class_names:
        context_parts.append(f"Classes: {', '.join(class_names[:3])}")
    
    # Add content snippet from main files
    main_files = [f for f in files_data.keys() if any(main_name in Path(f).name.lower() 
                 for main_name in ["main", "app", "index", "server"])]
    
    if main_files:
        main_file = main_files[0]
        main_content = files_data[main_file].get("content", "")[:300]  # First 300 chars
        context_parts.append(f"Main file snippet: {main_content}")
    
    return " | ".join(context_parts)

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

def analyze_python_file_enhanced(content: str, file_path: str) -> Dict[str, Any]:
    """Enhanced Python file analysis with business logic extraction"""
    analysis = {
        "functions": [],
        "classes": [],
        "imports": [],
        "data_models": [],
        "business_logic": {},
        "entry_points": [],
        "dependencies": []
    }
    
    try:
        tree = ast.parse(content)
        
        # Extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    analysis["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    analysis["imports"].append(f"{module}.{alias.name}")
        
        # Extract functions with business logic
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_info = {
                    "name": node.name,
                    "docstring": get_docstring(node),
                    "parameters": extract_python_parameters(node),
                    "return_type": extract_python_return_type(node),
                    "complexity": calculate_function_complexity(node),
                    "business_logic": extract_business_logic_from_function(node, content),
                    "is_api_candidate": is_api_candidate_function(node, content),
                    "suggested_http_method": infer_http_method(node.name, content),
                    "file_path": file_path
                }
                analysis["functions"].append(func_info)
                
                # Identify entry points
                if node.name in ["main", "run", "start", "execute"] or "if __name__ == '__main__'" in content:
                    analysis["entry_points"].append(func_info)
            
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "docstring": get_docstring(node),
                    "methods": [],
                    "attributes": [],
                    "is_data_model": is_data_model_class(node),
                    "is_service_class": is_service_class(node),
                    "file_path": file_path
                }
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "docstring": get_docstring(item),
                            "parameters": extract_python_parameters(item),
                            "return_type": extract_python_return_type(item),
                            "is_api_candidate": is_api_candidate_function(item, content)
                        }
                        class_info["methods"].append(method_info)
                
                analysis["classes"].append(class_info)
                
                # Check if it's a data model
                if class_info["is_data_model"]:
                    analysis["data_models"].append(class_info)
    
    except Exception as e:
        print(f"Error analyzing Python file {file_path}: {e}")
    
    return analysis

def analyze_javascript_file_enhanced(content: str, file_path: str) -> Dict[str, Any]:
    """Enhanced JavaScript/TypeScript file analysis"""
    analysis = {
        "functions": [],
        "classes": [],
        "imports": [],
        "exports": [],
        "business_logic": {},
        "is_react_component": "react" in content.lower() or "jsx" in content.lower()
    }
    
    # Extract functions using regex patterns
    function_patterns = [
        r'function\s+(\w+)\s*\([^)]*\)\s*\{([^}]+)\}',
        r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>\s*\{([^}]+)\}',
        r'(\w+)\s*:\s*function\s*\([^)]*\)\s*\{([^}]+)\}',
        r'async\s+function\s+(\w+)\s*\([^)]*\)\s*\{([^}]+)\}'
    ]
    
    for pattern in function_patterns:
        matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            func_name = match.group(1)
            func_body = match.group(2) if len(match.groups()) > 1 else ""
            
            func_info = {
                "name": func_name,
                "body": func_body[:200],  # First 200 chars
                "is_api_candidate": any(keyword in func_name.lower() for keyword in ["get", "post", "put", "delete", "fetch", "save", "load"]),
                "suggested_http_method": infer_http_method(func_name, content),
                "file_path": file_path
            }
            analysis["functions"].append(func_info)
    
    # Extract imports/requires
    import_patterns = [
        r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]',
        r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
    ]
    
    for pattern in import_patterns:
        matches = re.findall(pattern, content)
        analysis["imports"].extend(matches)
    
    return analysis

def analyze_java_file_enhanced(content: str, file_path: str) -> Dict[str, Any]:
    """Enhanced Java file analysis"""
    analysis = {
        "classes": [],
        "methods": [],
        "imports": [],
        "annotations": [],
        "is_spring_controller": "@Controller" in content or "@RestController" in content
    }
    
    # Extract imports
    import_matches = re.findall(r'import\s+([^;]+);', content)
    analysis["imports"] = import_matches
    
    # Extract classes
    class_pattern = r'public\s+class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[\w,\s]+)?\s*\{'
    class_matches = re.findall(class_pattern, content)
    
    for class_name in class_matches:
        analysis["classes"].append({
            "name": class_name,
            "is_controller": "@Controller" in content or "@RestController" in content,
            "file_path": file_path
        })
    
    # Extract methods with annotations
    method_pattern = r'(@\w+(?:\([^)]*\))?\s*)*public\s+(\w+)\s+(\w+)\s*\([^)]*\)'
    method_matches = re.finditer(method_pattern, content, re.MULTILINE)
    
    for match in method_matches:
        annotations = match.group(1) or ""
        return_type = match.group(2)
        method_name = match.group(3)
        
        method_info = {
            "name": method_name,
            "return_type": return_type,
            "annotations": annotations,
            "is_api_endpoint": any(anno in annotations for anno in ["@GetMapping", "@PostMapping", "@PutMapping", "@DeleteMapping", "@RequestMapping"]),
            "suggested_http_method": infer_http_method(method_name, content),
            "file_path": file_path
        }
        analysis["methods"].append(method_info)
    
    return analysis

def merge_file_analysis(main_analysis: Dict[str, Any], file_analysis: Dict[str, Any]) -> None:
    """Merge file analysis results into main analysis"""
    if "functions" in file_analysis:
        main_analysis["functions_analyzed"] += len(file_analysis["functions"])
        for func in file_analysis["functions"]:
            if func.get("is_api_candidate", False):
                main_analysis["main_functionality"].append({
                    "type": "function",
                    "name": func["name"],
                    "description": func.get("docstring") or f"Function: {func['name']}",
                    "file_path": func["file_path"],
                    "business_logic": func.get("business_logic", {}),
                    "http_method": func.get("suggested_http_method", "GET")
                })
    
    if "classes" in file_analysis:
        main_analysis["classes_analyzed"] += len(file_analysis["classes"])
        for cls in file_analysis["classes"]:
            if cls.get("is_service_class", False) or cls.get("is_controller", False):
                main_analysis["main_functionality"].append({
                    "type": "class",
                    "name": cls["name"],
                    "description": cls.get("docstring") or f"Class: {cls['name']}",
                    "file_path": cls["file_path"],
                    "methods": cls.get("methods", [])
                })
            
            if cls.get("is_data_model", False):
                main_analysis["data_models"].append(cls)
    
    if "imports" in file_analysis:
        main_analysis["dependencies"].extend(file_analysis["imports"])

def generate_intelligent_endpoints(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate intelligent API endpoints based on business logic analysis"""
    endpoints = []
    repo_purpose = analysis.get("repo_purpose", "general_utility")
    
    # Generate endpoints based on repository purpose
    if repo_purpose == "web_api":
        endpoints.extend(generate_web_api_endpoints(analysis))
    elif repo_purpose == "data_analysis":
        endpoints.extend(generate_data_analysis_endpoints(analysis))
    elif repo_purpose == "machine_learning":
        endpoints.extend(generate_ml_endpoints(analysis))
    elif repo_purpose == "file_processing":
        endpoints.extend(generate_file_processing_endpoints(analysis))
    elif repo_purpose == "database":
        endpoints.extend(generate_database_endpoints(analysis))
    else:
        endpoints.extend(generate_generic_endpoints(analysis))
    
    return endpoints

def generate_web_api_endpoints(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate endpoints for web API repositories"""
    endpoints = []
    
    for func in analysis.get("main_functionality", []):
        if func["type"] == "function":
            endpoint = {
                "path": f"/{func['name'].replace('_', '-')}",
                "method": func.get("http_method", "GET"),
                "function_name": func["name"],
                "description": func["description"],
                "source_file": func["file_path"],
                "business_logic": func.get("business_logic", {}),
                "parameters": [],
                "return_type": "object"
            }
            endpoints.append(endpoint)
    
    return endpoints

def generate_data_analysis_endpoints(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate endpoints for data analysis repositories"""
    return [
        {
            "path": "/analyze-data",
            "method": "POST",
            "function_name": "analyze_data",
            "description": "Analyze uploaded data using the repository's analysis logic",
            "parameters": [{"name": "data", "type": "object", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/generate-report",
            "method": "POST",
            "function_name": "generate_report",
            "description": "Generate analysis report",
            "parameters": [{"name": "analysis_id", "type": "string", "required": True}],
            "return_type": "object"
        }
    ]

def generate_ml_endpoints(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate endpoints for machine learning repositories"""
    return [
        {
            "path": "/predict",
            "method": "POST",
            "function_name": "predict",
            "description": "Make predictions using the trained model",
            "parameters": [{"name": "input_data", "type": "object", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/train",
            "method": "POST",
            "function_name": "train_model",
            "description": "Train the machine learning model",
            "parameters": [{"name": "training_data", "type": "object", "required": True}],
            "return_type": "object"
        }
    ]

def generate_file_processing_endpoints(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate endpoints for file processing repositories"""
    return [
        {
            "path": "/process-file",
            "method": "POST",
            "function_name": "process_file",
            "description": "Process uploaded file using repository logic",
            "parameters": [{"name": "file", "type": "file", "required": True}],
            "return_type": "object"
        },
        {
            "path": "/convert",
            "method": "POST",
            "function_name": "convert_file",
            "description": "Convert file to different format",
            "parameters": [{"name": "file", "type": "file", "required": True}, {"name": "target_format", "type": "string", "required": True}],
            "return_type": "object"
        }
    ]

def generate_database_endpoints(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate CRUD endpoints for database repositories"""
    endpoints = []
    
    for model in analysis.get("data_models", []):
        model_name = model["name"].lower()
        endpoints.extend([
            {
                "path": f"/{model_name}s",
                "method": "GET",
                "function_name": f"get_{model_name}s",
                "description": f"Get all {model_name} records",
                "parameters": [],
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

def generate_generic_endpoints(analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate generic endpoints based on detected functionality"""
    endpoints = []
    
    for func in analysis.get("main_functionality", []):
        if func["type"] == "function" and func.get("is_api_candidate", False):
            endpoint = {
                "path": f"/{func['name'].replace('_', '-')}",
                "method": func.get("http_method", "POST"),
                "function_name": func["name"],
                "description": func["description"],
                "source_file": func["file_path"],
                "parameters": [],
                "return_type": "object"
            }
            endpoints.append(endpoint)
    
    # Add default utility endpoints if no specific ones found
    if not endpoints:
        endpoints = [
            {
                "path": "/execute",
                "method": "POST",
                "function_name": "execute_main_function",
                "description": "Execute the main functionality of the repository",
                "parameters": [{"name": "input", "type": "object", "required": False}],
                "return_type": "object"
            },
            {
                "path": "/status",
                "method": "GET",
                "function_name": "get_status",
                "description": "Get repository status and available operations",
                "parameters": [],
                "return_type": "object"
            }
        ]
    
    return endpoints

def generate_enhanced_security_recommendations(analysis: Dict[str, Any]) -> List[str]:
    """Generate enhanced security recommendations based on analysis"""
    recommendations = [
        "Implement authentication and authorization for all endpoints",
        "Add input validation and sanitization",
        "Use HTTPS for all API communications",
        "Implement rate limiting to prevent abuse",
        "Add logging and monitoring for security events"
    ]
    
    repo_purpose = analysis.get("repo_purpose", "")
    
    if repo_purpose == "database":
        recommendations.extend([
            "Use parameterized queries to prevent SQL injection",
            "Implement database connection pooling",
            "Add database access logging"
        ])
    elif repo_purpose == "file_processing":
        recommendations.extend([
            "Validate file types and sizes",
            "Scan uploaded files for malware",
            "Implement file storage quotas"
        ])
    elif repo_purpose == "machine_learning":
        recommendations.extend([
            "Validate input data schemas",
            "Implement model versioning",
            "Add prediction confidence thresholds"
        ])
    
    return recommendations

def calculate_complexity_score(analysis: Dict[str, Any]) -> int:
    """Calculate repository complexity score"""
    score = 0
    
    # Base score from file count
    score += min(analysis.get("file_structure", {}).get("total_files", 0) * 2, 20)
    
    # Add score for functions and classes
    score += min(analysis.get("functions_analyzed", 0), 30)
    score += min(analysis.get("classes_analyzed", 0) * 3, 30)
    
    # Add score for dependencies
    score += min(len(analysis.get("dependencies", [])), 20)
    
    return min(score, 100)  # Cap at 100

def extract_business_logic_from_function(node: ast.FunctionDef, content: str) -> Dict[str, Any]:
    """Extract business logic information from function AST node"""
    logic = {
        "has_loops": False,
        "has_conditionals": False,
        "has_external_calls": False,
        "complexity": 1
    }
    
    for child in ast.walk(node):
        if isinstance(child, (ast.For, ast.While)):
            logic["has_loops"] = True
            logic["complexity"] += 1
        elif isinstance(child, (ast.If, ast.Try)):
            logic["has_conditionals"] = True
            logic["complexity"] += 1
        elif isinstance(child, ast.Call):
            logic["has_external_calls"] = True
    
    return logic

def is_api_candidate_function(node: ast.FunctionDef, content: str) -> bool:
    """Determine if a function is a good API endpoint candidate"""
    name = node.name.lower()
    
    # Skip private functions
    if name.startswith('_'):
        return False
    
    # Check for API-like patterns
    api_patterns = ['get', 'post', 'put', 'delete', 'create', 'update', 'fetch', 'save', 'load', 'process', 'analyze', 'calculate', 'generate']
    
    return any(pattern in name for pattern in api_patterns)

def is_data_model_class(node: ast.ClassDef) -> bool:
    """Check if a class represents a data model"""
    class_name = node.name.lower()
    
    # Check for common data model patterns
    model_indicators = ['model', 'entity', 'data', 'record', 'user', 'product', 'order', 'item']
    
    # Check for inheritance from common base classes
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id.lower() in ['basemodel', 'model', 'entity']:
            return True
    
    return any(indicator in class_name for indicator in model_indicators)

def is_service_class(node: ast.ClassDef) -> bool:
    """Check if a class represents a service or business logic class"""
    class_name = node.name.lower()
    service_indicators = ['service', 'manager', 'handler', 'processor', 'controller', 'api']
    
    return any(indicator in class_name for indicator in service_indicators)

def calculate_function_complexity(node: ast.FunctionDef) -> int:
    """Calculate cyclomatic complexity of a function"""
    complexity = 1  # Base complexity
    
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
    
    return complexity
