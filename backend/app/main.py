"""Main FastAPI application."""


from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from api import auth, chat, skills

# Define API_V1_STR if not present in settings
API_V1_STR = getattr(settings, "API_V1_STR", "/api/v1")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=getattr(settings, "VERSION", "1.0.0"),
    openapi_url=f"{API_V1_STR}/openapi.json"
)

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../Templates'))
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Serve the video interview page
@app.get("/video-interview", response_class=HTMLResponse)
async def video_interview(request: Request):
    return templates.TemplateResponse("video-interview.html", {"request": request})

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth.router,
    prefix=f"{API_V1_STR}/auth",
    tags=["authentication"]
)

app.include_router(
    chat.router,
    prefix=f"{API_V1_STR}/chat",
    tags=["chat"]
)

app.include_router(
    skills.router,
    prefix=f"{API_V1_STR}/skills",
    tags=["skills"]
)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to AskTech API",
        "version": getattr(settings, "VERSION", "1.0.0"),
        "docs_url": f"{API_V1_STR}/docs"
    }