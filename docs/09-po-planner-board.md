# PO Planner e quadro Scrum local (Fase 5.8)

## Objetivo

Dar base funcional para o Product Owner organizar roadmap, épicos, histórias e tarefas do projeto, com visualização em quadro estilo Scrum/Kanban na web. Nesta fase não há geração automática de backlog por LLM, nem execução da squad ou integração com GitHub.

## Modelo Roadmap → Epic → Story → Task

- **Roadmap**: continua documentado em `.squad/roadmap.md` (fora do escopo desta fase no SQLite).
- **Épico (`squad_epics`)**: agrupamento de alto nível ligado ao `project_id`.
- **História (`squad_stories`)**: trabalho de valor opcionalmente vinculado a um épico (`epic_id`), com prioridade.
- **Tarefa (`squad_tasks`)**: unidade operacional do quadro; pode referenciar uma história (`story_id`) e, no futuro, runs (`run_id`).

## Status permitidos

Os mesmos valores aplicam-se a épicos, histórias e tarefas:

| Valor API | Rótulo no quadro (web) |
|-----------|-------------------------|
| `backlog` | Backlog |
| `ready` | Ready |
| `in_progress` | In Progress |
| `in_review` | In Review |
| `qa` | QA |
| `waiting_human_approval` | Waiting Human Approval |
| `done` | Done |
| `blocked` | Blocked |

## Prioridade de histórias

Valores permitidos: `low`, `medium`, `high`, `critical` (padrão: `medium`).

## Agentes permitidos (atribuição de tarefa)

Inicialmente: `po`, `architect`, `dev-base`, `reviewer`, `qa`. O campo `assignee_agent` em `squad_tasks` pode ser `NULL` (sem atribuição).

## SQLite e `.squad/backlog.json`

- O **SQLite** é o índice operacional usado pela API e pela web para listar e alterar itens rapidamente.
- Após cada criação ou atualização relevante, o serviço exporta um snapshot JSON para **`<local_path>/.squad/backlog.json`**, usando o `local_path` do projeto cadastrado.
- O arquivo segue um envelope com `version`, `updated_at`, `project_slug`, e listas `epics`, `stories` e `tasks` espelhando as linhas das tabelas (incluindo `id` e timestamps). A intenção é que `.squad/backlog.json` permaneça a **fonte oficial legível** no repositório do projeto cliente, enquanto o banco local concentra a UX e futuras ligações com runs.

## Limitações atuais

- Sem drag-and-drop entre colunas; mudança de status por controle na própria tarefa.
- Sem chamadas OpenAI para sugerir ou reescrever backlog.
- Sem disparo automático da squad a partir do quadro.
- Sem sincronização bidirecional automática: edições manuais apenas no JSON não são relidas pelo SQLite nesta fase.
- `run_id` em tarefas existe no schema para vínculo futuro; o quadro apenas exibe quando preenchido.

## Próxima fase

PO gerar backlog automaticamente a partir do **contexto do projeto** (`.squad/context.md` e metadados), com revisão humana antes de persistir no SQLite e exportar para `backlog.json`.
