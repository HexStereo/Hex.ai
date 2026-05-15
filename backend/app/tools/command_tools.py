import re
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

STANDARD_CONFIRMATION_PHRASE = "I_CONFIRM_HEXAI_COMMAND"
FULL_ACCESS_CONFIRMATION_PHRASE = "I_CONFIRM_HEXAI_FULL_ACCESS"


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

    def _truncate_output(self, value: str, label: str) -> str:
        if len(value) > MAX_OUTPUT_CHARS:
            return value[:MAX_OUTPUT_CHARS] + f"\n\n[{label} truncated by Hex.ai]"

        return value

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

            stdout = self._truncate_output(result.stdout or "", "Output")
            stderr = self._truncate_output(result.stderr or "", "Error output")

            return {
                "command_key": command_key,
                "raw_command": None,
                "cwd": self.to_project_relative_path(resolved_cwd),
                "command": command,
                "risk_level": "READ_ONLY",
                "confirmation_used": False,
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": False,
            }

        except subprocess.TimeoutExpired as exc:
            stdout = self._truncate_output(str(exc.stdout or ""), "Output")
            stderr = self._truncate_output(str(exc.stderr or ""), "Error output")

            return {
                "command_key": command_key,
                "raw_command": None,
                "cwd": self.to_project_relative_path(resolved_cwd),
                "command": command,
                "risk_level": "READ_ONLY",
                "confirmation_used": False,
                "return_code": -1,
                "stdout": stdout,
                "stderr": stderr + "\nCommand timed out.",
                "timed_out": True,
            }

    def _normalize_command(self, command: str) -> str:
        return command.strip().lower()

    def _contains_any_word(self, command: str, words: set[str]) -> bool:
        tokens = re.findall(r"[a-zA-Z0-9_.:/\\-]+", command.lower())
        return any(token in words for token in tokens)

    def _starts_with_any(self, command: str, prefixes: tuple[str, ...]) -> bool:
        normalized = self._normalize_command(command)
        return any(normalized.startswith(prefix) for prefix in prefixes)

    def classify_command(self, command: str) -> dict:
        normalized = self._normalize_command(command)

        warnings = []

        if not normalized:
            return {
                "risk_level": "INVALID",
                "requires_confirmation": False,
                "allowed_to_run": False,
                "confirmation_phrase": None,
                "reason": "Command is empty.",
                "warnings": ["Empty commands cannot be executed."],
            }

        if any(symbol in command for symbol in ["&&", "||", "|", ">", ">>", "<"]):
            warnings.append("Command contains shell chaining, piping, or redirection.")

        system_high_risk_words = {
            "format",
            "diskpart",
            "bcdedit",
            "bootrec",
            "reg",
            "shutdown",
            "restart-computer",
            "stop-computer",
            "sc",
            "takeown",
            "icacls",
            "net",
            "cipher",
        }

        destructive_words = {
            "del",
            "erase",
            "rmdir",
            "rd",
            "rm",
            "remove-item",
        }

        network_words = {
            "curl",
            "wget",
            "invoke-webrequest",
            "invoke-restmethod",
            "ssh",
            "scp",
            "ftp",
        }

        script_words = {
            "powershell",
            "pwsh",
            "cmd",
            "wscript",
            "cscript",
        }

        read_only_prefixes = (
            "git status",
            "git log",
            "git diff",
            "python --version",
            "pip --version",
            "pip list",
            "ollama list",
            "dir",
            "tree",
            "where ",
            "echo ",
            "type ",
        )

        dev_safe_prefixes = (
            "dotnet build",
            "dotnet test",
            "dotnet --version",
            "npm test",
            "npm run",
            "pytest",
            "python -m pytest",
            "git branch",
            "git remote -v",
        )

        write_project_prefixes = (
            "git add",
            "git commit",
            "git restore",
            "git checkout",
            "git switch",
            "pip install",
            "npm install",
            "dotnet restore",
            "copy ",
            "xcopy ",
            "robocopy ",
            "move ",
            "ren ",
            "rename ",
            "mkdir ",
            "md ",
        )

        if self._contains_any_word(normalized, system_high_risk_words):
            return {
                "risk_level": "SYSTEM_HIGH_RISK",
                "requires_confirmation": True,
                "allowed_to_run": False,
                "confirmation_phrase": FULL_ACCESS_CONFIRMATION_PHRASE,
                "reason": "This command may modify system-level settings, disks, services, permissions, users, or power state. It is blocked from API execution in v0.9.",
                "warnings": warnings + [
                    "Run this manually in terminal only if you fully understand the consequences."
                ],
            }

        if self._contains_any_word(normalized, destructive_words):
            return {
                "risk_level": "DESTRUCTIVE",
                "requires_confirmation": True,
                "allowed_to_run": True,
                "confirmation_phrase": STANDARD_CONFIRMATION_PHRASE,
                "reason": "This command may delete files or directories.",
                "warnings": warnings + [
                    "Review the target path before running.",
                    "Destructive commands can cause data loss.",
                ],
            }

        if self._contains_any_word(normalized, network_words):
            return {
                "risk_level": "NETWORK",
                "requires_confirmation": True,
                "allowed_to_run": True,
                "confirmation_phrase": STANDARD_CONFIRMATION_PHRASE,
                "reason": "This command may access the network or transfer data.",
                "warnings": warnings + [
                    "Review URLs and remote destinations before running.",
                    "Avoid uploading private files or secrets.",
                ],
            }

        if self._contains_any_word(normalized, script_words) or normalized.endswith(".bat") or normalized.endswith(".ps1"):
            return {
                "risk_level": "SCRIPT_EXECUTION",
                "requires_confirmation": True,
                "allowed_to_run": True,
                "confirmation_phrase": STANDARD_CONFIRMATION_PHRASE,
                "reason": "This command may execute a script or shell command.",
                "warnings": warnings + [
                    "Scripts can perform multiple hidden actions.",
                    "Review script contents before running.",
                ],
            }

        if self._starts_with_any(normalized, read_only_prefixes) and not warnings:
            return {
                "risk_level": "READ_ONLY",
                "requires_confirmation": False,
                "allowed_to_run": True,
                "confirmation_phrase": None,
                "reason": "This command appears to only read information.",
                "warnings": warnings,
            }

        if self._starts_with_any(normalized, dev_safe_prefixes) and not warnings:
            return {
                "risk_level": "DEV_SAFE",
                "requires_confirmation": False,
                "allowed_to_run": True,
                "confirmation_phrase": None,
                "reason": "This command appears to be a standard development command.",
                "warnings": warnings,
            }

        if self._starts_with_any(normalized, write_project_prefixes):
            return {
                "risk_level": "WRITE_PROJECT",
                "requires_confirmation": True,
                "allowed_to_run": True,
                "confirmation_phrase": STANDARD_CONFIRMATION_PHRASE,
                "reason": "This command may modify project files, dependencies, or Git state.",
                "warnings": warnings + [
                    "Review changes with git status and git diff after running.",
                ],
            }

        if warnings:
            return {
                "risk_level": "MIXED_OR_CHAINED",
                "requires_confirmation": True,
                "allowed_to_run": True,
                "confirmation_phrase": STANDARD_CONFIRMATION_PHRASE,
                "reason": "This command contains shell operators or redirection and may perform multiple actions.",
                "warnings": warnings,
            }

        return {
            "risk_level": "UNKNOWN",
            "requires_confirmation": True,
            "allowed_to_run": True,
            "confirmation_phrase": STANDARD_CONFIRMATION_PHRASE,
            "reason": "This command is not recognized by the v0.9 risk classifier.",
            "warnings": [
                "Unknown commands require explicit owner confirmation.",
                "Review the command carefully before running.",
            ],
        }

    def plan_command(self, command: str, cwd: str = ".") -> dict:
        resolved_cwd = self.resolve_cwd(cwd)
        classification = self.classify_command(command)

        return {
            "command": command,
            "cwd": self.to_project_relative_path(resolved_cwd),
            **classification,
        }

    def run_confirmed_command(
        self,
        command: str,
        cwd: str = ".",
        confirmation_phrase: str | None = None,
    ) -> dict:
        resolved_cwd = self.resolve_cwd(cwd)
        plan = self.classify_command(command)

        if not plan["allowed_to_run"]:
            raise PermissionError(
                f"Command is not allowed to run through Hex.ai API. Reason: {plan['reason']}"
            )

        if plan["requires_confirmation"]:
            expected_phrase = plan["confirmation_phrase"]

            if confirmation_phrase != expected_phrase:
                raise PermissionError(
                    f"Confirmation required. Required phrase: {expected_phrase}"
                )

        actual_command = ["cmd", "/c", command]

        try:
            result = subprocess.run(
                actual_command,
                cwd=str(resolved_cwd),
                capture_output=True,
                text=True,
                timeout=COMMAND_TIMEOUT_SECONDS,
                shell=False,
            )

            stdout = self._truncate_output(result.stdout or "", "Output")
            stderr = self._truncate_output(result.stderr or "", "Error output")

            return {
                "command_key": None,
                "raw_command": command,
                "cwd": self.to_project_relative_path(resolved_cwd),
                "command": actual_command,
                "risk_level": plan["risk_level"],
                "confirmation_used": bool(plan["requires_confirmation"]),
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "timed_out": False,
            }

        except subprocess.TimeoutExpired as exc:
            stdout = self._truncate_output(str(exc.stdout or ""), "Output")
            stderr = self._truncate_output(str(exc.stderr or ""), "Error output")

            return {
                "command_key": None,
                "raw_command": command,
                "cwd": self.to_project_relative_path(resolved_cwd),
                "command": actual_command,
                "risk_level": plan["risk_level"],
                "confirmation_used": bool(plan["requires_confirmation"]),
                "return_code": -1,
                "stdout": stdout,
                "stderr": stderr + "\nCommand timed out.",
                "timed_out": True,
            }