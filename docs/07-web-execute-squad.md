# Web — aprovação humana e execução da squad completa (Fase 5.6)

## Objetivo

Depois que o **meta-orquestrador** produz o plano no chat, o Danilo **aprova explicitamente** a execução da **squad completa** (PO → Arquiteto → Dev Base → Reviewer → QA). Só então a API chama `run_squad.py` **sem** `--agent` e **sem** `--write-real-files`.

## Fluxo de aprovação humana

1. Envio de demanda → `POST /api/chats/messages/with-meta-orchestrator`.
2. Sucesso do meta-orquestrador → mensagem assistant com o plano + texto orientando o próximo passo.
3. Registro em `squad_runs` com status **`awaiting_human_approval`** e `chat_id` preenchido.
4. A web consulta `GET /api/chats/{chat_id}/pending-squad-run` e exibe o botão **Executar squad** quando há run pendente (projeto `cap`).
5. Clique no botão → `POST /api/runs/{run_id}/execute-squad` com `{ "chat_id": <id> }`.
6. A API valida status, atualiza para `running_squad`, executa o subprocesso e, ao terminar, grava nova mensagem assistant com o conteúdo de `final.md` (ou mensagem de erro) e atualiza `squad_runs` para `completed` ou `failed`.

Nenhuma execução da squad completa ocorre **sem** o passo 5.

## Endpoints

| Método | Caminho | Descrição |
|--------|---------|-----------|
| `GET` | `/api/chats/{chat_id}/pending-squad-run` | Retorna `{ run_id, run_path, status }` ou `null` se não houver run aguardando aprovação (`awaiting_human_approval` ou `meta_completed`). |
| `POST` | `/api/runs/{run_id}/execute-squad` | Corpo JSON opcional: `{ "chat_id": number \| null }`. Se o run já tiver `chat_id`, ele deve coincidir com o enviado. Resposta: `status`, `run_id`, `final_path`, `assistant_message`. |

O comando executado é:

```text
python scripts/run_squad.py cap runs/cap/<run_id>/input.md
```

(raiz do repositório, herança de `OPENAI_API_KEY` e demais variáveis do ambiente do processo da API.)

## Status de run (`squad_runs.status`)

Valores usados nesta fase:

- `created` — reservado para evoluções.
- `meta_completed` — opcional; tratado como elegível para aprovação junto com `awaiting_human_approval`.
- `awaiting_human_approval` — definido após meta-orquestrador bem-sucedido; aguarda o botão na web.
- `running_squad` — durante o subprocesso da squad completa.
- `completed` — `final.md` lido e mensagem assistant gravada com sucesso.
- `failed` — falha no meta-orquestrador, na squad completa ou rejeição de transição.

Colunas aditivas: `chat_id`, `error_detail` (migração automática em `init_database`).

## Limitações atuais

- Execução **síncrona** na requisição HTTP (pode demorar muito; timeout interno de 7200 s na squad completa).
- Apenas projeto **`cap`** para execução completa (alinhado ao `run_squad.py`).
- **Sem** `--write-real-files` nesta fase.
- Artefatos fora de `runs/` e `outputs/` seguem apenas o que o `run_squad.py` já grava hoje (sem alteração desse script).

## Próxima fase

Evoluir para **quadro Scrum / tarefas** ligadas a runs, ou **escrita real assistida** (`--write-real-files`) com fluxo de aprovação adicional, conforme roadmap.
