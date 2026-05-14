"""Execução da squad completa via `scripts/run_squad.py` (sem flags extras)."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from core.projects import project_context_service


from core.config import get_repo_root


def _repo_root() -> Path:
    return get_repo_root()


@dataclass(frozen=True)
class FullSquadRunResult:
    ok: bool
    exit_code: int | None
    stdout: str
    stderr: str
    final_markdown: str | None
    error_detail: str | None


def run_full_squad(
    *,
    project_slug: str,
    run_id: str,
    subprocess_timeout_sec: int = 7200,
) -> FullSquadRunResult:
    """
    Executa `python scripts/run_squad.py <slug> runs/<slug>/<run_id>/input.md`
    (fluxo completo PO → … → QA). Não usa `--write-real-files` nem `--agent`.
    """
    slug = (project_slug or "").strip().lower()
    rid = (run_id or "").strip()
    root = _repo_root()
    run_path_posix = f"runs/{slug}/{rid}"
    input_rel = f"{run_path_posix}/input.md"
    input_path = root / input_rel.replace("/", os.sep)
    if not input_path.is_file():
        return FullSquadRunResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            final_markdown=None,
            error_detail=f"Arquivo de entrada não encontrado: {input_path}",
        )

    run_dir = root / "runs" / slug / rid
    ev_ok, ev_err, _ev_rel = project_context_service.ensure_run_project_context_evidence(
        project_slug=slug,
        run_id=rid,
        repo_root=root,
    )
    if not ev_ok:
        return FullSquadRunResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            final_markdown=None,
            error_detail=ev_err or "Contexto mínimo do projeto ausente ou inválido.",
        )

    evidence_path = run_dir / project_context_service.PROJECT_CONTEXT_EVIDENCE_FILENAME
    if not evidence_path.is_file():
        return FullSquadRunResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            final_markdown=None,
            error_detail=(
                f"Evidência de contexto ausente: `{evidence_path}` "
                "(esperado após carregar o contexto do projeto)."
            ),
        )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return FullSquadRunResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            final_markdown=None,
            error_detail="OPENAI_API_KEY ausente ou vazia.",
        )

    cmd = [
        sys.executable,
        str(root / "scripts" / "run_squad.py"),
        slug,
        input_rel,
    ]

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
        return FullSquadRunResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            final_markdown=None,
            error_detail=(
                f"Tempo limite ({subprocess_timeout_sec}s) excedido na execução da squad completa."
            ),
        )
    except OSError as exc:
        return FullSquadRunResult(
            ok=False,
            exit_code=None,
            stdout="",
            stderr="",
            final_markdown=None,
            error_detail=f"Falha ao iniciar subprocesso: {exc}",
        )

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    final_path = run_dir / "final.md"
    final_md: str | None = None
    if final_path.is_file():
        try:
            final_md = final_path.read_text(encoding="utf-8").strip()
        except OSError as exc:
            return FullSquadRunResult(
                ok=False,
                exit_code=proc.returncode,
                stdout=stdout,
                stderr=stderr,
                final_markdown=None,
                error_detail=f"Não foi possível ler final.md: {exc}",
            )

    if proc.returncode != 0:
        tail = (stderr.strip() or stdout.strip() or "(sem saída)").splitlines()
        brief = "\n".join(tail[-40:])
        return FullSquadRunResult(
            ok=False,
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            final_markdown=final_md,
            error_detail=(
                f"A squad encerrou com exit_code={proc.returncode}.\n\n```\n{brief}\n```"
            ),
        )

    if not final_md:
        return FullSquadRunResult(
            ok=False,
            exit_code=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            final_markdown=None,
            error_detail=f"Execução retornou 0, mas final.md não foi encontrado em `{run_dir}`.",
        )

    return FullSquadRunResult(
        ok=True,
        exit_code=proc.returncode,
        stdout=stdout,
        stderr=stderr,
        final_markdown=final_md,
        error_detail=None,
    )
