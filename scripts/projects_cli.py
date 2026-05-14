#!/usr/bin/env python3
"""CLI mínima para testar cadastro de projetos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.projects import project_service


def cmd_list(_: argparse.Namespace) -> None:
    for p in project_service.list_projects():
        print(f"{p['slug']}\t{p['name']}\t{p['local_path']}")


def cmd_create(args: argparse.Namespace) -> None:
    row = project_service.create_project(args.name)
    print(f"Criado id={row['id']} slug={row['slug']} path={row['local_path']}")


def cmd_register(args: argparse.Namespace) -> None:
    row = project_service.register_existing_project(args.name, args.path)
    print(f"Registrado id={row['id']} slug={row['slug']} path={row['local_path']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Projetos squad-agentes (SQLite local)")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="Lista projetos cadastrados")
    p_list.set_defaults(func=cmd_list)

    p_create = sub.add_parser("create", help="Cria pasta em PROJECTS_ROOT e registra")
    p_create.add_argument("name", type=str, help='Nome do projeto (ex.: "Projeto Teste")')
    p_create.set_defaults(func=cmd_create)

    p_reg = sub.add_parser("register", help="Registra pasta existente")
    p_reg.add_argument("name", type=str, help="Nome exibido")
    p_reg.add_argument("path", type=str, help="Caminho absoluto da pasta do projeto")
    p_reg.set_defaults(func=cmd_register)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
