# CAP — Padrões do Projeto

## Princípio SUSEP-first

Todo item deve ser classificado antes de entrar no backlog:

```text
Exigência SUSEP
Necessidade operacional
Necessidade de auditoria / governança
Necessidade de integração
Legado útil, mas não prioritário
Legado descartado
Pendente de confirmação regulatória
```

## Separação de responsabilidades

```text
squad-agentes → planejamento, orquestração e evidências
cap-platform  → código real do CAP
```

## Hierarquia de backlog

```text
Projeto → Módulo → Épico → Feature/Frente → História → Critérios de aceite → Tarefas → Evidências
```

## Regra do CAP-BASE

O `cap-base` deve conter apenas estruturas fundacionais.

Não deve conter:

- regra de sorteio;
- regra de promoção;
- regra de produto;
- regra de plano;
- cálculo financeiro;
- provisões;
- número da sorte;
- integração regulatória específica.

## Models obrigatórios em `base.prisma` (CAP-BASE)

A proposta de schema para `../cap-platform/repos/cap-base/prisma/base.prisma` deve declarar **exatamente** estes **23** models (sem extras nesta fase inicial):

| # | Model |
|---|--------|
| 1 | Organization |
| 2 | OrganizationType |
| 3 | OrganizationStatus |
| 4 | OrganizationRole |
| 5 | OrganizationRoleAssignment |
| 6 | User |
| 7 | UserStatus |
| 8 | Role |
| 9 | Permission |
| 10 | RolePermission |
| 11 | UserOrganization |
| 12 | Address |
| 13 | AddressType |
| 14 | Contact |
| 15 | ContactType |
| 16 | Document |
| 17 | DocumentType |
| 18 | SystemParameter |
| 19 | SystemParameterType |
| 20 | SystemParameterScope |
| 21 | AuditLog |
| 22 | AuditActionType |
| 23 | AuditEntityType |

Relacionamento entre `Role` e `Permission` deve passar pelo model de junção **RolePermission** — many-to-many implícito é proibido.

### Models e campos proibidos (lista curta)

Models não permitidos nesta tarefa incluem: `UserRole`, `OrganizationPermission`, `UserPermission`, `Product`, `Plan`, `Drawing`, `Promotion`, `FinancialEntry`, `LuckyNumber`.

Campos sensíveis genéricos como `password`, `passwordHash`, `refreshToken`, `resetToken` e campo genérico `token` não devem aparecer no schema proposto.

### Governança de evidência

- Texto gerado em `squad-agentes` **não** prova criação de arquivo em `cap-platform`.
- Antes de qualquer aceite forte, deve haver evidência de arquivo real e de validação Prisma executada no repositório alvo, além do relatório `validation-output.md` do orquestrador.
