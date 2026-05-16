from typing import Any

from pydantic import BaseModel, Field


class AgentPlanRequest(BaseModel):
    message: str = Field(
        ...,
        description="User message that Hex.ai should route to the correct internal capability.",
    )
    cwd: str = Field(
        default=".",
        description="Project-relative working directory for command-related planning.",
    )
    model: str | None = Field(
        default=None,
        description="Optional model name for chat or codebase analysis planning.",
    )


class AgentPlanResponse(BaseModel):
    message: str
    intent: str
    confidence: float
    method: str
    endpoint: str
    parameters: dict[str, Any]
    requires_confirmation: bool
    reason: str
    warnings: list[str]