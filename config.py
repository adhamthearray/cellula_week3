import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


class Settings:
    """Application configuration loaded from environment variables."""

    PROJECT_ROOT = Path(__file__).resolve().parent
    DATABASE_DIR = PROJECT_ROOT / "database" / "chroma_db"
    LOG_DIR = PROJECT_ROOT / "logs"

    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY") or os.getenv("llm_key")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    MODEL_NAME: str = os.getenv("MODEL_NAME", "deepseek/deepseek-chat")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "solutions")
    CHROMA_PERSIST_DIRECTORY: Path = DATABASE_DIR
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))


settings = Settings()
