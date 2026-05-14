# Migrations e banco — CAP-BASE (`@cap/base`)

## Versão do Prisma

O pacote `repos/cap-base` fixa **Prisma 6.19.3** e **`@prisma/client` 6.19.3** (alinhados entre si). O CLI global Prisma 7 não substitui os scripts `npm run db:*` deste repositório.

## Provider oficial

O ficheiro `repos/cap-base/prisma/base.prisma` declara **`provider = "postgresql"`** e `url = env("DATABASE_URL")`.

- **SQLite** não é o alvo: mudar para SQLite exigiria outro datasource e duplicação ou alteração grande do schema, fora do escopo do CAP-BASE atual.
- Ambiente local de desenvolvimento e CI devem usar **PostgreSQL** acessível via `DATABASE_URL` (ou variável específica de integração, ver abaixo).

## Variáveis de ambiente

| Variável | Uso |
|----------|-----|
| `DATABASE_URL` | URL usada por `prisma migrate dev`, `migrate deploy`, `migrate status`, **`npm run db:seed`** e por `prisma generate` quando aplicável. |
| `CAP_BASE_INTEGRATION_DATABASE_URL` | **Apenas** testes integrados (`npm run test:integration`). O runner de integração lê **esta** variável (não confundir com `DATABASE_URL` dos comandos Prisma/seed). Base dedicada de teste; **nunca** apontar para produção. Em ambiente local é comum coincidir com a URL da mesma instância PostgreSQL usada em `DATABASE_URL`, desde que seja **sempre** base de teste. |

### Regra de segurança

- **Não** uses `DATABASE_URL` de produção em `CAP_BASE_INTEGRATION_DATABASE_URL`.
- **Não** executes `migrate dev` contra bases partilhadas de produção.
- **`npm run db:seed`** lê **`DATABASE_URL`**. Não apontar `DATABASE_URL` para **produção** sem aprovação explícita da equipa e política de dados; em geral, seed em produção é excecional e controlado fora deste guia.
- **`CAP_BASE_INTEGRATION_DATABASE_URL`** é lida **apenas** pelo `npm run test:integration` (não pelo Prisma CLI, nem por `db:seed`).
- Para validação estática do ficheiro schema sem subir servidor, o projeto já usa `npm run db:validate` com uma URL fictícia apenas para o comando `prisma validate`.

## Comandos oficiais (`repos/cap-base`)

