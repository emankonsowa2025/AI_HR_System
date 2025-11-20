"""Authentication endpoints."""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from pydantic import BaseModel

from backend.core.config import settings
from backend.services.auth_service import auth_service, User

router = APIRouter()
security = HTTPBearer()

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate):
    """Register a new user."""
    user = auth_service.register_user(
        username=user_data.username,
        password=user_data.password,
        email=user_data.email
    )
    
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(user, expires_delta=expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Authenticate user and return token."""
    user = auth_service.authenticate_user(user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(user, expires_delta=expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def get_current_user(current_user: User = Depends(auth_service.get_current_user)):
    """Get current user details."""
    return current_user