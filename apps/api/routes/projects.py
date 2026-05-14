"""Rotas REST de projetos."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from apps.api.schemas.projects import (
    CreateProjectRequest,
    ProjectBootstrapEnsureResponse,
    ProjectBootstrapStatusResponse,
    ProjectResponse,
    RefineContextRequest,
    RefineContextResponse,
    RegisterProjectRequest,
)
from core.projects import project_bootstrap_service, project_service

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[dict]:
    return project_service.list_projects()


@router.get("/{slug}/bootstrap-status", response_model=ProjectBootstrapStatusResponse)
def get_bootstrap_status(slug: str) -> dict:
    return project_bootstrap_service.project_bootstrap_status(slug.strip().lower())


@router.post("/{slug}/bootstrap", response_model=ProjectBootstrapEnsureResponse, status_code=status.HTTP_201_CREATED)
def post_project_bootstrap(slug: str) -> dict:
    try:
        return project_bootstrap_service.ensure_minimal_squad_artifacts(slug.strip().lower())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


@router.post(
    "/{slug}/context/refine",
    response_model=RefineContextResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_refine_context(slug: str, body: RefineContextRequest) -> dict:
    try:
        return project_bootstrap_service.refine_context_markdown_from_chat(
            slug.strip().lower(),
            body.chat_id,
            overwrite=body.overwrite,
        )
    except ValueError as e:
        msg = str(e)
        code = status.HTTP_404_NOT_FOUND if "não encontrado" in msg else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from e


@router.get("/{slug}", response_model=ProjectResponse)
def get_project(slug: str) -> dict:
    row = project_service.get_project_by_slug(slug)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
    return row


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(body: CreateProjectRequest) -> dict:
    try:
        return project_service.create_project(body.name)
    except FileExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post("/register", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def register_project(body: RegisterProjectRequest) -> dict:
    try:
        return project_service.register_existing_project(body.name, body.local_path)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
