# Relatório — Fase 5.8 (PO Planner + quadro Scrum local)

## Arquivos criados

- `core/backlog/__init__.py`
- `core/backlog/backlog_service.py`
- `core/backlog/backlog_exporter.py`
- `apps/api/schemas/backlog.py`
- `apps/api/routes/backlog.py`
- `apps/web/src/components/ScrumBoard.tsx`
- `tests/test_backlog_api.py`
- `docs/09-po-planner-board.md`
- `runs/squad-agentes/0058-po-planner-board/report.md` (este arquivo)

## Arquivos alterados

- `apps/api/main.py` — registro do router `/api/backlog`
- `apps/web/src/lib/api.ts` — tipos e helpers de backlog
- `apps/web/src/app/page.tsx` — abas Chat / Board e integração do quadro

## Endpoints criados

| Método | Caminho |
|--------|---------|
| GET | `/api/backlog/{project_slug}/epics` |
| POST | `/api/backlog/{project_slug}/epics` |
| PATCH | `/api/backlog/epics/{epic_id}/status` |
| GET | `/api/backlog/{project_slug}/stories` |
| POST | `/api/backlog/{project_slug}/stories` |
| PATCH | `/api/backlog/stories/{story_id}/status` |
| GET | `/api/backlog/{project_slug}/tasks` |
| POST | `/api/backlog/{project_slug}/tasks` |
| PATCH | `/api/backlog/tasks/{task_id}/status` |
| PATCH | `/api/backlog/tasks/{task_id}/assign` |

## Componentes / tela

- **`ScrumBoard`**: colunas por status, criação rápida de tarefa, alteração de status (select + botões «/»), atribuição de agente por select, exibição de `story_id` e `run_id` quando existirem.
- **`page.tsx`**: barra de abas **Chat** | **Board** após seleção de projeto; no modo Chat mantém lista de chats + janela existente; no modo Board oculta a lista de chats e exibe o quadro em largura útil.

## Comandos executados

```text
python scripts/init_db.py
python -m pytest tests/ -q
cd apps/web
npm run lint
npm run build
```

## Resultado pytest

```text
32 passed in ~6s
```

## Resultado lint / build

- **`npm run lint`**: sem avisos ou erros ESLint.
- **`npm run build`**: compilação e checagem de tipos concluídas com sucesso (Next.js 14.2.18).

## Smoke manual (sugerido)

1. Registrar ou selecionar projeto **CAP** (ou outro com `local_path` válido).
2. Abrir aba **Board**.
3. Criar tarefa rápida, alterar status, atribuir agente.
4. Conferir `\.squad\backlog.json` na pasta do projeto (envelope com `epics`, `stories`, `tasks`).

## Status final

Critérios de aceite atendidos: API de backlog operacional, quadro web por status, CRUD mínimo de tarefas na UI, exportação de `.squad/backlog.json` após mutações, testes automatizados, lint e build da web, documentação e relatório entregues. Nenhuma alteração em `scripts/run_squad.py`, `scripts/file_writer.py` ou fluxo do meta-orquestrador.
