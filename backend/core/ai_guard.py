# backend/core/ai_guard.py
from backend.core.config import settings

def is_ai_enabled() -> bool:
    """AI is enabled if OpenAI is configured."""
    return bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip())
