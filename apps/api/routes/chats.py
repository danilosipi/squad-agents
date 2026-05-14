"""Rotas REST de chats e mensagens."""

from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, status

from apps.api.schemas.chats import (
    AddMessageRequest,
    ChatResponse,
    CreateChatRequest,
    MessageResponse,
    MetaOrchestratorMessageRequest,
    MetaOrchestratorMessageResponse,
    PendingSquadRunResponse,
)
from core.chats import chat_service
from core.orchestration import meta_orchestrator_service
from core.projects import project_context_service
from core import squad_runs

router = APIRouter()

_HUMAN_SQUAD_APPROVAL_NOTE = (
    "\n\n---\n\n### Aprovação humana necessária\n\n"
    "O plano acima foi gerado pelo meta-orquestrador. Para executar a **squad completa** "
    "(PO → Arquiteto → Dev Base → Reviewer → QA), confirme na interface clicando em "
    "**Executar squad**.\n\n"
    "_Nenhuma execução adicional ocorre sem essa confirmação explícita._"
)


@router.get("/project/{project_slug}", response_model=list[ChatResponse])
def list_chats_for_project(project_slug: str) -> list[dict]:
    try:
        return chat_service.list_chats(project_slug)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(body: CreateChatRequest) -> dict:
    try:
        return chat_service.create_chat(body.project_slug, body.title)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{chat_id}/messages", response_model=list[MessageResponse])
def list_messages(chat_id: int) -> list[dict]:
    try:
        return chat_service.list_messages(chat_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{chat_id}/pending-squad-run", response_model=PendingSquadRunResponse | None)
def get_pending_squad_run(chat_id: int) -> dict | None:
    chat_row = chat_service.get_chat_with_project(chat_id)
    if not chat_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat não encontrado.")
    row = squad_runs.get_pending_approval_run_for_chat(chat_id)
    if not row:
        return None
    return {
        "run_id": str(row["run_id"]),
        "run_path": str(row["run_path"]),
        "status": str(row["status"]),
    }


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_message(body: AddMessageRequest) -> dict:
    try:
        return chat_service.add_message(body.chat_id, body.role, body.content)
    except ValueError as e:
        msg = str(e)
        code = (
            status.HTTP_400_BAD_REQUEST
            if "role inválido" in msg
            else status.HTTP_404_NOT_FOUND
        )
        raise HTTPException(status_code=code, detail=msg) from e


@router.post(
    "/messages/with-meta-orchestrator",
    response_model=MetaOrchestratorMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_message_with_meta_orchestrator(body: MetaOrchestratorMessageRequest) -> dict:
    chat_row = chat_service.get_chat_with_project(body.chat_id)
    if not chat_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat não encontrado.")

    slug = (chat_row.get("project_slug") or "").strip().lower()
    if slug != "cap":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=meta_orchestrator_service.UNSUPPORTED_PROJECT_MESSAGE,
        )

    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=meta_orchestrator_service.MISSING_OPENAI_MESSAGE,
        )

    ok_ctx, err_ctx, ctx_path_hint = project_context_service.minimum_project_context_status(slug)
    if not ok_ctx:
        detail = err_ctx or project_context_service.MINIMUM_CONTEXT_USER_MESSAGE
        if ctx_path_hint:
            detail += f" Arquivo esperado: `{ctx_path_hint.replace('/', os.sep)}`"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    try:
        user_row = chat_service.add_message(body.chat_id, "user", body.content)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    orch = meta_orchestrator_service.run_meta_orchestrator(
        project_slug=slug,
        chat_id=body.chat_id,
        user_message=body.content,
    )

    project_id = int(chat_row["project_id"])
    if orch.run_id:
        run_status = (
            squad_runs.STATUS_AWAITING_HUMAN_APPROVAL if orch.ok else squad_runs.STATUS_FAILED
        )
        create_kwargs: dict = {
            "project_id": project_id,
            "run_id": orch.run_id,
            "run_path": orch.run_path_posix,
            "status": run_status,
            "chat_id": body.chat_id,
            "error_detail": None if orch.ok else orch.error_detail,
        }
        squad_runs.create_squad_run_record(**create_kwargs)

    if orch.ok:
        assistant_body = orch.markdown.strip() + _HUMAN_SQUAD_APPROVAL_NOTE
    else:
        assistant_body = (
            "## Meta-orquestrador — erro\n\n"
            + (orch.error_detail or "Erro desconhecido ao executar o meta-orquestrador.")
        )

    try:
        assistant_row = chat_service.add_message(body.chat_id, "assistant", assistant_body)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    return {
        "user_message": user_row,
        "assistant_message": assistant_row,
        "run_id": orch.run_id,
        "run_path": orch.run_path_posix,
        "status": "success" if orch.ok else "failed",
        "context_loaded": bool(orch.context_loaded),
        "context_evidence_path": orch.context_evidence_path,
    }
