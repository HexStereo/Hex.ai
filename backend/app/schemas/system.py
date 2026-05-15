from pydantic import BaseModel


class PathStatus(BaseModel):
    path: str
    exists: bool
    is_file: bool
    is_dir: bool


class OllamaStatus(BaseModel):
    base_url: str
    reachable: bool
    models: list[str]
    error: str | None = None


class SystemInfoResponse(BaseModel):
    app_name: str
    app_env: str
    version: str
    project_root: str
    default_model: str
    embedding_model: str
    paths: dict[str, PathStatus]
    ollama: OllamaStatus