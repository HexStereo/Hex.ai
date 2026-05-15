from pathlib import Path

from app.config import PROJECT_ROOT
from app.security.command_policy import (
    MAX_READ_BYTES,
    MAX_RETURN_CHARS,
    is_allowed_text_file,
    is_blocked_path,
    is_inside_project,
)


class FileTools:
    def resolve_project_path(self, input_path: str) -> Path:
        if not input_path or input_path.strip() == "":
            input_path = "."

        raw_path = Path(input_path)

        if raw_path.is_absolute():
            resolved_path = raw_path.resolve()
        else:
            resolved_path = (PROJECT_ROOT / raw_path).resolve()

        if not is_inside_project(resolved_path):
            raise PermissionError("Access denied: path is outside the Hex.ai project directory.")

        if is_blocked_path(resolved_path):
            raise PermissionError("Access denied: this path is blocked by Hex.ai safety policy.")

        return resolved_path

    def to_project_relative_path(self, path: Path) -> str:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))

    def list_directory(self, input_path: str = ".") -> dict:
        target_path = self.resolve_project_path(input_path)

        if not target_path.exists():
            raise FileNotFoundError("Directory not found.")

        if not target_path.is_dir():
            raise NotADirectoryError("Target path is not a directory.")

        items = []

        for child in sorted(target_path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            if is_blocked_path(child):
                continue

            item_type = "directory" if child.is_dir() else "file"
            size_bytes = None

            if child.is_file():
                try:
                    size_bytes = child.stat().st_size
                except OSError:
                    size_bytes = None

            items.append(
                {
                    "name": child.name,
                    "path": self.to_project_relative_path(child),
                    "type": item_type,
                    "size_bytes": size_bytes,
                }
            )

        return {
            "path": self.to_project_relative_path(target_path),
            "items": items,
        }

    def read_file(self, input_path: str) -> dict:
        target_path = self.resolve_project_path(input_path)

        if not target_path.exists():
            raise FileNotFoundError("File not found.")

        if not target_path.is_file():
            raise IsADirectoryError("Target path is not a file.")

        if not is_allowed_text_file(target_path):
            raise PermissionError("Access denied: only approved text/code files can be read.")

        size_bytes = target_path.stat().st_size

        if size_bytes > MAX_READ_BYTES:
            raise PermissionError(
                f"Access denied: file is too large. Max allowed size is {MAX_READ_BYTES} bytes."
            )

        encodings = ["utf-8", "utf-8-sig", "cp1254", "latin-1"]

        content = None

        for encoding in encodings:
            try:
                content = target_path.read_text(encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            content = target_path.read_text(encoding="utf-8", errors="ignore")

        truncated = False

        if len(content) > MAX_RETURN_CHARS:
            content = content[:MAX_RETURN_CHARS]
            truncated = True

        return {
            "path": self.to_project_relative_path(target_path),
            "size_bytes": size_bytes,
            "content": content,
            "truncated": truncated,
        }