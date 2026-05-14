"""Testes de artefactos de run e anexos de imagem no chat (Fase 5.12)."""

from __future__ import annotations

import io
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# PNG 1x1 mínimo (assinatura válida)
_MINI_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


@pytest.fixture
def client(monkeypatch, tmp_path) -> TestClient:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "artifacts.db"))
    (tmp_path / "projects_root").mkdir()
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(tmp_path / "projects_root"))
    (tmp_path / "squad_repo").mkdir()
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(tmp_path / "squad_repo"))
    from apps.api.main import app

    with TestClient(app) as c:
        yield c


def _create_project_with_chat(client: TestClient, tmp_path: Path) -> tuple[str, int, Path]:
    r = client.post("/api/projects", json={"name": "Attach Proj"})
    slug = r.json()["slug"]
    lp = Path(r.json()["local_path"])
    (lp / ".squad").mkdir(parents=True, exist_ok=True)
    (lp / ".squad" / "context.md").write_text("x" * 120, encoding="utf-8")
    (lp / ".squad" / "backlog.json").write_text('{"epics":[]}', encoding="utf-8")
    ch = client.post("/api/chats", json={"project_slug": slug, "title": "c1"})
    cid = ch.json()["id"]
    return slug, int(cid), lp


def test_get_run_artifacts_all_files(client: TestClient, tmp_path: Path) -> None:
    r_proj = client.post("/api/projects", json={"name": "Art All"})
    slug = r_proj.json()["slug"]
    r_t = client.post(f"/api/backlog/{slug}/tasks", json={"title": "T1"})
    tid = r_t.json()["id"]
    r_p = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    rid = r_p.json()["run_id"]
    repo = tmp_path / "squad_repo"
    run_dir = repo / "runs" / slug / rid
    (run_dir / "final.md").write_text("# ok\n", encoding="utf-8")
    (run_dir / "execution.log").write_text("log line\n", encoding="utf-8")

    r = client.get(f"/api/runs/{rid}/artifacts")
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] == rid
    assert body["project_slug"] == slug
    names = {a["name"]: a for a in body["artifacts"]}
    assert names["input.md"]["exists"] is True
    assert names["final.md"]["exists"] is True
    assert "ok" in (names["final.md"]["content"] or "")
    assert names["execution.log"]["exists"] is True


def test_get_run_artifacts_404(client: TestClient) -> None:
    r = client.get("/api/runs/board-nao-existe-99999999/artifacts")
    assert r.status_code == 404


def test_get_run_artifacts_missing_final_ok(client: TestClient, tmp_path: Path) -> None:
    r_proj = client.post("/api/projects", json={"name": "Art No Final"})
    slug = r_proj.json()["slug"]
    r_t = client.post(f"/api/backlog/{slug}/tasks", json={"title": "T2"})
    tid = r_t.json()["id"]
    r_p = client.post(f"/api/backlog/tasks/{tid}/prepare-run")
    rid = r_p.json()["run_id"]
    repo = tmp_path / "squad_repo"
    final_p = repo / "runs" / slug / rid / "final.md"
    assert final_p.is_file() is False

    r = client.get(f"/api/runs/{rid}/artifacts")
    assert r.status_code == 200
    names = {a["name"]: a for a in r.json()["artifacts"]}
    assert names["input.md"]["exists"] is True
    assert names["final.md"]["exists"] is False
    assert names["final.md"]["content"] is None


def test_upload_image_valid(client: TestClient, tmp_path: Path) -> None:
    _, cid, lp = _create_project_with_chat(client, tmp_path)
    files = {"file": ("shot.png", io.BytesIO(_MINI_PNG), "image/png")}
    r = client.post(f"/api/chats/{cid}/attachments", files=files)
    assert r.status_code == 201
    row = r.json()
    assert row["chat_id"] == cid
    assert row["size_bytes"] == len(_MINI_PNG)
    rel = row["file_path"].replace("/", os.sep)
    saved = lp / rel
    assert saved.is_file()

    msgs = client.get(f"/api/chats/{cid}/messages").json()
    assert any("Imagem anexada" in str(m.get("content", "")) for m in msgs)


def test_upload_rejects_bad_extension(client: TestClient, tmp_path: Path) -> None:
    _, cid, _ = _create_project_with_chat(client, tmp_path)
    files = {"file": ("x.exe", io.BytesIO(_MINI_PNG), "application/octet-stream")}
    r = client.post(f"/api/chats/{cid}/attachments", files=files)
    assert r.status_code == 400


def test_upload_rejects_oversize(monkeypatch: pytest.MonkeyPatch, client: TestClient, tmp_path: Path) -> None:
    from core.chats import chat_attachment_service

    monkeypatch.setattr(chat_attachment_service, "_MAX_BYTES", 50)
    _, cid, _ = _create_project_with_chat(client, tmp_path)
    files = {"file": ("big.png", io.BytesIO(_MINI_PNG), "image/png")}
    r = client.post(f"/api/chats/{cid}/attachments", files=files)
    assert r.status_code == 400
    detail = str(r.json().get("detail", "")).lower()
    assert "grande" in detail or "5mb" in detail


def test_list_attachments(client: TestClient, tmp_path: Path) -> None:
    _, cid, _ = _create_project_with_chat(client, tmp_path)
    client.post(
        f"/api/chats/{cid}/attachments",
        files={"file": ("a.png", io.BytesIO(_MINI_PNG), "image/png")},
    )
    r = client.get(f"/api/chats/{cid}/attachments")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_get_attachment_preview(client: TestClient, tmp_path: Path) -> None:
    _, cid, _ = _create_project_with_chat(client, tmp_path)
    r_up = client.post(
        f"/api/chats/{cid}/attachments",
        files={"file": ("p.png", io.BytesIO(_MINI_PNG), "image/png")},
    )
    aid = r_up.json()["id"]
    r = client.get(f"/api/chats/attachments/{aid}")
    assert r.status_code == 200
    assert r.content == _MINI_PNG


def test_get_attachment_missing_file_404(client: TestClient, tmp_path: Path) -> None:
    _, cid, lp = _create_project_with_chat(client, tmp_path)
    r_up = client.post(
        f"/api/chats/{cid}/attachments",
        files={"file": ("gone.png", io.BytesIO(_MINI_PNG), "image/png")},
    )
    aid = r_up.json()["id"]
    rel = r_up.json()["file_path"].replace("/", os.sep)
    (lp / rel).unlink()
    r = client.get(f"/api/chats/attachments/{aid}")
    assert r.status_code == 404


def test_health_still_ok(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}
