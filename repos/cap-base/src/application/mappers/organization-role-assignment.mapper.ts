import type { OrganizationRoleAssignment } from "../../domain/entities/organization-role-assignment.entity.js";
import type { OrganizationRoleAssignmentOutput } from "../dto/create-organization-role-assignment.dto.js";

export function toOrganizationRoleAssignmentOutput(
  assignment: OrganizationRoleAssignment,
): OrganizationRoleAssignmentOutput {
  return {
    id: assignment.id,
    organizationId: assignment.organizationId,
    roleId: assignment.roleId,
    assignedAt: assignment.assignedAt,
    revokedAt: assignment.revokedAt,
    isActive: assignment.isActive,
  };
}
