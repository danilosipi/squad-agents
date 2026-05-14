# Como aplicar este pacote

1. Faça backup da pasta atual `Projetos/squad-agentes`.
2. Extraia este ZIP dentro da pasta `Projetos`.
3. Quando perguntar se deseja substituir arquivos, aceite somente se quiser aplicar os ajustes.
4. Não copie `.env` de dentro de outro ambiente. Use `.env.example` como referência.
5. Não copie `.venv` para o Git.

## Após extrair

Confira se existem estes caminhos:

```text
Projetos/squad-agentes/docs/00-fonte-oficial.md
Projetos/squad-agentes/agents/templates/
Projetos/squad-agentes/squads/cap/agents/
Projetos/squad-agentes/squads/cap/workflow.md
Projetos/squad-agentes/squads/cap/task-policy.md
Projetos/squad-agentes/projects/cap/backlog.md
Projetos/squad-agentes/runs/cap/001-cap-base-database/
Projetos/squad-agentes/outputs/cap/001-cap-base-database.md
```

## Próximo passo depois da estrutura

Criar o primeiro arquivo real no projeto CAP:

```text
Projetos/cap-platform/repos/cap-base/prisma/base.prisma
```

## Limpeza obrigatória após aplicar

Dentro de `Projetos/squad-agentes/squads/cap/agents/`, mantenha apenas:

```text
po.md
architect.md
dev-base.md
reviewer.md
qa.md
```

Remova, se ainda existirem:

```text
po-cap.md
architect-cap.md
dev-cap-base.md
reviewer-cap.md
qa-cap.md
```
