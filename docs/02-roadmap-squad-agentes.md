# Roadmap Oficial — Squad Agentes

## 1. Objetivo deste roadmap

Este documento define o caminho de evolução do `squad-agentes` para evitar dispersão entre código local, agentes, CAP, interface web, GitHub, deploy, Agno e plataforma final.

A regra principal é simples:

```text
Primeiro tornar o squad-agentes utilizável e confiável como ferramenta local.
Depois integrar GitHub.
Depois evoluir para interface web.
Depois avaliar frameworks externos.
Depois transformar em plataforma.
```

---

## 2. Estado atual real

O `squad-agentes` já possui uma base funcional em partes:

- agentes em Markdown;
- squad CAP estruturada;
- contexto versionado;
- `run_squad.py` como orquestrador principal;
- `prepare_run.py` para criação de runs pelo meta-orquestrador;
- `chat_squad.py` como interface conversacional local via terminal;
- `file_writer.py` para escrita assistida com whitelist;
- runs e outputs em arquivos;
- GitHub conectado para versionamento do próprio `squad-agentes`.

Mas ainda não é uma plataforma web estilo ChatGPT.

Hoje o fluxo mais comum ainda é:

```text
Danilo
↓
ChatGPT / Cursor
↓
Prompts manuais
↓
Arquivos alterados localmente
↓
Resumo colado de volta
```

O objetivo das próximas fases é reduzir esse uso manual até chegar em:

```text
Danilo conversa em uma interface web
↓
Projeto selecionado
↓
Chat salvo no projeto
↓
Meta-orquestrador entende a demanda
↓
Squad correta executa
↓
Arquivos/evidências são gerados
↓
Danilo aprova
↓
GitHub recebe branch/PR quando aplicável
```

---

## 3. Princípios obrigatórios

1. O Danilo sempre aprova decisões relevantes.
2. O sistema nunca deve fazer merge automático no início.
3. O sistema deve sempre gerar evidência rastreável.
4. Toda execução precisa estar associada a um projeto.
5. Todo projeto deve ter contexto, decisões, runs, outputs e chats separados.
6. O motor atual em Python não deve ser descartado antes de haver substituto validado.
7. Agno, CrewAI ou OpenClaw só devem ser avaliados depois do fluxo próprio funcionar.
8. Interface web não deve alterar arquivos livremente sem aprovação/whitelist.
9. Produção, deploy e banco real exigem aprovação explícita.
10. Primeiro funcionar simples; depois sofisticar.

---

## 4. Roadmap consolidado

### FASE 0 — Fundação do projeto

**Status:** concluída.

Objetivo:
Criar a estrutura inicial do `squad-agentes`.

Entregas esperadas:

- estrutura de pastas;
- documentação inicial;
- contexto do CAP;
- primeira squad;
- agentes em Markdown;
- scripts básicos.

Critério de conclusão:
O projeto existe, tem fonte oficial e pode ser versionado.

---

### FASE 1 — Squad CAP confiável

**Status:** concluída em nível inicial.

Objetivo:
Criar uma squad CAP com papéis mínimos confiáveis.

Fluxo base:

```text
Danilo
↓
PO
↓
Architect
↓
Dev
↓
Reviewer
↓
QA
↓
Aprovação humana
```

Critério de conclusão:
A squad possui papéis claros, responsabilidades separadas e validação por evidência.

---

### FASE 2 — Primeira entrega real no CAP

**Status:** concluída localmente para o `cap-base`, com ressalvas operacionais.

Objetivo:
Produzir uma entrega técnica real do CAP usando o método da squad.

Resultado alcançado:

- MVP técnico do `@cap/base` criado localmente;
- schema Prisma;
- domínio;
- application;
- repositories Prisma-like;
- composition root;
- seed preparado;
- documentação;
- testes unitários;
- evidências.

Ressalvas:

- teste integrado real com PostgreSQL ainda pendente;
- seed real contra PostgreSQL ainda pendente;
- migration inicial real ainda não versionada.

Critério de conclusão final:
Executar validações reais com PostgreSQL quando Docker/banco estiver disponível.

