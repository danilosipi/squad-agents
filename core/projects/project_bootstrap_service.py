"""Bootstrap de `.squad/` no disco do projeto cliente (sem exigir edição manual)."""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.chats import chat_service
from core.projects import project_context_service, project_service

_SLUG_SAFE = re.compile(r"[^a-z0-9-]+")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _empty_backlog_payload(project_slug: str) -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": _utc_now_iso(),
        "project_slug": project_slug,
        "epics": [],
        "stories": [],
        "tasks": [],
    }


def build_initial_context_markdown(
    *,
    project_name: str,
    project_slug: str,
    local_path: str,
    chat_notes: str | None = None,
) -> str:
    """Template mínimo com seções obrigatórias (≥ 80 caracteres úteis)."""
    notes = (chat_notes or "").strip()
    if not notes:
        notes = "_Nada registado ainda no chat._"
    return f"""# Contexto do Projeto

## Identificação
- Nome: {project_name}
- Slug: {project_slug}
- Caminho local: `{local_path}`

## Objetivo do Projeto
_A definir com o utilizador._

## Problema que o projeto resolve
_A definir com o utilizador._

## Público/utilizadores
_A definir com o utilizador._

## Escopo inicial
_A definir com o utilizador._

## Restrições
_A definir com o utilizador._

## Decisões registadas
- Contexto inicial criado automaticamente pelo squad-agentes.

## Pendências de contexto
- Detalhar objetivo, problema, público, escopo e restrições com precisão.

## Notas do chat (bootstrap)
{notes}

## Estado
Contexto gerado/refinado pelo squad-agentes — onboarding em curso.
"""


def project_bootstrap_status(project_slug: str) -> dict[str, Any]:
    """
    Estado de onboarding no disco do projeto.

    `block_reason` quando o cadastro não permite escrever ficheiros (ex.: sem `local_path`).
    """
    slug = (project_slug or "").strip().lower()
    base = project_context_service.get_project_context_paths(slug)
    if not base.get("ok"):
        return {
            "project_slug": slug,
            "ok": False,
            "block_reason": base.get("error") or "Projeto inválido.",
            "local_path_resolved": (base.get("local_path_resolved") or "").strip(),
            "has_squad_dir": False,
            "has_context_md": False,
            "has_backlog_json": False,
            "context_meets_minimum": False,
            "needs_bootstrap": True,
            "ready_for_meta_orchestrator": False,
            "expected_context_path": (base.get("expected_context_path") or "").strip(),
        }

    root = Path(base["local_path_resolved"])
    squad = root / ".squad"
    ctx_path = squad / "context.md"
    bl_path = squad / "backlog.json"
    has_squad = squad.is_dir()
    has_ctx = ctx_path.is_file()
    has_bl = bl_path.is_file()
    ctx_ok, _err, _p = project_context_service.minimum_project_context_status(slug)
    needs = (not has_squad) or (not has_ctx) or (not has_bl) or (not ctx_ok)
    row = project_service.get_project_by_slug(slug) or {}
    name = str(row.get("name") or slug)
    ready_meta = (slug == "cap") and ctx_ok and has_bl
    return {
        "project_slug": slug,
        "ok": True,
        "block_reason": None,
        "local_path_resolved": str(root),
        "has_squad_dir": has_squad,
        "has_context_md": has_ctx,
        "has_backlog_json": has_bl,
        "context_meets_minimum": bool(ctx_ok),
        "needs_bootstrap": bool(needs),
        "ready_for_meta_orchestrator": ready_meta,
        "expected_context_path": str(ctx_path),
    }


