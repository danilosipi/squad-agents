<!-- project_slug=cap project_root=D:\Drive\Projetos\cap-platform -->

## `.squad/context.md`
_Arquivo: `.squad/context.md` — presente: True_

# Documentação Inicial — Plataforma SaaS de Capitalização

## 1. Objetivo do projeto

Construir uma plataforma SaaS modular para operação, controle e gestão de produtos de capitalização, com foco inicial em números da sorte, promoções comerciais, sorteios, planos, produtos e obrigações regulatórias.

A plataforma deve nascer modular desde o início, permitindo que no futuro cada módulo possa ser separado em repositórios próprios, com equipes diferentes trabalhando em paralelo, sem grandes impactos arquiteturais.

## 2. Premissa regulatória central

A estrutura de negócio parte da lógica:

```text
Nota Técnica / Processo SUSEP
→ Plano
→ Produto
→ Série
→ Título
→ Número da Sorte
→ Sorteio
→ Promoção, quando aplicável
```

A plataforma precisa respeitar que títulos de capitalização são estruturados conforme modalidades reguladas. Cada modalidade possui regras próprias, por isso o sistema será vendido e habilitado por modalidade.

## 3. Visão de negócio principal

A base do sistema será composta por módulos comuns e módulos específicos por modalidade.

### Módulos core

```text
cap-base
cap-plans-products
cap-promotions
cap-lucky-numbers
cap-drawings
cap-financial
cap-reports
cap-integrations
```

### Módulos de modalidade

```text
cap-modality-incentive
cap-modality-guarantee
cap-modality-traditional
cap-modality-popular
cap-modality-philanthropy
cap-modality-scheduled-purchase
```

A ideia central é que os módulos core executam as operações comuns da plataforma, enquanto os módulos de modalidade funcionam como pacotes de regras plugáveis.

## 4. Arquitetura C1 — Visão macro dos módulos

Nome sugerido:

```text
Arquitetura Modular C1 da Plataforma de Capitalização
```

Fluxo macro:

```text
Usuários / Canais
        ↓
Módulo Base
        ↓
Módulo de Planos e Produtos
        ↓
Motor de Regras das Modalidades
        ↓
Módulo de Promoções
        ↓
Módulo de Gestão de Números da Sorte
        ↓
Módulo de Sorteios
        ↓
Módulo Financeiro
        ↓
Módulo de Relatórios
        ↓
Módulo de Integrações
```

### Interpretação

- **Módulo Base**: cadastro raiz, empresas, usuários, permissões e parâmetros.
- **Planos e Produtos**: nota técnica, processo SUSEP, plano, produto, série e título.
- **Modalidades**: regras específicas por tipo de produto de capitalização.
- **Promoções**: campanhas, regulamentos, empresas promotoras e elegibilidade.
- **Números da Sorte**: geração, reserva, distribuição, vínculo com participante e rastreabilidade.
- **Sorteios**: agenda, apuração, importação de resultados, contemplados e auditoria.
- **Financeiro**: contribuições, quotas, provisões, resgates e liquidações.
- **Relatórios**: relatórios gerenciais, oficiais, DBFs e registros obrigatórios.
- **Integrações**: SUSEP, registradora, ERP, BI, pagamentos e sistemas externos.

## 5. Arquitetura C2 — Containers da plataforma

O C2 detalha os grandes blocos técnicos que sustentam os módulos do C1.

```text
Usuário
→ Frontend Web
→ API Backend
→ Serviços internos
→ Banco de Dados / Arquivos / Filas
→ Integrações externas
```

### Containers sugeridos

```text
1. Frontend Web
   Backoffice, telas operacionais, cadastros, consultas e relatórios.

2. API Backend
   Camada principal de regras, autenticação, permissões e orquestração dos módulos.

3. Serviço de Regras Regulatórias
   Valida regras SUSEP, modalidade, produto, plano, sorteio, promoção e restrições.

4. Serviço de Gestão de Números da Sorte
   Geração, reserva, distribuição, elegibilidade, cancelamento e rastreabilidade.

5. Serviço de Sorteios
   Configuração de sorteios, importação/apuração pela Loteria Federal, identificação de contemplados.

6. Serviço Financeiro/Contábil
   Provisões, resgates, liquidações, eventos financeiros e lançamentos contábeis.

7. Serviço de Relatórios e Obrigações
   DBFs, relatórios oficiais, relatórios gerenciais, trilhas regulatórias e arquivos obrigatórios.

8. Serviço de Integrações
   Registradora, SUSEP, ERP, BI, pagamentos e sistemas externos.

9. Banco de Dados Operacional
   Dados transacionais: cadastros, planos, produtos, séries, títulos, promoções, participantes e sorteios.

10. Armazenamento de Arquivos
   Notas técnicas, regulamentos, documentos, comprovantes, relatórios e arquivos oficiais.

11. Fila / Event Bus
   Comunicação assíncrona entre módulos.

12. Auditoria e Logs
   Rastreabilidade de alterações, eventos, usuários, integrações e decisões regulatórias.
```