---

### FASE 3 — Repetibilidade do método

**Status:** parcialmente concluída.

Objetivo:
Provar que o método pode ser repetido em múltiplas entregas.

O que já aconteceu:

- várias fases sequenciais foram conduzidas com prompts e validações;
- relatórios foram gerados;
- o método se mostrou organizado.

O que ainda falta:

- executar o ciclo diretamente pelo `squad-agentes`, sem depender tanto de prompt manual no Cursor;
- reduzir a distância entre conversa, run, execução e evidência.

Critério de conclusão:
Rodar pelo menos uma demanda pequena ponta a ponta pelo próprio `squad-agentes`.

---

### FASE 4 — Agente principal / Meta-orquestrador

**Status:** concluída em nível inicial.

Objetivo:
Criar o agente que recebe a demanda bruta, classifica, escolhe fluxo e prepara plano.

O que existe:

- `agents/meta-orchestrator.md`;
- modo Markdown;
- modo JSON para `prepare_run`;
- integração com `prepare_run.py` e `chat_squad.py`.

Limite atual:
O meta-orquestrador ainda planeja; ele não deve executar especialistas diretamente sozinho.

Critério de conclusão:
Meta-orquestrador gera plano ou preparação de run de forma consistente.

---

### FASE 5 — Interface conversacional local

**Status:** parcial.

Objetivo:
Permitir que Danilo converse com o sistema de forma parecida com ChatGPT, inicialmente local.

O que existe:

- `scripts/chat_squad.py` no terminal;
- criação de runs a partir de mensagens;
- modo Markdown;
- modo `json_prepare_run`.

Limite atual:
Ainda não existe interface web. O chat local ainda não executa a squad completa com aprovação dentro da conversa.

Subfases necessárias:

#### FASE 5.1 — Auditoria do estado atual do squad-agentes

Objetivo:
Confirmar o que funciona de fato no código atual.

Entregas:

- diagnóstico dos scripts;
- lacunas identificadas;
- decisão sobre o próximo ajuste.

#### FASE 5.2 — Web Chat MVP local

Objetivo:
Criar interface web estilo ChatGPT, local, sem banco e sem login.

Escopo mínimo:

- sidebar de projetos;
- lista de chats por projeto;
- tela de conversa;
- envio de mensagem;
- persistência local em arquivos;
- chamada ao meta-orquestrador;
- exibição da resposta no chat.

Critério de conclusão:
Danilo consegue abrir o navegador, escolher projeto e conversar com o meta-orquestrador.

#### FASE 5.3 — Execução da squad completa pelo chat

Objetivo:
Após plano do meta-orquestrador, permitir aprovação humana e execução da squad.

Fluxo esperado:

```text
Mensagem do Danilo
↓
Meta-orquestrador gera plano
↓
Danilo aprova execução
↓
PO → Architect → Dev → Reviewer → QA
↓
final.md gerado
↓
Resumo volta para o chat
```

Critério de conclusão:
Uma demanda pequena roda ponta a ponta via web chat.

#### FASE 5.4 — Visualização de runs, outputs e evidências

Objetivo:
Exibir no navegador:

- runs do projeto;
- status;
- arquivos gerados;
- final.md;
- relatórios;
- evidências.

Critério de conclusão:
Danilo consegue auditar uma execução sem abrir pastas manualmente.

---

### FASE 6 — Execução real assistida / criação de arquivos reais

**Status:** parcial.

Objetivo:
Permitir que o sistema crie ou altere arquivos reais com segurança.

O que existe:

- `file_writer.py`;
- `files.manifest.json`;
- whitelist;
- dry-run;
- `--write-real-files`;
- relatório de escrita.

Limites atuais:

- fluxo ainda não está totalmente integrado à experiência web;
- aprovação humana ainda precisa ficar mais explícita;
- escopo de escrita ainda é restrito.

Critério de conclusão:
Pelo chat web, o sistema propõe arquivos, Danilo aprova, a escrita ocorre e a evidência aparece no histórico.

---

