# @cap/base (CAP-BASE)

O **CAP-BASE** (`@cap/base`) é o **módulo fundacional do CAP** no monorepo `squad-agentes`: schema Prisma canónico, contratos de domínio, casos de uso, integração Prisma, seed preparado e composition root. **Ainda não inclui** API HTTP, NestJS, controllers nem servidor embutido — é uma **biblioteca TypeScript** para composição noutros processos ou serviços.

---

## Objetivo

Centralizar o **schema de dados** (Prisma) e o **esqueleto de código em camadas** (domínio, aplicação, infraestrutura, composição), como pacote **`@cap/base`**, evoluindo de forma incremental **sem** acoplamento a frameworks de agentes, UI ou NestJS.

---

## Responsabilidades

- Manter o schema Prisma canónico em `prisma/base.prisma` (**23 models** obrigatórios; validação em `scripts/validate_cap_base_schema.py` na raiz do `squad-agentes`).
- Definir **entidades de domínio**, **value objects** e **contratos de repositório** alinhados ao modelo relacional.
- Implementar **casos de uso** na camada `application` e **repositórios Prisma** na `infrastructure`, sem que domínio/aplicação importem Prisma.
- Expor **composition root** (`createCapBaseModule`) para montar repositórios e use cases a partir de um cliente Prisma-like.
- Fornecer **seed idempotente** (dados fundacionais) e scripts oficiais `db:*` documentados em `docs/`.
- Expor API pública mínima em `src/index.ts` (tipos, use cases, factories, repositórios conforme fase atual).

---

## Fora de escopo (MVP técnico atual)

- **API HTTP**, rotas ou **controllers**.
- **NestJS** (módulos, providers DI do Nest, etc.).
- **Servidor HTTP** embutido no pacote.
- **Lógica de UI** ou frontend.
- **Agentes** e meta-orquestrador do `squad-agentes` (ficam no repositório de automação).
- Inflar regras de negócio antes de contratos e entidades estáveis.

---

## Arquitetura interna

```text
prisma/base.prisma          ← fonte de verdade do schema PostgreSQL
src/domain/                 ← entidades, VOs, interfaces de repositório (sem Prisma)
src/application/          ← DTOs, use cases, mappers de aplicação (sem Prisma)
src/infrastructure/prisma/  ← repositórios concretos + mappers Prisma ↔ domínio
src/infrastructure/seed/    ← dados iniciais, serviço de seed, entrypoint run-seed
src/composition/            ← createCapBaseModule + tipos do módulo composto
src/index.ts                ← exports públicos do pacote
```

Fluxo de dependência: **composition / callers** → **application** → **domain** ← **infrastructure** (implementações).

---

## Domain (`src/domain/`)

- **Entidades:** `Organization`, `OrganizationRole`, `OrganizationRoleAssignment`.
- **Value objects:** `Cnpj`, `Email`, `Phone`.
- **Repositórios (contratos):** `OrganizationsRepository`, `OrganizationRolesRepository`, `OrganizationRoleAssignmentsRepository`.

---

## Application (`src/application/`)

- **DTOs** para criar/atualizar/listar organizações, papéis e atribuições.
- **Use cases (12):** criar/atualizar/obter/listar organização; criar/atualizar/obter/listar papel; criar/revogar atribuição; listar atribuições por organização ou por papel.
- **Mappers** para outputs de aplicação.

---

## Infrastructure (`src/infrastructure/`)

