"""Cadastro e gestão de projetos locais (arquivos + SQLite)."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import get_projects_root
from core.database.connection import get_connection
from core.database.schema import init_database

_DEFAULT_CONTEXT = "# Contexto do projeto\n\n"
_DEFAULT_ROADMAP = "# Roadmap\n\n"
_DEFAULT_DECISIONS = "# Decisões\n\n"
_DEFAULT_BACKLOG: list[Any] = []


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify_project_name(name: str) -> str:
    """Gera slug estável a partir do nome (minúsculas, hífens, ASCII seguro)."""
    raw = (name or "").strip().lower()
    raw = re.sub(r"[^\w\s-]", "", raw, flags=re.UNICODE)
    raw = re.sub(r"[-\s]+", "-", raw, flags=re.UNICODE).strip("-")
    return raw or "project"


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def ensure_squad_layout_for_project(project_path: Path) -> None:
    """Cria `.squad/` e arquivos padrão apenas se ainda não existirem (idempotente)."""
    _ensure_squad_layout(project_path)


def _ensure_squad_layout(project_path: Path) -> None:
    """Cria `.squad/` e arquivos padrão apenas se ainda não existirem."""
    squad = project_path / ".squad"
    subdirs = (squad / "chats", squad / "runs", squad / "outputs")
    for d in subdirs:
        d.mkdir(parents=True, exist_ok=True)

    files_default: dict[Path, str] = {
        squad / "context.md": _DEFAULT_CONTEXT,
        squad / "roadmap.md": _DEFAULT_ROADMAP,
        squad / "decisions.md": _DEFAULT_DECISIONS,
        squad / "backlog.json": json.dumps(_DEFAULT_BACKLOG, ensure_ascii=False, indent=2) + "\n",
    }
    for path, content in files_default.items():
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


def _insert_project(conn: sqlite3.Connection, name: str, slug: str, local_path: Path) -> dict[str, Any]:
    now = _utc_now_iso()
    lp = str(local_path.resolve())
    try:
        cur = conn.execute(
            """
            INSERT INTO squad_projects (name, slug, local_path, status, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            (name.strip(), slug, lp, now, now),
        )
        conn.commit()
        pid = cur.lastrowid
    except sqlite3.IntegrityError as e:
        conn.rollback()
        raise ValueError(f"Projeto já cadastrado ou slug/caminho em conflito: {e}") from e

    row = conn.execute("SELECT * FROM squad_projects WHERE id = ?", (pid,)).fetchone()
    assert row is not None
    return _row_to_dict(row)


def list_projects() -> list[dict[str, Any]]:
    init_database()
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM squad_projects ORDER BY datetime(created_at) ASC, id ASC"
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_project_by_slug(slug: str) -> dict[str, Any] | None:
    init_database()
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM squad_projects WHERE slug = ?", (slug,)).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def register_existing_project(name: str, local_path: str) -> dict[str, Any]:
    """Registra pasta existente, garante `.squad` e persiste no SQLite."""
    init_database()
    path = Path(local_path).expanduser()
    if not path.exists() or not path.is_dir():
        raise ValueError(f"Caminho inválido ou não é diretório: {local_path}")

    resolved = path.resolve()
    slug = slugify_project_name(name)
    _ensure_squad_layout(resolved)

    conn = get_connection()
    try:
        return _insert_project(conn, name, slug, resolved)
    finally:
        conn.close()


def create_project(name: str) -> dict[str, Any]:
    """Cria diretório em PROJECTS_ROOT, layout `.squad` e registro no SQLite."""
    init_database()
    slug = slugify_project_name(name)
    root = get_projects_root()
    project_path = (root / slug).resolve()

    if project_path.exists():
        raise FileExistsError(f"Já existe pasta com slug '{slug}': {project_path}")

    project_path.mkdir(parents=True, exist_ok=False)
    _ensure_squad_layout(project_path)

    conn = get_connection()
    try:
        return _insert_project(conn, name, slug, project_path)
    finally:
        conn.close()
