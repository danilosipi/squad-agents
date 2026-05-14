import { describe, expect, it } from "vitest";
import type { PrismaOrganizationRecord } from "../../src/infrastructure/prisma/mappers/prisma-organization.mapper.js";
import type { PrismaOrganizationRoleRecord } from "../../src/infrastructure/prisma/mappers/prisma-organization-role.mapper.js";
import type { PrismaOrganizationRoleAssignmentRecord } from "../../src/infrastructure/prisma/mappers/prisma-organization-role-assignment.mapper.js";
import type { PrismaOrganizationDelegate } from "../../src/infrastructure/prisma/prisma-organizations.repository.js";
import type { PrismaOrganizationRoleDelegate } from "../../src/infrastructure/prisma/prisma-organization-roles.repository.js";
import type { PrismaOrganizationRoleAssignmentDelegate } from "../../src/infrastructure/prisma/prisma-organization-role-assignments.repository.js";
import type { PrismaCapBaseRepositoriesClientLike } from "../../src/composition/prisma-cap-base-repositories-client.js";
import { createCapBaseModule } from "../../src/composition/create-cap-base-module.js";
import { PrismaOrganizationsRepository } from "../../src/infrastructure/prisma/prisma-organizations.repository.js";
import { PrismaOrganizationRolesRepository } from "../../src/infrastructure/prisma/prisma-organization-roles.repository.js";
import { PrismaOrganizationRoleAssignmentsRepository } from "../../src/infrastructure/prisma/prisma-organization-role-assignments.repository.js";
import { CreateOrganizationUseCase } from "../../src/application/use-cases/create-organization.use-case.js";
import { CreateOrganizationRoleUseCase } from "../../src/application/use-cases/create-organization-role.use-case.js";
import { CreateOrganizationRoleAssignmentUseCase } from "../../src/application/use-cases/create-organization-role-assignment.use-case.js";

type OrgCreateArg = {
  data: {
    name: string;
    tradeName: string | null;
    documentNumber: string;
    isActive: boolean;
    typeId: number;
    statusId: number;
  };
};

