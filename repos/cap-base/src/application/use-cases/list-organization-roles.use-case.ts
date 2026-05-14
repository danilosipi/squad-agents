import type { OrganizationRolesRepository } from "../../domain/repositories/organization-roles.repository.js";
import type { ListOrganizationRolesInput } from "../dto/list-organization-roles.dto.js";
import type { OrganizationRoleOutput } from "../dto/create-organization-role.dto.js";
import { toOrganizationRoleOutput } from "../mappers/organization-role.mapper.js";

export class ListOrganizationRolesUseCase {
  constructor(private readonly roles: OrganizationRolesRepository) {}

  async execute(input?: ListOrganizationRolesInput): Promise<OrganizationRoleOutput[]> {
    const roles = await this.roles.list(input);
    return roles.map(toOrganizationRoleOutput);
  }
}
