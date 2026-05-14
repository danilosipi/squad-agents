import { Organization } from "../../../domain/entities/organization.entity.js";

/**
 * Registro persistido pelo Prisma (campos usados pelo agregado Organization).
 * `name` corresponde ao legalName do domínio.
 */
export type PrismaOrganizationRecord = {
  id: number;
  name: string;
  tradeName: string | null;
  documentNumber: string | null;
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
};

export function toDomain(record: PrismaOrganizationRecord): Organization {
  const doc = record.documentNumber?.trim() ?? "";
  if (!doc) {
    throw new Error("Registro Prisma sem documentNumber persistido.");
  }
  return Organization.create({
    id: record.id,
    legalName: record.name,
    tradeName: record.tradeName ?? undefined,
    documentNumber: doc,
    isActive: record.isActive,
    createdAt: record.createdAt,
    updatedAt: record.updatedAt,
  });
}

export type PrismaOrganizationCreateData = {
  name: string;
  tradeName: string | null;
  documentNumber: string;
  isActive: boolean;
  typeId: number;
  statusId: number;
};

export function toPrismaCreate(
  organization: Organization,
  statusId: number,
  typeId: number,
): PrismaOrganizationCreateData {
  return {
    name: organization.legalName,
    tradeName: organization.tradeName ?? null,
    documentNumber: organization.documentNumber.trim(),
    isActive: organization.isActive,
    typeId,
    statusId,
  };
}

export type PrismaOrganizationUpdateData = {
  name: string;
  tradeName: string | null;
  documentNumber: string;
  isActive: boolean;
  statusId: number;
};

export function toPrismaUpdate(organization: Organization, statusId: number): PrismaOrganizationUpdateData {
  return {
    name: organization.legalName,
    tradeName: organization.tradeName ?? null,
    documentNumber: organization.documentNumber.trim(),
    isActive: organization.isActive,
    statusId,
  };
}
