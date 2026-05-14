# Squad Agentes

Projeto interno para criação, orquestração e execução assistida de squads de agentes via OpenAI API.

## Objetivo atual

Validar o modelo usando a squad CAP como primeiro caso real.

## Objetivo final

Evoluir para uma plataforma/orquestrador capaz de criar e operar squads especializadas para qualquer projeto.

## Regra de separação

```text
squad-agentes
→ agentes, contexto, backlog, decisões, runs, outputs, validações e evidências.

cap-platform
→ código real do produto CAP.
```

## Fluxo atual da squad CAP

```text
Danilo → PO → Arquiteto → Dev → Validação determinística → Reviewer → QA → Aprovação humana
```

## Próximo artefato real previsto

```text
../cap-platform/repos/cap-base/prisma/base.prisma
```

## Pastas principais

```text
docs/                 Fonte oficial e decisões de alto nível
agents/templates/     Templates genéricos de agentes
squads/cap/agents/    Agentes especializados da squad CAP: po.md, architect.md, dev-base.md, reviewer.md, qa.md
projects/cap/         Contexto, backlog, decisões e padrões do CAP
runs/cap/             Histórico detalhado de execuções
outputs/cap/          Saídas consolidadas
scripts/              Orquestrador e utilitários
```


# ROADMAP - AGENTS SQUADS

```text
FASE 0 — Fundação do projeto
Status: em andamento / quase concluída

Objetivo:
Criar a estrutura mínima para rodar squads via OpenAI API.

Entregas:
- Estrutura de pastas do squad-agentes.
- Fonte oficial do projeto.
- Squad CAP criada.
- Agentes PO, Arquiteto, Dev, Reviewer e QA.
- Orquestrador inicial em Python.
- Primeira execução real.
- Validação determinística entrando no fluxo.

Critério de conclusão:
A squad roda ponta a ponta e reprova corretamente quando a entrega não atende os critérios.
```

```text
FASE 1 — Squad CAP confiável
Status: agora

Objetivo:
Fazer a squad CAP gerar entregas técnicas sem aprovação falsa.

Entregas:
- Validação determinística após Dev.
- Reviewer respeitando validação objetiva.
- QA sem aprovar sem evidência.
- final.md com status consolidado real.
- Correção dos agentes CAP.
- Nova execução da task Base de Dados do CAP-BASE.

Critério de conclusão:
Se o Dev errar, a squad reprova.
Se o Dev acertar, a squad marca no máximo “aprovável com ressalvas” até existir arquivo real e validação executada.
```

```text
FASE 2 — Primeira entrega real no cap-platform

Objetivo:
Sair da proposta textual e criar o primeiro arquivo real do CAP.

Entrega principal:
cap-platform/repos/cap-base/prisma/base.prisma

Entregas complementares:
- Criar arquivo físico.
- Rodar prisma validate.
- Registrar evidências no run.
- Atualizar final.md com evidência real.
- QA aprovar ou reprovar com base em arquivo real.

Critério de conclusão:
base.prisma existe, contém os 23 models obrigatórios e passa na validação.
```

```text
FASE 3 — Repetibilidade do método

Objetivo:
Provar que o método funciona mais de uma vez.

Próximas frentes possíveis:
- Domínio / entidades do CAP-BASE.
- Repositórios do CAP-BASE.
- Casos de uso fundacionais.
- README técnico do módulo.
- Seeds/tabelas de domínio.
- Testes estruturais.

Critério de conclusão:
A squad consegue repetir o ciclo:
demanda → história → arquitetura → dev → validação → reviewer → QA → evidência.
```

```text
FASE 4 — Agente principal / Meta-orquestrador

Objetivo:
Criar o agente com quem você conversa diretamente.

Esse agente deverá:
- entender sua demanda;
- identificar o projeto;
- escolher a squad correta;
- criar história;
- abrir run;
- acompanhar execução;
- resumir resultado;
- pedir aprovação humana.

Aqui começa a aproximar do modelo:
“Danilo conversa com um agente, e ele aciona a squad certa”.
```

```text
FASE 5 — Interface conversacional

Objetivo:
Sair do terminal.

Ordem sugerida:
1. Chat local simples.
2. Interface web simples.
3. WhatsApp.

No WhatsApp, o agente principal deverá:
- receber demandas;
- perguntar contexto faltante;
- criar tarefas;
- acionar squads;
- devolver status;
- pedir aprovação.

Critério de conclusão:
Você consegue iniciar uma task da squad pelo WhatsApp.
```

```text
FASE 6 — Integração com GitHub

Objetivo:
Permitir que o agente trabalhe com repositórios reais.

Entregas:
- Conectar GitHub API.
- Criar repositório.
- Criar branch.
- Criar arquivos.
- Fazer commit.
- Abrir pull request.
- Registrar evidências.

Regra crítica:
Merge nunca deve ser automático no início.
O agente prepara, você aprova.
```

```text
FASE 7 — Deploy controlado

Objetivo:
Permitir que o agente acione deploy com governança.

Entregas:
- Integração com pipeline.
- Validação antes do deploy.
- Aprovação explícita.
- Registro de logs.
- Plano de rollback.
- Notificação de sucesso/falha.

Regra:
Produção exige aprovação humana.
```

```text
FASE 8 — Avaliação do Agno

Objetivo:
Ver se Agno acelera ou complica.

Quando avaliar:
Depois de termos pelo menos:
- squad CAP funcionando;
- geração de arquivo real;
- 2 ou 3 runs bem-sucedidos;
- padrão claro de validação;
- começo do agente principal.

POC com Agno:
Recriar um fluxo pequeno:
PO → Arquiteto → Dev → Reviewer → QA

Comparar:
- ficou mais simples?
- reduziu código?
- melhorou memória?
- melhorou observabilidade?
- facilitou interface?
- preservou validação determinística?
- facilitou tools externas?

Decisão:
Se Agno acelerar sem tirar controle, usamos.
Se criar abstração demais, seguimos com motor próprio.
```

```text
FASE 9 — Plataforma de squads

Objetivo final:
Transformar o squad-agentes em uma plataforma reutilizável.

Capacidades:
- criar squads por projeto;
- criar agentes novos;
- gerenciar contexto;
- conversar via WhatsApp/web;
- integrar GitHub;
- gerar código;
- abrir PR;
- acionar deploy;
- registrar decisões;
- manter memória;
- auditar execuções.

Neste ponto, CAP deixa de ser laboratório e o squad-agentes vira produto operacional.
```

Minha recomendação de foco imediato:

```text
Agora:
FASE 1

Depois:
FASE 2

Só depois:
pensar em Agno, WhatsApp, GitHub e deploy.
```

O roadmap resumido:

```text
1. Squad CAP confiável
2. Arquivo real no cap-platform
3. Repetir o método
4. Criar agente principal
5. Criar interface
6. Integrar GitHub
7. Controlar deploy
8. Avaliar Agno
9. Transformar em plataforma
```
