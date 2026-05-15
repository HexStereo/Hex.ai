from pydantic import BaseModel, Field


class DocumentIngestResponse(BaseModel):
    files_processed: int
    chunks_created: int
    embeddings_created: int = 0
    embedding_model: str | None = None
    supported_extensions: list[str]


class DocumentChunkItem(BaseModel):
    id: int
    source_path: str
    chunk_index: int
    content: str
    created_at: str
    score: float | None = None


class DocumentSearchResponse(BaseModel):
    query: str
    search_type: str = Field(default="keyword")
    results: list[DocumentChunkItem]