import type { OrganizationRoleAssignment } from "../entities/organization-role-assignment.entity.js";

/**
 * Contrato de persistência para {@link OrganizationRoleAssignment} (sem implementação).
 */
export interface OrganizationRoleAssignmentsRepository {
  findById(id: number): Promise<OrganizationRoleAssignment | null>;
  listByOrganizationId(organizationId: number): Promise<OrganizationRoleAssignment[]>;
  listByRoleId(roleId: number): Promise<OrganizationRoleAssignment[]>;
  save(assignment: OrganizationRoleAssignment): Promise<OrganizationRoleAssignment>;
}
