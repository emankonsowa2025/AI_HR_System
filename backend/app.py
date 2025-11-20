

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import traceback
from fastapi.staticfiles import StaticFiles
from backend.api.routes import router as api_router
from backend.api.auth_routes import router as auth_router
from backend.api.user_stats import router as user_stats_router
from backend.core.config import settings
from backend.db.database import init_db

app = FastAPI(title="AskTech - Dev Scaffold")
BASE = Path(__file__).resolve().parent
STATIC_DIR = BASE / "Static"
TEMPLATES_DIR = BASE / "Templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
'''
# Video Interview page
@app.get(
    "/video-interview",
    response_class=HTMLResponse,
    name="video_interview_page"  # اسم ثابت نستخدمه في url_for
)
def video_interview_page(request: Request):
    return templates.TemplateResponse(
        "video-interview.html",
        {"request": request}
    )
'''
# Video Interview page
@app.get("/video-interview", response_class=HTMLResponse)
def video_interview_page(request: Request):
    return templates.TemplateResponse("video-interview.html", {"request": request})



# Include API routers (your routes under /api)
app.include_router(api_router, prefix="/api")
app.include_router(auth_router)
app.include_router(user_stats_router)


# Startup / Shutdown lifecycle (initialize expensive clients here)
@app.on_event("startup")
async def startup_event():
    """
    Initialize database and OpenAI embeddings here.
    Import inside the function to avoid doing network/API work on module import.
    """
    # Initialize database
    init_db()
    
    # Always initialize to None first
    app.state.embeddings = None
    app.state.rag_manager = None
    
    # Open browser after a short delay (redirect to login page)
    import sys
    if '--reload' not in sys.argv and os.environ.get('RUN_MAIN') != 'true':
        import webbrowser
        import asyncio
        async def open_browser():
            await asyncio.sleep(1.5)  # Wait for server to be ready
            webbrowser.open('http://127.0.0.1:8001/')
            print("\n🌐 Browser opened at http://127.0.0.1:8001/")
        asyncio.create_task(open_browser())
    
    # validate API key presence
    if not getattr(settings, "OPENAI_API_KEY", None):
        print("[Startup] ⚠️  OPENAI_API_KEY not configured. RAG features will be DISABLED.")
        print("[Startup] ℹ️  Add it to your .env file: OPENAI_API_KEY=sk-...")
        print("[Startup] ✅ Server will start without AI features (basic endpoints still work)")
        return
    
    try:
        # lazy imports (so import-time doesn't attempt API calls)
        from langchain_openai import OpenAIEmbeddings
        from backend.services.rag_manager import RAGManager
        from pydantic import SecretStr

        print(f"[Startup] 🔧 Initializing OpenAI embeddings...")
        
        # initialize and attach to app.state
        # At this point we know OPENAI_API_KEY is not None due to the check above
        api_key = settings.OPENAI_API_KEY
        if api_key is None:
            raise ValueError("OPENAI_API_KEY should not be None at this point")
        app.state.embeddings = OpenAIEmbeddings(api_key=SecretStr(api_key))
        
        # Initialize RAG manager with skip_initial_index flag to avoid startup hang
        print("[Startup] 📚 Initializing RAG manager (without initial indexing)...")
        app.state.rag_manager = RAGManager(
            embeddings=app.state.embeddings,
            skip_initial_index=True  # Don't try to create index during startup
        )
        print("[Startup] ✅ OpenAI embeddings and RAG manager initialized successfully!")
    except Exception as e:
        # catch & log so startup doesn't crash the whole app; routes can check app.state
        print(f"[Startup] ❌ Error initializing OpenAI/RAG: {e}")
        print("[Startup] ⚠️  This usually means:")
        print("[Startup]     1. Invalid or expired API key")
        print("[Startup]     2. Network connectivity issues")
        print("[Startup] ℹ️  Server will start without AI features")
        traceback.print_exc()
        app.state.embeddings = None
        app.state.rag_manager = None


