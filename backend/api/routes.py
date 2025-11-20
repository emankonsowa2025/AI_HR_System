# backend/api/routes.py
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Any, Dict, List
from datetime import datetime
from backend.api.auth_routes import get_current_user
from backend.models.user import User

router = APIRouter()
security = HTTPBearer()

class ChatRequest(BaseModel):
    message: str

class Message(BaseModel):
    role: str
    text: str

class ChatResponse(BaseModel):
    messages: List[Message]

# Simple in-memory chat history (replace with database in production)
chat_history = []

@router.post("/chat")
def chat(
    req: ChatRequest, 
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Chat endpoint that uses OpenAI for responses.
    Requires authentication.
    """
    print(f"💬 Chat request from user: {current_user.username}")
    print(f"📝 Message: {req.message[:100]}...")
    
    # Save user message
    chat_history.append({
        "role": "user",
        "text": req.message,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Try to use OpenAI client from app state
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        from backend.core.config import settings
        
        if not settings.is_openai_configured():
            error_msg = "⚠️ AI features not available. Please configure OPENAI_API_KEY in .env file."
            chat_history.append({
                "role": "assistant",
                "text": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            })
            return {
                "response": error_msg,
                "messages": [{"role": "assistant", "text": error_msg}]
            }
        
        # Initialize OpenAI chat
        chat_client = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Detect if the message is in Arabic
        has_arabic = any('\u0600' <= char <= '\u06FF' for char in req.message)
        
        # Check if JSON format is requested
        needs_json = 'JSON' in req.message or 'json' in req.message or '"phases"' in req.message or '"questions"' in req.message
        
        # Bilingual system message
        if needs_json:
            system_content = """You are AskTech AI Assistant. When user requests JSON format, you MUST respond with ONLY valid JSON, nothing else.

CRITICAL RULES for JSON responses:
1. Return ONLY valid JSON - no explanations before or after
2. No markdown code blocks (no ```json)
3. No additional text or comments
4. Use Arabic text inside JSON values when appropriate
5. Ensure proper JSON structure with quotes and commas

For career roadmap requests, use this structure:
{
    "phases": [
        {
            "title": "Phase title in Arabic",
            "duration": "Duration in Arabic",
            "icon": "emoji",
            "description": "Description in Arabic",
            "skills": ["skill1", "skill2"],
            "resources": ["resource1", "resource2"]
        }
    ]
}

For interview questions, use:
{
    "questions": ["question1 in Arabic", "question2 in Arabic"]
}

For other requests without JSON requirement, respond normally in Arabic in a friendly, concise manner."""
        elif has_arabic:
            system_content = """أنت AskTech، مساعد شغل صاحبك. اتكلم عامي زي الناس، مش رسمي خالص.

القواعد المهمة جداً:
- الرد كله ميزيدش عن 3 جمل بس! ممنوع تزيد.
- كل جملة قصيرة ومباشرة
- كلام بسيط زي الشارع
- لو فيه خطوات: اذكر 2 أو 3 بس
- مفيش أمثلة طويلة، كلمة أو كلمتين
- ممنوع تكرر نفس الفكرة

المواضيع:
- تطوير الشغل
- تحضير انترفيو
- CV ونصايح
- اختيار المجال

الأسلوب: صاحبك بيكلمك، مختصر جداً، تشجيعي.
استخدم "انت، ليك، ازاي، ممكن، جرّب، شوف".
ممنوع التشكيل أو المصطلحات الصعبة.

**مهم جداً: الرد كله = 3 جمل فقط، مش أكتر!**
"""
        else:
            system_content = """You are AskTech, an AI career assistant helping users with:
- Job skills development
- Interview preparation
- Career advice and guidance
- Career path selection

Be helpful, concise, and professional. Always respond in English when the user speaks English."""
        
        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=req.message)
        ]
        
        # Get response from OpenAI
        response = chat_client.invoke(messages)
        assistant_msg = response.content
        
        # Save assistant response
        chat_history.append({
            "role": "assistant",
            "text": assistant_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print(f"✅ Response generated: {assistant_msg[:100]}...")
        
        # Return in the format expected by frontend (with both formats for compatibility)
        return {
            "response": assistant_msg,  # Frontend expects this
            "messages": [{"role": "assistant", "text": assistant_msg}]  # Legacy format
        }
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback
        traceback.print_exc()
        error_msg = f"❌ Error: {str(e)}"
        chat_history.append({
            "role": "assistant",
            "text": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        return {
            "response": error_msg,
            "messages": [{"role": "assistant", "text": error_msg}]
        }

@router.get("/history")
def get_history(current_user: User = Depends(get_current_user)):
    """
    Return chat history. Requires authentication.
    """
    print(f"📜 History request from user: {current_user.username}")
    print(f"📊 Total messages in history: {len(chat_history)}")
    return [Message(role=msg["role"], text=msg["text"]) for msg in chat_history]

@router.delete("/history")
def clear_history(current_user: User = Depends(get_current_user)):
    """
    Clear chat history. Requires authentication.
    """
    global chat_history
    print(f"🗑️ Clearing chat history for user: {current_user.username}")
    chat_history.clear()
    print(f"✅ Chat history cleared. Current count: {len(chat_history)}")
    return {"message": "Chat history cleared successfully", "count": 0}

@router.post("/nim_chat")
def nim_chat(req: ChatRequest, request: Request):
    """
    Forward a simple chat message to NVIDIA NIM chat/completions endpoint and return the JSON result.
    Uses the nim client stored on request.app.state by backend.app startup.
    """
    nim = getattr(request.app.state, "nim_client", None)
    model = getattr(request.app.state, "nim_model", None)
    if nim is None or model is None:
        raise HTTPException(status_code=503, detail="NIM client not configured on server")

    messages = [
        {"role": "system", "content": "/think"},
        {"role": "user", "content": req.message}
    ]
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": 1024,
        "temperature": 0.7,
        "stream": False
    }
'''
    try:
        resp = nim.post("/chat/completions", json=payload)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        # Log and surface provider error as 502
        print("[/api/nim_chat] NIM request failed:", e)
        # you can also log resp.text here if resp exists
        raise HTTPException(status_code=502, detail=f"NIM request failed: {e}")
'''
# NOTE: The authenticated OpenAI-based /chat endpoint is defined above.
# The NIM chat endpoint remains available separately at /api/nim_chat.