- **Prisma:** `PrismaOrganizationsRepository`, `PrismaOrganizationRolesRepository`, `PrismaOrganizationRoleAssignmentsRepository` + mappers em `prisma/mappers/`.
- **Seed:** `CapBaseSeedService`, dados em `cap-base-seed-data.ts`, entrypoint `run-seed.ts` (ver secção [Seed](#seed)).

---

## Composition root (`src/composition/`)

- **`createCapBaseModule(client)`** — recebe `PrismaCapBaseRepositoriesClientLike` (`organization`, `organizationRole`, `organizationRoleAssignment`); **não** instancia `PrismaClient` no factory.
- **`DEFAULT_CAP_BASE_ORGANIZATION_PERSISTENCE`** — FKs padrão para `Organization` (`defaultTypeId`, `activeStatusId`, `inactiveStatusId`); na base real as linhas referenciadas devem existir ou a configuração deverá ser generalizada noutra fase.

Exemplo mínimo (TypeScript):

```typescript
import { createCapBaseModule } from "@cap/base";
// import { PrismaClient } from "@prisma/client";

// const prisma = new PrismaClient();
// const app = createCapBaseModule(prisma);

// const org = await app.useCases.createOrganization.execute({
//   legalName: "ACME",
//   documentNumber: "12345678000195",
// });
```

---

## Prisma

- **Versão fixa:** `prisma` e `@prisma/client` **6.19.3** (`package.json` do pacote).
- **CLI global Prisma 7** não é referência para validar este schema (fluxo antigo vs `datasource url`). Usar sempre os scripts `npm run db:*` **dentro** de `repos/cap-base` ou `npx prisma@6.19.3` / `npx --prefix repos/cap-base prisma …`. Detalhes: `docs/07-validacao-prisma-cap-base.md`.

---

## Seed

- Script: **`npm run db:seed`** (requer `DATABASE_URL`).
- Serviço idempotente e dados documentados em **`docs/09-seed-cap-base.md`**.
- **Ressalva:** na preparação das fases do `squad-agentes`, **`db:seed` ainda não foi executado com sucesso contra PostgreSQL real** (validação limitada a typecheck e testes com fakes). Quando houver base de desenvolvimento, seguir a ordem em `docs/08-migrations-cap-base.md`.

---

## Migrations

- Scripts oficiais: `db:migrate:dev`, `db:migrate:deploy`, `db:migrate:status`, `db:push:test` (só teste), alinhados a `docs/08-migrations-cap-base.md`.
- **Ressalva:** scripts e documentação estão **preparados**; **migration inicial SQL versionada** em `prisma/migrations/` pode ainda não existir ou não ter sido gerada neste monorepo — confirmar o estado da pasta antes de assumir histórico de schema em ambientes partilhados.

---

## Testes

| Comando | Âmbito |
|---------|--------|
| **`npm test`** | Testes **unitários** e **fakes** (Vitest, exclui `tests/integration/**`). **Não** exige PostgreSQL. |
| **`npm run test:integration`** | Testes contra **PostgreSQL real**. Exige **`CAP_BASE_INTEGRATION_DATABASE_URL`** (separada de `DATABASE_URL` usada pelo Prisma CLI/seed); se ausente, os integrados podem ficar **skipped** conforme configuração do projeto. |

**Não** confundir: variável de integração é **apenas** para o runner de testes integrados; `DATABASE_URL` serve Prisma/seed.

---

## Comandos oficiais (`repos/cap-base/`)

Na pasta do pacote:

```bash
npm install
npm run db:format
npm run db:validate
npm run db:generate
npm run typecheck
npm test
```

| Script | Descrição resumida |
|--------|---------------------|
| `db:format` | Formata `prisma/base.prisma`. |
| `db:validate` | Valida o schema (URL placeholder via `cross-env` no script). |
| `db:generate` | Gera o Prisma Client. |
| `db:migrate:dev` | Migrations em desenvolvimento. |
| `db:migrate:deploy` | Aplica migrations versionadas (CI/staging/prod). |
| `db:migrate:status` | Estado das migrations. |
| `db:push:test` | `db push` só para **bases de teste**; não substitui política de migrations. |
| `db:seed` | Seed idempotente (requer `DATABASE_URL`). |
| `typecheck` | `tsc --noEmit`. |
| `test` | Vitest unitário/fakes. |
| `test:integration` | Vitest integração (Postgres real se URL definida). |

---

## Status atual

- **Typecheck** e **`npm test`** (unitários/fakes) fazem parte do fluxo habitual de CI/local.
- **Schema:** validação determinística **23/23** models (`validate_cap_base_schema.py`); relatório em `runs/cap/005-real-file-creation/schema-validation-report.md`.
- **Prisma 6.19.3:** alinhado com `db:format` / `db:validate` documentados.
- **Composition root, seed, migrations:** ver secções e `docs/08`, `docs/09`, `docs/10-cap-base-technical-summary.md`, `docs/11-cap-base-mvp-technical-closure.md`.

---

## Pendências conhecidas (operacionais)

1. **`db:seed`** — execução verificada contra PostgreSQL **real** ainda pendente neste ambiente de documentação.
2. **`test:integration`** — depende de `CAP_BASE_INTEGRATION_DATABASE_URL` e base com schema aplicado; **não** obrigatório para `npm test`.
3. **Migration inicial versionada** — confirmar se `prisma/migrations/` contém a primeira migration acordada pela equipa antes de `migrate deploy` em ambientes partilhados.
4. **`DEFAULT_CAP_BASE_ORGANIZATION_PERSISTENCE`** — valores fixos (1 / 10 / 20) assumem dados de referência na base; eventual configuração injetável pode ser uma evolução futura.

---

## Documentação relacionada

| Documento | Conteúdo |
|-----------|----------|
| `docs/07-validacao-prisma-cap-base.md` | Validação Prisma e pin de versão. |
| `docs/08-migrations-cap-base.md` | Migrations, variáveis, ordem com seed e integração. |
| `docs/09-seed-cap-base.md` | Seed fundacional e idempotência. |
| `docs/10-cap-base-technical-summary.md` | Resumo técnico consolidado do módulo. |
| `docs/11-cap-base-mvp-technical-closure.md` | Fechamento formal do MVP técnico (escopo, ressalvas, status recomendado). |
| `projects/cap/decisions.md` | Decisões arquiteturais do projeto CAP. |
