# Squad CAP — Workflow Oficial

## Fluxo principal

```text
Danilo
↓
PO
↓
Arquiteto
↓
Dev Base
↓
Validação determinística (orquestrador)
↓
Reviewer
↓
QA
↓
Aprovação humana
```

## Regra de conversa

O Danilo conversa prioritariamente com o PO. O PO transforma conversa em backlog estruturado.

## Regra de saída

Cada rodada deve gerar uma pasta em `runs/cap/<run-id>/` com:

```text
input.md
po-output.md
architect-output.md
dev-base-output.md
validation-output.md
reviewer-output.md
qa-output.md
final.md
```

Cópias com carimbo de tempo ficam em `outputs/cap/` para auditoria.

## Validação determinística

Entre o Dev Base e o Reviewer, o orquestrador executa checagens determinísticas sobre a saída do Dev (models obrigatórios, proibições, placeholders, tokens, many-to-many implícito, caminho canônico e evidência física). O resultado é gravado em `validation-output.md` e deve ser tratado como fonte objetiva pelo Reviewer e pelo QA.

## Regra de código

Código real do CAP não deve ser salvo dentro de `squad-agentes`.

Código real deve ir para:

```text
../cap-platform/repos/<modulo>/
```

Nesta fase de calibragem, o orquestrador **não** cria nem altera arquivos em `cap-platform`; evidência física de `base.prisma` só existirá após execução humana ou pipeline dedicado no repositório alvo.
