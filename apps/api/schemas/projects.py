"""Schemas REST para projetos."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProjectResponse(BaseModel):
    id: int
    name: str
    slug: str
    local_path: str
    status: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": False}


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Nome exibido do projeto")


class RegisterProjectRequest(BaseModel):
    name: str = Field(..., min_length=1)
    local_path: str = Field(..., min_length=1)


class ProjectBootstrapStatusResponse(BaseModel):
    project_slug: str
    ok: bool
    block_reason: str | None = None
    local_path_resolved: str = ""
    has_squad_dir: bool = False
    has_context_md: bool = False
    has_backlog_json: bool = False
    context_meets_minimum: bool = False
    needs_bootstrap: bool = True
    ready_for_meta_orchestrator: bool = False
    expected_context_path: str = ""


class ProjectBootstrapEnsureResponse(BaseModel):
    project_slug: str
    local_path_resolved: str
    created_paths: list[str]
    bootstrap_status: dict[str, Any]


class RefineContextRequest(BaseModel):
    chat_id: int = Field(..., ge=1)
    overwrite: bool = True


class RefineContextResponse(BaseModel):
    project_slug: str
    context_path: str
    bootstrap_status: dict[str, Any]
