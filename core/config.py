"""Configuração local: raiz de projetos e caminho do SQLite."""

from __future__ import annotations

import os
from pathlib import Path

# Valores padrão (sobrescrevíveis por variáveis de ambiente).
PROJECTS_ROOT: Path = Path(r"D:\Drive\Projetos")
DATABASE_PATH: Path = Path("data") / "squad-agents.db"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_repo_root() -> Path:
    """Raiz do repositório squad-agentes (SQUAD_REPO_ROOT para testes ou CI)."""
    raw = os.environ.get("SQUAD_REPO_ROOT")
    if raw:
        return Path(raw).expanduser().resolve()
    return _repo_root()


def get_projects_root() -> Path:
    """Raiz onde projetos são listados/criados (SQUAD_PROJECTS_ROOT)."""
    raw = os.environ.get("SQUAD_PROJECTS_ROOT")
    if raw:
        return Path(raw).expanduser().resolve()
    return PROJECTS_ROOT.expanduser().resolve()


def get_database_path() -> Path:
    """Caminho absoluto do arquivo SQLite (SQUAD_DATABASE_PATH ou padrão em data/)."""
    raw = os.environ.get("SQUAD_DATABASE_PATH")
    if raw:
        return Path(raw).expanduser().resolve()
    return (_repo_root() / DATABASE_PATH).resolve()
