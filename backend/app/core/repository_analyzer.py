"""
Repository Analysis Engine
Handles GitHub repository cloning, analysis, and code extraction
"""

import os
import git
import tempfile
import shutil
import ast
import fnmatch
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from github import Github, GithubException
import logging
from dataclasses import dataclass

from .config import settings

logger = logging.getLogger(__name__)

@dataclass
class FunctionInfo:
    """Information about a parsed function"""
    name: str
    args: List[str]
    docstring: Optional[str]
    return_annotation: Optional[str]
    line_number: int
    file_path: str
    class_name: Optional[str] = None
    decorators: List[str] = None
    is_async: bool = False
    complexity: int = 1

@dataclass
class RepositoryInfo:
    """Repository metadata"""
    name: str
    url: str
    description: Optional[str]
    language: Optional[str]
    stars: int
    forks: int
    size: int
    default_branch: str

class RepositoryAnalyzer:
    """Analyzes GitHub repositories and extracts code structure"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.github = Github(github_token) if github_token else Github()
        
        # File patterns to include
        self.include_patterns = {
            'python': ['*.py'],
            'javascript': ['*.js', '*.jsx', '*.ts', '*.tsx'],
            'java': ['*.java'],
            'cpp': ['*.cpp', '*.cc', '*.cxx', '*.c'],
            'go': ['*.go'],
            'rust': ['*.rs'],
            'php': ['*.php'],
            'ruby': ['*.rb']
        }
        
        # File patterns to exclude
        self.exclude_patterns = [
            '*/node_modules/*',
            '*/.git/*',
            '*/venv/*',
            '*/env/*',
            '*/__pycache__/*',
            '*/build/*',
            '*/dist/*',
            '*/target/*',
            '*/vendor/*',
            '*.min.js',
            '*.bundle.js'
        ]

    async def analyze_repository(
        self, 
        repo_url: str, 
        branch: str = "main",
        include_private: bool = False
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository and extract code structure
        
        Args:
            repo_url: GitHub repository URL or 'owner/repo' format
            branch: Branch to analyze (default: main)
            include_private: Whether to include private repositories
        
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Parse repository URL
            repo_path = self._parse_repo_url(repo_url)
            
            # Get repository information
            repo_info = await self._get_repo_info(repo_path)
            
            # Clone repository
            local_path = await self._clone_repository(repo_path, branch)
            
            try:
                # Analyze repository structure
                structure = self._analyze_structure(local_path)
                
                # Extract functions from source files
                functions = await self._extract_functions(local_path, structure)
                
                # Calculate statistics
                statistics = self._calculate_statistics(structure, functions)
                
                return {
                    "repository_info": repo_info,
                    "structure": structure,
                    "functions": functions,
                    "statistics": statistics,
                    "files_analyzed": len([f for f in structure if f["type"] == "file"]),
                    "success": True
                }
                
            finally:
                # Cleanup cloned repository
                if os.path.exists(local_path):
                    shutil.rmtree(local_path, ignore_errors=True)
                
        except Exception as e:
            logger.error(f"Repository analysis failed for {repo_url}: {str(e)}")
            raise Exception(f"Repository analysis failed: {str(e)}")

    def _parse_repo_url(self, repo_url: str) -> str:
        """Parse repository URL to extract owner/repo format"""
        if repo_url.startswith("http"):
            # Extract from full URL
            parts = repo_url.rstrip("/").split("/")
            if len(parts) >= 2:
                return f"{parts[-2]}/{parts[-1]}"
        else:
            # Assume it's already in owner/repo format
            return repo_url
        
        raise ValueError(f"Invalid repository URL format: {repo_url}")

    async def _get_repo_info(self, repo_path: str) -> RepositoryInfo:
        """Get repository metadata from GitHub API"""
        try:
            repo = self.github.get_repo(repo_path)
            
            return RepositoryInfo(
                name=repo.name,
                url=repo.html_url,
                description=repo.description,
                language=repo.language,
                stars=repo.stargazers_count,
                forks=repo.forks_count,
                size=repo.size,
                default_branch=repo.default_branch
            )
            
        except GithubException as e:
            logger.error(f"Failed to get repository info: {str(e)}")
            # Return basic info if API fails
            owner, name = repo_path.split("/")
            return RepositoryInfo(
                name=name,
                url=f"https://github.com/{repo_path}",
                description=None,
                language=None,
                stars=0,
                forks=0,
                size=0,
                default_branch="main"
            )

    async def _clone_repository(self, repo_path: str, branch: str) -> str:
        """Clone repository to temporary directory"""
        temp_dir = tempfile.mkdtemp()
        repo_url = f"https://github.com/{repo_path}.git"
        
        try:
            logger.info(f"Cloning repository: {repo_url}")
            git.Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1)
            return temp_dir
            
        except git.exc.GitCommandError as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repository: {str(e)}")

    def _analyze_structure(self, repo_path: str) -> List[Dict[str, Any]]:
        """Analyze repository file structure"""
        structure = []
        
        for root, dirs, files in os.walk(repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(
                fnmatch.fnmatch(os.path.join(root, d), pattern) 
                for pattern in self.exclude_patterns
            )]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, repo_path)
                
                # Skip excluded files
                if any(fnmatch.fnmatch(file_path, pattern) for pattern in self.exclude_patterns):
                    continue
                
                # Detect language
                language = self._detect_language(file)
                
                if language:
                    try:
                        file_size = os.path.getsize(file_path)
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = len(f.readlines())
                        
                        structure.append({
                            "type": "file",
                            "path": relative_path,
                            "name": file,
                            "language": language,
                            "size": file_size,
                            "lines": lines
                        })
                    except Exception as e:
                        logger.warning(f"Failed to analyze file {file_path}: {str(e)}")
        
        return structure

    def _detect_language(self, filename: str) -> Optional[str]:
        """Detect programming language from filename"""
        ext = Path(filename).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.cc': 'cpp',
            '.cxx': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby'
        }
        
        return language_map.get(ext)

    async def _extract_functions(
        self, 
        repo_path: str, 
        structure: List[Dict[str, Any]]
    ) -> List[FunctionInfo]:
        """Extract function definitions from source files"""
        functions = []
        
        for file_info in structure:
            if file_info["type"] != "file":
                continue
                
            file_path = os.path.join(repo_path, file_info["path"])
            language = file_info["language"]
            
            try:
                if language == "python":
                    file_functions = self._extract_python_functions(file_path, file_info["path"])
                    functions.extend(file_functions)
                elif language in ["javascript", "typescript"]:
                    file_functions = self._extract_js_functions(file_path, file_info["path"])
                    functions.extend(file_functions)
                # Add more language parsers as needed
                
            except Exception as e:
                logger.warning(f"Failed to extract functions from {file_path}: {str(e)}")
        
        return functions

    def _extract_python_functions(self, file_path: str, relative_path: str) -> List[FunctionInfo]:
        """Extract function definitions from Python files"""
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Extract function information
                    function_info = FunctionInfo(
                        name=node.name,
                        args=[arg.arg for arg in node.args.args],
                        docstring=ast.get_docstring(node),
                        return_annotation=self._get_annotation_string(node.returns),
                        line_number=node.lineno,
                        file_path=relative_path,
                        decorators=[self._get_decorator_name(d) for d in node.decorator_list],
                        is_async=isinstance(node, ast.AsyncFunctionDef),
                        complexity=self._calculate_complexity(node)
                    )
                    
                    # Check if function is inside a class
                    for parent in ast.walk(tree):
                        if isinstance(parent, ast.ClassDef):
                            for child in ast.walk(parent):
                                if child == node:
                                    function_info.class_name = parent.name
                                    break
                    
                    functions.append(function_info)
            
        except Exception as e:
            logger.warning(f"Failed to parse Python file {file_path}: {str(e)}")
        
        return functions

    def _extract_js_functions(self, file_path: str, relative_path: str) -> List[FunctionInfo]:
        """Extract function definitions from JavaScript/TypeScript files"""
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic regex-based extraction for JS functions
            # In a production system, you'd use a proper JS parser like tree-sitter
            import re
            
            # Function declarations
            func_pattern = r'function\s+(\w+)\s*\(([^)]*)\)\s*{'
            matches = re.finditer(func_pattern, content)
            
            for match in matches:
                name = match.group(1)
                params = [p.strip() for p in match.group(2).split(',') if p.strip()]
                line_number = content[:match.start()].count('\n') + 1
                
                functions.append(FunctionInfo(
                    name=name,
                    args=params,
                    docstring=None,
                    return_annotation=None,
                    line_number=line_number,
                    file_path=relative_path,
                    complexity=1
                ))
            
            # Arrow functions
            arrow_pattern = r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>'
            matches = re.finditer(arrow_pattern, content)
            
            for match in matches:
                name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                functions.append(FunctionInfo(
                    name=name,
                    args=[],
                    docstring=None,
                    return_annotation=None,
                    line_number=line_number,
                    file_path=relative_path,
                    complexity=1
                ))
            
        except Exception as e:
            logger.warning(f"Failed to parse JavaScript file {file_path}: {str(e)}")
        
        return functions

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

    def _calculate_statistics(
        self, 
        structure: List[Dict[str, Any]], 
        functions: List[FunctionInfo]
    ) -> Dict[str, Any]:
        """Calculate repository statistics"""
        
        # File statistics
        files_by_language = {}
        total_lines = 0
        total_files = 0
        
        for item in structure:
            if item["type"] == "file":
                total_files += 1
                total_lines += item["lines"]
                
                lang = item["language"]
                if lang not in files_by_language:
                    files_by_language[lang] = 0
                files_by_language[lang] += 1
        
        # Function statistics
        functions_by_language = {}
        total_functions = len(functions)
        avg_complexity = 0
        
        if functions:
            for func in functions:
                lang = self._detect_language(func.file_path) or "unknown"
                if lang not in functions_by_language:
                    functions_by_language[lang] = 0
                functions_by_language[lang] += 1
            
            avg_complexity = sum(func.complexity for func in functions) / len(functions)
        
        return {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_functions": total_functions,
            "languages": files_by_language,
            "functions_by_language": functions_by_language,
            "average_complexity": round(avg_complexity, 2),
            "files_with_functions": len(set(func.file_path for func in functions))
        }
