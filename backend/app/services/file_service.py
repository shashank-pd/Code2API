import os
import aiofiles
import tempfile
import zipfile
import shutil
from pathlib import Path
from typing import Optional
from fastapi import UploadFile
import uuid

class FileService:
    """Service for handling file operations"""
    
    def __init__(self):
        self.temp_dir = Path(tempfile.gettempdir())
        # Use the actual generated API directory
        self.generated_api_dir = Path("generated_api")
        self.generated_apis_dir = Path("generated_apis") 
        # Ensure both directories exist
        self.generated_api_dir.mkdir(exist_ok=True)
        self.generated_apis_dir.mkdir(exist_ok=True)
    
    async def save_uploaded_file(self, file: UploadFile) -> str:
        """Save an uploaded file to temporary directory"""
        # Generate unique filename
        file_id = str(uuid.uuid4())
        file_extension = Path(file.filename).suffix if file.filename else ""
        temp_filename = f"{file_id}{file_extension}"
        temp_path = os.path.join(self.temp_dir, temp_filename)
        
        # Save file content
        async with aiofiles.open(temp_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return temp_path
    
    async def create_api_zip(self, api_path: str) -> str:
        """Create a ZIP file of the generated API"""
        try:
            # Clean up the path - remove Unix-style /tmp prefix if present
            clean_path = api_path.replace('/tmp/generated_apis/', '').replace('/tmp/', '')
            
            # Try both possible API directories
            possible_paths = [
                self.generated_api_dir,  # For current single API generation
                self.generated_apis_dir / clean_path,  # For multiple APIs
                Path(clean_path) if Path(clean_path).exists() else None  # Direct path
            ]
            
            full_api_path = None
            for path in possible_paths:
                if path and path.exists():
                    full_api_path = path
                    break
            
            if not full_api_path:
                raise FileNotFoundError(f"API path not found: {api_path}. Tried paths: {[str(p) for p in possible_paths if p]}")
            
            # Create ZIP file
            safe_name = clean_path.replace('/', '_').replace('\\', '_') or 'generated_api'
            zip_filename = f"{safe_name}.zip"
            zip_path = self.temp_dir / zip_filename
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add all files in the API directory
                for root, dirs, files in os.walk(full_api_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, full_api_path)
                        zipf.write(file_path, arcname)
            
            return str(zip_path)
            
        except Exception as e:
            raise Exception(f"Failed to create ZIP file: {str(e)}")
    
    def create_api_directory(self, repo_name: str) -> str:
        """Create a directory for a new API project"""
        # Sanitize repo name for directory
        safe_name = "".join(c for c in repo_name if c.isalnum() or c in ('-', '_'))
        api_dir = self.generated_apis_dir / safe_name
        
        # Create unique directory if it already exists
        counter = 1
        original_dir = api_dir
        while api_dir.exists():
            api_dir = Path(f"{original_dir}_{counter}")
            counter += 1
        
        api_dir.mkdir(parents=True, exist_ok=True)
        return str(api_dir.relative_to(self.generated_apis_dir))
    
    async def save_generated_file(self, file_path: str, content: str):
        """Save generated content to a file"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(content)
    
    async def cleanup_temp_files(self):
        """Clean up temporary files (called on shutdown)"""
        try:
            # Clean temp files older than 1 hour
            import time
            current_time = time.time()
            temp_path = Path(self.temp_dir)
            
            for file_path in temp_path.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > 3600:  # 1 hour
                        file_path.unlink()
        except Exception as e:
            print(f"Warning: Could not clean temp files: {e}")
    
    def get_api_structure(self, api_path: str) -> dict:
        """Get the structure of a generated API"""
        full_path = self.generated_apis_dir / api_path
        if not full_path.exists():
            return {}
        
        structure = {}
        for item in full_path.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(full_path)
                structure[str(rel_path)] = {
                    "size": item.stat().st_size,
                    "modified": item.stat().st_mtime
                }
        
        return structure
