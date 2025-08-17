"""
Caching module for Code2API
Provides caching for AI analysis results to improve performance
"""
import hashlib
import json
import time
from typing import Dict, Any, Optional
from pathlib import Path
import pickle
import threading
from dataclasses import dataclass

from .config import config


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    data: Any
    timestamp: float
    access_count: int = 0
    last_accessed: float = None
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp


class SimpleCache:
    """Thread-safe in-memory cache with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl  # Time to live in seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
    
    def _generate_key(self, data: Any) -> str:
        """Generate a cache key from data"""
        if isinstance(data, str):
            content = data
        elif isinstance(data, dict):
            content = json.dumps(data, sort_keys=True)
        else:
            content = str(data)
        
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if cache entry is expired"""
        return time.time() - entry.timestamp > self.ttl
    
    def _cleanup_expired(self):
        """Remove expired entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time - entry.timestamp > self.ttl
        ]
        for key in expired_keys:
            del self._cache[key]
    
    def _evict_lru(self):
        """Evict least recently used entries if cache is full"""
        if len(self._cache) >= self.max_size:
            # Sort by last accessed time and remove oldest
            lru_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].last_accessed
            )
            del self._cache[lru_key]
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self._lock:
            self._cleanup_expired()
            
            if key in self._cache:
                entry = self._cache[key]
                if not self._is_expired(entry):
                    entry.access_count += 1
                    entry.last_accessed = time.time()
                    return entry.data
                else:
                    del self._cache[key]
            
            return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache"""
        with self._lock:
            self._cleanup_expired()
            self._evict_lru()
            
            entry = CacheEntry(
                data=value,
                timestamp=time.time(),
                last_accessed=time.time()
            )
            self._cache[key] = entry
    
    def get_by_content(self, content: Any) -> Optional[Any]:
        """Get value by content (generates key automatically)"""
        key = self._generate_key(content)
        return self.get(key)
    
    def put_by_content(self, content: Any, value: Any) -> str:
        """Put value by content (generates key automatically)"""
        key = self._generate_key(content)
        self.put(key, value)
        return key
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            self._cleanup_expired()
            
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_ratio": 0.0 if total_accesses == 0 else 
                    sum(1 for e in self._cache.values() if e.access_count > 0) / len(self._cache),
                "total_accesses": total_accesses,
                "ttl": self.ttl
            }


class PersistentCache:
    """File-based persistent cache"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (config.ROOT_DIR / "cache")
        self.cache_dir.mkdir(exist_ok=True)
        self._memory_cache = SimpleCache(max_size=100, ttl=1800)  # 30 min TTL
    
    def _get_cache_file(self, key: str) -> Path:
        """Get cache file path for key"""
        return self.cache_dir / f"{key}.cache"
    
    def _generate_key(self, data: Any) -> str:
        """Generate a cache key from data"""
        return self._memory_cache._generate_key(data)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache (memory first, then disk)"""
        # Try memory cache first
        value = self._memory_cache.get(key)
        if value is not None:
            return value
        
        # Try disk cache
        cache_file = self._get_cache_file(key)
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                # Check if expired
                if time.time() - entry.timestamp < self._memory_cache.ttl * 2:  # Disk TTL is 2x memory
                    # Load into memory cache
                    self._memory_cache.put(key, entry.data)
                    return entry.data
                else:
                    # Remove expired file
                    cache_file.unlink()
            
            except (pickle.PickleError, FileNotFoundError, EOFError):
                # Handle corrupted cache files
                if cache_file.exists():
                    cache_file.unlink()
        
        return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache (memory and disk)"""
        # Store in memory cache
        self._memory_cache.put(key, value)
        
        # Store in disk cache
        entry = CacheEntry(
            data=value,
            timestamp=time.time()
        )
        
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
        except (pickle.PickleError, OSError) as e:
            # Log error but don't fail
            print(f"Warning: Could not write to cache file {cache_file}: {e}")
    
    def get_by_content(self, content: Any) -> Optional[Any]:
        """Get value by content"""
        key = self._generate_key(content)
        return self.get(key)
    
    def put_by_content(self, content: Any, value: Any) -> str:
        """Put value by content"""
        key = self._generate_key(content)
        self.put(key, value)
        return key
    
    def clear(self):
        """Clear all cache entries"""
        self._memory_cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                cache_file.unlink()
            except OSError:
                pass
    
    def cleanup_expired(self):
        """Clean up expired disk cache files"""
        current_time = time.time()
        ttl_disk = self._memory_cache.ttl * 2
        
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                if current_time - cache_file.stat().st_mtime > ttl_disk:
                    cache_file.unlink()
            except OSError:
                pass
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        memory_stats = self._memory_cache.stats()
        
        # Count disk cache files
        disk_files = len(list(self.cache_dir.glob("*.cache")))
        
        return {
            "memory": memory_stats,
            "disk_files": disk_files,
            "cache_dir": str(self.cache_dir)
        }


# Global cache instances
code_analysis_cache = PersistentCache()
ai_response_cache = SimpleCache(max_size=500, ttl=7200)  # 2 hours


def cache_ai_analysis(func):
    """Decorator to cache AI analysis results"""
    def wrapper(*args, **kwargs):
        # Generate cache key from function arguments
        cache_key_data = {
            "function": func.__name__,
            "args": str(args),
            "kwargs": kwargs
        }
        
        # Try to get from cache
        cached_result = ai_response_cache.get_by_content(cache_key_data)
        if cached_result is not None:
            return cached_result
        
        # Call function and cache result
        result = func(*args, **kwargs)
        ai_response_cache.put_by_content(cache_key_data, result)
        
        return result
    
    return wrapper


def cache_code_analysis(func):
    """Decorator to cache complete code analysis results"""
    def wrapper(*args, **kwargs):
        # Generate cache key from function arguments
        cache_key_data = {
            "function": func.__name__,
            "args": str(args),
            "kwargs": kwargs
        }
        
        # Try to get from cache
        cached_result = code_analysis_cache.get_by_content(cache_key_data)
        if cached_result is not None:
            return cached_result
        
        # Call function and cache result
        result = func(*args, **kwargs)
        code_analysis_cache.put_by_content(cache_key_data, result)
        
        return result
    
    return wrapper


# Cache management functions
def clear_all_caches():
    """Clear all caches"""
    code_analysis_cache.clear()
    ai_response_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches"""
    return {
        "code_analysis": code_analysis_cache.stats(),
        "ai_response": ai_response_cache.stats()
    }


def cleanup_caches():
    """Clean up expired cache entries"""
    code_analysis_cache.cleanup_expired()
    # Memory cache cleanup happens automatically