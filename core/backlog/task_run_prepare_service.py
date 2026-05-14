"""Prepara pasta de run + input.md a partir de uma tarefa do Board (sem executar squad)."""

from __future__ import annotations

import shutil
import sqlite3
import uuid
from typing import Any

from core.backlog.backlog_exporter import export_backlog_to_project_file
from core.config import get_repo_root
from core.database.connection import get_connection
from core.database.schema import init_database
from core import squad_runs


def _utc_now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _dash(v: str | None) -> str:
    s = (v or "").strip()
    return s if s else "—"


def _build_input_markdown(
    *,
    task_title: str,
    task_description: str | None,
    project_slug: str,
    epic_title: str | None,
    story_title: str | None,
    task_id: int,
    story_priority: str | None,
    task_status: str,
    assignee_agent: str | None,
) -> str:
    desc = (task_description or "").strip() or "_Sem descrição._"
    epic_line = _dash(epic_title)
    story_line = _dash(story_title)
    prio = _dash(story_priority)
    agent = _dash(assignee_agent)
    return (
        f"# Demanda\n\n{task_title.strip()}\n\n"
        f"## Descrição\n\n{desc}\n\n"
        "## Contexto do Backlog\n\n"
        f"Projeto: {project_slug}\n"
        f"Epic: {epic_line}\n"
        f"Story: {story_line}\n"
        f"Task ID: {task_id}\n"
        f"Prioridade: {prio}\n"
        f"Status atual: {task_status}\n"
        f"Agente sugerido: {agent}\n\n"
        "## Objetivo\n\n"
        "Preparar análise e execução assistida para esta tarefa usando a squad do projeto.\n\n"
        "## Restrições\n\n"
        "- Não aplicar alterações automaticamente sem aprovação humana.\n"
        "- Gerar saída rastreável.\n"
        "- Registrar decisões e evidências.\n"
    )


def prepare_squad_run_from_task(task_id: int) -> dict[str, Any]:
    """
    Cria `runs/<slug>/<run_id>/input.md` na raiz do repo, registro em `squad_runs`,
    atualiza `squad_tasks.run_id` e exporta `backlog.json`.
    Não invoca OpenAI nem `run_squad.py`.
    """
    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT t.*, p.slug AS project_slug
            FROM squad_tasks t
            INNER JOIN squad_projects p ON p.id = t.project_id
            WHERE t.id = ?
            """,
            (task_id,),
        ).fetchone()
        if not row:
            raise ValueError("Tarefa não encontrada.")

        if row["run_id"]:
            raise ValueError(
                "Esta tarefa já possui run associado. Use outra tarefa ou limpe o vínculo no banco."
            )

        project_id = int(row["project_id"])
        slug = str(row["project_slug"]).strip().lower()
        story_id = row["story_id"]
        epic_title: str | None = None
        story_title: str | None = None
        story_priority: str | None = None

        if story_id is not None:
            srow = conn.execute(
                """
                SELECT s.title AS story_title, s.priority AS story_priority, e.title AS epic_title
                FROM squad_stories s
                LEFT JOIN squad_epics e ON e.id = s.epic_id
                WHERE s.id = ? AND s.project_id = ?
                """,
                (story_id, project_id),
            ).fetchone()
            if srow:
                story_title = srow["story_title"]
                story_priority = srow["story_priority"]
                epic_title = srow["epic_title"]
    finally:
        conn.close()

    run_id = f"board-{uuid.uuid4().hex[:16]}"
    run_path_posix = f"runs/{slug}/{run_id}"
    root = get_repo_root()
    run_dir = root / "runs" / slug / run_id
    input_path = run_dir / "input.md"
    md = _build_input_markdown(
        task_title=str(row["title"]),
        task_description=row["description"],
        project_slug=slug,
        epic_title=epic_title,
        story_title=story_title,
        task_id=task_id,
        story_priority=story_priority,
        task_status=str(row["status"]),
        assignee_agent=row["assignee_agent"],
    )

    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        input_path.write_text(md, encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"Não foi possível gravar o diretório do run: {exc}") from exc

    try:
        squad_runs.create_squad_run_record(
            project_id=project_id,
            run_id=run_id,
            run_path=run_path_posix,
            status=squad_runs.STATUS_CREATED,
            task_id=task_id,
            chat_id=None,
            error_detail=None,
        )
        conn = get_connection()
        try:
            now = _utc_now_iso()
            conn.execute(
                "UPDATE squad_tasks SET run_id = ?, updated_at = ? WHERE id = ?",
                (run_id, now, task_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    except Exception:
        if run_dir.is_dir():
            shutil.rmtree(run_dir, ignore_errors=True)
        conn_del = get_connection()
        try:
            conn_del.execute("DELETE FROM squad_runs WHERE run_id = ?", (run_id,))
            conn_del.commit()
        finally:
            conn_del.close()
        raise

    export_backlog_to_project_file(slug)

    conn = get_connection()
    try:
        updated = conn.execute("SELECT * FROM squad_tasks WHERE id = ?", (task_id,)).fetchone()
        assert updated is not None
        task_out = _row_to_dict(updated)
    finally:
        conn.close()

    input_posix = f"{run_path_posix}/input.md"
    return {
        "task": task_out,
        "run_id": run_id,
        "run_path": run_path_posix,
        "input_path": input_posix,
    }
