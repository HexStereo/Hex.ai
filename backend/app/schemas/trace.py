from typing import Any

from pydantic import BaseModel


class AgentTraceItem(BaseModel):
    id: int
    created_at: str
    source: str
    trace_type: str
    message: str
    cwd: str
    model: str | None
    intent: str
    confidence: float
    planned_method: str
    planned_endpoint: str
    planned_parameters: dict[str, Any]
    executed: bool
    requires_confirmation: bool
    result_summary: dict[str, Any] | list[Any] | str | None
    reason: str | None
    warnings: list[str]


class AgentTraceListResponse(BaseModel):
    limit: int
    count: int
    records: list[AgentTraceItem]