# Squad Agentes — Fonte Oficial do Projeto

## 1. Visão geral

O `squad-agentes` é um projeto criado para estruturar, executar e evoluir squads de agentes de IA especializadas em projetos de software, produto e negócio.

A proposta é permitir que o Danilo conduza projetos complexos com apoio de agentes, mantendo controle humano sobre decisões, prioridades, validações e aprovação final.

O projeto será executado via OpenAI API, com agentes definidos em arquivos Markdown, contexto versionado no repositório e saídas registradas em arquivos.

---

## 2. Objetivo final do projeto

O objetivo final do `squad-agentes` é se tornar uma plataforma/orquestrador de squads de agentes para qualquer tipo de projeto.

A visão futura é permitir que o Danilo converse com uma interface semelhante ao ChatGPT, informe o contexto de um projeto, e o sistema seja capaz de:

- entender o objetivo do projeto;
- analisar o contexto disponível;
- propor a squad ideal;
- criar os agentes necessários;
- definir o fluxo entre os agentes;
- criar roadmap e tarefas de trabalho;
- executar rodadas de trabalho;
- validar entregas de forma determinística;
- revisar tecnicamente os resultados;
- gerar evidências;
- registrar decisões;
- preparar arquivos reais do projeto.

Em outras palavras, o objetivo final não é criar apenas uma squad para CAP, MAZ, MAP ou qualquer outro projeto específico.

O objetivo final é criar uma base reutilizável para montar e operar squads especializadas conforme a necessidade de cada projeto.

---

## 3. Objetivo atual

Apesar da visão final ser mais ampla, o foco atual é validar o modelo usando o projeto CAP como primeiro caso real.

Neste momento, o `squad-agentes` está sendo usado para construir e testar uma squad especializada em:

- CAP;
- capitalização;
- SUSEP;
- arquitetura modular;
- modelagem de dados;
- validação técnica;
- QA com evidências.

O CAP é o laboratório inicial do projeto.

---

## 4. Papel do CAP dentro do Squad Agentes

O CAP não é o produto final do `squad-agentes`.

O CAP é o primeiro projeto piloto usado para validar o funcionamento da squad.

Portanto:

```text
squad-agentes
→ projeto-base/orquestrador de squads

squad CAP
→ primeira squad especializada

cap-base
→ primeira entrega técnica real da squad CAP
```

A squad CAP deve provar que o modelo funciona antes de qualquer expansão para interface, meta-agentes ou squads genéricas.

---

## 5. Regra de foco

Mesmo com o objetivo final mais ambicioso, o projeto não deve se dispersar agora.

A prioridade atual é:

```text
1. Consolidar a squad CAP
2. Sair da simulação
3. Criar arquivos reais do projeto CAP
4. Validar entregas com evidências
5. Registrar decisões
6. Melhorar o método de execução
```

A criação de interface conversacional, meta-agente criador de agentes e orquestração para qualquer projeto ficará para uma etapa posterior.

---

## 6. Problema que o projeto resolve

Atualmente existem múltiplos projetos importantes em andamento, como:

* MAZ;
* CAP;
* MAP;
* FARMACINHA.

O volume de decisões, requisitos, arquitetura, documentação, validação, testes e prompts técnicos ficou maior do que o tempo disponível para execução direta.

O `squad-agentes` existe para reduzir carga operacional, organizar o raciocínio, melhorar a qualidade das decisões e permitir que projetos avancem com mais método.

---

## 7. Papel do Danilo

O Danilo atua como responsável final por:

* definir prioridades;
* aprovar escopo;
* validar regra de negócio;
* revisar decisões críticas;
* testar fluxos principais;
* aprovar ou reprovar entregas;
* decidir o que entra ou não no projeto.

O Danilo não deve ser o executor operacional principal de todos os projetos.

O papel principal do Danilo no modelo é atuar como PO, QA final e decisor estratégico.

---

## 8. Papel dos agentes

Os agentes devem apoiar o trabalho em etapas específicas, como:

* organizar requisitos;
* decompor demandas;
* propor arquitetura;
* modelar dados;
* gerar artefatos técnicos;
* validar critérios objetivos;
* revisar entregas;
* gerar checklists de QA;
* registrar decisões;
* reduzir ambiguidade antes da execução.

Os agentes não têm autoridade para tomar decisões finais sem aprovação humana.

---

## 9. Squad CAP — fluxo atual

A squad CAP está sendo estruturada com o seguinte fluxo:

```text
Danilo
↓
PO
↓
Arquiteto
↓
Dev
↓
Validação determinística
↓
Reviewer
↓
QA
↓
Aprovação humana
```

Esse fluxo pode ser ajustado conforme o projeto evoluir, mas a regra principal é manter rastreabilidade entre:

* demanda;
* decisão;
* entrega;
* validação;
* evidência;
* aprovação.

---

## 10. Estado atual da squad CAP

Último estado conhecido:

```text
- Dev gerou o schema Prisma completo do cap-base.
- Validação determinística confirmou os 23 models obrigatórios.
- Resultado técnico: APROVÁVEL COM RESSALVAS.
- Reviewer aprovou para QA com ressalvas.
- QA solicitou evidências reais de execução.
- Próximo passo: sair da simulação e criar arquivos reais no projeto.
```

Primeiro arquivo real previsto:

```text
repos/cap-base/prisma/base.prisma
```

---

## 11. Primeira entrega real prevista

A primeira entrega técnica real da squad CAP será o schema Prisma do módulo `cap-base`.

O `cap-base` deve conter apenas estruturas fundacionais da plataforma CAP:

