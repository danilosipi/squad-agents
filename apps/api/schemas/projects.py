"""Schemas REST para projetos."""

from __future__ import annotations

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
