import type { OrganizationRoleAssignmentsRepository } from "../../domain/repositories/organization-role-assignments.repository.js";
import type { OrganizationRoleAssignment } from "../../domain/entities/organization-role-assignment.entity.js";
import {
  toDomain,
  toPrismaCreate,
  toPrismaUpdate,
  type PrismaOrganizationRoleAssignmentRecord,
} from "./mappers/prisma-organization-role-assignment.mapper.js";

export type PrismaOrganizationRoleAssignmentDelegate = {
  findUnique(args: unknown): Promise<unknown>;
  findMany(args: unknown): Promise<unknown[]>;
  create(args: unknown): Promise<unknown>;
  update(args: unknown): Promise<unknown>;
};

export type PrismaOrganizationRoleAssignmentsClientLike = {
  organizationRoleAssignment: PrismaOrganizationRoleAssignmentDelegate;
};

function isAssignmentRecord(value: unknown): value is PrismaOrganizationRoleAssignmentRecord {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const r = value as Record<string, unknown>;
  return (
    typeof r.id === "number" &&
    typeof r.organizationId === "number" &&
    typeof r.roleId === "number" &&
    r.assignedAt instanceof Date &&
    (r.revokedAt === null || r.revokedAt instanceof Date) &&
    typeof r.isActive === "boolean"
  );
}

function asAssignmentRecord(value: unknown): PrismaOrganizationRoleAssignmentRecord | null {
  if (value === null || value === undefined) {
    return null;
  }
  return isAssignmentRecord(value) ? value : null;
}

/**
 * Implementação de {@link OrganizationRoleAssignmentsRepository} via delegate Prisma (`prisma.organizationRoleAssignment`).
 */
export class PrismaOrganizationRoleAssignmentsRepository implements OrganizationRoleAssignmentsRepository {
  constructor(private readonly prisma: PrismaOrganizationRoleAssignmentsClientLike) {}

  async findById(id: number): Promise<OrganizationRoleAssignment | null> {
    const raw = await this.prisma.organizationRoleAssignment.findUnique({ where: { id } });
    const row = asAssignmentRecord(raw);
    return row ? toDomain(row) : null;
  }

  async listByOrganizationId(organizationId: number): Promise<OrganizationRoleAssignment[]> {
    const rows = await this.prisma.organizationRoleAssignment.findMany({
      where: { organizationId },
      orderBy: { id: "asc" },
    });
    return rows.map((raw) => {
      const row = asAssignmentRecord(raw);
      if (!row) {
        throw new Error("Registro de OrganizationRoleAssignment inválido.");
      }
      return toDomain(row);
    });
  }

  async listByRoleId(roleId: number): Promise<OrganizationRoleAssignment[]> {
    const rows = await this.prisma.organizationRoleAssignment.findMany({
      where: { roleId },
      orderBy: { id: "asc" },
    });
    return rows.map((raw) => {
      const row = asAssignmentRecord(raw);
      if (!row) {
        throw new Error("Registro de OrganizationRoleAssignment inválido.");
      }
      return toDomain(row);
    });
  }

  async save(assignment: OrganizationRoleAssignment): Promise<OrganizationRoleAssignment> {
    if (assignment.id === 0) {
      const data = toPrismaCreate(assignment);
      const raw = await this.prisma.organizationRoleAssignment.create({ data });
      const row = asAssignmentRecord(raw);
      if (!row) {
        throw new Error("Prisma create não retornou registro de OrganizationRoleAssignment.");
      }
      return toDomain(row);
    }
    const data = toPrismaUpdate(assignment);
    const raw = await this.prisma.organizationRoleAssignment.update({
      where: { id: assignment.id },
      data,
    });
    const row = asAssignmentRecord(raw);
    if (!row) {
      throw new Error("Prisma update não retornou registro de OrganizationRoleAssignment.");
    }
    return toDomain(row);
  }
}
