# Squad CAP — Política de Quebra de Tarefas

## Hierarquia oficial

```text
Projeto
→ Módulo
→ Épico
→ Feature / Frente
→ História
→ Critérios de aceite
→ Tarefas funcionais
→ Tarefas técnicas
→ Evidências
```

## Exemplo inicial

```text
Projeto: CAP
Módulo: CAP-BASE
Épico: Estruturação do Módulo CAP-BASE
Feature / Frente: Base de Dados do Módulo CAP-BASE
História: Criar a base cadastral fundacional do CAP-BASE
```

## Responsabilidades

### PO

Cria histórias, critérios de aceite e tarefas funcionais.

### Arquiteto

Transforma histórias em especificação técnica, boundaries e estrutura de arquivos.

### Dev Base

Propõe schema e artefatos para `cap-platform`, incluindo o conjunto completo dos **23 models obrigatórios** do CAP-BASE em `base.prisma`. O Dev **não** declara arquivo criado nem aprova a própria entrega.

### Validação determinística (orquestrador)

Executada **após** o Dev Base e **antes** do Reviewer. Produz `validation-output.md` com status objetivo (**APROVADO**, **APROVÁVEL COM RESSALVAS**, **REPROVADO**) e checklist dos models. **Não substitui** `npx prisma validate` no repositório real, mas impede aprovação falsa quando a proposta viola regras fixas.

### Reviewer

Revisa aderência técnica e escopo usando a validação determinística como fonte obrigatória. Não afirma evidência física sem suporte objetivo.

### QA

Valida evidências reais e status final. Texto do Dev não conta como evidência de execução. Sem arquivo real e sem `npx prisma validate` executado com registro, **não** há `Aprovado`.

## Status na validação determinística

```text
APROVADO
APROVÁVEL COM RESSALVAS
REPROVADO
```

## Status humanos / agentes downstream

Conforme instruções dos agentes Reviewer e QA e registro em `final.md`.
