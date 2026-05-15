from pathlib import Path

from app.config import PROJECT_ROOT


BLOCKED_FILE_NAMES = {
    ".env",
}

BLOCKED_DIRECTORY_NAMES = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

BLOCKED_PATHS = {
    PROJECT_ROOT / "data" / "memory",
    PROJECT_ROOT / "data" / "vector_db",
}


ALLOWED_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".cs",
    ".js",
    ".ts",
    ".json",
    ".html",
    ".css",
    ".sql",
    ".bat",
    ".env.example",
    ".gitignore",
    ".yml",
    ".yaml",
    ".toml",
}


MAX_READ_BYTES = 1_000_000
MAX_RETURN_CHARS = 20_000


def is_inside_project(path: Path) -> bool:
    try:
        path.resolve().relative_to(PROJECT_ROOT.resolve())
        return True
    except ValueError:
        return False


def is_blocked_path(path: Path) -> bool:
    resolved = path.resolve()

    if resolved.name in BLOCKED_FILE_NAMES:
        return True

    if any(part in BLOCKED_DIRECTORY_NAMES for part in resolved.parts):
        return True

    for blocked_path in BLOCKED_PATHS:
        try:
            resolved.relative_to(blocked_path.resolve())
            return True
        except ValueError:
            continue

    return False


def is_allowed_text_file(path: Path) -> bool:
    if path.name in {".gitignore", ".env.example"}:
        return True

    return path.suffix.lower() in ALLOWED_TEXT_EXTENSIONS