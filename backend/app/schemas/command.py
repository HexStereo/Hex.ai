from pydantic import BaseModel, Field


class CommandRunRequest(BaseModel):
    command_key: str = Field(
        ...,
        description="Allowed command key, for example git_status, git_log, python_version"
    )
    cwd: str = Field(
        default=".",
        description="Project-relative working directory"
    )


class CommandPlanRequest(BaseModel):
    command: str = Field(
        ...,
        description="Raw command to analyze before execution"
    )
    cwd: str = Field(
        default=".",
        description="Project-relative working directory"
    )


class CommandPlanResponse(BaseModel):
    command: str
    cwd: str
    risk_level: str
    requires_confirmation: bool
    allowed_to_run: bool
    confirmation_phrase: str | None = None
    reason: str
    warnings: list[str]


class CommandConfirmedRunRequest(BaseModel):
    command: str = Field(
        ...,
        description="Raw command to execute after permission analysis"
    )
    cwd: str = Field(
        default=".",
        description="Project-relative working directory"
    )
    confirmation_phrase: str | None = Field(
        default=None,
        description="Required only for commands that need confirmation"
    )


class CommandRunResponse(BaseModel):
    command_key: str | None = None
    raw_command: str | None = None
    cwd: str
    command: list[str]
    risk_level: str | None = None
    confirmation_used: bool = False
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool