import type { OrganizationsRepository } from "../../domain/repositories/organizations.repository.js";
import type { OrganizationRolesRepository } from "../../domain/repositories/organization-roles.repository.js";
import type { OrganizationRoleAssignmentsRepository } from "../../domain/repositories/organization-role-assignments.repository.js";
import { OrganizationRoleAssignment } from "../../domain/entities/organization-role-assignment.entity.js";
import type {
  CreateOrganizationRoleAssignmentInput,
  OrganizationRoleAssignmentOutput,
} from "../dto/create-organization-role-assignment.dto.js";
import { toOrganizationRoleAssignmentOutput } from "../mappers/organization-role-assignment.mapper.js";

export class CreateOrganizationRoleAssignmentUseCase {
  constructor(
    private readonly assignments: OrganizationRoleAssignmentsRepository,
    private readonly organizations: OrganizationsRepository,
    private readonly roles: OrganizationRolesRepository,
  ) {}

  async execute(input: CreateOrganizationRoleAssignmentInput): Promise<OrganizationRoleAssignmentOutput> {
    const organization = await this.organizations.findById(input.organizationId);
    if (!organization) {
      throw new Error(`Organização com id ${input.organizationId} não encontrada.`);
    }
    const role = await this.roles.findById(input.roleId);
    if (!role) {
      throw new Error(`Papel organizacional com id ${input.roleId} não encontrado.`);
    }
    const existingForOrg = await this.assignments.listByOrganizationId(input.organizationId);
    const activeDuplicate = existingForOrg.find((a) => a.isActive && a.roleId === input.roleId);
    if (activeDuplicate) {
      throw new Error(
        `Já existe vínculo ativo entre a organização ${input.organizationId} e o papel ${input.roleId}.`,
      );
    }
    const assignment = OrganizationRoleAssignment.create({
      id: 0,
      organizationId: input.organizationId,
      roleId: input.roleId,
    });
    const saved = await this.assignments.save(assignment);
    return toOrganizationRoleAssignmentOutput(saved);
  }
}
