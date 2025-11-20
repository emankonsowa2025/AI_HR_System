"""User authentication and session management."""

from datetime import datetime, timedelta
from typing import Optional, Dict
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from backend.core.config import settings
from backend.db.db import get_connection

class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None

class AuthService:
    def __init__(self):
        self.security = HTTPBearer()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret = settings.SECRET_KEY or "your-secret-key"  # Use proper secret in production
        
        # Initialize users table
        self._init_db()
    
    def _init_db(self):
        """Initialize users table."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT,
                last_login TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, user: User, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)
        
        to_encode = {
            "exp": expire,
            "user_id": user.id,
            "username": user.username,
            "email": user.email
        }
        return jwt.encode(to_encode, self.secret, algorithm="HS256")
    
    def register_user(self, username: str, password: str, email: Optional[str] = None) -> User:
        """Register a new user."""
        conn = get_connection()
        cur = conn.cursor()
        
        # Check if username exists
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Create user
        user_id = username.lower()  # Simple ID generation, use UUID in production
        password_hash = self.get_password_hash(password)
        now = datetime.utcnow().isoformat()
        
        try:
            cur.execute(
                "INSERT INTO users (id, username, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, email, password_hash, now)
            )
            conn.commit()
        except Exception as e:
            conn.close()
            raise HTTPException(status_code=400, detail=str(e))
        
        conn.close()
        return User(id=user_id, username=username, email=email)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user and return user object."""
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, username, email, password_hash FROM users WHERE username = ?", (username,))
        user_row = cur.fetchone()
        
        if not user_row or not self.verify_password(password, user_row[3]):
            conn.close()
            return None
        
        # Update last login
        cur.execute(
            "UPDATE users SET last_login = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), user_row[0])
        )
        conn.commit()
        conn.close()
        
        return User(id=user_row[0], username=user_row[1], email=user_row[2])
    
    def get_current_user(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> User:
        """Validate JWT token and return current user."""
        try:
            token = credentials.credentials
            payload = jwt.decode(token, self.secret, algorithms=["HS256"])
            user = User(
                id=payload["user_id"],
                username=payload["username"],
                email=payload.get("email")
            )
            return user
        except (jwt.JWTError, KeyError):
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Global instance
auth_service = AuthService()