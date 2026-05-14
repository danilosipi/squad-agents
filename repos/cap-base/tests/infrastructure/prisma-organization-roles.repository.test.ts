import { describe, expect, it } from "vitest";
import { OrganizationRole } from "../../src/domain/entities/organization-role.entity.js";
import {
  PrismaOrganizationRolesRepository,
  type PrismaOrganizationRoleDelegate,
  type PrismaOrganizationRolesClientLike,
} from "../../src/infrastructure/prisma/prisma-organization-roles.repository.js";
import type { PrismaOrganizationRoleRecord } from "../../src/infrastructure/prisma/mappers/prisma-organization-role.mapper.js";

function includesInsensitive(haystack: string, needle: string): boolean {
  return haystack.toLowerCase().includes(needle.toLowerCase());
}

function createFakeDelegate(): PrismaOrganizationRoleDelegate {
  const rows: PrismaOrganizationRoleRecord[] = [];
  let nextId = 1;

  return {
    async findUnique(args: unknown): Promise<unknown> {
      const a = args as { where: { id: number } };
      return rows.find((r) => r.id === a.where.id) ?? null;
    },

    async findFirst(args: unknown): Promise<unknown> {
      const a = args as { where: { code: string } };
      const c = a.where.code;
      return rows.find((r) => r.code.trim() === c) ?? null;
    },

    async findMany(args: unknown): Promise<unknown[]> {
      const a = args as {
        where?: {
          isActive?: boolean;
          OR?: Array<{
            code?: { contains: string; mode: string };
            name?: { contains: string; mode: string };
            description?: { contains: string; mode: string };
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
            code?: { contains: string; mode: string };
            name?: { contains: string; mode: string };
            description?: { contains: string; mode: string };
          };
          q = c.code?.contains ?? c.name?.contains ?? c.description?.contains ?? "";
          if (q) {
            break;
          }
        }
        if (q) {
          result = result.filter(
            (r) =>
              includesInsensitive(r.code, q) ||
              includesInsensitive(r.name, q) ||
              includesInsensitive(r.description ?? "", q),
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
      const { data } = args as {
        data: { code: string; name: string; description: string | null; isActive: boolean };
      };
      const row: PrismaOrganizationRoleRecord = {
        id: nextId++,
        code: data.code,
        name: data.name,
        description: data.description,
        isActive: data.isActive,
      };
      rows.push(row);
      return row;
    },

    async update(args: unknown): Promise<unknown> {
      const { where, data } = args as {
        where: { id: number };
        data: { code: string; name: string; description: string | null; isActive: boolean };
      };
      const idx = rows.findIndex((r) => r.id === where.id);
      if (idx === -1) {
        throw new Error(`OrganizationRole ${where.id} not found`);
      }
      const prev = rows[idx]!;
      const row: PrismaOrganizationRoleRecord = {
        ...prev,
        code: data.code,
        name: data.name,
        description: data.description,
        isActive: data.isActive,
      };
      rows[idx] = row;
      return row;
    },
  };
}

function makeSut() {
  const organizationRole = createFakeDelegate();
  const prisma: PrismaOrganizationRolesClientLike = { organizationRole };
  const repo = new PrismaOrganizationRolesRepository(prisma);
  return { repo };
}

describe("PrismaOrganizationRolesRepository (cliente fake, sem banco)", () => {
  it("save cria quando id === 0", async () => {
    const { repo } = makeSut();
    const role = OrganizationRole.create({
      id: 0,
      code: "ADMIN",
      name: "Administrador",
      description: "Acesso total",
    });
    const saved = await repo.save(role);
    expect(saved.id).toBeGreaterThan(0);
    expect(saved.code).toBe("ADMIN");
    expect(saved.name).toBe("Administrador");
    expect(saved.description).toBe("Acesso total");
    expect(saved.isActive).toBe(true);
  });

  it("save atualiza quando id > 0", async () => {
    const { repo } = makeSut();
    const first = await repo.save(
      OrganizationRole.create({
        id: 0,
        code: "VIEW",
        name: "Leitura",
      }),
    );
    first.deactivate();
    const second = await repo.save(first);
    expect(second.id).toBe(first.id);
    expect(second.isActive).toBe(false);
  });

  it("findById retorna entidade", async () => {
    const { repo } = makeSut();
    const saved = await repo.save(
      OrganizationRole.create({
        id: 0,
        code: "FIND",
        name: "Busca",
      }),
    );
    const found = await repo.findById(saved.id);
    expect(found).not.toBeNull();
    expect(found!.code).toBe("FIND");
  });

  it("findByCode retorna entidade", async () => {
    const { repo } = makeSut();
    await repo.save(
      OrganizationRole.create({
        id: 0,
        code: "BYCODE",
        name: "Por código",
      }),
    );
    const found = await repo.findByCode("  BYCODE  ");
    expect(found).not.toBeNull();
    expect(found!.name).toBe("Por código");
  });

  it("list respeita search e isActive", async () => {
    const { repo } = makeSut();
    const active = OrganizationRole.create({
      id: 0,
      code: "A1",
      name: "Alpha Role",
      description: "Descrição alpha",
      isActive: true,
    });
    const inactive = OrganizationRole.create({
      id: 0,
      code: "B2",
      name: "Beta Role",
      isActive: false,
    });
    await repo.save(active);
    await repo.save(inactive);
    const onlyActive = await repo.list({ isActive: true });
    expect(onlyActive).toHaveLength(1);
    expect(onlyActive[0]!.code).toBe("A1");
    const search = await repo.list({ search: "Beta" });
    expect(search).toHaveLength(1);
    expect(search[0]!.code).toBe("B2");
  });
});
