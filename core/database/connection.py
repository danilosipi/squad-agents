"""Conexão SQLite e preparação do diretório do banco."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from core import config


def get_database_path() -> Path:
    """Caminho absoluto do arquivo SQLite (mesma regra que `core.config`)."""
    return config.get_database_path()


def ensure_database_directory() -> Path:
    """Garante que o diretório que contém o arquivo `.db` exista."""
    path = config.get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection() -> sqlite3.Connection:
    """Abre conexão com `foreign_keys` ativado e `Row` como factory."""
    ensure_database_directory()
    db_path = config.get_database_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
