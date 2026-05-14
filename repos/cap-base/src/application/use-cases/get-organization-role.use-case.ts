import type { OrganizationRolesRepository } from "../../domain/repositories/organization-roles.repository.js";
import type { OrganizationRoleOutput } from "../dto/create-organization-role.dto.js";
import { toOrganizationRoleOutput } from "../mappers/organization-role.mapper.js";

export class GetOrganizationRoleUseCase {
  constructor(private readonly roles: OrganizationRolesRepository) {}

  async execute(id: number): Promise<OrganizationRoleOutput | null> {
    const role = await this.roles.findById(id);
    return role ? toOrganizationRoleOutput(role) : null;
  }
}
