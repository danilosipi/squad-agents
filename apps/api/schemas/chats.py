"""Schemas REST para chats e mensagens."""

from __future__ import annotations

from typing import Any

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
    mode: str = "meta_orchestrator"
    bootstrap_status: dict[str, Any] | None = None


class RenameChatRequest(BaseModel):
    title: str = Field(..., min_length=1)


class SavePromptRequest(BaseModel):
    title_slug: str = Field(default="prompt", min_length=1)
    content: str = Field(..., min_length=1)


class PendingSquadRunResponse(BaseModel):
    run_id: str
    run_path: str
    status: str


class ChatAttachmentResponse(BaseModel):
    id: int
    chat_id: int
    message_id: int | None = None
    project_slug: str
    file_name: str
    file_path: str
    mime_type: str
    size_bytes: int
    created_at: str
