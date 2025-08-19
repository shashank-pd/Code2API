"""
Database configuration and connection management
"""

import sqlite3
import os
from typing import Optional, Dict, Any
import logging
from contextlib import asynccontextmanager

from ..core.config import settings

logger = logging.getLogger(__name__)

class Database:
    """Simple SQLite database manager"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or self._get_db_path()
        self.connection = None
        self._ensure_database_exists()

    def _get_db_path(self) -> str:
        """Get database path from settings"""
        if settings.DATABASE_URL.startswith("sqlite:///"):
            return settings.DATABASE_URL.replace("sqlite:///", "")
        return "code2api.db"

    def _ensure_database_exists(self):
        """Ensure database file and tables exist"""
        try:
            # Create directory if it doesn't exist
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            
            # Create tables if they don't exist
            with self.get_connection() as conn:
                self._create_tables(conn)
            
            logger.info(f"Database initialized at: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            raise

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            return conn
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise

    def _create_tables(self, conn: sqlite3.Connection):
        """Create database tables"""
        try:
            # Users table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    full_name TEXT,
                    disabled BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # API keys table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    key_hash TEXT NOT NULL,
                    name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Projects table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    description TEXT,
                    repo_url TEXT,
                    project_path TEXT,
                    status TEXT DEFAULT 'created',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Analysis results table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    analysis_data TEXT,
                    endpoints_count INTEGER DEFAULT 0,
                    files_analyzed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')
            
            # Workflows table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER,
                    project_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    steps_data TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')
            
            # Usage logs table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    endpoint TEXT,
                    method TEXT,
                    status_code INTEGER,
                    response_time_ms REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
            logger.info("Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Table creation failed: {str(e)}")
            raise

    def execute_query(self, query: str, params: tuple = None) -> Optional[sqlite3.Row]:
        """Execute a single query and return one result"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def execute_many(self, query: str, params: tuple = None) -> list:
        """Execute a query and return all results"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert data into table and return the ID"""
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, tuple(data.values()))
                conn.commit()
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Insert failed: {str(e)}")
            raise

    def update(self, table: str, data: Dict[str, Any], where_clause: str, where_params: tuple = None) -> int:
        """Update data in table and return affected rows"""
        try:
            set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
            
            params = list(data.values())
            if where_params:
                params.extend(where_params)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
            raise

    def delete(self, table: str, where_clause: str, where_params: tuple = None) -> int:
        """Delete data from table and return affected rows"""
        try:
            query = f"DELETE FROM {table} WHERE {where_clause}"
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, where_params or ())
                conn.commit()
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Delete failed: {str(e)}")
            raise

    def get_table_info(self, table: str) -> list:
        """Get table schema information"""
        try:
            query = f"PRAGMA table_info({table})"
            return self.execute_many(query)
        except Exception as e:
            logger.error(f"Get table info failed: {str(e)}")
            raise

    def get_tables(self) -> list:
        """Get list of all tables"""
        try:
            query = "SELECT name FROM sqlite_master WHERE type='table'"
            results = self.execute_many(query)
            return [row[0] for row in results]
        except Exception as e:
            logger.error(f"Get tables failed: {str(e)}")
            raise

    def backup_database(self, backup_path: str):
        """Create a backup of the database"""
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
        except Exception as e:
            logger.error(f"Database backup failed: {str(e)}")
            raise

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}
            
            # Get table counts
            for table in ['users', 'projects', 'workflows', 'analysis_results']:
                try:
                    result = self.execute_query(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = result[0] if result else 0
                except:
                    stats[f"{table}_count"] = 0
            
            # Database file size
            if os.path.exists(self.db_path):
                stats['db_size_bytes'] = os.path.getsize(self.db_path)
                stats['db_size_mb'] = round(stats['db_size_bytes'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Get database stats failed: {str(e)}")
            return {}

# Global database instance
_database = None

def get_database() -> Database:
    """Get global database instance"""
    global _database
    if _database is None:
        _database = Database()
    return _database

async def init_database():
    """Initialize database (async version for FastAPI startup)"""
    get_database()
    logger.info("Database initialized successfully")

async def close_database():
    """Close database connections (async version for FastAPI shutdown)"""
    global _database
    if _database and _database.connection:
        _database.connection.close()
        logger.info("Database connections closed")