def ensure_minimal_squad_artifacts(project_slug: str) -> dict[str, Any]:
    """
    Cria `.squad/`, `context.md` e `backlog.json` apenas quando faltam (idempotente).
    """
    slug = (project_slug or "").strip().lower()
    st = project_bootstrap_status(slug)
    if not st.get("ok"):
        raise ValueError(st.get("block_reason") or "Projeto inválido.")
    root = Path(st["local_path_resolved"])
    row = project_service.get_project_by_slug(slug)
    if not row:
        raise ValueError(f"Projeto não encontrado: {slug!r}")
    name = str(row.get("name") or slug)
    squad = root / ".squad"
    prompts = squad / "prompts"
    created: list[str] = []

    squad.mkdir(parents=True, exist_ok=True)
    prompts.mkdir(parents=True, exist_ok=True)
    for sub in (squad / "chats", squad / "runs", squad / "outputs"):
        sub.mkdir(parents=True, exist_ok=True)

    ctx_path = squad / "context.md"
    if not ctx_path.is_file():
        body = build_initial_context_markdown(
            project_name=name,
            project_slug=slug,
            local_path=str(root),
        )
        ctx_path.write_text(body, encoding="utf-8")
        created.append(str(ctx_path))

    bl_path = squad / "backlog.json"
    if not bl_path.is_file():
        bl_path.write_text(
            json.dumps(_empty_backlog_payload(slug), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        created.append(str(bl_path))

    return {
        "project_slug": slug,
        "local_path_resolved": str(root),
        "created_paths": created,
        "bootstrap_status": project_bootstrap_status(slug),
    }


def refine_context_markdown_from_chat(
    project_slug: str,
    chat_id: int,
    *,
    overwrite: bool = True,
) -> dict[str, Any]:
    """Gera ou atualiza `.squad/context.md` a partir do histórico do chat."""
    slug = (project_slug or "").strip().lower()
    st = project_bootstrap_status(slug)
    if not st.get("ok"):
        raise ValueError(st.get("block_reason") or "Projeto inválido.")

    chat_row = chat_service.get_chat_with_project(chat_id)
    if not chat_row:
        raise ValueError(f"Chat não encontrado: id={chat_id}")
    if (chat_row.get("project_slug") or "").strip().lower() != slug:
        raise ValueError("O chat não pertence a este projeto.")

    row = project_service.get_project_by_slug(slug)
    if not row:
        raise ValueError(f"Projeto não encontrado: {slug!r}")
    name = str(row.get("name") or slug)
    root = Path(st["local_path_resolved"])
    squad = root / ".squad"
    squad.mkdir(parents=True, exist_ok=True)

    msgs = chat_service.list_messages(chat_id)
    lines: list[str] = []
    for m in msgs:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        lines.append(f"**{role}**: {content}")
    transcript = "\n\n".join(lines).strip() or "_Sem mensagens._"

    from core.chats import chat_attachment_service

    att_names = chat_attachment_service.list_attachment_file_names(chat_id)
    if att_names:
        transcript += (
            "\n\n### Evidências visuais (anexos do chat)\n"
            + "\n".join(f"- {n}" for n in att_names)
            + "\n\n_Notas: ficheiros em `.squad/attachments/`; leitura multimodal automática pode ser "
            "uma evolução futura._\n"
        )

    body = build_initial_context_markdown(
        project_name=name,
        project_slug=slug,
        local_path=str(root),
        chat_notes=transcript,
    )
    path = squad / "context.md"
    if path.is_file() and not overwrite:
        raise ValueError("context.md já existe; use overwrite=true para substituir.")
    path.write_text(body, encoding="utf-8")

    bl_path = squad / "backlog.json"
    if not bl_path.is_file():
        bl_path.write_text(
            json.dumps(_empty_backlog_payload(slug), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return {
        "project_slug": slug,
        "context_path": str(path),
        "bootstrap_status": project_bootstrap_status(slug),
    }


def save_important_prompt_file(
    project_slug: str,
    *,
    title_slug: str,
    body: str,
) -> dict[str, Any]:
    """Grava `.squad/prompts/YYYYMMDD-HHMMSS-<slug>.md` no projeto cliente."""
    slug = (project_slug or "").strip().lower()
    st = project_bootstrap_status(slug)
    if not st.get("ok"):
        raise ValueError(st.get("block_reason") or "Projeto inválido.")
    root = Path(st["local_path_resolved"])
    squad = root / ".squad"
    prompts = squad / "prompts"
    squad.mkdir(parents=True, exist_ok=True)
    prompts.mkdir(parents=True, exist_ok=True)

    raw = (title_slug or "prompt").strip().lower().replace(" ", "-")
    safe = _SLUG_SAFE.sub("-", raw).strip("-") or "prompt"
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = f"{stamp}-{safe}.md"
    path = prompts / fname
    header = f"# Prompt importante\n\n**Projeto:** {slug}\n**Guardado em:** {_utc_now_iso()}\n\n---\n\n"
    path.write_text(header + (body or "").strip() + "\n", encoding="utf-8")
    return {"path": str(path), "relative": f".squad/prompts/{fname}"}


def expected_context_path_display(project_slug: str) -> str:
    st = project_bootstrap_status(project_slug)
    p = (st.get("expected_context_path") or "").strip()
    return p.replace("/", os.sep) if p else ""