| Script | Descrição |
|--------|-----------|
| `npm run db:format` | Formata `prisma/base.prisma`. |
| `npm run db:validate` | Valida o schema (não exige DB acessível para além do que o Prisma CLI precisar). |
| `npm run db:generate` | Gera o **Prisma Client** a partir de `prisma/base.prisma`. **Obrigatório** após clonar ou alterar o schema, antes de compilar/testar código que importa `@prisma/client`. |
| `npm run db:migrate:dev` | Cria/aplica migrations em desenvolvimento (`prisma migrate dev`). |
| `npm run db:migrate:deploy` | Aplica migrations pendentes (`prisma migrate deploy`) — típico de CI/staging/produção. |
| `npm run db:migrate:status` | Mostra estado das migrations. |
| `npm run db:push:test` | `prisma db push` com `--skip-generate` — **aceitável apenas** para bases de **teste** quando ainda não há pasta `prisma/migrations/`. Exige `DATABASE_URL` apontando para essa base (pode coincidir com a URL usada em integração local). **Não** substitui migrations oficiais em ambientes partilhados nem é o caminho oficial para staging/produção. |
| `npm run db:seed` | Aplica o seed idempotente do CAP-BASE (ver [Seed inicial](#seed-inicial-e-documentação-dedicada)). Exige `DATABASE_URL`; instancia `PrismaClient` no entrypoint de infraestrutura. |

## `migrate dev` vs `migrate deploy`

- **`migrate dev`**: interativo no desenvolvimento; gera ficheiros SQL em `prisma/migrations`, aplica ao `DATABASE_URL` configurado e regera o client quando necessário. Adequado para evolução do schema na máquina do programador.
- **`migrate deploy`**: não interativo; aplica migrations já versionadas. Adequado para pipelines e ambientes onde não se gera migration nova.

- **Migrations versionadas** (`migrate dev` / `migrate deploy`) continuam a ser o **caminho oficial** para ambientes controlados (equipa, CI, staging, produção). `db:push:test` é atalho de conveniência **só** em bases de teste descartáveis ou enquanto não existem migrations em disco.

## Seed inicial e documentação dedicada

O seed fundacional (papéis de organização, tipos/estados de organização, escopos de parâmetro de sistema) está documentado em **`docs/09-seed-cap-base.md`** — objetivo, dados iniciais, idempotência e execução de `npm run db:seed`.

## Ordem recomendada (ambiente local / teste)

Na pasta `repos/cap-base`, após ter PostgreSQL acessível e variáveis definidas:

1. **`npm run db:generate`** — gerar o Prisma Client alinhado ao schema (antes de código que importa `@prisma/client` ou de correr o seed).
2. **Aplicar o schema à base**, conforme o ambiente:
   - **`npm run db:migrate:dev`** (ou `db:migrate:deploy` em CI) quando existirem migrations versionadas em `prisma/migrations/` — preferido para fluxo normal;
   - **ou** **`npm run db:push:test`** apenas se estiveres numa base de **teste** e ainda não houver migrations versionadas (não usar como substituto de política de migrations em ambientes partilhados).
3. **`npm run db:seed`** — popular dados iniciais idempotentes (requer `DATABASE_URL`; detalhes em `docs/09-seed-cap-base.md`).
4. **`npm run test:integration`** — testes contra PostgreSQL real; requer **`CAP_BASE_INTEGRATION_DATABASE_URL`** apontando para uma base com schema aplicado (tipicamente a mesma URL da base de teste local, se assim estiver configurado).

Os testes unitários `npm test` podem correr em qualquer momento e **não** exigem estes passos.

## Testes

| Script | Descrição |
|--------|-----------|
| `npm test` | Apenas testes **unitários** e com **fakes** (exclui `tests/integration/**`). **Não** exige PostgreSQL. |
| `npm run test:integration` | Testes que falam com PostgreSQL real. Exige schema aplicado na base apontada por `CAP_BASE_INTEGRATION_DATABASE_URL`. Se a variável não existir, os testes integrados ficam **skipped** (comando termina com sucesso). |

### Postgres de teste local (Docker — FASE 17.1)

Opcional: `repos/cap-base/docker-compose.integration.yml` sobe um PostgreSQL **16-alpine** só para integração (`cap_base_test` / porta **55432**). Uso típico:

```bash
cd repos/cap-base
docker compose -f docker-compose.integration.yml up -d
```

URL de exemplo (credenciais de **teste**, não produção):

`postgresql://cap_base_test:cap_base_test@127.0.0.1:55432/cap_base_test?schema=public`

### Preparação da base de integração

Alinhar com a [ordem recomendada](#ordem-recomendada-ambiente-local--teste): criar uma base PostgreSQL vazia ou dedicada a testes (Docker acima ou instância própria); correr `db:generate`; aplicar schema via **`db:migrate:dev`/`deploy`** ou, só em teste, **`db:push:test`**; opcionalmente **`db:seed`** se os testes integrados ou o cenário local precisarem dos dados fundacionais; definir **`CAP_BASE_INTEGRATION_DATABASE_URL`** para a base onde o schema está aplicado; por fim **`npm run test:integration`**. Se a variável de integração não existir, o comando termina com sucesso e os testes integrados ficam **skipped**.

## Política de migrations do CAP-BASE

1. **Uma fonte de verdade**: o schema canónico é `repos/cap-base/prisma/base.prisma`.
2. **Migrations versionadas**: alterações de schema que exijam SQL devem entrar em `repos/cap-base/prisma/migrations/` via `migrate dev` (ou equivalente acordado pela equipa), nunca aplicadas “à mão” só em produção sem ficheiro de migration.
3. **Modelos obrigatórios**: não remover nenhum dos 23 models exigidos pelo validador `scripts/validate_cap_base_schema.py`.
4. **Seeds**: o seed inicial do CAP-BASE está descrito em **`docs/09-seed-cap-base.md`** e aplicado com **`npm run db:seed`** após o schema estar na base; deve ser **idempotente** e tratado como **opcional em CI** até existir base dedicada e política acordada.

## Sincronização com o meta-orchestrator

Os ficheiros `runs/cap/005-real-file-creation/schema-for-manifest.prisma` e `files.manifest.json` devem permanecer alinhados com alterações ao schema **quando** a fase de entrega o exigir (validador na raiz do monorepo).
