"""Invocação do meta-orquestrador via `scripts/run_squad.py` (subprocess na raiz do repo)."""

from __future__ import annotations

import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

from core.projects import project_context_service


from core.config import get_repo_root


def _repo_root() -> Path:
    return get_repo_root()


SUPPORTED_META_PROJECT_SLUGS = frozenset({"cap"})

MISSING_OPENAI_MESSAGE = (
    "Configure a variável de ambiente OPENAI_API_KEY (chave da OpenAI) "
    "antes de executar o meta-orquestrador."
)

UNSUPPORTED_PROJECT_MESSAGE = (
    "Projeto ainda não suportado para execução do meta-orquestrador."
)


@dataclass(frozen=True)
class MetaOrchestratorRunResult:
    ok: bool
    run_id: str
    run_path_posix: str
    markdown: str
    exit_code: int | None
    stdout: str
    stderr: str
    error_detail: str | None
    context_loaded: bool = False
    context_evidence_path: str | None = None


def _new_run_id() -> str:
    return f"web-{uuid.uuid4().hex[:16]}"


def _read_markdown_from_run_dir(run_dir: Path) -> tuple[str | None, str | None]:
    """Preferência: meta-orchestrator-output.md, depois final.md."""
    meta_path = run_dir / "meta-orchestrator-output.md"
    if meta_path.is_file():
        try:
            return meta_path.read_text(encoding="utf-8").strip(), "meta-orchestrator-output.md"
        except OSError:
            pass
    final_path = run_dir / "final.md"
    if final_path.is_file():
        try:
            return final_path.read_text(encoding="utf-8").strip(), "final.md"
        except OSError:
            pass
    return None, None


def run_meta_orchestrator(
    *,
    project_slug: str,
    chat_id: int,
    user_message: str,
    subprocess_timeout_sec: int = 900,
) -> MetaOrchestratorRunResult:
    """
    Cria `runs/<slug>/<run_id>/input.md` (com seção **Contexto do Projeto Selecionado**),
    grava `project-context-used.md`, executa apenas o meta-orquestrador e devolve o Markdown.
    Não altera `run_squad.py`: delega integralmente ao CLI existente.
    """
    slug = (project_slug or "").strip().lower()
    if slug not in SUPPORTED_META_PROJECT_SLUGS:
        return MetaOrchestratorRunResult(
            ok=False,
            run_id="",
            run_path_posix="",
            markdown="",
            exit_code=None,
            stdout="",
            stderr="",
            error_detail=UNSUPPORTED_PROJECT_MESSAGE,
            context_loaded=False,
            context_evidence_path=None,
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return MetaOrchestratorRunResult(
            ok=False,
            run_id="",
            run_path_posix="",
            markdown="",
            exit_code=None,
            stdout="",
            stderr="",
            error_detail=MISSING_OPENAI_MESSAGE,
            context_loaded=False,
            context_evidence_path=None,
        )

    ctx_ok, ctx_err, ctx_path_hint = project_context_service.minimum_project_context_status(slug)
    if not ctx_ok:
        path_line = ""
        if ctx_path_hint:
            path_line = (
                "\n\nArquivo esperado (preencha no disco local):\n\n`"
                + ctx_path_hint.replace("/", os.sep)
                + "`"
            )
        return MetaOrchestratorRunResult(
            ok=False,
            run_id="",
            run_path_posix="",
            markdown="",
            exit_code=None,
            stdout="",
            stderr="",
            error_detail=(ctx_err or project_context_service.MINIMUM_CONTEXT_USER_MESSAGE) + path_line,
            context_loaded=False,
            context_evidence_path=None,
        )

    root = _repo_root()
    run_id = _new_run_id()
    run_dir = root / "runs" / slug / run_id
    run_path_posix = f"runs/{slug}/{run_id}"
    evidence_posix = project_context_service.project_context_evidence_posix(slug, run_id)
    try:
        run_dir.mkdir(parents=True, exist_ok=True)
        ctx_md = project_context_service.build_project_context_markdown(slug)
        project_context_service.write_project_context_evidence(
            run_dir=run_dir,
            markdown_body=ctx_md,
        )
        input_path = run_dir / "input.md"
        header = (
            f"# Demanda (chat_id={chat_id})\n\n"
            "Esta demanda foi enviada pela interface web local (squad-agentes).\n\n"
        )
        input_body = project_context_service.build_input_with_project_context(
            demand_header=header,
            user_message=user_message or "",
            project_context_md=ctx_md,
        )
        input_path.write_text(input_body, encoding="utf-8")
    except OSError as exc:
        return MetaOrchestratorRunResult(
            ok=False,
            run_id=run_id,
            run_path_posix=run_path_posix,
            markdown="",
            exit_code=None,
            stdout="",
            stderr="",
            error_detail=f"Não foi possível preparar o diretório do run: {exc}",
            context_loaded=False,
            context_evidence_path=None,
        )

    input_rel = f"{run_path_posix}/input.md"
    cmd = [
        sys.executable,
        str(root / "scripts" / "run_squad.py"),
        slug,
        input_rel,
        "--agent",
        "meta-orchestrator",
    ]

    ctx_loaded = True

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=subprocess_timeout_sec,
            env=os.environ.copy(),
        )
    except subprocess.TimeoutExpired:
        return MetaOrchestratorRunResult(
            ok=False,
            run_id=run_id,
            run_path_posix=run_path_posix,
            markdown="",
            exit_code=None,
            stdout="",
            stderr="",
            error_detail=(
                f"Tempo limite ({subprocess_timeout_sec}s) excedido ao executar o meta-orquestrador."
            ),
            context_loaded=ctx_loaded,
            context_evidence_path=evidence_posix,
        )
    except OSError as exc:
        return MetaOrchestratorRunResult(
            ok=False,
            run_id=run_id,
            run_path_posix=run_path_posix,
            markdown="",
            exit_code=None,
            stdout="",
            stderr="",
            error_detail=f"Falha ao iniciar subprocesso do orquestrador: {exc}",
            context_loaded=ctx_loaded,
            context_evidence_path=evidence_posix,
        )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    if proc.returncode != 0:
        tail = (stderr.strip() or stdout.strip() or "(sem saída)").splitlines()
        brief = "\n".join(tail[-40:])
        return MetaOrchestratorRunResult(
            ok=False,
            run_id=run_id,
            run_path_posix=run_path_posix,
            markdown="",
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            error_detail=(
                "O meta-orquestrador encerrou com erro.\n\n"
                f"exit_code={proc.returncode}\n\n```\n{brief}\n```"
            ),
            context_loaded=ctx_loaded,
            context_evidence_path=evidence_posix,
        )

    md, _source = _read_markdown_from_run_dir(run_dir)
    if not md:
        return MetaOrchestratorRunResult(
            ok=False,
            run_id=run_id,
            run_path_posix=run_path_posix,
            markdown="",
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            error_detail=(
                "Execução concluída, mas não foi encontrado `meta-orchestrator-output.md` nem `final.md` "
                f"em `{run_dir}`."
            ),
            context_loaded=ctx_loaded,
            context_evidence_path=evidence_posix,
        )

    return MetaOrchestratorRunResult(
        ok=True,
        run_id=run_id,
        run_path_posix=run_path_posix,
        markdown=md,
        exit_code=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        error_detail=None,
        context_loaded=ctx_loaded,
        context_evidence_path=evidence_posix,
    )
