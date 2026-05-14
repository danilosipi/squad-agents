# Relatório — Fase 5.7 (contexto obrigatório do projeto)

## Arquivos criados

- `core/projects/project_context_service.py` — carregador e validação de contexto mínimo.
- `tests/test_project_context_service.py` — testes unitários do serviço.
- `docs/08-project-context-loading.md` — documentação operacional.
- `runs/squad-agentes/0057-project-context-loading/report.md` — este relatório.

## Arquivos alterados

- `core/config.py` — `get_repo_root()` e `SQUAD_REPO_ROOT` para isolamento de `runs/` em testes.
- `core/projects/project_service.py` — `ensure_squad_layout_for_project()` público.
- `core/orchestration/meta_orchestrator_service.py` — validação, `input.md` com seção de contexto, `project-context-used.md`.
- `core/orchestration/squad_full_run_service.py` — validação/regeneração da evidência antes do subprocesso.
- `apps/api/routes/chats.py` — validação de contexto mínimo antes da mensagem do usuário; payload com `context_loaded` / `context_evidence_path`.
- `apps/api/routes/runs.py` — validação antes de `running_squad`; resposta `blocked` com mensagem assistant.
- `apps/api/schemas/chats.py`, `apps/api/schemas/runs.py` — campos opcionais de contexto.
- `apps/web/src/lib/api.ts`, `apps/web/src/app/page.tsx` — tipos e mensagens para erro de contexto / `blocked`.
- `tests/test_meta_orchestrator_api.py`, `tests/test_execute_squad_api.py`, `tests/test_api_projects_chats.py` — `SQUAD_REPO_ROOT` e cenários de contexto.

## Regra de contexto mínimo

- Projeto no SQLite + `local_path` válido + `.squad/context.md` com **≥ 80** caracteres úteis (`strip`).

## Evidências geradas por run

- `runs/<slug>/<run_id>/project-context-used.md` — snapshot do contexto consolidado usado naquele run.

## Resultado pytest

31 testes passaram (`python -m pytest tests/ -q`).

## Resultado lint / build

- `npm run lint` — sem avisos ou erros ESLint.
- `npm run build` — compilação Next.js concluída com sucesso.

## Comandos executados

Na raiz do repositório:

- `python scripts/init_db.py`
- `python -m pytest tests/ -q`

Em `apps/web`:

- `npm run lint`
- `npm run build`

## Status final

**Concluído.** Contexto mínimo validado na API; `input.md` e `project-context-used.md` gerados pelo meta-orquestrador; a squad completa revalida a evidência; testes e build web passaram.