## 6. Arquitetura C3 — Componentes do API Backend

O C3 detalha os componentes internos do container principal: o API Backend.

```text
API Backend
├── Camada de Autenticação e Permissão
│   ├── Login / sessão
│   ├── Perfis de acesso
│   └── Controle por operação
│
├── Módulo Base
│   ├── Sociedade de Capitalização
│   ├── Empresas / parceiros
│   ├── Usuários
│   ├── Parâmetros sistêmicos
│   └── Regras gerais da plataforma
│
├── Módulo de Planos e Produtos
│   ├── Nota técnica atuarial
│   ├── Processo SUSEP
│   ├── Plano de capitalização
│   ├── Produto comercial
│   ├── Série
│   └── Título
│
├── Motor de Regras das Modalidades
│   ├── Regras gerais
│   ├── Tradicional
│   ├── Instrumento de garantia
│   ├── Compra programada
│   ├── Popular
│   ├── Incentivo
│   └── Filantropia premiável
│
├── Módulo de Promoções
│   ├── Campanha
│   ├── Promoção comercial
│   ├── Empresa promotora
│   ├── Regulamento
│   ├── Participantes
│   └── Elegibilidade
│
├── Módulo de Gestão de Números da Sorte
│   ├── Geração
│   ├── Reserva
│   ├── Distribuição
│   ├── Vinculação ao participante
│   ├── Cancelamento / substituição
│   └── Rastreabilidade
│
├── Módulo de Sorteios
│   ├── Agenda de sorteios
│   ├── Tipo de sorteio
│   ├── Importação de resultado oficial
│   ├── Apuração
│   ├── Contemplados
│   └── Auditoria do sorteio
│
├── Módulo Financeiro
│   ├── Contribuições
│   ├── Quotas
│   ├── Provisões
│   ├── Resgates
│   ├── Liquidação de prêmios
│   └── Eventos contábeis
│
├── Módulo de Relatórios e Obrigações
│   ├── Relatórios gerenciais
│   ├── Relatórios oficiais
│   ├── Arquivos regulatórios
│   ├── DBFs
│   └── Registro de operações
│
├── Módulo de Integrações
│   ├── Registradora
│   ├── SUSEP
│   ├── ERP
│   ├── BI / Data Warehouse
│   └── Meios de pagamento
│
├── Event Bus Interno
│   ├── Título emitido
│   ├── Número da sorte gerado
│   ├── Número distribuído
│   ├── Sorteio apurado
│   ├── Contemplado identificado
│   ├── Resgate solicitado
│   └── Liquidação realizada
│
└── Auditoria e Logs
    ├── Alterações cadastrais
    ├── Decisões de regra
    ├── Eventos operacionais
    ├── Acessos
    └── Integrações
```

## 7. Estratégia de repositório

A decisão foi começar com um monorepo, mas estruturado como se já fossem múltiplos repositórios internos.

O objetivo é permitir evolução para multi-repo real no futuro.

Estrutura sugerida:

```text
cap-platform/
├── repos/
│   ├── cap-web/
│   ├── cap-api/
│   ├── cap-worker/
│   │
│   ├── cap-base/
│   ├── cap-plans-products/
│   ├── cap-promotions/
│   ├── cap-lucky-numbers/
│   ├── cap-drawings/
│   ├── cap-financial/
│   ├── cap-reports/
│   ├── cap-integrations/
│   │
│   ├── cap-modality-incentive/
│   ├── cap-modality-guarantee/
│   ├── cap-modality-traditional/
│   ├── cap-modality-popular/
│   ├── cap-modality-philanthropy/
│   └── cap-modality-scheduled-purchase/
│
├── packages/
│   ├── cap-shared/
│   ├── cap-contracts/
│   ├── cap-config/
│   └── cap-database/
│
├── infra/
├── docs/
└── tools/
```

## 8. Regras para não acoplar os repositórios internos

Cada pasta dentro de `repos/` deve nascer como se fosse um repositório independente.

