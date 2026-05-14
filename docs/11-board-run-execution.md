# Execução assistida da run preparada pelo Board (Fase 5.10)

## Objetivo

Permitir que o usuário **execute explicitamente** a squad sobre uma run criada pelo fluxo do Board (Fase 5.9), usando o `input.md` já gravado em `runs/<slug>/<run_id>/`, **sem** depender de `chat_id` e **sem** alterar o contrato do meta-orquestrador no chat.

## Fluxo

1. No Board, **Preparar execução** (Fase 5.9) cria a pasta da run, `input.md`, registro em `squad_runs` (`status = created`, `task_id` preenchido, `chat_id` nulo) e atualiza `squad_tasks.run_id`.
2. O usuário clica em **Executar run** (somente se a run não estiver `completed` nem `running_squad`).
3. A API `POST /api/runs/{run_id}/execute-board-run` valida a run, exige `OPENAI_API_KEY`, passa a run para `running_squad`, delega a execução a `run_full_squad` (mesmo subprocesso de `scripts/run_squad.py` usado pelo fluxo “squad completa”), grava `execution.log`, atualiza o status da run e ajusta a tarefa.

Nada disso ocorre automaticamente após o passo 1.

## Endpoint

| Método | Caminho | Descrição |
|--------|---------|-----------|
| POST | `/api/runs/{run_id}/execute-board-run` | Execução explícita de run `board-*` com `task_id` e sem `chat`. |

Respostas comuns:

- **200** — corpo `ExecuteBoardRunResponse`: `status` `completed` ou `failed`, caminhos de `final.md` e `execution.log`, `task` atualizada (inclui `run_status` quando listada pela API de backlog).
- **404** — run inexistente.
- **400** — run que não atende ao critério Board, `input.md` ausente, status inválido para execução, etc.
- **409** — run já concluída ou já em `running_squad`.
- **503** — `OPENAI_API_KEY` não configurada.

## Critérios de run executável pelo Board

- `run_id` com prefixo `board-`.
- `task_id` preenchido e `chat_id` nulo.
- Status em `created` ou `failed` (reexecução após falha).

## Status (SQLite)

| Conceito | Valor em `squad_runs.status` |
|----------|------------------------------|
| Criada | `created` |
| Em execução | `running_squad` |
| Concluída | `completed` |
| Falha | `failed` |

## Artefatos na pasta da run

- `input.md` — já existente após a preparação.
- `final.md` — produzido pela squad quando a execução tem sucesso (como no fluxo existente).
- `execution.log` — texto com timestamp, `ok`, `exit_code`, stdout e stderr (sempre gravado após a tentativa).

Outros arquivos gerados por `run_squad.py` / contexto do projeto são preservados.

## Tarefa (`squad_tasks`)

- Em **sucesso**: status da tarefa passa para `in_review` (revisão humana do resultado).
- Em **falha**: status da tarefa passa para `blocked`.
- `run_id` na tarefa **não** é alterado.

## Lista de tarefas na API

`GET .../tasks` passa a incluir opcionalmente `run_status` (último status em `squad_runs` para o `run_id` da tarefa), para o Board decidir quando mostrar **Executar run**.

## Relação com o chat

`POST /api/runs/{run_id}/execute-squad` continua exclusivo do fluxo meta + `chat_id` + estados de aprovação. O novo endpoint **não** grava mensagens no chat.

## Riscos

- Execução real pode levar muito tempo e consumir API OpenAI; o timeout segue o de `run_full_squad` (padrão 7200 s).
- Apenas runs que passam na validação de contexto mínimo do projeto (via `run_full_squad`) chegam a executar o subprocesso com sucesso.
