from pathlib import Path

import requests

from app.config import PROJECT_ROOT, settings


class SystemDiagnostics:
    def __init__(self, version: str):
        self.version = version

    def resolve_path(self, path_value: str) -> Path:
        path = Path(path_value)

        if path.is_absolute():
            return path

        return PROJECT_ROOT / path

    def get_path_status(self, path_value: str) -> dict:
        resolved_path = self.resolve_path(path_value)

        return {
            "path": str(resolved_path),
            "exists": resolved_path.exists(),
            "is_file": resolved_path.is_file(),
            "is_dir": resolved_path.is_dir(),
        }

    def get_ollama_status(self) -> dict:
        url = f"{settings.OLLAMA_BASE_URL}/api/tags"

        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            models = []

            for model in data.get("models", []):
                name = model.get("name")

                if name:
                    models.append(name)

            return {
                "base_url": settings.OLLAMA_BASE_URL,
                "reachable": True,
                "models": models,
                "error": None,
            }

        except requests.exceptions.RequestException as exc:
            return {
                "base_url": settings.OLLAMA_BASE_URL,
                "reachable": False,
                "models": [],
                "error": str(exc),
            }

    def get_system_info(self) -> dict:
        return {
            "app_name": settings.APP_NAME,
            "app_env": settings.APP_ENV,
            "version": self.version,
            "project_root": str(PROJECT_ROOT),
            "default_model": settings.DEFAULT_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL,
            "paths": {
                "memory_db": self.get_path_status(settings.MEMORY_DB_PATH),
                "documents": self.get_path_status(settings.DOCUMENTS_PATH),
                "vector_db": self.get_path_status(settings.VECTOR_DB_PATH),
            },
            "ollama": self.get_ollama_status(),
        }