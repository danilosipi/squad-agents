import json
import sqlite3
from pathlib import Path

import pytest

from core.database.schema import init_database
from core.projects.project_service import (
    create_project,
    get_project_by_slug,
    list_projects,
    register_existing_project,
    slugify_project_name,
)


@pytest.fixture
def isolated_env(monkeypatch, tmp_path):
    db = tmp_path / "test.db"
    root = tmp_path / "projetos"
    root.mkdir()
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(db))
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(root))
    return {"db": db, "root": root}


def test_slugify_basic():
    assert slugify_project_name("Projeto Teste") == "projeto-teste"
    assert slugify_project_name("  CAP  ") == "cap"
    assert slugify_project_name("---") == "project"


def test_init_database_creates_tables(isolated_env):
    init_database()
    conn = sqlite3.connect(str(isolated_env["db"]))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        names = {r[0] for r in rows}
    finally:
        conn.close()
    expected = {
        "squad_projects",
        "squad_chats",
        "squad_messages",
        "squad_epics",
        "squad_stories",
        "squad_tasks",
        "squad_runs",
    }
    assert expected <= names


def test_create_project_creates_folder_and_squad(isolated_env):
    init_database()
    row = create_project("Alpha Beta")
    path = Path(row["local_path"])
    assert path.is_dir()
    assert (path / ".squad" / "context.md").exists()
    assert (path / ".squad" / "roadmap.md").exists()
    assert (path / ".squad" / "decisions.md").exists()
    assert (path / ".squad" / "backlog.json").exists()
    assert (path / ".squad" / "chats").is_dir()
    assert (path / ".squad" / "runs").is_dir()
    assert (path / ".squad" / "outputs").is_dir()
    raw = (path / ".squad" / "backlog.json").read_text(encoding="utf-8")
    assert json.loads(raw) == []


def test_register_existing_project(isolated_env):
    init_database()
    existing = isolated_env["root"] / "externo"
    existing.mkdir()
    (existing / "readme.txt").write_text("x", encoding="utf-8")
    row = register_existing_project("Externo", str(existing))
    assert Path(row["local_path"]) == existing.resolve()
    squad = existing / ".squad"
    assert squad.is_dir()


def test_list_projects_returns_rows(isolated_env):
    init_database()
    create_project("Um")
    create_project("Dois")
    items = list_projects()
    assert len(items) == 2
    slugs = {p["slug"] for p in items}
    assert slugs == {"um", "dois"}


def test_get_project_by_slug(isolated_env):
    init_database()
    create_project("Gamma")
    g = get_project_by_slug("gamma")
    assert g is not None
    assert g["name"] == "Gamma"
