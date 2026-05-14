# Relatório — Fase 5.6 (Aprovação humana + squad completa pelo chat)

## Status final

**Concluído.** O meta-orquestrador grava `squad_runs` como `awaiting_human_approval`, a web oferece **Executar squad**, e `POST /api/runs/{run_id}/execute-squad` roda a squad completa via subprocesso, persiste `completed`/`failed`, grava mensagem assistant com `final.md` (ou erro) e atualiza o status do run. Testes usam mocks (sem OpenAI real). `pytest`, `npm run lint` e `npm run build` passaram.

## Arquivos criados

- `core/orchestration/squad_full_run_service.py` — subprocesso da squad completa e leitura de `final.md`.
- `apps/api/routes/runs.py` — rota `execute-squad`.
- `apps/api/schemas/runs.py` — `ExecuteSquadRequest`, `ExecuteSquadResponse`.
- `tests/test_execute_squad_api.py` — cobertura do fluxo de execução e do pending run.
- `docs/07-web-execute-squad.md` — operação e limitações.
- `runs/squad-agentes/0056-web-execute-squad/report.md` — este relatório.

## Arquivos alterados

- `core/database/schema.py` — migração aditiva `chat_id` / `error_detail` em `squad_runs`.
- `core/squad_runs.py` — status nomeados, `get_squad_run_by_run_id`, `get_pending_approval_run_for_chat`, `update_squad_run_status`, `can_execute_full_squad`, `create_squad_run_record` estendido.
- `apps/api/main.py` — router `/api/runs`.
- `apps/api/routes/chats.py` — nota de aprovação no assistant após meta, registro `awaiting_human_approval`, `GET .../pending-squad-run`.
- `apps/api/schemas/chats.py` — `PendingSquadRunResponse`.
- `tests/test_meta_orchestrator_api.py` — expectativas de status e texto do assistant.
- `apps/web/src/lib/api.ts` — `fetchPendingSquadRun`, `executeSquad`.
- `apps/web/src/app/page.tsx` — botão **Executar squad**, estados de carregamento e atualização de pending run.

## Endpoints

- `GET /api/chats/{chat_id}/pending-squad-run`
- `POST /api/runs/{run_id}/execute-squad`

## Status de run

Ver `docs/07-web-execute-squad.md` para a lista e o significado de cada valor.

## Comandos executados

Na raiz:

```text
python scripts/init_db.py
python -m pytest tests/ -q
```

Resultado: **22 passed**.

Em `apps/web`:

```text
npm run lint
npm run build
```

Resultado: **sem avisos ESLint**; **build Next.js concluído com sucesso**.

## Smoke manual

Não executado neste ambiente. Sugestão: API com `OPENAI_API_KEY`, web, projeto `cap`, enviar demanda, clicar **Executar squad**, verificar `runs/cap/<run_id>/final.md` e mensagens no chat.

## Observações

- `scripts/file_writer.py` e `scripts/run_squad.py` **não** foram alterados.
- A squad completa **não** é disparada automaticamente após o meta-orquestrador; só após o POST de execução (ação explícita na UI).
