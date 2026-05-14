# Carregamento de contexto do projeto (Fase 5.7)

## Objetivo

Garantir que o meta-orquestrador e a squad completa trabalhem com o **contexto real** do projeto selecionado (pasta local registrada no SQLite, em geral sob `D:\Drive\Projetos\<slug>`), em especial arquivos em **`.squad/`**, antes de planejar ou entregar qualquer coisa.

## Arquivos lidos

O serviço `core/projects/project_context_service.py` consolida, quando existem:

| Origem | Caminho |
|--------|---------|
| Contexto squad | `.squad/context.md` |
| Roadmap local | `.squad/roadmap.md` |
| Decisões | `.squad/decisions.md` |
| Backlog JSON | `.squad/backlog.json` |
| Visão geral | `README.md` na raiz do projeto |
| Documentação | `docs/**/*.md` (limite de 25 arquivos; truncamento por arquivo e avisos no Markdown consolidado) |

## Contexto mínimo obrigatório

Para usar o chat com meta-orquestrador ou **Executar squad**, o projeto precisa:

1. Estar registrado no SQLite (`squad_projects`).
2. Ter `local_path` existente e acessível como diretório.
3. Ter **`.squad/context.md`** existente, legível, com pelo menos **80 caracteres** no conteúdo útil (após `strip`).

Se o mínimo não for atendido, a API responde com erro claro (HTTP 400 no envio ao meta-orquestrador, ou `status: "blocked"` no `execute-squad`) e a UI sugere preencher o arquivo.

## Estrutura `.squad/`

Ao criar ou registrar projeto pela API, o layout padrão inclui `.squad/` com arquivos iniciais (ver `project_service`). A função `ensure_project_squad_structure(slug, create_template_if_missing=True)` reutiliza o mesmo comportamento de templates do cadastro.

## Como preencher `.squad/context.md`

Inclua, em texto livre (Markdown):

- Objetivo do produto e escopo atual
- Stack tecnológica e ambientes
- Restrições (compliance, performance, orçamento)
- Glossário ou termos de negócio

O arquivo deve passar do limite mínimo de caracteres após edição; o stub gerado automaticamente costuma ser **insuficiente** até você complementar.

## Como o contexto entra no run

1. **Antes** de gravar `runs/<slug>/<run_id>/input.md`, o meta-orquestrador monta o Markdown consolidado e insere a seção `# Contexto do Projeto Selecionado` no `input.md`.
2. O mesmo conteúdo consolidado é gravado em **`runs/<slug>/<run_id>/project-context-used.md`** como evidência auditável.

## Evidência `project-context-used.md`

- Caminho relativo ao repositório: `runs/<slug>/<run_id>/project-context-used.md`.
- Em respostas JSON de sucesso do meta-orquestrador: `context_evidence_path`.
- Na execução da squad completa após aprovação: o endpoint devolve `context_evidence_path` quando a evidência foi garantida.

## Variável `SQUAD_REPO_ROOT`

Em produção, a raiz do repositório `squad-agentes` é inferida a partir do código. Em **testes** ou automações, defina `SQUAD_REPO_ROOT` apontando para uma pasta temporária para que `runs/` não seja escrita no disco de desenvolvimento real.

## Limitações atuais

- Sem integração GitHub: apenas arquivos locais.
- Sem `--write-real-files` nesta fase: nenhuma escrita fora do repositório da squad e da pasta do projeto além da leitura de contexto.
- Limite simples em `docs/**/*.md` (quantidade e truncamento) para proteger tokens.
- O projeto **CAP** continua sendo o único slug suportado pelo meta-orquestrador e pela squad completa na API; o carregador de contexto é genérico por `project_slug` para evolução futura.
