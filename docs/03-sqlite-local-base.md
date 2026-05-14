# Base local SQLite (Fase 5.2)

## Por que SQLite

O squad-agentes precisa de um **índice operacional** leve para a futura interface web: projetos escolhidos, chats, mensagens, backlog e status de runs. SQLite oferece persistência local **sem servidor**, **sem Docker** e com **baixa complexidade**, alinhado a um fluxo de desenvolvimento em máquina única (por exemplo `D:\Drive\Projetos`).

## Onde fica o banco

- Padrão: `data/squad-agents.db` (relativo à raiz do repositório `squad-agentes`).
- Sobrescrita: variável de ambiente `SQUAD_DATABASE_PATH` com caminho absoluto ou relativo resolvido pelo sistema.

O diretório `data/` é criado automaticamente na primeira inicialização.

## O que vai para o SQLite

Tabelas pensadas para **UX e consulta rápida**, por exemplo:

- `squad_projects` — projetos cadastrados (nome, slug, caminho local, status).
- `squad_chats` / `squad_messages` — conversas da plataforma (futuro).
- `squad_epics` / `squad_stories` / `squad_tasks` — backlog indexado (futuro).
- `squad_runs` — referência a runs e caminhos (futuro).

## O que continua em arquivos

A **fonte oficial** permanece em Markdown/JSON no disco do projeto (e na estrutura atual de `docs/`, `projects/`, `squads/`, `runs/`, `outputs/` do repositório). O banco **não substitui** esses arquivos; apenas indexa e apoia navegação e estado na UI.

## Como inicializar

Na raiz do repositório:

```bash
python scripts/init_db.py
```

Isso garante a pasta `data/`, cria o arquivo do banco se necessário e aplica o schema (idempotente).

## Como cadastrar um projeto existente

```bash
python scripts/projects_cli.py register "NOME" "CAMINHO_DA_PASTA"
```

Exemplo:

```bash
python scripts/projects_cli.py register "CAP" "D:\Drive\Projetos\cap-platform"
```

Requisitos: a pasta deve existir. O serviço cria a árvore `.squad/` **somente onde ainda não existir**, sem sobrescrever arquivos existentes.

## Como criar um novo projeto

```bash
python scripts/projects_cli.py create "Nome do projeto"
```

Isso cria uma pasta sob a raiz de projetos (padrão `D:\Drive\Projetos`) usando o **slug** derivado do nome, aplica `.squad/` e grava o registro no SQLite.

Raiz de projetos padrão: `D:\Drive\Projetos`. Sobrescrita: `SQUAD_PROJECTS_ROOT`.

## Regra de `.squad` por projeto

Em cada projeto (pasta local), o layout opcional/padrão criado pelo cadastro:

- `.squad/context.md`
- `.squad/roadmap.md`
- `.squad/backlog.json`
- `.squad/decisions.md`
- `.squad/chats/`
- `.squad/runs/`
- `.squad/outputs/`

Arquivos e pastas já existentes **não são sobrescritos**; apenas faltantes são criados.

## Decisão de não usar Docker

Docker não é necessário para um SQLite local e um CLI de desenvolvimento: reduz atrito, mantém o repositório simples e evita dependência de daemon ou imagens para esta fase.

## Testes

```bash
pytest
```

Os testes usam diretórios temporários e variáveis `SQUAD_DATABASE_PATH` / `SQUAD_PROJECTS_ROOT` para não alterar `D:\Drive\Projetos` nem o banco padrão.
