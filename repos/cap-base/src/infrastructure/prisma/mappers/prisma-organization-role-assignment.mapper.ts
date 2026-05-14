import { OrganizationRoleAssignment } from "../../../domain/entities/organization-role-assignment.entity.js";

export type PrismaOrganizationRoleAssignmentRecord = {
  id: number;
  organizationId: number;
  roleId: number;
  assignedAt: Date;
  revokedAt: Date | null;
  isActive: boolean;
};

export function toDomain(record: PrismaOrganizationRoleAssignmentRecord): OrganizationRoleAssignment {
  return OrganizationRoleAssignment.create({
    id: record.id,
    organizationId: record.organizationId,
    roleId: record.roleId,
    assignedAt: record.assignedAt,
    revokedAt: record.revokedAt ?? undefined,
    isActive: record.isActive,
  });
}

export type PrismaOrganizationRoleAssignmentWriteData = {
  organizationId: number;
  roleId: number;
  assignedAt: Date;
  revokedAt: Date | null;
  isActive: boolean;
};

export function toPrismaCreate(assignment: OrganizationRoleAssignment): PrismaOrganizationRoleAssignmentWriteData {
  return {
    organizationId: assignment.organizationId,
    roleId: assignment.roleId,
    assignedAt: assignment.assignedAt,
    revokedAt: assignment.revokedAt ?? null,
    isActive: assignment.isActive,
  };
}

export function toPrismaUpdate(assignment: OrganizationRoleAssignment): PrismaOrganizationRoleAssignmentWriteData {
  return toPrismaCreate(assignment);
}
