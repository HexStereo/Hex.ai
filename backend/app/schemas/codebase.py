from pydantic import BaseModel, Field


class CodebaseAnalyzeRequest(BaseModel):
    path: str = Field(default=".", description="Project-relative path to analyze")
    model: str | None = Field(default=None, description="Optional Ollama model name")
    max_files: int = Field(default=25, ge=1, le=80)
    max_chars_per_file: int = Field(default=2500, ge=500, le=8000)
    max_total_chars: int = Field(default=30000, ge=5000, le=80000)
    focus: str | None = Field(
        default=None,
        description="Optional analysis focus, for example architecture, bugs, security, next steps"
    )


class CodebaseFileItem(BaseModel):
    path: str
    size_bytes: int
    chars_included: int
    truncated: bool


class CodebaseFilesResponse(BaseModel):
    path: str
    file_count: int
    files: list[CodebaseFileItem]


class CodebaseAnalyzeResponse(BaseModel):
    model: str
    path: str
    files_analyzed: int
    total_chars: int
    files: list[CodebaseFileItem]
    response: str