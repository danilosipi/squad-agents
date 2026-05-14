import { describe, expect, it } from "vitest";
import { OrganizationRoleAssignment } from "../../src/domain/entities/organization-role-assignment.entity.js";
import {
  PrismaOrganizationRoleAssignmentsRepository,
  type PrismaOrganizationRoleAssignmentDelegate,
  type PrismaOrganizationRoleAssignmentsClientLike,
} from "../../src/infrastructure/prisma/prisma-organization-role-assignments.repository.js";
import type { PrismaOrganizationRoleAssignmentRecord } from "../../src/infrastructure/prisma/mappers/prisma-organization-role-assignment.mapper.js";

function createFakeDelegate(): PrismaOrganizationRoleAssignmentDelegate {
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

function makeSut() {
  const organizationRoleAssignment = createFakeDelegate();
  const prisma: PrismaOrganizationRoleAssignmentsClientLike = { organizationRoleAssignment };
  const repo = new PrismaOrganizationRoleAssignmentsRepository(prisma);
  return { repo };
}

describe("PrismaOrganizationRoleAssignmentsRepository (cliente fake, sem banco)", () => {
  it("save cria quando id === 0", async () => {
    const { repo } = makeSut();
    const a = OrganizationRoleAssignment.create({
      id: 0,
      organizationId: 100,
      roleId: 200,
    });
    const saved = await repo.save(a);
    expect(saved.id).toBeGreaterThan(0);
    expect(saved.organizationId).toBe(100);
    expect(saved.roleId).toBe(200);
    expect(saved.isActive).toBe(true);
  });

  it("save atualiza quando id > 0", async () => {
    const { repo } = makeSut();
    const first = await repo.save(
      OrganizationRoleAssignment.create({
        id: 0,
        organizationId: 1,
        roleId: 2,
      }),
    );
    first.revoke();
    const second = await repo.save(first);
    expect(second.id).toBe(first.id);
    expect(second.isActive).toBe(false);
    expect(second.revokedAt).toBeDefined();
  });

  it("findById retorna entidade", async () => {
    const { repo } = makeSut();
    const saved = await repo.save(
      OrganizationRoleAssignment.create({
        id: 0,
        organizationId: 50,
        roleId: 60,
      }),
    );
    const found = await repo.findById(saved.id);
    expect(found).not.toBeNull();
    expect(found!.organizationId).toBe(50);
  });

  it("listByOrganizationId retorna vínculos da organização", async () => {
    const { repo } = makeSut();
    await repo.save(
      OrganizationRoleAssignment.create({
        id: 0,
        organizationId: 10,
        roleId: 1,
      }),
    );
    await repo.save(
      OrganizationRoleAssignment.create({
        id: 0,
        organizationId: 10,
        roleId: 2,
      }),
    );
    await repo.save(
      OrganizationRoleAssignment.create({
        id: 0,
        organizationId: 99,
        roleId: 3,
      }),
    );
    const list = await repo.listByOrganizationId(10);
    expect(list).toHaveLength(2);
    expect(list.map((x) => x.roleId).sort()).toEqual([1, 2]);
  });

  it("listByRoleId retorna vínculos do papel", async () => {
    const { repo } = makeSut();
    await repo.save(
      OrganizationRoleAssignment.create({
        id: 0,
        organizationId: 1,
        roleId: 77,
      }),
    );
    await repo.save(
      OrganizationRoleAssignment.create({
        id: 0,
        organizationId: 2,
        roleId: 77,
      }),
    );
    await repo.save(
      OrganizationRoleAssignment.create({
        id: 0,
        organizationId: 3,
        roleId: 88,
      }),
    );
    const list = await repo.listByRoleId(77);
    expect(list).toHaveLength(2);
    expect(list.every((x) => x.roleId === 77)).toBe(true);
  });
});
