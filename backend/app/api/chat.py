"""Chat endpoints."""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer

from backend.models.chat import ChatRequest, ChatResponse, Message
from backend.services.chat_service import save_message, get_history
from backend.services.langchain_adapter import generate_chat_response
from backend.services.auth_service import auth_service, User

router = APIRouter()
security = HTTPBearer()

@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    req: ChatRequest, 
    current_user: User = Depends(auth_service.get_current_user)
):
    """Process chat message using LangChain+OpenAI, considering chat history."""
    # persist user message with user context
    save_message(
        role="user", 
        text=req.message, 
        created_at=datetime.utcnow().isoformat()
    )

    # generate response using OpenAI
    reply_text = generate_chat_response(req.message)

    # persist assistant reply
    save_message(
        role="assistant", 
        text=reply_text, 
        created_at=datetime.utcnow().isoformat()
    )

    return ChatResponse(messages=[Message(role="assistant", text=reply_text)])

@router.get("/history", response_model=List[Message])
async def history_endpoint(
    current_user: User = Depends(auth_service.get_current_user)
):
    """Get chat history for authenticated user."""
    rows = get_history()
    return [Message(role=r[1], text=r[2]) for r in rows]