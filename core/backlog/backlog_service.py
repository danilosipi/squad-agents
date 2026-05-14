"""CRUD de backlog (SQLite) com exportação para `.squad/backlog.json`."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from core.backlog.backlog_exporter import export_backlog_to_project_file
from core.database.connection import get_connection
from core.database.schema import init_database


ALLOWED_STATUSES = frozenset(
    {
        "backlog",
        "ready",
        "in_progress",
        "in_review",
        "qa",
        "waiting_human_approval",
        "done",
        "blocked",
    }
)

ALLOWED_STORY_PRIORITIES = frozenset({"low", "medium", "high", "critical"})

ALLOWED_ASSIGNEE_AGENTS = frozenset({"po", "architect", "dev-base", "reviewer", "qa"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _validate_status(status: str) -> None:
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Status inválido: {status!r}. Permitidos: {sorted(ALLOWED_STATUSES)}")


def _validate_priority(priority: str) -> None:
    if priority not in ALLOWED_STORY_PRIORITIES:
        raise ValueError(
            f"Prioridade inválida: {priority!r}. Permitidas: {sorted(ALLOWED_STORY_PRIORITIES)}"
        )


def _validate_agent(agent: str | None) -> None:
    if agent is None or agent == "":
        return
    if agent not in ALLOWED_ASSIGNEE_AGENTS:
        raise ValueError(
            f"Agente inválido: {agent!r}. Permitidos: {sorted(ALLOWED_ASSIGNEE_AGENTS)}"
        )


def _project_id_for_slug(conn: sqlite3.Connection, project_slug: str) -> int:
    row = conn.execute("SELECT id FROM squad_projects WHERE slug = ?", (project_slug,)).fetchone()
    if not row:
        raise ValueError(f"Projeto não encontrado: {project_slug}")
    return int(row["id"])


def _ensure_epic_in_project(conn: sqlite3.Connection, epic_id: int, project_id: int) -> None:
    r = conn.execute(
        "SELECT 1 FROM squad_epics WHERE id = ? AND project_id = ?",
        (epic_id, project_id),
    ).fetchone()
    if not r:
        raise ValueError("Épico inexistente ou não pertence ao projeto")


def _ensure_story_in_project(conn: sqlite3.Connection, story_id: int, project_id: int) -> None:
    r = conn.execute(
        "SELECT 1 FROM squad_stories WHERE id = ? AND project_id = ?",
        (story_id, project_id),
    ).fetchone()
    if not r:
        raise ValueError("História inexistente ou não pertence ao projeto")


def list_epics(project_slug: str) -> list[dict[str, Any]]:
    init_database()
    conn = get_connection()
    try:
        pid = _project_id_for_slug(conn, project_slug)
        rows = conn.execute(
            "SELECT * FROM squad_epics WHERE project_id = ? ORDER BY id ASC",
            (pid,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def create_epic(project_slug: str, title: str, description: str | None = None) -> dict[str, Any]:
    init_database()
    conn = get_connection()
    try:
        pid = _project_id_for_slug(conn, project_slug)
        now = _utc_now_iso()
        cur = conn.execute(
            """
            INSERT INTO squad_epics (project_id, title, description, status, created_at, updated_at)
            VALUES (?, ?, ?, 'backlog', ?, ?)
            """,
            (pid, title.strip(), description, now, now),
        )
        conn.commit()
        eid = cur.lastrowid
        row = conn.execute("SELECT * FROM squad_epics WHERE id = ?", (eid,)).fetchone()
        assert row is not None
        out = _row_to_dict(row)
    finally:
        conn.close()
    export_backlog_to_project_file(project_slug)
    return out


def update_epic_status(epic_id: int, status: str) -> dict[str, Any]:
    _validate_status(status)
    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT e.id, p.slug AS project_slug
            FROM squad_epics e
            JOIN squad_projects p ON p.id = e.project_id
            WHERE e.id = ?
            """,
            (epic_id,),
        ).fetchone()
        if not row:
            raise ValueError("Épico não encontrado")
        slug = str(row["project_slug"])
        now = _utc_now_iso()
        conn.execute(
            "UPDATE squad_epics SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, epic_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM squad_epics WHERE id = ?", (epic_id,)).fetchone()
        assert updated is not None
        out = _row_to_dict(updated)
    finally:
        conn.close()
    export_backlog_to_project_file(slug)
    return out


