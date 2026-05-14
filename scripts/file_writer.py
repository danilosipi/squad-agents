"""
Escrita assistida de arquivos com whitelist e evidências (FASE 6).

Usado pelo run_squad quando existe `files.manifest.json` no diretório do run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

FileWriteStatus = Literal["CREATED", "UPDATED", "SKIPPED", "BLOCKED", "ERROR"]


def allowed_path_prefix_parts() -> tuple[tuple[str, ...], ...]:
    """Prefixos de diretório permitidos (partes do caminho relativo, case-insensitive no 1º segmento)."""
    return (
        ("repos", "cap-base"),
        ("runs",),
        ("outputs",),
    )


def normalize_path_under_root(*, root: Path, raw_path: str) -> tuple[Path | None, str | None]:
    """
    Resolve `raw_path` em caminho absoluto sob `root`.

    Retorna (caminho_resolvido, None) em sucesso, ou (None, mensagem de erro).
    """
    root_res = root.resolve()
    text = raw_path.strip()
    if not text:
        return None, "Caminho vazio."
    if "\x00" in text:
        return None, "Caminho contém caractere inválido."

    candidate = (root_res / text).resolve()

    try:
        candidate.relative_to(root_res)
    except ValueError:
        return None, "Caminho resolve fora da raiz do repositório (path traversal ou absoluto inválido)."

    return candidate, None


def is_path_whitelisted(*, root: Path, resolved: Path) -> bool:
    """True se `resolved` estiver sob `root` e obedecer à whitelist de pastas."""
    root_res = root.resolve()
    try:
        rel = resolved.resolve().relative_to(root_res)
    except ValueError:
        return False

    parts = tuple(p.lower() for p in rel.parts)
    if not parts:
        return False

    allowed = allowed_path_prefix_parts()
    for prefix in allowed:
        if len(parts) < len(prefix):
            continue
        if tuple(parts[: len(prefix)]) == tuple(p.lower() for p in prefix):
            return True
    return False


def ensure_parent_dirs(path: Path) -> str | None:
    """Cria diretórios pais; retorna mensagem de erro ou None."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return str(exc)
    return None


@dataclass
class FileWriteEvidence:
    """Evidência de uma entrada do manifesto."""

    requested_path: str
    status: FileWriteStatus
    final_path: str
    notes: str = ""
    verified_on_disk: bool | None = None


@dataclass
class ManifestProcessResult:
    entries: list[FileWriteEvidence] = field(default_factory=list)
    parse_error: str | None = None


def _read_manifest(path: Path) -> tuple[Any | None, str | None]:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"Falha ao ler manifesto: {exc}"
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as exc:
        return None, f"JSON inválido: {exc}"


def process_files_manifest(
    *,
    root: Path,
    manifest_path: Path,
    write_real: bool,
) -> ManifestProcessResult:
    """
    Processa `files.manifest.json`: valida paths, aplica whitelist, escreve ou simula.

    `write_real=False` nunca grava arquivos; status refletem o que ocorreria.
    """
    result = ManifestProcessResult()
    data, err = _read_manifest(manifest_path)
    if err:
        result.parse_error = err
        return result
    if not isinstance(data, dict):
        result.parse_error = "Raiz do JSON deve ser um objeto."
        return result
    files = data.get("files")
    if files is None:
        result.parse_error = 'Chave obrigatória ausente: "files".'
        return result
    if not isinstance(files, list):
        result.parse_error = '"files" deve ser uma lista.'
        return result

    for idx, item in enumerate(files):
        if not isinstance(item, dict):
            result.entries.append(
                FileWriteEvidence(
                    requested_path=f"(entrada #{idx + 1})",
                    status="ERROR",
                    final_path="",
                    notes="Item não é um objeto JSON.",
                )
            )
            continue

        rel = item.get("path")
        content = item.get("content")
        if not isinstance(rel, str):
            result.entries.append(
                FileWriteEvidence(
                    requested_path=f"(entrada #{idx + 1})",
                    status="ERROR",
                    final_path="",
                    notes='Campo "path" ausente ou não é string.',
                )
            )
            continue
        if not isinstance(content, str):
            result.entries.append(
                FileWriteEvidence(
                    requested_path=rel,
                    status="ERROR",
                    final_path="",
                    notes='Campo "content" ausente ou não é string.',
                )
            )
            continue

        resolved, norm_err = normalize_path_under_root(root=root, raw_path=rel)
        if norm_err or resolved is None:
            result.entries.append(
                FileWriteEvidence(
                    requested_path=rel,
                    status="BLOCKED",
                    final_path="",
                    notes=norm_err or "Normalização falhou.",
                )
            )
            continue

        if not is_path_whitelisted(root=root, resolved=resolved):
            result.entries.append(
                FileWriteEvidence(
                    requested_path=rel,
                    status="BLOCKED",
                    final_path=str(resolved),
                    notes="Fora da whitelist (permitido: repos/cap-base/, runs/, outputs/).",
                )
            )
            continue

        final_str = str(resolved)
        exists_before = resolved.is_file()
        existing_body: str | None = None
        if exists_before:
            try:
                existing_body = resolved.read_text(encoding="utf-8")
            except OSError as exc:
                result.entries.append(
                    FileWriteEvidence(
                        requested_path=rel,
                        status="ERROR",
                        final_path=final_str,
                        notes=f"Não foi possível ler arquivo existente: {exc}",
                    )
                )
                continue
        same_content = existing_body is not None and existing_body == content

        if not write_real:
            if not exists_before:
                status: FileWriteStatus = "CREATED"
                notes = "Dry-run: arquivo seria criado."
                verified: bool | None = None
            elif same_content:
                status = "SKIPPED"
                notes = "Dry-run: arquivo já existe com o mesmo conteúdo; nenhuma alteração necessária."
                verified = resolved.is_file()
            else:
                status = "UPDATED"
                notes = "Dry-run: arquivo seria atualizado (conteúdo diferente)."
                verified = resolved.is_file()
            result.entries.append(
                FileWriteEvidence(
                    requested_path=rel,
                    status=status,
                    final_path=final_str,
                    notes=notes,
                    verified_on_disk=verified,
                )
            )
            continue

        # Escrita real
        if same_content:
            result.entries.append(
                FileWriteEvidence(
                    requested_path=rel,
                    status="SKIPPED",
                    final_path=final_str,
                    notes="Conteúdo idêntico ao existente; escrita omitida.",
                    verified_on_disk=resolved.is_file(),
                )
            )
            continue

        mkdir_err = ensure_parent_dirs(resolved)
        if mkdir_err:
            result.entries.append(
                FileWriteEvidence(
                    requested_path=rel,
                    status="ERROR",
                    final_path=final_str,
                    notes=f"Falha ao criar diretórios: {mkdir_err}",
                )
            )
            continue

        try:
            resolved.write_text(content, encoding="utf-8", newline="\n")
        except OSError as exc:
            result.entries.append(
                FileWriteEvidence(
                    requested_path=rel,
                    status="ERROR",
                    final_path=final_str,
                    notes=f"Falha ao gravar: {exc}",
                )
            )
            continue

        verified_disk = resolved.is_file()
        if exists_before:
            status = "UPDATED"
            op_note = "Arquivo atualizado."
        else:
            status = "CREATED"
            op_note = "Arquivo criado."

        verify_note = " Pós-escrita: arquivo presente no disco." if verified_disk else " Pós-escrita: arquivo NÃO encontrado no disco."
        result.entries.append(
            FileWriteEvidence(
                requested_path=rel,
                status=status,
                final_path=final_str,
                notes=op_note + verify_note,
                verified_on_disk=verified_disk,
            )
        )

    return result


