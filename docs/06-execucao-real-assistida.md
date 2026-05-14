# FASE 6 — Execução real assistida (materialização controlada)

## Objetivo

Permitir que o **squad-agentes** materialize arquivos reais dentro do repositório de forma **assistida**, com **whitelist de caminhos**, **flag explícita** para gravação física e **evidência em Markdown** (`file-write-report.md`), sem escrita livre no filesystem.

## Modos: dry-run e `--write-real-files`

| Situação | Comportamento |
| --- | --- |
| **Sem** `--write-real-files` (padrão) | **Simulação**: nenhum arquivo do manifesto é gravado. O relatório indica o status que seria aplicado (criação, atualização, ignorado por conteúdo idêntico, bloqueado ou erro). |
| **Com** `--write-real-files` | **Gravação real** apenas para entradas permitidas pela whitelist. Após cada escrita bem-sucedida, o sistema verifica se o arquivo existe no disco e registra o resultado no relatório. |

O manifesto é processado **antes** da verificação da `OPENAI_API_KEY`, desde que não seja `--validate-existing` e não seja execução isolada com `--agent`. Assim, é possível gerar `file-write-report.md` em dry-run mesmo que a execução da squad pare depois por falta de chave de API.

## Whitelist de caminhos

Todos os caminhos do manifesto são resolvidos em relação à **raiz do repositório squad-agentes**. Só são aceitos destinos cuja resolução fique sob um destes prefixos:

- `repos/cap-base/`
- `runs/`
- `outputs/`

Qualquer outro caminho recebe status **BLOCKED** no relatório e **não** é gravado, mesmo com `--write-real-files`.

A lógica está em `scripts/file_writer.py` (normalização anti path-traversal e validação por segmentos de pasta).

## Formato do manifesto

Arquivo opcional no diretório do run: `files.manifest.json` (mesmo nível que `input.md`).

```json
{
  "files": [
    {
      "path": "repos/cap-base/prisma/base.prisma",
      "content": "conteúdo completo do arquivo"
    }
  ]
}
```

- `path`: relativo à raiz do squad-agentes (use barras normais `repos/...`).
- `content`: texto UTF-8 do arquivo (strings JSON com `\n` para quebras de linha).

## Relatório de evidência

Caminho fixo por run:

`runs/<projeto>/<run_id>/file-write-report.md`

Exemplo: `runs/cap/005-real-file-creation/file-write-report.md`.

O relatório inclui: `run_id`, projeto, modo (`dry-run` ou `write-real-files`), caminho do manifesto, tabela por arquivo (status, caminho final, verificação pós-escrita quando aplicável), texto sobre segurança e contagem por status (**CREATED**, **UPDATED**, **SKIPPED**, **BLOCKED**, **ERROR**).

## Exemplo de execução

Na raiz do repositório:

```bash
# Simulação: relatório gerado, nenhum arquivo do manifesto gravado
python scripts/run_squad.py cap runs/cap/005-real-file-creation/input.md

# Gravação real dos arquivos permitidos + mesmo relatório com modo write-real-files
python scripts/run_squad.py cap runs/cap/005-real-file-creation/input.md --write-real-files
```

Combinações **não** permitidas (o script encerra com erro):

- `--write-real-files` com `--validate-existing`
- `--write-real-files` com `--agent meta-orchestrator`

## Critérios de segurança

1. **Sem flag explícita**: nenhuma gravação física a partir do manifesto.
2. **Whitelist rígida**: apenas `repos/cap-base/`, `runs/`, `outputs/` sob a raiz do squad-agentes.
3. **Path traversal**: caminhos que resolvem fora da raiz são bloqueados.
4. **Rastreabilidade**: toda rodada com manifesto presente gera `file-write-report.md`.
5. **Comportamento existente**: `--write-files` do CAP (destino em `cap-platform/`), `--validate-existing` e `--agent meta-orchestrator` permanecem como antes; o manifesto **não** é processado na execução isolada do meta-orquestrador.

## Run de referência

- Manifesto de teste: `runs/cap/005-real-file-creation/files.manifest.json`
- Entrada: `runs/cap/005-real-file-creation/input.md`
