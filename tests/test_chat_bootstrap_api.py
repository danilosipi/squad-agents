"""Testes de bootstrap de projeto, chats e prompts (API)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "bootstrap-test.db"))
    root = tmp_path / "projects_root"
    root.mkdir()
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(root))
    repo_work = tmp_path / "squad_repo"
    repo_work.mkdir()
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(repo_work))
    from apps.api.main import app

    with TestClient(app) as c:
        yield c


def test_bootstrap_status_sem_contexto(client: TestClient) -> None:
    r = client.post("/api/projects", json={"name": "Alpha Boot"})
    assert r.status_code == 201
    slug = r.json()["slug"]
    lp = Path(r.json()["local_path"])
    (lp / ".squad" / "context.md").unlink(missing_ok=True)
    st = client.get(f"/api/projects/{slug}/bootstrap-status").json()
    assert st["needs_bootstrap"] is True
    assert st["has_context_md"] is False


def test_post_bootstrap_cria_context_e_backlog(client: TestClient) -> None:
    r = client.post("/api/projects", json={"name": "Beta Boot"})
    assert r.status_code == 201
    slug = r.json()["slug"]
    lp = Path(r.json()["local_path"])
    (lp / ".squad" / "context.md").unlink(missing_ok=True)
    (lp / ".squad" / "backlog.json").unlink(missing_ok=True)

    r2 = client.post(f"/api/projects/{slug}/bootstrap")
    assert r2.status_code == 201
    ctx = lp / ".squad" / "context.md"
    assert ctx.is_file()
    text = ctx.read_text(encoding="utf-8")
    assert "Nome:" in text and slug in text
    assert str(lp.resolve()) in text or str(lp) in text
    raw = (lp / ".squad" / "backlog.json").read_text(encoding="utf-8")
    data = json.loads(raw)
    assert "epics" in data and "tasks" in data


def test_refine_context_grava_ficheiro(client: TestClient) -> None:
    r = client.post("/api/projects", json={"name": "Gamma Ref"})
    slug = r.json()["slug"]
    lp = Path(r.json()["local_path"])
    (lp / ".squad" / "context.md").unlink(missing_ok=True)

    cid = client.post(
        "/api/chats",
        json={"project_slug": slug, "title": "t1"},
    ).json()["id"]
    client.post(
        "/api/chats/messages",
        json={"chat_id": cid, "role": "user", "content": "Objetivo: testar refine."},
    )
    r3 = client.post(
        f"/api/projects/{slug}/context/refine",
        json={"chat_id": int(cid), "overwrite": True},
    )
    assert r3.status_code == 201
    body = r3.json()
    assert "context_path" in body
    assert (lp / ".squad" / "context.md").is_file()


def test_rename_e_delete_chat(client: TestClient) -> None:
    client.post("/api/projects", json={"name": "Delta Chat"})
    slug = "delta-chat"
    cid = int(
        client.post("/api/chats", json={"project_slug": slug, "title": "A"}).json()["id"]
    )
    r = client.patch(f"/api/chats/{cid}", json={"title": "Novo nome"})
    assert r.status_code == 200
    assert r.json()["title"] == "Novo nome"

    r_del = client.delete(f"/api/chats/{cid}")
    assert r_del.status_code == 204
    assert client.get(f"/api/chats/{cid}/messages").status_code == 404


def test_save_prompt_cria_ficheiro_rastreavel(client: TestClient) -> None:
    client.post("/api/projects", json={"name": "Epsilon Prompt"})
    slug = "epsilon-prompt"
    lp = Path(client.get(f"/api/projects/{slug}").json()["local_path"])
    cid = int(
        client.post("/api/chats", json={"project_slug": slug, "title": "p"}).json()["id"]
    )
    r = client.post(
        f"/api/chats/{cid}/save-prompt",
        json={"title_slug": "meu-prompt", "content": "Conteúdo importante."},
    )
    assert r.status_code == 201
    rel = r.json()["relative"]
    assert rel.startswith(".squad/prompts/")
    assert (lp / ".squad" / "prompts").is_dir()
    files = list((lp / ".squad" / "prompts").glob("*.md"))
    assert len(files) >= 1
