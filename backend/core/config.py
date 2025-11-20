# backend/core/config.py
from pathlib import Path
import os
from typing import Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root: two levels above this file (backend/core -> backend -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# Load .env if it exists (silently continue if it does not)
load_dotenv(dotenv_path=str(ENV_PATH), override=False)


class Settings(BaseSettings):
    """Application settings loaded from environment and/or .env."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),          # also let Pydantic read the .env
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI API settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # NVIDIA NIM settings (kept for future use; safe if unset)
    NVIDIA_API_KEY: Optional[str] = None
    NVIDIA_MODEL: str = "nvidia/llama-3.1-nemotron-70b-instruct"
    NIM_BASE_URL: str = "https://integrate.api.nvidia.com/v1"

    # General app settings
    PROJECT_NAME: str = "AskTech"
    # IMPORTANT: Set a secure SECRET_KEY in production via environment variable
    DATABASE_URL: str = "sqlite:///./asktech.db"

    def is_openai_configured(self) -> bool:
        """Return True if an OpenAI API key is present (non-empty string)."""
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip())

    def is_nvidia_configured(self) -> bool:
        """Return True if a NVIDIA (NIM) API key is present (non-empty string)."""
        return bool(self.NVIDIA_API_KEY and isinstance(self.NVIDIA_API_KEY, str) and self.NVIDIA_API_KEY.strip())

    def debug_nvidia_repr(self) -> str:
        """
        Masked representation of the NVIDIA key for safe logs.
        For keys <= 12 chars, show first 3 and last 2 chars.
        For longer keys, show first 6 and last 6 chars, with length.
        """
        k = self.NVIDIA_API_KEY or ""
        if not k:
            return "<missing>"
        if len(k) <= 12:
            return f"{k[:3]}...{k[-2:]} (len={len(k)})"
        return f"{k[:6]}...{k[-6:]} (len={len(k)})"


# Single settings instance
settings = Settings()
