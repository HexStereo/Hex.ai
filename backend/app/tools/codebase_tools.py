from pathlib import Path

from app.config import PROJECT_ROOT
from app.security.command_policy import (
    is_allowed_text_file,
    is_blocked_path,
    is_inside_project,
)


CODE_EXTENSIONS = {
    ".py",
    ".cs",
    ".js",
    ".ts",
    ".json",
    ".html",
    ".css",
    ".sql",
    ".md",
    ".txt",
    ".bat",
    ".yml",
    ".yaml",
    ".toml",
}


SKIP_DIRECTORY_NAMES = {
    "data",
    "node_modules",
    "dist",
    "build",
    "bin",
    "obj",
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}


PRIORITY_FILE_NAMES = {
    "main.py",
    "config.py",
    "requirements.txt",
    "README.md",
    ".env.example",
    ".gitignore",
}


class CodebaseTools:
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

    def should_skip_path(self, path: Path) -> bool:
        if is_blocked_path(path):
            return True

        path_parts = {part.lower() for part in path.parts}
        skipped_parts = {part.lower() for part in SKIP_DIRECTORY_NAMES}

        return bool(path_parts.intersection(skipped_parts))

    def is_candidate_file(self, path: Path) -> bool:
        if not path.is_file():
            return False

        if self.should_skip_path(path):
            return False

        if path.name in PRIORITY_FILE_NAMES:
            return True

        if path.suffix.lower() not in CODE_EXTENSIONS:
            return False

        return is_allowed_text_file(path)

    def collect_files(self, input_path: str = ".", max_files: int = 25) -> list[Path]:
        target_path = self.resolve_project_path(input_path)

        if not target_path.exists():
            raise FileNotFoundError("Codebase path not found.")

        if target_path.is_file():
            if not self.is_candidate_file(target_path):
                raise PermissionError("Access denied: target file is not allowed for codebase analysis.")

            return [target_path]

        if not target_path.is_dir():
            raise NotADirectoryError("Target path is not a directory or file.")

        files = []

        for file_path in target_path.rglob("*"):
            if self.is_candidate_file(file_path):
                files.append(file_path)

        files = sorted(
            files,
            key=lambda item: (
                0 if item.name in PRIORITY_FILE_NAMES else 1,
                len(item.parts),
                self.to_project_relative_path(item).lower(),
            ),
        )

        return files[:max_files]

    def read_text_file(self, file_path: Path) -> str:
        encodings = ["utf-8", "utf-8-sig", "cp1254", "latin-1"]

        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue

        return file_path.read_text(encoding="utf-8", errors="ignore")

    def collect_code_context(
        self,
        input_path: str = ".",
        max_files: int = 25,
        max_chars_per_file: int = 2500,
        max_total_chars: int = 30000,
    ) -> dict:
        files = self.collect_files(
            input_path=input_path,
            max_files=max_files,
        )

        file_items = []
        context_blocks = []
        total_chars = 0

        for file_path in files:
            raw_content = self.read_text_file(file_path)
            truncated = False

            content = raw_content

            if len(content) > max_chars_per_file:
                content = content[:max_chars_per_file]
                truncated = True

            remaining_chars = max_total_chars - total_chars

            if remaining_chars <= 0:
                break

            if len(content) > remaining_chars:
                content = content[:remaining_chars]
                truncated = True

            relative_path = self.to_project_relative_path(file_path)
            size_bytes = file_path.stat().st_size
            chars_included = len(content)

            file_items.append(
                {
                    "path": relative_path,
                    "size_bytes": size_bytes,
                    "chars_included": chars_included,
                    "truncated": truncated,
                }
            )

            context_block = (
                f"FILE: {relative_path}\n"
                f"SIZE_BYTES: {size_bytes}\n"
                f"TRUNCATED: {truncated}\n\n"
                f"CONTENT:\n"
                f"{content}"
            )

            context_blocks.append(context_block)
            total_chars += chars_included

        resolved_target = self.resolve_project_path(input_path)

        return {
            "path": self.to_project_relative_path(resolved_target),
            "files": file_items,
            "file_count": len(file_items),
            "total_chars": total_chars,
            "context": "\n\n---\n\n".join(context_blocks),
        }

    def build_analysis_prompt(self, code_context: dict, focus: str | None = None) -> str:
        focus_text = focus or (
            "architecture, module responsibilities, risks, missing pieces, "
            "security observations, and next development steps"
        )

        return f"""
Analyze the following Hex.ai codebase context.

Analysis focus:
{focus_text}

Return the answer in this structure:

1. High-level architecture
2. Module-by-module responsibility
3. Current implemented capabilities
4. Technical risks or weak points
5. Security observations
6. Recommended next development steps
7. Short summary

Codebase path:
{code_context["path"]}

Files analyzed:
{code_context["file_count"]}

Code context:
{code_context["context"]}
""".strip()