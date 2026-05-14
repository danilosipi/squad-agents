# Fase 5 — Interface conversacional (CLI)

## Objetivo da fase

Oferecer uma **sessão interativa no terminal** para que o Danilo descreva demandas em linguagem natural, **sem montar manualmente** o comando `python scripts/run_squad.py ...`. O repositório continua sendo a fonte de verdade: cada execução gera arquivos em `runs/<projeto>/` (e `outputs/cap/` quando aplicável), no mesmo padrão já usado pelo orquestrador.

## O que a interface faz

- Inicia um loop local (`python scripts/chat_squad.py`) com mensagem de boas-vindas e estado atual (**projeto** e **modo**).
- Aceita comandos para alterar o **projeto** (padrão `cap`) e o **modo**:
  - **`markdown`**: grava `runs/{projeto}/{run_id}/input.md` com a demanda, depois executa o meta-orquestrador via `scripts/run_squad.py ... --agent meta-orchestrator` (subprocess na raiz do repo), gerando `final.md`, `meta-orchestrator-output.md` e cópias em `outputs/cap/`, como no fluxo atual.
  - **`json_prepare_run`**: chama a preparação em JSON reutilizando `prepare_run.py` (`prepare_cap_run_json_forced_slug`), criando `input.md` e `meta-output.md` em `runs/cap/{run_id}/`. O `run_id` segue o formato `YYYYMMDD-HHMMSS-slug-curto` (UTC).
- Gera um **run_id** legível a partir do horário UTC e de um slug derivado da demanda.
- Permite **várias demandas na mesma sessão** até o usuário encerrar com `sair`, `exit` ou `quit`.
- Mostra no terminal um **resumo** com demanda, projeto, modo, run id, caminhos dos arquivos principais e status da execução.

## O que a interface não faz

- Não substitui **aprovação humana** do plano ou das entregas.
- Não inclui **frontend web**, **banco de dados** nem **agentes autônomos** em background.
- Não altera o contrato da linha de comando de `run_squad.py` nem remove flags existentes.
- No modo JSON, o preparador continua **acoplado ao projeto `cap`** nos caminhos de contexto (igual ao `prepare_run.py` atual); outros projetos ainda não são suportados pelo preparador.

## Como executar

Na raiz do repositório `squad-agentes`, com o ambiente Python e dependências já configurados (`pip install -r requirements.txt`) e `OPENAI_API_KEY` definida (por exemplo em `.env`):

```text
python scripts/chat_squad.py
```

Comandos úteis dentro da sessão:

```text
projeto cap
modo markdown
modo json_prepare_run
sair
```

## Exemplo de uso

```text
python scripts/chat_squad.py

Squad Agentes — Interface Conversacional
Projeto atual: cap
Modo atual: markdown

> Criar plano técnico para implementar contratos do cap-base
```

O script cria `runs/cap/<run_id>/input.md`, invoca `run_squad.py` com `--agent meta-orchestrator` e imprime os caminhos de `final.md` e demais artefatos conforme a saída do orquestrador.

Para apenas **estruturar** o próximo run em Markdown de input via modelo (JSON), use `modo json_prepare_run` e descreva a demanda; em seguida é possível executar manualmente a squad completa com o comando sugerido ao final.

## Limitações atuais

- Apenas o projeto **`cap`** é suportado de ponta a ponta; `run_squad.py` e `prepare_run.py` já refletem essa restrição.
- O modo **`json_prepare_run`** grava sempre em `runs/cap/...`, independentemente do rótulo de projeto na sessão (o resumo indica `cap` para refletir os caminhos reais).
- Erros da API (rede, quota, chave inválida) aparecem como mensagens no terminal; falhas no modo JSON encerram aquela tentativa com `SystemExit` tratado na interface (sem derrubar o processo inteiro, salvo `KeyboardInterrupt` / EOF).
- Não há histórico persistente da conversa além dos arquivos gerados no disco.

## Próximos passos futuros (sugestões)

- Suportar outros `projects/` com bundles de contexto configuráveis.
- Opção de encadear automaticamente, após o JSON, uma execução `--agent meta-orchestrator` sobre o `input.md` gerado (hoje é um passo manual sugerido).
- Atalhos para `--write-files` / `--validate-existing` com confirmação explícita no terminal.
- Testes automatizados com subprocess mockado ou fixtures de entrada/saída.
