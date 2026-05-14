"""Schemas REST para execução de runs / squad completa."""

from __future__ import annotations

from pydantic import BaseModel, Field

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
