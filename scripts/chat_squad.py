"""
Interface conversacional local para o meta-orquestrador (squad-agentes).

Uso (na raiz do repositório):
    python scripts/chat_squad.py
"""

from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPTS_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from prepare_run import prepare_cap_run_json_forced_slug  # noqa: E402

ROOT = _REPO_ROOT

EXIT_WORDS = frozenset({"sair", "exit", "quit"})
VALID_MODES = frozenset({"markdown", "json_prepare_run"})


def _slug_from_demanda(text: str, max_len: int = 36) -> str:
    s = unicodedata.normalize("NFKD", text)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        return "demanda"
    s = s[:max_len].rstrip("-")
    return s or "demanda"


def _new_run_id(demanda: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{_slug_from_demanda(demanda)}"


def _build_input_markdown(demanda: str) -> str:
    return f"# Demanda\n\n{demanda.strip()}\n"


def _ensure_project_supported(project: str) -> bool:
    p = project.strip().lower()
    if p != "cap":
        print(
            f"Erro: projeto não suportado: {project!r}. Nesta fase apenas 'cap' é aceito.",
            file=sys.stderr,
        )
        return False
    return True


def _parse_modo_command(line: str) -> str | None:
    m = re.match(r"^\s*modo\s+(\S+)\s*$", line, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip().lower()


def _parse_projeto_command(line: str) -> str | None:
    m = re.match(r"^\s*projeto\s+(\S+)\s*$", line, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).strip().lower()


def _run_meta_orchestrator_markdown(*, project: str, input_rel: str) -> tuple[int, str, str]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "run_squad.py"),
        project,
        input_rel,
        "--agent",
        "meta-orchestrator",
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def _print_run_summary(
    *,
    demanda: str,
    project: str,
    mode: str,
    run_id: str,
    input_path: Path,
    final_path: Path | None,
    status: str,
    meta_output_path: Path | None = None,
) -> None:
    print()
    print("—" * 48)
    print(f"Demanda recebida: {demanda.strip()[:500]}{'…' if len(demanda.strip()) > 500 else ''}")
    print(f"Projeto: {project}")
    print(f"Modo: {mode}")
    print(f"Run ID: {run_id}")
    print(f"Arquivo de entrada: {input_path.resolve()}")
    if mode == "markdown":
        if final_path is not None:
            if final_path.is_file():
                print(f"Arquivo final: {final_path.name}")
                print(f"  {final_path.resolve()}")
            else:
                print(f"Arquivo final: {final_path.name} (ausente ou incompleto)")
                print(f"  {final_path.resolve()}")
        else:
            print("Arquivo final: (não aplicável)")
    elif mode == "json_prepare_run":
        if meta_output_path is not None:
            print(f"Arquivo de preparação: {meta_output_path.name}")
            print(f"  {meta_output_path.resolve()}")
        else:
            print("Arquivo de preparação: (não aplicável)")
    print(f"Status da execução: {status}")
    print("—" * 48)
    print()


def _session_banner(project: str, mode: str) -> None:
    print()
    print("Squad Agentes — Interface Conversacional")
    print(f"Projeto atual: {project}")
    print(f"Modo atual: {mode}")
    print()
    print("Digite a demanda em linguagem natural, ou um comando:")
    print("  projeto <nome>     (padrão: cap)")
    print("  modo markdown      (plano em Markdown via run_squad.py)")
    print("  modo json_prepare_run   (prepara input via prepare_run / JSON)")
    print("  sair | exit | quit")
    print()


def main() -> None:
    project = "cap"
    mode = "markdown"

    _session_banner(project, mode)

    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            raise SystemExit(130) from None

        if not line:
            continue

        low = line.lower()
        if low in EXIT_WORDS:
            print("Até logo.")
            return

        parsed_projeto = _parse_projeto_command(line)
        if parsed_projeto is not None:
            project = parsed_projeto
            if not _ensure_project_supported(project):
                project = "cap"
            print(f"Projeto atual: {project}")
            continue

        parsed_modo = _parse_modo_command(line)
        if parsed_modo is not None:
            if parsed_modo not in VALID_MODES:
                print(
                    f"Erro: modo inválido {parsed_modo!r}. Use: markdown ou json_prepare_run.",
                    file=sys.stderr,
                )
                continue
            mode = parsed_modo
            print(f"Modo atual: {mode}")
            continue

        if not _ensure_project_supported(project):
            project = "cap"
            print("Projeto revertido para 'cap' (único suportado nesta fase).")
            continue

        demanda = line
        run_id = _new_run_id(demanda)

        display_project = "cap" if mode == "json_prepare_run" else project

        if mode == "markdown":
            run_dir = ROOT / "runs" / project / run_id
            input_path = run_dir / "input.md"

            try:
                run_dir.mkdir(parents=True, exist_ok=False)
            except FileExistsError:
                print(
                    f"Erro: pasta do run já existe (colisão de ID). Tente novamente: {run_dir}",
                    file=sys.stderr,
                )
                continue
            except OSError as exc:
                print(f"Erro: não foi possível criar a pasta do run: {exc}", file=sys.stderr)
                continue

            try:
                input_path.write_text(_build_input_markdown(demanda), encoding="utf-8")
            except OSError as exc:
                print(f"Erro: não foi possível gravar input.md: {exc}", file=sys.stderr)
                try:
                    run_dir.rmdir()
                except OSError:
                    pass
                continue

            input_rel = input_path.relative_to(ROOT).as_posix()
            code, out, err = _run_meta_orchestrator_markdown(project=project, input_rel=input_rel)
            if out.strip():
                print(out.rstrip())
            if err.strip():
                print(err.rstrip(), file=sys.stderr)

            final_path = run_dir / "final.md"
            status = "sucesso" if code == 0 else f"falha (código {code})"
            _print_run_summary(
                demanda=demanda,
                project=display_project,
                mode=mode,
                run_id=run_id,
                input_path=input_path,
                final_path=final_path,
                status=status,
            )
            if code != 0:
                print(
                    "Observação: verifique mensagens acima. Arquivos parciais podem existir na pasta do run.",
                    file=sys.stderr,
                )
            continue

        # json_prepare_run — prepare_run.py cria runs/cap/{run_id}/ (projeto fixo cap no preparador)
        try:
            input_written, meta_path = prepare_cap_run_json_forced_slug(
                demanda=demanda,
                run_slug=run_id,
            )
        except SystemExit:
            print("Status da execução: falha (preparação JSON abortada).", file=sys.stderr)
            continue

        _print_run_summary(
            demanda=demanda,
            project=display_project,
            mode=mode,
            run_id=run_id,
            input_path=input_written,
            final_path=None,
            status="sucesso (input estruturado pelo modelo)",
            meta_output_path=meta_path,
        )
        print(
            "Próximo passo sugerido (execução da squad completa ou revisão):\n"
            f"  python scripts/run_squad.py cap {input_written.relative_to(ROOT).as_posix()}\n"
        )


if __name__ == "__main__":
    main()
