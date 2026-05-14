import { describe, expect, it } from "vitest";
import { Organization } from "../../src/domain/entities/organization.entity.js";
import {
  PrismaOrganizationsRepository,
  type PrismaClientLike,
  type PrismaOrganizationDelegate,
} from "../../src/infrastructure/prisma/prisma-organizations.repository.js";
import type { PrismaOrganizationRecord } from "../../src/infrastructure/prisma/mappers/prisma-organization.mapper.js";

type CreateArg = {
  data: {
    name: string;
    tradeName: string | null;
    documentNumber: string;
    isActive: boolean;
    typeId: number;
    statusId: number;
  };
};

type UpdateArg = {
  where: { id: number };
  data: {
    name: string;
    tradeName: string | null;
    documentNumber: string;
    isActive: boolean;
    statusId: number;
  };
};

function includesInsensitive(haystack: string, needle: string): boolean {
  return haystack.toLowerCase().includes(needle.toLowerCase());
}

/**
 * Delegate em memória com o mesmo formato de argumentos usado por {@link PrismaOrganizationsRepository}.
 */
function createFakeDelegate(): PrismaOrganizationDelegate {
  const rows: PrismaOrganizationRecord[] = [];
  let nextId = 1;

  return {
    async findUnique(args: unknown): Promise<unknown> {
      const a = args as { where: { id: number } };
      return rows.find((r) => r.id === a.where.id) ?? null;
    },

    async findFirst(args: unknown): Promise<unknown> {
      const a = args as { where: { documentNumber: string } };
      const doc = a.where.documentNumber;
      return rows.find((r) => (r.documentNumber ?? "").trim() === doc) ?? null;
    },

    async findMany(args: unknown): Promise<unknown[]> {
      const a = args as {
        where?: {
          isActive?: boolean;
          OR?: Array<{
            name?: { contains: string; mode: string };
            tradeName?: { contains: string; mode: string };
            documentNumber?: { contains: string; mode: string };
          }>;
        };
        skip?: number;
        take?: number;
        orderBy?: { id: string };
      };
      let result = [...rows];
      if (a.where?.isActive !== undefined) {
        result = result.filter((r) => r.isActive === a.where!.isActive);
      }
      const or = a.where?.OR;
      if (or && or.length > 0) {
        let q = "";
        for (const cond of or) {
          const c = cond as {
            name?: { contains: string; mode: string };
            tradeName?: { contains: string; mode: string };
            documentNumber?: { contains: string; mode: string };
          };
          q = c.name?.contains ?? c.tradeName?.contains ?? c.documentNumber?.contains ?? "";
          if (q) {
            break;
          }
        }
        if (q) {
          result = result.filter(
            (r) =>
              includesInsensitive(r.name, q) ||
              includesInsensitive(r.tradeName ?? "", q) ||
              includesInsensitive(r.documentNumber ?? "", q),
          );
        }
      }
      result.sort((x, y) => x.id - y.id);
      const offset = a.skip ?? 0;
      const limit = a.take;
      if (limit !== undefined) {
        return result.slice(offset, offset + limit);
      }
      return result.slice(offset);
    },

    async create(args: unknown): Promise<unknown> {
      const { data } = args as CreateArg;
      const now = new Date();
      const row: PrismaOrganizationRecord = {
        id: nextId++,
        name: data.name,
        tradeName: data.tradeName,
        documentNumber: data.documentNumber,
        isActive: data.isActive,
        createdAt: now,
        updatedAt: now,
      };
      rows.push(row);
      return row;
    },

    async update(args: unknown): Promise<unknown> {
      const { where, data } = args as UpdateArg;
      const idx = rows.findIndex((r) => r.id === where.id);
      if (idx === -1) {
        throw new Error(`Organization ${where.id} not found`);
      }
      const prev = rows[idx]!;
      const now = new Date();
      const row: PrismaOrganizationRecord = {
        ...prev,
        name: data.name,
        tradeName: data.tradeName,
        documentNumber: data.documentNumber,
        isActive: data.isActive,
        updatedAt: now,
      };
      rows[idx] = row;
      return row;
    },

    async delete(args: unknown): Promise<unknown> {
      const a = args as { where: { id: number } };
      const idx = rows.findIndex((r) => r.id === a.where.id);
      if (idx !== -1) {
        rows.splice(idx, 1);
      }
      return {};
    },
  };
}

function makeSut() {
  const organization = createFakeDelegate();
  const prisma: PrismaClientLike = { organization };
  const repo = new PrismaOrganizationsRepository(prisma, {
    defaultTypeId: 1,
    activeStatusId: 10,
    inactiveStatusId: 20,
  });
  return { repo, delegate: organization };
}

describe("PrismaOrganizationsRepository (cliente fake, sem banco)", () => {
  it("save cria quando id === 0", async () => {
    const { repo } = makeSut();
    const created = Organization.create({
      id: 0,
      legalName: "ACME LTDA",
      tradeName: "ACME",
      documentNumber: "12345678000195",
    });
    const saved = await repo.save(created);
    expect(saved.id).toBeGreaterThan(0);
    expect(saved.legalName).toBe("ACME LTDA");
    expect(saved.tradeName).toBe("ACME");
    expect(saved.documentNumber).toBe("12345678000195");
  });

  it("save atualiza quando id > 0", async () => {
    const { repo } = makeSut();
    const first = await repo.save(
      Organization.create({
        id: 0,
        legalName: "Antes",
        documentNumber: "11111111000191",
      }),
    );
    first.updateBasicInfo({ legalName: "Depois" });
    const second = await repo.save(first);
    expect(second.id).toBe(first.id);
    expect(second.legalName).toBe("Depois");
  });

  it("findById retorna entidade", async () => {
    const { repo } = makeSut();
    const saved = await repo.save(
      Organization.create({
        id: 0,
        legalName: "Busca Id",
        documentNumber: "22222222000172",
      }),
    );
    const found = await repo.findById(saved.id);
    expect(found).not.toBeNull();
    expect(found!.legalName).toBe("Busca Id");
  });

  it("findByDocumentNumber retorna entidade", async () => {
    const { repo } = makeSut();
    await repo.save(
      Organization.create({
        id: 0,
        legalName: "Doc",
        documentNumber: "33333333000153",
      }),
    );
    const found = await repo.findByDocumentNumber("33333333000153");
    expect(found).not.toBeNull();
    expect(found!.legalName).toBe("Doc");
  });

  it("list respeita isActive e search básico", async () => {
    const { repo } = makeSut();
    const a = Organization.create({
      id: 0,
      legalName: "Alpha Indústria",
      documentNumber: "44444444000135",
      isActive: true,
    });
    const b = Organization.create({
      id: 0,
      legalName: "Beta Serviços",
      documentNumber: "55555555000116",
      isActive: false,
    });
    await repo.save(a);
    await repo.save(b);
    const activeOnly = await repo.list({ isActive: true });
    expect(activeOnly).toHaveLength(1);
    expect(activeOnly[0]!.legalName).toBe("Alpha Indústria");
    const search = await repo.list({ search: "Beta" });
    expect(search).toHaveLength(1);
    expect(search[0]!.legalName).toBe("Beta Serviços");
  });

  it("delete remove registro", async () => {
    const { repo } = makeSut();
    const saved = await repo.save(
      Organization.create({
        id: 0,
        legalName: "Remover",
        documentNumber: "66666666000197",
      }),
    );
    await repo.delete(saved.id);
    expect(await repo.findById(saved.id)).toBeNull();
  });
});
