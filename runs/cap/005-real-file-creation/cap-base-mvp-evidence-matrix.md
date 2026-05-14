# Matriz de evidências — MVP técnico CAP-BASE (run 005)

Tabela de rastreabilidade entre **fases** do plano `squad-agentes`, **entrega principal**, **evidência** (relatório ou artefato) e **status** consolidado neste fechamento. Caminhos relativos à raiz do repositório `squad-agentes`, salvo indicação.

| Fase | Entrega principal | Evidência / arquivo | Status | Ressalva |
|------|-------------------|---------------------|--------|----------|
| 6 | Materialização controlada do schema (`files.manifest`, escrita assistida) | `runs/cap/005-real-file-creation/file-write-report.md`, `runs/cap/005-real-file-creation/input.md` | APROVADO | Run assistido; não substitui revisão humana de conteúdo. |
| 7 | Validação determinística dos 23 models | `runs/cap/005-real-file-creation/schema-validation-report.md`, `scripts/validate_cap_base_schema.py` | APROVADO | Regenerado quando o schema muda. |
| 8 | Validação Prisma 6.x no pacote (`db:validate`, pin CLI) | `runs/cap/005-real-file-creation/prisma-validation-report.md`, `docs/07-validacao-prisma-cap-base.md` | APROVADO | CLI global Prisma 7 não é referência. |
| 9 | Esqueleto do módulo `@cap/base` (package, tsconfig, exports iniciais) | `runs/cap/005-real-file-creation/cap-base-module-report.md` | APROVADO | — |
| 10 | Primeiras entidades de domínio | `runs/cap/005-real-file-creation/cap-base-domain-entities-report.md` | APROVADO | Cobertura parcial do schema completo. |
| 11 | Contratos de repositório (domain) | `runs/cap/005-real-file-creation/cap-base-repository-contracts-report.md` | APROVADO | Três repositórios implementados em Prisma nas fases seguintes. |
| 12 | Use cases de `Organization` | `runs/cap/005-real-file-creation/cap-base-organization-use-cases-report.md` | APROVADO | — |
| 13 | Testes unitários (Vitest) + fakes | `runs/cap/005-real-file-creation/cap-base-tests-report.md` | APROVADO | Sem Postgres. |
| 13.1 | Reprodutibilidade (pin Vitest, tsconfig) | `runs/cap/005-real-file-creation/cap-base-tests-reproducibility-report.md` | APROVADO | — |
| 14 | `PrismaOrganizationsRepository` | `runs/cap/005-real-file-creation/cap-base-prisma-organizations-repository-report.md` | APROVADO | FKs padrão no composition root (1/10/20). |
| 15 | Repositórios Prisma de papel e atribuição | `runs/cap/005-real-file-creation/cap-base-prisma-roles-repositories-report.md` | APROVADO | Ajustes de schema documentados na fase. |
| 16 | Use cases de papel organizacional | `runs/cap/005-real-file-creation/cap-base-role-use-cases-report.md` | APROVADO | — |
| 17 | Testes integrados (config + runner) | `runs/cap/005-real-file-creation/cap-base-integration-tests-report.md` | APROVADO COM RESSALVAS | Exige `CAP_BASE_INTEGRATION_DATABASE_URL` + schema na base. |
| 17.1 | Execução real integrada (Postgres de teste) | `runs/cap/005-real-file-creation/cap-base-integration-real-postgres-report.md` | APROVADO COM RESSALVAS | Docker/Postgres real nem sempre disponível no ambiente de escrita. |
| 18 | Preparação de migrations (scripts, docs) | `runs/cap/005-real-file-creation/cap-base-migrations-preparation-report.md`, `docs/08-migrations-cap-base.md` | APROVADO COM RESSALVAS | Migration inicial SQL versionada pode ainda não existir em `prisma/migrations/`. |
| 19 | Seed idempotente (dados + serviço + `db:seed`) | `runs/cap/005-real-file-creation/cap-base-seed-preparation-report.md`, `docs/09-seed-cap-base.md` | APROVADO COM RESSALVAS | `db:seed` contra Postgres real não evidenciado no âmbito da fase. |
| 19.1 | Cross-reference migrations ↔ seed | `runs/cap/005-real-file-creation/cap-base-docs-migrations-seed-crossref-report.md` | APROVADO | Apenas documentação. |
| 20 | Composition root (`createCapBaseModule`) | `runs/cap/005-real-file-creation/cap-base-composition-root-report.md` | APROVADO | Sem `PrismaClient` no factory. |
| 21 | Documentação consolidada | `runs/cap/005-real-file-creation/cap-base-documentation-consolidation-report.md`, `docs/10-cap-base-technical-summary.md` | APROVADO | — |
| 22 | Fechamento formal do MVP técnico (checklist, matriz, relatório) | `docs/11-cap-base-mvp-technical-closure.md`, `runs/cap/005-real-file-creation/cap-base-mvp-technical-closure-report.md`, `cap-base-mvp-final-checklist.md`, `cap-base-mvp-evidence-matrix.md` | APROVADO COM RESSALVAS | Ressalvas operacionais globais: integração real, seed real, migration inicial versionada. |

**Nota:** A fase **6** inclui também sincronização manifesto/schema quando aplicável: `runs/cap/005-real-file-creation/cap-base-schema-manifest-sync-report.md`.