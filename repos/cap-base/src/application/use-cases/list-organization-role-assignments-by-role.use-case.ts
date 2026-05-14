import type { OrganizationRoleAssignmentsRepository } from "../../domain/repositories/organization-role-assignments.repository.js";
import type { OrganizationRoleAssignmentOutput } from "../dto/create-organization-role-assignment.dto.js";
import { toOrganizationRoleAssignmentOutput } from "../mappers/organization-role-assignment.mapper.js";

export class ListOrganizationRoleAssignmentsByRoleUseCase {
  constructor(private readonly assignments: OrganizationRoleAssignmentsRepository) {}

  async execute(roleId: number): Promise<OrganizationRoleAssignmentOutput[]> {
    const list = await this.assignments.listByRoleId(roleId);
    return list.map(toOrganizationRoleAssignmentOutput);
  }
}
