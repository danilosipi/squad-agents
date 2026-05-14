# Chat inteligente de bootstrap do projeto (Fase 5.11)

## Objetivo

Quando um projeto registado no SQLite ainda não tem **contexto mínimo** em disco (`.squad/context.md` com conteúdo útil e `.squad/backlog.json`), o fluxo deixa de ser um erro fatal no chat. O assistente entra em **modo de onboarding**, conduz o utilizador e permite criar ou refinar ficheiros via API — sem exigir edição manual no explorador de ficheiros.

## Estado de bootstrap

`GET /api/projects/{slug}/bootstrap-status`

Devolve, entre outros:

- `needs_bootstrap` — `true` se faltar `.squad/`, `context.md`, `backlog.json` ou se o texto de `context.md` for demasiado curto (regra alinhada com `minimum_project_context_status`).
- `block_reason` — quando o projeto não tem `local_path` válido ou a pasta não existe (não é possível escrever no disco).
- `ready_for_meta_orchestrator` — `true` apenas para o slug `cap` com contexto mínimo válido (comportamento existente do meta-orquestrador).

## Criar estrutura mínima em disco

`POST /api/projects/{slug}/bootstrap`

Cria apenas o que falta: diretório `.squad/`, subpastas utilitárias, `context.md` com template longo (inclui nome, slug e caminho local) e `backlog.json` vazio no formato exportado (`version`, `epics`, `stories`, `tasks`).

## Refinar `context.md` a partir do chat

`POST /api/projects/{slug}/context/refine`

Corpo JSON:

```json
{ "chat_id": 1, "overwrite": true }
```

Reescreve `.squad/context.md` com o template padrão e uma secção **Notas do chat** com o histórico de mensagens. Garante `backlog.json` se ainda não existir.

## Chat com meta-orquestrador

`POST /api/chats/messages/with-meta-orchestrator`

- Se `needs_bootstrap`: grava a mensagem do utilizador, gera resposta do assistente (**onboarding**), grava a resposta. Resposta JSON com `status: "bootstrap"`, `mode: "bootstrap_onboarding"` e `bootstrap_status` atualizado. **Não** executa `run_squad.py`.
- Se o contexto estiver pronto e o projeto for **`cap`**: comportamento anterior (exige `OPENAI_API_KEY`, corre o meta-orquestrador).
- Se o contexto estiver pronto e o projeto **não** for `cap`: HTTP 400 com mensagem de projeto não suportado para o meta-orquestrador.

Com `OPENAI_API_KEY`, o texto de onboarding pode ser gerado via modelo configurável (`SQUAD_BOOTSTRAP_MODEL`, predefinição `gpt-4o-mini`). Sem chave, usa-se um texto estático seguro em português.

## Gestão de chats

- `PATCH /api/chats/{chat_id}` — corpo `{ "title": "..." }` para renomear.
- `DELETE /api/chats/{chat_id}` — elimina mensagens, anula `chat_id` em `squad_runs` e remove o chat.

## Guardar prompts importantes

`POST /api/chats/{chat_id}/save-prompt`

Corpo:

```json
{ "title_slug": "meu-prompt", "content": "..." }
```

Grava `.squad/prompts/YYYYMMDD-HHMMSS-<title_slug>.md` no `local_path` do projeto do chat.

## Onde os ficheiros ficam

Todos os caminhos são relativos ao **`local_path`** do projeto no SQLite, por exemplo:

`{local_path}\.squad\context.md`  
`{local_path}\.squad\backlog.json`  
`{local_path}\.squad\prompts\*.md`

No Windows, use caminhos absolutos ao registar o projeto.

## Compatibilidade com fases anteriores

O **Board**, preparação de run por tarefa e execução explícita de run do Board mantêm-se inalterados na API existente. O meta-orquestrador técnico continua restrito ao projeto `cap` quando o contexto mínimo existe.
