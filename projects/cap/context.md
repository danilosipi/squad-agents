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

