from langchain.tools import tool
from langchain_core.tools import BaseTool
from typing import Dict, Any, List
import os
import tempfile
import shutil
from pathlib import Path
from github import Github
import zipfile
import requests

@tool
def code_fetcher_tool(repo_url: str, branch: str = "main") -> Dict[str, Any]:
    """
    Fetch code from a GitHub repository and return the file structure and contents.
    
    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
        branch: Git branch to fetch (default: main)
    
    Returns:
        Dictionary containing repository info, file structure, and file contents
    """
    try:
        # Parse GitHub URL
        if repo_url.startswith("https://github.com/"):
            repo_path = repo_url.replace("https://github.com/", "").strip("/")
        elif repo_url.startswith("http://github.com/"):
            repo_path = repo_url.replace("http://github.com/", "").strip("/")
        else:
            return {"error": "Invalid GitHub URL format"}
        
        # Initialize GitHub client
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            g = Github(github_token)
        else:
            g = Github()  # Anonymous access with rate limits
        
        # Get repository
        repo = g.get_repo(repo_path)
        
        # Get repository contents
        contents = repo.get_contents("", ref=branch)
        
        files_data = {}
        file_structure = []
        
        def process_contents(contents_list, path_prefix=""):
            for content in contents_list:
                full_path = f"{path_prefix}/{content.name}" if path_prefix else content.name
                
                if content.type == "dir":
                    # Recursively process directories
                    file_structure.append({
                        "path": full_path,
                        "type": "directory",
                        "size": 0
                    })
                    sub_contents = repo.get_contents(content.path, ref=branch)
                    process_contents(sub_contents, full_path)
                else:
                    # Process files
                    file_structure.append({
                        "path": full_path,
                        "type": "file",
                        "size": content.size
                    })
                    
                    # Only download text files and limit size
                    if (content.size < 1024 * 1024 and  # Less than 1MB
                        any(content.name.endswith(ext) for ext in [
                            '.py', '.js', '.ts', '.java', '.cpp', '.c', '.cs', 
                            '.php', '.rb', '.go', '.rs', '.kt', '.swift', '.m',
                            '.h', '.hpp', '.txt', '.md', '.yml', '.yaml', '.json'
                        ])):
                        try:
                            file_content = content.decoded_content.decode('utf-8')
                            files_data[full_path] = {
                                "content": file_content,
                                "size": content.size,
                                "language": get_language_from_extension(content.name)
                            }
                        except Exception as e:
                            files_data[full_path] = {
                                "error": f"Could not decode file: {str(e)}",
                                "size": content.size
                            }
        
        # Process all contents
        process_contents(contents)
        
        return {
            "success": True,
            "repo_name": repo.name,
            "repo_full_name": repo.full_name,
            "description": repo.description,
            "language": repo.language,
            "default_branch": repo.default_branch,
            "file_structure": file_structure,
            "files_data": files_data,
            "stats": {
                "total_files": len([f for f in file_structure if f["type"] == "file"]),
                "total_directories": len([f for f in file_structure if f["type"] == "directory"]),
                "downloaded_files": len(files_data)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch repository: {str(e)}"
        }

def get_language_from_extension(filename: str) -> str:
    """Get programming language from file extension"""
    extension_map = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.kt': 'kotlin',
        '.swift': 'swift',
        '.m': 'objective-c',
        '.h': 'c',
        '.hpp': 'cpp'
    }
    
    ext = Path(filename).suffix.lower()
    return extension_map.get(ext, 'text')
