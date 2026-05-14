"""Rotas REST de chats e mensagens."""

from __future__ import annotations

import os

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from apps.api.schemas.chats import (
    AddMessageRequest,
    ChatAttachmentResponse,
    ChatResponse,
    CreateChatRequest,
    MessageResponse,
    MetaOrchestratorMessageRequest,
    MetaOrchestratorMessageResponse,
    PendingSquadRunResponse,
    RenameChatRequest,
    SavePromptRequest,
)
from core.chats import chat_attachment_service, chat_service
from core.orchestration import bootstrap_chat_service, meta_orchestrator_service
from core.projects import project_bootstrap_service, project_context_service, project_service
from core import squad_runs

router = APIRouter()

_HUMAN_SQUAD_APPROVAL_NOTE = (
    "\n\n---\n\n### Aprovação humana necessária\n\n"
    "O plano acima foi gerado pelo meta-orquestrador. Para executar a **squad completa** "
    "(PO → Arquiteto → Dev Base → Reviewer → QA), confirme na interface clicando em "
    "**Executar squad**.\n\n"
    "_Nenhuma execução adicional ocorre sem essa confirmação explícita._"
)


@router.get("/attachments/{attachment_id}")
def download_chat_attachment(attachment_id: int) -> FileResponse:
    """Devolve o ficheiro do anexo (preview / descarga)."""
    row = chat_attachment_service.get_attachment_row(attachment_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anexo não encontrado.")
    try:
        path = chat_attachment_service.resolve_attachment_path(row)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    if not path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ficheiro do anexo não está disponível no disco.",
        )
    return FileResponse(
        str(path),
        media_type=str(row.get("mime_type") or "application/octet-stream"),
        filename=str(row.get("file_name") or path.name),
    )


@router.get("/{chat_id}/attachments", response_model=list[ChatAttachmentResponse])
def list_chat_attachments(chat_id: int) -> list[dict]:
    try:
        return chat_attachment_service.list_attachments(chat_id)
    except ValueError as e:
        msg = str(e)
        code = (
            status.HTTP_404_NOT_FOUND if "não encontrado" in msg else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=msg) from e


@router.post(
    "/{chat_id}/attachments",
    response_model=ChatAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_chat_attachment(chat_id: int, file: UploadFile = File(...)) -> dict:
    try:
        return chat_attachment_service.save_image_attachment(
            chat_id=chat_id,
            original_filename=file.filename or "image",
            file_obj=file.file,
            content_type=file.content_type,
        )
    except ValueError as e:
        msg = str(e)
        code = (
            status.HTTP_404_NOT_FOUND if "não encontrado" in msg else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=msg) from e


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


@router.patch("/{chat_id}", response_model=ChatResponse)
def rename_chat(chat_id: int, body: RenameChatRequest) -> dict:
    try:
        return chat_service.update_chat_title(chat_id, body.title)
    except ValueError as e:
        msg = str(e)
        code = status.HTTP_404_NOT_FOUND if "não encontrado" in msg else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=msg) from e


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_chat(chat_id: int) -> None:
    try:
        chat_service.delete_chat(chat_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/{chat_id}/save-prompt", status_code=status.HTTP_201_CREATED)
def save_important_prompt(chat_id: int, body: SavePromptRequest) -> dict:
    row = chat_service.get_chat_with_project(chat_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat não encontrado.")
    slug = (row.get("project_slug") or "").strip().lower()
    try:
        return project_bootstrap_service.save_important_prompt_file(
            slug,
            title_slug=body.title_slug,
            body=body.content,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e


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
    bst = project_bootstrap_service.project_bootstrap_status(slug)
    if not bst.get("ok"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=bst.get("block_reason") or "Projeto inválido para onboarding.",
        )

    if bst.get("needs_bootstrap"):
        try:
            user_row = chat_service.add_message(body.chat_id, "user", body.content)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

        proj = project_service.get_project_by_slug(slug) or {}
        msgs = chat_service.list_messages(body.chat_id)
        assistant_text = bootstrap_chat_service.generate_bootstrap_assistant_reply(
            project_name=str(proj.get("name") or slug),
            project_slug=slug,
            local_path=str(proj.get("local_path") or bst.get("local_path_resolved") or ""),
            messages=msgs,
            latest_user_message=body.content,
            chat_id=body.chat_id,
        )
        try:
            assistant_row = chat_service.add_message(body.chat_id, "assistant", assistant_text)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

        fresh = project_bootstrap_service.project_bootstrap_status(slug)
        return {
            "user_message": user_row,
            "assistant_message": assistant_row,
            "run_id": "",
            "run_path": "",
            "status": "bootstrap",
            "context_loaded": False,
            "context_evidence_path": None,
            "mode": "bootstrap_onboarding",
            "bootstrap_status": fresh,
        }

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
        "mode": "meta_orchestrator",
        "bootstrap_status": None,
    }
