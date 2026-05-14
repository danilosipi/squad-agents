import type { ListOrganizationsParams, OrganizationsRepository } from "../../domain/repositories/organizations.repository.js";
import type { Organization } from "../../domain/entities/organization.entity.js";
import {
  toDomain,
  toPrismaCreate,
  toPrismaUpdate,
  type PrismaOrganizationRecord,
} from "./mappers/prisma-organization.mapper.js";

export type PrismaOrganizationDelegate = {
  findUnique(args: unknown): Promise<unknown>;
  findFirst(args: unknown): Promise<unknown>;
  findMany(args: unknown): Promise<unknown[]>;
  create(args: unknown): Promise<unknown>;
  update(args: unknown): Promise<unknown>;
  delete(args: unknown): Promise<unknown>;
};

export type PrismaClientLike = {
  organization: PrismaOrganizationDelegate;
};

export type PrismaOrganizationsPersistenceConfig = {
  /** FK obrigatório no schema `Organization.typeId`. */
  defaultTypeId: number;
  /** `statusId` quando `organization.isActive === true`. */
  activeStatusId: number;
  /** `statusId` quando `organization.isActive === false`. */
  inactiveStatusId: number;
};

function isRecord(value: unknown): value is PrismaOrganizationRecord {
  if (value === null || typeof value !== "object") {
    return false;
  }
  const r = value as Record<string, unknown>;
  return (
    typeof r.id === "number" &&
    typeof r.name === "string" &&
    (r.tradeName === null || typeof r.tradeName === "string") &&
    (r.documentNumber === null || typeof r.documentNumber === "string") &&
    typeof r.isActive === "boolean" &&
    r.createdAt instanceof Date &&
    r.updatedAt instanceof Date
  );
}

function asOrganizationRecord(value: unknown): PrismaOrganizationRecord | null {
  if (value === null || value === undefined) {
    return null;
  }
  if (!isRecord(value)) {
    return null;
  }
  return value;
}

/**
 * Implementação de {@link OrganizationsRepository} via delegate Prisma (`prisma.organization`).
 */
export class PrismaOrganizationsRepository implements OrganizationsRepository {
  constructor(
    private readonly prisma: PrismaClientLike,
    private readonly persistence: PrismaOrganizationsPersistenceConfig,
  ) {}

  private resolveStatusId(organization: Organization): number {
    return organization.isActive ? this.persistence.activeStatusId : this.persistence.inactiveStatusId;
  }

  async findById(id: number): Promise<Organization | null> {
    const raw = await this.prisma.organization.findUnique({
      where: { id },
    });
    const row = asOrganizationRecord(raw);
    return row ? toDomain(row) : null;
  }

  async findByDocumentNumber(documentNumber: string): Promise<Organization | null> {
    const doc = documentNumber.trim();
    const raw = await this.prisma.organization.findFirst({
      where: { documentNumber: doc },
    });
    const row = asOrganizationRecord(raw);
    return row ? toDomain(row) : null;
  }

  async list(params?: ListOrganizationsParams): Promise<Organization[]> {
    const where: Record<string, unknown> = {};
    if (params?.isActive !== undefined) {
      where.isActive = params.isActive;
    }
    const search = params?.search?.trim();
    if (search) {
      where.OR = [
        { name: { contains: search, mode: "insensitive" } },
        { tradeName: { contains: search, mode: "insensitive" } },
        { documentNumber: { contains: search, mode: "insensitive" } },
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
    const rows = await this.prisma.organization.findMany(findArgs);
    const out: Organization[] = [];
    for (const raw of rows) {
      const row = asOrganizationRecord(raw);
      if (row) {
        out.push(toDomain(row));
      }
    }
    return out;
  }

  async save(organization: Organization): Promise<Organization> {
    if (organization.id === 0) {
      const statusId = this.resolveStatusId(organization);
      const data = toPrismaCreate(organization, statusId, this.persistence.defaultTypeId);
      const raw = await this.prisma.organization.create({ data });
      const row = asOrganizationRecord(raw);
      if (!row) {
        throw new Error("Prisma create não retornou registro de Organization.");
      }
      return toDomain(row);
    }
    const statusId = this.resolveStatusId(organization);
    const data = toPrismaUpdate(organization, statusId);
    const raw = await this.prisma.organization.update({
      where: { id: organization.id },
      data,
    });
    const row = asOrganizationRecord(raw);
    if (!row) {
      throw new Error("Prisma update não retornou registro de Organization.");
    }
    return toDomain(row);
  }

  async delete(id: number): Promise<void> {
    await this.prisma.organization.delete({
      where: { id },
    });
  }
}
