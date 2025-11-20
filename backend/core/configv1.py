# backend/core/config.py
from pathlib import Path
import os
from dotenv import load_dotenv
from typing import Optional

# Project root = two levels above this file (backend/core -> backend -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# Load .env if it exists (silently continue if it does not)
load_dotenv(dotenv_path=str(ENV_PATH), override=False)

def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Helper to read an env var and strip accidental whitespace/newlines."""
    val = os.getenv(key, default)
    if val is None:
        return default
    # strip BOM, whitespace and newlines that might be accidentally pasted
    return val.strip()

class Settings:
    """Application settings loaded from environment / .env."""

    def __init__(self):
        # Keep original raw value accessible for diagnostic if needed
        self._OPENAI_API_KEY_raw: Optional[str] = _get_env("OPENAI_API_KEY", None)

        # Exposed cleaned values
        self.OPENAI_API_KEY: Optional[str] = self._OPENAI_API_KEY_raw
        self.PROJECT_NAME: str = _get_env("PROJECT_NAME", "AskTech") or "AskTech"
        self.SECRET_KEY: str = _get_env("SECRET_KEY", "default-secret") or "default-secret"
        self.DATABASE_URL: str = _get_env("DATABASE_URL", "sqlite:///./asktech.db") or "sqlite:///./asktech.db"

    def is_openai_configured(self) -> bool:
        """Return True if an OpenAI API key appears present and well-formed."""
        if not self.OPENAI_API_KEY:
            return False
        # basic sanity check — project keys start with sk- (sk-proj, sk-live, etc.)
        return self.OPENAI_API_KEY.startswith("sk-")

    def debug_key_repr(self) -> str:
        """
        Return a safe debug representation of the key for logs:
         - shows prefix and suffix lengths but hides middle characters.
        """
        k = self.OPENAI_API_KEY or ""
        if not k:
            return "<missing>"
        if len(k) <= 12:
            return f"{k[:6]}...{k[-3:]}"
        return f"{k[:6]}...{k[-6:]} (len={len(k)})"

# Single settings instance
settings = Settings()

