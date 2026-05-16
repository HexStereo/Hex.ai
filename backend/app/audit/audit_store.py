import json
import sqlite3
from pathlib import Path
from typing import Any

from app.config import settings


class CommandAuditStore:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path or settings.MEMORY_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS command_audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    source TEXT NOT NULL,
                    action TEXT NOT NULL,
                    command_text TEXT,
                    command_key TEXT,
                    cwd TEXT NOT NULL,
                    risk_level TEXT,
                    requires_confirmation INTEGER,
                    allowed_to_run INTEGER,
                    executed INTEGER NOT NULL,
                    return_code INTEGER,
                    timed_out INTEGER,
                    reason TEXT,
                    warnings_json TEXT,
                    stdout_preview TEXT,
                    stderr_preview TEXT,
                    confirmation_provided INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def _to_dict(self, value: Any) -> dict:
        if value is None:
            return {}

        if isinstance(value, dict):
            return value

        if hasattr(value, "model_dump"):
            return value.model_dump()

        if hasattr(value, "dict"):
            return value.dict()

        return {}

    def _bool_to_int(self, value: Any) -> int | None:
        if value is None:
            return None

        return 1 if bool(value) else 0

    def _preview(self, value: Any, max_length: int = 2000) -> str | None:
        if value is None:
            return None

        text = str(value)

        if len(text) <= max_length:
            return text

        return text[:max_length] + "\n...[truncated]"

    def _warnings_to_json(self, warnings: list[str] | None) -> str:
        return json.dumps(warnings or [], ensure_ascii=False)

    def _warnings_from_json(self, value: str | None) -> list[str]:
        if not value:
            return []

        try:
            parsed = json.loads(value)

            if isinstance(parsed, list):
                return [str(item) for item in parsed]

            return []

        except json.JSONDecodeError:
            return []

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "source": row["source"],
            "action": row["action"],
            "command_text": row["command_text"],
            "command_key": row["command_key"],
            "cwd": row["cwd"],
            "risk_level": row["risk_level"],
            "requires_confirmation": bool(row["requires_confirmation"])
            if row["requires_confirmation"] is not None
            else None,
            "allowed_to_run": bool(row["allowed_to_run"])
            if row["allowed_to_run"] is not None
            else None,
            "executed": bool(row["executed"]),
            "return_code": row["return_code"],
            "timed_out": bool(row["timed_out"])
            if row["timed_out"] is not None
            else None,
            "reason": row["reason"],
            "warnings": self._warnings_from_json(row["warnings_json"]),
            "stdout_preview": row["stdout_preview"],
            "stderr_preview": row["stderr_preview"],
            "confirmation_provided": bool(row["confirmation_provided"]),
        }

    def record_command_event(
        self,
        source: str,
        action: str,
        cwd: str,
        command_text: str | None = None,
        command_key: str | None = None,
        command_plan: Any = None,
        command_result: Any = None,
        executed: bool = False,
        reason: str | None = None,
        warnings: list[str] | None = None,
        confirmation_provided: bool = False,
    ) -> dict:
        plan = self._to_dict(command_plan)
        result = self._to_dict(command_result)

        resolved_command_text = (
            command_text
            or plan.get("command")
            or result.get("raw_command")
            or result.get("command")
        )

        if isinstance(resolved_command_text, list):
            resolved_command_text = " ".join(str(part) for part in resolved_command_text)

        resolved_command_key = command_key or result.get("command_key")

        risk_level = plan.get("risk_level") or result.get("risk_level")
        requires_confirmation = plan.get("requires_confirmation")
        allowed_to_run = plan.get("allowed_to_run")

        return_code = result.get("return_code")
        timed_out = result.get("timed_out")

        stdout_preview = self._preview(result.get("stdout"))
        stderr_preview = self._preview(result.get("stderr"))

        resolved_reason = reason or plan.get("reason") or result.get("reason")
        resolved_warnings = warnings or plan.get("warnings") or result.get("warnings") or []

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO command_audit_logs (
                    source,
                    action,
                    command_text,
                    command_key,
                    cwd,
                    risk_level,
                    requires_confirmation,
                    allowed_to_run,
                    executed,
                    return_code,
                    timed_out,
                    reason,
                    warnings_json,
                    stdout_preview,
                    stderr_preview,
                    confirmation_provided
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source,
                    action,
                    resolved_command_text,
                    resolved_command_key,
                    cwd,
                    risk_level,
                    self._bool_to_int(requires_confirmation),
                    self._bool_to_int(allowed_to_run),
                    self._bool_to_int(executed),
                    return_code,
                    self._bool_to_int(timed_out),
                    resolved_reason,
                    self._warnings_to_json(resolved_warnings),
                    stdout_preview,
                    stderr_preview,
                    self._bool_to_int(confirmation_provided),
                ),
            )

            audit_id = cursor.lastrowid

            row = connection.execute(
                """
                SELECT *
                FROM command_audit_logs
                WHERE id = ?
                """,
                (audit_id,),
            ).fetchone()

            return self._row_to_dict(row)

    def list_command_events(self, limit: int = 50) -> list[dict]:
        safe_limit = max(1, min(limit, 200))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM command_audit_logs
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

            return [self._row_to_dict(row) for row in rows]