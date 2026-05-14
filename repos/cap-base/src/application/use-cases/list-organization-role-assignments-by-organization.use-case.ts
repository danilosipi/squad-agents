import type { OrganizationRoleAssignmentsRepository } from "../../domain/repositories/organization-role-assignments.repository.js";
import type { OrganizationRoleAssignmentOutput } from "../dto/create-organization-role-assignment.dto.js";
import { toOrganizationRoleAssignmentOutput } from "../mappers/organization-role-assignment.mapper.js";

export class ListOrganizationRoleAssignmentsByOrganizationUseCase {
  constructor(private readonly assignments: OrganizationRoleAssignmentsRepository) {}

  async execute(organizationId: number): Promise<OrganizationRoleAssignmentOutput[]> {
    const list = await this.assignments.listByOrganizationId(organizationId);
    return list.map(toOrganizationRoleAssignmentOutput);
  }
}
