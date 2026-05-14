from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    key: str = Field(..., description="Short memory key")
    value: str = Field(..., description="Memory value")
    category: str = Field(default="general", description="Memory category")


class MemoryItem(BaseModel):
    id: int
    key: str
    value: str
    category: str
    created_at: str
    updated_at: str