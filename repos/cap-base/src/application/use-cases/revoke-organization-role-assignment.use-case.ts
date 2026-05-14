import type { OrganizationRoleAssignmentsRepository } from "../../domain/repositories/organization-role-assignments.repository.js";
import type { RevokeOrganizationRoleAssignmentInput } from "../dto/revoke-organization-role-assignment.dto.js";
import type { OrganizationRoleAssignmentOutput } from "../dto/create-organization-role-assignment.dto.js";
import { toOrganizationRoleAssignmentOutput } from "../mappers/organization-role-assignment.mapper.js";

export class RevokeOrganizationRoleAssignmentUseCase {
  constructor(private readonly assignments: OrganizationRoleAssignmentsRepository) {}

  async execute(input: RevokeOrganizationRoleAssignmentInput): Promise<OrganizationRoleAssignmentOutput> {
    const assignment = await this.assignments.findById(input.id);
    if (!assignment) {
      throw new Error(`Atribuição de papel com id ${input.id} não encontrada.`);
    }
    assignment.revoke();
    const saved = await this.assignments.save(assignment);
    return toOrganizationRoleAssignmentOutput(saved);
  }
}
