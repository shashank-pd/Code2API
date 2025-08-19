"""
File utility functions
Handles file operations, uploads, and language detection
"""

import os
import mimetypes
from pathlib import Path
from typing import Optional, Dict, List, Any
import tempfile
import shutil
import logging

logger = logging.getLogger(__name__)

class FileManager:
    """Manages file operations and language detection"""
    
    def __init__(self):
        # Language detection mappings
        self.extension_to_language = {
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
            '.h': 'c',
            '.hpp': 'cpp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.cs': 'csharp',
            '.swift': 'swift',
            '.m': 'objective-c',
            '.pl': 'perl',
            '.sh': 'bash',
            '.ps1': 'powershell',
            '.r': 'r',
            '.jl': 'julia',
            '.lua': 'lua',
            '.dart': 'dart',
            '.elm': 'elm',
            '.clj': 'clojure',
            '.fs': 'fsharp',
            '.vb': 'vb.net',
            '.sql': 'sql',
            '.proto': 'protobuf'
        }
        
        # MIME type mappings
        self.mime_to_language = {
            'text/x-python': 'python',
            'application/javascript': 'javascript',
            'text/javascript': 'javascript',
            'application/x-javascript': 'javascript',
            'text/x-java-source': 'java',
            'text/x-c': 'c',
            'text/x-c++': 'cpp',
            'text/x-go': 'go',
            'text/x-rust': 'rust',
            'application/x-php': 'php',
            'text/x-php': 'php',
            'application/x-ruby': 'ruby',
            'text/x-ruby': 'ruby'
        }

    def detect_language(self, filename: str, content: Optional[str] = None) -> Optional[str]:
        """
        Detect programming language from filename and optionally content
        
        Args:
            filename: Name of the file
            content: File content (optional)
        
        Returns:
            Detected language or None
        """
        try:
            # First try extension-based detection
            file_path = Path(filename)
            extension = file_path.suffix.lower()
            
            if extension in self.extension_to_language:
                return self.extension_to_language[extension]
            
            # Try MIME type detection if available
            try:
                mime_type, _ = mimetypes.guess_type(filename)
                if mime_type in self.mime_to_language:
                    return self.mime_to_language[mime_type]
            except Exception:
                pass
            
            # Content-based detection for files without extensions
            if content:
                return self._detect_language_from_content(content, filename)
            
            logger.warning(f"Could not detect language for file: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"Language detection failed for {filename}: {str(e)}")
            return None

    def _detect_language_from_content(self, content: str, filename: str) -> Optional[str]:
        """Detect language from file content"""
        try:
            content_lower = content.lower().strip()
            
            # Python detection
            if any(keyword in content for keyword in ['def ', 'import ', 'from ', 'class ', '__init__']):
                return 'python'
            
            # JavaScript/TypeScript detection
            if any(keyword in content for keyword in ['function', 'var ', 'let ', 'const ', '=>', 'console.log']):
                if 'interface ' in content or 'type ' in content or ': ' in content:
                    return 'typescript'
                return 'javascript'
            
            # Java detection
            if any(keyword in content for keyword in ['public class', 'public static void main', 'package ', 'import java']):
                return 'java'
            
            # C/C++ detection
            if any(keyword in content for keyword in ['#include', 'int main', 'printf', 'cout', 'namespace']):
                if any(cpp_keyword in content for cpp_keyword in ['cout', 'cin', 'namespace', 'class', 'template']):
                    return 'cpp'
                return 'c'
            
            # Go detection
            if any(keyword in content for keyword in ['package main', 'func main', 'import "', 'fmt.Print']):
                return 'go'
            
            # Rust detection
            if any(keyword in content for keyword in ['fn main', 'use std', 'let mut', 'println!']):
                return 'rust'
            
            # PHP detection
            if content.startswith('<?php') or '<?=' in content:
                return 'php'
            
            # Ruby detection
            if any(keyword in content for keyword in ['def ', 'end', 'puts ', 'require ']):
                return 'ruby'
            
            # SQL detection
            if any(keyword in content_lower for keyword in ['select ', 'insert ', 'update ', 'delete ', 'create table']):
                return 'sql'
            
            # Shell script detection
            if content.startswith('#!/bin/bash') or content.startswith('#!/bin/sh'):
                return 'bash'
            
            # PowerShell detection
            if any(keyword in content for keyword in ['param(', 'Write-Host', 'Get-', 'Set-']):
                return 'powershell'
            
            logger.info(f"Could not detect language from content for: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"Content-based language detection failed: {str(e)}")
            return None

    def validate_file_size(self, file_size: int, max_size_mb: int = 10) -> bool:
        """Validate file size"""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes

    def validate_file_type(self, filename: str, allowed_extensions: List[str] = None) -> bool:
        """Validate file type based on extension"""
        if allowed_extensions is None:
            allowed_extensions = list(self.extension_to_language.keys())
        
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        return extension in allowed_extensions

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        try:
            # Remove directory path components
            filename = os.path.basename(filename)
            
            # Replace dangerous characters
            dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
            for char in dangerous_chars:
                filename = filename.replace(char, '_')
            
            # Limit length
            if len(filename) > 255:
                name, ext = os.path.splitext(filename)
                filename = name[:255-len(ext)] + ext
            
            return filename
            
        except Exception as e:
            logger.error(f"Filename sanitization failed: {str(e)}")
            return "unknown_file"

    def create_temp_file(self, content: str, suffix: str = '.tmp') -> str:
        """Create a temporary file with content"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
                f.write(content)
                return f.name
        except Exception as e:
            logger.error(f"Temporary file creation failed: {str(e)}")
            raise

    def save_uploaded_file(self, file_content: bytes, filename: str, upload_dir: str) -> str:
        """Save uploaded file to disk"""
        try:
            # Ensure upload directory exists
            os.makedirs(upload_dir, exist_ok=True)
            
            # Sanitize filename
            safe_filename = self.sanitize_filename(filename)
            
            # Generate unique filename if file already exists
            file_path = os.path.join(upload_dir, safe_filename)
            counter = 1
            base_name, extension = os.path.splitext(safe_filename)
            
            while os.path.exists(file_path):
                new_filename = f"{base_name}_{counter}{extension}"
                file_path = os.path.join(upload_dir, new_filename)
                counter += 1
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            logger.info(f"Saved uploaded file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"File upload save failed: {str(e)}")
            raise

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            stat = os.stat(file_path)
            file_path_obj = Path(file_path)
            
            # Basic info
            info = {
                'filename': file_path_obj.name,
                'size_bytes': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'extension': file_path_obj.suffix.lower(),
                'created_at': stat.st_ctime,
                'modified_at': stat.st_mtime
            }
            
            # Detect language
            info['language'] = self.detect_language(file_path_obj.name)
            
            # MIME type
            try:
                mime_type, encoding = mimetypes.guess_type(file_path)
                info['mime_type'] = mime_type
                info['encoding'] = encoding
            except Exception:
                info['mime_type'] = None
                info['encoding'] = None
            
            # Line count for text files
            if info['language']:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        info['line_count'] = len(f.readlines())
                except Exception:
                    info['line_count'] = None
            
            return info
            
        except Exception as e:
            logger.error(f"Get file info failed for {file_path}: {str(e)}")
            raise

    def cleanup_temp_files(self, temp_dir: str, older_than_hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            if not os.path.exists(temp_dir):
                return 0
            
            import time
            current_time = time.time()
            cutoff_time = current_time - (older_than_hours * 3600)
            
            deleted_count = 0
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        if os.path.getmtime(file_path) < cutoff_time:
                            os.remove(file_path)
                            deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file {file_path}: {str(e)}")
            
            logger.info(f"Cleaned up {deleted_count} temporary files")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {str(e)}")
            return 0

    def compress_directory(self, directory_path: str, output_path: str) -> str:
        """Compress a directory into a ZIP file"""
        try:
            import zipfile
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(directory_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, directory_path)
                        zipf.write(file_path, arcname)
            
            logger.info(f"Compressed directory {directory_path} to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Directory compression failed: {str(e)}")
            raise

    def extract_archive(self, archive_path: str, extract_to: str) -> str:
        """Extract ZIP archive to directory"""
        try:
            import zipfile
            
            os.makedirs(extract_to, exist_ok=True)
            
            with zipfile.ZipFile(archive_path, 'r') as zipf:
                zipf.extractall(extract_to)
            
            logger.info(f"Extracted archive {archive_path} to {extract_to}")
            return extract_to
            
        except Exception as e:
            logger.error(f"Archive extraction failed: {str(e)}")
            raise

    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported programming languages"""
        languages = []
        
        # Remove duplicates and create language info
        unique_languages = set(self.extension_to_language.values())
        
        for lang in sorted(unique_languages):
            # Get extensions for this language
            extensions = [ext for ext, l in self.extension_to_language.items() if l == lang]
            
            languages.append({
                'name': lang,
                'display_name': lang.title(),
                'extensions': extensions,
                'primary_extension': extensions[0] if extensions else None
            })
        
        return languages
