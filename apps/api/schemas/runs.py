"""Schemas REST para execução de runs / squad completa."""

from __future__ import annotations

from pydantic import BaseModel, Field

from apps.api.schemas.backlog import TaskResponse
from apps.api.schemas.chats import MessageResponse


class ExecuteSquadRequest(BaseModel):
    chat_id: int | None = Field(default=None)


class ExecuteSquadResponse(BaseModel):
    status: str
    run_id: str
    final_path: str
    assistant_message: MessageResponse
    context_loaded: bool | None = None
    context_evidence_path: str | None = None


class RunArtifactItem(BaseModel):
    name: str
    type: str
    exists: bool
    content: str | None = None
    truncated: bool | None = None


class RunArtifactsResponse(BaseModel):
    run_id: str
    project_slug: str
    artifacts: list[RunArtifactItem]


class ExecuteBoardRunResponse(BaseModel):
    """Resposta da execução explícita de run preparada pelo Board (sem chat)."""

    status: str
    run_id: str
    final_path: str
    execution_log_path: str
    task: TaskResponse
    error_detail: str | None = None
