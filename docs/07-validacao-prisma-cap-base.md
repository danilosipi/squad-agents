# Validação Prisma — CAP-BASE (FASE 8)

## Objetivo

Garantir **validação técnica real** do ficheiro `repos/cap-base/prisma/base.prisma` (23 models fundacionais preservados), com `prisma format` e `prisma validate` reprodutíveis, após o conflito observado com a **CLI Prisma 7** global.

## Versões detetadas

| Contexto | Versão |
| --- | --- |
| `npx prisma` na máquina (resolução típica para o cache global) | **7.8.0** |
| **Versão oficial definida para o pacote CAP-BASE** (`repos/cap-base/package.json`) | **6.19.3** |

## Problema encontrado

1. **Prisma 7.x:** o comando `npx prisma format --schema repos/cap-base/prisma/base.prisma` (e o `validate` equivalente) resolve para a CLI **7.x** e falha com **P1012**: a propriedade `url` no `datasource` deixa de ser aceite no ficheiro de schema sem o novo fluxo (`prisma.config.ts`, etc.).
2. **`prisma validate` (Prisma 5/6):** o passo de configuração exige **`DATABASE_URL`** definida (URL sintaticamente válida); não implica que o servidor PostgreSQL esteja acessível.

## Decisão técnica

1. **Fixar Prisma 6.19.3** em `repos/cap-base/package.json` como ferramenta de `format`/`validate` alinhada ao schema atual (`generator` + `datasource` com `url = env("DATABASE_URL")`).
2. **Não migrar** nesta fase para o modelo Prisma 7 (`prisma.config.ts` + cliente), para não desviar o escopo e manter o schema rastreável e estável.
3. **Scripts npm** em `repos/cap-base/`: `db:format` e `db:validate` (este último com `cross-env` a definir uma URL placeholder só para o WASM de configuração).
4. **Documentar** o uso de `DATABASE_URL` real via `repos/cap-base/.env.example` (cópia opcional para `.env` local, ignorada pelo Git quando aplicável).

## Comandos recomendados

> **Nota:** `npx prisma …` sem versão pode resolver para **Prisma 7** e falhar com **P1012** (`url` no `datasource`). Para o schema atual, use **Prisma 6.19.3** (pin explícito ou pacote em `repos/cap-base`).

Na raiz do `squad-agentes`:

```bash
npx prisma@6.19.3 format --schema repos/cap-base/prisma/base.prisma
```

ou (CLI do `node_modules` de `repos/cap-base`):

```bash
npx --prefix repos/cap-base prisma format --schema repos/cap-base/prisma/base.prisma
```

Validação (requer `DATABASE_URL` no ambiente ou `.env` carregado pela CLI):

```bash
npx prisma@6.19.3 validate --schema repos/cap-base/prisma/base.prisma
```

ou:

```bash
npx --prefix repos/cap-base prisma validate --schema repos/cap-base/prisma/base.prisma
```

Dentro de `repos/cap-base/`:

```bash
npm install
npm run db:format
npm run db:validate
```

Validação determinística dos 23 models:

```bash
.venv\Scripts\python.exe scripts\validate_cap_base_schema.py
```

## Resultado final

- **Format:** OK (Prisma 6.19.3).
- **Validate:** OK com `DATABASE_URL` definida (Prisma 6.19.3).
- **Script Python:** 23/23 models — **APROVADO**.

Evidência consolidada do run: `runs/cap/005-real-file-creation/prisma-validation-report.md`.

## Rastreabilidade do `base.prisma`

Comentários no topo do ficheiro referenciam a FASE 8 e o uso da CLI pinada em `repos/cap-base/package.json`, em alternativa ao `npx prisma` global v7.
