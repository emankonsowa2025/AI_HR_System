# backend/app.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os, traceback

from backend.api.routes import router as api_router
from backend.core.config import settings

app = FastAPI(title="AskTech - Dev Scaffold")

BASE = Path(__file__).resolve().parent
STATIC_DIR = BASE / "static"
TEMPLATES_DIR = BASE / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    # default state
    app.state.nim_client = None
    app.state.nim_base_url = None
    app.state.nim_model = None

    # Open browser after a short delay (only in main process, not reloader)
    import sys
    if '--reload' not in sys.argv and os.environ.get('RUN_MAIN') != 'true':
        import webbrowser
        import asyncio
        async def open_browser():
            await asyncio.sleep(1.5)  # Wait for server to be ready
            webbrowser.open('http://127.0.0.1:8001/')
            print("\n🌐 Browser opened at http://127.0.0.1:8001/")
        asyncio.create_task(open_browser())

    if settings.is_nvidia_configured():
        try:
            import httpx
            # build client
            headers = {"Authorization": f"Bearer {settings.NVIDIA_API_KEY}"}
            client = httpx.Client(base_url=settings.NIM_BASE_URL, headers=headers, timeout=30.0)
            app.state.nim_client = client
            app.state.nim_base_url = settings.NIM_BASE_URL
            app.state.nim_model = settings.NVIDIA_MODEL
            print("[startup] NVIDIA NIM client initialized.")
            print("[startup] model:", app.state.nim_model, "base_url:", app.state.nim_base_url)
        except Exception as e:
            print("[startup] Could not initialize NIM client:", e)
            traceback.print_exc()
            app.state.nim_client = None
    else:
        print("[startup] NVIDIA not configured. Set NVIDIA_API_KEY/NVIDIA_MODEL in .env to enable NIM.")

    # Note: we intentionally do not initialize embeddings/rag here to keep startup predictable.


@app.on_event("shutdown")
def shutdown_event():
    nim = getattr(app.state, "nim_client", None)
    if nim:
        try:
            nim.close()
            print("[shutdown] Closed NIM client.")
        except Exception:
            pass


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return templates.TemplateResponse("index.html", {"request": request})
    return HTMLResponse(
        "<html><body><h2>AskTech Backend is running</h2>"
        '<p>Visit <a href="/docs">/docs</a> for API docs or <a href="/chat">/chat</a> for the chat UI (if installed).</p>'
        "</body></html>"
    )


@app.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    chat_file = TEMPLATES_DIR / "chat.html"
    if chat_file.exists():
        return templates.TemplateResponse("chat.html", {"request": request})
    return HTMLResponse("<html><body><h2>Chat UI not found</h2><p>Create backend/templates/chat.html</p></body></html>")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8001, reload=True)
