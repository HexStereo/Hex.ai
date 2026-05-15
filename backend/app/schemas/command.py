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


class CommandRunResponse(BaseModel):
    command_key: str
    cwd: str
    command: list[str]
    return_code: int
    stdout: str
    stderr: str
    timed_out: bool