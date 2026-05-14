from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message sent to Hex.ai")
    model: str | None = Field(default=None, description="Optional Ollama model name")


class ChatResponse(BaseModel):
    model: str
    response: str