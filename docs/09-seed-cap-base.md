# Seed inicial — CAP-BASE (`@cap/base`)

## Objetivo

Garantir dados **fundacionais** (papéis de organização, tipos e estados de organização, escopos de parâmetro de sistema) de forma **repetível** e **idempotente**, alinhados ao schema `repos/cap-base/prisma/base.prisma`, sem acoplar domínio ou casos de uso da aplicação.

## Dados iniciais

| Conjunto | Onde vive no código | Persistência no schema |
|----------|---------------------|-------------------------|
| Papéis de organização | `INITIAL_ORGANIZATION_ROLES` em `repos/cap-base/src/infrastructure/seed/cap-base-seed-data.ts` | `OrganizationRole` (`code` único, `name`, `description?`, `isActive`) |
| Tipos de organização | `INITIAL_ORGANIZATION_TYPES` | `OrganizationType.name` (valores canónicos `LEGAL_ENTITY`, `INDIVIDUAL`) |
| Estados de organização | `INITIAL_ORGANIZATION_STATUSES` (alias exportado: `INITIAL_STATUSES`) | `OrganizationStatus.name` (`ACTIVE`, `INACTIVE`) |
| Escopos de parâmetro | `INITIAL_SYSTEM_PARAMETER_SCOPES` | `SystemParameterScope.name` (`GLOBAL`, `ORGANIZATION`) |

Os códigos de papel seguem a lista acordada na fase (ex.: `CAPITALIZATION_COMPANY`, `PROMOTER_COMPANY`, …). Rótulos e descrições em português são apenas dados de seed.

## Regra de idempotência

- **`OrganizationRole`**: chave natural **`code`** (único no Prisma). O serviço usa `findUnique` + `upsert` para criar, saltar se já estiver igual ou atualizar se `name` / `description` / `isActive` divergirem.
- **Tabelas só com `name`**: não há `@unique` em `OrganizationType`, `OrganizationStatus` nem `SystemParameterScope` no schema atual. A idempotência é por **`findFirst({ name })`**: se existir linha com o mesmo `name`, o seed **não cria duplicata** (conta como `skipped`). Isto pressupõe disciplina na base (evitar duplicar manualmente o mesmo `name`).

## Como executar quando houver banco

1. Aplicar migrations (ver `docs/08-migrations-cap-base.md`).
2. Gerar o client: `npm run db:generate`.
3. Definir **`DATABASE_URL`** com uma URL PostgreSQL válida.
4. Na pasta `repos/cap-base`: `npm run db:seed`.

O script `src/infrastructure/seed/run-seed.ts` instancia `PrismaClient`, executa `CapBaseSeedService.run()` e imprime um resumo JSON no console. Se `DATABASE_URL` estiver ausente ou vazia, o processo termina com mensagem clara e código de saída diferente de zero.

## Variáveis necessárias

| Variável | Obrigatória para `db:seed` | Descrição |
|----------|---------------------------|-----------|
| `DATABASE_URL` | Sim | URL PostgreSQL usada pelo Prisma (mesma convenção das migrations). |

## Fase 19 — execução contra banco real

**Esta fase não executou o seed contra PostgreSQL real** no ambiente de preparação (apenas typecheck, testes unitários com cliente fake e validação estática do schema). Quando Docker/Postgres estiver disponível, validar manualmente `npm run db:seed` numa base de desenvolvimento.

## Testes sem banco

`repos/cap-base/tests/infrastructure/cap-base-seed.service.test.ts` cobre criação, segunda execução sem duplicar papéis, atualização quando o conteúdo diverge e contadores das referências nomeadas.
