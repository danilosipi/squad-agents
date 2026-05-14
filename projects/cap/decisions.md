# CAP — Registro de Decisões

## DEC-001 — CAP como primeiro piloto do squad-agentes

O CAP será o primeiro projeto real usado para validar a criação e execução de squads especializadas no `squad-agentes`.

## DEC-002 — CAP-BASE como primeiro módulo

O `cap-base` será o primeiro módulo real do CAP, responsável por cadastros institucionais, organizações, usuários, permissões, parâmetros e auditoria cadastral.

## DEC-003 — Base de Dados do CAP-BASE como primeira frente

A primeira frente de implementação será a base de dados do módulo CAP-BASE.

Primeiro arquivo real previsto:

```text
../cap-platform/repos/cap-base/prisma/base.prisma
```

## DEC-004 — Separação entre orquestrador e código real

O `squad-agentes` guarda agentes, contexto, backlog, decisões, runs, outputs, validações e evidências.

O código real do CAP deve ser salvo no projeto `cap-platform`.

## DEC-005 — Fluxo oficial da squad CAP

```text
Danilo → PO CAP → Arquiteto CAP → Dev CAP → Validação determinística → Reviewer CAP → QA CAP → Aprovação humana
```

## DEC-006 — PO CAP como ponto de conversa

O Danilo conversa com o PO CAP. O PO transforma a conversa em projeto, módulo, épico, feature, história, critérios de aceite e tarefas.

## DEC-010 — Primeira entrega real do CAP-BASE validada

A primeira entrega real da squad CAP foi concluída com sucesso.

Entrega:

* Base de Dados do Módulo CAP-BASE

Arquivo criado:

* D:\Drive\Projetos\cap-platform\repos\cap-base\prisma\base.prisma

Evidência:

* runs/cap/001-cap-base-database/final.md
* runs/cap/001-cap-base-database/write-files-output.md

Resultado:

* Arquivo físico presente
* `npx.cmd prisma validate --schema D:\Drive\Projetos\cap-platform\repos\cap-base\prisma\base.prisma` executado
* Exit code: 0
* Status final consolidado: APROVADO COM EVIDÊNCIA REAL

Decisão:
A entrega da base de dados fundacional do CAP-BASE está aprovada como primeira entrega real da squad CAP.

## DEC-011 — Domínio inicial do CAP-BASE validado

A segunda entrega real da squad CAP foi concluída com sucesso.

Entrega:

* Domínio / Entidades do Módulo CAP-BASE

Arquivos criados:

