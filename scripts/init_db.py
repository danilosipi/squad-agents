#!/usr/bin/env python3
"""Inicializa o SQLite local (schema + diretório data/)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.database.connection import ensure_database_directory, get_database_path
from core.database.schema import init_database


def main() -> None:
    ensure_database_directory()
    init_database()
    db = get_database_path()
    print(f"Banco SQLite pronto em: {db}")


if __name__ == "__main__":
    main()
