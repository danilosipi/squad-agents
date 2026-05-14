"""Rotas REST de projetos."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from apps.api.schemas.projects import CreateProjectRequest, ProjectResponse, RegisterProjectRequest
from core.projects import project_service

router = APIRouter()


@router.get("", response_model=list[ProjectResponse])
def list_projects() -> list[dict]:
    return project_service.list_projects()


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
