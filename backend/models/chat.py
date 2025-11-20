from pydantic import BaseModel
from typing import List, Optional


class Message(BaseModel):
    role: str
    text: str


class ChatRequest(BaseModel):
    message: str
    metadata: Optional[dict] = None


class ChatResponse(BaseModel):
    messages: List[Message]
