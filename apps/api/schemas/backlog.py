"""Schemas REST do backlog (épicos, histórias, tarefas)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BacklogStatus = Literal[
    "backlog",
    "ready",
    "in_progress",
    "in_review",
    "qa",
    "waiting_human_approval",
    "done",
    "blocked",
]

StoryPriority = Literal["low", "medium", "high", "critical"]

AssigneeAgent = Literal["po", "architect", "dev-base", "reviewer", "qa"]


class EpicResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str | None
    status: str
    created_at: str
    updated_at: str


class CreateEpicRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None


class UpdateStatusRequest(BaseModel):
    status: BacklogStatus


class StoryResponse(BaseModel):
    id: int
    epic_id: int | None
    project_id: int
    title: str
    description: str | None
    status: str
    priority: str
    created_at: str
    updated_at: str


class CreateStoryRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    epic_id: int | None = None
    priority: StoryPriority = "medium"


class TaskResponse(BaseModel):
    id: int
    story_id: int | None
    project_id: int
    title: str
    description: str | None
    status: str
    assignee_agent: str | None
    run_id: str | None
    created_at: str
    updated_at: str
    run_status: str | None = None


class CreateTaskRequest(BaseModel):
    title: str = Field(..., min_length=1)
    description: str | None = None
    story_id: int | None = None
    assignee_agent: AssigneeAgent | None = None


class AssignTaskRequest(BaseModel):
    assignee_agent: AssigneeAgent | None = None


class PrepareTaskRunResponse(BaseModel):
    """Resposta após preparar pasta de run + input.md a partir de uma tarefa."""

    task: TaskResponse
    run_id: str
    run_path: str
    input_path: str
