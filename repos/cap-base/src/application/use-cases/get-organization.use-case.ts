import type { OrganizationsRepository } from "../../domain/repositories/organizations.repository.js";
import type { OrganizationOutput } from "../dto/create-organization.dto.js";
import { toOrganizationOutput } from "../mappers/organization.mapper.js";

export class GetOrganizationUseCase {
  constructor(private readonly organizations: OrganizationsRepository) {}

  async execute(id: number): Promise<OrganizationOutput | null> {
    const organization = await this.organizations.findById(id);
    return organization ? toOrganizationOutput(organization) : null;
  }
}
