import { describe, expect, it } from "vitest";
import { CreateOrganizationRoleUseCase } from "../../src/application/use-cases/create-organization-role.use-case.js";
import { UpdateOrganizationRoleUseCase } from "../../src/application/use-cases/update-organization-role.use-case.js";
import { GetOrganizationRoleUseCase } from "../../src/application/use-cases/get-organization-role.use-case.js";
import { ListOrganizationRolesUseCase } from "../../src/application/use-cases/list-organization-roles.use-case.js";
import { InMemoryOrganizationRolesRepository } from "../fakes/in-memory-organization-roles.repository.js";

describe("OrganizationRole use cases", () => {
  it("CreateOrganizationRoleUseCase cria papel", async () => {
    const repo = new InMemoryOrganizationRolesRepository();
    const useCase = new CreateOrganizationRoleUseCase(repo);
    const out = await useCase.execute({
      code: "ADMIN",
      name: "Administrador",
      description: "Acesso total",
    });
    expect(out.id).toBeGreaterThan(0);
    expect(out.code).toBe("ADMIN");
    expect(out.name).toBe("Administrador");
    expect(out.description).toBe("Acesso total");
    expect(out.isActive).toBe(true);
  });

  it("CreateOrganizationRoleUseCase bloqueia code duplicado", async () => {
    const repo = new InMemoryOrganizationRolesRepository();
    const useCase = new CreateOrganizationRoleUseCase(repo);
    await useCase.execute({ code: "VIEWER", name: "Leitor" });
    await expect(useCase.execute({ code: "VIEWER", name: "Outro nome" })).rejects.toThrow(
      'Já existe papel organizacional com o code "VIEWER".',
    );
  });

  it("UpdateOrganizationRoleUseCase atualiza papel", async () => {
    const repo = new InMemoryOrganizationRolesRepository();
    const create = new CreateOrganizationRoleUseCase(repo);
    const created = await create.execute({ code: "OLD", name: "Nome Antigo" });
    const update = new UpdateOrganizationRoleUseCase(repo);
    const out = await update.execute({
      id: created.id,
      name: "Nome Novo",
      code: "NEW",
    });
    expect(out.name).toBe("Nome Novo");
    expect(out.code).toBe("NEW");
  });

  it("UpdateOrganizationRoleUseCase falha para id inexistente", async () => {
    const repo = new InMemoryOrganizationRolesRepository();
    const update = new UpdateOrganizationRoleUseCase(repo);
    await expect(update.execute({ id: 999, name: "X" })).rejects.toThrow(
      "Papel organizacional com id 999 não encontrado.",
    );
  });

  it("GetOrganizationRoleUseCase busca por id", async () => {
    const repo = new InMemoryOrganizationRolesRepository();
    const create = new CreateOrganizationRoleUseCase(repo);
    const created = await create.execute({ code: "GET_ME", name: "Para Buscar" });
    const get = new GetOrganizationRoleUseCase(repo);
    const out = await get.execute(created.id);
    expect(out).not.toBeNull();
    expect(out!.code).toBe("GET_ME");
  });

  it("ListOrganizationRolesUseCase lista papéis", async () => {
    const repo = new InMemoryOrganizationRolesRepository();
    const create = new CreateOrganizationRoleUseCase(repo);
    await create.execute({ code: "A_ROLE", name: "Alpha Cargo" });
    await create.execute({ code: "B_ROLE", name: "Beta Serviços" });
    const list = new ListOrganizationRolesUseCase(repo);
    const all = await list.execute();
    expect(all).toHaveLength(2);
    const filtered = await list.execute({ search: "Alpha", limit: 10, offset: 0 });
    expect(filtered).toHaveLength(1);
    expect(filtered[0]!.code).toBe("A_ROLE");
  });
});
