import subprocess
from pathlib import Path

from app.config import PROJECT_ROOT
from app.security.command_policy import is_blocked_path, is_inside_project


SAFE_COMMANDS: dict[str, list[str]] = {
    "git_status": ["git", "status"],
    "git_log": ["git", "log", "--oneline", "--max-count=10"],
    "git_diff": ["git", "diff"],
    "python_version": ["python", "--version"],
    "pip_version": ["pip", "--version"],
    "pip_list": ["pip", "list"],
    "ollama_list": ["ollama", "list"],
    "tree": ["cmd", "/c", "tree", "/F"],
    "dir": ["cmd", "/c", "dir"],
}


MAX_OUTPUT_CHARS = 20_000
COMMAND_TIMEOUT_SECONDS = 20


class CommandTools:
    def resolve_cwd(self, input_path: str) -> Path:
        if not input_path or input_path.strip() == "":
            input_path = "."

        raw_path = Path(input_path)

        if raw_path.is_absolute():
            resolved_path = raw_path.resolve()
        else:
            resolved_path = (PROJECT_ROOT / raw_path).resolve()

        if not is_inside_project(resolved_path):
            raise PermissionError("Access denied: cwd is outside the Hex.ai project directory.")

        if is_blocked_path(resolved_path):
            raise PermissionError("Access denied: cwd is blocked by Hex.ai safety policy.")

        if not resolved_path.exists():
            raise FileNotFoundError("Working directory not found.")

        if not resolved_path.is_dir():
            raise NotADirectoryError("Working directory is not a directory.")

        return resolved_path

    def to_project_relative_path(self, path: Path) -> str:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))

    def get_allowed_commands(self) -> dict[str, list[str]]:
        return SAFE_COMMANDS

    def run_command(self, command_key: str, cwd: str = ".") -> dict:
        if command_key not in SAFE_COMMANDS:
            raise PermissionError(
                f"Command '{command_key}' is not allowed by Hex.ai safety policy."
            )

        resolved_cwd = self.resolve_cwd(cwd)
        command = SAFE_COMMANDS[command_key]

        try:
            result = subprocess.run(
                command,
                cwd=str(resolved_cwd),
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
                shell=False,
            )

            stdout = result.stdout or ""
            stderr = result.stderr or ""

            if len(stdout) > MAX_OUTPUT_CHARS:
                stdout = stdout[:MAX_OUTPUT_CHARS] + "\n\n[Output truncated by Hex.ai]"

            if len(stderr) > MAX_OUTPUT_CHARS:
                stderr = stderr[:MAX_OUTPUT_CHARS] + "\n\n[Error output truncated by Hex.ai]"

            return {
                "command_key": command_key,
                "cwd": self.to_project_relative_path(resolved_cwd),
                "command": command,
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": False,
            }

        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""

            return {
                "command_key": command_key,
                "cwd": self.to_project_relative_path(resolved_cwd),
                "command": command,
                "return_code": -1,
                "stdout": str(stdout)[:MAX_OUTPUT_CHARS],
                "stderr": str(stderr)[:MAX_OUTPUT_CHARS] + "\nCommand timed out.",
                "timed_out": True,
            }