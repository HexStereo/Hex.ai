from pydantic import BaseModel


class CommandAuditItem(BaseModel):
    id: int
    created_at: str
    source: str
    action: str
    command_text: str | None
    command_key: str | None
    cwd: str
    risk_level: str | None
    requires_confirmation: bool | None
    allowed_to_run: bool | None
    executed: bool
    return_code: int | None
    timed_out: bool | None
    reason: str | None
    warnings: list[str]
    stdout_preview: str | None
    stderr_preview: str | None
    confirmation_provided: bool


class CommandAuditListResponse(BaseModel):
    limit: int
    count: int
    records: list[CommandAuditItem]