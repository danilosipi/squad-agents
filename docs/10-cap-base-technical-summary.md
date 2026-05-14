# Resumo técnico — CAP-BASE (`@cap/base`)

Pacote em `repos/cap-base/`. **Módulo fundacional do CAP** no monorepo `squad-agentes`: dados e cadastro institucional base (organizações, papéis, vínculos), **sem** API HTTP, NestJS ou controllers neste MVP.

---

## Objetivo

Fornecer schema Prisma canónico (PostgreSQL), modelo de domínio enxuto, casos de uso, persistência Prisma desacoplada, seed idempotente e um **composition root** para montar o grafo de dependências a partir de um cliente Prisma-like.

---

## Arquitetura

| Camada | Pasta | Notas |
|--------|--------|--------|
| Domain | `src/domain/` | Sem imports de Prisma. |
| Application | `src/application/` | Use cases + DTOs; sem Prisma. |
| Infrastructure | `src/infrastructure/` | Prisma repositories, mappers, seed. |
| Composition | `src/composition/` | `createCapBaseModule` — não cria `PrismaClient`. |

---

## Models Prisma principais (schema)

O ficheiro `prisma/base.prisma` define **23 models** obrigatórios (validador na raiz). Entre os mais usados pelo código TypeScript atual:

- **Organização:** `Organization`, `OrganizationType`, `OrganizationStatus`.
- **Papéis:** `OrganizationRole`, `OrganizationRoleAssignment`.
- **Outros** no schema: `User`, `UserStatus`, `Role`, `Permission`, `RolePermission`, `UserOrganization`, `Address`, `AddressType`, `Contact`, `ContactType`, `Document`, `DocumentType`, `SystemParameter`, `SystemParameterType`, `SystemParameterScope`, `AuditLog`, `AuditActionType`, `AuditEntityType`.

A lista completa e a regra “não remover models” estão em `scripts/validate_cap_base_schema.py`.

---

## Entidades de domínio

- `Organization` — razão social / nome legal, nome fantasia, documento, ativo.
- `OrganizationRole` — código único, nome, descrição, ativo.
- `OrganizationRoleAssignment` — vínculo organização ↔ papel, datas de atribuição/revogação.

---

## Value objects

- `Cnpj`, `Email`, `Phone` — validação/formato no domínio.

---

## Repositórios (contratos e implementações)

| Contrato (domain) | Implementação (infrastructure) |
|-------------------|--------------------------------|
| `OrganizationsRepository` | `PrismaOrganizationsRepository` |
| `OrganizationRolesRepository` | `PrismaOrganizationRolesRepository` |
| `OrganizationRoleAssignmentsRepository` | `PrismaOrganizationRoleAssignmentsRepository` |

---

## Use cases (application)

Organização: criar, atualizar, obter, listar.  
Papel: criar, atualizar, obter, listar.  
Atribuição: criar, revogar, listar por organização, listar por papel.

---

## Composition root

- **`createCapBaseModule(client)`** em `src/composition/create-cap-base-module.ts`.
- **`CapBaseModule`:** `repositories` + `useCases` (12 casos de uso).
- **`PrismaCapBaseRepositoriesClientLike`:** interseção dos delegates necessários aos três repositórios.
- **`DEFAULT_CAP_BASE_ORGANIZATION_PERSISTENCE`:** FKs padrão para persistência de `Organization`.

---

## Seed

- Dados: `src/infrastructure/seed/cap-base-seed-data.ts`.
- Serviço: `CapBaseSeedService` (idempotência por `code` em papéis e por `name` em referências sem `@unique` extra).
- Entrypoint: `run-seed.ts` → `npm run db:seed`.
- Documentação detalhada: `docs/09-seed-cap-base.md`.

**Ressalva:** execução do seed contra PostgreSQL real ainda não validada de ponta a ponta no histórico de fases do `squad-agentes` documentado aqui.

---

## Testes

- **`npm test`:** unitários + fakes, sem Postgres.
- **`npm run test:integration`:** Postgres real via `CAP_BASE_INTEGRATION_DATABASE_URL`; separado de `DATABASE_URL`.

---

## Validações

| Validação | Onde |
|-----------|------|
| Models 23/23 | `python scripts/validate_cap_base_schema.py` (raiz) |
| Schema Prisma | `npm run db:validate` em `repos/cap-base` |
| TypeScript | `npm run typecheck` |

---

## Ressalvas

1. Sem API/Nest/controller no pacote.  
2. Prisma **6.19.3** no pacote; CLI global **7** não é referência.  
3. `DATABASE_URL` vs `CAP_BASE_INTEGRATION_DATABASE_URL` — papéis distintos (Prisma/seed vs testes integrados).  
4. Migrations: scripts prontos; estado exato da pasta `prisma/migrations/` depende da equipa/ambiente.  
5. Seed e integração: ver README e `docs/08` / `docs/09`.

---

## Próximos passos (sugestão)

- Correr `db:seed` e `test:integration` numa base PostgreSQL de desenvolvimento quando disponível.
- Gerar e versionar a **primeira migration** oficial quando o fluxo `migrate dev` estiver acordado com a base alvo.
- Evoluir o composition root (ex.: configuração injetável de `PrismaOrganizationsPersistenceConfig`) se os FKs padrão deixarem de servir a todos os ambientes.
- Introduzir camada HTTP/Nest noutro pacote ou serviço que **consuma** `@cap/base`, mantendo este módulo como biblioteca.
