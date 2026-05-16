from typing import Any

from pydantic import BaseModel


class DocumentIngestSourceItem(BaseModel):
    source_path: str
    status: str
    chunks_created: int
    size_bytes: int
    content_hash: str


class DocumentIngestResponse(BaseModel):
    files_processed: int
    files_skipped: int = 0
    files_refreshed: int = 0
    chunks_created: int
    embeddings_created: int = 0
    embedding_model: str | None = None
    supported_extensions: list[str]
    sources: list[DocumentIngestSourceItem]


class DocumentSearchResult(BaseModel):
    id: int
    source_path: str
    chunk_index: int
    content: str
    content_preview: str
    char_count: int
    token_estimate: int
    content_hash: str | None = None
    embedding_model: str | None = None
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    score: float
    score_type: str


class DocumentSearchResponse(BaseModel):
    query: str
    search_type: str
    results: list[DocumentSearchResult]


class DocumentSourceItem(BaseModel):
    id: int
    source_path: str
    file_name: str
    extension: str
    content_hash: str
    size_bytes: int
    modified_at: float
    chunk_count: int
    embedding_model: str | None = None
    created_at: str
    updated_at: str


class DocumentSourceListResponse(BaseModel):
    limit: int
    count: int
    sources: list[DocumentSourceItem]