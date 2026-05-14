"""
Orquestrador da squad CAP via OpenAI API (primeira versão funcional).

Uso (na raiz do repositório):
    python scripts/run_squad.py cap runs/cap/001-cap-base-database/input.md
    python scripts/run_squad.py cap runs/cap/001-cap-base-database/input.md --write-files
    python scripts/run_squad.py cap runs/cap/001-cap-base-database/input.md --validate-existing
    python scripts/run_squad.py cap runs/cap/002-cap-base-domain/input.md --validate-existing
    python scripts/run_squad.py cap runs/cap/003-cap-base-repository-contracts/input.md --write-files
    python scripts/run_squad.py cap runs/cap/003-cap-base-repository-contracts/input.md --validate-existing
    python scripts/run_squad.py cap runs/cap/004-meta-orchestrator/input.md --agent meta-orchestrator
    python scripts/run_squad.py cap runs/cap/005-real-file-creation/input.md
    python scripts/run_squad.py cap runs/cap/005-real-file-creation/input.md --write-real-files
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

try:
    from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Dependência 'openai' não encontrada. Instale com: pip install -r requirements.txt"
    ) from exc


import file_writer

ROOT = Path(__file__).resolve().parents[1]

CAP_BASE_PRISMA_PATH = (
    ROOT.parent / "cap-platform" / "repos" / "cap-base" / "prisma" / "base.prisma"
)

REQUIRED_MODELS: list[str] = [
    "Organization",
    "OrganizationType",
    "OrganizationStatus",
    "OrganizationRole",
    "OrganizationRoleAssignment",
    "User",
    "UserStatus",
    "Role",
    "Permission",
    "RolePermission",
    "UserOrganization",
    "Address",
    "AddressType",
    "Contact",
    "ContactType",
    "Document",
    "DocumentType",
    "SystemParameter",
    "SystemParameterType",
    "SystemParameterScope",
    "AuditLog",
    "AuditActionType",
    "AuditEntityType",
]

FORBIDDEN_MODELS: list[str] = [
    "UserRole",
    "OrganizationPermission",
    "UserPermission",
    "Product",
    "Plan",
    "Drawing",
    "Promotion",
    "FinancialEntry",
    "LuckyNumber",
]

FORBIDDEN_TERM_PATTERNS: list[tuple[str, str]] = [
    ("password", r"\bpassword\b"),
    ("passwordHash", r"\bpasswordHash\b"),
    ("refreshToken", r"\brefreshToken\b"),
    ("resetToken", r"\bresetToken\b"),
    ("token", r"\btoken\b"),
]

# Padrões determinísticos — reduzir falsos positivos (ex.: "similarity").
PLACEHOLDER_RULES: list[tuple[str, str]] = [
    ("continuação", r"\bcontinuação\b"),
    ("demais models", r"demais\s+models"),
    ("similar", r"\bsimilar\b"),
    ("etc.", r"\betc\."),
    ("...", r"\.\.\."),
    ("other models", r"other\s+models"),
    ("restante do schema", r"restante\s+do\s+schema"),
]

PATH_MARKERS: tuple[str, ...] = (
    "../cap-platform/repos/cap-base/prisma/base.prisma",
    "cap-platform/repos/cap-base/prisma/base.prisma",
)

CAP_BASE_ROOT_PATH = ROOT.parent / "cap-platform" / "repos" / "cap-base"
CAP_BASE_SRC_PATH = CAP_BASE_ROOT_PATH / "src"
CAP_BASE_DOMAIN_PATH = CAP_BASE_SRC_PATH / "domain"
CAP_BASE_DOMAIN_ENTITIES_PATH = CAP_BASE_DOMAIN_PATH / "entities"
CAP_BASE_REPOSITORIES_PATH = CAP_BASE_DOMAIN_PATH / "repositories"
CAP_BASE_SRC_INDEX_PATH = CAP_BASE_SRC_PATH / "index.ts"
CAP_BASE_DOMAIN_INDEX_PATH = CAP_BASE_DOMAIN_PATH / "index.ts"
CAP_PLATFORM_ROOT_PATH = ROOT.parent / "cap-platform"

CAP_BASE_MODULE_PREFIXES: tuple[str, ...] = (
    "cap-platform/repos/cap-base/",
    "../cap-platform/repos/cap-base/",
)

DOMAIN_PATH_MARKERS: tuple[str, ...] = (
    "../cap-platform/repos/cap-base/src/domain",
    "cap-platform/repos/cap-base/src/domain",
)

REPOSITORY_PATH_MARKERS: tuple[str, ...] = (
    "../cap-platform/repos/cap-base/src/domain/repositories",
    "cap-platform/repos/cap-base/src/domain/repositories",
)

REPOSITORY_SCOPE_PREFIXES: tuple[str, ...] = REPOSITORY_PATH_MARKERS

REQUIRED_ENTITIES: list[str] = list(REQUIRED_MODELS)

DOMAIN_FORBIDDEN_TERM_PATTERNS: list[tuple[str, str]] = [
    ("controller", r"\bcontroller\b"),
    ("api", r"\bapi\b"),
    ("route", r"\broute\b"),
    ("endpoint", r"\bendpoint\b"),
    ("crud", r"\bcrud\b"),
    ("password", r"\bpassword\b"),
    ("passwordHash", r"\bpasswordHash\b"),
    ("refreshToken", r"\brefreshToken\b"),
    ("resetToken", r"\bresetToken\b"),
    ("token", r"\btoken\b"),
    ("Product", r"\bProduct\b"),
    ("Plan", r"\bPlan\b"),
    ("Drawing", r"\bDrawing\b"),
    ("Promotion", r"\bPromotion\b"),
    ("FinancialEntry", r"\bFinancialEntry\b"),
    ("LuckyNumber", r"\bLuckyNumber\b"),
    ("service", r"\bservice\b"),
]

REPOSITORY_FORBIDDEN_TERM_PATTERNS: list[tuple[str, str]] = [
    ("controller", r"\bcontroller\b"),
    ("api", r"\bapi\b"),
    ("route", r"\broute\b"),
    ("endpoint", r"\bendpoint\b"),
    ("service", r"\bservice\b"),
    ("crud", r"\bcrud\b"),
    ("prisma client", r"\bprisma\s+client\b"),
    ("prisma", r"\bprisma\b"),
    ("database implementation", r"\bdatabase\s+implementation\b"),
    ("implementation", r"\bimplementation\b"),
    ("password", r"\bpassword\b"),
    ("passwordHash", r"\bpasswordHash\b"),
    ("refreshToken", r"\brefreshToken\b"),
    ("resetToken", r"\bresetToken\b"),
    ("token", r"\btoken\b"),
    ("Product", r"\bProduct\b"),
    ("Plan", r"\bPlan\b"),
    ("Drawing", r"\bDrawing\b"),
    ("Promotion", r"\bPromotion\b"),
    ("FinancialEntry", r"\bFinancialEntry\b"),
    ("LuckyNumber", r"\bLuckyNumber\b"),
]

REPOSITORY_WRITE_FORBIDDEN_TERM_PATTERNS: list[tuple[str, str]] = [
    ("password", r"\bpassword\b"),
    ("passwordHash", r"\bpasswordHash\b"),
    ("refreshToken", r"\brefreshToken\b"),
    ("resetToken", r"\bresetToken\b"),
    ("token", r"\btoken\b"),
    ("Product", r"\bProduct\b"),
    ("Plan", r"\bPlan\b"),
    ("Drawing", r"\bDrawing\b"),
    ("Promotion", r"\bPromotion\b"),
    ("FinancialEntry", r"\bFinancialEntry\b"),
    ("LuckyNumber", r"\bLuckyNumber\b"),
    ("PrismaClient", r"\bPrismaClient\b"),
    ("prisma", r"\bprisma\b"),
    ("controller", r"\bcontroller\b"),
    ("service", r"\bservice\b"),
    ("route", r"\broute\b"),
    ("endpoint", r"\bendpoint\b"),
]


def _pascal_to_kebab(name: str) -> str:
    return re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", name).lower()


def _entity_to_domain_filename(entity: str) -> str:
    return f"{_pascal_to_kebab(entity)}.entity.ts"


REQUIRED_DOMAIN_ENTITY_FILENAMES: list[str] = [
    _entity_to_domain_filename(entity) for entity in REQUIRED_ENTITIES
]


def _repository_read_basename(stem: str) -> str:
    return f"{stem}-read.repository.ts"


def _repository_write_basename(stem: str) -> str:
    return f"{stem}-write.repository.ts"


def _repository_stem_to_pascal(stem: str) -> str:
    return "".join(part[0].upper() + part[1:] for part in stem.split("-"))


# Par (stem do agregado em kebab-case, nome da entidade TypeScript) — ordem estável da squad.
REPOSITORY_CONTRACT_SPECS: list[tuple[str, str]] = [
    ("organizations", "Organization"),
    ("organization-types", "OrganizationType"),
    ("organization-status", "OrganizationStatus"),
    ("organization-roles", "OrganizationRole"),
    ("organization-role-assignments", "OrganizationRoleAssignment"),
    ("users", "User"),
    ("user-status", "UserStatus"),
    ("roles", "Role"),
    ("permissions", "Permission"),
    ("role-permissions", "RolePermission"),
    ("user-organizations", "UserOrganization"),
    ("addresses", "Address"),
    ("address-types", "AddressType"),
    ("contacts", "Contact"),
    ("contact-types", "ContactType"),
    ("documents", "Document"),
    ("document-types", "DocumentType"),
    ("system-parameters", "SystemParameter"),
    ("system-parameter-types", "SystemParameterType"),
    ("system-parameter-scopes", "SystemParameterScope"),
    ("audit-logs", "AuditLog"),
    ("audit-action-types", "AuditActionType"),
    ("audit-entity-types", "AuditEntityType"),
]

REPOSITORY_CONTRACT_KIND_BY_STEM: dict[str, str] = {
    "organizations": "org",
    "organization-types": "default",
    "organization-status": "default",
    "organization-roles": "default",
    "organization-role-assignments": "assign",
    "users": "user",
    "user-status": "default",
    "roles": "role",
    "permissions": "permission",
    "role-permissions": "roleperm",
    "user-organizations": "userorg",
    "addresses": "default",
    "address-types": "default",
    "contacts": "default",
    "contact-types": "default",
    "documents": "default",
    "document-types": "default",
    "system-parameters": "sysparam",
    "system-parameter-types": "default",
    "system-parameter-scopes": "default",
    "audit-logs": "auditlog",
    "audit-action-types": "default",
    "audit-entity-types": "default",
}


def _entity_to_repository_filename(entity: str) -> str:
    """Nome canônico do contrato de leitura para a entidade (compatível com layout read/write)."""
    for stem, ent in REPOSITORY_CONTRACT_SPECS:
        if ent == entity:
            return _repository_read_basename(stem)
    return f"{_pascal_to_kebab(entity)}-read.repository.ts"


REQUIRED_REPOSITORY_FILENAMES: list[str] = [
    fn
    for stem, _ent in REPOSITORY_CONTRACT_SPECS
    for fn in (_repository_read_basename(stem), _repository_write_basename(stem))
] + ["index.ts"]

REPOSITORY_FORBIDDEN_METHOD_PATTERNS: list[tuple[str, str]] = [
    ("delete", r"\bdelete\s*\("),
    ("remove", r"\bremove\s*\("),
    ("softDelete", r"\bsoftDelete\s*\("),
    ("restore", r"\brestore\s*\("),
    ("save", r"\bsave\s*\("),
    ("upsert", r"\bupsert\s*\("),
]

CONTEXT_FILES = [
    ROOT / "docs" / "00-fonte-oficial.md",
    ROOT / "docs" / "01-organizacao-projetos-prioritarios.md",
    ROOT / "projects" / "cap" / "context.md",
    ROOT / "projects" / "cap" / "standards.md",
    ROOT / "projects" / "cap" / "decisions.md",
    ROOT / "projects" / "cap" / "backlog.md",
    ROOT / "squads" / "cap" / "workflow.md",
    ROOT / "squads" / "cap" / "task-policy.md",
]

AGENTS: list[tuple[str, str, Path]] = [
    ("po", "po", ROOT / "squads" / "cap" / "agents" / "po.md"),
    ("architect", "architect", ROOT / "squads" / "cap" / "agents" / "architect.md"),
    ("dev-base", "dev-base", ROOT / "squads" / "cap" / "agents" / "dev-base.md"),
    ("reviewer", "reviewer", ROOT / "squads" / "cap" / "agents" / "reviewer.md"),
    ("qa", "qa", ROOT / "squads" / "cap" / "agents" / "qa.md"),
]

META_ORCHESTRATOR_INSTRUCTIONS_PATH = ROOT / "agents" / "meta-orchestrator.md"


def _parse_cli_args(argv: list[str]) -> tuple[str, str, bool, bool, bool, str | None]:
    """
    Retorna (projeto, caminho_input, write_files, validate_existing, write_real_files, single_agent).

    single_agent: quando definido (ex.: \"meta-orchestrator\"), executa apenas esse agente.

    Aceita dois argumentos posicionais e, opcionalmente, --write-files, --validate-existing,
    --write-real-files ou --agent <nome> (hoje apenas meta-orchestrator).
    """
    write_files = False
    validate_existing = False
    write_real_files = False
    single_agent: str | None = None
    positional: list[str] = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--write-files":
            write_files = True
            i += 1
            continue
        if arg == "--validate-existing":
            validate_existing = True
            i += 1
            continue
        if arg == "--write-real-files":
            write_real_files = True
            i += 1
            continue
        if arg == "--agent":
            if i + 1 >= len(argv):
                _die("Erro: --agent requer um valor (ex.: meta-orchestrator).")
            single_agent = argv[i + 1].strip().lower()
            i += 2
            continue
        if arg.startswith("-"):
            _die(
                f"Erro: argumento desconhecido: {arg!r}. "
                "Opções: --write-files, --validate-existing, --write-real-files ou --agent meta-orchestrator."
            )
        positional.append(arg)
        i += 1

    if write_files and validate_existing:
        _die("Erro: --write-files e --validate-existing não podem ser usados juntos.")

    if validate_existing and write_real_files:
        _die("Erro: --validate-existing não pode ser combinado com --write-real-files.")

    if single_agent and (write_files or validate_existing):
        _die("Erro: --agent não pode ser combinado com --write-files ou --validate-existing.")

    if single_agent and write_real_files:
        _die("Erro: --agent não pode ser combinado com --write-real-files.")

    if single_agent and single_agent != "meta-orchestrator":
        _die(
            "Erro: para execução isolada, apenas --agent meta-orchestrator é suportado nesta fase "
            f"(recebido: {single_agent!r})."
        )

    if len(positional) != 2:
        _die(
            "Uso: python scripts/run_squad.py <projeto> <caminho-do-input.md> "
            "[--write-files | --validate-existing | --write-real-files | --agent meta-orchestrator]\n"
            "Exemplo: python scripts/run_squad.py cap runs/cap/001-cap-base-database/input.md\n"
            "Exemplo: python scripts/run_squad.py cap runs/cap/001-cap-base-database/input.md --write-files\n"
            "Exemplo: python scripts/run_squad.py cap runs/cap/001-cap-base-database/input.md --validate-existing\n"
            "Exemplo: python scripts/run_squad.py cap runs/cap/004-meta-orchestrator/input.md "
            "--agent meta-orchestrator\n"
            "Exemplo: python scripts/run_squad.py cap runs/cap/005-real-file-creation/input.md\n"
            "Exemplo: python scripts/run_squad.py cap runs/cap/005-real-file-creation/input.md --write-real-files"
        )

    return positional[0], positional[1], write_files, validate_existing, write_real_files, single_agent


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


def _model_decl_pattern(name: str) -> re.Pattern[str]:
    return re.compile(rf"model\s+{re.escape(name)}\s*\{{", re.MULTILINE)


def _find_forbidden_models(text: str) -> list[str]:
    found: list[str] = []
    for name in FORBIDDEN_MODELS:
        if _model_decl_pattern(name).search(text):
            found.append(name)
    return found


def _find_forbidden_terms(text: str) -> list[str]:
    hits: list[str] = []
    for label, pattern in FORBIDDEN_TERM_PATTERNS:
        if re.search(pattern, text):
            hits.append(label)
    return hits


def _find_placeholders(text: str) -> list[str]:
    hits: list[str] = []
    for label, pattern in PLACEHOLDER_RULES:
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(label)
    return hits


def _extract_first_prisma_block(dev_output: str) -> str | None:
    """Primeiro fence ```prisma ... ``` na saída do Dev Base."""
    m = re.search(r"```prisma\s*\n([\s\S]*?)```", dev_output, re.IGNORECASE)
    if not m:
        return None
    body = m.group(1).strip()
    return body if body else None


def _find_implicit_m2m_issues(text: str) -> list[str]:
    """
    Many-to-many implícito proibido entre Role e Permission.
    Usa (?<!\\w) para não disparar em `OrganizationRole[]` ou `RolePermission[]`.
    """
    issues: list[str] = []
    if re.search(r"\broles\s+Role\[\]", text):
        issues.append("Encontrado `roles Role[]` (many-to-many implícito proibido).")
    if re.search(r"\bpermissions\s+Permission\[\]", text):
        issues.append("Encontrado `permissions Permission[]` (many-to-many implícito proibido).")
    if re.search(r"(?<!\w)Permission\[\]", text):
        issues.append(
            "Encontrado `Permission[]` isolado (verificar junção explícita via `RolePermission`)."
        )
    if re.search(r"(?<!\w)Role\[\]", text):
        issues.append(
            "Encontrado `Role[]` isolado (verificar junção explícita via `RolePermission`)."
        )
    return issues


def _path_reference_ok(text: str) -> bool:
    return any(marker in text for marker in PATH_MARKERS)


def _physical_file_present() -> bool:
    try:
        return CAP_BASE_PRISMA_PATH.is_file()
    except OSError:
        return False


def _prisma_validate_claimed(text: str) -> bool:
    if not re.search(r"npx\s+prisma\s+validate\b", text, re.IGNORECASE):
        return False
    success = re.search(
        r"(validated\s+successfully|No\s+schema\s+errors|schema\s+validation\s*:\s*success|✔\s*Generated\s+Prisma\s+Client)",
        text,
        re.IGNORECASE,
    )
    explicit_ok = re.search(r"prisma\s+validate\b[^\n]*\b(ok|success|passed)\b", text, re.IGNORECASE)
    return bool(success or explicit_ok)


def _infer_run_delivery_type(run_dir: Path) -> str:
    """Inferir tipo de entrega pelo nome da pasta do run."""
    name = run_dir.name.lower()
    if "database" in name:
        return "database"
    if "domain" in name:
        return "domain"
    if "repository-contracts" in name:
        return "repository-contracts"
    return "generic"


def _entity_name_stem(name: str) -> str:
    if not name:
        return name
    return name[0].lower() + name[1:]


def _entity_file_patterns(name: str) -> list[str]:
    stem = _entity_name_stem(name)
    return [
        f"{stem}.entity.ts",
        f"{name}.ts",
        f"{stem}.ts",
    ]


def _entity_proposed_in_output(dev_output: str, entity: str) -> bool:
    lowered = dev_output.lower()
    for pattern in _entity_file_patterns(entity):
        if pattern.lower() in lowered:
            return True
    if re.search(rf"\b{re.escape(entity)}\b", dev_output):
        return True
    return False


def _extract_proposed_ts_files(dev_output: str) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for match in re.finditer(r"[`'\"]?([\w./-]+\.ts)[`'\"]?", dev_output):
        candidate = match.group(1).strip()
        if candidate and candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def _find_domain_forbidden_terms(text: str) -> list[str]:
    hits: list[str] = []
    for label, pattern in DOMAIN_FORBIDDEN_TERM_PATTERNS:
        if re.search(pattern, text):
            hits.append(label)
    return hits


def _path_within_cap_base_module(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(prefix in normalized for prefix in CAP_BASE_MODULE_PREFIXES)


def _find_out_of_scope_paths(dev_output: str) -> list[str]:
    issues: list[str] = []
    for path in _extract_proposed_ts_files(dev_output):
        normalized = path.replace("\\", "/")
        if "/" not in normalized:
            continue
        if not _path_within_cap_base_module(normalized):
            issues.append(path)
    return issues


def _domain_path_reference_ok(text: str) -> bool:
    return any(marker in text for marker in DOMAIN_PATH_MARKERS)


def _domain_physical_files_present() -> bool:
    try:
        if not CAP_BASE_DOMAIN_PATH.is_dir():
            return False
        return any(CAP_BASE_DOMAIN_PATH.rglob("*.ts"))
    except OSError:
        return False


def _canonical_entity_filename(filename: str) -> str | None:
    base = Path(filename.replace("\\", "/")).name.lower()
    for entity in REQUIRED_ENTITIES:
        candidates = {
            _entity_to_domain_filename(entity).lower(),
            f"{_entity_name_stem(entity).lower()}.entity.ts",
            f"{entity.lower()}.entity.ts",
        }
        if base in candidates:
            return _entity_to_domain_filename(entity)
    return None


def _normalize_domain_file_ref(file_ref: str) -> str | None:
    normalized = file_ref.replace("\\", "/").strip()
    basename = Path(normalized).name
    lowered = basename.lower()
    if lowered == "index.ts":
        if "src/index.ts" in normalized or normalized.endswith("/src/index.ts"):
            return "src/index.ts"
        return "domain/index.ts"
    canonical = _canonical_entity_filename(basename)
    if canonical:
        return f"entities/{canonical}"
    if lowered.endswith(".entity.ts"):
        return f"entities/{basename}"
    return None


def _extract_typescript_files_from_dev_output(dev_output: str) -> dict[str, str]:
    files: dict[str, str] = {}

    header_fence = re.compile(
        r"(?:^|\n)(?:#+\s*|[-*]\s*)?[`'\"]?([\w./-]+\.(?:entity\.ts|ts))[`'\"]?"
        r"\s*\n+```(?:typescript|ts)\s*\n([\s\S]*?)```",
        re.MULTILINE,
    )
    for match in header_fence.finditer(dev_output):
        key = _normalize_domain_file_ref(match.group(1))
        if key:
            files[key] = match.group(2).strip()

    for match in re.finditer(r"```(?:typescript|ts)\s*\n([\s\S]*?)```", dev_output):
        body = match.group(1).strip()
        if not body:
            continue
        first_line = body.splitlines()[0].strip()
        file_hint = re.match(
            r"//\s*(?:file:\s*)?([\w./-]+\.(?:entity\.ts|ts))",
            first_line,
            re.IGNORECASE,
        )
        if file_hint:
            key = _normalize_domain_file_ref(file_hint.group(1))
            if key:
                files[key] = body
                continue
        class_match = re.search(r"export\s+(?:class|interface|type|enum)\s+(\w+)", body)
        if not class_match:
            continue
        entity = class_match.group(1)
        if entity not in REQUIRED_ENTITIES:
            continue
        key = f"entities/{_entity_to_domain_filename(entity)}"
        files.setdefault(key, body)

    return files


def _build_domain_index_ts() -> str:
    lines = [
        f"export * from './entities/{filename.replace('.entity.ts', '.entity')}';"
        for filename in REQUIRED_DOMAIN_ENTITY_FILENAMES
    ]
    return "\n".join(lines) + "\n"


def _build_src_index_ts() -> str:
    return "export * from './domain';\n"


def _write_text_file_with_backup(
    *,
    target: Path,
    content: str,
    ts: str,
) -> tuple[str, str | None]:
    action = "Criado"
    backup_path: str | None = None
    if target.is_file():
        backup = target.with_name(f"{target.name}.bak-{ts}")
        shutil.copy2(target, backup)
        backup_path = str(backup.resolve())
        action = "Sobrescrito com backup"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")
    return action, backup_path


def _resolve_domain_target_path(file_key: str) -> Path:
    if file_key == "src/index.ts":
        return CAP_BASE_SRC_INDEX_PATH
    if file_key == "domain/index.ts":
        return CAP_BASE_DOMAIN_INDEX_PATH
    if file_key.startswith("entities/"):
        return CAP_BASE_DOMAIN_ENTITIES_PATH / Path(file_key).name
    return CAP_BASE_DOMAIN_PATH / file_key


def _find_tsconfig() -> tuple[Path | None, Path | None]:
    candidates = (
        CAP_BASE_ROOT_PATH / "tsconfig.json",
        CAP_PLATFORM_ROOT_PATH / "tsconfig.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate, candidate.parent
    return None, None


def _run_tsc_validate(*, cwd: Path) -> tuple[int | None, str, str, str]:
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
    validate_cmd_display = f"{npx_cmd} --yes tsc --noEmit"
    cmd = [npx_cmd, "--yes", "tsc", "--noEmit"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(cwd),
            shell=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or "", validate_cmd_display
    except FileNotFoundError:
        return -1, "", f"Comando {npx_cmd!r} não encontrado no PATH.", validate_cmd_display
    except subprocess.TimeoutExpired:
        return -2, "", f"Timeout ao executar {validate_cmd_display}.", validate_cmd_display
    except OSError as exc:
        return -3, "", str(exc), validate_cmd_display


def _validate_written_domain_files() -> tuple[dict[str, bool], list[str], list[str]]:
    checks: dict[str, bool] = {}
    missing: list[str] = []
    for filename in REQUIRED_DOMAIN_ENTITY_FILENAMES:
        present = (CAP_BASE_DOMAIN_ENTITIES_PATH / filename).is_file()
        checks[filename] = present
        if not present:
            missing.append(filename)
    checks["domain/index.ts"] = CAP_BASE_DOMAIN_INDEX_PATH.is_file()
    if not checks["domain/index.ts"]:
        missing.append("domain/index.ts")
    checks["src/index.ts"] = CAP_BASE_SRC_INDEX_PATH.is_file()
    if not checks["src/index.ts"]:
        missing.append("src/index.ts")

    forbidden_hits: list[str] = []
    scan_paths = [CAP_BASE_DOMAIN_INDEX_PATH, CAP_BASE_SRC_INDEX_PATH]
    scan_paths.extend(CAP_BASE_DOMAIN_ENTITIES_PATH.glob("*.entity.ts"))
    for path in scan_paths:
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for label, pattern in DOMAIN_FORBIDDEN_TERM_PATTERNS:
            if re.search(pattern, content) and label not in forbidden_hits:
                forbidden_hits.append(label)
    return checks, missing, forbidden_hits


def _compute_domain_real_validation_status(
    *,
    missing: list[str],
    forbidden_hits: list[str],
    tsc_exit: int | None,
    tsc_skipped: bool,
) -> str:
    if missing or forbidden_hits:
        return "REPROVADO"
    if tsc_skipped:
        return "APROVÁVEL COM RESSALVAS"
    if tsc_exit == 0:
        return "APROVADO"
    return "REPROVADO"


def _canonical_repository_filename(filename: str) -> str | None:
    base = Path(filename.replace("\\", "/")).name
    lowered = base.lower()
    for stem, entity in REPOSITORY_CONTRACT_SPECS:
        read_fn = _repository_read_basename(stem)
        write_fn = _repository_write_basename(stem)
        if lowered == read_fn.lower():
            return read_fn
        if lowered == write_fn.lower():
            return write_fn
        legacy = f"{_pascal_to_kebab(entity)}.repository.ts"
        if lowered == legacy.lower():
            return read_fn
        if lowered == f"{entity.lower()}.repository.ts".lower():
            return read_fn
    return None


def _normalize_repository_file_ref(file_ref: str) -> str | None:
    normalized = file_ref.replace("\\", "/").strip()
    basename = Path(normalized).name
    lowered = basename.lower()
    if lowered == "index.ts":
        if "repositories" in normalized:
            return "repositories/index.ts"
        if "domain/index.ts" in normalized or normalized.endswith("/domain/index.ts"):
            return "domain/index.ts"
        return None
    canonical = _canonical_repository_filename(basename)
    if canonical:
        return f"repositories/{canonical}"
    if lowered.endswith(".repository.ts"):
        return f"repositories/{basename}"
    return None


def _extract_repository_typescript_files_from_dev_output(dev_output: str) -> dict[str, str]:
    files: dict[str, str] = {}

    header_fence = re.compile(
        r"(?:^|\n)(?:#+\s*|[-*]\s*)?[`'\"]?([\w./-]+\.(?:repository\.ts|ts))[`'\"]?"
        r"\s*\n+```(?:typescript|ts)\s*\n([\s\S]*?)```",
        re.MULTILINE,
    )
    for match in header_fence.finditer(dev_output):
        key = _normalize_repository_file_ref(match.group(1))
        if key:
            files[key] = match.group(2).strip()

    for match in re.finditer(r"```(?:typescript|ts)\s*\n([\s\S]*?)```", dev_output):
        body = match.group(1).strip()
        if not body:
            continue
        first_line = body.splitlines()[0].strip()
        file_hint = re.match(
            r"//\s*(?:file:\s*)?([\w./-]+\.(?:repository\.ts|ts))",
            first_line,
            re.IGNORECASE,
        )
        if file_hint:
            key = _normalize_repository_file_ref(file_hint.group(1))
            if key:
                files[key] = body
                continue
        iface_match = re.search(r"export\s+interface\s+(\w+)\b", body)
        if iface_match:
            iface = iface_match.group(1)
            matched = False
            for stem, entity in REPOSITORY_CONTRACT_SPECS:
                pascal = _repository_stem_to_pascal(stem)
                read_iface = f"{pascal}ReadRepository"
                write_iface = f"{pascal}WriteRepository"
                if iface == read_iface:
                    key = f"repositories/{_repository_read_basename(stem)}"
                    files.setdefault(key, body)
                    matched = True
                    break
                if iface == write_iface:
                    key = f"repositories/{_repository_write_basename(stem)}"
                    files.setdefault(key, body)
                    matched = True
                    break
            if matched:
                continue
            if iface.endswith("Repository"):
                entity_from_iface = iface.removesuffix("Repository")
                if entity_from_iface in REQUIRED_ENTITIES:
                    key = f"repositories/{_entity_to_repository_filename(entity_from_iface)}"
                    files.setdefault(key, body)

    return files


def _build_repositories_index_ts() -> str:
    lines: list[str] = []
    for stem, _ in REPOSITORY_CONTRACT_SPECS:
        lines.append(f"export * from './{stem}-read.repository';")
        lines.append(f"export * from './{stem}-write.repository';")
    return "\n".join(lines) + "\n"


def _build_repository_read_stub(*, stem: str, entity_name: str) -> str:
    pascal = _repository_stem_to_pascal(stem)
    kind = REPOSITORY_CONTRACT_KIND_BY_STEM.get(stem, "default")
    lines = [
        f'import {{ {entity_name} }} from "../entities";',
        "",
        f"export interface {pascal}ReadRepository {{",
        f"  findById(id: number): Promise<{entity_name} | null>;",
        f"  findMany(): Promise<{entity_name}[]>;",
        "  existsById(id: number): Promise<boolean>;",
    ]
    if kind in ("org", "user"):
        lines.append("  existsByDocument(document: string): Promise<boolean>;")
    if kind == "permission" or kind == "role":
        lines.append(f"  findByCode(code: string): Promise<{entity_name} | null>;")
    if kind == "sysparam":
        lines.append(f"  findByKey(key: string): Promise<{entity_name} | null>;")
    if kind == "assign":
        lines.append(f"  findByOrganizationId(organizationId: number): Promise<{entity_name}[]>;")
        lines.append(f"  findByRoleId(roleId: number): Promise<{entity_name}[]>;")
    if kind == "roleperm":
        lines.append(f"  findByRoleId(roleId: number): Promise<{entity_name}[]>;")
        lines.append(f"  findByPermissionId(permissionId: number): Promise<{entity_name}[]>;")
    if kind == "userorg":
        lines.append(f"  findByUserId(userId: number): Promise<{entity_name}[]>;")
        lines.append(f"  findByOrganizationId(organizationId: number): Promise<{entity_name}[]>;")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _build_repository_write_stub(*, stem: str, entity_name: str) -> str:
    pascal = _repository_stem_to_pascal(stem)
    kind = REPOSITORY_CONTRACT_KIND_BY_STEM.get(stem, "default")
    lines = [
        f'import {{ {entity_name} }} from "../entities";',
        "",
        f"export interface {pascal}WriteRepository {{",
    ]
    if kind == "auditlog":
        lines.append(f"  create(entry: {entity_name}): Promise<{entity_name}>;")
        lines.append("}")
        lines.append("")
        return "\n".join(lines)
    lines.append(f"  create(entity: {entity_name}): Promise<{entity_name}>;")
    lines.append(f"  update(entity: {entity_name}): Promise<{entity_name}>;")
    if kind in ("org", "user"):
        lines.append(f"  activate(entity: {entity_name}): Promise<{entity_name}>;")
        lines.append(f"  deactivate(entity: {entity_name}): Promise<{entity_name}>;")
    if kind == "assign":
        lines.append(
            "  assignRole(params: { organizationId: number; roleId: number }): "
            f"Promise<{entity_name}>;"
        )
        lines.append("  revokeRole(assignmentId: number): Promise<void>;")
    if kind == "roleperm":
        lines.append(
            "  attachPermission(roleId: number, permissionId: number): "
            f"Promise<{entity_name}>;"
        )
        lines.append("  detachPermission(roleId: number, permissionId: number): Promise<void>;")
    if kind == "userorg":
        lines.append(f"  linkUserToOrganization(link: {entity_name}): Promise<{entity_name}>;")
        lines.append("  unlinkUserFromOrganization(assignmentId: number): Promise<void>;")
    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def _build_deterministic_repository_files() -> dict[str, str]:
    files: dict[str, str] = {}
    for stem, entity_name in REPOSITORY_CONTRACT_SPECS:
        files[f"repositories/{_repository_read_basename(stem)}"] = _build_repository_read_stub(
            stem=stem, entity_name=entity_name
        )
        files[f"repositories/{_repository_write_basename(stem)}"] = _build_repository_write_stub(
            stem=stem, entity_name=entity_name
        )
    files["repositories/index.ts"] = _build_repositories_index_ts()
    return files


def _demand_indicates_repository_contracts(demanda: str) -> bool:
    lowered = demanda.lower()
    markers = (
        "repository-contracts",
        "contratos de repositório",
        "contratos e interfaces de repositório",
        "interfaces de repositório",
        "src/domain/repositories",
        "domain/repositories",
    )
    return any(marker in lowered for marker in markers)


def _should_deterministic_repository_contracts_write(
    *,
    project: str,
    run_dir: Path,
    demanda: str,
) -> bool:
    if project != "cap":
        return False
    run_slug = run_dir.name.lower()
    if "repository-contracts" not in run_slug:
        return False
    if "cap-base" not in run_slug and "cap-base" not in demanda.lower():
        return False
    return _demand_indicates_repository_contracts(demanda)


def _build_domain_index_with_entities_and_repositories() -> str:
    return 'export * from "./entities";\nexport * from "./repositories";\n'


def _ensure_domain_index_entities_and_repositories(content: str) -> str:
    updated = content
    if not re.search(r"export\s+\*\s+from\s+['\"]\./entities['\"]", updated) and not re.search(
        r"export\s+\*\s+from\s+['\"]\./entities/",
        updated,
    ):
        updated = 'export * from "./entities";\n' + updated.lstrip()
    return _ensure_domain_index_exports_repositories(updated)


def _ensure_domain_index_exports_repositories(content: str) -> str:
    if re.search(r"export\s+\*\s+from\s+['\"]\./repositories['\"]", content):
        return content if content.endswith("\n") else content + "\n"
    trimmed = content.rstrip()
    return trimmed + "\nexport * from './repositories';\n"


def _resolve_repository_target_path(file_key: str) -> Path:
    if file_key == "domain/index.ts":
        return CAP_BASE_DOMAIN_INDEX_PATH
    if file_key == "repositories/index.ts":
        return CAP_BASE_REPOSITORIES_PATH / "index.ts"
    if file_key.startswith("repositories/"):
        return CAP_BASE_REPOSITORIES_PATH / Path(file_key).name
    return CAP_BASE_REPOSITORIES_PATH / file_key


def _validate_written_repository_files() -> tuple[dict[str, bool], list[str], list[str]]:
    checks: dict[str, bool] = {}
    missing: list[str] = []
    for filename in REQUIRED_REPOSITORY_FILENAMES:
        present = (CAP_BASE_REPOSITORIES_PATH / filename).is_file()
        checks[filename] = present
        if not present:
            missing.append(filename)

    forbidden_hits: list[str] = []
    if CAP_BASE_REPOSITORIES_PATH.is_dir():
        for path in CAP_BASE_REPOSITORIES_PATH.glob("*.ts"):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for label, pattern in REPOSITORY_WRITE_FORBIDDEN_TERM_PATTERNS:
                if re.search(pattern, content) and label not in forbidden_hits:
                    forbidden_hits.append(label)
            for label, pattern in REPOSITORY_FORBIDDEN_METHOD_PATTERNS:
                if re.search(pattern, content) and label not in forbidden_hits:
                    forbidden_hits.append(label)
    return checks, missing, forbidden_hits


def _validate_existing_repository_contract_files() -> tuple[dict[str, bool], list[str], list[str]]:
    checks: dict[str, bool] = {}
    missing: list[str] = []
    for filename in REQUIRED_REPOSITORY_FILENAMES:
        rel_key = "repositories/index.ts" if filename == "index.ts" else filename
        present = (CAP_BASE_REPOSITORIES_PATH / filename).is_file()
        checks[rel_key] = present
        if not present:
            missing.append(rel_key)

    for key, path in (
        ("domain/entities/index.ts", CAP_BASE_DOMAIN_ENTITIES_PATH / "index.ts"),
        ("domain/index.ts", CAP_BASE_DOMAIN_INDEX_PATH),
        ("src/index.ts", CAP_BASE_SRC_INDEX_PATH),
    ):
        checks[key] = path.is_file()
        if not checks[key]:
            missing.append(key)

    forbidden_hits: list[str] = []
    if CAP_BASE_REPOSITORIES_PATH.is_dir():
        for path in CAP_BASE_REPOSITORIES_PATH.glob("*.ts"):
            if not path.is_file():
                continue
            try:
                content = path.read_text(encoding="utf-8")
            except OSError:
                continue
            for label, pattern in REPOSITORY_WRITE_FORBIDDEN_TERM_PATTERNS:
                if re.search(pattern, content) and label not in forbidden_hits:
                    forbidden_hits.append(label)
            for label, pattern in REPOSITORY_FORBIDDEN_METHOD_PATTERNS:
                if label == "save":
                    continue
                if re.search(pattern, content) and label not in forbidden_hits:
                    forbidden_hits.append(label)
    return checks, missing, forbidden_hits


def _compute_repository_real_validation_status(
    *,
    missing: list[str],
    forbidden_hits: list[str],
    tsc_exit: int | None,
    tsc_skipped: bool,
) -> str:
    if missing or forbidden_hits:
        return "REPROVADO"
    if tsc_skipped:
        return "APROVÁVEL COM RESSALVAS"
    if tsc_exit == 0:
        return "APROVADO"
    return "REPROVADO"


def validate_dev_base_domain_output(dev_output: str) -> tuple[str, str]:
    """
    Validação determinística sobre a saída textual do Dev Base para entrega de domínio TypeScript.

    Retorna (status, markdown), com status em:
    APROVADO | APROVÁVEL COM RESSALVAS | REPROVADO
    """
    path_ok = _domain_path_reference_ok(dev_output)
    physical = _domain_physical_files_present()
    proposed_files = _extract_proposed_ts_files(dev_output)

    present = {name: _entity_proposed_in_output(dev_output, name) for name in REQUIRED_ENTITIES}
    missing = [name for name in REQUIRED_ENTITIES if not present[name]]
    forbidden_terms = _find_domain_forbidden_terms(dev_output)
    out_of_scope = _find_out_of_scope_paths(dev_output)

    structural_fail = (
        bool(missing)
        or bool(forbidden_terms)
        or bool(out_of_scope)
        or not path_ok
    )

    if structural_fail:
        status = "REPROVADO"
    elif not physical:
        status = "APROVÁVEL COM RESSALVAS"
    else:
        status = "APROVÁVEL COM RESSALVAS"

    evidence_label = "Presente" if physical else "Ausente"

    lines: list[str] = [
        "# Validação Determinística — Domínio CAP-BASE",
        "",
        "## Status",
        status,
        "",
        "## Entidades esperadas",
        "",
    ]
    for name in REQUIRED_ENTITIES:
        mark = "[x]" if present[name] else "[ ]"
        lines.append(f"- {mark} {name}")
    lines.append("")

    lines.append("## Caminho de domínio")
    lines.append("")
    lines.append(
        "OK"
        if path_ok
        else "AUSENTE — a saída deve citar explicitamente o caminho canônico de domínio."
    )
    lines.append("")

    lines.append("## Arquivos propostos")
    lines.append("")
    if proposed_files:
        for path in proposed_files:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum arquivo `.ts` detectado na saída)")
    lines.append("")

    lines.append("## Termos proibidos encontrados")
    lines.append("")
    if forbidden_terms:
        for term in forbidden_terms:
            lines.append(f"- {term}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Escopo proibido encontrado")
    lines.append("")
    if out_of_scope:
        for path in out_of_scope:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Evidência física dos arquivos")
    lines.append(evidence_label)
    lines.append("")

    lines.append("## Resultado")
    lines.append("")
    explanations: list[str] = []
    if missing:
        explanations.append(f"Faltam entidades esperadas na proposta: {', '.join(missing)}.")
    if forbidden_terms:
        explanations.append(f"Termos proibidos detectados: {', '.join(forbidden_terms)}.")
    if out_of_scope:
        explanations.append(
            "Arquivos propostos fora do módulo `cap-platform/repos/cap-base/`: "
            f"{', '.join(out_of_scope)}."
        )
    if not path_ok:
        explanations.append(
            "A saída não referencia explicitamente `../cap-platform/repos/cap-base/src/domain` "
            "nem `cap-platform/repos/cap-base/src/domain`."
        )
    if structural_fail:
        explanations.append("Resultado: reprovação estrutural — Reviewer e QA devem tratar como falha objetiva.")
    elif not physical:
        explanations.append(
            "Entidades e proibições passíveis de verificação textual OK; arquivos TypeScript físicos ausentes no "
            f"caminho esperado (`{CAP_BASE_DOMAIN_PATH}`). Status máximo: APROVÁVEL COM RESSALVAS até haver "
            "evidência física e validação real do domínio."
        )
    else:
        explanations.append(
            "Checagens estruturais OK e evidência física de arquivos TypeScript presente — permanece APROVÁVEL COM "
            "RESSALVAS até haver validação real do domínio registrada no run."
        )

    lines.append(" ".join(explanations) if explanations else "Sem observações.")
    lines.append("")

    return status, "\n".join(lines).strip()


def _repository_path_reference_ok(text: str) -> bool:
    return any(marker in text for marker in REPOSITORY_PATH_MARKERS)


def _repository_physical_files_present() -> bool:
    try:
        if not CAP_BASE_REPOSITORIES_PATH.is_dir():
            return False
        return any(CAP_BASE_REPOSITORIES_PATH.rglob("*.ts"))
    except OSError:
        return False


def _find_repository_forbidden_terms(text: str) -> list[str]:
    hits: list[str] = []
    for label, pattern in REPOSITORY_FORBIDDEN_TERM_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            hits.append(label)
    return hits


def _path_within_repository_scope(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return any(prefix in normalized for prefix in REPOSITORY_SCOPE_PREFIXES)


def _find_repository_out_of_scope_paths(dev_output: str) -> list[str]:
    issues: list[str] = []
    for path in _extract_proposed_ts_files(dev_output):
        normalized = path.replace("\\", "/")
        if "/" not in normalized:
            continue
        if not _path_within_repository_scope(normalized):
            issues.append(path)
    return issues


def _repository_contract_file_proposed(dev_output: str, stem: str) -> bool:
    lowered = dev_output.lower()
    read_fn = _repository_read_basename(stem).lower()
    write_fn = _repository_write_basename(stem).lower()
    if read_fn in lowered or write_fn in lowered:
        return True
    pascal = _repository_stem_to_pascal(stem)
    patterns = (
        rf"\bexport\s+interface\s+{re.escape(pascal)}ReadRepository\b",
        rf"\bexport\s+interface\s+{re.escape(pascal)}WriteRepository\b",
    )
    return any(re.search(pattern, dev_output) for pattern in patterns)


def _repository_index_proposed(dev_output: str) -> bool:
    lowered = dev_output.lower()
    return any(
        marker in lowered
        for marker in (
            "repositories/index.ts",
            "domain/repositories/index.ts",
        )
    )


def validate_dev_base_repository_contracts_output(dev_output: str) -> tuple[str, str]:
    """
    Validação determinística sobre a saída textual do Dev Base para contratos de repositório.

    Retorna (status, markdown), com status em:
    APROVADO | APROVÁVEL COM RESSALVAS | REPROVADO
    """
    path_ok = _repository_path_reference_ok(dev_output)
    physical = _repository_physical_files_present()
    proposed_files = _extract_proposed_ts_files(dev_output)

    present: dict[str, bool] = {}
    for filename in REQUIRED_REPOSITORY_FILENAMES:
        if filename == "index.ts":
            present[filename] = _repository_index_proposed(dev_output)
            continue
        stem_match: str | None = None
        for stem, _ in REPOSITORY_CONTRACT_SPECS:
            if filename in (
                _repository_read_basename(stem),
                _repository_write_basename(stem),
            ):
                stem_match = stem
                break
        if stem_match is None:
            present[filename] = False
            continue
        present[filename] = _repository_contract_file_proposed(dev_output, stem_match)
    missing = [filename for filename in REQUIRED_REPOSITORY_FILENAMES if not present[filename]]
    forbidden_terms = _find_repository_forbidden_terms(dev_output)
    out_of_scope = _find_repository_out_of_scope_paths(dev_output)

    structural_fail = (
        bool(missing)
        or bool(forbidden_terms)
        or bool(out_of_scope)
        or not path_ok
    )

    if structural_fail:
        status = "REPROVADO"
    elif not physical:
        status = "APROVÁVEL COM RESSALVAS"
    else:
        status = "APROVÁVEL COM RESSALVAS"

    evidence_label = "Presente" if physical else "Ausente"

    lines: list[str] = [
        "# Validação Determinística — Repository Contracts CAP-BASE",
        "",
        "## Status",
        status,
        "",
        "## Interfaces esperadas",
        "",
    ]
    for filename in REQUIRED_REPOSITORY_FILENAMES:
        mark = "[x]" if present[filename] else "[ ]"
        lines.append(f"- {mark} {filename}")
    lines.append("")

    lines.append("## Caminho de repositórios")
    lines.append("")
    lines.append(
        "OK"
        if path_ok
        else (
            "AUSENTE — a saída deve citar explicitamente "
            "`../cap-platform/repos/cap-base/src/domain/repositories` "
            "ou `cap-platform/repos/cap-base/src/domain/repositories`."
        )
    )
    lines.append("")

    lines.append("## Arquivos propostos")
    lines.append("")
    if proposed_files:
        for path in proposed_files:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum arquivo `.ts` detectado na saída)")
    lines.append("")

    lines.append("## Termos proibidos encontrados")
    lines.append("")
    if forbidden_terms:
        for term in forbidden_terms:
            lines.append(f"- {term}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Escopo proibido encontrado")
    lines.append("")
    if out_of_scope:
        for path in out_of_scope:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Evidência física dos arquivos")
    lines.append(evidence_label)
    lines.append("")

    lines.append("## Resultado")
    lines.append("")
    explanations: list[str] = []
    if missing:
        explanations.append(
            "Faltam interfaces ou arquivos de repositório esperados na proposta: "
            f"{', '.join(missing)}."
        )
    if forbidden_terms:
        explanations.append(f"Termos proibidos detectados: {', '.join(forbidden_terms)}.")
    if out_of_scope:
        explanations.append(
            "Arquivos propostos fora de `cap-platform/repos/cap-base/src/domain/repositories`: "
            f"{', '.join(out_of_scope)}."
        )
    if not path_ok:
        explanations.append(
            "A saída não referencia explicitamente o caminho canônico de repositórios do CAP-BASE."
        )
    if structural_fail:
        explanations.append("Resultado: reprovação estrutural — Reviewer e QA devem tratar como falha objetiva.")
    elif not physical:
        explanations.append(
            "Interfaces e proibições passíveis de verificação textual OK; arquivos TypeScript físicos ausentes em "
            f"`{CAP_BASE_REPOSITORIES_PATH}`. Status máximo: APROVÁVEL COM RESSALVAS até haver evidência física e "
            "validação TypeScript real dos contratos."
        )
    else:
        explanations.append(
            "Checagens estruturais OK e evidência física de arquivos TypeScript presente — permanece APROVÁVEL COM "
            "RESSALVAS até haver validação TypeScript real registrada no run."
        )

    lines.append(" ".join(explanations) if explanations else "Sem observações.")
    lines.append("")

    return status, "\n".join(lines).strip()


def validate_dev_base_generic_output(dev_output: str) -> tuple[str, str]:
    """
    Validação determinística genérica para entregas sem regra específica de database/domínio/repositórios.
    """
    forbidden_terms = _find_domain_forbidden_terms(dev_output)
    placeholder_hits = _find_placeholders(dev_output)
    proposed_files = _extract_proposed_ts_files(dev_output)
    body = dev_output.strip()

    structural_fail = not body or bool(forbidden_terms) or bool(placeholder_hits)
    status = "REPROVADO" if structural_fail else "APROVÁVEL COM RESSALVAS"

    lines: list[str] = [
        "# Validação Determinística — Entrega genérica CAP-BASE",
        "",
        "## Status",
        status,
        "",
        "## Arquivos propostos",
        "",
    ]
    if proposed_files:
        for path in proposed_files:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum arquivo `.ts` detectado na saída)")
    lines.append("")

    lines.append("## Termos proibidos encontrados")
    lines.append("")
    if forbidden_terms:
        for term in forbidden_terms:
            lines.append(f"- {term}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Placeholders encontrados")
    lines.append("")
    if placeholder_hits:
        for placeholder in placeholder_hits:
            lines.append(f"- {placeholder}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Evidência física dos arquivos")
    lines.append("Não aplicável para validação genérica textual.")
    lines.append("")

    lines.append("## Resultado")
    lines.append("")
    if not body:
        lines.append("Saída vazia — reprovação estrutural.")
    elif forbidden_terms:
        lines.append(
            "Termos proibidos detectados — Reviewer e QA devem tratar como falha objetiva."
        )
    elif placeholder_hits:
        lines.append("Placeholders detectados — reprovação estrutural.")
    else:
        lines.append(
            "Proposta textual recebida sem regra específica de database, domínio ou repositórios. "
            "Status máximo: APROVÁVEL COM RESSALVAS até haver validação dedicada e evidência física."
        )
    lines.append("")

    return status, "\n".join(lines).strip()


def _validate_dev_output(dev_output: str, delivery_type: str) -> tuple[str, str]:
    if delivery_type == "database":
        return validate_dev_base_output(dev_output)
    if delivery_type == "domain":
        return validate_dev_base_domain_output(dev_output)
    if delivery_type == "repository-contracts":
        return validate_dev_base_repository_contracts_output(dev_output)
    return validate_dev_base_generic_output(dev_output)


def validate_dev_base_output(dev_output: str) -> tuple[str, str]:
    """
    Validação determinística sobre a saída textual do Dev Base.

    Retorna (status, markdown), com status em:
    APROVADO | APROVÁVEL COM RESSALVAS | REPROVADO
    """
    path_ok = _path_reference_ok(dev_output)
    physical = _physical_file_present()

    schema_text = _extract_first_prisma_block(dev_output)
    prisma_missing = schema_text is None

    if prisma_missing:
        present = {name: False for name in REQUIRED_MODELS}
        missing = list(REQUIRED_MODELS)
        forbidden_found: list[str] = []
        term_hits: list[str] = []
        placeholder_hits: list[str] = []
        m2m_issues: list[str] = []
    else:
        present = {}
        for name in REQUIRED_MODELS:
            present[name] = bool(_model_decl_pattern(name).search(schema_text))
        missing = [n for n in REQUIRED_MODELS if not present[n]]
        forbidden_found = _find_forbidden_models(schema_text)
        term_hits = _find_forbidden_terms(schema_text)
        placeholder_hits = _find_placeholders(schema_text)
        m2m_issues = _find_implicit_m2m_issues(schema_text)

    structural_fail = (
        prisma_missing
        or bool(missing)
        or bool(forbidden_found)
        or bool(term_hits)
        or bool(placeholder_hits)
        or bool(m2m_issues)
        or not path_ok
    )

    if structural_fail:
        status = "REPROVADO"
    elif not physical:
        status = "APROVÁVEL COM RESSALVAS"
    elif _prisma_validate_claimed(dev_output):
        status = "APROVADO"
    else:
        status = "APROVÁVEL COM RESSALVAS"

    evidence_label = "Presente" if physical else "Ausente"

    lines: list[str] = [
        "# Validação Determinística — Dev Base",
        "",
        "## Status",
        status,
        "",
        "## Models obrigatórios",
        "",
    ]
    for name in REQUIRED_MODELS:
        mark = "[x]" if present[name] else "[ ]"
        lines.append(f"- {mark} {name}")
    lines.append("")

    lines.append("## Models proibidos encontrados")
    lines.append("")
    if forbidden_found:
        for name in forbidden_found:
            lines.append(f"- {name}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Termos proibidos encontrados")
    lines.append("")
    if term_hits:
        for t in term_hits:
            lines.append(f"- {t}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Placeholders encontrados")
    lines.append("")
    if placeholder_hits:
        for p in placeholder_hits:
            lines.append(f"- {p}")
    else:
        lines.append("- (nenhum)")
    lines.append("")

    lines.append("## Many-to-many implícito")
    lines.append("")
    if m2m_issues:
        for issue in m2m_issues:
            lines.append(f"- {issue}")
    else:
        lines.append("- (nenhuma ocorrência detectada pelos padrões configurados)")
    lines.append("")

    lines.append("## Referência ao caminho canônico de base.prisma")
    lines.append("")
    lines.append("OK" if path_ok else "AUSENTE — a saída deve citar explicitamente o caminho canônico.")
    lines.append("")

    lines.append("## Evidência física do arquivo")
    lines.append(evidence_label)
    lines.append("")

    lines.append("## Resultado")
    lines.append("")
    explanations: list[str] = []
    if prisma_missing:
        explanations.append("Bloco prisma ausente.")
    elif missing:
        explanations.append(f"Faltam models obrigatórios: {', '.join(missing)}.")
    if forbidden_found:
        explanations.append(f"Models proibidos declarados: {', '.join(forbidden_found)}.")
    if term_hits:
        explanations.append(f"Termos proibidos detectados: {', '.join(term_hits)}.")
    if placeholder_hits:
        explanations.append(f"Placeholders proibidos detectados: {', '.join(placeholder_hits)}.")
    if m2m_issues:
        explanations.append("Possível many-to-many implícito entre Role e Permission (ou padrão equivalente).")
    if not path_ok:
        explanations.append(
            "A saída não referencia explicitamente `../cap-platform/repos/cap-base/prisma/base.prisma` "
            "nem `cap-platform/repos/cap-base/prisma/base.prisma`."
        )
    if structural_fail:
        explanations.append("Resultado: reprovação estrutural — Reviewer e QA devem tratar como falha objetiva.")
    elif not physical:
        explanations.append(
            "Models e proibições passíveis de verificação textual OK; arquivo físico ausente no caminho esperado "
            f"(`{CAP_BASE_PRISMA_PATH}`). Status máximo: APROVÁVEL COM RESSALVAS até haver arquivo real e "
            "`npx prisma validate` executado com evidência."
        )
    elif not _prisma_validate_claimed(dev_output):
        explanations.append(
            "Arquivo físico presente, porém não há evidência textual inequívoca de `npx prisma validate` bem-sucedido "
            "na saída do Dev — permanece APROVÁVEL COM RESSALVAS."
        )
    else:
        explanations.append(
            "Checagens estruturais OK, arquivo físico presente e menção a `npx prisma validate` com indicadores de sucesso "
            "na saída — APROVADO pela validação determinística (ainda sujeito ao QA e à evidência real registrada no run)."
        )

    lines.append(" ".join(explanations) if explanations else "Sem observações.")
    lines.append("")

    return status, "\n".join(lines).strip()


def _run_prisma_validate(
    *,
    target: Path,
) -> tuple[int | None, str, str, str]:
    """Executa `npx prisma validate --schema <alvo>` e retorna (exit, stdout, stderr, comando)."""
    target_resolved = target.resolve()
    npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
    validate_cmd_display = f"{npx_cmd} prisma validate --schema {target_resolved}"

    cap_base_root = target.parent.parent
    cwd = cap_base_root if cap_base_root.is_dir() else target.parent
    cmd = [npx_cmd, "prisma", "validate", "--schema", str(target_resolved)]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(cwd),
            shell=False,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or "", validate_cmd_display
    except FileNotFoundError:
        return -1, "", f"Comando {npx_cmd!r} não encontrado no PATH.", validate_cmd_display
    except subprocess.TimeoutExpired:
        return -2, "", f"Timeout ao executar {validate_cmd_display}.", validate_cmd_display
    except OSError as exc:
        return -3, "", str(exc), validate_cmd_display


def _build_prisma_evidence_markdown(
    *,
    flag_label: str,
    target_resolved: Path,
    action: str,
    backup_path: str | None,
    validate_cmd_display: str,
    prisma_exit: int | None,
    prisma_stdout: str,
    prisma_stderr: str,
    evidence: str,
    real_validation: str,
    blocking: list[str] | None = None,
) -> str:
    exit_disp = "(não executado)" if prisma_exit is None else str(prisma_exit)
    md_lines = [
        "# Escrita de Arquivos — CAP-BASE",
        "",
        "## Flag usada",
        flag_label,
        "",
        "## Arquivo alvo",
        str(target_resolved),
        "",
        "## Ação executada",
        action,
        "",
        "## Backup criado",
        backup_path if backup_path else "N/A",
        "",
        "## Comando executado",
        "",
        validate_cmd_display,
        "",
        "## Resultado do prisma validate",
        "",
        f"exit code: {exit_disp}",
        "",
        "stdout:",
        "",
        "```text",
        (prisma_stdout or "(vazio)").rstrip(),
        "```",
        "",
        "stderr:",
        "",
        "```text",
        (prisma_stderr or "(vazio)").rstrip(),
        "```",
        "",
        "## Status da evidência física",
        evidence,
        "",
        "## Status da validação real",
        real_validation,
        "",
    ]
    if blocking:
        md_lines.extend(
            [
                "## Observações / bloqueios",
                "",
                "\n".join(f"- {b}" for b in blocking),
                "",
            ]
        )
    return "\n".join(md_lines).strip()


def _run_validate_existing_phase(
    *,
    target: Path,
) -> tuple[dict[str, Any], str]:
    """
    Valida o arquivo Prisma já existente sem sobrescrever nem chamar agentes/OpenAI.
  """
    target_resolved = target.resolve()
    blocking: list[str] = []
    summary: dict[str, Any] = {
        "target_resolved": str(target_resolved),
        "action": "Validação do arquivo existente (sem escrita)",
        "backup_path": None,
        "prisma_exit": None,
        "prisma_stdout": "",
        "prisma_stderr": "",
        "evidence": "AUSENTE",
        "real_validation": "REPROVADO",
        "blocking_reasons": blocking,
        "validate_cmd_display": "",
        "consolidated_status": "REPROVADO — evidência física ausente.",
    }

    if not target.is_file():
        blocking.append(f"Arquivo inexistente no caminho esperado: {target_resolved}")
        markdown = _build_prisma_evidence_markdown(
            flag_label="--validate-existing",
            target_resolved=target_resolved,
            action=summary["action"],
            backup_path=None,
            validate_cmd_display="(não executado — arquivo ausente)",
            prisma_exit=None,
            prisma_stdout="",
            prisma_stderr="",
            evidence=summary["evidence"],
            real_validation=summary["real_validation"],
            blocking=blocking,
        )
        return summary, markdown

    summary["evidence"] = "PRESENTE"
    exit_code, stdout, stderr, validate_cmd_display = _run_prisma_validate(target=target)
    summary["validate_cmd_display"] = validate_cmd_display
    summary["prisma_exit"] = exit_code
    summary["prisma_stdout"] = stdout
    summary["prisma_stderr"] = stderr
    summary["real_validation"] = "APROVADO" if exit_code == 0 else "REPROVADO"
    if exit_code != 0:
        blocking.append(f"`prisma validate` retornou exit code {exit_code}.")

    if summary["evidence"] == "PRESENTE" and exit_code == 0:
        summary["consolidated_status"] = "APROVADO COM EVIDÊNCIA REAL"
    elif summary["evidence"] == "PRESENTE":
        summary["consolidated_status"] = "REPROVADO — prisma validate falhou."
    else:
        summary["consolidated_status"] = "REPROVADO — evidência física ausente."

    markdown = _build_prisma_evidence_markdown(
        flag_label="--validate-existing",
        target_resolved=target_resolved,
        action=summary["action"],
        backup_path=None,
        validate_cmd_display=validate_cmd_display,
        prisma_exit=exit_code,
        prisma_stdout=stdout,
        prisma_stderr=stderr,
        evidence=summary["evidence"],
        real_validation=summary["real_validation"],
        blocking=blocking or None,
    )
    return summary, markdown


def _build_domain_validate_existing_markdown(
    *,
    target_resolved: Path,
    action: str,
    physical_checks: dict[str, bool],
    forbidden_hits: list[str],
    tsc_exit: int | None,
    tsc_skipped: bool,
    tsc_stdout: str,
    tsc_stderr: str,
    tsc_cmd: str,
    evidence: str,
    real_validation: str,
    blocking: list[str] | None = None,
) -> str:
    if tsc_skipped:
        tsc_exit_display = "skipped"
        tsc_stdout_display = "TypeScript validation skipped: tsconfig não encontrado."
        tsc_stderr_display = ""
    else:
        tsc_exit_display = "(não executado)" if tsc_exit is None else str(tsc_exit)
        tsc_stdout_display = tsc_stdout or "(vazio)"
        tsc_stderr_display = tsc_stderr or "(vazio)"

    lines = [
        "# Validação do Domínio Existente — CAP-BASE",
        "",
        "## Flag usada",
        "--validate-existing",
        "",
        "## Diretório alvo",
        str(target_resolved),
        "",
        "## Ação executada",
        action,
        "",
        "## Validação física dos arquivos",
        "",
    ]
    for filename in REQUIRED_DOMAIN_ENTITY_FILENAMES:
        mark = "[x]" if physical_checks.get(filename) else "[ ]"
        lines.append(f"- {mark} {filename}")
    domain_index_mark = "[x]" if physical_checks.get("domain/index.ts") else "[ ]"
    src_index_mark = "[x]" if physical_checks.get("src/index.ts") else "[ ]"
    lines.append(f"- {domain_index_mark} domain/index.ts")
    lines.append(f"- {src_index_mark} src/index.ts")
    lines.extend(["", "## Termos proibidos encontrados", ""])
    if forbidden_hits:
        for term in forbidden_hits:
            lines.append(f"- {term}")
    else:
        lines.append("- (nenhum)")
    lines.extend(
        [
            "",
            "## Resultado do tsc",
            tsc_exit_display,
            "",
            "stdout",
            "",
            "```text",
            tsc_stdout_display.rstrip(),
            "```",
            "",
            "stderr",
            "",
            "```text",
            tsc_stderr_display.rstrip(),
            "```",
            "",
            "## Comando executado",
            "",
            tsc_cmd or "(não executado)",
            "",
            "## Status da evidência física",
            evidence,
            "",
            "## Status da validação real",
            real_validation,
            "",
        ]
    )
    if blocking:
        lines.extend(["## Observações / bloqueios", "", "\n".join(f"- {item}" for item in blocking), ""])
    return "\n".join(lines).strip()


def _run_validate_existing_domain_phase() -> tuple[dict[str, Any], str]:
    """Valida o domínio TypeScript já existente sem sobrescrever nem chamar agentes/OpenAI."""
    target_resolved = CAP_BASE_DOMAIN_PATH.resolve()
    blocking: list[str] = []
    physical_checks: dict[str, bool] = {name: False for name in REQUIRED_DOMAIN_ENTITY_FILENAMES}
    physical_checks["domain/index.ts"] = False
    physical_checks["src/index.ts"] = False
    forbidden_hits: list[str] = []
    tsc_exit: int | None = None
    tsc_skipped = False
    tsc_stdout = ""
    tsc_stderr = ""
    tsc_cmd = ""
    summary: dict[str, Any] = {
        "target_resolved": str(target_resolved),
        "action": "Validação do domínio existente (sem escrita)",
        "evidence": "AUSENTE",
        "real_validation": "REPROVADO",
        "tsc_exit": None,
        "tsc_stdout": "",
        "tsc_stderr": "",
        "validate_cmd_display": "",
        "physical_checks": physical_checks,
        "forbidden_hits": forbidden_hits,
        "blocking_reasons": blocking,
        "consolidated_status": "REPROVADO — correções obrigatórias",
    }

    def build_markdown() -> str:
        return _build_domain_validate_existing_markdown(
            target_resolved=target_resolved,
            action=summary["action"],
            physical_checks=physical_checks,
            forbidden_hits=forbidden_hits,
            tsc_exit=tsc_exit,
            tsc_skipped=tsc_skipped,
            tsc_stdout=tsc_stdout,
            tsc_stderr=tsc_stderr,
            tsc_cmd=tsc_cmd,
            evidence=summary["evidence"],
            real_validation=summary["real_validation"],
            blocking=blocking or None,
        )

    if not CAP_BASE_DOMAIN_PATH.is_dir():
        blocking.append(f"Diretório inexistente no caminho esperado: {target_resolved}")
        return summary, build_markdown()

    physical_checks, missing, forbidden_hits = _validate_written_domain_files()
    summary["physical_checks"] = physical_checks
    summary["forbidden_hits"] = forbidden_hits
    summary["evidence"] = "PRESENTE" if not missing else "AUSENTE"

    if missing:
        blocking.append(f"Arquivos obrigatórios ausentes: {', '.join(missing)}.")
    if forbidden_hits:
        blocking.append(f"Termos proibidos nos arquivos existentes: {', '.join(forbidden_hits)}.")

    tsconfig_path, tsc_cwd = _find_tsconfig()
    if tsconfig_path is None or tsc_cwd is None:
        tsc_skipped = True
        tsc_stdout = "TypeScript validation skipped: tsconfig não encontrado."
        tsc_cmd = "(não executado — tsconfig ausente)"
        blocking.append("tsconfig não encontrado — tsc não executado.")
    else:
        tsc_exit, tsc_stdout, tsc_stderr, tsc_cmd = _run_tsc_validate(cwd=tsc_cwd)
        if tsc_exit == -1:
            blocking.append("npx não encontrado — tsc não executado.")
        elif tsc_exit == -2:
            blocking.append("Timeout ao executar tsc.")
        elif tsc_exit == -3:
            blocking.append(f"Erro ao executar tsc: {tsc_stderr}")
        elif tsc_exit != 0:
            blocking.append(f"`tsc --noEmit` retornou exit code {tsc_exit}.")

    summary["tsc_exit"] = tsc_exit
    summary["tsc_stdout"] = tsc_stdout
    summary["tsc_stderr"] = tsc_stderr
    summary["validate_cmd_display"] = tsc_cmd

    if not missing and not forbidden_hits and tsc_exit == 0:
        summary["real_validation"] = "APROVADO"
        summary["consolidated_status"] = "APROVADO COM EVIDÊNCIA REAL"
    else:
        summary["real_validation"] = "REPROVADO"
        summary["consolidated_status"] = "REPROVADO — correções obrigatórias"

    return summary, build_markdown()


def _build_repository_validate_existing_markdown(
    *,
    target_resolved: Path,
    action: str,
    physical_checks: dict[str, bool],
    forbidden_hits: list[str],
    tsc_exit: int | None,
    tsc_skipped: bool,
    tsc_stdout: str,
    tsc_stderr: str,
    tsc_cmd: str,
    evidence: str,
    real_validation: str,
    blocking: list[str] | None = None,
) -> str:
    if tsc_skipped:
        tsc_exit_display = "skipped"
        tsc_stdout_display = "TypeScript validation skipped: tsconfig não encontrado."
        tsc_stderr_display = ""
    else:
        tsc_exit_display = "(não executado)" if tsc_exit is None else str(tsc_exit)
        tsc_stdout_display = tsc_stdout or "(vazio)"
        tsc_stderr_display = tsc_stderr or "(vazio)"

    lines = [
        "# Validação dos Repository Contracts Existentes — CAP-BASE",
        "",
        "## Flag usada",
        "--validate-existing",
        "",
        "## Diretório alvo",
        str(target_resolved),
        "",
        "## Ação executada",
        action,
        "",
        "## Validação física dos arquivos",
        "",
    ]
    for filename in REQUIRED_REPOSITORY_FILENAMES:
        rel_key = "repositories/index.ts" if filename == "index.ts" else filename
        mark = "[x]" if physical_checks.get(rel_key) else "[ ]"
        lines.append(f"- {mark} {rel_key}")
    for rel_key in ("domain/entities/index.ts", "domain/index.ts", "src/index.ts"):
        mark = "[x]" if physical_checks.get(rel_key) else "[ ]"
        lines.append(f"- {mark} {rel_key}")
    lines.extend(["", "## Termos proibidos encontrados", ""])
    if forbidden_hits:
        for term in forbidden_hits:
            lines.append(f"- {term}")
    else:
        lines.append("- (nenhum)")
    lines.extend(
        [
            "",
            "## Resultado do tsc",
            tsc_exit_display,
            "",
            "stdout",
            "",
            "```text",
            tsc_stdout_display.rstrip(),
            "```",
            "",
            "stderr",
            "",
            "```text",
            tsc_stderr_display.rstrip(),
            "```",
            "",
            "## Comando executado",
            "",
            tsc_cmd or "(não executado)",
            "",
            "## Status da evidência física",
            evidence,
            "",
            "## Status da validação real",
            real_validation,
            "",
        ]
    )
    if blocking:
        lines.extend(["## Observações / bloqueios", "", "\n".join(f"- {item}" for item in blocking), ""])
    return "\n".join(lines).strip()


def _run_validate_existing_repository_contracts_phase() -> tuple[dict[str, Any], str]:
    """Valida repository contracts TypeScript já existentes sem sobrescrever nem chamar agentes/OpenAI."""
    target_resolved = CAP_BASE_REPOSITORIES_PATH.resolve()
    blocking: list[str] = []
    physical_checks: dict[str, bool] = {}
    forbidden_hits: list[str] = []
    tsc_exit: int | None = None
    tsc_skipped = False
    tsc_stdout = ""
    tsc_stderr = ""
    tsc_cmd = ""
    summary: dict[str, Any] = {
        "target_resolved": str(target_resolved),
        "action": "Validação dos repository contracts existentes (sem escrita)",
        "evidence": "AUSENTE",
        "real_validation": "REPROVADO",
        "tsc_exit": None,
        "tsc_skipped": False,
        "tsc_stdout": "",
        "tsc_stderr": "",
        "validate_cmd_display": "",
        "physical_checks": physical_checks,
        "forbidden_hits": forbidden_hits,
        "blocking_reasons": blocking,
        "consolidated_status": "REPROVADO — correções obrigatórias",
    }

    def build_markdown() -> str:
        return _build_repository_validate_existing_markdown(
            target_resolved=target_resolved,
            action=summary["action"],
            physical_checks=physical_checks,
            forbidden_hits=forbidden_hits,
            tsc_exit=tsc_exit,
            tsc_skipped=tsc_skipped,
            tsc_stdout=tsc_stdout,
            tsc_stderr=tsc_stderr,
            tsc_cmd=tsc_cmd,
            evidence=summary["evidence"],
            real_validation=summary["real_validation"],
            blocking=blocking or None,
        )

    if not CAP_BASE_REPOSITORIES_PATH.is_dir():
        blocking.append(f"Diretório inexistente no caminho esperado: {target_resolved}")
        return summary, build_markdown()

    physical_checks, missing, forbidden_hits = _validate_existing_repository_contract_files()
    summary["physical_checks"] = physical_checks
    summary["forbidden_hits"] = forbidden_hits
    summary["evidence"] = "PRESENTE" if not missing else "AUSENTE"

    if missing:
        blocking.append(f"Arquivos obrigatórios ausentes: {', '.join(missing)}.")
    if forbidden_hits:
        blocking.append(f"Termos proibidos nos arquivos existentes: {', '.join(forbidden_hits)}.")

    tsconfig_path, tsc_cwd = _find_tsconfig()
    if tsconfig_path is None or tsc_cwd is None:
        tsc_skipped = True
        tsc_stdout = "TypeScript validation skipped: tsconfig não encontrado."
        tsc_cmd = "(não executado — tsconfig ausente)"
        blocking.append("tsconfig não encontrado — tsc não executado.")
    else:
        tsc_exit, tsc_stdout, tsc_stderr, tsc_cmd = _run_tsc_validate(cwd=tsc_cwd)
        if tsc_exit == -1:
            blocking.append("npx não encontrado — tsc não executado.")
        elif tsc_exit == -2:
            blocking.append("Timeout ao executar tsc.")
        elif tsc_exit == -3:
            blocking.append(f"Erro ao executar tsc: {tsc_stderr}")
        elif tsc_exit != 0:
            blocking.append(f"`tsc --noEmit` retornou exit code {tsc_exit}.")

    summary["tsc_exit"] = tsc_exit
    summary["tsc_skipped"] = tsc_skipped
    summary["tsc_stdout"] = tsc_stdout
    summary["tsc_stderr"] = tsc_stderr
    summary["validate_cmd_display"] = tsc_cmd

    summary["real_validation"] = _compute_repository_real_validation_status(
        missing=missing,
        forbidden_hits=forbidden_hits,
        tsc_exit=tsc_exit,
        tsc_skipped=tsc_skipped,
    )
    if not missing and not forbidden_hits and tsc_exit == 0:
        summary["consolidated_status"] = "APROVADO COM EVIDÊNCIA REAL"
    else:
        summary["consolidated_status"] = "REPROVADO — correções obrigatórias"

    return summary, build_markdown()


def _build_validate_existing_final_markdown(
    *,
    demanda: str,
    timestamp: str,
    summary: dict[str, Any],
    write_out_rel: str,
) -> str:
    exit_disp = (
        "(não executado)" if summary["prisma_exit"] is None else str(summary["prisma_exit"])
    )
    lines = [
        "# Relatório final — squad CAP",
        "",
        "## Demanda original",
        "",
        demanda.strip(),
        "",
        "## Validação do arquivo existente (`--validate-existing`)",
        "",
        f"- **Arquivo alvo**: `{summary['target_resolved']}`",
        f"- **Ação executada**: {summary['action']}",
        f"- **Evidência física**: {summary['evidence']}",
        f"- **prisma validate**: {summary['real_validation']}",
        f"- **prisma validate (exit code)**: {exit_disp}",
        f"- **Relatório de evidência**: `{write_out_rel}`",
        "",
        "_Nenhum agente foi executado e nenhum arquivo foi sobrescrito neste run._",
        "",
        "## Status final consolidado",
        "",
        summary["consolidated_status"],
        "",
        "## Execução",
        "",
        "Fluxo `--validate-existing` concluído (sem OpenAI e sem agentes).",
        f"Timestamp da execução (UTC): `{timestamp}`",
        "",
    ]
    return "\n".join(lines).strip()


def _build_validate_existing_unsupported_delivery_final_markdown(
    *,
    demanda: str,
    timestamp: str,
    summary: dict[str, Any],
    write_out_rel: str,
) -> str:
    """Relatório final quando `--validate-existing` não se aplica ao tipo de entrega do run."""
    lines = [
        "# Relatório final — squad CAP",
        "",
        "## Demanda original",
        "",
        demanda.strip(),
        "",
        "## Validação existente (`--validate-existing`)",
        "",
        f"- **Ação executada**: {summary['action']}",
        f"- **Tipo inferido**: `{summary.get('delivery_type', 'desconhecido')}`",
        f"- **Relatório de evidência**: `{write_out_rel}`",
        "",
        "_Nenhum agente foi executado e nenhum arquivo foi sobrescrito neste run._",
        "",
        "## Status final consolidado",
        "",
        summary["consolidated_status"],
        "",
        "## Execução",
        "",
        "Fluxo `--validate-existing` encerrado sem validação de artefatos (tipo de entrega não suportado neste modo).",
        f"Timestamp da execução (UTC): `{timestamp}`",
        "",
    ]
    return "\n".join(lines).strip()


def _build_validate_existing_domain_final_markdown(
    *,
    demanda: str,
    timestamp: str,
    summary: dict[str, Any],
    write_out_rel: str,
) -> str:
    if summary.get("tsc_skipped"):
        tsc_status = "skipped (tsconfig não encontrado)"
    else:
        tsc_exit = summary.get("tsc_exit")
        tsc_status = "(não executado)" if tsc_exit is None else f"exit code {tsc_exit}"

    lines = [
        "# Relatório final — squad CAP",
        "",
        "## Demanda original",
        "",
        demanda.strip(),
        "",
        "## Domínio / Entidades CAP-BASE",
        "",
        "- **Caminho canônico**: `cap-platform/repos/cap-base/src/domain`",
        "",
        "## Validação do domínio existente (`--validate-existing`)",
        "",
        f"- **Diretório alvo**: `{summary['target_resolved']}`",
        f"- **Ação executada**: {summary['action']}",
        f"- **Evidência física**: {summary['evidence']}",
        f"- **Validação TypeScript (`tsc --noEmit`)**: {summary['real_validation']}",
        f"- **Resultado do `tsc --noEmit`**: {tsc_status}",
        f"- **Relatório de evidência**: `{write_out_rel}`",
        "",
        "_Nenhum agente foi executado e nenhum arquivo foi sobrescrito neste run._",
        "",
        "## Status final consolidado",
        "",
        summary["consolidated_status"],
        "",
        "## Execução",
        "",
        "Fluxo `--validate-existing` concluído (sem OpenAI e sem agentes).",
        f"Timestamp da execução (UTC): `{timestamp}`",
        "",
    ]
    return "\n".join(lines).strip()


def _build_validate_existing_repository_contracts_final_markdown(
    *,
    demanda: str,
    timestamp: str,
    summary: dict[str, Any],
    write_out_rel: str,
) -> str:
    if summary.get("tsc_skipped"):
        tsc_status = "skipped (tsconfig não encontrado)"
        tsc_exit_display = "skipped"
    else:
        tsc_exit = summary.get("tsc_exit")
        tsc_status = "(não executado)" if tsc_exit is None else f"exit code {tsc_exit}"
        tsc_exit_display = "(não executado)" if tsc_exit is None else str(tsc_exit)

    lines = [
        "# Relatório final — squad CAP",
        "",
        "## Demanda original",
        "",
        demanda.strip(),
        "",
        "## Repository Contracts CAP-BASE",
        "",
        "- **Caminho canônico**: `cap-platform/repos/cap-base/src/domain/repositories`",
        "",
        "## Validação dos repository contracts existentes (`--validate-existing`)",
        "",
        f"- **Diretório alvo**: `{summary['target_resolved']}`",
        f"- **Ação executada**: {summary['action']}",
        f"- **Evidência física**: {summary['evidence']}",
        f"- **Validação TypeScript (`tsc --noEmit`)**: {summary['real_validation']}",
        f"- **Resultado do `tsc --noEmit`**: {tsc_status}",
        f"- **Exit code do `tsc --noEmit`**: {tsc_exit_display}",
        f"- **Relatório de evidência**: `{write_out_rel}`",
        "",
        "_Nenhum agente foi executado e nenhum arquivo foi sobrescrito neste run._",
        "",
        "## Status final consolidado",
        "",
        summary["consolidated_status"],
        "",
        "## Execução",
        "",
        "Fluxo `--validate-existing` concluído (sem OpenAI e sem agentes).",
        f"Timestamp da execução (UTC): `{timestamp}`",
        "",
    ]
    return "\n".join(lines).strip()


def _run_write_files_phase(
    *,
    dev_output: str,
    validation_status: str,
    ts: str,
    target: Path,
) -> tuple[dict[str, Any], str]:
    """
    Materializa base.prisma quando permitido pela validação determinística.
    Executa apenas `npx prisma validate --schema <caminho>` como comando externo.
    """
    target_resolved = target.resolve()
    blocking: list[str] = []
    summary: dict[str, Any] = {
        "target_resolved": str(target_resolved),
        "action": "Não executado",
        "backup_path": None,
        "prisma_exit": None,
        "prisma_stdout": "",
        "prisma_stderr": "",
        "evidence": "AUSENTE",
        "real_validation": "REPROVADO",
        "blocking_reasons": blocking,
        "validate_cmd_display": "",
    }

    def build_markdown() -> str:
        return _build_prisma_evidence_markdown(
            flag_label="--write-files",
            target_resolved=target_resolved,
            action=summary["action"],
            backup_path=summary["backup_path"],
            validate_cmd_display=summary["validate_cmd_display"] or "(não executado)",
            prisma_exit=summary["prisma_exit"],
            prisma_stdout=summary["prisma_stdout"],
            prisma_stderr=summary["prisma_stderr"],
            evidence=summary["evidence"],
            real_validation=summary["real_validation"],
            blocking=blocking or None,
        )

    if validation_status == "REPROVADO":
        blocking.append("Validação determinística REPROVADO — escrita bloqueada.")
        return summary, build_markdown()

    if validation_status not in ("APROVÁVEL COM RESSALVAS", "APROVADO"):
        blocking.append(f"Status determinístico inesperado: {validation_status!r}.")
        return summary, build_markdown()

    schema = _extract_first_prisma_block(dev_output)
    if schema is None:
        blocking.append("Bloco ```prisma não encontrado na saída do Dev Base.")
        return summary, build_markdown()

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        blocking.append(f"Falha ao criar diretórios: {exc}")
        return summary, build_markdown()

    pending_action = "Criado"
    if target.is_file():
        backup_path = target.with_name(f"{target.name}.bak-{ts}")
        try:
            shutil.copy2(target, backup_path)
        except OSError as exc:
            blocking.append(f"Falha ao criar backup antes de sobrescrever: {exc}")
            return summary, build_markdown()
        summary["backup_path"] = str(backup_path.resolve())
        pending_action = "Sobrescrito com backup"

    try:
        target.write_text(schema + "\n", encoding="utf-8")
    except OSError as exc:
        blocking.append(f"Falha ao gravar arquivo: {exc}")
        return summary, build_markdown()

    summary["action"] = pending_action
    summary["evidence"] = "PRESENTE" if target.is_file() else "AUSENTE"

    exit_code, stdout, stderr, validate_cmd_display = _run_prisma_validate(target=target)
    summary["validate_cmd_display"] = validate_cmd_display
    summary["prisma_exit"] = exit_code
    summary["prisma_stdout"] = stdout
    summary["prisma_stderr"] = stderr
    if exit_code == -1:
        blocking.append("npx não encontrado — prisma validate não executado.")
    elif exit_code == -2:
        blocking.append("Timeout ao executar prisma validate.")
    elif exit_code == -3:
        blocking.append(f"Erro ao executar prisma validate: {stderr}")

    exit_code = summary["prisma_exit"]
    summary["real_validation"] = "APROVADO" if exit_code == 0 else "REPROVADO"
    summary["evidence"] = "PRESENTE" if target.is_file() else "AUSENTE"

    return summary, build_markdown()


def _build_domain_evidence_markdown(
    *,
    target_resolved: Path,
    created_files: list[str],
    backups: list[str],
    physical_checks: dict[str, bool],
    forbidden_hits: list[str],
    tsc_exit: int | None,
    tsc_skipped: bool,
    tsc_stdout: str,
    tsc_stderr: str,
    tsc_cmd: str,
    evidence: str,
    real_validation: str,
    blocking: list[str] | None = None,
) -> str:
    if tsc_skipped:
        tsc_exit_display = "skipped"
        tsc_stdout_display = "TypeScript validation skipped: tsconfig não encontrado."
        tsc_stderr_display = ""
    else:
        tsc_exit_display = "(não executado)" if tsc_exit is None else str(tsc_exit)
        tsc_stdout_display = tsc_stdout or "(vazio)"
        tsc_stderr_display = tsc_stderr or "(vazio)"

    lines = [
        "# Escrita de Arquivos — Domínio CAP-BASE",
        "",
        "## Flag usada",
        "--write-files",
        "",
        "## Diretório alvo",
        str(target_resolved),
        "",
        "## Arquivos criados",
        "",
    ]
    if created_files:
        for path in created_files:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum)")
    lines.extend(["", "## Backups criados", ""])
    if backups:
        for path in backups:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum)")
    lines.extend(["", "## Validação física dos arquivos", ""])
    for filename in REQUIRED_DOMAIN_ENTITY_FILENAMES:
        mark = "[x]" if physical_checks.get(filename) else "[ ]"
        lines.append(f"- {mark} {filename}")
    domain_index_mark = "[x]" if physical_checks.get("domain/index.ts") else "[ ]"
    src_index_mark = "[x]" if physical_checks.get("src/index.ts") else "[ ]"
    lines.append(f"- {domain_index_mark} domain/index.ts")
    lines.append(f"- {src_index_mark} src/index.ts")
    lines.extend(["", "## Termos proibidos encontrados", ""])
    if forbidden_hits:
        for term in forbidden_hits:
            lines.append(f"- {term}")
    else:
        lines.append("- (nenhum)")
    lines.extend(
        [
            "",
            "## Resultado do tsc",
            tsc_exit_display,
            "",
            "stdout",
            "",
            "```text",
            tsc_stdout_display.rstrip(),
            "```",
            "",
            "stderr",
            "",
            "```text",
            tsc_stderr_display.rstrip(),
            "```",
            "",
            "## Comando executado",
            "",
            tsc_cmd or "(não executado)",
            "",
            "## Status da evidência física",
            evidence,
            "",
            "## Status da validação real",
            real_validation,
            "",
        ]
    )
    if blocking:
        lines.extend(["## Observações / bloqueios", "", "\n".join(f"- {item}" for item in blocking), ""])
    return "\n".join(lines).strip()


def _run_write_files_domain_phase(
    *,
    dev_output: str,
    validation_status: str,
    ts: str,
) -> tuple[dict[str, Any], str]:
    """Materializa entidades TypeScript do domínio CAP-BASE quando permitido pela validação determinística."""
    target_resolved = CAP_BASE_DOMAIN_PATH.resolve()
    blocking: list[str] = []
    created_files: list[str] = []
    backups: list[str] = []
    physical_checks: dict[str, bool] = {name: False for name in REQUIRED_DOMAIN_ENTITY_FILENAMES}
    physical_checks["domain/index.ts"] = False
    physical_checks["src/index.ts"] = False
    forbidden_hits: list[str] = []
    tsc_exit: int | None = None
    tsc_skipped = False
    tsc_stdout = ""
    tsc_stderr = ""
    tsc_cmd = ""
    summary: dict[str, Any] = {
        "target_resolved": str(target_resolved),
        "action": "Não executado",
        "created_files": created_files,
        "backups": backups,
        "evidence": "AUSENTE",
        "real_validation": "REPROVADO",
        "tsc_exit": None,
        "tsc_skipped": False,
        "tsc_stdout": "",
        "tsc_stderr": "",
        "tsc_cmd": "",
        "physical_checks": physical_checks,
        "forbidden_hits": forbidden_hits,
        "blocking_reasons": blocking,
    }

    def build_markdown() -> str:
        return _build_domain_evidence_markdown(
            target_resolved=target_resolved,
            created_files=created_files,
            backups=backups,
            physical_checks=physical_checks,
            forbidden_hits=forbidden_hits,
            tsc_exit=tsc_exit,
            tsc_skipped=tsc_skipped,
            tsc_stdout=tsc_stdout,
            tsc_stderr=tsc_stderr,
            tsc_cmd=tsc_cmd,
            evidence=summary["evidence"],
            real_validation=summary["real_validation"],
            blocking=blocking or None,
        )

    if validation_status == "REPROVADO":
        blocking.append("Validação determinística REPROVADO — escrita bloqueada.")
        return summary, build_markdown()

    if validation_status not in ("APROVÁVEL COM RESSALVAS", "APROVADO"):
        blocking.append(f"Status determinístico inesperado: {validation_status!r}.")
        return summary, build_markdown()

    extracted = _extract_typescript_files_from_dev_output(dev_output)
    if not any(key.startswith("entities/") for key in extracted):
        blocking.append("Nenhum arquivo TypeScript de entidade encontrado na saída do Dev Base.")
        return summary, build_markdown()

    if "domain/index.ts" not in extracted:
        extracted["domain/index.ts"] = _build_domain_index_ts()
    if "src/index.ts" not in extracted:
        extracted["src/index.ts"] = _build_src_index_ts()

    actions: list[str] = []
    for file_key, content in sorted(extracted.items()):
        target = _resolve_domain_target_path(file_key)
        try:
            action, backup_path = _write_text_file_with_backup(target=target, content=content, ts=ts)
        except OSError as exc:
            blocking.append(f"Falha ao gravar {target}: {exc}")
            return summary, build_markdown()
        created_files.append(str(target.resolve()))
        actions.append(action)
        if backup_path:
            backups.append(backup_path)

    summary["action"] = (
        "Criado"
        if all(action == "Criado" for action in actions)
        else "Sobrescrito com backup"
        if any(action == "Sobrescrito com backup" for action in actions)
        else "Criado"
    )

    physical_checks, missing, forbidden_hits = _validate_written_domain_files()
    summary["physical_checks"] = physical_checks
    summary["forbidden_hits"] = forbidden_hits
    summary["evidence"] = "PRESENTE" if not missing else "AUSENTE"

    tsconfig_path, tsc_cwd = _find_tsconfig()
    if tsconfig_path is None or tsc_cwd is None:
        tsc_skipped = True
        tsc_stdout = "TypeScript validation skipped: tsconfig não encontrado."
        tsc_cmd = "(não executado — tsconfig ausente)"
    else:
        tsc_exit, tsc_stdout, tsc_stderr, tsc_cmd = _run_tsc_validate(cwd=tsc_cwd)
        if tsc_exit == -1:
            blocking.append("npx não encontrado — tsc não executado.")
        elif tsc_exit == -2:
            blocking.append("Timeout ao executar tsc.")
        elif tsc_exit == -3:
            blocking.append(f"Erro ao executar tsc: {tsc_stderr}")

    summary["tsc_exit"] = tsc_exit
    summary["tsc_skipped"] = tsc_skipped
    summary["tsc_stdout"] = tsc_stdout
    summary["tsc_stderr"] = tsc_stderr
    summary["tsc_cmd"] = tsc_cmd
    summary["real_validation"] = _compute_domain_real_validation_status(
        missing=missing,
        forbidden_hits=forbidden_hits,
        tsc_exit=tsc_exit,
        tsc_skipped=tsc_skipped,
    )
    if missing:
        blocking.append(f"Arquivos obrigatórios ausentes após escrita: {', '.join(missing)}.")
    if forbidden_hits:
        blocking.append(f"Termos proibidos nos arquivos gravados: {', '.join(forbidden_hits)}.")
    if not tsc_skipped and tsc_exit not in (0, None):
        blocking.append(f"`tsc --noEmit` retornou exit code {tsc_exit}.")

    return summary, build_markdown()


def _build_repository_evidence_markdown(
    *,
    target_resolved: Path,
    created_files: list[str],
    backups: list[str],
    physical_checks: dict[str, bool],
    forbidden_hits: list[str],
    tsc_exit: int | None,
    tsc_skipped: bool,
    tsc_stdout: str,
    tsc_stderr: str,
    tsc_cmd: str,
    evidence: str,
    real_validation: str,
    deterministic: bool,
    blocking: list[str] | None = None,
) -> str:
    if tsc_skipped:
        tsc_exit_display = "skipped"
        tsc_stdout_display = "TypeScript validation skipped: tsconfig não encontrado."
        tsc_stderr_display = ""
    else:
        tsc_exit_display = "(não executado)" if tsc_exit is None else str(tsc_exit)
        tsc_stdout_display = tsc_stdout or "(vazio)"
        tsc_stderr_display = tsc_stderr or "(vazio)"

    lines = [
        "# Escrita de Arquivos — Repository Contracts CAP-BASE",
        "",
        "## Flag usada",
        "--write-files",
        "",
        "## Modo de materialização",
        "Determinística (orquestrador)" if deterministic else "Blocos TypeScript do Dev Base",
        "",
        "## Diretório alvo",
        str(target_resolved),
        "",
        "## Arquivos criados",
        "",
    ]
    if created_files:
        for path in created_files:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum)")
    lines.extend(["", "## Backups criados", ""])
    if backups:
        for path in backups:
            lines.append(f"- {path}")
    else:
        lines.append("- (nenhum)")
    lines.extend(["", "## Validação física dos arquivos", ""])
    for filename in REQUIRED_REPOSITORY_FILENAMES:
        mark = "[x]" if physical_checks.get(filename) else "[ ]"
        lines.append(f"- {mark} {filename}")
    lines.extend(["", "## Termos proibidos encontrados", ""])
    if forbidden_hits:
        for term in forbidden_hits:
            lines.append(f"- {term}")
    else:
        lines.append("- (nenhum)")
    lines.extend(
        [
            "",
            "## Resultado do tsc",
            tsc_exit_display,
            "",
            "stdout",
            "",
            "```text",
            tsc_stdout_display.rstrip(),
            "```",
            "",
            "stderr",
            "",
            "```text",
            tsc_stderr_display.rstrip(),
            "```",
            "",
            "## Comando executado",
            "",
            tsc_cmd or "(não executado)",
            "",
            "## Status da evidência física",
            evidence,
            "",
            "## Status da validação real",
            real_validation,
            "",
        ]
    )
    if blocking:
        lines.extend(["## Observações / bloqueios", "", "\n".join(f"- {item}" for item in blocking), ""])
    return "\n".join(lines).strip()


def _run_write_files_repository_contracts_phase(
    *,
    dev_output: str,
    validation_status: str,
    ts: str,
    run_dir: Path,
    demanda: str,
    project: str = "cap",
) -> tuple[dict[str, Any], str]:
    """Materializa contratos de repositório TypeScript quando permitido pela validação determinística."""
    target_resolved = CAP_BASE_REPOSITORIES_PATH.resolve()
    blocking: list[str] = []
    created_files: list[str] = []
    backups: list[str] = []
    physical_checks: dict[str, bool] = {name: False for name in REQUIRED_REPOSITORY_FILENAMES}
    forbidden_hits: list[str] = []
    tsc_exit: int | None = None
    tsc_skipped = False
    tsc_stdout = ""
    tsc_stderr = ""
    tsc_cmd = ""
    deterministic = _should_deterministic_repository_contracts_write(
        project=project,
        run_dir=run_dir,
        demanda=demanda,
    )
    summary: dict[str, Any] = {
        "target_resolved": str(target_resolved),
        "action": "Não executado",
        "created_files": created_files,
        "backups": backups,
        "evidence": "AUSENTE",
        "real_validation": "REPROVADO",
        "tsc_exit": None,
        "tsc_skipped": False,
        "tsc_stdout": "",
        "tsc_stderr": "",
        "tsc_cmd": "",
        "physical_checks": physical_checks,
        "forbidden_hits": forbidden_hits,
        "blocking_reasons": blocking,
        "deterministic": deterministic,
    }

    def build_markdown() -> str:
        return _build_repository_evidence_markdown(
            target_resolved=target_resolved,
            created_files=created_files,
            backups=backups,
            physical_checks=physical_checks,
            forbidden_hits=forbidden_hits,
            tsc_exit=tsc_exit,
            tsc_skipped=tsc_skipped,
            tsc_stdout=tsc_stdout,
            tsc_stderr=tsc_stderr,
            tsc_cmd=tsc_cmd,
            evidence=summary["evidence"],
            real_validation=summary["real_validation"],
            deterministic=deterministic,
            blocking=blocking or None,
        )

    if deterministic:
        blocking.append(
            "Materialização determinística habilitada — blocos TypeScript do Dev Base não são fonte da escrita."
        )
        if validation_status == "REPROVADO":
            blocking.append(
                "Validação determinística do Dev Base REPROVADO — não bloqueia a escrita determinística."
            )
        extracted = _build_deterministic_repository_files()
        if CAP_BASE_DOMAIN_INDEX_PATH.is_file():
            current_domain_index = CAP_BASE_DOMAIN_INDEX_PATH.read_text(encoding="utf-8")
            updated_domain_index = _ensure_domain_index_entities_and_repositories(current_domain_index)
            if updated_domain_index != current_domain_index:
                extracted["domain/index.ts"] = updated_domain_index
        else:
            extracted["domain/index.ts"] = _build_domain_index_with_entities_and_repositories()
    else:
        if validation_status == "REPROVADO":
            blocking.append("Validação determinística REPROVADO — escrita bloqueada.")
            return summary, build_markdown()

        if validation_status not in ("APROVÁVEL COM RESSALVAS", "APROVADO"):
            blocking.append(f"Status determinístico inesperado: {validation_status!r}.")
            return summary, build_markdown()

        extracted = _extract_repository_typescript_files_from_dev_output(dev_output)
        if not any(key.startswith("repositories/") and key != "repositories/index.ts" for key in extracted):
            blocking.append("Nenhum arquivo TypeScript de repositório encontrado na saída do Dev Base.")
            return summary, build_markdown()

        if "repositories/index.ts" not in extracted:
            extracted["repositories/index.ts"] = _build_repositories_index_ts()

        if "domain/index.ts" in extracted:
            extracted["domain/index.ts"] = _ensure_domain_index_exports_repositories(extracted["domain/index.ts"])
        elif CAP_BASE_DOMAIN_INDEX_PATH.is_file():
            current_domain_index = CAP_BASE_DOMAIN_INDEX_PATH.read_text(encoding="utf-8")
            updated_domain_index = _ensure_domain_index_exports_repositories(current_domain_index)
            if updated_domain_index != current_domain_index:
                extracted["domain/index.ts"] = updated_domain_index
        else:
            blocking.append(
                "domain/index.ts ausente — não foi possível exportar ./repositories sem alterar src/index.ts."
            )
            return summary, build_markdown()

    actions: list[str] = []
    for file_key, content in sorted(extracted.items()):
        target = _resolve_repository_target_path(file_key)
        try:
            action, backup_path = _write_text_file_with_backup(target=target, content=content, ts=ts)
        except OSError as exc:
            blocking.append(f"Falha ao gravar {target}: {exc}")
            return summary, build_markdown()
        created_files.append(str(target.resolve()))
        actions.append(action)
        if backup_path:
            backups.append(backup_path)

    summary["action"] = (
        "Criado"
        if all(action == "Criado" for action in actions)
        else "Sobrescrito com backup"
        if any(action == "Sobrescrito com backup" for action in actions)
        else "Criado"
    )

    physical_checks, missing, forbidden_hits = _validate_written_repository_files()
    summary["physical_checks"] = physical_checks
    summary["forbidden_hits"] = forbidden_hits
    summary["evidence"] = "PRESENTE" if not missing else "AUSENTE"

    tsconfig_path, tsc_cwd = _find_tsconfig()
    if tsconfig_path is None or tsc_cwd is None:
        tsc_skipped = True
        tsc_stdout = "TypeScript validation skipped: tsconfig não encontrado."
    else:
        tsc_exit, tsc_stdout, tsc_stderr, tsc_cmd = _run_tsc_validate(cwd=tsc_cwd)
        if tsc_exit == -1:
            blocking.append("npx não encontrado — tsc não executado.")
        elif tsc_exit == -2:
            blocking.append("Timeout ao executar tsc.")
        elif tsc_exit == -3:
            blocking.append(f"Erro ao executar tsc: {tsc_stderr}")

    summary["tsc_exit"] = tsc_exit
    summary["tsc_skipped"] = tsc_skipped
    summary["tsc_stdout"] = tsc_stdout
    summary["tsc_stderr"] = tsc_stderr
    summary["tsc_cmd"] = tsc_cmd
    summary["real_validation"] = _compute_repository_real_validation_status(
        missing=missing,
        forbidden_hits=forbidden_hits,
        tsc_exit=tsc_exit,
        tsc_skipped=tsc_skipped,
    )
    if missing:
        blocking.append(f"Arquivos obrigatórios ausentes após escrita: {', '.join(missing)}.")
    if forbidden_hits:
        blocking.append(f"Termos proibidos nos arquivos gravados: {', '.join(forbidden_hits)}.")
    if not tsc_skipped and tsc_exit not in (0, None):
        blocking.append(f"`tsc --noEmit` retornou exit code {tsc_exit}.")

    return summary, build_markdown()


def _load_context_bundle() -> dict[str, str]:
    labels = [
        "fonte oficial",
        "organização dos projetos prioritários",
        "contexto CAP",
        "standards CAP",
        "decisions CAP",
        "backlog CAP",
        "workflow da squad CAP",
        "task-policy da squad CAP",
    ]
    bundle: dict[str, str] = {}
    for label, path in zip(labels, CONTEXT_FILES, strict=True):
        bundle[label] = _read_text(path, label)
    return bundle


def _build_shared_context_block(bundle: dict[str, str]) -> str:
    parts: list[str] = []
    for title, body in bundle.items():
        parts.append(f"## {title.upper()}\n\n{body.strip()}\n")
    return "\n".join(parts)


def _build_user_prompt(
    *,
    shared_context: str,
    demanda: str,
    previous_outputs: dict[str, str],
) -> str:
    prev_section = ""
    if previous_outputs:
        blocks: list[str] = []
        order = ["po", "architect", "dev-base", "validation", "reviewer", "qa"]
        for key in order:
            if key not in previous_outputs:
                continue
            body = previous_outputs[key].strip()
            if key == "validation":
                blocks.append(f"### Validação determinística (orquestrador)\n\n{body}\n")
            else:
                blocks.append(f"### Saída do agente: {key}\n\n{body}\n")
        prev_section = "## SAÍDAS E VALIDAÇÕES ANTERIORES\n\n" + "\n".join(blocks) + "\n"

    return textwrap.dedent(
        f"""\
        Você está executando uma etapa da squad CAP. Use todo o contexto abaixo.

        {shared_context}

        ## DEMANDA ORIGINAL

        {demanda.strip()}

        {prev_section}
        """
    ).strip()


def _build_meta_orchestrator_user_prompt(*, shared_context: str, demanda: str) -> str:
    return textwrap.dedent(
        f"""\
        Você está no **Modo plano de execução (Markdown)** do meta-orquestrador.
        Não há saídas de outros agentes nesta execução.

        Use o contexto do repositório abaixo e a demanda do run.

        {shared_context}

        ## DEMANDA DO RUN (input.md)

        {demanda.strip()}

        Produza **somente** o Markdown no formato obrigatório definido nas suas instruções
        (começando por `# Plano de Execução — Meta-orquestrador`).
        """
    ).strip()


def _validate_meta_plan_structure(plan_md: str) -> tuple[str, list[str]]:
    """Checagem determinística mínima da estrutura do plano em Markdown."""
    required_markers = [
        "# Plano de Execução",
        "## 1.",
        "## 2.",
        "## 3.",
        "## 4.",
        "## 5.",
        "## 6.",
        "## 7.",
        "## 8.",
        "## 9.",
        "AGUARDANDO APROVAÇÃO HUMANA",
    ]
    missing = [m for m in required_markers if m not in plan_md]
    if missing:
        status = "REPROVADO — faltam marcadores estruturais: " + ", ".join(missing)
    else:
        status = "APROVADO — estrutura mínima do plano presente"
    return status, missing


def _build_meta_orchestrator_final_markdown(
    *,
    demanda: str,
    timestamp: str,
    plan_md: str,
    structure_status: str,
    missing_markers: list[str],
    run_rel_meta: str,
    out_rel_meta: str,
) -> str:
    lines: list[str] = [
        "# Run — Meta-orquestrador (execução isolada)",
        "",
        f"- **Timestamp (UTC)**: `{timestamp}`",
        "- **Agente**: meta-orquestrador (`--agent meta-orchestrator`)",
        "",
        "## Validação determinística (estrutura do plano)",
        "",
        f"- **Resultado**: {structure_status}",
    ]
    if missing_markers:
        lines.append("")
        lines.append("- **Marcadores ausentes:**")
        for m in missing_markers:
            lines.append(f"  - `{m}`")
    lines.extend(
        [
            "",
            "## Artefatos gerados",
            "",
            f"- **Run**: `{run_rel_meta}`",
            f"- **Outputs cap**: `{out_rel_meta}`",
            "",
            "## Demanda original (entrada)",
            "",
            demanda.strip(),
            "",
            "## Plano completo (saída do modelo)",
            "",
            plan_md.strip(),
        ]
    )
    return "\n".join(lines).strip() + "\n"


def _run_meta_orchestrator_flow(
    *,
    client: OpenAI,
    model: str,
    demanda: str,
    run_dir: Path,
    outputs_cap: Path,
    timestamp: str,
) -> None:
    bundle = _load_context_bundle()
    shared_context = _build_shared_context_block(bundle)
    agent_instructions = _read_text(META_ORCHESTRATOR_INSTRUCTIONS_PATH, "meta-orchestrator")
    user_prompt = _build_meta_orchestrator_user_prompt(
        shared_context=shared_context,
        demanda=demanda,
    )
    plan_md = _run_agent(
        client=client,
        model=model,
        agent_key="meta-orchestrator",
        agent_instructions=agent_instructions,
        user_prompt=user_prompt,
    )
    structure_status, missing = _validate_meta_plan_structure(plan_md)

    meta_run_path = run_dir / "meta-orchestrator-output.md"
    meta_out_path = outputs_cap / f"{timestamp}-meta-orchestrator.md"
    meta_run_path.write_text(plan_md + "\n", encoding="utf-8")
    meta_out_path.write_text(plan_md + "\n", encoding="utf-8")

    run_rel_meta = str(meta_run_path.relative_to(ROOT)).replace("\\", "/")
    out_rel_meta = str(meta_out_path.relative_to(ROOT)).replace("\\", "/")

    final_body = _build_meta_orchestrator_final_markdown(
        demanda=demanda,
        timestamp=timestamp,
        plan_md=plan_md,
        structure_status=structure_status,
        missing_markers=missing,
        run_rel_meta=run_rel_meta,
        out_rel_meta=out_rel_meta,
    )
    final_run = run_dir / "final.md"
    final_out = outputs_cap / f"{timestamp}-final.md"
    final_run.write_text(final_body, encoding="utf-8")
    final_out.write_text(final_body, encoding="utf-8")

    print(f"meta-orchestrator-output.md: {meta_run_path.resolve()}")
    print(f"final.md: {final_run.resolve()}")
    print(f"outputs: {meta_out_path.resolve()} e {final_out.resolve()}")
    print(f"Validação estrutural do plano: {structure_status}")


def _run_agent(
    *,
    client: OpenAI,
    model: str,
    agent_key: str,
    agent_instructions: str,
    user_prompt: str,
) -> str:
    if agent_key == "meta-orchestrator":
        system = textwrap.dedent(
            f"""\
            Você é o meta-orquestrador do repositório squad-agentes.
            Siga estritamente as instruções do seu papel.

            --- INSTRUÇÕES DO PAPEL (meta-orquestrador) ---

            {agent_instructions.strip()}
            """
        ).strip()
    else:
        system = textwrap.dedent(
            f"""\
            Você é um agente da squad CAP. Siga estritamente as instruções do seu papel.

            --- INSTRUÇÕES DO PAPEL ({agent_key}) ---

            {agent_instructions.strip()}
            """
        ).strip()

    try:
        response = client.chat.completions.create(
            model=model,
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
    except Exception as exc:  # pragma: no cover - fallback
        _die(f"Erro inesperado na chamada OpenAI: {exc}")

    choice = response.choices[0].message
    content = choice.content
    if content is None:
        _die("Erro na chamada OpenAI: resposta sem conteúdo (content vazio).")
    return content.strip()


def _preview(text: str, max_chars: int = 400) -> str:
    t = text.strip()
    if len(t) <= max_chars:
        return t
    return t[:max_chars].rstrip() + "\n\n…"


def _extract_validation_result_summary(validation_markdown: str) -> str:
    m = re.search(r"## Resultado\s*\n+([\s\S]*?)(?=\n## |\Z)", validation_markdown)
    if not m:
        return "(sem seção Resultado na validação determinística)"
    return m.group(1).strip()


def _parse_physical_evidence(validation_markdown: str) -> bool:
    patterns = (
        r"## Evidência física do arquivo\s*\n(Presente|Ausente)\b",
        r"## Evidência física dos arquivos\s*\n(Presente|Ausente)\b",
    )
    for pattern in patterns:
        m = re.search(pattern, validation_markdown)
        if m:
            return m.group(1) == "Presente"
    return False


def _consolidated_final_paragraph(
    validation_status: str,
    physical_from_validation: bool,
    write_files_flag: bool,
    write_summary: dict[str, Any] | None,
    delivery_type: str,
) -> str:
    lines: list[str] = ["Status final consolidado:", ""]

    deterministic_repo = bool(
        delivery_type == "repository-contracts"
        and write_files_flag
        and write_summary
        and write_summary.get("deterministic")
    )

    if validation_status == "REPROVADO" and not deterministic_repo:
        if delivery_type == "domain":
            lines.append(
                "REPROVADO — correções obrigatórias antes de materializar entidades TypeScript no domínio CAP-BASE."
            )
        elif delivery_type == "repository-contracts":
            lines.append(
                "REPROVADO — correções obrigatórias antes de materializar contratos de repositório no CAP-BASE."
            )
        elif delivery_type == "database":
            lines.append("REPROVADO — correções obrigatórias antes de gerar arquivo real.")
        else:
            lines.append("REPROVADO — correções obrigatórias antes de prosseguir com a entrega.")
        return "\n".join(lines)

    if write_files_flag and write_summary:
        if delivery_type == "domain":
            lines.append(
                f"- Validação determinística de domínio (snapshot após Dev): **{validation_status}** "
                f"(evidência física nesse momento: **{'Presente' if physical_from_validation else 'Ausente'}**)."
            )
        elif delivery_type == "repository-contracts":
            lines.append(
                f"- Validação determinística de repository contracts (snapshot após Dev): **{validation_status}** "
                f"(evidência física nesse momento: **{'Presente' if physical_from_validation else 'Ausente'}**)."
            )
            if deterministic_repo:
                lines.append(
                    "- Materialização em disco: **determinística** (orquestrador; não usou blocos TypeScript do Dev Base)."
                )
        elif delivery_type == "database":
            lines.append(
                f"- Validação determinística (snapshot após Dev): **{validation_status}** "
                f"(evidência física nesse momento: **{'Presente' if physical_from_validation else 'Ausente'}**)."
            )
        else:
            lines.append(
                f"- Validação determinística genérica (snapshot após Dev): **{validation_status}**."
            )
        lines.append(f"- Ação de escrita (`--write-files`): **{write_summary['action']}**.")
        if delivery_type == "repository-contracts":
            lines.append(
                f"- Evidência física dos arquivos TypeScript após escrita: **{write_summary['evidence']}**."
            )
            if write_summary.get("tsc_skipped"):
                lines.append("- Validação TypeScript (`tsc --noEmit`): **skipped** (tsconfig não encontrado).")
            else:
                tsc_exit = write_summary.get("tsc_exit")
                tsc_exit_disp = "(não executado)" if tsc_exit is None else str(tsc_exit)
                lines.append(
                    f"- Validação TypeScript (`tsc --noEmit`): **{write_summary['real_validation']}** "
                    f"(exit code: {tsc_exit_disp})."
                )
            lines.append("")
            if write_summary["action"] == "Não executado":
                lines.append(
                    "Nenhum contrato de repositório foi gravado ou a escrita foi bloqueada — detalhes em "
                    "`write-files-output.md`."
                )
            elif write_summary["real_validation"] != "APROVADO":
                lines.append(
                    "Contratos de repositório podem ter sido gravados, porém a validação física ou o `tsc` não "
                    "aprovou — conferir `write-files-output.md`."
                )
            elif deterministic_repo:
                lines.append(
                    "APROVADO COM EVIDÊNCIA REAL — materialização determinística concluída; a reprovação textual do "
                    "Dev Base não bloqueou a escrita; aprovação final baseada na evidência física e no `tsc --noEmit`."
                )
            else:
                lines.append(
                    "Materialização dos contratos de repositório concluída e validação real aprovada — conferir diff "
                    "no repositório e o parecer do QA."
                )
            if deterministic_repo and validation_status == "REPROVADO":
                lines.append(
                    "A validação determinística do Dev Base pode ter reprovado; a materialização foi controlada pelo "
                    "orquestrador e o status final considera a validação real dos arquivos escritos."
                )
            return "\n".join(lines)
        if delivery_type == "domain":
            lines.append(f"- Evidência física dos arquivos TypeScript após escrita: **{write_summary['evidence']}**.")
            if write_summary.get("tsc_skipped"):
                lines.append("- Validação TypeScript (`tsc --noEmit`): **skipped** (tsconfig não encontrado).")
            else:
                tsc_exit = write_summary.get("tsc_exit")
                tsc_exit_disp = "(não executado)" if tsc_exit is None else str(tsc_exit)
                lines.append(
                    f"- Validação TypeScript (`tsc --noEmit`): **{write_summary['real_validation']}** "
                    f"(exit code: {tsc_exit_disp})."
                )
            lines.append("")
            if write_summary["action"] == "Não executado":
                lines.append(
                    "Nenhum arquivo de domínio foi gravado ou a escrita foi bloqueada — detalhes em "
                    "`write-files-output.md`."
                )
            elif write_summary["real_validation"] != "APROVADO":
                lines.append(
                    "Arquivos de domínio podem ter sido gravados, porém a validação física ou o `tsc` não aprovou — "
                    "conferir `write-files-output.md`."
                )
            else:
                lines.append(
                    "Materialização do domínio concluída e validação real aprovada — conferir diff no repositório e "
                    "o parecer do QA."
                )
            return "\n".join(lines)

        if delivery_type != "database":
            lines.append("")
            lines.append(
                "Nenhum arquivo foi gravado ou a escrita foi bloqueada — detalhes em `write-files-output.md`."
            )
            return "\n".join(lines)

        exit_code = write_summary["prisma_exit"]
        lines.append(f"- Evidência física após escrita: **{write_summary['evidence']}**.")
        lines.append(
            f"- Validação real (`npx prisma validate`): **{write_summary['real_validation']}** "
            f"(exit code: {exit_code})."
        )
        lines.append("")
        if write_summary["action"] == "Não executado":
            lines.append(
                "Nenhum arquivo foi gravado ou a escrita foi bloqueada — detalhes em `write-files-output.md`."
            )
        elif write_summary["real_validation"] != "APROVADO":
            lines.append(
                "Arquivo pode ter sido gravado, porém o `prisma validate` falhou — corrigir schema ou ambiente "
                "antes de aprovar."
            )
        else:
            lines.append(
                "Materialização concluída e `npx prisma validate` retornou sucesso — conferir diff no repositório e "
                "o parecer do QA."
            )
        return "\n".join(lines)

    if validation_status == "APROVÁVEL COM RESSALVAS":
        if delivery_type == "domain":
            lines.append(
                "APROVÁVEL COM RESSALVAS — sem reprovação estrutural imediata; sem `--write-files`, "
                "nenhuma entidade TypeScript foi materializada neste run em "
                "`cap-platform/repos/cap-base/src/domain`."
            )
        elif delivery_type == "repository-contracts":
            lines.append(
                "APROVÁVEL COM RESSALVAS — sem reprovação estrutural imediata; sem `--write-files`, "
                "nenhum contrato de repositório foi materializado neste run em "
                "`cap-platform/repos/cap-base/src/domain/repositories`."
            )
        elif delivery_type == "database":
            lines.append(
                "APROVÁVEL COM RESSALVAS — sem reprovação estrutural imediata; sem `--write-files`, "
                "nenhum arquivo foi materializado neste run no `cap-platform`."
            )
        else:
            lines.append(
                "APROVÁVEL COM RESSALVAS — sem reprovação estrutural imediata; sem `--write-files`, "
                "nenhuma materialização foi feita neste run."
            )
        return "\n".join(lines)

    if delivery_type == "domain":
        lines.append(
            "APROVADO na validação determinística estrutural de domínio — sem `--write-files`, o aceite de "
            "materialização depende de rodada futura com flag (evidência física dos arquivos TypeScript no snapshot "
            f"da validação: **{'Presente' if physical_from_validation else 'Ausente'}**)."
        )
        return "\n".join(lines)

    if delivery_type == "repository-contracts":
        lines.append(
            "APROVADO na validação determinística estrutural de repository contracts — sem `--write-files`, o aceite "
            "de materialização depende de rodada futura com flag (evidência física dos arquivos TypeScript no snapshot "
            f"da validação: **{'Presente' if physical_from_validation else 'Ausente'}**)."
        )
        return "\n".join(lines)

    if delivery_type == "database":
        lines.append(
            "APROVADO na validação determinística estrutural — sem `--write-files`, o aceite de materialização "
            f"depende de rodada futura com flag (evidência física no snapshot da validação: "
            f"**{'Presente' if physical_from_validation else 'Ausente'}**)."
        )
        return "\n".join(lines)

    lines.append(
        "APROVADO na validação determinística genérica — sem `--write-files`, o aceite depende de validação dedicada "
        "e evidência física futura."
    )
    return "\n".join(lines)


def _terminal_consolidated_status(
    validation_status: str,
    write_files_flag: bool,
    write_summary: dict[str, Any] | None,
    delivery_type: str,
) -> str:
    deterministic_repo = bool(
        delivery_type == "repository-contracts"
        and write_files_flag
        and write_summary
        and write_summary.get("deterministic")
    )
    if validation_status == "REPROVADO" and not deterministic_repo:
        if delivery_type == "domain":
            return "REPROVADO — correções obrigatórias antes de materializar domínio TypeScript."
        if delivery_type == "repository-contracts":
            return "REPROVADO — correções obrigatórias antes de materializar repository contracts."
        if delivery_type == "database":
            return "REPROVADO — correções obrigatórias antes de gerar arquivo real."
        return "REPROVADO — correções obrigatórias antes de prosseguir com a entrega."
    if write_files_flag and write_summary:
        if delivery_type == "repository-contracts":
            if write_summary["action"] == "Não executado":
                return "Escrita de repository contracts não executada — ver write-files-output.md."
            if write_summary["real_validation"] == "APROVADO":
                if deterministic_repo:
                    return (
                        "APROVADO COM EVIDÊNCIA REAL — materialização determinística concluída e validação real "
                        "APROVADA."
                    )
                return "Materialização de repository contracts concluída e validação real APROVADA."
            if write_summary["real_validation"] == "APROVÁVEL COM RESSALVAS":
                return (
                    "Materialização de repository contracts registrada com ressalvas — ver write-files-output.md."
                )
            return (
                "Materialização de repository contracts registrada, mas validação real REPROVADA — "
                "ver write-files-output.md."
            )
        if delivery_type == "domain":
            if write_summary["action"] == "Não executado":
                return "Escrita de domínio não executada — ver write-files-output.md."
            if write_summary["real_validation"] == "APROVADO":
                return "Materialização de domínio concluída e validação real APROVADA."
            if write_summary["real_validation"] == "APROVÁVEL COM RESSALVAS":
                return "Materialização de domínio registrada com ressalvas — ver write-files-output.md."
            return "Materialização de domínio registrada, mas validação real REPROVADA — ver write-files-output.md."
        if delivery_type != "database":
            return "Escrita em disco não executada — ver write-files-output.md."
        if write_summary["action"] == "Não executado":
            return "Escrita em disco não executada — ver write-files-output.md."
        if write_summary["real_validation"] != "APROVADO":
            return "Materialização registrada, mas prisma validate REPROVADO — ver write-files-output.md."
        return "Materialização concluída e prisma validate APROVADO."
    if validation_status == "APROVÁVEL COM RESSALVAS":
        if delivery_type == "domain":
            return "APROVÁVEL COM RESSALVAS — sem materialização de domínio neste run."
        if delivery_type == "repository-contracts":
            return "APROVÁVEL COM RESSALVAS — sem materialização de repository contracts neste run."
        return "APROVÁVEL COM RESSALVAS — sem escrita em disco neste run."
    if delivery_type == "domain":
        return "APROVADO (validação determinística de domínio) — sem escrita em disco neste run."
    if delivery_type == "repository-contracts":
        return "APROVADO (validação determinística de repository contracts) — sem escrita em disco neste run."
    if delivery_type == "database":
        return "APROVADO (validação determinística) — sem escrita em disco neste run."
    return "APROVADO (validação determinística genérica) — sem escrita em disco neste run."


def _build_final_markdown(
    *,
    demanda: str,
    outputs: dict[str, str],
    timestamp: str,
    validation_status: str,
    validation_markdown: str,
    validation_run_rel: str,
    validation_output_rel: str,
    write_files_flag: bool,
    write_summary: dict[str, Any] | None,
    write_run_rel: str,
    write_out_rel: str,
    output_files: list[str],
    run_files: list[str],
    delivery_type: str,
) -> str:
    val_status = validation_status
    physical = _parse_physical_evidence(validation_markdown)
    val_summary = _extract_validation_result_summary(validation_markdown)

    lines: list[str] = [
        "# Relatório final — squad CAP",
        "",
        "## Demanda original",
        "",
        demanda.strip(),
        "",
    ]

    if delivery_type == "domain":
        lines.extend(
            [
                "## Domínio / Entidades CAP-BASE",
                "",
                "- **Caminho canônico**: `cap-platform/repos/cap-base/src/domain`",
                f"- **Status da validação determinística de domínio**: {val_status}",
                f"- **Evidência física dos arquivos TypeScript (snapshot após Dev)**: "
                f"{'Presente' if physical else 'Ausente'}",
                "- **Arquivos da validação**:",
                f"  - `{validation_run_rel}`",
                f"  - `{validation_output_rel}`",
                "",
                "_Esta evidência reflete o momento da validação determinística de domínio, antes de "
                "`--write-files` (se usado)._",
                "",
                "### Resumo da validação de domínio",
                "",
                val_summary,
                "",
                "## Materialização em disco (`--write-files`)",
                "",
            ]
        )
    elif delivery_type == "repository-contracts":
        lines.extend(
            [
                "## Contratos / Interfaces de Repositório CAP-BASE",
                "",
                "- **Caminho canônico**: `cap-platform/repos/cap-base/src/domain/repositories`",
                f"- **Status da validação determinística de repository contracts**: {val_status}",
                f"- **Evidência física dos arquivos TypeScript (snapshot após Dev)**: "
                f"{'Presente' if physical else 'Ausente'}",
                "- **Arquivos da validação**:",
                f"  - `{validation_run_rel}`",
                f"  - `{validation_output_rel}`",
                "",
                "_Esta evidência reflete o momento da validação determinística de repository contracts, antes de "
                "`--write-files` (se usado)._",
                "",
                "### Resumo da validação de repository contracts",
                "",
                val_summary,
                "",
                "## Materialização em disco (`--write-files`)",
                "",
            ]
        )
    elif delivery_type == "database":
        lines.extend(
            [
                "## Validação determinística",
                "",
                f"- **Status**: {val_status}",
                f"- **Evidência física de `base.prisma` (snapshot após Dev)**: "
                f"{'Presente' if physical else 'Ausente'}",
                "- **Arquivos da validação**:",
                f"  - `{validation_run_rel}`",
                f"  - `{validation_output_rel}`",
                "",
                "_Esta evidência reflete o momento da validação determinística, antes de `--write-files` (se usado)._",
                "",
                "### Resumo da validação",
                "",
                val_summary,
                "",
                "## Materialização em disco (`--write-files`)",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Validação determinística genérica",
                "",
                f"- **Status**: {val_status}",
                "- **Arquivos da validação**:",
                f"  - `{validation_run_rel}`",
                f"  - `{validation_output_rel}`",
                "",
                "_Esta evidência reflete o momento da validação determinística genérica, antes de "
                "`--write-files` (se usado)._",
                "",
                "### Resumo da validação",
                "",
                val_summary,
                "",
                "## Materialização em disco (`--write-files`)",
                "",
            ]
        )

    if not write_files_flag:
        if delivery_type == "domain":
            lines.extend(
                [
                    "Flag **não** utilizada. Nenhuma entidade TypeScript foi materializada em "
                    "`cap-platform/repos/cap-base/src/domain` por este run.",
                    "",
                ]
            )
        elif delivery_type == "repository-contracts":
            lines.extend(
                [
                    "Flag **não** utilizada. Nenhum contrato de repositório foi materializado em "
                    "`cap-platform/repos/cap-base/src/domain/repositories` por este run.",
                    "",
                ]
            )
        elif delivery_type == "database":
            lines.extend(
                [
                    "Flag **não** utilizada. Nenhuma escrita foi feita em `cap-platform` por este run.",
                    "",
                ]
            )
        else:
            lines.extend(
                [
                    "Flag **não** utilizada. Nenhuma materialização foi feita neste run.",
                    "",
                ]
            )
    elif write_summary is None:
        lines.extend(["Flag solicitada, porém relatório interno ausente (erro inesperado).", ""])
    elif delivery_type == "repository-contracts":
        if write_summary.get("tsc_skipped"):
            tsc_status = "skipped (tsconfig não encontrado)"
        else:
            tsc_exit = write_summary.get("tsc_exit")
            tsc_status = "(não executado)" if tsc_exit is None else f"exit code {tsc_exit}"
        lines.extend(
            [
                f"- **Diretório alvo**: `{write_summary['target_resolved']}`",
                f"- **Ação executada**: {write_summary['action']}",
                f"- **Evidência física dos arquivos TypeScript após escrita**: {write_summary['evidence']}",
                f"- **Status da validação real**: {write_summary['real_validation']}",
                f"- **Resultado do `tsc --noEmit`**: {tsc_status}",
                "- **Relatórios de evidência**:",
                f"  - `{write_run_rel}`",
                f"  - `{write_out_rel}`",
                "",
                "_Saída completa de validação física, termos proibidos e `tsc` está nos arquivos acima._",
                "",
            ]
        )
    elif delivery_type == "domain":
        if write_summary.get("tsc_skipped"):
            tsc_status = "skipped (tsconfig não encontrado)"
        else:
            tsc_exit = write_summary.get("tsc_exit")
            tsc_status = (
                "(não executado)"
                if tsc_exit is None
                else f"exit code {tsc_exit}"
            )
        lines.extend(
            [
                f"- **Diretório alvo**: `{write_summary['target_resolved']}`",
                f"- **Ação executada**: {write_summary['action']}",
                f"- **Evidência física dos arquivos TypeScript após escrita**: {write_summary['evidence']}",
                f"- **Status da validação real**: {write_summary['real_validation']}",
                f"- **Resultado do `tsc --noEmit`**: {tsc_status}",
                "- **Relatórios de evidência**:",
                f"  - `{write_run_rel}`",
                f"  - `{write_out_rel}`",
                "",
                "_Saída completa de validação física, termos proibidos e `tsc` está nos arquivos acima._",
                "",
            ]
        )
    elif delivery_type == "database":
        exit_disp = (
            "(não executado)"
            if write_summary["prisma_exit"] is None
            else str(write_summary["prisma_exit"])
        )
        lines.extend(
            [
                f"- **Arquivo alvo**: `{write_summary['target_resolved']}`",
                f"- **Ação executada**: {write_summary['action']}",
                f"- **Backup criado**: {write_summary['backup_path'] or 'N/A'}",
                f"- **Evidência física após escrita**: {write_summary['evidence']}",
                f"- **prisma validate (exit code)**: {exit_disp}",
                f"- **Status da validação real**: {write_summary['real_validation']}",
                "- **Relatórios de evidência**:",
                f"  - `{write_run_rel}`",
                f"  - `{write_out_rel}`",
                "",
                "_Saída completa de stdout/stderr está nos arquivos acima._",
                "",
            ]
        )
    else:
        lines.extend(
            [
                f"- **Ação executada**: {write_summary.get('action', 'Não executado')}",
                "- **Relatórios de evidência**:",
                f"  - `{write_run_rel}`",
                f"  - `{write_out_rel}`",
                "",
                "_Materialização genérica não implementada para este tipo de entrega._",
                "",
            ]
        )

    lines.extend(
        [
            "## Resumo das etapas (agentes)",
            "",
        ]
    )
    order = ["po", "architect", "dev-base", "reviewer", "qa"]
    for key in order:
        if key in outputs:
            lines.append(f"- **{key}**: {_preview(outputs[key])}")
            lines.append("")

    lines.extend(
        [
            "## Saída final do QA",
            "",
            outputs.get("qa", "(sem saída de QA)").strip(),
            "",
            "## Status final do QA (texto bruto — interpretação humana)",
            "",
            "Extraia o status declarado pelo QA na própria saída (campo “Status recomendado”).",
            "",
            _consolidated_final_paragraph(
                val_status,
                physical,
                write_files_flag,
                write_summary,
                delivery_type,
            ),
            "",
            "## Execução",
            "",
            "Fluxo PO → Architect → Dev Base → validação determinística → "
            + ("materialização opcional → " if write_files_flag else "")
            + "Reviewer → QA concluído.",
            f"Timestamp da execução (UTC): `{timestamp}`",
            "",
            "## Arquivos gerados",
            "",
            "### Pasta `outputs/cap/`",
            "",
        ]
    )
    for p in output_files:
        lines.append(f"- `{p}`")
    lines.extend(["", "### Pasta do run", ""])
    for p in run_files:
        lines.append(f"- `{p}`")
    lines.append("")
    return "\n".join(lines)


def _run_validate_existing_flow(*, input_path: Path) -> None:
    run_dir = input_path.parent
    delivery_type = _infer_run_delivery_type(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    demanda = _read_text(input_path, "demanda (input)")

    if delivery_type == "domain":
        summary, wf_md = _run_validate_existing_domain_phase()
        final_builder = _build_validate_existing_domain_final_markdown
    elif delivery_type == "repository-contracts":
        summary, wf_md = _run_validate_existing_repository_contracts_phase()
        final_builder = _build_validate_existing_repository_contracts_final_markdown
    elif delivery_type == "database":
        summary, wf_md = _run_validate_existing_phase(target=CAP_BASE_PRISMA_PATH)
        final_builder = _build_validate_existing_final_markdown
    else:
        summary = {
            "delivery_type": delivery_type,
            "target_resolved": str(CAP_BASE_REPOSITORIES_PATH.resolve()),
            "action": "Validação do tipo de entrega não suportada em --validate-existing",
            "consolidated_status": "Não aplicável — use o fluxo completo da squad para este run.",
        }
        wf_md = "\n".join(
            [
                "# Validação existente não suportada para este tipo de entrega",
                "",
                f"Tipo inferido: `{delivery_type}`",
                "",
                "O fluxo `--validate-existing` neste script cobre entregas `database`, `domain` e `repository-contracts`.",
                "",
            ]
        ).strip()
        final_builder = _build_validate_existing_unsupported_delivery_final_markdown

    wf_run_path = run_dir / "write-files-output.md"
    wf_run_path.write_text(wf_md + "\n", encoding="utf-8")
    write_out_rel = str(wf_run_path.relative_to(ROOT)).replace("\\", "/")

    final_body = final_builder(
        demanda=demanda,
        timestamp=ts,
        summary=summary,
        write_out_rel=write_out_rel,
    )
    final_run = run_dir / "final.md"
    final_run.write_text(final_body + "\n", encoding="utf-8")

    print(f"write-files-output.md: {wf_run_path.resolve()}")
    print(f"final.md: {final_run.resolve()}")
    print(f"Status final consolidado: {summary['consolidated_status']}")


def main() -> None:
    load_dotenv(ROOT / ".env")

    project, raw_input_str, write_files_flag, validate_existing_flag, write_real_files_flag, single_agent = (
        _parse_cli_args(sys.argv[1:])
    )

    project = project.strip().lower()
    if project != "cap":
        _die(f"Erro: projeto não suportado: {project!r}. Por enquanto aceite apenas: cap")

    raw_input = Path(raw_input_str)
    input_path = raw_input if raw_input.is_absolute() else (ROOT / raw_input).resolve()
    if not input_path.is_file():
        _die(f"Erro: arquivo de demanda não encontrado: {input_path}")

    run_dir = input_path.parent
    run_dir.mkdir(parents=True, exist_ok=True)

    if validate_existing_flag:
        _run_validate_existing_flow(input_path=input_path)
        return

    assisted_manifest = run_dir / "files.manifest.json"
    if single_agent is None:
        if assisted_manifest.is_file():
            proc = file_writer.process_files_manifest(
                root=ROOT,
                manifest_path=assisted_manifest,
                write_real=write_real_files_flag,
            )
            report_path = run_dir / "file-write-report.md"
            report_md = file_writer.build_file_write_report_markdown(
                run_id=run_dir.name,
                project=project,
                write_real=write_real_files_flag,
                manifest_rel=str(assisted_manifest.relative_to(ROOT)).replace("\\", "/"),
                process_result=proc,
            )
            report_path.write_text(report_md, encoding="utf-8")
            print(f"file-write-report.md: {report_path.resolve()}")
        elif write_real_files_flag:
            print(
                "Aviso: --write-real-files sem files.manifest.json neste run; nada foi gravado pelo manifesto.",
                file=sys.stderr,
            )

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        _die("Erro: variável de ambiente OPENAI_API_KEY ausente ou vazia.")

    model = os.getenv("OPENAI_MODEL", "").strip() or "gpt-4.1-mini"

    demanda = _read_text(input_path, "demanda (input)")

    outputs_cap = ROOT / "outputs" / "cap"

    outputs_cap.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")

    client = OpenAI(api_key=api_key)

    if single_agent == "meta-orchestrator":
        _run_meta_orchestrator_flow(
            client=client,
            model=model,
            demanda=demanda,
            run_dir=run_dir,
            outputs_cap=outputs_cap,
            timestamp=ts,
        )
        return

    bundle = _load_context_bundle()
    shared_context = _build_shared_context_block(bundle)

    agent_instructions: dict[str, str] = {}
    for key, _slug, path in AGENTS:
        agent_instructions[key] = _read_text(path, f"agente ({key})")

    delivery_type = _infer_run_delivery_type(run_dir)

    previous: dict[str, str] = {}
    outputs: dict[str, str] = {}

    run_suffix_map = {
        "po": "po-output.md",
        "architect": "architect-output.md",
        "dev-base": "dev-base-output.md",
        "reviewer": "reviewer-output.md",
        "qa": "qa-output.md",
    }

    saved_output_paths: list[Path] = []
    saved_run_paths: list[Path] = []

    validation_markdown = ""
    validation_status = ""
    validation_run_rel = ""
    validation_output_rel = ""

    write_summary: dict[str, Any] | None = None
    write_run_rel = ""
    write_out_rel = ""

    for key, file_slug, _path in AGENTS:
        user_prompt = _build_user_prompt(
            shared_context=shared_context,
            demanda=demanda,
            previous_outputs=previous,
        )
        result = _run_agent(
            client=client,
            model=model,
            agent_key=key,
            agent_instructions=agent_instructions[key],
            user_prompt=user_prompt,
        )
        outputs[key] = result
        previous[key] = result

        out_cap_file = outputs_cap / f"{ts}-{file_slug}.md"
        run_file = run_dir / run_suffix_map[key]

        out_cap_file.write_text(result + "\n", encoding="utf-8")
        run_file.write_text(result + "\n", encoding="utf-8")

        saved_output_paths.append(out_cap_file.relative_to(ROOT))
        saved_run_paths.append(run_file.relative_to(ROOT))

        if key == "dev-base":
            validation_status, validation_markdown = _validate_dev_output(result, delivery_type)

            val_run_path = run_dir / "validation-output.md"
            val_out_path = outputs_cap / f"{ts}-validation.md"
            val_run_path.write_text(validation_markdown + "\n", encoding="utf-8")
            val_out_path.write_text(validation_markdown + "\n", encoding="utf-8")

            validation_run_rel = str(val_run_path.relative_to(ROOT)).replace("\\", "/")
            validation_output_rel = str(val_out_path.relative_to(ROOT)).replace("\\", "/")

            saved_output_paths.append(val_out_path.relative_to(ROOT))
            saved_run_paths.append(val_run_path.relative_to(ROOT))

            previous["validation"] = validation_markdown

            if write_files_flag:
                if delivery_type == "domain":
                    write_summary, wf_md = _run_write_files_domain_phase(
                        dev_output=result,
                        validation_status=validation_status,
                        ts=ts,
                    )
                elif delivery_type == "repository-contracts":
                    write_summary, wf_md = _run_write_files_repository_contracts_phase(
                        dev_output=result,
                        validation_status=validation_status,
                        ts=ts,
                        run_dir=run_dir,
                        demanda=demanda,
                        project=project,
                    )
                elif delivery_type == "database":
                    write_summary, wf_md = _run_write_files_phase(
                        dev_output=result,
                        validation_status=validation_status,
                        ts=ts,
                        target=CAP_BASE_PRISMA_PATH,
                    )
                else:
                    write_summary = {
                        "target_resolved": str(ROOT.resolve()),
                        "action": "Não executado",
                        "evidence": "AUSENTE",
                        "real_validation": "REPROVADO",
                    }
                    wf_md = "\n".join(
                        [
                            "# Escrita de Arquivos — Entrega genérica CAP-BASE",
                            "",
                            "## Flag usada",
                            "--write-files",
                            "",
                            "## Ação executada",
                            "Não executado",
                            "",
                            "## Observações / bloqueios",
                            "",
                            "- Materialização genérica ainda não implementada para este tipo de entrega.",
                            "",
                        ]
                    ).strip()
                wf_run_path = run_dir / "write-files-output.md"
                wf_out_path = outputs_cap / f"{ts}-write-files.md"
                wf_run_path.write_text(wf_md + "\n", encoding="utf-8")
                wf_out_path.write_text(wf_md + "\n", encoding="utf-8")
                saved_output_paths.append(wf_out_path.relative_to(ROOT))
                saved_run_paths.append(wf_run_path.relative_to(ROOT))
                write_run_rel = str(wf_run_path.relative_to(ROOT)).replace("\\", "/")
                write_out_rel = str(wf_out_path.relative_to(ROOT)).replace("\\", "/")

    final_body = _build_final_markdown(
        demanda=demanda,
        outputs=outputs,
        timestamp=ts,
        validation_status=validation_status,
        validation_markdown=validation_markdown,
        validation_run_rel=validation_run_rel,
        validation_output_rel=validation_output_rel,
        write_files_flag=write_files_flag,
        write_summary=write_summary,
        write_run_rel=write_run_rel,
        write_out_rel=write_out_rel,
        output_files=[str(p).replace("\\", "/") for p in saved_output_paths]
        + [str((outputs_cap / f"{ts}-final.md").relative_to(ROOT)).replace("\\", "/")],
        run_files=[str(p).replace("\\", "/") for p in saved_run_paths]
        + [str((run_dir / "final.md").relative_to(ROOT)).replace("\\", "/")],
        delivery_type=delivery_type,
    )

    final_out = outputs_cap / f"{ts}-final.md"
    final_run = run_dir / "final.md"

    final_out.write_text(final_body + "\n", encoding="utf-8")
    final_run.write_text(final_body + "\n", encoding="utf-8")

    val_run_abs = (run_dir / "validation-output.md").resolve()
    final_run_abs = final_run.resolve()
    print(f"final.md: {final_run_abs}")
    print(f"validation-output.md: {val_run_abs}")
    if write_files_flag:
        print(f"write-files-output.md: {(run_dir / 'write-files-output.md').resolve()}")
    print(
        "Status final consolidado: "
        f"{_terminal_consolidated_status(validation_status, write_files_flag, write_summary, delivery_type)}"
    )


if __name__ == "__main__":
    main()
