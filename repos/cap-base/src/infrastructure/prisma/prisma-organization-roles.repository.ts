import type { ListOrganizationRolesParams, OrganizationRolesRepository } from "../../domain/repositories/organization-roles.repository.js";
import type { OrganizationRole } from "../../domain/entities/organization-role.entity.js";
import {
  toDomain,
  toPrismaCreate,
  toPrismaUpdate,
  type PrismaOrganizationRoleRecord,
} from "./mappers/prisma-organization-role.mapper.js";

export type PrismaOrganizationRoleDelegate = {
  findUnique(args: unknown): Promise<unknown>;
  findFirst(args: unknown): Promise<unknown>;
  findMany(args: unknown): Promise<unknown[]>;
  create(args: unknown): Promise<unknown>;
  update(args: unknown): Promise<unknown>;
};

export type PrismaOrganizationRolesClientLike = {
  organizationRole: PrismaOrganizationRoleDelegate;
};

function isRoleRecord(value: unknown): value is PrismaOrganizationRoleRecord {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const r = value as Record<string, unknown>;
  return (
    typeof r.id === "number" &&
    typeof r.code === "string" &&
    typeof r.name === "string" &&
    (r.description === null || typeof r.description === "string") &&
    typeof r.isActive === "boolean"
  );
}

function asRoleRecord(value: unknown): PrismaOrganizationRoleRecord | null {
  if (value === null || value === undefined) {
    return null;
  }
  return isRoleRecord(value) ? value : null;
}

/**
 * Implementação de {@link OrganizationRolesRepository} via delegate Prisma (`prisma.organizationRole`).
 */
export class PrismaOrganizationRolesRepository implements OrganizationRolesRepository {
  constructor(private readonly prisma: PrismaOrganizationRolesClientLike) {}

  async findById(id: number): Promise<OrganizationRole | null> {
    const raw = await this.prisma.organizationRole.findUnique({ where: { id } });
    const row = asRoleRecord(raw);
    return row ? toDomain(row) : null;
  }

  async findByCode(code: string): Promise<OrganizationRole | null> {
    const c = code.trim();
    const raw = await this.prisma.organizationRole.findFirst({ where: { code: c } });
    const row = asRoleRecord(raw);
    return row ? toDomain(row) : null;
  }

  async list(params?: ListOrganizationRolesParams): Promise<OrganizationRole[]> {
    const where: Record<string, unknown> = {};
    if (params?.isActive !== undefined) {
      where.isActive = params.isActive;
    }
    const search = params?.search?.trim();
    if (search) {
      where.OR = [
        { code: { contains: search, mode: "insensitive" } },
        { name: { contains: search, mode: "insensitive" } },
        { description: { contains: search, mode: "insensitive" } },
      ];
    }
    const findArgs: Record<string, unknown> = {
      where,
      orderBy: { id: "asc" },
    };
    if (params?.offset !== undefined) {
      findArgs.skip = params.offset;
    }
    if (params?.limit !== undefined) {
      findArgs.take = params.limit;
    }
    const rows = await this.prisma.organizationRole.findMany(findArgs);
    const out: OrganizationRole[] = [];
    for (const raw of rows) {
      const row = asRoleRecord(raw);
      if (row) {
        out.push(toDomain(row));
      }
    }
    return out;
  }

  async save(role: OrganizationRole): Promise<OrganizationRole> {
    if (role.id === 0) {
      const data = toPrismaCreate(role);
      const raw = await this.prisma.organizationRole.create({ data });
      const row = asRoleRecord(raw);
      if (!row) {
        throw new Error("Prisma create não retornou registro de OrganizationRole.");
      }
      return toDomain(row);
    }
    const data = toPrismaUpdate(role);
    const raw = await this.prisma.organizationRole.update({
      where: { id: role.id },
      data,
    });
    const row = asRoleRecord(raw);
    if (!row) {
      throw new Error("Prisma update não retornou registro de OrganizationRole.");
    }
    return toDomain(row);
  }
}