* cap-platform/repos/cap-base/src/domain/entities/*.entity.ts
* cap-platform/repos/cap-base/src/domain/index.ts
* cap-platform/repos/cap-base/src/index.ts
* cap-platform/repos/cap-base/tsconfig.json
* cap-platform/repos/cap-base/package.json

Evidência:

* runs/cap/002-cap-base-domain/final.md
* runs/cap/002-cap-base-domain/write-files-output.md

Resultado:

* 23 entidades TypeScript criadas
* Imports entre entidades corrigidos
* Propriedades ajustadas com definite assignment assertion (!)
* `npx.cmd --yes tsc --noEmit` executado
* Exit code: 0
* Status final consolidado: APROVADO COM EVIDÊNCIA REAL

Decisão:
A estrutura inicial de domínio do CAP-BASE está aprovada como segunda entrega real da squad CAP.

## DEC-012 — Validação TypeScript do domínio CAP-BASE concluída

A validação TypeScript da estrutura inicial de domínio do CAP-BASE foi concluída com sucesso.

Entrega:
- Validação técnica das entidades TypeScript do CAP-BASE

Arquivos criados:
- cap-platform/repos/cap-base/tsconfig.json
- cap-platform/repos/cap-base/package.json

Arquivos ajustados:
- cap-platform/repos/cap-base/src/domain/entities/*.entity.ts

Correções aplicadas:
- Propriedades ajustadas com definite assignment assertion (!)
- Imports relativos entre entidades corrigidos
- `strict: true` mantido no tsconfig

Evidência:
- runs/cap/002-cap-base-domain/final.md
- runs/cap/002-cap-base-domain/write-files-output.md

Resultado:
- `npx.cmd --yes tsc --noEmit` executado
- Exit code: 0
- Status final consolidado: APROVADO COM EVIDÊNCIA REAL

Decisão:
A estrutura inicial de domínio do CAP-BASE está validada tecnicamente com TypeScript e aprovada como entrega real da squad CAP.

## DEC-013 — Contratos de repositório do CAP-BASE validados

A terceira entrega real da squad CAP foi concluída com sucesso.

Entrega:
- Contratos / Interfaces de Repositório do Módulo CAP-BASE

Arquivos criados:
- cap-platform/repos/cap-base/src/domain/repositories/*.repository.ts
- cap-platform/repos/cap-base/src/domain/repositories/index.ts
- cap-platform/repos/cap-base/src/domain/entities/index.ts

Evidência:
- runs/cap/003-cap-base-repository-contracts/final.md
- runs/cap/003-cap-base-repository-contracts/write-files-output.md

Resultado:
- 23 contratos de repositório criados
- Barrel de repositories criado
- Barrel de entities criado
- `npx.cmd --yes tsc --noEmit` executado
- Exit code: 0
- Status final consolidado: APROVADO COM EVIDÊNCIA REAL

Decisão:
Os contratos de repositório do CAP-BASE estão aprovados como terceira entrega real da squad CAP.

## DEC-014 — CAP-BASE no squad-agentes: Prisma 6.19.3 e CLI global

No monorepo `squad-agentes`, o pacote `repos/cap-base` fixa **Prisma 6.19.3** e **`@prisma/client` 6.19.3** em `devDependencies`.

A **CLI global Prisma 7** (ou `npx prisma` sem pin) **não** é referência para `format` / `validate` / `generate` deste módulo: o fluxo e o schema seguem a linha 6.x com `url` no `datasource`.

**Decisão:** validação e geração oficiais do CAP-BASE passam pelos scripts `npm run db:*` do pacote ou por invocação explícita `prisma@6.19.3` / `npx --prefix repos/cap-base prisma …`.

## DEC-015 — Separação `DATABASE_URL` e `CAP_BASE_INTEGRATION_DATABASE_URL`

- **`DATABASE_URL`** — usada pelo Prisma CLI (migrate, validate onde aplicável), `db:seed` e geração de client conforme documentação do pacote.
- **`CAP_BASE_INTEGRATION_DATABASE_URL`** — usada **apenas** pelo runner **`npm run test:integration`** (base dedicada de teste; não apontar para produção).

**Decisão:** manter as variáveis com responsabilidades distintas; em local pode coincidir o destino PostgreSQL, mas os nomes e os consumidores permanecem separados.

## DEC-016 — Seed idempotente preparado; execução real documentada como pendência

O CAP-BASE inclui dados fundacionais, `CapBaseSeedService` e `npm run db:seed` (ver `docs/09-seed-cap-base.md`), com idempotência por chaves naturais onde o schema o permite.

**Decisão:** o desenho do seed está aprovado para o MVP técnico; a **execução verificada contra PostgreSQL real** fica como passo operacional explícito quando a base estiver disponível (não bloquear documentação e CI apenas com unitários).

## DEC-017 — Composition root sem instanciar `PrismaClient`

A função **`createCapBaseModule`** recebe um cliente **Prisma-like** já construído e monta repositórios concretos e use cases.

**Decisão:** o composition root **não** instancia `PrismaClient` no factory — o caller (app, script ou teste) mantém o controlo do ciclo de vida e da configuração do client.

## DEC-018 — API HTTP, NestJS e controllers fora do MVP técnico atual do `@cap/base`

O pacote `@cap/base` entrega biblioteca (domínio, aplicação, infraestrutura Prisma, seed, composição).

**Decisão:** **não** integrar NestJS module, controllers nem servidor HTTP neste MVP; uma API futura deve viver noutro artefacto que dependa de `@cap/base`.

## DEC-019 — Migrations: scripts oficiais sem obrigar migration inicial versionada em todas as fases

Os scripts `db:migrate:*` e `db:push:test` estão documentados em `docs/08-migrations-cap-base.md`. O caminho oficial para ambientes controlados continua a ser **migrations versionadas**; `db:push:test` limita-se a bases de teste.

**Decisão:** preparação de migrations e política documentada são parte do módulo; a **existência e o nome da primeira migration SQL** dependem do fluxo `migrate dev` acordado com a base alvo — estado a confirmar na pasta `prisma/migrations/` por ambiente.

## DEC-020 — MVP técnico do CAP-BASE (`@cap/base`) aprovado com ressalvas operacionais

No monorepo `squad-agentes`, o pacote `repos/cap-base` conclui o **MVP técnico** definido nas fases 6–22 do run **005**: schema e validações, domínio, aplicação, repositórios Prisma, seed preparado, scripts de migrations, composition root, testes unitários/fakes e documentação (`docs/07`–`docs/11`).

As validações automáticas (`npm run db:validate`, `npm run typecheck`, `npm test`, `python scripts/validate_cap_base_schema.py`) foram cumpridas no fechamento da **FASE 22**.

**Ressalvas operacionais** (não bloqueantes para aprovação “com ressalvas”): execução verificada de **`npm run test:integration`** contra PostgreSQL real ainda dependente de ambiente; **`npm run db:seed`** contra base real ainda pendente de evidência operacional; **migration inicial** versionada em `prisma/migrations/` ainda não garantida em disco.

**Decisão:** o **MVP técnico do CAP-BASE** é declarado **APROVADO COM RESSALVAS OPERACIONAIS**; próximos passos são correr integração/seed/migrate dev em base dedicada e expor consumo HTTP/Nest noutro artefacto, conforme `docs/11-cap-base-mvp-technical-closure.md`.