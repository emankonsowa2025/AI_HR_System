
import requests
import os
import base64
import sys

invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
stream = True
query = "Describe the scene"

kApiKey = "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"

# ext: {mime, media_type}
kSupportedList = {
    "png": ["image/png", "image_url"],
    "jpg": ["image/jpeg", "image_url"],
    "jpeg": ["image/jpeg", "image_url"],
    "webp": ["image/webp", "image_url"],
    "mp4": ["video/mp4", "video_url"],
    "webm": ["video/webm", "video_url"],
    "mov": ["video/mov", "video_url"]
}

def get_extension(filename):
    _, ext = os.path.splitext(filename)
    ext = ext[1:].lower()
    return ext

def mime_type(ext):
    return kSupportedList[ext][0]

def media_type(ext):
    return kSupportedList[ext][1]

def encode_media_base64(media_file):
    """Encode media file to base64 string"""
    with open(media_file, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def chat_with_media(infer_url, media_files, query: str, stream: bool = False):
    assert isinstance(media_files, list), f"{media_files}"
    
    has_video = False
    
    # Build content based on whether we have media files
    if len(media_files) == 0:
        # Text-only mode
        content = query
    else:
        # Build content array with text and media
        content = [{"type": "text", "text": query}]
        
        for media_file in media_files:
            ext = get_extension(media_file)
            assert ext in kSupportedList, f"{media_file} format is not supported"
            
            media_type_key = media_type(ext)
            if media_type_key == "video_url":
                has_video = True
            
            print(f"Encoding {media_file} as base64...")
            base64_data = encode_media_base64(media_file)
            
            # Add media to content array
            media_obj = {
                "type": media_type_key,
                media_type_key: {
                    "url": f"data:{mime_type(ext)};base64,{base64_data}"
                }
            }
            content.append(media_obj)
        
        if has_video:
            assert len(media_files) == 1, "Only single video supported."
    
    headers = {
        "Authorization": f"Bearer {kApiKey}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if stream:
        headers["Accept"] = "text/event-stream"

    # Add system message with appropriate prompt
    # Videos only support /no_think, images support both
    
    system_prompt = "/think"
    
    
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": content,
        }
    ]
    payload = {
        "max_tokens": 4096,
        "temperature": 1,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "messages": messages,
        "stream": stream,
        "model": "nvidia/nemotron-nano-12b-v2-vl",
    }

    response = requests.post(infer_url, headers=headers, json=payload, stream=stream)
    if stream:
        for line in response.iter_lines():
            if line:
                print(line.decode("utf-8"))
    else:
        print(response.json())

if __name__ == "__main__":
    """ Usage:
        python test.py                                    # Text-only
        python test.py sample.mp4                         # Single video
        python test.py sample1.png sample2.png            # Multiple images
    """

    media_samples = list(sys.argv[1:])
    chat_with_media(invoke_url, media_samples, query, stream)








# backend/app.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import traceback

from backend.api.routes import router as api_router
from backend.core.config import settings

# Create the FastAPI app first
app = FastAPI(title="AskTech - Dev Scaffold")

# Ensure folders exist (avoid StaticFiles mount errors)
BASE = Path(__file__).resolve().parent
STATIC_DIR = BASE / "static"
TEMPLATES_DIR = BASE / "templates"

# create directories if they don't exist (safe no-op if they already exist)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# mount static files and templates AFTER app creation
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API router (your routes under /api)
app.include_router(api_router, prefix="/api")


# Startup / Shutdown lifecycle (initialize expensive clients here)
@app.on_event("startup")
def startup_event():
    """
    Initialize NVIDIA embeddings and RAG manager here.
    Import inside the function to avoid doing network/API work on module import.
    """
    # Always initialize to None first
    app.state.embeddings = None
    app.state.rag_manager = None
    
    # validate API key presence
    if not settings.is_nvidia_configured():
        print("[Startup] ⚠️  NVIDIA_API_KEY not configured. RAG features will be DISABLED.")
        print("[Startup] ℹ️  Get your free API key from: https://build.nvidia.com/")
        print("[Startup] ℹ️  Add it to your .env file: NVIDIA_API_KEY=nvapi-...")
        print("[Startup] ✅ Server will start without AI features (basic endpoints still work)")
        return
    
    try:
        # lazy imports (so import-time doesn't attempt API calls)
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
        from backend.services.rag_manager import RAGManager

        print(f"[Startup] 🔧 Initializing NVIDIA embeddings...")
        print(f"[Startup] 📡 Base URL: {settings.NIM_BASE_URL}")
        print(f"[Startup] 🤖 Model: {settings.NVIDIA_MODEL}")
        
        # Test the API key first with a simple embedding call
        test_embeddings = NVIDIAEmbeddings(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NIM_BASE_URL
        )
        
        # Only initialize RAG if embeddings work (skip RAG if API key is invalid)
        app.state.embeddings = test_embeddings
        
        # Initialize RAG manager with skip_initial_index flag to avoid startup errors
        print("[Startup] 📚 Initializing RAG manager (without initial indexing)...")
        app.state.rag_manager = RAGManager(
            embeddings=app.state.embeddings,
            skip_initial_index=True  # Don't try to create index during startup
        )
        print("[Startup] ✅ NVIDIA embeddings and RAG manager initialized successfully!")
        
    except Exception as e:
        # catch & log so startup doesn't crash the whole app; routes can check app.state
        print(f"[Startup] ❌ Error initializing NVIDIA/RAG: {e}")
        print("[Startup] ⚠️  This usually means:")
        print("[Startup]     1. Invalid or expired API key")
        print("[Startup]     2. Network connectivity issues")
        print("[Startup]     3. NVIDIA API service unavailable")
        print("[Startup] ℹ️  Server will start without AI features")
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


# Friendly root: render index.html if present, else redirect to /docs
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return templates.TemplateResponse("index.html", {"request": request})
    # fall back to a simple message
    return HTMLResponse(
        """
        <html>
            <body>
                <h2>AskTech Backend is running</h2>
                <p>Visit <a href="/docs">/docs</a> for API docs or <a href="/chat">/chat</a> for the chat UI (if installed).</p>
            </body>
        </html>
        """
    )


# Simple chat UI route that renders backend/templates/chat.html if present
@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request) -> HTMLResponse:
    """
    Renders the chat UI if 'chat.html' exists in the templates directory; 
    otherwise, returns an informative HTML message indicating the chat UI is not found.
    """
    chat_file = TEMPLATES_DIR / "chat.html"
    if chat_file.exists():
        return templates.TemplateResponse("chat.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>Chat UI not found</h2>"
        '<p>Create <code>backend/templates/chat.html</code> and restart the server.</p>'
        "</body></html>"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8001, reload=True)
