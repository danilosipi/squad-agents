"""DDL inicial do SQLite (índice operacional da UX)."""

from __future__ import annotations

import sqlite3

from core.database.connection import get_connection, ensure_database_directory

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS squad_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    local_path TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS squad_chats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES squad_projects(id)
);

CREATE TABLE IF NOT EXISTS squad_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(chat_id) REFERENCES squad_chats(id)
);

CREATE TABLE IF NOT EXISTS squad_epics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'backlog',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES squad_projects(id)
);

CREATE TABLE IF NOT EXISTS squad_stories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    epic_id INTEGER,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'backlog',
    priority TEXT DEFAULT 'medium',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(epic_id) REFERENCES squad_epics(id),
    FOREIGN KEY(project_id) REFERENCES squad_projects(id)
);

CREATE TABLE IF NOT EXISTS squad_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    story_id INTEGER,
    project_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL DEFAULT 'backlog',
    assignee_agent TEXT,
    run_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(story_id) REFERENCES squad_stories(id),
    FOREIGN KEY(project_id) REFERENCES squad_projects(id)
);

CREATE TABLE IF NOT EXISTS squad_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    task_id INTEGER,
    run_id TEXT NOT NULL,
    run_path TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'created',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY(project_id) REFERENCES squad_projects(id),
    FOREIGN KEY(task_id) REFERENCES squad_tasks(id)
);

CREATE TABLE IF NOT EXISTS squad_chat_attachments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    message_id INTEGER,
    project_slug TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(chat_id) REFERENCES squad_chats(id) ON DELETE CASCADE
);
"""


def _existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(r[1]) for r in rows}


def _ensure_squad_runs_migrations(conn: sqlite3.Connection) -> None:
    """Colunas aditivas em `squad_runs` (bases já criadas antes da Fase 5.6)."""
    cols = _existing_columns(conn, "squad_runs")
    if "chat_id" not in cols:
        conn.execute(
            "ALTER TABLE squad_runs ADD COLUMN chat_id INTEGER "
            "REFERENCES squad_chats(id)"
        )
    if "error_detail" not in cols:
        conn.execute("ALTER TABLE squad_runs ADD COLUMN error_detail TEXT")


def init_database() -> None:
    """Cria tabelas se não existirem (idempotente)."""
    ensure_database_directory()
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        _ensure_squad_runs_migrations(conn)
        conn.commit()
    finally:
        conn.close()
