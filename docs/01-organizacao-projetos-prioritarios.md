Sim. Crie este arquivo:

```text id="ri0huw"
squad-agentes/docs/00-fonte-oficial.md
```

Se a pasta `docs` ainda não existir:

```powershell id="91zjkx"
New-Item -ItemType Directory -Force -Path squad-agentes\docs
New-Item -ItemType File -Force -Path squad-agentes\docs\00-fonte-oficial.md
```

Conteúdo para colar no arquivo:

```markdown id="03qapm"
# Squad Agentes — Fonte Oficial do Projeto

## Objetivo

O `squad-agentes` é um projeto interno criado para apoiar a gestão e execução assistida de projetos de software usando agentes de IA.

O objetivo principal é permitir que o Danilo atue como PO/QA, enquanto os agentes auxiliam na organização, análise, decomposição de tarefas, arquitetura, preparação de prompts técnicos e validação das entregas.

Este projeto não nasce para substituir o desenvolvedor, nem para executar código automaticamente de forma autônoma. Ele nasce para reduzir carga operacional, acelerar decisões e preparar tarefas mais claras para execução assistida.

---

## Problema que o projeto resolve

Atualmente existem múltiplos projetos em andamento:

- MAZ
- CAP
- MAP
- FARMACINHA

O volume de decisões, organização, backlog, requisitos, prompts para Cursor, validação e documentação ficou maior do que o tempo disponível diariamente.

O Danilo possui cerca de 2 horas por dia para atuar. Por isso, o modelo de trabalho precisa mudar de execução direta para gestão assistida.

---

## Estratégia inicial

A estratégia será paralelizar principalmente:

- **MAZ**: continua sob foco direto do Danilo para finalização, testes, ajustes críticos e preparação comercial.
- **CAP**: será conduzido com apoio da squad de agentes, com o Danilo atuando como PO/QA.

MAP e FARMACINHA ficam fora da frente ativa neste primeiro momento, salvo decisão explícita posterior.

---

## Papel do Danilo

O Danilo será o responsável por:

- definir prioridade;
- aprovar escopo;
- validar regra de negócio;
- revisar entregas;
- testar fluxos principais;
- decidir o que entra ou não no produto;
- atuar como PO e QA final.

O Danilo não deve ser o executor principal do CAP.

---

## Papel dos agentes

Os agentes serão responsáveis por apoiar o trabalho em etapas específicas:

- organizar requisitos;
- quebrar demandas em histórias;
- sugerir arquitetura;
- preparar prompts para implementação;
- gerar checklists de QA;
- registrar decisões;
- reduzir ambiguidade antes da execução.

Os agentes não devem tomar decisões finais de produto sem aprovação humana.

---

## Agentes iniciais

A primeira versão da squad terá apenas 3 agentes:

### PO

Responsável por transformar demandas brutas em requisitos, épicos, histórias e critérios de aceite.

### Arquiteto

Responsável por validar impacto técnico, modularização, padrões, boundaries, integrações e riscos arquiteturais.

### QA

Responsável por transformar entregas em cenários de teste, checklist de validação e critérios objetivos de aprovação.

---

## Agentes futuros

Após o MVP funcionar, poderão ser adicionados:

- Backend
- Frontend
- DevOps
- Documentador
- Segurança
- Produto/Marketing

Nenhum agente novo deve ser criado antes de haver necessidade real.

---

## Como os agentes serão criados

Os agentes serão definidos inicialmente como arquivos Markdown em:

```text
agents/
```

Cada agente terá:

- papel;
- responsabilidades;
- limites;
- entradas esperadas;
- saídas esperadas;
- regras obrigatórias;
- formato de resposta.

Posteriormente, esses agentes serão executados por um orquestrador simples usando a API da OpenAI.

---

## Como os agentes irão “conversar”

Os agentes não conversarão livremente entre si no início.

O fluxo será orquestrado em sequência:

```text id="ylhf6m"
Demanda do Danilo
↓
Agente PO
↓
Agente Arquiteto
↓
Agente QA
↓
Saída final em Markdown
```

O orquestrador será responsável por:

- carregar o contexto do projeto;
- carregar o prompt do agente;
- enviar a tarefa para a OpenAI;
- pegar a resposta de um agente;
- passar como contexto para o próximo;
- salvar os resultados em arquivos.

---

## Estrutura inicial do projeto

```text id="ajdn3x"
squad-agentes/
├── agents/
│   ├── po.md
│   ├── architect.md
│   └── qa.md
│
├── docs/
│   └── 00-fonte-oficial.md
│
├── (memória por projeto: <repo-do-cliente>/.squad/ — fora do squad-agentes)
│
├── outputs/
│   └── cap/
│
├── runs/
│
├── scripts/
│   └── run_squad.py
│
├── README.md
├── .env.example
└── requirements.txt
```

---

## Projeto inicial

O primeiro projeto atendido pela squad será o CAP.

O CAP será usado como caso real para validar o funcionamento dos agentes.

A squad deve ajudar a estruturar:

- visão da POC;
- escopo inicial;
- módulos principais;
- backlog;
- decisões arquiteturais;
- checklist de QA;
- prompts para execução no Cursor.

---

## Regras do projeto

1. O `squad-agentes` deve ser simples.
2. Não criar automação pesada no início.
3. Não criar frontend agora.
4. Não criar banco de dados agora.
5. Não permitir que agentes alterem código automaticamente.
6. Toda saída deve ser salva em Markdown.
7. Toda decisão importante deve ser registrada.
8. O Danilo sempre aprova a decisão final.
9. O objetivo é reduzir tempo, não criar mais complexidade.
10. Primeiro funcionar simples, depois evoluir.

---

## Stack inicial

A stack inicial será:

- Python
- OpenAI API
- Arquivos Markdown
- Execução via terminal
- Estrutura local versionada no Git

Frameworks como Agno ou CrewAI poderão ser avaliados, mas a primeira decisão ainda será validada antes da implementação.

---

## MVP inicial

O MVP do `squad-agentes` deve fazer apenas isto:

```text id="rrovmv"
Receber uma demanda
Ler o contexto do projeto
Executar PO
Executar Arquiteto
Executar QA
Salvar a saída final em Markdown
```

Nada além disso entra na primeira versão.

---

## Resultado esperado

Ao final de uma execução, o sistema deve gerar uma saída clara contendo:

- requisito refinado;
- análise técnica;
- riscos;
- critérios de aceite;
- checklist de QA;
- prompt final para Cursor, quando aplicável.

---

## Princípio central

O `squad-agentes` existe para permitir que o Danilo trabalhe melhor com pouco tempo disponível.

A função da squad é preparar, organizar e validar o trabalho.

A decisão final continua humana.
```

Depois de salvar esse arquivo, o próximo passo é preencher o `README.md` com uma versão mais curta desse documento.