def build_file_write_report_markdown(
    *,
    run_id: str,
    project: str,
    write_real: bool,
    manifest_rel: str,
    process_result: ManifestProcessResult,
) -> str:
    """Monta o Markdown do relatório `file-write-report.md`."""
    mode = "write-real-files" if write_real else "dry-run"
    lines: list[str] = [
        "# Relatório de escrita assistida de arquivos",
        "",
        "## Metadados",
        "",
        f"- **run_id**: `{run_id}`",
        f"- **projeto**: `{project}`",
        f"- **modo**: `{mode}`",
        f"- **manifesto**: `{manifest_rel}`",
        "",
        "## Whitelist de segurança",
        "",
        "Somente caminhos resolvidos sob a raiz do repositório **squad-agentes** nas áreas:",
        "",
        "- `repos/cap-base/`",
        "- `runs/`",
        "- `outputs/`",
        "",
        "Caminhos absolutos ou relativos que escapem da raiz, ou fora dessas pastas, recebem status **BLOCKED**.",
        "",
        "## Arquivos processados",
        "",
        "| Path solicitado | Status | Caminho final | Verificado no disco | Observações |",
        "| --- | --- | --- | --- | --- |",
    ]

    if process_result.parse_error:
        lines.extend(
            [
                "| — | ERROR | — | — | "
                + process_result.parse_error.replace("|", "\\|").replace("\n", " ")[:500]
                + " |",
            ]
        )
    else:
        for ev in process_result.entries:
            vf = "—" if ev.verified_on_disk is None else ("sim" if ev.verified_on_disk else "não")
            fp = ev.final_path.replace("|", "\\|") if ev.final_path else "—"
            notes = ev.notes.replace("|", "\\|").replace("\n", " ")
            req = ev.requested_path.replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{req}` | **{ev.status}** | `{fp}` | {vf} | {notes} |")

    lines.extend(
        [
            "",
            "## Resumo",
            "",
        ]
    )
    if process_result.parse_error:
        lines.append("- Processamento abortado por erro de manifesto.")
    else:
        counts: dict[str, int] = {}
        for ev in process_result.entries:
            counts[ev.status] = counts.get(ev.status, 0) + 1
        for st in ("CREATED", "UPDATED", "SKIPPED", "BLOCKED", "ERROR"):
            if st in counts:
                lines.append(f"- **{st}**: {counts[st]}")

    lines.append("")
    lines.append("## Evidência")
    lines.append("")
    lines.append(
        "Este relatório foi gerado automaticamente pelo `scripts/run_squad.py` "
        f"({'escrita real habilitada' if write_real else 'modo simulação, sem gravação'})."
    )
    lines.append("")
    return "\n".join(lines).strip() + "\n"
