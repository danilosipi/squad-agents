# Integração Board ↔ execução assistida da squad (Fase 5.9)

## Objetivo

Permitir que uma **tarefa do quadro (Board)** sirva de origem para **preparar** uma execução assistida da squad: gerar `input.md` numa pasta de run no repositório `squad-agentes`, registrar o run no SQLite e vincular `run_id` à tarefa — **sem** executar `run_squad.py` automaticamente e **sem** alterar o fluxo do meta-orquestrador no chat.

## Fluxo do usuário

1. Abrir o projeto e a aba **Board**.
2. Clicar num cartão de tarefa para selecioná-lo (borda destacada).
3. Clicar em **Preparar execução**.
4. O sistema cria `runs/<project_slug>/<run_id>/input.md` (na raiz do repo definida por `SQUAD_REPO_ROOT`), insere linha em `squad_runs` com `task_id`, atualiza `squad_tasks.run_id` e reexporta `.squad/backlog.json` no projeto cliente.

Tarefas que **já possuem** `run_id` não podem ser preparadas de novo (HTTP 409).

## Conteúdo de `input.md`

O arquivo segue o modelo acordado na fase:

- `# Demanda` com o título da tarefa.
- `## Descrição` (ou texto padrão se vazio).
- `## Contexto do Backlog` com projeto, épico e história (quando existirem), ID da tarefa, prioridade da história, status e agente sugerido.
- `## Objetivo` e `## Restrições` com orientações para execução assistida e aprovação humana.

## Dados e persistência

| Onde | O quê |
|------|--------|
| `squad_tasks.run_id` | ID do run (`board-` + sufixo hex) |
| `squad_runs` | Registro com `status = created`, `task_id` preenchido, `chat_id` nulo |
| `runs/<slug>/<run_id>/input.md` | Demanda formatada (caminho relativo ao repo) |
| `.squad/backlog.json` | Export atualizado (inclui `run_id` na tarefa) |

O run preparado pelo Board **não** passa pelo fluxo de aprovação do chat (`awaiting_human_approval` do meta-orquestrador). A execução explícita da squad completa via API continua restrita ao projeto `cap` e aos estados já suportados em `execute-squad`; preparar pelo Board é um passo **manual** de materialização de contexto e rastreabilidade.

## API

- `POST /api/backlog/tasks/{task_id}/prepare-run` — corpo vazio; resposta `PrepareTaskRunResponse` (`task`, `run_id`, `run_path`, `input_path`).

## Limitações e ressalvas

- Não há disparo automático de `scripts/run_squad.py`.
- Runs do Board começam com status `created`; integração futura pode encadear aprovação ou CLI manual.
- `OPENAI_API_KEY` não é necessária para **apenas** preparar o run.

## Próximos passos sugeridos

- Botão ou fluxo opcional “Executar squad” a partir do run preparado (com confirmação e regras por projeto).
- Sincronização ou import reverso de `backlog.json` → SQLite.
