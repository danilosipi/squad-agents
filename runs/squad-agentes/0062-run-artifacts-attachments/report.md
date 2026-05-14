# Relatório — Fase 5.12 (artefactos da run + anexos de imagem no chat)

## Ficheiros criados

- `core/runs/__init__.py`
- `core/runs/run_artifacts_service.py`
- `core/chats/chat_attachment_service.py`
- `tests/test_run_artifacts_attachments_api.py`
- `docs/13-run-artifacts-attachments.md`
- `runs/squad-agentes/0062-run-artifacts-attachments/report.md` (este ficheiro)

## Ficheiros alterados

- `requirements.txt` — `python-multipart`
- `core/database/schema.py` — tabela `squad_chat_attachments`
- `core/chats/chat_service.py` — remoção de pasta de anexos antes de apagar chat
- `core/orchestration/bootstrap_chat_service.py` — `chat_id` opcional e menção a anexos
- `core/projects/project_bootstrap_service.py` — secção de anexos no `refine_context_markdown_from_chat`
- `apps/api/schemas/runs.py` — `RunArtifactItem`, `RunArtifactsResponse`
- `apps/api/schemas/chats.py` — `ChatAttachmentResponse`
- `apps/api/routes/runs.py` — `GET /{run_id}/artifacts`
- `apps/api/routes/chats.py` — rotas de anexos + import `chat_attachment_service`
- `apps/web/src/lib/api.ts` — funções e tipos de artefactos/anexos
- `apps/web/src/components/ChatWindow.tsx` — barra de anexos
- `apps/web/src/components/MessageInput.tsx` — botão de anexar imagem
- `apps/web/src/components/ScrumBoard.tsx` — painel «Ver resultado»
- `apps/web/src/app/page.tsx` — estado de anexos e upload

## Endpoints novos ou alterados

| Método | Caminho | Descrição |
|--------|---------|-----------|
| GET | `/api/runs/{run_id}/artifacts` | JSON com `input.md`, `final.md`, `execution.log` |
| GET | `/api/chats/attachments/{attachment_id}` | Ficheiro binário (imagem) |
| GET | `/api/chats/{chat_id}/attachments` | Lista de anexos |
| POST | `/api/chats/{chat_id}/attachments` | Upload `multipart/form-data` (`file`) |

Os endpoints existentes mantêm o mesmo comportamento.

## Fluxo manual de validação (síntese)

1. Subir API (`uvicorn apps.api.main:app --reload`) e web (`npm run dev` em `apps/web`).
2. Selecionar projeto CAP (ou outro com `local_path` válido).
3. Board: seleccionar tarefa, preparar run, executar se necessário, **Ver resultado** e confirmar os três separadores.
4. Chat: anexar PNG/JPEG/WebP, ver mensagem «Imagem anexada», lista e abrir preview.
5. Confirmar ficheiro em `<local_path>/.squad/attachments/chats/<chat_id>/`.
6. Refinar contexto / onboarding e verificar que o fluxo continua estável.

## Comandos executados

```text
pip install "python-multipart>=0.0.9"
python -m pytest tests/ -q
cd apps/web && npm run lint && npm run build
```

## Resultado dos testes

- `python -m pytest tests/ -q` — **55 passed** (na última execução local desta fase).
- `npm run lint` — sem avisos.
- `npm run build` — concluído com sucesso.

## Riscos e ressalvas

- Leitura de artefactos limitada a **1 MiB** por ficheiro na API; ficheiros maiores devolvem `exists: true`, `content: null`, `truncated: true`.
- Runs do Board vivem na raiz **squad-agentes** (`runs/...`), não no repositório cliente — alinhado com a implementação actual de `prepare_run` / `execute_board_run`.
- Imagens não são enviadas ao modelo OpenAI nesta fase; apenas texto (nomes / secção no refine).

## Status final

**Concluída** — critérios de aceite da fase 5.12 cumpridos com testes, lint e build verdes.
