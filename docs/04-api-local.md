# API local (Fase 5.3)

## Objetivo

Expor uma **API HTTP local** com [FastAPI](https://fastapi.tiangolo.com/) para alimentar, no futuro, uma interface web estilo ChatGPT: cadastro de projetos, criação de chats por projeto e troca de mensagens persistidas no **SQLite** já usado na fase 5.2 (`core/database`).

Nesta fase **não** há execução de agentes, **não** há chamadas à OpenAI e **não** há interface web.

## Como rodar

Na raiz do repositório `squad-agentes`, com dependências instaladas (`pip install -r requirements.txt`):

```bash
python scripts/init_db.py
python scripts/api_dev.py
```

Por padrão o servidor sobe em `http://127.0.0.1:8000` com reload. Documentação interativa: `http://127.0.0.1:8000/docs`.

Variáveis de ambiente (mesmas da base local):

- `SQUAD_PROJECTS_ROOT` — raiz onde projetos são criados (padrão `D:\Drive\Projetos`).
- `SQUAD_DATABASE_PATH` — arquivo SQLite (padrão `data/squad-agents.db` sob a raiz do repo).

## CORS (consumo pelo browser)

A interface web em `apps/web` chama a API a partir do navegador. O `apps.api.main` inclui `CORSMiddleware` permitindo `http://localhost:3000` e `http://127.0.0.1:3000`.

## Endpoints

### Saúde

| Método | Caminho | Resposta |
|--------|---------|----------|
| GET | `/api/health` | `{"status": "ok"}` |

### Projetos (`/api/projects`)

| Método | Caminho | Descrição |
|--------|---------|-----------|
| GET | `/api/projects` | Lista projetos |
| GET | `/api/projects/{slug}` | Projeto por slug |
| POST | `/api/projects` | Cria projeto (pasta em `PROJECTS_ROOT` + `.squad` + SQLite) |
| POST | `/api/projects/register` | Registra pasta existente |

### Chats e mensagens (`/api/chats`)

| Método | Caminho | Descrição |
|--------|---------|-----------|
| GET | `/api/chats/project/{project_slug}` | Lista chats do projeto |
| POST | `/api/chats` | Cria chat |
| GET | `/api/chats/{chat_id}/messages` | Lista mensagens do chat |
| POST | `/api/chats/messages` | Adiciona mensagem |

## Exemplos de payload

**Criar projeto**

```json
POST /api/projects
{ "name": "Meu projeto" }
```

**Registrar pasta existente**

```json
POST /api/projects/register
{
  "name": "CAP",
  "local_path": "D:\\Drive\\Projetos\\cap-platform"
}
```

**Criar chat**

```json
POST /api/chats
{
  "project_slug": "cap",
  "title": "Planejamento"
}
```

**Adicionar mensagem**

```json
POST /api/chats/messages
{
  "chat_id": 1,
  "role": "user",
  "content": "Resumo do backlog"
}
```

Valores permitidos para `role`: `user`, `assistant`, `system`, `agent`.

## Por que ainda não executar agentes

A API isola **CRUD** e leitura/escrita no índice SQLite para evoluir a UX sem acoplar ao meta-orchestrator ou ao `run_squad`. Agentes e runs entram em fases posteriores, mantendo esta camada testável e previsível.

## Relação com o SQLite

Tabelas principais: `squad_projects`, `squad_chats`, `squad_messages`. O schema é inicializado no **startup** da aplicação (`init_database()`).

## Relação com a futura web

O front poderá consumir estes endpoints (CORS e autenticação podem ser adicionados depois). Markdown/JSON em disco continuam como **fonte de evidência** oficial; o banco permanece índice operacional para a interface.

## Testes

```bash
pytest tests/test_api_projects_chats.py -q
```
