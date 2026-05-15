from pydantic import BaseModel, Field


class DirectoryItem(BaseModel):
    name: str
    path: str
    type: str = Field(..., description="file or directory")
    size_bytes: int | None = None


class DirectoryListResponse(BaseModel):
    path: str
    items: list[DirectoryItem]


class FileReadResponse(BaseModel):
    path: str
    size_bytes: int
    content: str
    truncated: bool