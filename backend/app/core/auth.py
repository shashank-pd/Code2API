"""
Authentication and Authorization Manager
Handles user authentication, JWT tokens, and security
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from passlib.context import CryptContext
from fastapi import HTTPException, status
import logging

from .config import settings

logger = logging.getLogger(__name__)

class AuthManager:
    """Manages authentication and authorization"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.ALGORITHM
        self.access_token_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        
        # In-memory user store (in production, use a database)
        self.users_db = {
            "admin": {
                "username": "admin",
                "email": "admin@code2api.com",
                "hashed_password": self.get_password_hash("admin123"),
                "full_name": "Administrator",
                "disabled": False
            },
            "user": {
                "username": "user",
                "email": "user@code2api.com", 
                "hashed_password": self.get_password_hash("user123"),
                "full_name": "Regular User",
                "disabled": False
            }
        }

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """
        Authenticate a user and return a JWT token
        
        Args:
            username: User's username
            password: User's plain text password
        
        Returns:
            JWT token if authentication successful, None otherwise
        """
        try:
            user = self.users_db.get(username)
            
            if not user:
                logger.warning(f"Authentication failed: user {username} not found")
                return None
            
            if not self.verify_password(password, user["hashed_password"]):
                logger.warning(f"Authentication failed: invalid password for {username}")
                return None
            
            if user.get("disabled", False):
                logger.warning(f"Authentication failed: user {username} is disabled")
                return None
            
            # Create access token
            access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
            access_token = self.create_access_token(
                data={"sub": username}, 
                expires_delta=access_token_expires
            )
            
            logger.info(f"User {username} authenticated successfully")
            return access_token
            
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return None

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a JWT token and return the payload
        
        Args:
            token: JWT token to verify
        
        Returns:
            Token payload if valid
        
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials"
                )
            
            # Check if user exists and is active
            user = self.users_db.get(username)
            if not user or user.get("disabled", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or disabled"
                )
            
            return {
                "username": username,
                "email": user["email"],
                "full_name": user["full_name"]
            }
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )

    def create_user(self, username: str, email: str, password: str, full_name: str = None) -> bool:
        """
        Create a new user
        
        Args:
            username: Unique username
            email: User's email address
            password: Plain text password
            full_name: User's full name
        
        Returns:
            True if user created successfully, False otherwise
        """
        try:
            # Check if user already exists
            if username in self.users_db:
                logger.warning(f"User creation failed: {username} already exists")
                return False
            
            # Create new user
            hashed_password = self.get_password_hash(password)
            
            self.users_db[username] = {
                "username": username,
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name or username,
                "disabled": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"User {username} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"User creation failed: {str(e)}")
            return False

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information (without password hash)"""
        user = self.users_db.get(username)
        if user:
            # Return user info without password hash
            return {
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "disabled": user["disabled"],
                "created_at": user.get("created_at")
            }
        return None

    def update_user(self, username: str, updates: Dict[str, Any]) -> bool:
        """Update user information"""
        try:
            if username not in self.users_db:
                return False
            
            user = self.users_db[username]
            
            # Allow updating specific fields
            allowed_fields = ["email", "full_name", "disabled"]
            for field, value in updates.items():
                if field in allowed_fields:
                    user[field] = value
                elif field == "password":
                    user["hashed_password"] = self.get_password_hash(value)
            
            user["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"User {username} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"User update failed: {str(e)}")
            return False

    def delete_user(self, username: str) -> bool:
        """Delete a user"""
        try:
            if username in self.users_db:
                del self.users_db[username]
                logger.info(f"User {username} deleted successfully")
                return True
            return False
            
        except Exception as e:
            logger.error(f"User deletion failed: {str(e)}")
            return False

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (without password hashes)"""
        return [
            {
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"],
                "disabled": user["disabled"],
                "created_at": user.get("created_at")
            }
            for user in self.users_db.values()
        ]

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        try:
            user = self.users_db.get(username)
            if not user:
                return False
            
            # Verify old password
            if not self.verify_password(old_password, user["hashed_password"]):
                logger.warning(f"Password change failed: invalid old password for {username}")
                return False
            
            # Update password
            user["hashed_password"] = self.get_password_hash(new_password)
            user["password_changed_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Password changed successfully for {username}")
            return True
            
        except Exception as e:
            logger.error(f"Password change failed: {str(e)}")
            return False

    def generate_api_key(self, username: str) -> Optional[str]:
        """Generate an API key for a user"""
        try:
            user = self.users_db.get(username)
            if not user:
                return None
            
            # Create a long-lived token for API access
            api_key_data = {
                "sub": username,
                "type": "api_key",
                "exp": datetime.utcnow() + timedelta(days=365)  # 1 year expiry
            }
            
            api_key = jwt.encode(api_key_data, self.secret_key, algorithm=self.algorithm)
            
            # Store API key reference
            if "api_keys" not in user:
                user["api_keys"] = []
            
            user["api_keys"].append({
                "key_id": len(user["api_keys"]) + 1,
                "created_at": datetime.utcnow().isoformat(),
                "last_used": None
            })
            
            logger.info(f"API key generated for {username}")
            return api_key
            
        except Exception as e:
            logger.error(f"API key generation failed: {str(e)}")
            return None

    def revoke_api_key(self, username: str, key_id: int) -> bool:
        """Revoke an API key"""
        try:
            user = self.users_db.get(username)
            if not user or "api_keys" not in user:
                return False
            
            # Find and remove the API key
            user["api_keys"] = [
                key for key in user["api_keys"] 
                if key["key_id"] != key_id
            ]
            
            logger.info(f"API key {key_id} revoked for {username}")
            return True
            
        except Exception as e:
            logger.error(f"API key revocation failed: {str(e)}")
            return False
