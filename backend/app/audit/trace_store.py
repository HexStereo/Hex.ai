import json
import sqlite3
from pathlib import Path
from typing import Any

from app.config import settings


class AgentTraceStore:
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
                CREATE TABLE IF NOT EXISTS agent_execution_traces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    source TEXT NOT NULL,
                    trace_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    cwd TEXT NOT NULL,
                    model TEXT,
                    intent TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    planned_method TEXT NOT NULL,
                    planned_endpoint TEXT NOT NULL,
                    planned_parameters_json TEXT NOT NULL,
                    executed INTEGER NOT NULL,
                    requires_confirmation INTEGER NOT NULL,
                    result_summary_json TEXT,
                    reason TEXT,
                    warnings_json TEXT NOT NULL
                )
                """
            )

    def _bool_to_int(self, value: Any) -> int:
        return 1 if bool(value) else 0

    def _json_dumps(self, value: Any) -> str:
        return json.dumps(value, ensure_ascii=False, default=str)

    def _json_loads(self, value: str | None, fallback: Any) -> Any:
        if not value:
            return fallback

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback

    def _preview_json(self, value: Any, max_length: int = 6000) -> str | None:
        if value is None:
            return None

        text = self._json_dumps(value)

        if len(text) <= max_length:
            return text

        return text[:max_length] + "\n...[truncated]"

    def _summarize_result(self, result: Any) -> dict | list | str | None:
        if result is None:
            return None

        if isinstance(result, dict):
            summary: dict[str, Any] = {
                "type": "dict",
                "keys": list(result.keys()),
            }

            if "command_plan" in result:
                command_plan = result.get("command_plan") or {}

                summary["command_plan"] = {
                    "command": command_plan.get("command"),
                    "cwd": command_plan.get("cwd"),
                    "risk_level": command_plan.get("risk_level"),
                    "requires_confirmation": command_plan.get("requires_confirmation"),
                    "allowed_to_run": command_plan.get("allowed_to_run"),
                    "confirmation_phrase": command_plan.get("confirmation_phrase"),
                }

            if "command_result" in result:
                command_result = result.get("command_result") or {}

                summary["command_result"] = {
                    "command_key": command_result.get("command_key"),
                    "raw_command": command_result.get("raw_command"),
                    "cwd": command_result.get("cwd"),
                    "return_code": command_result.get("return_code"),
                    "timed_out": command_result.get("timed_out"),
                    "stdout_preview": self._text_preview(command_result.get("stdout")),
                    "stderr_preview": self._text_preview(command_result.get("stderr")),
                }

            if "audit_record" in result:
                audit_record = result.get("audit_record") or {}

                summary["audit_record"] = {
                    "id": audit_record.get("id"),
                    "source": audit_record.get("source"),
                    "action": audit_record.get("action"),
                    "risk_level": audit_record.get("risk_level"),
                    "executed": audit_record.get("executed"),
                    "confirmation_provided": audit_record.get("confirmation_provided"),
                }

            if "model" in result:
                summary["model"] = result.get("model")

            if "memory_used" in result:
                summary["memory_used"] = result.get("memory_used")

            if "documents_used" in result:
                summary["documents_used"] = result.get("documents_used")

            if "search_type" in result:
                summary["search_type"] = result.get("search_type")

            if "results" in result and isinstance(result.get("results"), list):
                summary["result_count"] = len(result.get("results") or [])

            if "files_analyzed" in result:
                summary["files_analyzed"] = result.get("files_analyzed")

            if "total_chars" in result:
                summary["total_chars"] = result.get("total_chars")

            return summary

        if isinstance(result, list):
            return {
                "type": "list",
                "count": len(result),
                "preview": result[:5],
            }

        return self._text_preview(result)

    def _text_preview(self, value: Any, max_length: int = 2000) -> str | None:
        if value is None:
            return None

        text = str(value)

        if len(text) <= max_length:
            return text

        return text[:max_length] + "\n...[truncated]"

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "created_at": row["created_at"],
            "source": row["source"],
            "trace_type": row["trace_type"],
            "message": row["message"],
            "cwd": row["cwd"],
            "model": row["model"],
            "intent": row["intent"],
            "confidence": row["confidence"],
            "planned_method": row["planned_method"],
            "planned_endpoint": row["planned_endpoint"],
            "planned_parameters": self._json_loads(
                row["planned_parameters_json"],
                fallback={},
            ),
            "executed": bool(row["executed"]),
            "requires_confirmation": bool(row["requires_confirmation"]),
            "result_summary": self._json_loads(
                row["result_summary_json"],
                fallback=None,
            ),
            "reason": row["reason"],
            "warnings": self._json_loads(
                row["warnings_json"],
                fallback=[],
            ),
        }

    def record_trace(
        self,
        source: str,
        trace_type: str,
        message: str,
        cwd: str,
        model: str | None,
        plan: dict,
        executed: bool,
        requires_confirmation: bool,
        result: Any,
        reason: str,
        warnings: list[str],
    ) -> dict:
        result_summary = self._summarize_result(result)

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO agent_execution_traces (
                    source,
                    trace_type,
                    message,
                    cwd,
                    model,
                    intent,
                    confidence,
                    planned_method,
                    planned_endpoint,
                    planned_parameters_json,
                    executed,
                    requires_confirmation,
                    result_summary_json,
                    reason,
                    warnings_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source,
                    trace_type,
                    message,
                    cwd,
                    model,
                    plan.get("intent", "UNKNOWN"),
                    float(plan.get("confidence", 0.0)),
                    plan.get("method", "UNKNOWN"),
                    plan.get("endpoint", "UNKNOWN"),
                    self._json_dumps(plan.get("parameters", {})),
                    self._bool_to_int(executed),
                    self._bool_to_int(requires_confirmation),
                    self._preview_json(result_summary),
                    reason,
                    self._json_dumps(warnings or []),
                ),
            )

            trace_id = cursor.lastrowid

            row = connection.execute(
                """
                SELECT *
                FROM agent_execution_traces
                WHERE id = ?
                """,
                (trace_id,),
            ).fetchone()

            return self._row_to_dict(row)

    def list_traces(self, limit: int = 50) -> list[dict]:
        safe_limit = max(1, min(limit, 200))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM agent_execution_traces
                ORDER BY id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

            return [self._row_to_dict(row) for row in rows]