* sociedades de capitalização;
* empresas;
* papéis de empresas;
* usuários;
* permissões;
* vínculos;
* endereços;
* contatos;
* documentos;
* parâmetros;
* auditoria cadastral.

O `cap-base` não deve conter:

* regras de sorteio;
* regras de promoção;
* regras de produto;
* cálculo financeiro;
* provisões;
* geração de número da sorte;
* integrações regulatórias específicas.

---

## 12. Projeto CAP — visão resumida

O CAP será uma plataforma SaaS modular para operação, controle e gestão de produtos de capitalização, com foco inicial em:

* números da sorte;
* promoções comerciais;
* sorteios;
* planos;
* produtos;
* obrigações regulatórias;
* rastreabilidade;
* governança;
* modularização por modalidade.

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

A plataforma deve nascer modular desde o início, permitindo que no futuro cada módulo possa evoluir com independência.

---

## 13. Módulos previstos do CAP

Módulos core:

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

Módulos por modalidade:

```text
cap-modality-incentive
cap-modality-guarantee
cap-modality-traditional
cap-modality-popular
cap-modality-philanthropy
cap-modality-scheduled-purchase
```

O `cap-base` é a fundação.

Ele pode ser consumido por todos os demais módulos, mas não deve depender de módulos de negócio.

---

## 14. Estratégia técnica do CAP

A plataforma CAP será construída inicialmente como monorepo com estrutura de multi-repo simulada.

Estrutura conceitual:

```text
cap-platform/
├── repos/
│   ├── cap-web/
│   ├── cap-api/
│   ├── cap-worker/
│   ├── cap-base/
│   ├── cap-plans-products/
│   ├── cap-promotions/
│   ├── cap-lucky-numbers/
│   ├── cap-drawings/
│   ├── cap-financial/
│   ├── cap-reports/
│   ├── cap-integrations/
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

Cada pasta dentro de `repos/` deve nascer como se fosse um repositório independente.

Regra de importação:

```ts
// Errado
import { Organization } from "../../../cap-base/src/domain/entities";

// Certo
import { Organization } from "@cap/base";
```

---

## 15. Estrutura atual esperada do squad-agentes

Estrutura base do projeto:

```text
squad-agentes/
├── docs/
│   ├── 00-fonte-oficial.md
│   └── 01-organizacao-projetos-prioritarios.md
│
├── agents/
│   └── templates/
│       ├── po.md
│       ├── architect.md
│       ├── dev.md
│       ├── reviewer.md
│       └── qa.md
│
├── squads/
│   └── cap/
│       ├── workflow.md
│       ├── task-policy.md
│       └── agents/
│           ├── po.md
│           ├── architect.md
│           ├── dev-base.md
│           ├── reviewer.md
│           └── qa.md
│
├── projects/
│   └── cap/
│       ├── context.md
│       ├── backlog.md
│       ├── decisions.md
│       └── standards.md
│
├── outputs/
│   └── cap/
│
├── runs/
│   └── cap/
│
├── scripts/
│   └── run_squad.py
│
├── README.md
├── .env.example
├── .gitignore
└── requirements.txt
```

Essa estrutura pode evoluir, mas não deve ser expandida antes de necessidade real.

---

## 16. Stack inicial do squad-agentes

A stack inicial será simples:

```text
Python
OpenAI API
Arquivos Markdown
Execução via terminal
Estrutura local versionada no Git
```

Frameworks como Agno ou CrewAI podem ser avaliados posteriormente, mas não devem ser adotados antes de a execução simples funcionar.

---

## 17. Regra sobre Cursor

A squad roda via OpenAI API, não via Cursor.

O Cursor pode ser usado posteriormente como executor de código quando for necessário aplicar prompts em projetos reais.

Mas o raciocínio, a criação dos agentes, a orquestração, os testes, as validações e os registros pertencem ao `squad-agentes`.

---

## 18. Regras de execução

Toda rodada da squad deve produzir saída rastreável.

Cada execução deve registrar:

* demanda original;
* contexto usado;
* agente responsável;
* resposta do agente;
* arquivos propostos;
* validações executadas;
* evidências;
* ressalvas;
* decisão final.

Nenhuma entrega deve ser considerada concluída apenas porque um agente afirmou que está correta.

Sempre que possível, deve haver validação objetiva.

---

## 19. Regras de aprovação

Os status possíveis são:

```text
APROVADO
APROVÁVEL COM RESSALVAS
REPROVADO
AGUARDANDO EVIDÊNCIAS
```

Definições:

```text
APROVADO
Entrega validada sem pendências relevantes.

APROVÁVEL COM RESSALVAS
Entrega tecnicamente aceitável, mas com pontos menores a revisar.

REPROVADO
Entrega não atende critérios mínimos.

AGUARDANDO EVIDÊNCIAS
Entrega ainda não possui comprovação objetiva suficiente.
```

---

## 20. Regras principais do projeto

1. O `squad-agentes` deve começar simples.
2. Não criar automação pesada no início.
3. Não criar frontend agora.
4. Não criar banco de dados agora para o squad-agentes.
5. Não permitir execução autônoma sem aprovação humana.
6. Toda saída relevante deve ser salva em Markdown.
7. Toda decisão importante deve ser registrada.
8. O Danilo sempre aprova a decisão final.
9. O foco atual é validar a squad CAP.
10. O objetivo futuro deve ser preservado, mas sem dispersar o presente.

---

## 21. Princípio central

O `squad-agentes` existe para permitir que o Danilo trabalhe melhor com pouco tempo disponível.

A função da squad é preparar, organizar, revisar e validar o trabalho.

A decisão final continua humana.

O CAP é o primeiro teste real.

A visão final é transformar esse método em uma plataforma capaz de criar e operar squads para qualquer projeto.

