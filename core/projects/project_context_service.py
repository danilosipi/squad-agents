"""Carrega e valida contexto local do projeto (`.squad/`, README, docs) para runs da squad."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from core.config import get_repo_root
from core.projects import project_service

# Limites simples para não explodir o prompt
_MAX_DOCS_FILES = 25
_MAX_CHARS_PER_DOC_FILE = 12_000
_MAX_README_CHARS = 80_000

# Conteúdo mínimo em `.squad/context.md` (além de existir o arquivo)
_CONTEXT_MIN_STRIP_LEN = 80

PROJECT_CONTEXT_EVIDENCE_FILENAME = "project-context-used.md"

MINIMUM_CONTEXT_USER_MESSAGE = (
    "Este projeto ainda não possui contexto mínimo. Preencha `.squad/context.md` antes de executar a squad."
)


def _posix_rel_under_project(project_root: Path, file_path: Path) -> str:
    try:
        rel = file_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        rel = file_path.name
    return rel.as_posix()


def get_project_context_paths(project_slug: str) -> dict[str, Any]:
    """
    Resolve caminhos esperados para arquivos de contexto do projeto.
    Retorna `ok=False` se o projeto não estiver no SQLite ou `local_path` inválido.
    """
    slug = (project_slug or "").strip().lower()
    if not slug:
        return {
            "ok": False,
            "error": "project_slug vazio.",
            "project_slug": slug,
            "local_path_resolved": "",
            "squad_dir": "",
            "expected_context_path": "",
            "paths": {},
        }

    row = project_service.get_project_by_slug(slug)
    if not row:
        return {
            "ok": False,
            "error": f"Projeto não encontrado no cadastro: {slug!r}",
            "project_slug": slug,
            "local_path_resolved": "",
            "squad_dir": "",
            "expected_context_path": "",
            "paths": {},
        }

    lp = (row.get("local_path") or "").strip()
    if not lp:
        return {
            "ok": False,
            "error": "Projeto sem `local_path` no cadastro.",
            "project_slug": slug,
            "local_path_resolved": "",
            "squad_dir": "",
            "expected_context_path": "",
            "paths": {},
        }

    root = Path(lp).expanduser()
    try:
        root = root.resolve()
    except OSError as exc:
        return {
            "ok": False,
            "error": f"Caminho do projeto inválido: {exc}",
            "project_slug": slug,
            "local_path_resolved": lp,
            "squad_dir": "",
            "expected_context_path": "",
            "paths": {},
        }

    if not root.is_dir():
        return {
            "ok": False,
            "error": f"Pasta do projeto inexistente ou inacessível: {root}",
            "project_slug": slug,
            "local_path_resolved": str(root),
            "squad_dir": "",
            "expected_context_path": "",
            "paths": {},
        }

    squad = root / ".squad"
    paths_map: dict[str, str | None] = {
        "context_md": str(squad / "context.md"),
        "roadmap_md": str(squad / "roadmap.md"),
        "decisions_md": str(squad / "decisions.md"),
        "backlog_json": str(squad / "backlog.json"),
        "readme_md": str(root / "README.md"),
    }

    return {
        "ok": True,
        "error": None,
        "project_slug": slug,
        "local_path_resolved": str(root),
        "squad_dir": str(squad),
        "expected_context_path": str(squad / "context.md"),
        "paths": paths_map,
    }


def ensure_project_squad_structure(
    project_slug: str,
    *,
    create_template_if_missing: bool = False,
) -> dict[str, Any]:
    """
    Garante diretório `.squad/` (e defaults de arquivos) no `local_path` do projeto.

    Se `create_template_if_missing` for True, delega a `ensure_squad_layout_for_project`
    (cria arquivos padrão como no cadastro). Caso contrário, apenas cria `.squad` vazio
    e subpastas utilitárias sem sobrescrever arquivos existentes.
    """
    base = get_project_context_paths(project_slug)
    if not base.get("ok"):
        return {**base, "created": []}

    root = Path(base["local_path_resolved"])
    squad = root / ".squad"
    created: list[str] = []

    if create_template_if_missing:
        before_ctx = (squad / "context.md").exists()
        project_service.ensure_squad_layout_for_project(root)
        if not before_ctx and (squad / "context.md").exists():
            created.append(str(squad / "context.md"))
        return {
            "ok": True,
            "error": None,
            "project_slug": base["project_slug"],
            "local_path_resolved": base["local_path_resolved"],
            "squad_dir": str(squad),
            "expected_context_path": base["expected_context_path"],
            "paths": base["paths"],
            "created": created,
        }

    squad.mkdir(parents=True, exist_ok=True)
    subdirs = (squad / "chats", squad / "runs", squad / "outputs")
    for d in subdirs:
        d.mkdir(parents=True, exist_ok=True)

    return {
        "ok": True,
        "error": None,
        "project_slug": base["project_slug"],
        "local_path_resolved": base["local_path_resolved"],
        "squad_dir": str(squad),
        "expected_context_path": base["expected_context_path"],
        "paths": base["paths"],
        "created": created,
    }


def _read_text_limited(path: Path, max_chars: int) -> tuple[str | None, str | None]:
    if not path.is_file():
        return None, None
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"{path}: {exc}"
    if len(raw) > max_chars:
        return raw[:max_chars] + "\n\n_[conteúdo truncado por limite interno]_\n", None
    return raw, None


def load_project_context(project_slug: str) -> dict[str, Any]:
    """Carrega arquivos conhecidos de contexto do projeto local."""
    base = get_project_context_paths(project_slug)
    out: dict[str, Any] = {
        "ok": base.get("ok", False),
        "error": base.get("error"),
        "project_slug": base.get("project_slug", ""),
        "project_root": base.get("local_path_resolved", ""),
        "files": {},
        "docs_markdown": [],
        "read_errors": [],
    }
    if not out["ok"]:
        return out

    root = Path(base["local_path_resolved"])
    paths = base["paths"]
    squad = root / ".squad"

    for key, rel_name in (
        ("context_md", "context.md"),
        ("roadmap_md", "roadmap.md"),
        ("decisions_md", "decisions.md"),
    ):
        p = squad / rel_name
        content, err = _read_text_limited(p, _MAX_README_CHARS)
        if err:
            out["read_errors"].append(err)
        out["files"][key] = {
            "path": str(p),
            "relative": f".squad/{rel_name}",
            "present": p.is_file(),
            "content": content,
        }

    backlog_path = squad / "backlog.json"
    backlog_content: str | None = None
    if backlog_path.is_file():
        try:
            backlog_raw = backlog_path.read_text(encoding="utf-8")
            if len(backlog_raw) > _MAX_README_CHARS:
                backlog_content = backlog_raw[:_MAX_README_CHARS] + "\n"
                out["read_errors"].append(f"{backlog_path}: backlog truncado por limite.")
            else:
                backlog_content = backlog_raw
            try:
                json.loads(backlog_content)
            except json.JSONDecodeError as exc:
                out["read_errors"].append(f"{backlog_path}: JSON inválido ({exc}).")
        except OSError as exc:
            out["read_errors"].append(f"{backlog_path}: {exc}")
    out["files"]["backlog_json"] = {
        "path": str(backlog_path),
        "relative": ".squad/backlog.json",
        "present": backlog_path.is_file(),
        "content": backlog_content,
    }

    readme = root / "README.md"
    r_content, r_err = _read_text_limited(readme, _MAX_README_CHARS)
    if r_err:
        out["read_errors"].append(r_err)
    out["files"]["readme_md"] = {
        "path": str(readme),
        "relative": "README.md",
        "present": readme.is_file(),
        "content": r_content,
    }

    docs_dir = root / "docs"
    if docs_dir.is_dir():
        md_files = sorted(docs_dir.rglob("*.md"))
        used = 0
        for p in md_files:
            if used >= _MAX_DOCS_FILES:
                out["read_errors"].append(
                    f"Pasta docs/: limite de {_MAX_DOCS_FILES} arquivos .md atingido; demais ignorados."
                )
                break
            rel = _posix_rel_under_project(root, p)
            content, err = _read_text_limited(p, _MAX_CHARS_PER_DOC_FILE)
            if err:
                out["read_errors"].append(err)
            if content is not None:
                out["docs_markdown"].append({"relative": rel, "content": content})
                used += 1

    return out


def build_project_context_markdown(project_slug: str) -> str:
    """Monta Markdown consolidado com tudo que foi carregado (para evidência e input)."""
    data = load_project_context(project_slug)
    lines: list[str] = [
        f"<!-- project_slug={data.get('project_slug', '')} project_root={data.get('project_root', '')} -->",
        "",
    ]
    if not data.get("ok"):
        lines.append(f"_Erro ao resolver projeto: {data.get('error')}_\n")
        return "\n".join(lines)

    files = data.get("files") or {}

    def _section(title: str, rel: str, content: str | None, present: bool) -> None:
        lines.append(f"## {title}")
        lines.append(f"_Arquivo: `{rel}` — presente: {present}_\n")
        if content:
            lines.append(content.strip())
            lines.append("")
        else:
            lines.append("_Arquivo ausente ou não legível._\n")

    ctx = files.get("context_md") or {}
    _section("`.squad/context.md`", str(ctx.get("relative", ".squad/context.md")), ctx.get("content"), bool(ctx.get("present")))

    rm = files.get("roadmap_md") or {}
    _section("`.squad/roadmap.md`", str(rm.get("relative", ".squad/roadmap.md")), rm.get("content"), bool(rm.get("present")))

    dec = files.get("decisions_md") or {}
    _section("`.squad/decisions.md`", str(dec.get("relative", ".squad/decisions.md")), dec.get("content"), bool(dec.get("present")))

    bl = files.get("backlog_json") or {}
    lines.append("## `.squad/backlog.json`")
    lines.append(f"_Arquivo: `{bl.get('relative', '.squad/backlog.json')}` — presente: {bool(bl.get('present'))}_\n")
    if bl.get("content"):
        lines.append("```json")
        lines.append(bl["content"].strip())
        lines.append("```\n")
    else:
        lines.append("_Arquivo ausente ou não legível._\n")

    rd = files.get("readme_md") or {}
    _section("`README.md`", str(rd.get("relative", "README.md")), rd.get("content"), bool(rd.get("present")))

    for doc in data.get("docs_markdown") or []:
        rel = doc.get("relative", "")
        lines.append(f"## `docs/` — `{rel}`\n")
        lines.append(doc.get("content", "").strip())
        lines.append("")

    if data.get("read_errors"):
        lines.append("## Avisos de leitura\n")
        for e in data["read_errors"]:
            lines.append(f"- {e}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def minimum_project_context_status(project_slug: str) -> tuple[bool, str | None, str | None]:
    """
    Valida contexto mínimo para executar meta/squad.

    Retorna (ok, mensagem_erro_pt, expected_context_path_abs).
    """
    base = get_project_context_paths(project_slug)
    if not base.get("ok"):
        exp = (base.get("expected_context_path") or "").strip()
        return False, base.get("error") or "Projeto inválido.", exp or None

    ctx_path = Path(base["expected_context_path"])
    if not ctx_path.is_file():
        return (
            False,
            MINIMUM_CONTEXT_USER_MESSAGE,
            str(ctx_path),
        )

    try:
        text = ctx_path.read_text(encoding="utf-8")
    except OSError as exc:
        return False, f"Não foi possível ler `.squad/context.md`: {exc}", str(ctx_path)

    stripped = text.strip()
    if len(stripped) < _CONTEXT_MIN_STRIP_LEN:
        return (
            False,
            MINIMUM_CONTEXT_USER_MESSAGE
            + f" O arquivo existe mas o conteúdo é curto demais (mínimo {_CONTEXT_MIN_STRIP_LEN} caracteres úteis).",
            str(ctx_path),
        )

    return True, None, str(ctx_path)


def expected_context_markdown_path_display(project_slug: str) -> str:
    """Caminho esperado de `.squad/context.md` para mensagens ao usuário (estilo Windows quando aplicável)."""
    _ok, _err, p = minimum_project_context_status(project_slug)
    if p:
        return p.replace("/", os.sep)
    base = get_project_context_paths(project_slug)
    exp = base.get("expected_context_path") or ""
    return str(exp).replace("/", os.sep)


def write_project_context_evidence(*, run_dir: Path, markdown_body: str) -> Path:
    """Grava `project-context-used.md` no diretório do run."""
    path = run_dir / PROJECT_CONTEXT_EVIDENCE_FILENAME
    path.write_text(markdown_body.strip() + "\n", encoding="utf-8")
    return path


def project_context_evidence_posix(project_slug: str, run_id: str) -> str:
    slug = (project_slug or "").strip().lower()
    rid = (run_id or "").strip()
    return f"runs/{slug}/{rid}/{PROJECT_CONTEXT_EVIDENCE_FILENAME}"


def ensure_run_project_context_evidence(
    *,
    project_slug: str,
    run_id: str,
    repo_root: Path | None = None,
) -> tuple[bool, str | None, str | None]:
    """
    Garante que `runs/<slug>/<run_id>/project-context-used.md` exista; gera a partir do
    contexto atual se faltar. Valida contexto mínimo antes.

    Retorna (ok, error_message, evidence_path_posix).
    """
    ok, err, _ctx_abs = minimum_project_context_status(project_slug)
    if not ok:
        return False, err, None

    root = repo_root or get_repo_root()
    slug = (project_slug or "").strip().lower()
    rid = (run_id or "").strip()
    run_dir = root / "runs" / slug / rid
    evidence = run_dir / PROJECT_CONTEXT_EVIDENCE_FILENAME

    if not evidence.is_file():
        md = build_project_context_markdown(project_slug)
        try:
            run_dir.mkdir(parents=True, exist_ok=True)
            write_project_context_evidence(run_dir=run_dir, markdown_body=md)
        except OSError as exc:
            return False, f"Não foi possível gravar evidência de contexto: {exc}", None

    rel = project_context_evidence_posix(slug, rid)
    return True, None, rel


def build_input_with_project_context(*, demand_header: str, user_message: str, project_context_md: str) -> str:
    """Compõe o conteúdo de `input.md` com seção de contexto + demanda."""
    ctx_block = project_context_md.strip()
    body = (user_message or "").strip()
    return (
        f"{demand_header}"
        "# Contexto do Projeto Selecionado\n\n"
        f"{ctx_block}\n\n"
        "---\n\n"
        f"{body}\n"
    )


def build_squad_run_context_bundle(
    project_slug: str,
    *,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """
    Textos para o prompt da squad CAP nos scripts (`run_squad.py`, `prepare_run.py`).

    Combina documentação fixa do repositório com ficheiros em `<local_path>/.squad/`
    resolvidos via SQLite (`get_project_context_paths`).

    Chaves e ordem são estáveis (dict ordenado) para o mesmo formato que o CLI já usava.
    """
    root = (repo_root or get_repo_root()).resolve()
    base = get_project_context_paths(project_slug)
    if not base.get("ok"):
        raise ValueError(
            f"Não foi possível resolver o projeto {project_slug!r} no cadastro: {base.get('error')}"
        )
    squad = Path(base["local_path_resolved"]) / ".squad"

    def slurp_file(path: Path, *, label: str, required: bool) -> str:
        if not path.is_file():
            if required:
                raise ValueError(f"Arquivo de {label} não encontrado: {path}")
            return f"_(Arquivo opcional ausente: `{path}`.)_\n"
        try:
            return path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"Não foi possível ler {label} ({path}): {exc}") from exc

    out: dict[str, str] = {}

    out["fonte oficial"] = slurp_file(
        root / "docs" / "00-fonte-oficial.md",
        label="fonte oficial",
        required=True,
    )
    out["organização dos projetos prioritários"] = slurp_file(
        root / "docs" / "01-organizacao-projetos-prioritarios.md",
        label="organização dos projetos prioritários",
        required=True,
    )
    out["contexto CAP"] = slurp_file(squad / "context.md", label="contexto CAP", required=True)
    out["standards CAP"] = slurp_file(squad / "standards.md", label="standards CAP", required=False)
    out["decisions CAP"] = slurp_file(squad / "decisions.md", label="decisions CAP", required=False)

    bl_json = squad / "backlog.json"
    bl_md = squad / "backlog.md"
    if bl_json.is_file():
        out["backlog CAP"] = slurp_file(bl_json, label="backlog CAP", required=False)
    elif bl_md.is_file():
        out["backlog CAP"] = slurp_file(bl_md, label="backlog CAP", required=False)
    else:
        out["backlog CAP"] = (
            f"_(Nenhum ficheiro `backlog.json` nem `backlog.md` em `{squad}`.)_\n"
        )

    out["workflow da squad CAP"] = slurp_file(
        root / "squads" / "cap" / "workflow.md",
        label="workflow da squad CAP",
        required=True,
    )
    out["task-policy da squad CAP"] = slurp_file(
        root / "squads" / "cap" / "task-policy.md",
        label="task-policy da squad CAP",
        required=True,
    )
    return out
