"""All configuration in one place. Values come from environment variables or the
project's .env file, with the defaults below. .env is loaded exactly once, here."""

import os
from dataclasses import dataclass, fields
from pathlib import Path

from dotenv import load_dotenv

# src/my_ai_agent/settings.py -> project root, where .env and credentials.json live
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


class MissingSettingError(RuntimeError):
    pass


@dataclass(frozen=True)
class Settings:
    google_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    ollama_model: str = "hermes3:8b"
    wake_word: str = "hey_jarvis"
    wake_threshold: float = 0.5
    whisper_model: str = "base.en"
    notes_dir: str = str(PROJECT_ROOT / "notes")

    @classmethod
    def from_env(cls) -> "Settings":
        """Read each field from the upper-case environment variable of the same name."""
        values = {}
        for field in fields(cls):
            raw = os.getenv(field.name.upper())
            if raw not in (None, ""):
                values[field.name] = float(raw) if field.type is float else raw
        return cls(**values)

    def require(self, name: str) -> str:
        """Return a setting that must be present, or fail with a clear message."""
        value = getattr(self, name)
        if not value:
            raise MissingSettingError(
                f"{name.upper()} is not set. Add it to {PROJECT_ROOT / '.env'}."
            )
        return value


settings = Settings.from_env()
