"""Testes do carregador de contexto de projeto (`.squad/`, README, docs)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from core.database.schema import init_database
from core.projects import project_context_service, project_service


@pytest.fixture
def ctx_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("SQUAD_DATABASE_PATH", str(tmp_path / "ctx.db"))
    monkeypatch.setenv("SQUAD_PROJECTS_ROOT", str(tmp_path / "roots"))
    monkeypatch.setenv("SQUAD_REPO_ROOT", str(tmp_path / "fake_squad_repo"))
    init_database()
    return tmp_path


def _write_min_context(project_root: Path) -> None:
    c = project_root / ".squad" / "context.md"
    c.parent.mkdir(parents=True, exist_ok=True)
    c.write_text(
        "# Contexto\n\n" + ("Conteúdo mínimo para validação da squad. " * 5) + "\n",
        encoding="utf-8",
    )


def test_get_paths_falha_projeto_inexistente(ctx_env: Path) -> None:
    r = project_context_service.get_project_context_paths("nao-existe-slug")
    assert r["ok"] is False
    assert "não encontrado" in (r.get("error") or "").lower()


def test_ensure_squad_com_template(ctx_env: Path) -> None:
    row = project_service.create_project("Alpha Ctx")
    slug = row["slug"]
    root = Path(row["local_path"])
    (root / ".squad" / "context.md").unlink(missing_ok=True)
    out = project_context_service.ensure_project_squad_structure(slug, create_template_if_missing=True)
    assert out["ok"] is True
    assert (root / ".squad" / "context.md").is_file()


def test_load_inclui_readme_e_docs_com_limite(ctx_env: Path) -> None:
    row = project_service.create_project("Beta Ctx")
    slug = row["slug"]
    root = Path(row["local_path"])
    _write_min_context(root)
    (root / "README.md").write_text("# README teste\n\nCorpo.\n", encoding="utf-8")
    docs = root / "docs" / "sub"
    docs.mkdir(parents=True)
    for i in range(30):
        (docs / f"n{i}.md").write_text(f"# doc {i}\n", encoding="utf-8")

    data = project_context_service.load_project_context(slug)
    assert data["ok"] is True
    assert data["files"]["readme_md"]["present"] is True
    assert "README teste" in (data["files"]["readme_md"]["content"] or "")
    assert len(data["docs_markdown"]) == 25
    assert any("limite" in e.lower() for e in (data.get("read_errors") or []))


def test_minimum_context_ausente_arquivo(ctx_env: Path) -> None:
    row = project_service.create_project("Gamma Ctx")
    slug = row["slug"]
    root = Path(row["local_path"])
    (root / ".squad" / "context.md").unlink(missing_ok=True)
    ok, err, pth = project_context_service.minimum_project_context_status(slug)
    assert ok is False
    assert err
    assert pth and "context.md" in pth.replace("/", os.sep)


def test_minimum_context_conteudo_curto(ctx_env: Path) -> None:
    row = project_service.create_project("Delta Ctx")
    slug = row["slug"]
    root = Path(row["local_path"])
    (root / ".squad" / "context.md").write_text("abc", encoding="utf-8")
    ok, err, _p = project_context_service.minimum_project_context_status(slug)
    assert ok is False
    assert "curto" in (err or "").lower()


def test_build_markdown_e_input(ctx_env: Path) -> None:
    row = project_service.create_project("Epsilon Ctx")
    slug = row["slug"]
    root = Path(row["local_path"])
    _write_min_context(root)
    md = project_context_service.build_project_context_markdown(slug)
    assert "context.md" in md
    composed = project_context_service.build_input_with_project_context(
        demand_header="# Demanda\n\n",
        user_message="Fazer X",
        project_context_md=md,
    )
    assert "# Contexto do Projeto Selecionado" in composed
    assert "Fazer X" in composed


def test_ensure_run_evidence_cria_arquivo(ctx_env: Path) -> None:
    row = project_service.create_project("Zeta Ctx")
    slug = row["slug"]
    _write_min_context(Path(row["local_path"]))
    repo = ctx_env / "squad-repo"
    repo.mkdir()
    run_dir = repo / "runs" / slug / "run-ev-1"
    run_dir.mkdir(parents=True)
    (run_dir / "input.md").write_text("x", encoding="utf-8")

    ok, err, rel = project_context_service.ensure_run_project_context_evidence(
        project_slug=slug,
        run_id="run-ev-1",
        repo_root=repo,
    )
    assert ok is True
    assert err is None
    assert rel and rel.endswith("project-context-used.md")
    assert (run_dir / "project-context-used.md").is_file()
