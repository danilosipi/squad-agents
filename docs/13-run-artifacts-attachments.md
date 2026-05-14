# Run: artefactos e anexos de imagem no chat (Fase 5.12)

## Objetivo

- Ver pela web o conteúdo de `input.md`, `final.md` e `execution.log` de uma run (sem abrir o disco manualmente).
- Anexar imagens no chat como evidência rastreável no projeto cliente (`.squad/attachments/`), com registo no SQLite.

## Onde ficam os ficheiros

| Tipo | Local no disco |
|------|----------------|
| Artefactos da run | `<SQUAD_REPO_ROOT>/runs/<project_slug>/<run_id>/` (raiz do repositório **squad-agentes**, não o `local_path` do cliente) |
| Imagens do chat | `<local_path_do_projeto>/.squad/attachments/chats/<chat_id>/` |

Não duplicamos imagens em `.squad/evidences/` — tudo em **uma** pasta: `.squad/attachments/`.

## API

### Runs

- `GET /api/runs/{run_id}/artifacts`  
  Resposta JSON: `run_id`, `project_slug`, `artifacts[]` com `name`, `type` (`markdown` \| `log`), `exists`, `content` (ou `null` se não existir ou se exceder limite de leitura).

Regras de segurança (servidor):

- Só leitura de ficheiros com nome exacto na pasta da run resolvida a partir de `squad_runs.run_path`, confinada a `runs/` sob `SQUAD_REPO_ROOT`.
- Run inexistente → `404`.

### Chats — anexos

- `POST /api/chats/{chat_id}/attachments` — `multipart/form-data`, campo `file`. Formatos: png, jpg, jpeg, webp; máximo **5MB**; validação de MIME e assinatura de bytes.
- `GET /api/chats/{chat_id}/attachments` — lista metadados (sem binário).
- `GET /api/chats/attachments/{attachment_id}` — devolve o ficheiro (preview / descarga).

Após upload com sucesso, é criada uma mensagem de utilizador: `Imagem anexada: <nome>`.

## Base de dados

Tabela `squad_chat_attachments`:

- `id`, `chat_id`, `message_id`, `project_slug`, `file_name`, `file_path` (relativo ao `local_path`, estilo POSIX), `mime_type`, `size_bytes`, `created_at`
- `FOREIGN KEY(chat_id) REFERENCES squad_chats(id) ON DELETE CASCADE`

Ao apagar um chat, a pasta `.squad/attachments/chats/<id>/` é removida do disco antes do registo do chat.

## UI

- **Board**: botão **Ver resultado** (tarefa com `run_id`) abre painel lateral com separadores `input.md`, `final.md`, `execution.log`.
- **Chat**: botão **📎** para anexar imagem; lista de miniaturas com link para abrir o ficheiro.

## Multimodal

Nesta fase as imagens são **evidência em disco** e metadados na BD; o modelo de bootstrap/refine **não** recebe os pixels — apenas nomes/lista de anexos no texto de contexto. Análise visual automática fica para evolução futura.

## Dependências

- `python-multipart` (upload FastAPI).