def list_stories(project_slug: str) -> list[dict[str, Any]]:
    init_database()
    conn = get_connection()
    try:
        pid = _project_id_for_slug(conn, project_slug)
        rows = conn.execute(
            "SELECT * FROM squad_stories WHERE project_id = ? ORDER BY id ASC",
            (pid,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def create_story(
    project_slug: str,
    title: str,
    description: str | None = None,
    epic_id: int | None = None,
    priority: str = "medium",
) -> dict[str, Any]:
    _validate_priority(priority)
    init_database()
    conn = get_connection()
    try:
        pid = _project_id_for_slug(conn, project_slug)
        if epic_id is not None:
            _ensure_epic_in_project(conn, epic_id, pid)
        now = _utc_now_iso()
        cur = conn.execute(
            """
            INSERT INTO squad_stories
            (epic_id, project_id, title, description, status, priority, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'backlog', ?, ?, ?)
            """,
            (epic_id, pid, title.strip(), description, priority, now, now),
        )
        conn.commit()
        sid = cur.lastrowid
        row = conn.execute("SELECT * FROM squad_stories WHERE id = ?", (sid,)).fetchone()
        assert row is not None
        out = _row_to_dict(row)
    finally:
        conn.close()
    export_backlog_to_project_file(project_slug)
    return out


def update_story_status(story_id: int, status: str) -> dict[str, Any]:
    _validate_status(status)
    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT s.id, p.slug AS project_slug
            FROM squad_stories s
            JOIN squad_projects p ON p.id = s.project_id
            WHERE s.id = ?
            """,
            (story_id,),
        ).fetchone()
        if not row:
            raise ValueError("História não encontrada")
        slug = str(row["project_slug"])
        now = _utc_now_iso()
        conn.execute(
            "UPDATE squad_stories SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, story_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM squad_stories WHERE id = ?", (story_id,)).fetchone()
        assert updated is not None
        out = _row_to_dict(updated)
    finally:
        conn.close()
    export_backlog_to_project_file(slug)
    return out


def list_tasks(project_slug: str) -> list[dict[str, Any]]:
    init_database()
    conn = get_connection()
    try:
        pid = _project_id_for_slug(conn, project_slug)
        rows = conn.execute(
            """
            SELECT t.id, t.story_id, t.project_id, t.title, t.description, t.status,
                   t.assignee_agent, t.run_id, t.created_at, t.updated_at,
                   (SELECT sr.status FROM squad_runs sr
                    WHERE sr.run_id = t.run_id ORDER BY sr.id DESC LIMIT 1) AS run_status
            FROM squad_tasks t
            WHERE t.project_id = ?
            ORDER BY t.id ASC
            """,
            (pid,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def create_task(
    project_slug: str,
    title: str,
    description: str | None = None,
    story_id: int | None = None,
    assignee_agent: str | None = None,
) -> dict[str, Any]:
    _validate_agent(assignee_agent)
    init_database()
    conn = get_connection()
    try:
        pid = _project_id_for_slug(conn, project_slug)
        if story_id is not None:
            _ensure_story_in_project(conn, story_id, pid)
        now = _utc_now_iso()
        agent = assignee_agent if assignee_agent else None
        cur = conn.execute(
            """
            INSERT INTO squad_tasks
            (story_id, project_id, title, description, status, assignee_agent, run_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'backlog', ?, NULL, ?, ?)
            """,
            (story_id, pid, title.strip(), description, agent, now, now),
        )
        conn.commit()
        tid = cur.lastrowid
        row = conn.execute("SELECT * FROM squad_tasks WHERE id = ?", (tid,)).fetchone()
        assert row is not None
        out = _row_to_dict(row)
    finally:
        conn.close()
    export_backlog_to_project_file(project_slug)
    return out


def update_task_status(task_id: int, status: str) -> dict[str, Any]:
    _validate_status(status)
    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT t.id, p.slug AS project_slug
            FROM squad_tasks t
            JOIN squad_projects p ON p.id = t.project_id
            WHERE t.id = ?
            """,
            (task_id,),
        ).fetchone()
        if not row:
            raise ValueError("Tarefa não encontrada")
        slug = str(row["project_slug"])
        now = _utc_now_iso()
        conn.execute(
            "UPDATE squad_tasks SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, task_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM squad_tasks WHERE id = ?", (task_id,)).fetchone()
        assert updated is not None
        out = _row_to_dict(updated)
    finally:
        conn.close()
    export_backlog_to_project_file(slug)
    return out


def assign_task_to_agent(task_id: int, assignee_agent: str | None) -> dict[str, Any]:
    _validate_agent(assignee_agent)
    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT t.id, p.slug AS project_slug
            FROM squad_tasks t
            JOIN squad_projects p ON p.id = t.project_id
            WHERE t.id = ?
            """,
            (task_id,),
        ).fetchone()
        if not row:
            raise ValueError("Tarefa não encontrada")
        slug = str(row["project_slug"])
        now = _utc_now_iso()
        agent = assignee_agent if assignee_agent else None
        conn.execute(
            "UPDATE squad_tasks SET assignee_agent = ?, updated_at = ? WHERE id = ?",
            (agent, now, task_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM squad_tasks WHERE id = ?", (task_id,)).fetchone()
        assert updated is not None
        out = _row_to_dict(updated)
    finally:
        conn.close()
    export_backlog_to_project_file(slug)
    return out
