import type { OrganizationsRepository } from "../../domain/repositories/organizations.repository.js";
import type { ListOrganizationsInput } from "../dto/list-organizations.dto.js";
import type { OrganizationOutput } from "../dto/create-organization.dto.js";
import { toOrganizationOutput } from "../mappers/organization.mapper.js";

export class ListOrganizationsUseCase {
  constructor(private readonly organizations: OrganizationsRepository) {}

  async execute(input?: ListOrganizationsInput): Promise<OrganizationOutput[]> {
    const organizations = await this.organizations.list(input);
    return organizations.map(toOrganizationOutput);
  }
}
