# Relatório — Fase 5.5 (Web + meta-orquestrador)

## Status final

**Concluído.** Chat web usa o endpoint `POST /api/chats/messages/with-meta-orchestrator`, persiste mensagens e `squad_runs`, cria pasta `runs/cap/<run_id>/` e delega ao `run_squad.py` existente com `--agent meta-orchestrator`. Testes não invocam OpenAI real; lint e build da web passaram.

## Arquivos criados

- `core/orchestration/__init__.py`
- `core/orchestration/meta_orchestrator_service.py` — subprocesso, leitura de saída Markdown, validação de `OPENAI_API_KEY` e projeto suportado.
- `core/squad_runs.py` — inserção em `squad_runs`.
- `tests/test_meta_orchestrator_api.py` — testes do endpoint com mocks.
- `docs/06-web-meta-orchestrator.md` — operação e limitações.
- `runs/squad-agentes/0055-web-meta-orchestrator/report.md` — este relatório.

## Arquivos alterados

- `core/chats/chat_service.py` — `get_chat_with_project`.
- `apps/api/schemas/chats.py` — schemas do novo endpoint.
- `apps/api/routes/chats.py` — rota `with-meta-orchestrator`.
- `apps/web/src/lib/api.ts` — `sendMessageWithMetaOrchestrator`, melhoria em `parseError`.
- `apps/web/src/app/page.tsx` — fluxo real vs `NEXT_PUBLIC_USE_FAKE_ASSISTANT`, banner de execução.

## Endpoint criado

- `POST /api/chats/messages/with-meta-orchestrator`  
  Payload: `{ "chat_id": number, "content": string }`  
  Resposta: `user_message`, `assistant_message`, `run_id`, `run_path`, `status`.

## Fluxo implementado

1. Valida chat + projeto; restringe meta-orquestrador ao slug `cap`.
2. Exige `OPENAI_API_KEY` na API antes de gravar mensagens.
3. Grava mensagem `user`, executa serviço (run + subprocesso), grava `assistant` (plano ou erro em Markdown).
4. Insere linha em `squad_runs` com `completed` ou `failed`.

## Comandos executados (validação)

Na raiz do repositório:

```text
python scripts/init_db.py
python -m pytest tests/ -q
```

Resultado pytest: **14 passed**.

Em `apps/web`:

```text
npm run lint
npm run build
```

Resultado: **sem avisos ESLint**; **Next.js build concluído com sucesso**.

## Smoke manual

Não executado neste ambiente automatizado. Passos sugeridos:

1. Exportar `OPENAI_API_KEY`, subir API (`uvicorn`) e web (`npm run dev`).
2. Garantir projeto com slug **`cap`** e um chat.
3. Enviar mensagem e confirmar Markdown do meta-orquestrador no painel e arquivos em `runs/cap/<run_id>/`.

## Observações

- `scripts/run_squad.py` e `scripts/file_writer.py` **não** foram alterados.
- Fallback fake apenas com `NEXT_PUBLIC_USE_FAKE_ASSISTANT=true` na web.