### Cada repo interno deve ter

```text
package.json
README.md
src/
tests/
```

### Regra de importação

Errado:

```ts
import { Organization } from "../../../cap-base/src/domain/entities";
```

Certo:

```ts
import { Organization } from "@cap/base";
```

### Workspace

```yaml
packages:
  - "repos/*"
  - "packages/*"
```

### Nomes dos pacotes

```text
@cap/web
@cap/api
@cap/worker
@cap/base
@cap/plans-products
@cap/promotions
@cap/lucky-numbers
@cap/drawings
@cap/financial
@cap/reports
@cap/integrations
@cap/modality-incentive
@cap/modality-guarantee
@cap/modality-traditional
@cap/modality-popular
@cap/modality-philanthropy
@cap/modality-scheduled-purchase
@cap/shared
@cap/contracts
@cap/config
@cap/database
```

## 9. Dependências entre módulos

### Regra principal

O `cap-base` é a fundação. Ele pode ser consumido por todos, mas não deve depender de nenhum módulo de negócio.

```text
cap-base
  ← consumido por todos
  → não depende de planos, produtos, promoções, sorteios, financeiro ou integrações
```

### Fluxo lógico

```text
cap-base
↓
cap-plans-products
↓
cap-modality-*
↓
cap-promotions
↓
cap-lucky-numbers
↓
cap-drawings
↓
cap-financial
↓
cap-reports / cap-integrations
```

### Importante

Os módulos de modalidade não devem duplicar módulos operacionais.

Eles devem fornecer regras específicas para os módulos core.

Exemplo:

```text
cap-modality-incentive
- valida se a promoção é obrigatória
- valida empresa promotora
- valida cessão gratuita do direito de sorteio
- bloqueia cessão de resgate
- define regras específicas de sorteio oficial
- define campos obrigatórios do regulamento
```

O módulo `cap-promotions` continua cuidando de promoções. O módulo `cap-modality-incentive` apenas define as regras que promoções devem respeitar quando a modalidade ativa for incentivo.

## 10. Estratégia de SaaS por modalidade

A plataforma será vendida ou habilitada por modalidade.

Exemplo de combinação por cliente:

```text
Cliente A — Incentivo
- cap-base
- cap-plans-products
- cap-modality-incentive
- cap-promotions
- cap-lucky-numbers
- cap-drawings
- cap-reports

Cliente B — Filantropia Premiável
- cap-base
- cap-plans-products
- cap-modality-philanthropy
- cap-lucky-numbers
- cap-drawings
- cap-financial
- cap-reports

Cliente C — Instrumento de Garantia
- cap-base
- cap-plans-products
- cap-modality-guarantee
- cap-financial
- cap-reports
```

Esse desenho permite feature flags, licenciamento por módulo e separação futura por repositório.

## 11. Módulo Base — Arquitetura inicial

O Módulo Base será o primeiro módulo construído.

Objetivo:

```text
Ser o módulo raiz da plataforma, responsável por cadastros institucionais, usuários, permissões, parâmetros globais e estrutura organizacional.
```

Responsabilidades:

```text
- cadastrar sociedade de capitalização;
- cadastrar empresas/parceiros;
- cadastrar usuários e perfis;
- controlar permissões;
- manter parâmetros sistêmicos;
- manter tabelas de domínio;
- registrar auditoria básica de alterações;
- fornecer dados base para planos, produtos, promoções, sorteios, financeiro e integrações.
```

Estrutura funcional:

```text
cap-base
├── Cadastro Institucional
│   ├── Sociedade de Capitalização
│   ├── Empresas
│   ├── Endereços
│   ├── Contatos
│   └── Documentos
│
├── Controle de Acesso
│   ├── Usuários
│   ├── Perfis
│   ├── Permissões
│   └── Vínculo usuário x empresa
│
├── Parâmetros
│   ├── Parâmetros globais
│   ├── Parâmetros por sociedade
│   ├── Tipos de documento
│   ├── Status
│   └── Domínios regulatórios
│
└── Governança
    ├── Auditoria cadastral
    ├── Histórico de alterações
    └── Controle de documentos
```

## 12. Primeiro recorte do Módulo Base

Para MVP, começar por:

```text
1. Sociedade de Capitalização
2. Empresas / Parceiros
3. Usuários
4. Perfis e Permissões
5. Parâmetros Sistêmicos
```

Ordem sugerida:

```text
1. Cadastro Institucional
2. Controle de Acesso
3. Parâmetros
4. Governança / Auditoria
```

