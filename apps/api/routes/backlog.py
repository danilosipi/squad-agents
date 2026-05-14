"""Rotas REST do backlog (PO planner / quadro)."""

from __future__ import annotations

from typing import NoReturn

from fastapi import APIRouter, HTTPException, status

from apps.api.schemas.backlog import (
    AssignTaskRequest,
    CreateEpicRequest,
    CreateStoryRequest,
    CreateTaskRequest,
    EpicResponse,
    PrepareTaskRunResponse,
    StoryResponse,
    TaskResponse,
    UpdateStatusRequest,
)
from core.backlog import backlog_service
from core.backlog import task_run_prepare_service

router = APIRouter()


@router.post(
    "/tasks/{task_id}/prepare-run",
    response_model=PrepareTaskRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_prepare_run_from_task(task_id: int) -> dict:
    """Cria run + input.md no repositório squad-agentes, vincula à tarefa (sem executar squad)."""
    try:
        return task_run_prepare_service.prepare_squad_run_from_task(task_id)
    except ValueError as e:
        msg = str(e)
        if "já possui run associado" in msg:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg) from e
        _raise_from_value_error(e)


def _raise_from_value_error(exc: ValueError) -> NoReturn:
    msg = str(exc)
    not_found = (
        "não encontrado" in msg
        or "não encontrada" in msg
        or "inexistente" in msg
    )
    code = status.HTTP_404_NOT_FOUND if not_found else status.HTTP_400_BAD_REQUEST
    raise HTTPException(status_code=code, detail=msg) from exc


@router.get("/{project_slug}/epics", response_model=list[EpicResponse])
def get_epics(project_slug: str) -> list[dict]:
    try:
        return backlog_service.list_epics(project_slug)
    except ValueError as e:
        _raise_from_value_error(e)


@router.post("/{project_slug}/epics", response_model=EpicResponse, status_code=status.HTTP_201_CREATED)
def post_epic(project_slug: str, body: CreateEpicRequest) -> dict:
    try:
        return backlog_service.create_epic(project_slug, body.title, body.description)
    except ValueError as e:
        _raise_from_value_error(e)


@router.patch("/epics/{epic_id}/status", response_model=EpicResponse)
def patch_epic_status(epic_id: int, body: UpdateStatusRequest) -> dict:
    try:
        return backlog_service.update_epic_status(epic_id, body.status)
    except ValueError as e:
        _raise_from_value_error(e)


@router.get("/{project_slug}/stories", response_model=list[StoryResponse])
def get_stories(project_slug: str) -> list[dict]:
    try:
        return backlog_service.list_stories(project_slug)
    except ValueError as e:
        _raise_from_value_error(e)


@router.post(
    "/{project_slug}/stories",
    response_model=StoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_story(project_slug: str, body: CreateStoryRequest) -> dict:
    try:
        return backlog_service.create_story(
            project_slug,
            body.title,
            body.description,
            body.epic_id,
            body.priority,
        )
    except ValueError as e:
        _raise_from_value_error(e)


@router.patch("/stories/{story_id}/status", response_model=StoryResponse)
def patch_story_status(story_id: int, body: UpdateStatusRequest) -> dict:
    try:
        return backlog_service.update_story_status(story_id, body.status)
    except ValueError as e:
        _raise_from_value_error(e)


@router.get("/{project_slug}/tasks", response_model=list[TaskResponse])
def get_tasks(project_slug: str) -> list[dict]:
    try:
        return backlog_service.list_tasks(project_slug)
    except ValueError as e:
        _raise_from_value_error(e)


@router.post(
    "/{project_slug}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_task(project_slug: str, body: CreateTaskRequest) -> dict:
    try:
        return backlog_service.create_task(
            project_slug,
            body.title,
            body.description,
            body.story_id,
            body.assignee_agent,
        )
    except ValueError as e:
        _raise_from_value_error(e)


@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
def patch_task_status(task_id: int, body: UpdateStatusRequest) -> dict:
    try:
        return backlog_service.update_task_status(task_id, body.status)
    except ValueError as e:
        _raise_from_value_error(e)


@router.patch("/tasks/{task_id}/assign", response_model=TaskResponse)
def patch_task_assign(task_id: int, body: AssignTaskRequest) -> dict:
    try:
        return backlog_service.assign_task_to_agent(task_id, body.assignee_agent)
    except ValueError as e:
        _raise_from_value_error(e)
