import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from app.config import PROJECT_ROOT, settings


SUPPORTED_EXTENSIONS = {
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
}


class DocumentStore:
    def __init__(self):
        self.db_path = self._resolve_db_path(settings.MEMORY_DB_PATH)
        self.documents_path = self._resolve_path(settings.DOCUMENTS_PATH)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.documents_path.mkdir(parents=True, exist_ok=True)

        self.init_db()

    def _resolve_path(self, path_value: str) -> Path:
        path = Path(path_value)

        if path.is_absolute():
            return path

        return PROJECT_ROOT / path

    def _resolve_db_path(self, path_value: str) -> Path:
        return self._resolve_path(path_value)

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def init_db(self):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS document_embeddings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id INTEGER NOT NULL UNIQUE,
                    embedding_model TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    dimension INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.commit()

    def chunk_text(self, text: str, chunk_size: int = 1800, overlap: int = 200) -> list[str]:
        cleaned_text = text.strip()

        if not cleaned_text:
            return []

        chunks = []
        start = 0

        while start < len(cleaned_text):
            end = start + chunk_size
            chunk = cleaned_text[start:end].strip()

            if chunk:
                chunks.append(chunk)

            start += chunk_size - overlap

        return chunks

    def read_text_file(self, file_path: Path) -> str:
        encodings = ["utf-8", "utf-8-sig", "cp1254", "latin-1"]

        for encoding in encodings:
            try:
                return file_path.read_text(encoding=encoding)
            except UnicodeDecodeError:
                continue

        return file_path.read_text(encoding="utf-8", errors="ignore")

    def clear_file_chunks(self, relative_path: str):
        with self._connect() as connection:
            cursor = connection.cursor()

            cursor.execute(
                """
                DELETE FROM document_embeddings
                WHERE chunk_id IN (
                    SELECT id FROM document_chunks WHERE source_path = ?
                )
                """,
                (relative_path,),
            )

            cursor.execute(
                """
                DELETE FROM document_chunks
                WHERE source_path = ?
                """,
                (relative_path,),
            )

            connection.commit()

    def ingest_documents(
        self,
        embedder: Callable[[str], list[float]] | None = None,
        embedding_model: str | None = None,
    ) -> dict:
        files_processed = 0
        chunks_created = 0
        embeddings_created = 0

        for file_path in self.documents_path.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.name == ".gitkeep":
                continue

            if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            relative_path = str(file_path.relative_to(PROJECT_ROOT))
            text = self.read_text_file(file_path)
            chunks = self.chunk_text(text)

            self.clear_file_chunks(relative_path)

            now = datetime.now(timezone.utc).isoformat()

            with self._connect() as connection:
                cursor = connection.cursor()

                for index, chunk in enumerate(chunks):
                    cursor.execute(
                        """
                        INSERT INTO document_chunks (source_path, chunk_index, content, created_at)
                        VALUES (?, ?, ?, ?)
                        """,
                        (relative_path, index, chunk, now),
                    )

                    chunk_id = cursor.lastrowid
                    chunks_created += 1

                    if embedder is not None:
                        embedding = embedder(chunk)

                        cursor.execute(
                            """
                            INSERT INTO document_embeddings (
                                chunk_id,
                                embedding_model,
                                embedding_json,
                                dimension,
                                created_at
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (
                                chunk_id,
                                embedding_model or settings.EMBEDDING_MODEL,
                                json.dumps(embedding),
                                len(embedding),
                                now,
                            ),
                        )

                        embeddings_created += 1

                connection.commit()

            files_processed += 1

        return {
            "files_processed": files_processed,
            "chunks_created": chunks_created,
            "embeddings_created": embeddings_created,
            "embedding_model": embedding_model or settings.EMBEDDING_MODEL,
            "supported_extensions": sorted(SUPPORTED_EXTENSIONS),
        }

    def _extract_search_terms(self, query: str) -> list[str]:
        raw_terms = (
            query.replace("?", " ")
            .replace(".", " ")
            .replace(",", " ")
            .replace(":", " ")
            .replace(";", " ")
            .replace("!", " ")
            .replace("(", " ")
            .replace(")", " ")
            .split()
        )

        ignored_terms = {
            "ve", "veya", "ile", "icin", "için", "ne", "neler", "hangi",
            "hangisi", "nelerdir", "nedir", "mi", "mı", "mu", "mü",
            "the", "and", "or", "what", "which", "is", "are", "for"
        }

        terms = []

        for term in raw_terms:
            cleaned = term.strip().lower()

            if len(cleaned) < 3:
                continue

            if cleaned in ignored_terms:
                continue

            terms.append(cleaned)

        return terms

    def search_documents(self, query: str, limit: int = 8) -> list[dict]:
        terms = self._extract_search_terms(query)

        if not terms:
            terms = [query.lower()]

        where_parts = []
        parameters = []

        for term in terms:
            where_parts.append("(LOWER(source_path) LIKE ? OR LOWER(content) LIKE ?)")
            search_value = f"%{term}%"
            parameters.extend([search_value, search_value])

        where_clause = " OR ".join(where_parts)

        sql = f"""
            SELECT id, source_path, chunk_index, content, created_at, NULL as score
            FROM document_chunks
            WHERE {where_clause}
            ORDER BY id DESC
            LIMIT ?
        """

        parameters.append(limit)

        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()
            cursor.execute(sql, parameters)
            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def _cosine_similarity(self, vector_a: list[float], vector_b: list[float]) -> float:
        if not vector_a or not vector_b:
            return 0.0

        if len(vector_a) != len(vector_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
        norm_a = math.sqrt(sum(a * a for a in vector_a))
        norm_b = math.sqrt(sum(b * b for b in vector_b))

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)

    def semantic_search_documents(self, query_embedding: list[float], limit: int = 8) -> list[dict]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT
                    document_chunks.id,
                    document_chunks.source_path,
                    document_chunks.chunk_index,
                    document_chunks.content,
                    document_chunks.created_at,
                    document_embeddings.embedding_json
                FROM document_chunks
                INNER JOIN document_embeddings
                    ON document_embeddings.chunk_id = document_chunks.id
                """
            )

            rows = cursor.fetchall()

        scored_results = []

        for row in rows:
            row_dict = dict(row)
            stored_embedding = json.loads(row_dict.pop("embedding_json"))

            score = self._cosine_similarity(query_embedding, stored_embedding)
            row_dict["score"] = round(score, 6)

            scored_results.append(row_dict)

        scored_results.sort(key=lambda item: item["score"], reverse=True)

        return scored_results[:limit]

    def list_recent_chunks(self, limit: int = 5) -> list[dict]:
        with self._connect() as connection:
            connection.row_factory = sqlite3.Row
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT id, source_path, chunk_index, content, created_at, NULL as score
                FROM document_chunks
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()

        return [dict(row) for row in rows]

    def get_document_context(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        limit: int = 5,
    ) -> list[dict]:
        if query_embedding is not None:
            semantic_results = self.semantic_search_documents(
                query_embedding=query_embedding,
                limit=limit,
            )

            if semantic_results:
                return semantic_results

        results = self.search_documents(query=query, limit=limit)

        if results:
            return results

        fallback_queries = [
            "Hex.ai",
            "qwen3-coder",
            "güvenlik",
            "security",
            "local-first",
            "private",
            "GitHub",
            "dangerous commands",
        ]

        for fallback_query in fallback_queries:
            results = self.search_documents(query=fallback_query, limit=limit)

            if results:
                return results

        return self.list_recent_chunks(limit=limit)