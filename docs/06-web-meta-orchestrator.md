# Web local + meta-orquestrador (Fase 5.5)

## Objetivo

Conectar o chat da web (`apps/web`) ao **meta-orquestrador** real via API FastAPI, substituindo a resposta fake do assistente. Cada envio:

1. persiste a mensagem do usuário no SQLite;
2. cria um run em `runs/cap/<run_id>/` com `input.md`;
3. executa `python scripts/run_squad.py cap runs/cap/<run_id>/input.md --agent meta-orchestrator` (subprocess na raiz do repositório);
4. persiste a resposta do assistente (Markdown do plano ou mensagem de erro estruturada);
5. registra o run na tabela `squad_runs`.

Nesta fase **não** há execução da squad completa (PO/Architect/Dev/Reviewer/QA), **não** há `--write-real-files` e **não** há geração de arquivos de produto fora de `runs/`.

## Configuração da OpenAI

A API e o subprocesso herdam o ambiente do processo que sobe o Uvicorn.

1. Crie um arquivo `.env` na **raiz** do repositório `squad-agentes` (o mesmo diretório onde está `scripts/run_squad.py`), com pelo menos:

   ```env
   OPENAI_API_KEY=sk-...
   ```

2. Opcional: `OPENAI_MODEL` (o `run_squad.py` usa `gpt-4.1-mini` como padrão se vazio).

Se `OPENAI_API_KEY` estiver ausente ou vazia, o endpoint dedicado responde **503** com mensagem explícita; a web exibe o texto retornado pela API.

## Como rodar a API

Na raiz do repositório (com dependências Python instaladas, `pip install -r requirements.txt`):

```bash
python scripts/init_db.py
uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

Variáveis úteis (opcionais):

- `SQUAD_DATABASE_PATH` — caminho do arquivo SQLite (padrão: `data/squad-agents.db` sob a raiz).
- `SQUAD_PROJECTS_ROOT` — raiz onde projetos locais são criados.

## Como rodar a web

```bash
cd apps/web
npm install
npm run dev
```

Por padrão a web chama a API em `http://127.0.0.1:8000`. Para outro host/porta use `NEXT_PUBLIC_API_BASE_URL`.

### Modo fake (desenvolvimento)

Se definir `NEXT_PUBLIC_USE_FAKE_ASSISTANT=true` no ambiente da build/dev da web, o envio volta a usar apenas `POST /api/chats/messages` (usuário + resposta fixa), **sem** chamar o meta-orquestrador. O fluxo principal permanece com o endpoint real abaixo.

## Endpoint criado

| Método | Caminho | Descrição |
|--------|---------|-----------|
| `POST` | `/api/chats/messages/with-meta-orchestrator` | Corpo JSON: `chat_id` (int), `content` (string). Resposta: `user_message`, `assistant_message`, `run_id`, `run_path`, `status` (`success` ou `failed`). |

Regras de negócio:

- O chat precisa existir; caso contrário **404**.
- Apenas projeto com `slug === "cap"` é aceito; outro slug retorna **400** com: *"Projeto ainda não suportado para execução do meta-orquestrador."*
- Sem `OPENAI_API_KEY`: **503** (nenhuma mensagem é gravada).

## Fluxo da mensagem

```text
Web (page.tsx)
  → POST /api/chats/messages/with-meta-orchestrator
     → SQLite: mensagem user
     → core/orchestration/meta_orchestrator_service.py
        → runs/cap/<run_id>/input.md
        → subprocess: run_squad.py … --agent meta-orchestrator
        → leitura de meta-orchestrator-output.md (preferencial) ou final.md
     → SQLite: mensagem assistant + squad_runs
  → GET /api/chats/{id}/messages (atualização da lista)
```

## Limitações atuais

- Somente **`cap`** como `project_slug` para execução do meta-orquestrador (alinhado ao `run_squad.py`).
- Chamada **síncrona** na requisição HTTP: respostas longas bloqueiam até o subprocesso terminar (timeout interno de 900 s no serviço).
- Não há autenticação nem fila de jobs.

## Próxima fase

Após revisão humana do plano, evoluir para **execução da squad completa** (demais agentes e políticas de escrita de arquivos), mantendo rastreabilidade e aprovações explícitas conforme o roadmap.