### FASE 7 — Integração com GitHub

**Status:** não iniciada funcionalmente.

Objetivo:
Permitir que o `squad-agentes` trabalhe com repositórios reais via GitHub.

Entregas:

- listar repositórios conectados;
- ler arquivos;
- criar branch;
- criar/alterar arquivos em branch;
- abrir pull request;
- registrar evidência;
- impedir merge automático.

Regra crítica:
O agente pode preparar PR, mas merge exige aprovação humana.

Critério de conclusão:
A partir de uma execução aprovada, o sistema abre um PR no GitHub com os arquivos propostos.

---

### FASE 8 — Deploy controlado

**Status:** não iniciada.

Objetivo:
Permitir que o sistema acompanhe ou acione deploy com governança.

Entregas:

- integração com pipeline;
- validações pré-deploy;
- aprovação explícita;
- logs;
- rollback documentado;
- notificação de sucesso/falha.

Regra crítica:
Produção exige aprovação humana.

Critério de conclusão:
Um deploy de ambiente seguro/homologação pode ser disparado com aprovação e evidência.

---

### FASE 9 — Avaliação de frameworks externos

**Status:** não iniciada.

Objetivo:
Avaliar se Agno, CrewAI, OpenClaw ou outro framework ajudam ou complicam.

Ordem recomendada:
Avaliar somente depois que o fluxo próprio mínimo funcionar.

Critérios de avaliação:

- reduz código?
- melhora observabilidade?
- melhora memória/contexto?
- facilita ferramentas externas?
- mantém controle humano?
- mantém validação determinística?
- melhora segurança?
- reduz ou aumenta complexidade operacional?

Decisão possível:

```text
Adotar parcialmente
Não adotar
Adiar
Usar apenas como runtime auxiliar
```

Critério de conclusão:
POC pequena comparada com o motor atual.

---

### FASE 10 — Plataforma de squads

**Status:** visão futura.

Objetivo:
Transformar `squad-agentes` em uma plataforma reutilizável para múltiplos projetos.

Capacidades finais desejadas:

- projetos separados;
- chats por projeto;
- contexto por projeto;
- squads por projeto;
- criação de agentes;
- execução de runs;
- GitHub integrado;
- PRs;
- deploy controlado;
- memória/auditoria;
- dashboards;
- permissões;
- histórico completo.

Critério de conclusão:
O CAP deixa de ser laboratório e o `squad-agentes` passa a operar qualquer projeto com método confiável.

---

## 5. Ordem recomendada a partir de agora

A ordem correta, considerando o estado atual, é:

```text
1. FASE 5.1 — Auditoria do estado atual
2. FASE 5.2 — Web Chat MVP local
3. FASE 5.3 — Executar squad completa pelo chat
4. FASE 5.4 — Visualizar runs/evidências no navegador
5. FASE 6 — Integrar escrita real assistida ao chat
6. FASE 7 — GitHub: branch + PR
7. FASE 8 — Deploy controlado
8. FASE 9 — Avaliar Agno/CrewAI/OpenClaw
9. FASE 10 — Plataforma de squads
```

---

## 6. Decisão atual

A prioridade imediata não é avançar em novo módulo CAP.

A prioridade imediata é fazer o `squad-agentes` virar uma ferramenta local utilizável pelo Danilo em fluxo conversacional.

Próxima fase recomendada:

```text
FASE 5.1 — Auditoria do estado atual do squad-agentes
```

Depois:

```text
FASE 5.2 — Web Chat MVP local
```

---

## 7. Critério de sucesso do próximo marco

O próximo marco será considerado bem-sucedido quando o Danilo conseguir:

```text
1. Abrir uma interface web local.
2. Selecionar um projeto.
3. Criar ou abrir um chat do projeto.
4. Enviar uma demanda.
5. Receber resposta do meta-orquestrador.
6. Aprovar ou não a execução da squad.
7. Ver o run e as evidências no navegador.
```

Esse é o ponto em que o `squad-agentes` começa a se aproximar da experiência ChatGPT, mas com projetos, agentes e evidências próprias.
