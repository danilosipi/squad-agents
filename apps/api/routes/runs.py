"""Rotas REST para execução da squad completa (após aprovação humana)."""

from __future__ import annotations

import os

from fastapi import APIRouter, Body, HTTPException, status

from apps.api.schemas.runs import ExecuteSquadRequest, ExecuteSquadResponse
from core.chats import chat_service
from core.orchestration import squad_full_run_service
from core.projects import project_context_service
from core import squad_runs

router = APIRouter()


def _final_path_posix(project_slug: str, run_id: str) -> str:
    slug = (project_slug or "").strip().lower()
    return f"runs/{slug}/{run_id}/final.md"


@router.post(
    "/{run_id}/execute-squad",
    response_model=ExecuteSquadResponse,
    status_code=status.HTTP_200_OK,
)
def execute_squad(
    run_id: str,
    body: ExecuteSquadRequest | None = Body(default=None),
) -> dict:
    req = body if body is not None else ExecuteSquadRequest()
    rid = (run_id or "").strip()
    if not rid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="run_id inválido.")

    run_row = squad_runs.get_squad_run_by_run_id(rid)
    if not run_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run não encontrado.")

    st = (run_row.get("status") or "").strip()
    if st == squad_runs.STATUS_COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este run já foi concluído.",
        )
    if st == squad_runs.STATUS_RUNNING_SQUAD:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este run já está em execução (squad completa).",
        )
    if not squad_runs.can_execute_full_squad(st):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Execução não permitida: o run precisa estar em "
                f"'{squad_runs.STATUS_AWAITING_HUMAN_APPROVAL}' ou "
                f"'{squad_runs.STATUS_META_COMPLETED}'."
            ),
        )

    slug = (run_row.get("project_slug") or "").strip().lower()
    if slug != "cap":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Projeto ainda não suportado para execução da squad completa.",
        )

    chat_id_resolved = req.chat_id
    if chat_id_resolved is None:
        stored = run_row.get("chat_id")
        chat_id_resolved = int(stored) if stored is not None else None
    if chat_id_resolved is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe chat_id no corpo da requisição (run sem chat associado).",
        )

    stored_chat = run_row.get("chat_id")
    if stored_chat is not None and int(stored_chat) != int(chat_id_resolved):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="chat_id não corresponde ao run registrado.",
        )

    chat_row = chat_service.get_chat_with_project(int(chat_id_resolved))
    if not chat_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat não encontrado.")
    if int(chat_row["project_id"]) != int(run_row["project_id"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat não pertence ao mesmo projeto do run.",
        )

    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Configure OPENAI_API_KEY antes de executar a squad completa.",
        )

    final_rel = _final_path_posix(slug, rid)

    ok_ctx, err_ctx, ev_rel = project_context_service.ensure_run_project_context_evidence(
        project_slug=slug,
        run_id=rid,
    )
    if not ok_ctx:
        path_disp = project_context_service.expected_context_markdown_path_display(slug)
        assistant_body = (
            "## Squad bloqueada — contexto do projeto\n\n"
            + (err_ctx or project_context_service.MINIMUM_CONTEXT_USER_MESSAGE)
            + f"\n\nArquivo esperado:\n\n`{path_disp}`\n"
        )
        assistant_row = chat_service.add_message(int(chat_id_resolved), "assistant", assistant_body)
        return {
            "status": "blocked",
            "run_id": rid,
            "final_path": final_rel,
            "assistant_message": assistant_row,
            "context_loaded": False,
            "context_evidence_path": None,
        }

    squad_runs.update_squad_run_status(
        run_id=rid,
        status=squad_runs.STATUS_RUNNING_SQUAD,
        error_detail=None,
    )

    result = squad_full_run_service.run_full_squad(project_slug=slug, run_id=rid)

    if result.ok and result.final_markdown:
        squad_runs.update_squad_run_status(run_id=rid, status=squad_runs.STATUS_COMPLETED, error_detail=None)
        intro = "## Resultado da squad completa\n\n_Execução assistida (PO → Architect → Dev → Reviewer → QA)._\n\n"
        assistant_body = intro + result.final_markdown.strip()
        assistant_row = chat_service.add_message(int(chat_id_resolved), "assistant", assistant_body)
        return {
            "status": "completed",
            "run_id": rid,
            "final_path": final_rel,
            "assistant_message": assistant_row,
            "context_loaded": True,
            "context_evidence_path": ev_rel,
        }

    err = result.error_detail or "Falha desconhecida na execução da squad completa."
    squad_runs.update_squad_run_status(run_id=rid, status=squad_runs.STATUS_FAILED, error_detail=err)
    assistant_body = (
        "## Squad completa — erro\n\n"
        + err
        + ("\n\n### final.md (parcial)\n\n" + result.final_markdown.strip() if result.final_markdown else "")
    )
    assistant_row = chat_service.add_message(int(chat_id_resolved), "assistant", assistant_body)
    return {
        "status": "failed",
        "run_id": rid,
        "final_path": final_rel,
        "assistant_message": assistant_row,
        "context_loaded": True,
        "context_evidence_path": ev_rel,
    }