## 13. Modelagem conceitual inicial do Módulo Base

A modelagem deve evitar campos soltos e ser preparada para normalização.

Entidades conceituais iniciais:

```text
organizations
organization_types
organization_roles
organization_role_assignments
users
roles
permissions
user_organizations
addresses
contacts
documents
system_parameters
audit_logs
```

### Observação importante

Não misturar sociedade de capitalização, empresa promotora, distribuidor e prestador em uma única tabela sem papéis bem definidos.

A melhor abordagem inicial é:

```text
organizations
organization_roles
organization_role_assignments
```

Assim, uma mesma empresa pode assumir papéis diferentes em contextos distintos.

Exemplos de papéis:

```text
CAPITALIZATION_COMPANY
PROMOTER_COMPANY
DISTRIBUTOR
BROKER
SERVICE_PROVIDER
BENEFICENT_ENTITY
```

## 14. Estrutura interna de arquivos do cap-base

Dentro de `repos/cap-base`:

```text
repos/
└── cap-base/
    ├── package.json
    ├── README.md
    ├── src/
    │   ├── index.ts
    │   │
    │   ├── domain/
    │   │   ├── entities/
    │   │   │   ├── organization.entity.ts
    │   │   │   ├── organization-role.entity.ts
    │   │   │   ├── address.entity.ts
    │   │   │   ├── contact.entity.ts
    │   │   │   └── document.entity.ts
    │   │   │
    │   │   ├── value-objects/
    │   │   │   ├── cnpj.vo.ts
    │   │   │   ├── email.vo.ts
    │   │   │   └── phone.vo.ts
    │   │   │
    │   │   ├── repositories/
    │   │   │   ├── organizations.repository.ts
    │   │   │   ├── organization-roles.repository.ts
    │   │   │   └── documents.repository.ts
    │   │   │
    │   │   └── services/
    │   │       └── organization-domain.service.ts
    │   │
    │   ├── application/
    │   │   ├── use-cases/
    │   │   │   ├── create-organization.use-case.ts
    │   │   │   ├── update-organization.use-case.ts
    │   │   │   ├── get-organization.use-case.ts
    │   │   │   ├── list-organizations.use-case.ts
    │   │   │   ├── activate-organization.use-case.ts
    │   │   │   └── deactivate-organization.use-case.ts
    │   │   │
    │   │   ├── dto/
    │   │   │   ├── create-organization.dto.ts
    │   │   │   ├── update-organization.dto.ts
    │   │   │   ├── organization-response.dto.ts
    │   │   │   └── list-organizations-query.dto.ts
    │   │   │
    │   │   └── mappers/
    │   │       └── organization.mapper.ts
    │   │
    │   ├── infrastructure/
    │   │   ├── prisma/
    │   │   │   ├── prisma-organizations.repository.ts
    │   │   │   ├── prisma-organization-roles.repository.ts
    │   │   │   └── prisma-documents.repository.ts
    │   │   │
    │   │   └── storage/
    │   │       └── document-storage.service.ts
    │   │
    │   └── presentation/
    │       └── controllers/
    │           └── organizations.controller.ts
    │
    ├── prisma/
    │   └── base.prisma
    │
    └── tests/
```

## 15. Regra de arquitetura do cap-base

O `cap-base` deve conter somente cadastros e estruturas fundacionais.

Não deve conter:

```text
- regras de sorteio;
- regras de promoção;
- regras de produto;
- cálculo financeiro;
- provisões;
- geração de número da sorte;
- integrações regulatórias específicas.
```

Deve conter:

```text
- sociedades;
- empresas;
- papéis de empresas;
- usuários;
- permissões;
- endereços;
- contatos;
- documentos;
- parâmetros;
- auditoria cadastral.
```

## 16. Decisão arquitetural consolidada

A plataforma será construída como:

```text
Monorepo com estrutura multi-repo simulada
+ módulos core independentes
+ módulos plugáveis por modalidade
+ contratos compartilhados
+ event bus interno
+ separação futura planejada para múltiplos repositórios
```

Esse será o padrão-base do projeto daqui para frente.

## `.squad/roadmap.md`
_Arquivo: `.squad/roadmap.md` — presente: True_

# Roadmap

## `.squad/decisions.md`
_Arquivo: `.squad/decisions.md` — presente: True_

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

## `.squad/backlog.json`
_Arquivo: `.squad/backlog.json` — presente: True_

```json
[]
```

## `README.md`
_Arquivo: `README.md` — presente: False_

_Arquivo ausente ou não legível._
