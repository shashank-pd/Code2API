"""
GitHub repository integration for Code2API
Fetches and analyzes code directly from GitHub repositories
"""
import requests
import base64
import os
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import zipfile
from urllib.parse import urlparse
import git

class GitHubRepoFetcher:
    """Fetches code from GitHub repositories"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_token = github_token
        self.headers = {}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
        
        self.api_base = "https://api.github.com"
    
    def parse_github_url(self, url: str) -> Dict[str, str]:
        """Parse GitHub URL to extract owner and repo"""
        # Handle different GitHub URL formats
        if url.startswith('https://github.com/'):
            # https://github.com/owner/repo
            path = url.replace('https://github.com/', '').split('/')
            if len(path) >= 2:
                return {"owner": path[0], "repo": path[1].replace('.git', '')}
        elif '/' in url and not url.startswith('http'):
            # owner/repo format
            parts = url.split('/')
            if len(parts) == 2:
                return {"owner": parts[0], "repo": parts[1]}
        
        raise ValueError(f"Invalid GitHub URL format: {url}")
    
    def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information"""
        url = f"{self.api_base}/repos/{owner}/{repo}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 404:
            raise ValueError(f"Repository {owner}/{repo} not found")
        elif response.status_code != 200:
            raise ValueError(f"Error fetching repo info: {response.status_code}")
        
        return response.json()
    
    def get_repo_tree(self, owner: str, repo: str, branch: str = "main") -> List[Dict[str, Any]]:
        """Get repository file tree"""
        url = f"{self.api_base}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code == 404:
            # Try 'master' branch if 'main' doesn't exist
            if branch == "main":
                return self.get_repo_tree(owner, repo, "master")
            raise ValueError(f"Branch {branch} not found in {owner}/{repo}")
        elif response.status_code != 200:
            raise ValueError(f"Error fetching repo tree: {response.status_code}")
        
        return response.json().get('tree', [])
    
    def get_file_content(self, owner: str, repo: str, file_path: str, branch: str = "main") -> str:
        """Get content of a specific file"""
        url = f"{self.api_base}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise ValueError(f"Error fetching file {file_path}: {response.status_code}")
        
        file_data = response.json()
        if file_data.get('encoding') == 'base64':
            content = base64.b64decode(file_data['content']).decode('utf-8')
            return content
        else:
            return file_data.get('content', '')
    
    def clone_repo(self, owner: str, repo: str, target_dir: str, branch: str = "main") -> str:
        """Clone entire repository using git"""
        repo_url = f"https://github.com/{owner}/{repo}.git"
        
        try:
            # Clone the repository
            git.Repo.clone_from(repo_url, target_dir, branch=branch)
            return target_dir
        except git.exc.GitCommandError as e:
            if branch == "main":
                # Try master branch
                try:
                    git.Repo.clone_from(repo_url, target_dir, branch="master")
                    return target_dir
                except git.exc.GitCommandError:
                    pass
            raise ValueError(f"Error cloning repository: {str(e)}")
    
    def download_repo_zip(self, owner: str, repo: str, branch: str = "main") -> str:
        """Download repository as ZIP file"""
        url = f"https://github.com/{owner}/{repo}/archive/{branch}.zip"
        response = requests.get(url)
        
        if response.status_code != 200:
            if branch == "main":
                # Try master branch
                url = f"https://github.com/{owner}/{repo}/archive/master.zip"
                response = requests.get(url)
        
        if response.status_code != 200:
            raise ValueError(f"Error downloading repository: {response.status_code}")
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name
    
    def extract_supported_files(self, repo_path: str, supported_extensions: List[str]) -> List[str]:
        """Extract all supported source code files from repository"""
        supported_files = []
        repo_path = Path(repo_path)
        
        for ext in supported_extensions:
            supported_files.extend(repo_path.rglob(f"*{ext}"))
        
        # Filter out common directories to ignore
        ignore_dirs = {
            'node_modules', '.git', '__pycache__', '.pytest_cache',
            'venv', 'env', '.venv', 'build', 'dist', '.next',
            'coverage', '.coverage', 'logs', '.logs'
        }
        
        filtered_files = []
        for file_path in supported_files:
            # Check if any parent directory is in ignore list
            if not any(part in ignore_dirs for part in file_path.parts):
                filtered_files.append(str(file_path))
        
        return filtered_files
    
    def get_repo_statistics(self, files: List[str]) -> Dict[str, Any]:
        """Get statistics about the repository"""
        stats = {
            "total_files": len(files),
            "languages": {},
            "total_lines": 0,
            "file_sizes": []
        }
        
        for file_path in files:
            try:
                path = Path(file_path)
                ext = path.suffix.lower()
                
                # Count by language
                if ext == '.py':
                    lang = 'Python'
                elif ext in ['.js', '.jsx', '.ts', '.tsx']:
                    lang = 'JavaScript/TypeScript'
                elif ext == '.java':
                    lang = 'Java'
                else:
                    lang = 'Other'
                
                stats["languages"][lang] = stats["languages"].get(lang, 0) + 1
                
                # Count lines and size
                if path.exists():
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = len(f.readlines())
                        stats["total_lines"] += lines
                    
                    stats["file_sizes"].append(path.stat().st_size)
            
            except Exception:
                continue  # Skip files that can't be read
        
        return stats
