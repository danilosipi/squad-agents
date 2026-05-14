"""Exporta o backlog do SQLite para `.squad/backlog.json` do projeto."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.database.connection import get_connection
from core.database.schema import init_database
from core.projects import project_service


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def export_backlog_to_project_file(project_slug: str) -> Path:
    """Persiste épicos, histórias e tarefas em `<local_path>/.squad/backlog.json`."""
    init_database()
    proj = project_service.get_project_by_slug(project_slug)
    if not proj:
        raise ValueError(f"Projeto não encontrado: {project_slug}")

    project_id = int(proj["id"])
    base = Path(proj["local_path"]).resolve()
    squad = base / ".squad"
    squad.mkdir(parents=True, exist_ok=True)
    out_path = squad / "backlog.json"

    conn = get_connection()
    try:
        epics = [
            _row_to_dict(r)
            for r in conn.execute(
                "SELECT * FROM squad_epics WHERE project_id = ? ORDER BY id ASC",
                (project_id,),
            ).fetchall()
        ]
        stories = [
            _row_to_dict(r)
            for r in conn.execute(
                "SELECT * FROM squad_stories WHERE project_id = ? ORDER BY id ASC",
                (project_id,),
            ).fetchall()
        ]
        tasks = [
            _row_to_dict(r)
            for r in conn.execute(
                "SELECT * FROM squad_tasks WHERE project_id = ? ORDER BY id ASC",
                (project_id,),
            ).fetchall()
        ]
    finally:
        conn.close()

    payload = {
        "version": 1,
        "updated_at": _utc_now_iso(),
        "project_slug": project_slug,
        "epics": epics,
        "stories": stories,
        "tasks": tasks,
    }
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out_path
