"""Anexos de imagem do chat: disco em `.squad/attachments/` + registro SQLite."""

from __future__ import annotations

import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, BinaryIO

from core.database.connection import get_connection
from core.database.schema import init_database
from core.chats import chat_service

_MAX_BYTES = 5 * 1024 * 1024
_ALLOWED_EXT = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_EXT_TO_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}

_SLUG_SAFE = re.compile(r"[^a-z0-9._-]+", re.IGNORECASE)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _mime_matches(ext: str, content_type: str | None) -> bool:
    expected = _EXT_TO_MIME[ext]
    if not content_type:
        return True
    ct = content_type.split(";")[0].strip().lower()
    if ct in ("application/octet-stream", "binary/octet-stream"):
        return True
    if ct == "image/jpg":
        ct = "image/jpeg"
    return ct == expected


def _validate_magic(ext: str, head: bytes) -> bool:
    if ext == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if ext in (".jpg", ".jpeg"):
        return len(head) >= 3 and head[:3] == b"\xff\xd8\xff"
    if ext == ".webp":
        return len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    return False


def _project_root_for_chat(chat_id: int) -> tuple[dict[str, Any], Path]:
    row = chat_service.get_chat_with_project(chat_id)
    if not row:
        raise ValueError("Chat não encontrado.")
    lp = (row.get("project_local_path") or "").strip()
    if not lp:
        raise ValueError("Projeto sem local_path no cadastro.")
    root = Path(lp).expanduser()
    try:
        root = root.resolve()
    except OSError as exc:
        raise ValueError(f"Caminho do projeto inválido: {exc}") from exc
    if not root.is_dir():
        raise ValueError("Pasta do projeto inexistente ou inacessível.")
    return row, root


def _attachments_dir(root: Path, chat_id: int) -> Path:
    return root / ".squad" / "attachments" / "chats" / str(chat_id)


def _relative_db_path(chat_id: int, filename: str) -> str:
    return f".squad/attachments/chats/{chat_id}/{filename}".replace("\\", "/")


def _resolve_stored_file(project_root: Path, rel_posix: str) -> Path:
    rel = (rel_posix or "").strip().replace("\\", "/")
    if not rel or rel.startswith("..") or "/../" in rel:
        raise ValueError("Caminho de anexo inválido.")
    full = (project_root / Path(*rel.split("/"))).resolve()
    base = (project_root / ".squad" / "attachments").resolve()
    try:
        full.relative_to(base)
    except ValueError as exc:
        raise ValueError("Anexo fora da pasta permitida.") from exc
    return full


def list_attachments(chat_id: int) -> list[dict[str, Any]]:
    init_database()
    if not chat_service.get_chat_with_project(chat_id):
        raise ValueError("Chat não encontrado.")
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, chat_id, message_id, project_slug, file_name, file_path,
                   mime_type, size_bytes, created_at
            FROM squad_chat_attachments
            WHERE chat_id = ?
            ORDER BY datetime(created_at) ASC, id ASC
            """,
            (chat_id,),
        ).fetchall()
        return [_row_to_dict(r) for r in rows]
    finally:
        conn.close()


def get_attachment_row(attachment_id: int) -> dict[str, Any] | None:
    init_database()
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT a.*, p.local_path AS project_local_path
            FROM squad_chat_attachments a
            INNER JOIN squad_chats c ON c.id = a.chat_id
            INNER JOIN squad_projects p ON p.id = c.project_id
            WHERE a.id = ?
            """,
            (attachment_id,),
        ).fetchone()
        return _row_to_dict(row) if row else None
    finally:
        conn.close()


def delete_attachment_files_for_chat(chat_id: int) -> None:
    """Remove ficheiros de anexo do disco (chamado antes de apagar o chat)."""
    try:
        _, root = _project_root_for_chat(chat_id)
    except ValueError:
        return
    folder = _attachments_dir(root, chat_id)
    if folder.is_dir():
        import shutil

        shutil.rmtree(folder, ignore_errors=True)


def save_image_attachment(
    *,
    chat_id: int,
    original_filename: str,
    file_obj: BinaryIO,
    content_type: str | None,
) -> dict[str, Any]:
    """
    Valida imagem, grava em `.squad/attachments/chats/<id>/`, regista na BD,
    cria mensagem de utilizador e associa `message_id`.
    """
    init_database()
    chat_row, root = _project_root_for_chat(chat_id)
    slug = str(chat_row.get("project_slug") or "").strip().lower()

    raw_name = Path(original_filename or "image").name
    ext = Path(raw_name).suffix.lower()
    if ext not in _ALLOWED_EXT:
        raise ValueError(f"Extensão não permitida. Use: {', '.join(sorted(_ALLOWED_EXT))}.")

    data = file_obj.read(_MAX_BYTES + 1)
    if len(data) > _MAX_BYTES:
        raise ValueError("Ficheiro demasiado grande (máximo 5MB).")
    if not data:
        raise ValueError("Ficheiro vazio.")

    expected_mime = _EXT_TO_MIME[ext]
    if not _mime_matches(ext, content_type):
        raise ValueError("Tipo MIME não corresponde à extensão.")

    if not _validate_magic(ext, data[:32]):
        raise ValueError("Conteúdo não parece uma imagem válida (assinatura inválida).")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_slug = _SLUG_SAFE.sub("-", Path(raw_name).stem.lower()).strip("-.") or "imagem"
    base_slug = base_slug[:80]

    dest_dir = _attachments_dir(root, chat_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    fname = f"{stamp}-{base_slug}{ext}"
    dest_path = dest_dir / fname
    if dest_path.exists():
        fname = f"{stamp}-{base_slug}-{uuid.uuid4().hex[:8]}{ext}"
        dest_path = dest_dir / fname

    dest_path.write_bytes(data)

    display_name = raw_name or fname
    msg = chat_service.add_message(chat_id, "user", f"Imagem anexada: {display_name}")
    mid = int(msg["id"])
    rel = _relative_db_path(chat_id, fname)
    now = _utc_now_iso()

    conn = get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO squad_chat_attachments (
                chat_id, message_id, project_slug, file_name, file_path,
                mime_type, size_bytes, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                mid,
                slug,
                display_name,
                rel,
                expected_mime,
                len(data),
                now,
            ),
        )
        conn.commit()
        aid = cur.lastrowid
        row = conn.execute(
            "SELECT id, chat_id, message_id, project_slug, file_name, file_path, "
            "mime_type, size_bytes, created_at FROM squad_chat_attachments WHERE id = ?",
            (aid,),
        ).fetchone()
        assert row is not None
        return _row_to_dict(row)
    except Exception:
        conn.rollback()
        try:
            if dest_path.is_file():
                dest_path.unlink()
        except OSError:
            pass
        raise
    finally:
        conn.close()


def resolve_attachment_path(row: dict[str, Any]) -> Path:
    lp = (row.get("project_local_path") or "").strip()
    if not lp:
        raise ValueError("Projeto sem local_path.")
    root = Path(lp).expanduser().resolve()
    return _resolve_stored_file(root, str(row.get("file_path") or ""))


def list_attachment_file_names(chat_id: int) -> list[str]:
    """Nomes de ficheiro para contexto (bootstrap/refine)."""
    try:
        rows = list_attachments(chat_id)
    except ValueError:
        return []
    return [str(r.get("file_name") or "") for r in rows if r.get("file_name")]
