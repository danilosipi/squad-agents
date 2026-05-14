"""Testes da API de backlog (épicos, histórias, tarefas + export backlog.json)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "backlog-api.db"))
    root = tmp_path / "projects_root"
    root.mkdir()
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(root))
    repo_work = tmp_path / "squad_repo"
    repo_work.mkdir()
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(repo_work))
    from apps.api.main import app

    with TestClient(app) as c:
        yield c


def test_backlog_flow_export_json(client: TestClient) -> None:
    r_proj = client.post("/api/projects", json={"name": "Backlog Host"})
    assert r_proj.status_code == 201
    slug = r_proj.json()["slug"]
    local_path = Path(r_proj.json()["local_path"])

    r_ep = client.post(f"/api/backlog/{slug}/epics", json={"title": "Épico A", "description": "d1"})
    assert r_ep.status_code == 201
    epic = r_ep.json()
    assert epic["title"] == "Épico A"
    eid = epic["id"]

    r_le = client.get(f"/api/backlog/{slug}/epics")
    assert r_le.status_code == 200
    assert len(r_le.json()) == 1

    r_st = client.post(
        f"/api/backlog/{slug}/stories",
        json={"title": "História 1", "description": None, "epic_id": eid, "priority": "high"},
    )
    assert r_st.status_code == 201
    story = r_st.json()
    sid = story["id"]

    r_ls = client.get(f"/api/backlog/{slug}/stories")
    assert r_ls.status_code == 200
    assert len(r_ls.json()) == 1

    r_t = client.post(
        f"/api/backlog/{slug}/tasks",
        json={"title": "Tarefa X", "description": "fazer", "story_id": sid},
    )
    assert r_t.status_code == 201
    task = r_t.json()
    tid = task["id"]

    r_lt = client.get(f"/api/backlog/{slug}/tasks")
    assert r_lt.status_code == 200
    assert len(r_lt.json()) == 1

    r_patch = client.patch(f"/api/backlog/tasks/{tid}/status", json={"status": "in_progress"})
    assert r_patch.status_code == 200
    assert r_patch.json()["status"] == "in_progress"

    r_as = client.patch(f"/api/backlog/tasks/{tid}/assign", json={"assignee_agent": "qa"})
    assert r_as.status_code == 200
    assert r_as.json()["assignee_agent"] == "qa"

    backlog_path = local_path / ".squad" / "backlog.json"
    assert backlog_path.is_file()
    data = json.loads(backlog_path.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["project_slug"] == slug
    assert len(data["epics"]) == 1
    assert len(data["stories"]) == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["assignee_agent"] == "qa"
    assert data["tasks"][0]["status"] == "in_progress"
