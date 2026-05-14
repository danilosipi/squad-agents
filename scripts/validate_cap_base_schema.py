"""
Validação determinística do schema Prisma em repos/cap-base/prisma/base.prisma.

Verifica a presença dos 23 models obrigatórios do CAP-BASE (lista explícita abaixo).
Gera relatório Markdown e retorna código de saída 0 (APROVADO) ou 1 (REPROVADO).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Lista explícita dos 23 models obrigatórios (FASE 7 — alinhado à entrega database CAP-BASE).
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

_MODEL_DECL = re.compile(r"^\s*model\s+(\w+)\s*\{", re.MULTILINE)


def _find_model_names(text: str) -> list[str]:
    return [m.group(1) for m in _MODEL_DECL.finditer(text)]


def _build_report_markdown(
    *,
    schema_rel: str,
    expected: int,
    total_declared: int,
    present_count: int,
    present_sorted: list[str],
    missing: list[str],
    approved: bool,
) -> str:
    status = "APROVADO" if approved else "REPROVADO"
    lines = [
        "# Validação determinística — schema CAP-BASE",
        "",
        "## Arquivo validado",
        "",
        f"`{schema_rel}`",
        "",
        "## Resumo numérico",
        "",
        f"- **Total de models obrigatórios esperados**: {expected}",
        f"- **Total de models obrigatórios encontrados**: {present_count}",
        f"- **Total de declarações `model` no arquivo**: {total_declared}",
        "",
        "## Lista de models obrigatórios encontrados",
        "",
    ]
    for name in present_sorted:
        lines.append(f"- `{name}`")
    lines.extend(["", "## Lista de models obrigatórios ausentes", ""])
    if missing:
        for name in missing:
            lines.append(f"- `{name}`")
    else:
        lines.append("- _(nenhum)_")
    lines.extend(
        [
            "",
            "## Status final",
            "",
            f"**{status}**",
            "",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    p = argparse.ArgumentParser(description="Valida models obrigatórios em base.prisma")
    p.add_argument(
        "--schema",
        type=Path,
        default=root / "repos" / "cap-base" / "prisma" / "base.prisma",
        help="Caminho do schema Prisma",
    )
    p.add_argument(
        "--report",
        type=Path,
        default=root / "runs" / "cap" / "005-real-file-creation" / "schema-validation-report.md",
        help="Caminho do relatório Markdown de saída",
    )
    args = p.parse_args()
    schema_path = args.schema if args.schema.is_absolute() else (root / args.schema).resolve()
    report_path = args.report if args.report.is_absolute() else (root / args.report).resolve()

    try:
        schema_rel = str(schema_path.relative_to(root)).replace("\\", "/")
    except ValueError:
        schema_rel = str(schema_path)

    if not schema_path.is_file():
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            _build_report_markdown(
                schema_rel=schema_rel,
                expected=len(REQUIRED_MODELS),
                total_declared=0,
                present_count=0,
                present_sorted=[],
                missing=sorted(REQUIRED_MODELS),
                approved=False,
            )
            + "\n## Erro\n\nArquivo de schema não encontrado no disco.\n",
            encoding="utf-8",
        )
        print(f"REPROVADO: schema não encontrado: {schema_path}", file=sys.stderr)
        return 1

    text = schema_path.read_text(encoding="utf-8")
    declared = _find_model_names(text)
    required_set = set(REQUIRED_MODELS)
    declared_set = set(declared)
    present_sorted = sorted(required_set & declared_set)
    missing = sorted(required_set - declared_set)
    approved = not missing
    present_count = len(present_sorted)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        _build_report_markdown(
            schema_rel=schema_rel,
            expected=len(REQUIRED_MODELS),
            total_declared=len(declared),
            present_count=present_count,
            present_sorted=present_sorted,
            missing=missing,
            approved=approved,
        ),
        encoding="utf-8",
    )

    print(f"Schema: {schema_path}")
    print(f"Relatório: {report_path}")
    print(f"Obrigatórios presentes: {present_count}/{len(REQUIRED_MODELS)}")
    if missing:
        print(f"Ausentes: {', '.join(missing)}", file=sys.stderr)
        return 1
    print("APROVADO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
