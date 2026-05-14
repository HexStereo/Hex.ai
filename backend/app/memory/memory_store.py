import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from app.config import PROJECT_ROOT, settings


class MemoryStore:
    def __init__(self):
        self.db_path = self._resolve_db_path(settings.MEMORY_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _resolve_db_path(self, path_value: str) -> Path:
        path = Path(path_value)

        if path.is_absolute():
            return path

        return PROJECT_ROOT / path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    category TEXT NOT NULL DEFAULT 'general',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def add_memory(self, key: str, value: str, category: str = "general") -> dict:
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO memories (key, value, category, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (key, value, category, now, now),
            )

            connection.commit()
            memory_id = cursor.lastrowid

        return {
            "id": memory_id,
            "key": key,
            "value": value,
            "category": category,
            "created_at": now,
            "updated_at": now,
        }

    def list_memories(self, limit: int = 50) -> list[dict]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, key, value, category, created_at, updated_at
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def search_memories(self, query: str, limit: int = 10) -> list[dict]:
        search_value = f"%{query}%"

        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, key, value, category, created_at, updated_at
                FROM memories
                WHERE key LIKE ? OR value LIKE ? OR category LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (search_value, search_value, search_value, limit),
            )

            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_memory_context(self, query: str, limit: int = 8) -> list[dict]:
        """
        First tries to find memories related to the user query.
        If no direct match is found, returns recent memories as fallback.

        This is a simple v0.2 memory retrieval system.
        Later, this will be replaced or improved with vector search / RAG.
        """

        matched_memories = self.search_memories(query=query, limit=limit)

        if matched_memories:
            return matched_memories

        return self.list_memories(limit=limit)