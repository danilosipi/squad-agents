# Fechamento do MVP técnico — CAP-BASE (`@cap/base`)

## Objetivo do fechamento

Registrar formalmente o **estado de entrega** do MVP técnico do pacote `repos/cap-base` (`@cap/base`): o que foi construído, como se valida, que limitações operacionais permanecem e qual **status consolidado** recomenda a equipa antes de evoluir para API, produção ou integrações adicionais.

Este documento **não** substitui relatórios por fase em `runs/cap/005-real-file-creation/`; sintetiza-os e aponta para evidências.

---

## Escopo entregue (MVP técnico)

- **Schema Prisma** canónico (`prisma/base.prisma`) com **23 models** obrigatórios, validação determinística na raiz do monorepo.
- **Domínio:** entidades `Organization`, `OrganizationRole`, `OrganizationRoleAssignment`; value objects `Cnpj`, `Email`, `Phone`; contratos de repositório.
- **Application:** DTOs, mappers e **12 use cases** (organização, papel, atribuição).
- **Infrastructure:** repositórios Prisma com mappers; **seed** idempotente (dados + serviço + `npm run db:seed`).
- **Composition root:** `createCapBaseModule` com cliente Prisma-like (sem instanciar `PrismaClient` no factory).
- **Migrations:** scripts `npm run db:migrate:*` e `db:push:test` documentados (`docs/08-migrations-cap-base.md`).
- **Testes unitários** com Vitest e fakes (sem PostgreSQL obrigatório para `npm test`).
- **Documentação:** `README` do pacote, `docs/07`–`docs/11`, matriz de evidências e checklist no run **005**.

---

## Escopo fora do MVP técnico

- API HTTP, **controllers**, **NestJS**, servidor embutido no `@cap/base`.
- Execução **garantida** de seed ou de testes integrados contra PostgreSQL real neste fechamento (preparados, validação operacional pendente onde indicado).
- **Migration SQL inicial** versionada obrigatória em disco em todas as cópias do repositório (scripts e política entregues; ficheiros em `prisma/migrations/` dependem do fluxo `migrate dev` da equipa).

---

## Arquitetura entregue

Camadas: **domain** (sem Prisma) → **application** (sem Prisma) ← **infrastructure** (Prisma, seed) — **composition** monta grafos a partir de um client injetado.

---

## Artefatos principais

| Área | Local / artefato |
|------|-------------------|
| Schema | `repos/cap-base/prisma/base.prisma` |
| Pacote público | `repos/cap-base/src/index.ts` |
| Composition | `repos/cap-base/src/composition/` |
| Seed | `repos/cap-base/src/infrastructure/seed/` |
| Evidências por fase | `runs/cap/005-real-file-creation/cap-base-mvp-evidence-matrix.md` |
| Checklist | `runs/cap/005-real-file-creation/cap-base-mvp-final-checklist.md` |
| Decisões CAP | `projects/cap/decisions.md` (incl. DEC-014–DEC-020) |

---

## Schema Prisma

- PostgreSQL; generator `prisma-client-js`; **23 models** alinhados ao validador `scripts/validate_cap_base_schema.py`.
- Pin **Prisma 6.19.3** no pacote; ver `docs/07-validacao-prisma-cap-base.md`.

---

## Domínio

Entidades e VOs acima; invariantes e repositórios como interfaces em `src/domain/`.

---

## Application

Use cases e DTOs para CRUD/listagem de organizações, papéis e atribuições; sem dependência de infraestrutura.

---

## Infrastructure

Implementações Prisma dos três repositórios; mappers; `CapBaseSeedService` e entrypoint `run-seed.ts`.

---

## Composition root

`createCapBaseModule`, tipos `CapBaseModule` / `CapBaseRepositories` / `CapBaseUseCases`, `DEFAULT_CAP_BASE_ORGANIZATION_PERSISTENCE`.

---

## Seed

Preparado e documentado em `docs/09-seed-cap-base.md`; **execução verificada contra PostgreSQL real** permanece ressalva operacional até ambiente dedicado.

---

## Migrations

Documentação e scripts em `docs/08-migrations-cap-base.md`; **primeira migration versionada** a confirmar em `prisma/migrations/` por ambiente.

---

## Testes

- **`npm test`:** unitários + fakes (55 testes no fechamento FASE 22).
- **`npm run test:integration`:** preparado; depende de `CAP_BASE_INTEGRATION_DATABASE_URL` e base com schema — **não** exigido para declarar o MVP técnico de biblioteca fechado com ressalvas.

---

## Documentação

- `repos/cap-base/README.md` — visão consolidada.
- `docs/07` … `docs/11` — Prisma, migrations, seed, resumo técnico, **este fechamento**.

---

## Decisões registradas

`projects/cap/decisions.md`: DEC-001 … DEC-019 e **DEC-020** (fechamento MVP com ressalvas).

---

## Evidências por fase

Ver **`runs/cap/005-real-file-creation/cap-base-mvp-evidence-matrix.md`**.

---

## Ressalvas operacionais

1. **Teste integrado** com Postgres real: depende de URL segura e base preparada; não bloqueia o MVP de **código** entregue.
2. **`db:seed` real:** idempotência testada com fakes; corrida contra DB real pendente de validação operacional.
3. **Migration inicial SQL:** pasta `prisma/migrations/` pode estar vazia até primeira `migrate dev` acordada.

---

## Status final recomendado

**MVP TÉCNICO APROVADO COM RESSALVAS OPERACIONAIS**

Critérios automáticos (`db:validate`, `typecheck`, `npm test`, `validate_cap_base_schema.py`) cumprem-se; as três ressalvas acima impedem um “aprovado” pleno sem evidência de runtime em base real.

---

## Próximos passos sugeridos

1. Subir PostgreSQL de desenvolvimento/teste; aplicar schema (`migrate dev` ou `db:push:test` só em teste); correr `db:seed` e `test:integration`.
2. Versionar a **primeira migration** oficial quando o nome e o SQL forem fechados com a equipa.
3. Consumir `@cap/base` a partir de um **serviço ou módulo HTTP** externo (fora deste pacote).
