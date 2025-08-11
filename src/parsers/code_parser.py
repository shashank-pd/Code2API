"""
Multi-language code parser using tree-sitter
"""
import tree_sitter
from tree_sitter import Language, Parser
import ast
import re
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Function:
    """Represents a parsed function"""
    name: str
    parameters: List[Dict[str, Any]]
    return_type: Optional[str]
    docstring: Optional[str]
    line_number: int
    is_async: bool = False
    decorators: List[str] = None
    visibility: str = "public"  # public, private, protected

@dataclass
class Class:
    """Represents a parsed class"""
    name: str
    methods: List[Function]
    attributes: List[str]
    docstring: Optional[str]
    line_number: int
    inheritance: List[str] = None

@dataclass
class ParsedCode:
    """Container for parsed code elements"""
    functions: List[Function]
    classes: List[Class]
    imports: List[str]
    language: str
    file_path: str

class CodeParser:
    """Multi-language code parser"""
    
    def __init__(self):
        self.parsers = {}
        self._setup_parsers()
    
    def _setup_parsers(self):
        """Setup tree-sitter parsers for supported languages"""
        try:
            # Note: In production, you'd compile these properly
            # For now, we'll use fallback parsing
            pass
        except Exception as e:
            print(f"Warning: Could not setup tree-sitter parsers: {e}")
    
    def parse_file(self, file_path: str) -> ParsedCode:
        """Parse a source code file"""
        path = Path(file_path)
        language = self._detect_language(path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if language == "python":
            return self._parse_python(content, file_path)
        elif language == "javascript":
            return self._parse_javascript(content, file_path)
        elif language == "java":
            return self._parse_java(content, file_path)
        else:
            raise ValueError(f"Unsupported language: {language}")
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        extension = file_path.suffix.lower()
        
        if extension == ".py":
            return "python"
        elif extension in [".js", ".jsx", ".ts", ".tsx"]:
            return "javascript"
        elif extension == ".java":
            return "java"
        else:
            raise ValueError(f"Unsupported file extension: {extension}")
    
    def _parse_python(self, content: str, file_path: str) -> ParsedCode:
        """Parse Python code using AST"""
        try:
            tree = ast.parse(content)
            functions = []
            classes = []
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func = self._extract_python_function(node)
                    functions.append(func)
                elif isinstance(node, ast.AsyncFunctionDef):
                    func = self._extract_python_function(node, is_async=True)
                    functions.append(func)
                elif isinstance(node, ast.ClassDef):
                    cls = self._extract_python_class(node)
                    classes.append(cls)
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.extend(self._extract_python_imports(node))
            
            return ParsedCode(
                functions=functions,
                classes=classes,
                imports=imports,
                language="python",
                file_path=file_path
            )
        except Exception as e:
            raise ValueError(f"Failed to parse Python code: {e}")
    
    def _extract_python_function(self, node: ast.FunctionDef, is_async: bool = False) -> Function:
        """Extract function information from Python AST node"""
        # Parameters
        params = []
        for arg in node.args.args:
            param = {
                "name": arg.arg,
                "type": self._get_annotation(arg.annotation) if arg.annotation else None,
                "default": None
            }
            params.append(param)
        
        # Handle defaults
        defaults = node.args.defaults
        if defaults:
            for i, default in enumerate(defaults):
                param_index = len(params) - len(defaults) + i
                if param_index >= 0:
                    params[param_index]["default"] = ast.unparse(default)
        
        # Return type
        return_type = self._get_annotation(node.returns) if node.returns else None
        
        # Docstring
        docstring = ast.get_docstring(node)
        
        # Decorators
        decorators = [ast.unparse(d) for d in node.decorator_list]
        
        return Function(
            name=node.name,
            parameters=params,
            return_type=return_type,
            docstring=docstring,
            line_number=node.lineno,
            is_async=is_async,
            decorators=decorators,
            visibility="private" if node.name.startswith("_") else "public"
        )
    
    def _extract_python_class(self, node: ast.ClassDef) -> Class:
        """Extract class information from Python AST node"""
        methods = []
        attributes = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method = self._extract_python_function(item)
                methods.append(method)
            elif isinstance(item, ast.AsyncFunctionDef):
                method = self._extract_python_function(item, is_async=True)
                methods.append(method)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        
        # Inheritance
        inheritance = [ast.unparse(base) for base in node.bases]
        
        return Class(
            name=node.name,
            methods=methods,
            attributes=attributes,
            docstring=ast.get_docstring(node),
            line_number=node.lineno,
            inheritance=inheritance
        )
    
    def _extract_python_imports(self, node) -> List[str]:
        """Extract import statements"""
        imports = []
        if isinstance(node, ast.Import):
            for name in node.names:
                imports.append(name.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for name in node.names:
                imports.append(f"{module}.{name.name}" if module else name.name)
        return imports
    
    def _get_annotation(self, annotation) -> str:
        """Get type annotation as string"""
        if annotation:
            return ast.unparse(annotation)
        return None
    
    def _parse_javascript(self, content: str, file_path: str) -> ParsedCode:
        """Parse JavaScript code (simplified implementation)"""
        # This is a simplified regex-based parser for demonstration
        # In production, use proper tree-sitter or babel parser
        
        functions = []
        classes = []
        imports = []
        
        # Extract functions
        func_pattern = r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            params_str = match.group(2)
            
            params = []
            if params_str.strip():
                for param in params_str.split(','):
                    param = param.strip()
                    params.append({
                        "name": param,
                        "type": None,
                        "default": None
                    })
            
            functions.append(Function(
                name=name,
                parameters=params,
                return_type=None,
                docstring=None,
                line_number=content[:match.start()].count('\n') + 1,
                is_async='async' in match.group(0)
            ))
        
        # Extract arrow functions
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'
        for match in re.finditer(arrow_pattern, content):
            name = match.group(1)
            functions.append(Function(
                name=name,
                parameters=[],
                return_type=None,
                docstring=None,
                line_number=content[:match.start()].count('\n') + 1,
                is_async='async' in match.group(0)
            ))
        
        # Extract imports
        import_pattern = r'import\s+.*?from\s+["\']([^"\']+)["\']'
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1))
        
        return ParsedCode(
            functions=functions,
            classes=classes,
            imports=imports,
            language="javascript",
            file_path=file_path
        )
    
    def _parse_java(self, content: str, file_path: str) -> ParsedCode:
        """Parse Java code (simplified implementation)"""
        # Simplified regex-based parser for demonstration
        
        functions = []
        classes = []
        imports = []
        
        # Extract methods
        method_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*(?:\w+)\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(method_pattern, content):
            name = match.group(1)
            params_str = match.group(2)
            
            params = []
            if params_str.strip():
                for param in params_str.split(','):
                    param = param.strip()
                    if ' ' in param:
                        type_name, var_name = param.rsplit(' ', 1)
                        params.append({
                            "name": var_name,
                            "type": type_name,
                            "default": None
                        })
            
            functions.append(Function(
                name=name,
                parameters=params,
                return_type=None,
                docstring=None,
                line_number=content[:match.start()].count('\n') + 1
            ))
        
        # Extract imports
        import_pattern = r'import\s+([^;]+);'
        for match in re.finditer(import_pattern, content):
            imports.append(match.group(1).strip())
        
        return ParsedCode(
            functions=functions,
            classes=classes,
            imports=imports,
            language="java",
            file_path=file_path
        )
