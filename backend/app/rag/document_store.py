import hashlib
import json
import math
import sqlite3
from pathlib import Path
from typing import Any, Callable


class DocumentStore:
    def __init__(self, db_path: str | Path | None = None):
        self.project_root = Path(__file__).resolve().parents[3]

        self.db_path = self._resolve_project_path(
            db_path or "data/memory/hexai_documents.db"
        )
        self.documents_path = self._resolve_project_path("data/documents")

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.documents_path.mkdir(parents=True, exist_ok=True)

        self.supported_extensions = {
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

        self._initialize_database()
        self._migrate_database()
        self._create_indexes()

    def _resolve_project_path(self, value: str | Path) -> Path:
        path = Path(value)

        if path.is_absolute():
            return path

        return (self.project_root / path).resolve()

    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT NOT NULL UNIQUE,
                    file_name TEXT NOT NULL DEFAULT '',
                    extension TEXT NOT NULL DEFAULT '',
                    content_hash TEXT NOT NULL DEFAULT '',
                    size_bytes INTEGER NOT NULL DEFAULT 0,
                    modified_at REAL NOT NULL DEFAULT 0,
                    chunk_count INTEGER NOT NULL DEFAULT 0,
                    embedding_model TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_path TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def _create_indexes(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_document_chunks_source_path
                ON document_chunks(source_path)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_document_chunks_content_hash
                ON document_chunks(content_hash)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_document_sources_source_path
                ON document_sources(source_path)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_document_sources_content_hash
                ON document_sources(content_hash)
                """
            )

    def _table_columns(self, table_name: str) -> set[str]:
        with self._connect() as connection:
            rows = connection.execute(
                f"PRAGMA table_info({table_name})"
            ).fetchall()

            return {row["name"] for row in rows}

    def _add_column_if_missing(
        self,
        table_name: str,
        column_name: str,
        column_definition: str,
    ):
        columns = self._table_columns(table_name)

        if column_name in columns:
            return

        with self._connect() as connection:
            connection.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
            )

    def _migrate_database(self):
        self._add_column_if_missing(
            table_name="document_chunks",
            column_name="content_hash",
            column_definition="TEXT",
        )
        self._add_column_if_missing(
            table_name="document_chunks",
            column_name="char_count",
            column_definition="INTEGER NOT NULL DEFAULT 0",
        )
        self._add_column_if_missing(
            table_name="document_chunks",
            column_name="token_estimate",
            column_definition="INTEGER NOT NULL DEFAULT 0",
        )
        self._add_column_if_missing(
            table_name="document_chunks",
            column_name="embedding_json",
            column_definition="TEXT",
        )
        self._add_column_if_missing(
            table_name="document_chunks",
            column_name="embedding_model",
            column_definition="TEXT",
        )

        self._add_column_if_missing(
            table_name="document_sources",
            column_name="file_name",
            column_definition="TEXT NOT NULL DEFAULT ''",
        )
        self._add_column_if_missing(
            table_name="document_sources",
            column_name="extension",
            column_definition="TEXT NOT NULL DEFAULT ''",
        )
        self._add_column_if_missing(
            table_name="document_sources",
            column_name="content_hash",
            column_definition="TEXT NOT NULL DEFAULT ''",
        )
        self._add_column_if_missing(
            table_name="document_sources",
            column_name="size_bytes",
            column_definition="INTEGER NOT NULL DEFAULT 0",
        )
        self._add_column_if_missing(
            table_name="document_sources",
            column_name="modified_at",
            column_definition="REAL NOT NULL DEFAULT 0",
        )
        self._add_column_if_missing(
            table_name="document_sources",
            column_name="chunk_count",
            column_definition="INTEGER NOT NULL DEFAULT 0",
        )
        self._add_column_if_missing(
            table_name="document_sources",
            column_name="embedding_model",
            column_definition="TEXT",
        )
        self._add_column_if_missing(
            table_name="document_sources",
            column_name="created_at",
            column_definition="TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
        )
        self._add_column_if_missing(
            table_name="document_sources",
            column_name="updated_at",
            column_definition="TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP",
        )

        with self._connect() as connection:
            connection.execute(
                """
                UPDATE document_chunks
                SET char_count = LENGTH(content)
                WHERE char_count IS NULL OR char_count = 0
                """
            )

            connection.execute(
                """
                UPDATE document_chunks
                SET token_estimate = CAST((LENGTH(content) / 4) AS INTEGER)
                WHERE token_estimate IS NULL OR token_estimate = 0
                """
            )

            connection.execute(
                """
                UPDATE document_chunks
                SET content_hash = lower(hex(randomblob(16)))
                WHERE content_hash IS NULL OR content_hash = ''
                """
            )

    def _relative_source_path(self, file_path: Path) -> str:
        try:
            return str(file_path.relative_to(self.documents_path)).replace("/", "\\")
        except ValueError:
            return str(file_path).replace("/", "\\")

    def _safe_read_text(self, file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8", errors="ignore")

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()

    def _hash_file(self, file_path: Path) -> str:
        sha256 = hashlib.sha256()

        with file_path.open("rb") as file:
            for block in iter(lambda: file.read(1024 * 1024), b""):
                sha256.update(block)

        return sha256.hexdigest()

    def _json_dumps(self, value: Any) -> str:
        return json.dumps(value, ensure_ascii=False)

    def _json_loads(self, value: str | None, fallback: Any) -> Any:
        if not value:
            return fallback

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return fallback

    def _estimate_tokens(self, text: str) -> int:
        return max(1, math.ceil(len(text) / 4))

    def _normalize_text(self, text: str) -> str:
        normalized_lines: list[str] = []

        for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            cleaned = line.rstrip()

            if cleaned:
                normalized_lines.append(cleaned)
            elif normalized_lines and normalized_lines[-1] != "":
                normalized_lines.append("")

        return "\n".join(normalized_lines).strip()

    def _split_text_into_chunks(
        self,
        text: str,
        max_chars: int = 1400,
        overlap_chars: int = 180,
    ) -> list[str]:
        normalized = self._normalize_text(text)

        if not normalized:
            return []

        paragraphs = [
            paragraph.strip()
            for paragraph in normalized.split("\n\n")
            if paragraph.strip()
        ]

        chunks: list[str] = []
        current = ""

        for paragraph in paragraphs:
            if len(paragraph) > max_chars:
                if current.strip():
                    chunks.append(current.strip())
                    current = ""

                start = 0

                while start < len(paragraph):
                    end = min(start + max_chars, len(paragraph))
                    chunk = paragraph[start:end].strip()

                    if chunk:
                        chunks.append(chunk)

                    if end >= len(paragraph):
                        break

                    start = max(0, end - overlap_chars)

                continue

            candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph

            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())

                current = paragraph

        if current.strip():
            chunks.append(current.strip())

        deduplicated_chunks: list[str] = []
        seen_hashes: set[str] = set()

        for chunk in chunks:
            chunk_hash = self._hash_text(chunk)

            if chunk_hash in seen_hashes:
                continue

            seen_hashes.add(chunk_hash)
            deduplicated_chunks.append(chunk)

        return deduplicated_chunks

    def _cosine_similarity(
        self,
        left: list[float] | None,
        right: list[float] | None,
    ) -> float:
        if not left or not right:
            return 0.0

        if len(left) != len(right):
            return 0.0

        dot_product = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))

        if left_norm == 0 or right_norm == 0:
            return 0.0

        return dot_product / (left_norm * right_norm)

    def _keyword_score(self, query: str, content: str) -> float:
        query_terms = [
            term.strip().lower()
            for term in query.replace("\n", " ").split(" ")
            if len(term.strip()) >= 3
        ]

        if not query_terms:
            return 0.0

        content_lower = content.lower()

        matched_terms = 0
        total_hits = 0

        for term in query_terms:
            hits = content_lower.count(term)

            if hits > 0:
                matched_terms += 1
                total_hits += hits

        coverage_score = matched_terms / len(query_terms)
        frequency_score = min(total_hits / max(len(query_terms), 1), 3.0) / 3.0

        return round((coverage_score * 0.75) + (frequency_score * 0.25), 6)

    def _hybrid_score(
        self,
        semantic_score: float,
        keyword_score: float,
        has_query_embedding: bool,
    ) -> float:
        if has_query_embedding:
            return round((semantic_score * 0.72) + (keyword_score * 0.28), 6)

        return round(keyword_score, 6)

    def _get_existing_source(self, source_path: str) -> sqlite3.Row | None:
        with self._connect() as connection:
            return connection.execute(
                """
                SELECT *
                FROM document_sources
                WHERE source_path = ?
                """,
                (source_path,),
            ).fetchone()

    def _delete_source_chunks(self, source_path: str):
        with self._connect() as connection:
            connection.execute(
                """
                DELETE FROM document_chunks
                WHERE source_path = ?
                """,
                (source_path,),
            )

    def _upsert_source_metadata(
        self,
        source_path: str,
        file_name: str,
        extension: str,
        content_hash: str,
        size_bytes: int,
        modified_at: float,
        chunk_count: int,
        embedding_model: str | None,
    ):
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO document_sources (
                    source_path,
                    file_name,
                    extension,
                    content_hash,
                    size_bytes,
                    modified_at,
                    chunk_count,
                    embedding_model,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(source_path)
                DO UPDATE SET
                    file_name = excluded.file_name,
                    extension = excluded.extension,
                    content_hash = excluded.content_hash,
                    size_bytes = excluded.size_bytes,
                    modified_at = excluded.modified_at,
                    chunk_count = excluded.chunk_count,
                    embedding_model = excluded.embedding_model,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    source_path,
                    file_name,
                    extension,
                    content_hash,
                    size_bytes,
                    modified_at,
                    chunk_count,
                    embedding_model,
                ),
            )

    def _insert_chunks(
        self,
        source_path: str,
        chunks: list[str],
        embedder: Callable[[str], list[float]] | None,
        embedding_model: str | None,
    ) -> int:
        inserted_count = 0

        with self._connect() as connection:
            for index, chunk in enumerate(chunks):
                chunk_hash = self._hash_text(chunk)
                embedding = None

                if embedder:
                    embedding = embedder(chunk)

                connection.execute(
                    """
                    INSERT INTO document_chunks (
                        source_path,
                        chunk_index,
                        content,
                        content_hash,
                        char_count,
                        token_estimate,
                        embedding_json,
                        embedding_model
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        source_path,
                        index,
                        chunk,
                        chunk_hash,
                        len(chunk),
                        self._estimate_tokens(chunk),
                        self._json_dumps(embedding) if embedding is not None else None,
                        embedding_model if embedding is not None else None,
                    ),
                )

                inserted_count += 1

        return inserted_count

    def _iter_supported_document_files(self) -> list[Path]:
        if not self.documents_path.exists():
            return []

        files: list[Path] = []

        for file_path in self.documents_path.rglob("*"):
            if not file_path.is_file():
                continue

            if file_path.suffix.lower() not in self.supported_extensions:
                continue

            files.append(file_path)

        return sorted(files)

    def ingest_documents(
        self,
        embedder: Callable[[str], list[float]] | None = None,
        embedding_model: str | None = None,
    ) -> dict:
        files_processed = 0
        files_skipped = 0
        files_refreshed = 0
        chunks_created = 0
        embeddings_created = 0
        sources: list[dict[str, Any]] = []

        for file_path in self._iter_supported_document_files():
            source_path = self._relative_source_path(file_path)
            extension = file_path.suffix.lower()
            stat = file_path.stat()
            size_bytes = stat.st_size
            modified_at = stat.st_mtime
            content_hash = self._hash_file(file_path)

            existing_source = self._get_existing_source(source_path)

            if existing_source and existing_source["content_hash"] == content_hash:
                files_skipped += 1
                sources.append(
                    {
                        "source_path": source_path,
                        "status": "skipped_unchanged",
                        "chunks_created": 0,
                        "size_bytes": size_bytes,
                        "content_hash": content_hash,
                    }
                )
                continue

            text = self._safe_read_text(file_path)
            chunks = self._split_text_into_chunks(text)

            self._delete_source_chunks(source_path)

            inserted_chunks = self._insert_chunks(
                source_path=source_path,
                chunks=chunks,
                embedder=embedder,
                embedding_model=embedding_model,
            )

            self._upsert_source_metadata(
                source_path=source_path,
                file_name=file_path.name,
                extension=extension,
                content_hash=content_hash,
                size_bytes=size_bytes,
                modified_at=modified_at,
                chunk_count=inserted_chunks,
                embedding_model=embedding_model if embedder else None,
            )

            files_processed += 1
            chunks_created += inserted_chunks

            if embedder:
                embeddings_created += inserted_chunks

            if existing_source:
                files_refreshed += 1

            sources.append(
                {
                    "source_path": source_path,
                    "status": "refreshed" if existing_source else "created",
                    "chunks_created": inserted_chunks,
                    "size_bytes": size_bytes,
                    "content_hash": content_hash,
                }
            )

        return {
            "files_processed": files_processed,
            "files_skipped": files_skipped,
            "files_refreshed": files_refreshed,
            "chunks_created": chunks_created,
            "embeddings_created": embeddings_created,
            "embedding_model": embedding_model,
            "supported_extensions": sorted(self.supported_extensions),
            "sources": sources,
        }

    def _row_to_result(
        self,
        row: sqlite3.Row,
        query: str,
        query_embedding: list[float] | None,
    ) -> dict[str, Any]:
        content = row["content"]
        chunk_embedding = self._json_loads(row["embedding_json"], fallback=None)

        semantic_score = self._cosine_similarity(query_embedding, chunk_embedding)
        keyword_score = self._keyword_score(query, content)
        hybrid_score = self._hybrid_score(
            semantic_score=semantic_score,
            keyword_score=keyword_score,
            has_query_embedding=query_embedding is not None,
        )

        return {
            "id": row["id"],
            "source_path": row["source_path"],
            "chunk_index": row["chunk_index"],
            "content": content,
            "content_preview": content[:500],
            "char_count": row["char_count"],
            "token_estimate": row["token_estimate"],
            "content_hash": row["content_hash"],
            "embedding_model": row["embedding_model"],
            "semantic_score": round(semantic_score, 6),
            "keyword_score": round(keyword_score, 6),
            "score": hybrid_score,
            "score_type": "hybrid" if query_embedding is not None else "keyword",
        }

    def get_document_context(
        self,
        query: str,
        query_embedding: list[float] | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 50))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM document_chunks
                ORDER BY id DESC
                """
            ).fetchall()

        scored_results = [
            self._row_to_result(
                row=row,
                query=query,
                query_embedding=query_embedding,
            )
            for row in rows
        ]

        filtered_results = [
            result
            for result in scored_results
            if result["score"] > 0 or result["keyword_score"] > 0
        ]

        filtered_results.sort(
            key=lambda item: (
                item["score"],
                item["semantic_score"],
                item["keyword_score"],
                -item["chunk_index"],
            ),
            reverse=True,
        )

        return filtered_results[:safe_limit]

    def list_document_sources(self, limit: int = 100) -> list[dict[str, Any]]:
        safe_limit = max(1, min(limit, 500))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM document_sources
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                (safe_limit,),
            ).fetchall()

        return [
            {
                "id": row["id"],
                "source_path": row["source_path"],
                "file_name": row["file_name"],
                "extension": row["extension"],
                "content_hash": row["content_hash"],
                "size_bytes": row["size_bytes"],
                "modified_at": row["modified_at"],
                "chunk_count": row["chunk_count"],
                "embedding_model": row["embedding_model"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]