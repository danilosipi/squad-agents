import type { OrganizationsRepository } from "../../domain/repositories/organizations.repository.js";
import { Organization } from "../../domain/entities/organization.entity.js";
import type { CreateOrganizationInput, OrganizationOutput } from "../dto/create-organization.dto.js";
import { toOrganizationOutput } from "../mappers/organization.mapper.js";

export class CreateOrganizationUseCase {
  constructor(private readonly organizations: OrganizationsRepository) {}

  async execute(input: CreateOrganizationInput): Promise<OrganizationOutput> {
    const doc = input.documentNumber.trim();
    if (!doc) {
      throw new Error("documentNumber é obrigatório.");
    }
    const existing = await this.organizations.findByDocumentNumber(doc);
    if (existing) {
      throw new Error(`Já existe organização com o documentNumber "${doc}".`);
    }
    const organization = Organization.create({
      id: 0,
      legalName: input.legalName,
      tradeName: input.tradeName,
      documentNumber: input.documentNumber,
    });
    const saved = await this.organizations.save(organization);
    return toOrganizationOutput(saved);
  }
}