@app.on_event("shutdown")
def shutdown_event():
    rag = getattr(app.state, "rag_manager", None)
    if rag:
        try:
            rag.shutdown()
            print("[Shutdown] RAGManager closed cleanly.")
        except Exception as e:
            print(f"[Shutdown] Error shutting down RAGManager: {e}")


# Welcome/Landing page - public page with Sign In/Sign Up buttons
@app.get("/", response_class=HTMLResponse)
def welcome(request: Request):
    welcome_file = TEMPLATES_DIR / "welcome.html"
    if welcome_file.exists():
        return templates.TemplateResponse("welcome.html", {"request": request})
    # Fallback to login if welcome page doesn't exist
    return RedirectResponse(url="/login")

# Main authenticated page - serves the main app with all services
@app.get("/home", response_class=HTMLResponse)
def home(request: Request):
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return templates.TemplateResponse("index.html", {"request": request})
    # Fallback to login if index page doesn't exist
    return RedirectResponse(url="/login")

# Login page
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    login_file = TEMPLATES_DIR / "login.html"
    if login_file.exists():
        return templates.TemplateResponse("login.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Login page not found</h2></body></html>"
    )

# Register page
@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    register_file = TEMPLATES_DIR / "register.html"
    if register_file.exists():
        return templates.TemplateResponse("register.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Register page not found</h2></body></html>"
    )

# Chat page (protected - JS will check authentication)
@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Chat UI not found</h2>"
        '<p>Create <code>backend/templates/index.html</code> and restart the server.</p>'
        "</body></html>"
    )

# Interview Preparation page
@app.get("/interview", response_class=HTMLResponse)
def interview_page(request: Request):
    interview_file = TEMPLATES_DIR / "interview.html"
    if interview_file.exists():
        return templates.TemplateResponse("interview.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Interview page not found</h2></body></html>"
    )

# Job Requirements page
@app.get("/requirements", response_class=HTMLResponse)
def requirements_page(request: Request):
    requirements_file = TEMPLATES_DIR / "requirements.html"
    if requirements_file.exists():
        return templates.TemplateResponse("requirements.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Requirements page not found</h2></body></html>"
    )

# Top Jobs page
@app.get("/top-jobs", response_class=HTMLResponse)
def top_jobs_page(request: Request):
    top_jobs_file = TEMPLATES_DIR / "top-jobs.html"
    if top_jobs_file.exists():
        return templates.TemplateResponse("top-jobs.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Top Jobs page not found</h2></body></html>"
    )

# Career Path page
@app.get("/career-path", response_class=HTMLResponse)
def career_path_page(request: Request):
    career_path_file = TEMPLATES_DIR / "career-path.html"
    if career_path_file.exists():
        return templates.TemplateResponse("career-path.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Career Path page not found</h2></body></html>"
    )

# Skills Gap Analysis page
@app.get("/skills-gap", response_class=HTMLResponse)
def skills_gap_page(request: Request):
    skills_gap_file = TEMPLATES_DIR / "skills-gap.html"
    if skills_gap_file.exists():
        return templates.TemplateResponse("skills-gap.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Skills Gap page not found</h2></body></html>"
    )

# Mock Interview Simulator page
@app.get("/mock-interview", response_class=HTMLResponse)
def mock_interview_page(request: Request):
    mock_interview_file = TEMPLATES_DIR / "mock-interview.html"
    if mock_interview_file.exists():
        return templates.TemplateResponse("mock-interview.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Mock Interview page not found</h2></body></html>"
    )

# Resume Builder page
@app.get("/resume-builder", response_class=HTMLResponse)
def resume_builder_page(request: Request):
    resume_builder_file = TEMPLATES_DIR / "resume-builder.html"
    if resume_builder_file.exists():
        return templates.TemplateResponse("resume-builder.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Resume Builder page not found</h2></body></html>"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8001, reload=True)
