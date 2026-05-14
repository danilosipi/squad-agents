"""
Prepara um novo run a partir de demanda em linguagem natural (meta-orquestrador).

Uso (na raiz do repositório):
    python scripts/prepare_run.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Dependência 'openai' não encontrada. Instale com: pip install -r requirements.txt"
    ) from exc


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.projects import project_context_service

AGENT_PATH = ROOT / "agents" / "meta-orchestrator.md"

# Legado: 001-cap-base-database. Chat: 20260512-143055-slug-curto (UTC).
RUN_SLUG_RE_LEGACY = re.compile(r"^[0-9]{3}-[a-z0-9-]+$")
RUN_SLUG_RE_CHAT = re.compile(r"^\d{8}-\d{6}-[a-z0-9-]+$")
JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n([\s\S]*?)```", re.IGNORECASE)


def _is_valid_run_slug(run_slug: str) -> bool:
    return bool(RUN_SLUG_RE_LEGACY.fullmatch(run_slug) or RUN_SLUG_RE_CHAT.fullmatch(run_slug))


def _die(message: str, code: int = 1) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(code)


def _read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        _die(f"Erro: arquivo de {label} não encontrado: {path}")
    except OSError as exc:
        _die(f"Erro: não foi possível ler {label} ({path}): {exc}")


def _load_context_bundle() -> str:
    try:
        bundle = project_context_service.build_squad_run_context_bundle("cap", repo_root=ROOT)
    except ValueError as exc:
        _die(str(exc))
    order = [
        "fonte oficial",
        "contexto CAP",
        "backlog CAP",
        "decisions CAP",
        "standards CAP",
    ]
    parts: list[str] = []
    for label in order:
        parts.append(f"## {label.upper()}\n\n{bundle[label].strip()}\n")
    return "\n".join(parts)


def _list_existing_run_slugs() -> list[str]:
    runs_dir = ROOT / "runs" / "cap"
    if not runs_dir.is_dir():
        return []
    return sorted(
        path.name
        for path in runs_dir.iterdir()
        if path.is_dir()
    )


def _next_run_sequence(existing: list[str]) -> int:
    max_seq = 0
    for slug in existing:
        match = re.match(r"^(\d+)", slug)
        if match:
            max_seq = max(max_seq, int(match.group(1)))
    return max_seq + 1


def _build_user_prompt(*, demanda: str, shared_context: str, existing_runs: list[str], next_seq: int) -> str:
    existing_block = (
        "\n".join(f"- {slug}" for slug in existing_runs) if existing_runs else "- (nenhum run ainda)"
    )
    return (
        "Use o contexto abaixo e a demanda do Danilo para preparar o próximo run da squad CAP.\n\n"
        f"{shared_context}\n\n"
        "## RUNS EXISTENTES EM runs/cap/\n\n"
        f"{existing_block}\n\n"
        f"Próximo número sequencial sugerido: {next_seq:03d}.\n\n"
        "## DEMANDA DO DANILO\n\n"
        f"{demanda.strip()}\n\n"
        "Responda somente com JSON estrito no formato exigido pelo meta-orquestrador "
        "(project, run_slug, title, input_markdown, command_to_run). "
        "Não execute nada; apenas prepare a próxima execução."
    )


def _call_meta_orchestrator(*, client: OpenAI, model: str, system: str, user_prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_prompt},
            ],
        )
    except APIConnectionError as exc:
        _die(f"Erro na chamada OpenAI (conexão): {exc}")
    except RateLimitError as exc:
        _die(f"Erro na chamada OpenAI (rate limit): {exc}")
    except APIStatusError as exc:
        _die(f"Erro na chamada OpenAI (HTTP {exc.status_code}): {exc}")
    except Exception as exc:  # pragma: no cover
        _die(f"Erro inesperado na chamada OpenAI: {exc}")

    content = response.choices[0].message.content
    if content is None:
        _die("Erro na chamada OpenAI: resposta sem conteúdo (content vazio).")
    return content.strip()


def _parse_json_response(raw: str) -> dict:
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        match = JSON_FENCE_RE.search(raw)
        if not match:
            _die("Erro: resposta do modelo não é JSON válido.")
        try:
            parsed = json.loads(match.group(1).strip())
        except json.JSONDecodeError as exc:
            _die(f"Erro: JSON inválido na resposta do modelo: {exc}")

    if not isinstance(parsed, dict):
        _die("Erro: resposta do modelo deve ser um objeto JSON.")
    return parsed


def _validate_prepared_run(data: dict) -> None:
    required = ("project", "run_slug", "title", "input_markdown", "command_to_run")
    missing = [key for key in required if key not in data]
    if missing:
        _die(f"Erro: JSON incompleto. Campos ausentes: {', '.join(missing)}.")

    project = str(data["project"]).strip().lower()
    if project != "cap":
        _die(f"Erro: project inválido {project!r}. Nesta fase apenas 'cap' é suportado.")

    run_slug = str(data["run_slug"]).strip()
    if not _is_valid_run_slug(run_slug):
        _die(
            "Erro: run_slug inválido. Use o padrão NNN-... (legado) ou "
            "YYYYMMDD-HHMMSS-slug (interface chat), com letras minúsculas, números e hífens."
        )

    input_markdown = str(data["input_markdown"]).strip()
    if not input_markdown:
        _die("Erro: input_markdown não pode estar vazio.")

    expected_input = f"runs/cap/{run_slug}/input.md"
    command_to_run = str(data["command_to_run"]).strip()
    if expected_input not in command_to_run.replace("\\", "/"):
        _die(
            "Erro: command_to_run deve apontar para o input criado "
            f"({expected_input})."
        )


def _write_meta_output(*, run_dir: Path, demanda: str, data: dict) -> None:
    body = (
        "# Meta-orquestrador — saída\n\n"
        "## Demanda original\n\n"
        f"{demanda.strip()}\n\n"
        "## JSON retornado\n\n"
        "```json\n"
        f"{json.dumps(data, ensure_ascii=False, indent=2)}\n"
        "```\n"
    )
    (run_dir / "meta-output.md").write_text(body, encoding="utf-8")


def _load_openai_client_and_model() -> tuple[OpenAI, str]:
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        _die("Erro: variável de ambiente OPENAI_API_KEY ausente ou vazia.")
    model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4o-mini"
    return OpenAI(api_key=api_key), model


def _build_user_prompt_with_fixed_slug(
    *,
    demanda: str,
    shared_context: str,
    existing_runs: list[str],
    next_seq: int,
    forced_run_slug: str,
) -> str:
    base = _build_user_prompt(
        demanda=demanda,
        shared_context=shared_context,
        existing_runs=existing_runs,
        next_seq=next_seq,
    )
    fixed_cmd = f"python scripts/run_squad.py cap runs/cap/{forced_run_slug}/input.md"
    return (
        f"{base}\n\n"
        "## SLUG E COMANDO FIXOS (interface conversacional)\n\n"
        f"- O campo `run_slug` no JSON deve ser exatamente: `{forced_run_slug}`.\n"
        f"- O campo `project` no JSON deve ser exatamente: `cap`.\n"
        f"- O campo `command_to_run` no JSON deve ser exatamente: `{fixed_cmd}`.\n"
    )


def prepare_cap_run_json_forced_slug(*, demanda: str, run_slug: str) -> tuple[Path, Path]:
    """
    Prepara `runs/cap/{run_slug}/` com `input.md` e `meta-output.md` via meta-orquestrador (JSON).

    O slug deve passar em `_is_valid_run_slug` (inclui o formato `YYYYMMDD-HHMMSS-slug` da chat).

    Em caso de erro, chama `_die` (SystemExit). Destinado a ser invocado por `chat_squad.py`.
    """
    if not demanda.strip():
        _die("Erro: demanda vazia.")
    if not _is_valid_run_slug(run_slug):
        _die(
            "Erro: run_slug inválido. Use o padrão legado `NNN-...` ou o formato chat "
            f"`YYYYMMDD-HHMMSS-slug`. Recebido: {run_slug!r}."
        )

    run_dir = ROOT / "runs" / "cap" / run_slug
    if run_dir.exists():
        _die(f"Erro: run já existe e não será sobrescrito: {run_dir.relative_to(ROOT)}")

    client, model = _load_openai_client_and_model()
    agent_instructions = _read_text(AGENT_PATH, "meta-orquestrador")
    shared_context = _load_context_bundle()
    existing_runs = _list_existing_run_slugs()
    next_seq = _next_run_sequence(existing_runs)

    user_prompt = _build_user_prompt_with_fixed_slug(
        demanda=demanda,
        shared_context=shared_context,
        existing_runs=existing_runs,
        next_seq=next_seq,
        forced_run_slug=run_slug,
    )
    system = (
        "Você é o Meta-Orquestrador do squad-agentes. "
        "Siga estritamente as instruções abaixo.\n\n"
        f"{agent_instructions.strip()}"
    )

    raw_response = _call_meta_orchestrator(
        client=client,
        model=model,
        system=system,
        user_prompt=user_prompt,
    )
    data = _parse_json_response(raw_response)

    fixed_cmd = f"python scripts/run_squad.py cap runs/cap/{run_slug}/input.md"
    data["run_slug"] = run_slug
    data["project"] = "cap"
    data["command_to_run"] = fixed_cmd

    _validate_prepared_run(data)

    run_dir.mkdir(parents=True, exist_ok=False)
    input_path = run_dir / "input.md"
    input_path.write_text(str(data["input_markdown"]).strip() + "\n", encoding="utf-8")
    _write_meta_output(run_dir=run_dir, demanda=demanda, data=data)
    meta_path = run_dir / "meta-output.md"
    return input_path, meta_path


def main() -> None:
    client, model = _load_openai_client_and_model()

    agent_instructions = _read_text(AGENT_PATH, "meta-orquestrador")
    shared_context = _load_context_bundle()
    existing_runs = _list_existing_run_slugs()
    next_seq = _next_run_sequence(existing_runs)

    try:
        demanda = input("Descreva a demanda: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        _die("Operação cancelada.", code=130)

    if not demanda:
        _die("Erro: demanda vazia.")

    user_prompt = _build_user_prompt(
        demanda=demanda,
        shared_context=shared_context,
        existing_runs=existing_runs,
        next_seq=next_seq,
    )
    system = (
        "Você é o Meta-Orquestrador do squad-agentes. "
        "Siga estritamente as instruções abaixo.\n\n"
        f"{agent_instructions.strip()}"
    )

    raw_response = _call_meta_orchestrator(
        client=client,
        model=model,
        system=system,
        user_prompt=user_prompt,
    )
    data = _parse_json_response(raw_response)
    _validate_prepared_run(data)

    run_slug = str(data["run_slug"]).strip()
    run_dir = ROOT / "runs" / "cap" / run_slug
    if run_dir.exists():
        _die(f"Erro: run já existe e não será sobrescrito: {run_dir.relative_to(ROOT)}")

    run_dir.mkdir(parents=True, exist_ok=False)
    input_path = run_dir / "input.md"
    input_path.write_text(str(data["input_markdown"]).strip() + "\n", encoding="utf-8")
    _write_meta_output(run_dir=run_dir, demanda=demanda, data=data)

    rel_run = run_dir.relative_to(ROOT).as_posix()
    rel_input = input_path.relative_to(ROOT).as_posix()
    command_to_run = str(data["command_to_run"]).strip()

    print(f"Run criado:\n{rel_run}\n")
    print(f"Input:\n{rel_input}\n")
    print(f"Para executar:\n{command_to_run}")


if __name__ == "__main__":
    main()
