"""Testes do endpoint de execução de runs preparadas pelo Board (Fase 5.10)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.orchestration.squad_full_run_service import FullSquadRunResult


@pytest.fixture
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "board-exec.db"))
    (tmp_path / "projects_root").mkdir()
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(tmp_path / "projects_root"))
    (tmp_path / "squad_repo").mkdir()
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(tmp_path / "squad_repo"))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake-key-for-board-exec-tests")
    from apps.api.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def client_no_task(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "board-exec-nt.db"))
    (tmp_path / "projects_root").mkdir()
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(tmp_path / "projects_root"))
    (tmp_path / "squad_repo").mkdir()
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(tmp_path / "squad_repo"))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    from apps.api.main import app

    with TestClient(app) as c:
        yield c


def test_execute_board_run_success_writes_log(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run_full_squad(**kwargs: object) -> FullSquadRunResult:
        return FullSquadRunResult(
            ok=True,
            exit_code=0,
            stdout="stdout-line",
            stderr="",
            final_markdown="# final ok\n",
            error_detail=None,
        )

    monkeypatch.setattr(
        "core.orchestration.board_run_execute_service.run_full_squad",
        fake_run_full_squad,
    )

    r_proj = client.post("/api/projects", json={"name": "Exec Board Ok"})
    slug = r_proj.json()["slug"]
    r_t = client.post(f"/api/backlog/{slug}/tasks", json={"title": "T1"})
    tid = r_t.json()["id"]
    r_p = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    rid = r_p.json()["run_id"]

    r_x = client.post(f"/api/runs/{rid}/execute-board-run")
    assert r_x.status_code == 200
    body = r_x.json()
    assert body["status"] == "completed"
    assert body["run_id"] == rid
    assert body["task"]["status"] == "in_review"
    assert body["task"]["run_id"] == rid

    repo = tmp_path / "squad_repo"
    log_path = repo / "runs" / slug / rid / "execution.log"
    assert log_path.is_file()
    assert "stdout-line" in log_path.read_text(encoding="utf-8")


def test_execute_board_run_404(client: TestClient) -> None:
    r = client.post("/api/runs/board-does-not-exist-zzzzzzzz/execute-board-run")
    assert r.status_code == 404


def test_execute_board_run_without_task_id(client_no_task: TestClient, tmp_path: Path) -> None:
    client = client_no_task
    r_proj = client.post("/api/projects", json={"name": "No Task"})
    slug = r_proj.json()["slug"]
    r_t = client.post(f"/api/backlog/{slug}/tasks", json={"title": "T2"})
    tid = r_t.json()["id"]
    r_p = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    rid = r_p.json()["run_id"]
    db_path = tmp_path / "board-exec-nt.db"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("UPDATE squad_runs SET task_id = NULL WHERE run_id = ?", (rid,))
        conn.commit()
    finally:
        conn.close()

    r = client.post(f"/api/runs/{rid}/execute-board-run")
    assert r.status_code == 400


def test_execute_board_run_missing_input_returns_400(
    client: TestClient, tmp_path: Path
) -> None:
    r_proj = client.post("/api/projects", json={"name": "No Input File"})
    slug = r_proj.json()["slug"]
    r_t = client.post(f"/api/backlog/{slug}/tasks", json={"title": "T3"})
    tid = r_t.json()["id"]
    r_p = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    rid = r_p.json()["run_id"]
    root = tmp_path / "squad_repo"
    input_path = root / "runs" / slug / rid / "input.md"
    assert input_path.is_file()
    input_path.unlink()

    r = client.post(f"/api/runs/{rid}/execute-board-run")
    assert r.status_code == 400
    assert "input" in r.json()["detail"].lower()


def test_execute_board_run_squad_failure_returns_failed_payload(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_fail(**kwargs: object) -> FullSquadRunResult:
        return FullSquadRunResult(
            ok=False,
            exit_code=1,
            stdout="",
            stderr="nope",
            final_markdown=None,
            error_detail="falha simulada",
        )

    monkeypatch.setattr(
        "core.orchestration.board_run_execute_service.run_full_squad",
        fake_fail,
    )

    r_proj = client.post("/api/projects", json={"name": "Fail Squad"})
    slug = r_proj.json()["slug"]
    r_t = client.post(f"/api/backlog/{slug}/tasks", json={"title": "T3b"})
    tid = r_t.json()["id"]
    r_p = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    rid = r_p.json()["run_id"]

    r = client.post(f"/api/runs/{rid}/execute-board-run")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "failed"
    assert body["task"]["run_id"] == rid
    assert body["task"]["status"] == "blocked"


def test_execute_board_run_completed_is_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_ok(**kwargs: object) -> FullSquadRunResult:
        return FullSquadRunResult(True, 0, "o", "", "# f", None)

    monkeypatch.setattr(
        "core.orchestration.board_run_execute_service.run_full_squad",
        fake_ok,
    )

    r_proj = client.post("/api/projects", json={"name": "Twice"})
    slug = r_proj.json()["slug"]
    r_t = client.post(f"/api/backlog/{slug}/tasks", json={"title": "T4"})
    tid = r_t.json()["id"]
    r_p = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    rid = r_p.json()["run_id"]
    assert client.post(f"/api/runs/{rid}/execute-board-run").status_code == 200
    r2 = client.post(f"/api/runs/{rid}/execute-board-run")
    assert r2.status_code == 409
