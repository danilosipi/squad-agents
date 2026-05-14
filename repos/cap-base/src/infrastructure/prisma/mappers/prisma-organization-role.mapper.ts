import { OrganizationRole } from "../../../domain/entities/organization-role.entity.js";

export type PrismaOrganizationRoleRecord = {
  id: number;
  code: string;
  name: string;
  description: string | null;
  isActive: boolean;
};

export function toDomain(record: PrismaOrganizationRoleRecord): OrganizationRole {
  return OrganizationRole.create({
    id: record.id,
    code: record.code,
    name: record.name,
    description: record.description ?? undefined,
    isActive: record.isActive,
  });
}

export type PrismaOrganizationRoleCreateData = {
  code: string;
  name: string;
  description: string | null;
  isActive: boolean;
};

export function toPrismaCreate(role: OrganizationRole): PrismaOrganizationRoleCreateData {
  return {
    code: role.code.trim(),
    name: role.name.trim(),
    description: role.description?.trim() ? role.description.trim() : null,
    isActive: role.isActive,
  };
}

export type PrismaOrganizationRoleUpdateData = PrismaOrganizationRoleCreateData;

export function toPrismaUpdate(role: OrganizationRole): PrismaOrganizationRoleUpdateData {
  return toPrismaCreate(role);
}
