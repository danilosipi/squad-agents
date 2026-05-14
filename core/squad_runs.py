"""Registro de execuções (squad_runs) no SQLite."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from core.database.connection import get_connection
from core.database.schema import init_database

# Status mínimos (Fase 5.6)
STATUS_CREATED = "created"
STATUS_META_COMPLETED = "meta_completed"
STATUS_AWAITING_HUMAN_APPROVAL = "awaiting_human_approval"
STATUS_RUNNING_SQUAD = "running_squad"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"

_APPROVAL_STATUSES = frozenset({STATUS_META_COMPLETED, STATUS_AWAITING_HUMAN_APPROVAL})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def create_squad_run_record(
    *,
    project_id: int,
    run_id: str,
    run_path: str,
    status: str,
    task_id: int | None = None,
    chat_id: int | None = None,
    error_detail: str | None = None,
) -> dict[str, Any]:
    """Insere linha em squad_runs."""
    init_database()
    now = _utc_now_iso()
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO squad_runs (
                project_id, task_id, run_id, run_path, status,
                created_at, updated_at, chat_id, error_detail
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (project_id, task_id, run_id, run_path, status, now, now, chat_id, error_detail),
        )
        conn.commit()
        rid = cur.lastrowid
        row = conn.execute("SELECT * FROM squad_runs WHERE id = ?", (rid,)).fetchone()
        assert row is not None
        return _row_to_dict(row)
    finally:
        conn.close()


def get_squad_run_by_run_id(run_id: str) -> dict[str, Any] | None:
    """Último registro com `run_id`, com `project_slug` via join."""
    init_database()
    rid = (run_id or "").strip()
    if not rid:
        return None
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT sr.*, p.slug AS project_slug
            FROM squad_runs sr
            INNER JOIN squad_projects p ON p.id = sr.project_id
            WHERE sr.run_id = ?
            ORDER BY sr.id DESC
            LIMIT 1
            """,
            (rid,),
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def get_pending_approval_run_for_chat(chat_id: int) -> dict[str, Any] | None:
    """Run aguardando aprovação explícita para execução da squad completa."""
    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT sr.*, p.slug AS project_slug
            FROM squad_runs sr
            INNER JOIN squad_projects p ON p.id = sr.project_id
            WHERE sr.chat_id = ? AND sr.status IN (?, ?)
            ORDER BY sr.id DESC
            LIMIT 1
            """,
            (chat_id, STATUS_AWAITING_HUMAN_APPROVAL, STATUS_META_COMPLETED),
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def update_squad_run_status(
    *,
    run_id: str,
    status: str,
    error_detail: str | None = None,
) -> int:
    """
    Atualiza todas as linhas com o mesmo `run_id` (normalmente uma).
    Retorna número de linhas afetadas.
    """
    init_database()
    now = _utc_now_iso()
    rid = (run_id or "").strip()
    conn = get_connection()
    try:
        cur = conn.execute(
            """
            UPDATE squad_runs
            SET status = ?, updated_at = ?, error_detail = ?
            WHERE run_id = ?
            """,
            (status, now, error_detail, rid),
        )
        conn.commit()
        return int(cur.rowcount)
    finally:
        conn.close()


def can_execute_full_squad(status: str) -> bool:
    """Indica se o run pode receber execução explícita da squad completa."""
    return (status or "").strip() in _APPROVAL_STATUSES
