from pydantic import BaseModel, Field


class DocumentIngestResponse(BaseModel):
    files_processed: int
    chunks_created: int
    supported_extensions: list[str]


class DocumentChunkItem(BaseModel):
    id: int
    source_path: str
    chunk_index: int
    content: str
    created_at: str


class DocumentSearchResponse(BaseModel):
    query: str
    results: list[DocumentChunkItem]