# Web Chat MVP local (Fase 5.4)

## Objetivo

Fornecer uma **interface web local** no estilo ChatGPT para operar o squad-agentes: sidebar com projetos, lista de chats por projeto, área de conversa e envio de mensagens, tudo persistido pela **API FastAPI** (SQLite), **sem** executar a squad, **sem** OpenAI e **sem** autenticação nesta fase.

## Como rodar a API

Na raiz do repositório `squad-agentes`:

```bash
python scripts/init_db.py
python scripts/api_dev.py
```

A API fica em `http://127.0.0.1:8000` por padrão. A aplicação Next.js chama essa base a partir do browser; por isso a API inclui **CORS** liberando `http://localhost:3000` e `http://127.0.0.1:3000`.

## Como rodar a web

```bash
cd apps/web
npm install
npm run dev
```

Abra `http://localhost:3000` (ou o host que o Next indicar).

Build de produção local:

```bash
cd apps/web
npm run build
npm start
```

## Variáveis de ambiente

| Variável | Descrição |
|----------|-----------|
| `NEXT_PUBLIC_API_BASE_URL` | URL base da FastAPI. Padrão no código: `http://127.0.0.1:8000` se não definida. |

Exemplo em `apps/web/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Há também `apps/web/.env.local.example` com o mesmo valor.

## Funcionalidades disponíveis

- **Projetos**: lista via `GET /api/projects`; seleção na sidebar; **Novo** (`POST /api/projects`) e **Registrar** (`POST /api/projects/register`) com prompts simples.
- **Chats**: ao selecionar projeto, `GET /api/chats/project/{slug}`; **+ Novo** cria chat (`POST /api/chats`); seleção na segunda coluna.
- **Mensagens**: ao selecionar chat, `GET /api/chats/{id}/messages`; envio com `POST /api/chats/messages` com `role: user`.
- **Resposta local**: após cada mensagem do usuário, a UI envia automaticamente uma mensagem `assistant` com o texto fixo: *"Mensagem registrada. A execução da squad será conectada na próxima fase."*, para simular conversa completa sem modelo.

## Limitações atuais

- Sem login, sem RBAC, sem deploy.
- Sem integração com meta-orquestrador / `run_squad`.
- UI deliberadamente simples (CSS global, sem design system pesado).
- `npm install` pode reportar avisos de segurança de dependências; avaliar upgrades pontuais (`next`, etc.) fora do escopo deste MVP.

## Próxima fase

Conectar o **meta-orquestrador / squad** (e, quando aplicável, OpenAI ou outros provedores) para que mensagens do utilizador disparem runs reais e respostas de agentes substituam o texto fixo do `assistant`.
