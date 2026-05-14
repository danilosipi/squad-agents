# CAP — Backlog Inicial

## Épico 1 — Estruturação do Módulo CAP-BASE

### Feature / Frente 1.1 — Base de Dados do Módulo CAP-BASE

História:

Como administrador da plataforma, quero ter a estrutura cadastral fundacional do CAP-BASE para permitir o cadastro de sociedades, empresas, usuários, permissões, documentos, contatos, endereços, parâmetros e auditoria cadastral.

Critérios de aceite:

- Deve existir schema Prisma fundacional do CAP-BASE.
- Deve conter as entidades obrigatórias do módulo base.
- Deve manter modelagem normalizada.
- Deve evitar campos textuais livres para tipos, status e categorias.
- Não deve conter regra de sorteio, promoção, produto, financeiro ou integração.
- Deve permitir validação determinística dos models obrigatórios.

Tarefas técnicas iniciais:

- Criar `../cap-platform/repos/cap-base/prisma/base.prisma`.
- Validar presença dos models obrigatórios.
- Registrar evidências em `runs/cap/001-cap-base-database/`.
- Consolidar resultado em `outputs/cap/001-cap-base-database.md`.

## Próximas frentes do CAP-BASE

- Domínio / entidades.
- Repositórios.
- Casos de uso.
- APIs / controllers.
- Testes.
- Documentação do módulo.
