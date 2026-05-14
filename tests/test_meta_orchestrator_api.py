"""Testes do endpoint meta-orquestrador (sem chamadas reais à OpenAI)."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from core.orchestration import meta_orchestrator_service


@pytest.fixture
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "meta-api-test.db"))
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
        json={"project_slug": "cap", "title": "Chat meta"},
    )
    assert r_chat.status_code == 201
    chat = r_chat.json()
    return int(chat["id"]), int(chat["project_id"])


def test_meta_endpoint_chat_inexistente(client: TestClient) -> None:
    r = client.post(
        "/api/chats/messages/with-meta-orchestrator",
        json={"chat_id": 99999, "content": "Olá"},
    )
    assert r.status_code == 404


def test_meta_endpoint_contexto_minimo_insuficiente(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    r_proj = client.post("/api/projects", json={"name": "CAP"})
    assert r_proj.status_code == 201
    lp = Path(r_proj.json()["local_path"])
    (lp / ".squad" / "context.md").write_text("curto", encoding="utf-8")
    r_chat = client.post(
        "/api/chats",
        json={"project_slug": "cap", "title": "Chat curto"},
    )
    assert r_chat.status_code == 201
    cid = int(r_chat.json()["id"])
    r = client.post(
        "/api/chats/messages/with-meta-orchestrator",
        json={"chat_id": cid, "content": "demanda"},
    )
    assert r.status_code == 400
    detail = r.json().get("detail", "")
    assert "contexto" in detail.lower() or ".squad" in detail

    r_msgs = client.get(f"/api/chats/{cid}/messages")
    assert r_msgs.json() == []


def test_meta_endpoint_projeto_nao_cap(client: TestClient) -> None:
    assert client.post("/api/projects", json={"name": "Outro"}).status_code == 201
    r_chat = client.post(
        "/api/chats",
        json={"project_slug": "outro", "title": "X"},
    )
    assert r_chat.status_code == 201
    cid = int(r_chat.json()["id"])
    r = client.post(
        "/api/chats/messages/with-meta-orchestrator",
        json={"chat_id": cid, "content": "demanda"},
    )
    assert r.status_code == 400
    assert meta_orchestrator_service.UNSUPPORTED_PROJECT_MESSAGE in r.json().get("detail", "")


def test_meta_endpoint_sem_openai_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cid, _ = _cap_chat(client)
    r = client.post(
        "/api/chats/messages/with-meta-orchestrator",
        json={"chat_id": cid, "content": "demanda"},
    )
    assert r.status_code == 503
    assert "OPENAI_API_KEY" in r.json().get("detail", "")

    r_msgs = client.get(f"/api/chats/{cid}/messages")
    assert r_msgs.status_code == 200
    assert r_msgs.json() == []


def test_meta_endpoint_falha_orquestrador_nao_quebra_api(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    cid, pid = _cap_chat(client)

    def _boom(**_kwargs):
        return meta_orchestrator_service.MetaOrchestratorRunResult(
            ok=False,
            run_id="web-fail1",
            run_path_posix="runs/cap/web-fail1",
            markdown="",
            exit_code=1,
            stdout="",
            stderr="erro simulado",
            error_detail="Falha simulada do subprocesso.",
        )

    monkeypatch.setattr(meta_orchestrator_service, "run_meta_orchestrator", _boom)

    r = client.post(
        "/api/chats/messages/with-meta-orchestrator",
        json={"chat_id": cid, "content": "demanda"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "failed"
    assert body["run_id"] == "web-fail1"
    assert "erro" in body["assistant_message"]["content"].lower()

    r_msgs = client.get(f"/api/chats/{cid}/messages")
    msgs = r_msgs.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["role"] == "assistant"

    p = Path(os.environ["SQUAD_DATABASE_PATH"])
    conn = sqlite3.connect(str(p))
    try:
        n = conn.execute("SELECT COUNT(*) FROM squad_runs WHERE project_id = ?", (pid,)).fetchone()[0]
        assert n == 1
        st = conn.execute("SELECT status FROM squad_runs WHERE project_id = ?", (pid,)).fetchone()[0]
        assert st == "failed"
    finally:
        conn.close()


def test_meta_endpoint_sucesso_mock(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-fake")
    cid, pid = _cap_chat(client)

    def _ok(**_kwargs):
        return meta_orchestrator_service.MetaOrchestratorRunResult(
            ok=True,
            run_id="web-ok1",
            run_path_posix="runs/cap/web-ok1",
            markdown="# Plano\n\n- passo 1",
            exit_code=0,
            stdout="ok",
            stderr="",
            error_detail=None,
            context_loaded=True,
            context_evidence_path="runs/cap/web-ok1/project-context-used.md",
        )

    monkeypatch.setattr(meta_orchestrator_service, "run_meta_orchestrator", _ok)

    r = client.post(
        "/api/chats/messages/with-meta-orchestrator",
        json={"chat_id": cid, "content": "Quero um plano"},
    )
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "success"
    assert body["run_id"] == "web-ok1"
    assert body["run_path"] == "runs/cap/web-ok1"
    assert body.get("context_loaded") is True
    assert body.get("context_evidence_path") == "runs/cap/web-ok1/project-context-used.md"
    assert body["user_message"]["role"] == "user"
    assert body["user_message"]["content"] == "Quero um plano"
    assert "# Plano" in body["assistant_message"]["content"]
    assert "Executar squad" in body["assistant_message"]["content"]

    r_msgs = client.get(f"/api/chats/{cid}/messages")
    msgs = r_msgs.json()
    assert len(msgs) == 2
    assert "# Plano" in msgs[1]["content"]
    assert "Executar squad" in msgs[1]["content"]

    p = Path(os.environ["SQUAD_DATABASE_PATH"])
    conn = sqlite3.connect(str(p))
    try:
        n = conn.execute("SELECT COUNT(*) FROM squad_runs WHERE project_id = ?", (pid,)).fetchone()[0]
        assert n == 1
        st = conn.execute("SELECT status FROM squad_runs WHERE project_id = ?", (pid,)).fetchone()[0]
        assert st == "awaiting_human_approval"
    finally:
        conn.close()
