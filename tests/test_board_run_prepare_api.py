"""Testes da preparação de run a partir de tarefa do Board (Fase 5.9)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "board-run.db"))
    root = tmp_path / "projects_root"
    root.mkdir()
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(root))
    repo_work = tmp_path / "squad_repo"
    repo_work.mkdir()
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(repo_work))
    from apps.api.main import app

    with TestClient(app) as c:
        yield c


def test_prepare_run_from_task_creates_input_and_links(client: TestClient, tmp_path: Path) -> None:
    r_proj = client.post("/api/projects", json={"name": "Board Run Proj"})
    assert r_proj.status_code == 201
    slug = r_proj.json()["slug"]
    local_path = Path(r_proj.json()["local_path"])

    r_ep = client.post(f"/api/backlog/{slug}/epics", json={"title": "E1"})
    assert r_ep.status_code == 201
    eid = r_ep.json()["id"]

    r_st = client.post(
        f"/api/backlog/{slug}/stories",
        json={"title": "S1", "epic_id": eid, "priority": "high"},
    )
    assert r_st.status_code == 201
    sid = r_st.json()["id"]

    r_t = client.post(
        f"/api/backlog/{slug}/tasks",
        json={"title": "Tarefa Board", "description": "Detalhe X", "story_id": sid},
    )
    assert r_t.status_code == 201
    tid = r_t.json()["id"]
    assert r_t.json().get("run_id") in (None, "")

    r_prep = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    assert r_prep.status_code == 201
    body = r_prep.json()
    assert body["run_id"].startswith("board-")
    assert body["run_path"] == f"runs/{slug}/{body['run_id']}"
    assert body["input_path"] == f"runs/{slug}/{body['run_id']}/input.md"
    assert body["task"]["run_id"] == body["run_id"]

    repo = tmp_path / "squad_repo"
    input_file = repo / "runs" / slug / body["run_id"] / "input.md"
    assert input_file.is_file()
    md = input_file.read_text(encoding="utf-8")
    assert "# Demanda" in md
    assert "Tarefa Board" in md
    assert f"Task ID: {tid}" in md
    assert "E1" in md
    assert "S1" in md
    assert "high" in md

    backlog_path = local_path / ".squad" / "backlog.json"
    data = json.loads(backlog_path.read_text(encoding="utf-8"))
    tasks = data["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["run_id"] == body["run_id"]

    r_dup = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    assert r_dup.status_code == 409


def test_prepare_run_unknown_task(client: TestClient) -> None:
    r = client.post("/api/backlog/tasks/99999/prepare-run")
    assert r.status_code == 404
