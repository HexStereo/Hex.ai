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


class AgentExecuteRequest(BaseModel):
    message: str = Field(
        ...,
        description="User message that Hex.ai should plan and execute when safe.",
    )
    cwd: str = Field(
        default=".",
        description="Project-relative working directory for command-related execution.",
    )
    model: str | None = Field(
        default=None,
        description="Optional model name for chat or codebase analysis execution.",
    )
    auto_execute_safe_commands: bool = Field(
        default=True,
        description="If true, read-only or development-safe commands can be executed automatically.",
    )


class AgentExecuteResponse(BaseModel):
    message: str
    intent: str
    confidence: float
    planned_method: str
    planned_endpoint: str
    planned_parameters: dict[str, Any]
    executed: bool
    requires_confirmation: bool
    result: dict[str, Any] | list[Any] | str | None
    reason: str
    warnings: list[str]