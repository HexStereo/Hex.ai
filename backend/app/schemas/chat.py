from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message sent to Hex.ai")
    model: str | None = Field(default=None, description="Optional Ollama model name")
    use_memory: bool = Field(default=True, description="Whether Hex.ai should use stored memory")


class ChatResponse(BaseModel):
    model: str
    response: str
    memory_used: int = Field(default=0, description="Number of memory records used")