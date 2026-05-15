import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Hex.ai")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "qwen2.5-coder:14b")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

    MEMORY_DB_PATH: str = os.getenv("MEMORY_DB_PATH", "./data/memory/hexai_memory.db")
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    DOCUMENTS_PATH: str = os.getenv("DOCUMENTS_PATH", "./data/documents")

    ALLOW_COMMAND_EXECUTION: bool = os.getenv("ALLOW_COMMAND_EXECUTION", "false").lower() == "true"


settings = Settings()