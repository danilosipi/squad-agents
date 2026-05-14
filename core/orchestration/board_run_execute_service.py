"""Execução explícita de runs preparadas pelo Board (sem chat_id)."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.backlog import backlog_service
from core.config import get_repo_root
from core.orchestration.squad_full_run_service import FullSquadRunResult, run_full_squad
from core import squad_runs


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_board_run_row(row: dict[str, Any]) -> bool:
    rid = str(row.get("run_id") or "").strip()
    if not rid.startswith("board-"):
        return False
    if row.get("task_id") is None:
        return False
    if row.get("chat_id") is not None:
        return False
    return True


def _write_execution_log(
    run_dir: Path,
    *,
    slug: str,
    rid: str,
    result: FullSquadRunResult,
    extra: str | None,
) -> str:
    """Grava `execution.log` na pasta da run; retorna caminho relativo POSIX."""
    lines = [
        f"# execution.log (Board run)",
        f"timestamp_utc: {_utc_stamp()}",
        f"project_slug: {slug}",
        f"run_id: {rid}",
        f"ok: {result.ok}",
        f"exit_code: {result.exit_code}",
    ]
    if extra:
        lines.append(f"error_detail: {extra}")
    lines.extend(
        [
            "",
            "--- stdout ---",
            result.stdout.strip() if result.stdout else "(vazio)",
            "",
            "--- stderr ---",
            result.stderr.strip() if result.stderr else "(vazio)",
        ]
    )
    path = run_dir / "execution.log"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return f"runs/{slug}/{rid}/execution.log"


def _final_path_posix(slug: str, rid: str) -> str:
    return f"runs/{slug}/{rid}/final.md"


def _fetch_task_with_run_status(task_id: int) -> dict[str, Any]:
    from core.database.connection import get_connection
    from core.database.schema import init_database

    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT t.*,
              (SELECT sr.status FROM squad_runs sr
               WHERE sr.run_id = t.run_id ORDER BY sr.id DESC LIMIT 1) AS run_status
            FROM squad_tasks t
            WHERE t.id = ?
            """,
            (task_id,),
        ).fetchone()
        if not row:
            return {}
        return {k: row[k] for k in row.keys()}
    finally:
        conn.close()


def execute_prepared_board_run(run_id: str) -> dict[str, Any]:
    """
    Executa squad completa para uma run `board-*` com `task_id` e sem `chat_id`.
    Atualiza `squad_runs`, grava `execution.log`, ajusta status da tarefa e exporta backlog.
    """
    rid = (run_id or "").strip()
    if not rid:
        raise ValueError("run_id inválido.")

    row = squad_runs.get_squad_run_by_run_id(rid)
    if not row:
        raise ValueError("Run não encontrado.")

    if not _is_board_run_row(row):
        raise ValueError(
            "Run não é executável por este fluxo (esperado: run_id board-*, com task_id e sem chat)."
        )

    st = (row.get("status") or "").strip()
    if st == squad_runs.STATUS_COMPLETED:
        raise ValueError("Run já foi concluído e não pode ser reexecutado por este endpoint.")
    if st == squad_runs.STATUS_RUNNING_SQUAD:
        raise ValueError("Run já está em execução (squad). Aguarde o término.")
    if not squad_runs.can_execute_board_run(st):
        raise ValueError(
            f"Execução não permitida para o status atual da run: {st!r}. "
            f"Permitidos: {sorted(squad_runs.BOARD_EXECUTABLE_STATUSES)}."
        )

    slug = str(row.get("project_slug") or "").strip().lower()
    task_id = int(row["task_id"])

    root = get_repo_root()
    run_dir = root / "runs" / slug / rid
    input_path = run_dir / "input.md"
    if not input_path.is_file():
        raise ValueError(f"Arquivo input.md não encontrado em: {input_path}")

    if not os.getenv("OPENAI_API_KEY", "").strip():
        raise ValueError("Configure OPENAI_API_KEY antes de executar a squad.")

    squad_runs.update_squad_run_status(
        run_id=rid,
        status=squad_runs.STATUS_RUNNING_SQUAD,
        error_detail=None,
    )

    result = run_full_squad(project_slug=slug, run_id=rid)
    err = result.error_detail

    _write_execution_log(run_dir, slug=slug, rid=rid, result=result, extra=err)

    final_rel = _final_path_posix(slug, rid)
    log_rel = f"runs/{slug}/{rid}/execution.log"

    if result.ok and result.final_markdown:
        squad_runs.update_squad_run_status(run_id=rid, status=squad_runs.STATUS_COMPLETED, error_detail=None)
        backlog_service.update_task_status(task_id, "in_review")
        task_out = _fetch_task_with_run_status(task_id)
        return {
            "status": "completed",
            "run_id": rid,
            "final_path": final_rel,
            "execution_log_path": log_rel,
            "task": task_out,
            "error_detail": None,
        }

    squad_runs.update_squad_run_status(
        run_id=rid,
        status=squad_runs.STATUS_FAILED,
        error_detail=err or "Falha na execução da squad.",
    )
    backlog_service.update_task_status(task_id, "blocked")
    task_out = _fetch_task_with_run_status(task_id)
    return {
        "status": "failed",
        "run_id": rid,
        "final_path": final_rel,
        "execution_log_path": log_rel,
        "task": task_out,
        "error_detail": err or "Falha na execução da squad.",
    }
