"""Leitura segura de artefatos de uma run (`input.md`, `final.md`, `execution.log`)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.config import get_repo_root
from core import squad_runs

_MAX_BYTES_PER_FILE = 1_048_576  # 1 MiB por artefato (proteção simples)


def _artifact_type(name: str) -> str:
    if name.endswith(".md"):
        return "markdown"
    if name == "execution.log":
        return "log"
    return "text"


def _safe_run_dir(run_id: str, row: dict[str, Any]) -> Path:
    rid = (run_id or "").strip()
    if not rid:
        raise ValueError("run_id inválido.")

    rp = str(row.get("run_path") or "").strip().replace("\\", "/").strip("/")
    if not rp or ".." in rp or rp.startswith("/"):
        raise ValueError("run_path inválido.")

    root = get_repo_root().resolve()
    runs_root = (root / "runs").resolve()
    run_dir = (root / Path(*rp.split("/"))).resolve()

    try:
        run_dir.relative_to(runs_root)
    except ValueError as exc:
        raise ValueError("Caminho da run fora da área permitida.") from exc

    if run_dir.name != rid:
        raise ValueError("run_path não corresponde ao run_id.")

    return run_dir


def get_run_artifacts(run_id: str) -> dict[str, Any]:
    """
    Devolve metadados e conteúdo dos artefatos esperados da run.

    Levanta `ValueError` se a run não existir ou o caminho for inválido.
    """
    rid = (run_id or "").strip()
    row = squad_runs.get_squad_run_by_run_id(rid)
    if not row:
        raise ValueError("Run não encontrado.")

    slug = str(row.get("project_slug") or "").strip().lower()
    run_dir = _safe_run_dir(rid, row)

    artifacts: list[dict[str, Any]] = []
    for name in ("input.md", "final.md", "execution.log"):
        path = run_dir / name
        if not path.is_file():
            artifacts.append(
                {
                    "name": name,
                    "type": _artifact_type(name),
                    "exists": False,
                    "content": None,
                }
            )
            continue
        try:
            raw = path.read_bytes()
        except OSError:
            artifacts.append(
                {
                    "name": name,
                    "type": _artifact_type(name),
                    "exists": True,
                    "content": None,
                }
            )
            continue
        if len(raw) > _MAX_BYTES_PER_FILE:
            artifacts.append(
                {
                    "name": name,
                    "type": _artifact_type(name),
                    "exists": True,
                    "content": None,
                    "truncated": True,
                }
            )
            continue
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")
        artifacts.append(
            {
                "name": name,
                "type": _artifact_type(name),
                "exists": True,
                "content": text,
            }
        )

    return {
        "run_id": rid,
        "project_slug": slug,
        "artifacts": artifacts,
    }
