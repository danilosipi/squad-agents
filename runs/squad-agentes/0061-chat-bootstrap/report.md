# Relatório — Fase 5.11 (Chat inteligente de bootstrap)

## Arquivos criados

- `core/projects/project_bootstrap_service.py` — estado de bootstrap, criação de artefactos, refine a partir do chat, guardar prompts.
- `core/orchestration/bootstrap_chat_service.py` — resposta do assistente em modo onboarding (OpenAI opcional + fallback estático).
- `tests/test_chat_bootstrap_api.py` — testes de API para bootstrap, refine, rename/delete chat, save-prompt.
- `docs/12-chat-bootstrap.md` — documentação do fluxo e endpoints.

## Arquivos alterados

- `apps/api/routes/chats.py` — fluxo `with-meta-orchestrator` com modo bootstrap; `PATCH`/`DELETE` chat; `POST` save-prompt.
- `apps/api/routes/projects.py` — `bootstrap-status`, `bootstrap`, `context/refine`.
- `apps/api/schemas/chats.py`, `apps/api/schemas/projects.py` — novos modelos.
- `apps/api/main.py` — remoção de imports FastAPI duplicados.
- `core/chats/chat_service.py` — `update_chat_title`, `delete_chat`.
- `apps/web/src/lib/api.ts` — tipos e funções REST novas.
- `apps/web/src/app/page.tsx` — estado de bootstrap, ações de UI, rename/delete na lista.
- `apps/web/src/components/ChatList.tsx` — renomear/eliminar por chat.
- `tests/test_meta_orchestrator_api.py` — expectativas alinhadas ao bootstrap em contexto curto; projeto não-`cap` com contexto válido continua a devolver 400.

## Endpoints novos ou alterados

| Método | Caminho | Descrição |
|--------|---------|-----------|
| GET | `/api/projects/{slug}/bootstrap-status` | Estado de onboarding no disco. |
| POST | `/api/projects/{slug}/bootstrap` | Cria `.squad/`, `context.md` e `backlog.json` em falta. |
| POST | `/api/projects/{slug}/context/refine` | Gera/atualiza `context.md` a partir do histórico do `chat_id`. |
| PATCH | `/api/chats/{chat_id}` | Renomeia chat (`title`). |
| DELETE | `/api/chats/{chat_id}` | Remove chat e mensagens. |
| POST | `/api/chats/{chat_id}/save-prompt` | Grava ficheiro em `.squad/prompts/`. |
| POST | `/api/chats/messages/with-meta-orchestrator` | **Alterado:** resposta `status`/`mode` para onboarding quando `needs_bootstrap`. |

## Fluxo manual de validação (resumo)

1. Projeto sem `context.md` → `GET bootstrap-status` com `needs_bootstrap: true`.
2. Criar chat com título → `POST /api/chats`.
3. Primeira mensagem via `with-meta-orchestrator` → 201, `bootstrap`, mensagens persistidas.
4. Escolher opções no chat; usar **Gravar context.md (chat)** ou `POST context/refine`.
5. Confirmar ficheiros em `{local_path}/.squad/`.
6. **Guardar prompt** → ficheiro em `.squad/prompts/`.
7. Renomear/eliminar chat via UI ou PATCH/DELETE.
8. Com contexto mínimo e slug `cap`, meta-orquestrador e Board continuam como antes.

## Comandos executados

```text
Set-Location "d:\Drive\Projetos\squad-agentes"; python -m pytest tests/ -q
Set-Location "d:\Drive\Projetos\squad-agentes\apps\web"; npm run lint; npm run build
```

## Resultado dos testes

- `pytest tests/ -q`: **45 passed**.
- `npm run lint`: **sem avisos**.
- `npm run build`: **compilação bem-sucedida**.

## Riscos / ressalvas

- O onboarding com OpenAI depende de rede e quotas; sem chave usa-se texto estático (menos personalizado).
- `SQUAD_BOOTSTRAP_MODEL` não é validado na arranque; valores inválidos falham em runtime na chamada OpenAI (cai no fallback estático em caso de exceção).
- Projetos não-`cap` com contexto completo ainda não executam o meta-orquestrador técnico (comportamento mantido de propósito).
- Eliminar um chat remove o histórico; `squad_runs.chat_id` é anulado mas os registos de run mantêm-se.

## Status final

**Concluído.** Critérios de aceite cobertos por testes automatizados e validação de lint/build da web; `scripts/run_squad.py` não foi alterado.
