"""Testes da API local (projetos + chats + mensagens)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "api-test.db"))
    root = tmp_path / "projects_root"
    root.mkdir()
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(root))
    repo_work = tmp_path / "squad_repo"
    repo_work.mkdir()
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(repo_work))
    from apps.api.main import app

    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_projects_create_list(client: TestClient) -> None:
    r = client.post("/api/projects", json={"name": "Projeto API"})
    assert r.status_code == 201
    body = r.json()
    assert body["name"] == "Projeto API"
    assert body["slug"] == "projeto-api"

    r2 = client.get("/api/projects")
    assert r2.status_code == 200
    items = r2.json()
    assert len(items) == 1
    assert items[0]["slug"] == "projeto-api"


def test_chats_and_messages_flow(client: TestClient) -> None:
    assert client.post("/api/projects", json={"name": "Chat Host"}).status_code == 201

    r_chat = client.post(
        "/api/chats",
        json={"project_slug": "chat-host", "title": "Sessão 1"},
    )
    assert r_chat.status_code == 201
    chat = r_chat.json()
    assert chat["title"] == "Sessão 1"
    cid = chat["id"]

    r_list = client.get("/api/chats/project/chat-host")
    assert r_list.status_code == 200
    assert len(r_list.json()) == 1

    r_msg = client.post(
        "/api/chats/messages",
        json={"chat_id": cid, "role": "user", "content": "Olá"},
    )
    assert r_msg.status_code == 201
    assert r_msg.json()["role"] == "user"

    r_msgs = client.get(f"/api/chats/{cid}/messages")
    assert r_msgs.status_code == 200
    msgs = r_msgs.json()
    assert len(msgs) == 1
    assert msgs[0]["content"] == "Olá"
