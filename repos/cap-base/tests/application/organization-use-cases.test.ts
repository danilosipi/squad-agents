import { describe, expect, it } from "vitest";
import { CreateOrganizationUseCase } from "../../src/application/use-cases/create-organization.use-case.js";
import { UpdateOrganizationUseCase } from "../../src/application/use-cases/update-organization.use-case.js";
import { GetOrganizationUseCase } from "../../src/application/use-cases/get-organization.use-case.js";
import { ListOrganizationsUseCase } from "../../src/application/use-cases/list-organizations.use-case.js";
import { InMemoryOrganizationsRepository } from "../fakes/in-memory-organizations.repository.js";

describe("Organization use cases", () => {
  it("CreateOrganizationUseCase cria organização", async () => {
    const repo = new InMemoryOrganizationsRepository();
    const useCase = new CreateOrganizationUseCase(repo);
    const out = await useCase.execute({
      legalName: "Empresa A",
      tradeName: "Marca A",
      documentNumber: "12345678000195",
    });
    expect(out.id).toBeGreaterThan(0);
    expect(out.legalName).toBe("Empresa A");
    expect(out.tradeName).toBe("Marca A");
    expect(out.documentNumber).toBe("12345678000195");
    expect(out.isActive).toBe(true);
    expect(out.createdAt).toBeInstanceOf(Date);
  });

  it("CreateOrganizationUseCase bloqueia documento duplicado", async () => {
    const repo = new InMemoryOrganizationsRepository();
    const useCase = new CreateOrganizationUseCase(repo);
    await useCase.execute({
      legalName: "Primeira",
      documentNumber: "12345678000195",
    });
    await expect(
      useCase.execute({
        legalName: "Segunda",
        documentNumber: "12345678000195",
      }),
    ).rejects.toThrow('Já existe organização com o documentNumber "12345678000195".');
  });

  it("UpdateOrganizationUseCase atualiza organização", async () => {
    const repo = new InMemoryOrganizationsRepository();
    const create = new CreateOrganizationUseCase(repo);
    const created = await create.execute({
      legalName: "Nome Antigo",
      documentNumber: "12345678000195",
    });
    const update = new UpdateOrganizationUseCase(repo);
    const out = await update.execute({
      id: created.id,
      legalName: "Nome Novo",
    });
    expect(out.legalName).toBe("Nome Novo");
    expect(out.documentNumber).toBe("12345678000195");
  });

  it("UpdateOrganizationUseCase falha para id inexistente", async () => {
    const repo = new InMemoryOrganizationsRepository();
    const update = new UpdateOrganizationUseCase(repo);
    await expect(update.execute({ id: 999, legalName: "X" })).rejects.toThrow(
      "Organização com id 999 não encontrada.",
    );
  });

  it("GetOrganizationUseCase retorna DTO", async () => {
    const repo = new InMemoryOrganizationsRepository();
    const create = new CreateOrganizationUseCase(repo);
    const created = await create.execute({
      legalName: "Para Buscar",
      documentNumber: "98765432000187",
    });
    const get = new GetOrganizationUseCase(repo);
    const out = await get.execute(created.id);
    expect(out).not.toBeNull();
    expect(out!.id).toBe(created.id);
    expect(out!.legalName).toBe("Para Buscar");
  });

  it("ListOrganizationsUseCase retorna lista", async () => {
    const repo = new InMemoryOrganizationsRepository();
    const create = new CreateOrganizationUseCase(repo);
    await create.execute({ legalName: "Alpha Indústria", documentNumber: "11111111000191" });
    await create.execute({ legalName: "Beta Serviços", documentNumber: "22222222000172" });
    const list = new ListOrganizationsUseCase(repo);
    const all = await list.execute();
    expect(all).toHaveLength(2);
    const filtered = await list.execute({ search: "Alpha", limit: 10, offset: 0 });
    expect(filtered).toHaveLength(1);
    expect(filtered[0]!.legalName).toBe("Alpha Indústria");
  });
});
