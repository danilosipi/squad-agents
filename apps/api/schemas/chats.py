"""Schemas REST para chats e mensagens."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatResponse(BaseModel):
    id: int
    project_id: int
    title: str
    status: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: str
    content: str
    created_at: str


class CreateChatRequest(BaseModel):
    project_slug: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)


class AddMessageRequest(BaseModel):
    chat_id: int = Field(..., ge=1)
    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)


class MetaOrchestratorMessageRequest(BaseModel):
    chat_id: int = Field(..., ge=1)
    content: str = Field(..., min_length=1)


class MetaOrchestratorMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
    run_id: str
    run_path: str
    status: str
    context_loaded: bool = False
    context_evidence_path: str | None = None


class PendingSquadRunResponse(BaseModel):
    run_id: str
    run_path: str
    status: str