type OrgUpdateArg = {
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

function createFakeOrganizationDelegate(): PrismaOrganizationDelegate {
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
      const { data } = args as OrgCreateArg;
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
      const { where, data } = args as OrgUpdateArg;
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

function createFakeOrganizationRoleDelegate(): PrismaOrganizationRoleDelegate {
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

function createFakeOrganizationRoleAssignmentDelegate(): PrismaOrganizationRoleAssignmentDelegate {
  const rows: PrismaOrganizationRoleAssignmentRecord[] = [];
  let nextId = 1;

  return {
    async findUnique(args: unknown): Promise<unknown> {
      const a = args as { where: { id: number } };
      return rows.find((r) => r.id === a.where.id) ?? null;
    },

    async findMany(args: unknown): Promise<unknown[]> {
      const a = args as {
        where?: { organizationId?: number; roleId?: number };
        orderBy?: { id: string };
      };
      let result = [...rows];
      if (a.where?.organizationId !== undefined) {
        result = result.filter((r) => r.organizationId === a.where!.organizationId);
      }
      if (a.where?.roleId !== undefined) {
        result = result.filter((r) => r.roleId === a.where!.roleId);
      }
      result.sort((x, y) => x.id - y.id);
      return result;
    },

    async create(args: unknown): Promise<unknown> {
      const { data } = args as {
        data: {
          organizationId: number;
          roleId: number;
          assignedAt: Date;
          revokedAt: Date | null;
          isActive: boolean;
        };
      };
      const row: PrismaOrganizationRoleAssignmentRecord = {
        id: nextId++,
        organizationId: data.organizationId,
        roleId: data.roleId,
        assignedAt: data.assignedAt,
        revokedAt: data.revokedAt,
        isActive: data.isActive,
      };
      rows.push(row);
      return row;
    },

    async update(args: unknown): Promise<unknown> {
      const { where, data } = args as {
        where: { id: number };
        data: {
          organizationId: number;
          roleId: number;
          assignedAt: Date;
          revokedAt: Date | null;
          isActive: boolean;
        };
      };
      const idx = rows.findIndex((r) => r.id === where.id);
      if (idx === -1) {
        throw new Error(`OrganizationRoleAssignment ${where.id} not found`);
      }
      const prev = rows[idx]!;
      const row: PrismaOrganizationRoleAssignmentRecord = {
        ...prev,
        organizationId: data.organizationId,
        roleId: data.roleId,
        assignedAt: data.assignedAt,
        revokedAt: data.revokedAt,
        isActive: data.isActive,
      };
      rows[idx] = row;
      return row;
    },
  };
}

function createFakePrismaCapBaseClient(): PrismaCapBaseRepositoriesClientLike {
  return {
    organization: createFakeOrganizationDelegate(),
    organizationRole: createFakeOrganizationRoleDelegate(),
    organizationRoleAssignment: createFakeOrganizationRoleAssignmentDelegate(),
  };
}

describe("createCapBaseModule", () => {
  it("expõe os três repositórios Prisma esperados", () => {
    const mod = createCapBaseModule(createFakePrismaCapBaseClient());
    expect(mod.repositories.organizations).toBeInstanceOf(PrismaOrganizationsRepository);
    expect(mod.repositories.organizationRoles).toBeInstanceOf(PrismaOrganizationRolesRepository);
    expect(mod.repositories.organizationRoleAssignments).toBeInstanceOf(
      PrismaOrganizationRoleAssignmentsRepository,
    );
  });

  it("expõe todos os use cases esperados", () => {
    const mod = createCapBaseModule(createFakePrismaCapBaseClient());
    const keys = Object.keys(mod.useCases).sort();
    expect(keys).toEqual([
      "createOrganization",
      "createOrganizationRole",
      "createOrganizationRoleAssignment",
      "getOrganization",
      "getOrganizationRole",
      "listOrganizationRoleAssignmentsByOrganization",
      "listOrganizationRoleAssignmentsByRole",
      "listOrganizationRoles",
      "listOrganizations",
      "revokeOrganizationRoleAssignment",
      "updateOrganization",
      "updateOrganizationRole",
    ]);
    expect(mod.useCases.createOrganization).toBeInstanceOf(CreateOrganizationUseCase);
    expect(mod.useCases.createOrganizationRole).toBeInstanceOf(CreateOrganizationRoleUseCase);
    expect(mod.useCases.createOrganizationRoleAssignment).toBeInstanceOf(
      CreateOrganizationRoleAssignmentUseCase,
    );
  });

  it("createOrganization funciona com o módulo composto", async () => {
    const mod = createCapBaseModule(createFakePrismaCapBaseClient());
    const out = await mod.useCases.createOrganization.execute({
      legalName: "Empresa Módulo",
      tradeName: "Marca",
      documentNumber: "33445566000187",
    });
    expect(out.id).toBeGreaterThan(0);
    expect(out.legalName).toBe("Empresa Módulo");
    expect(out.documentNumber).toBe("33445566000187");
  });

  it("createOrganizationRole funciona com o módulo composto", async () => {
    const mod = createCapBaseModule(createFakePrismaCapBaseClient());
    const out = await mod.useCases.createOrganizationRole.execute({
      code: "MODULE_ROLE",
      name: "Papel de teste",
      description: "via composition root",
    });
    expect(out.id).toBeGreaterThan(0);
    expect(out.code).toBe("MODULE_ROLE");
  });

  it("createOrganizationRoleAssignment funciona com o módulo composto", async () => {
    const mod = createCapBaseModule(createFakePrismaCapBaseClient());
    const org = await mod.useCases.createOrganization.execute({
      legalName: "Org vínculo",
      documentNumber: "55667788000120",
    });
    const role = await mod.useCases.createOrganizationRole.execute({
      code: "ROLE_FOR_ASSIGN",
      name: "Papel vínculo",
    });
    const link = await mod.useCases.createOrganizationRoleAssignment.execute({
      organizationId: org.id,
      roleId: role.id,
    });
    expect(link.organizationId).toBe(org.id);
    expect(link.roleId).toBe(role.id);
    expect(link.isActive).toBe(true);
  });
});
