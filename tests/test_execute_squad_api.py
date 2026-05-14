"""Testes do endpoint de execução da squad completa (sem OpenAI real)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core import squad_runs
from core.orchestration import squad_full_run_service


@pytest.fixture
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "exec-squad-test.db"))
    root = tmp_path / "projects_root"
    root.mkdir()
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(root))
    repo_work = tmp_path / "squad_repo"
    repo_work.mkdir()
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(repo_work))
    from apps.api.main import app

    with TestClient(app) as c:
        yield c


def _cap_chat(client: TestClient) -> tuple[int, int]:
    r_proj = client.post("/api/projects", json={"name": "CAP"})
    assert r_proj.status_code == 201
    proj = r_proj.json()
    lp = Path(proj["local_path"])
    ctx = lp / ".squad" / "context.md"
    ctx.write_text(
        "# Contexto CAP (testes API)\n\n"
        + ("Objetivo, stack e restrições descritas para pytest. " * 3)
        + "\n",
        encoding="utf-8",
    )
    r_chat = client.post(
        "/api/chats",
        json={"project_slug": "cap", "title": "Chat squad"},
    )
    assert r_chat.status_code == 201
    chat = r_chat.json()
    return int(chat["id"]), int(chat["project_id"])


def test_execute_squad_bloqueado_contexto_minimo(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    r_proj = client.post("/api/projects", json={"name": "CAP"})
    assert r_proj.status_code == 201
    lp = Path(r_proj.json()["local_path"])
    (lp / ".squad" / "context.md").write_text("x", encoding="utf-8")
    r_chat = client.post(
        "/api/chats",
        json={"project_slug": "cap", "title": "Chat bloq"},
    )
    assert r_chat.status_code == 201
    cid = int(r_chat.json()["id"])
    pid = int(r_chat.json()["project_id"])

    def _should_not_run(**_kwargs: object) -> None:
        raise AssertionError("run_full_squad não deveria ser chamado quando o contexto bloqueia")

    monkeypatch.setattr(squad_full_run_service, "run_full_squad", _should_not_run)

    squad_runs.create_squad_run_record(
        project_id=pid,
        run_id="run-block-ctx",
        run_path="runs/cap/run-block-ctx",
        status=squad_runs.STATUS_AWAITING_HUMAN_APPROVAL,
        chat_id=cid,
    )
    r = client.post("/api/runs/run-block-ctx/execute-squad", json={"chat_id": cid})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "blocked"
    assert body.get("context_loaded") is False
    assert body.get("context_evidence_path") is None
    msgs = client.get(f"/api/chats/{cid}/messages").json()
    assert any("Squad bloqueada" in m["content"] for m in msgs)

    p = Path(os.environ["SQUAD_DATABASE_PATH"])
    conn = sqlite3.connect(str(p))
    try:
        st = conn.execute(
            "SELECT status FROM squad_runs WHERE run_id = ?", ("run-block-ctx",)
        ).fetchone()[0]
        assert st == squad_runs.STATUS_AWAITING_HUMAN_APPROVAL
    finally:
        conn.close()


def test_execute_run_inexistente(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    r = client.post("/api/runs/nao-existe/execute-squad", json={"chat_id": 1})
    assert r.status_code == 404


def test_execute_status_invalido(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    cid, pid = _cap_chat(client)
    squad_runs.create_squad_run_record(
        project_id=pid,
        run_id="run-x",
        run_path="runs/cap/run-x",
        status=squad_runs.STATUS_FAILED,
        chat_id=cid,
    )
    r = client.post("/api/runs/run-x/execute-squad", json={"chat_id": cid})
    assert r.status_code == 400


def test_execute_sem_status_aprovacao(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    cid, pid = _cap_chat(client)
    squad_runs.create_squad_run_record(
        project_id=pid,
        run_id="run-created",
        run_path="runs/cap/run-created",
        status=squad_runs.STATUS_CREATED,
        chat_id=cid,
    )
    r = client.post("/api/runs/run-created/execute-squad", json={"chat_id": cid})
    assert r.status_code == 400


def test_execute_sucesso_mock(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    cid, pid = _cap_chat(client)

    squad_runs.create_squad_run_record(
        project_id=pid,
        run_id="run-ok",
        run_path="runs/cap/run-ok",
        status=squad_runs.STATUS_AWAITING_HUMAN_APPROVAL,
        chat_id=cid,
    )

    def _ok(**_kwargs):
        return squad_full_run_service.FullSquadRunResult(
            ok=True,
            exit_code=0,
            stdout="",
            stderr="",
            final_markdown="# Final\n\nTudo certo.",
            error_detail=None,
        )

    monkeypatch.setattr(squad_full_run_service, "run_full_squad", _ok)

    r = client.post("/api/runs/run-ok/execute-squad", json={"chat_id": cid})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "completed"
    assert body["run_id"] == "run-ok"
    assert body["final_path"] == "runs/cap/run-ok/final.md"
    assert body.get("context_loaded") is True
    assert body.get("context_evidence_path", "").endswith("project-context-used.md")
    assert "Resultado da squad completa" in body["assistant_message"]["content"]
    assert "Tudo certo" in body["assistant_message"]["content"]

    msgs = client.get(f"/api/chats/{cid}/messages").json()
    assert any("Resultado da squad completa" in m["content"] for m in msgs)

    p = Path(os.environ["SQUAD_DATABASE_PATH"])
    conn = sqlite3.connect(str(p))
    try:
        st = conn.execute(
            "SELECT status FROM squad_runs WHERE run_id = ?", ("run-ok",)
        ).fetchone()[0]
        assert st == "completed"
    finally:
        conn.close()


def test_execute_falha_mock(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    cid, pid = _cap_chat(client)
    squad_runs.create_squad_run_record(
        project_id=pid,
        run_id="run-bad",
        run_path="runs/cap/run-bad",
        status=squad_runs.STATUS_AWAITING_HUMAN_APPROVAL,
        chat_id=cid,
    )

    def _bad(**_kwargs):
        return squad_full_run_service.FullSquadRunResult(
            ok=False,
            exit_code=1,
            stdout="",
            stderr="oops",
            final_markdown=None,
            error_detail="Falha simulada.",
        )

    monkeypatch.setattr(squad_full_run_service, "run_full_squad", _bad)

    r = client.post("/api/runs/run-bad/execute-squad", json={"chat_id": cid})
    assert r.status_code == 200
    assert r.json()["status"] == "failed"
    assert "Squad completa" in r.json()["assistant_message"]["content"]

    p = Path(os.environ["SQUAD_DATABASE_PATH"])
    conn = sqlite3.connect(str(p))
    try:
        st = conn.execute(
            "SELECT status FROM squad_runs WHERE run_id = ?", ("run-bad",)
        ).fetchone()[0]
        assert st == "failed"
    finally:
        conn.close()


def test_execute_run_ja_concluido(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    cid, pid = _cap_chat(client)
    squad_runs.create_squad_run_record(
        project_id=pid,
        run_id="run-done",
        run_path="runs/cap/run-done",
        status=squad_runs.STATUS_COMPLETED,
        chat_id=cid,
    )
    r = client.post("/api/runs/run-done/execute-squad", json={"chat_id": cid})
    assert r.status_code == 400


def test_pending_squad_run_endpoint(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    cid, pid = _cap_chat(client)
    squad_runs.create_squad_run_record(
        project_id=pid,
        run_id="run-pend",
        run_path="runs/cap/run-pend",
        status=squad_runs.STATUS_AWAITING_HUMAN_APPROVAL,
        chat_id=cid,
    )
    r = client.get(f"/api/chats/{cid}/pending-squad-run")
    assert r.status_code == 200
    j = r.json()
    assert j is not None
    assert j["run_id"] == "run-pend"
    assert j["status"] == squad_runs.STATUS_AWAITING_HUMAN_APPROVAL


def test_execute_chat_id_incompativel(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    cid, pid = _cap_chat(client)
    squad_runs.create_squad_run_record(
        project_id=pid,
        run_id="run-chat",
        run_path="runs/cap/run-chat",
        status=squad_runs.STATUS_AWAITING_HUMAN_APPROVAL,
        chat_id=cid,
    )
    r = client.post("/api/runs/run-chat/execute-squad", json={"chat_id": 99999})
    assert r.status_code == 400
