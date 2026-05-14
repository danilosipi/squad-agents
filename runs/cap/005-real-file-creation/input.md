Execução assistida (FASE 6): materialização controlada via `files.manifest.json`.

Projeto: CAP
Run: 005-real-file-creation

Objetivo:
Validar o fluxo de escrita real assistida no repositório squad-agentes (whitelist, manifesto e relatório `file-write-report.md`), incluindo a criação de `repos/cap-base/prisma/base.prisma` quando `--write-real-files` estiver ativo.

Esta demanda pode ser executada junto com a squad completa; o processamento do manifesto ocorre antes da chamada à API e não altera o modo `--agent meta-orchestrator`.
