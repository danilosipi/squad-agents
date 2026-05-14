"""Persistência de chats e mensagens no SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from core.database.connection import get_connection
from core.database.schema import init_database
from core.projects import project_service

_ALLOWED_ROLES = frozenset({"user", "assistant", "system", "agent"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _get_project_or_raise(project_slug: str) -> dict[str, Any]:
    p = project_service.get_project_by_slug(project_slug)
    if not p:
        raise ValueError(f"Projeto não encontrado: {project_slug!r}")
    return p


def list_chats(project_slug: str) -> list[dict[str, Any]]:
    init_database()
    project = _get_project_or_raise(project_slug)
    pid = int(project["id"])
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT * FROM squad_chats
            WHERE project_id = ?
            ORDER BY datetime(created_at) ASC, id ASC
            """,
            (pid,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def create_chat(project_slug: str, title: str) -> dict[str, Any]:
    init_database()
    project = _get_project_or_raise(project_slug)
    pid = int(project["id"])
    now = _utc_now_iso()
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO squad_chats (project_id, title, status, created_at, updated_at)
            VALUES (?, ?, 'active', ?, ?)
            """,
            (pid, title.strip(), now, now),
        )
        conn.commit()
        cid = cur.lastrowid
        row = conn.execute("SELECT * FROM squad_chats WHERE id = ?", (cid,)).fetchone()
        assert row is not None
        return _row_to_dict(row)
    finally:
        conn.close()


def _chat_exists(conn: sqlite3.Connection, chat_id: int) -> bool:
    r = conn.execute("SELECT 1 FROM squad_chats WHERE id = ?", (chat_id,)).fetchone()
    return r is not None


def get_chat_with_project(chat_id: int) -> dict[str, Any] | None:
    """Retorna o chat com `project_slug` e `project_local_path` (join em squad_projects)."""
    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT c.*, p.slug AS project_slug, p.local_path AS project_local_path
            FROM squad_chats c
            INNER JOIN squad_projects p ON p.id = c.project_id
            WHERE c.id = ?
            """,
            (chat_id,),
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def list_messages(chat_id: int) -> list[dict[str, Any]]:
    init_database()
    conn = get_connection()
    try:
        if not _chat_exists(conn, chat_id):
            raise ValueError(f"Chat não encontrado: id={chat_id}")
        rows = conn.execute(
            """
            SELECT * FROM squad_messages
            WHERE chat_id = ?
            ORDER BY datetime(created_at) ASC, id ASC
            """,
            (chat_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def add_message(chat_id: int, role: str, content: str) -> dict[str, Any]:
    init_database()
    rnorm = (role or "").strip().lower()
    if rnorm not in _ALLOWED_ROLES:
        raise ValueError(
            f"role inválido: {role!r}; permitidos: {', '.join(sorted(_ALLOWED_ROLES))}"
        )
    now = _utc_now_iso()
    conn = get_connection()
    try:
        if not _chat_exists(conn, chat_id):
            raise ValueError(f"Chat não encontrado: id={chat_id}")
        cur = conn.execute(
            """
            INSERT INTO squad_messages (chat_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (chat_id, rnorm, content, now),
        )
        conn.execute(
            "UPDATE squad_chats SET updated_at = ? WHERE id = ?",
            (now, chat_id),
        )
        conn.commit()
        mid = cur.lastrowid
        row = conn.execute("SELECT * FROM squad_messages WHERE id = ?", (mid,)).fetchone()
        assert row is not None
        return _row_to_dict(row)
    finally:
        conn.close()
