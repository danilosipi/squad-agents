import type { OrganizationsRepository } from "../../domain/repositories/organizations.repository.js";
import type { UpdateOrganizationInput } from "../dto/update-organization.dto.js";
import type { OrganizationOutput } from "../dto/create-organization.dto.js";
import { toOrganizationOutput } from "../mappers/organization.mapper.js";

export class UpdateOrganizationUseCase {
  constructor(private readonly organizations: OrganizationsRepository) {}

  async execute(input: UpdateOrganizationInput): Promise<OrganizationOutput> {
    const organization = await this.organizations.findById(input.id);
    if (!organization) {
      throw new Error(`Organização com id ${input.id} não encontrada.`);
    }
    if (input.documentNumber !== undefined) {
      const doc = input.documentNumber.trim();
      if (!doc) {
        throw new Error("documentNumber não pode ser vazio.");
      }
      const other = await this.organizations.findByDocumentNumber(doc);
      if (other && other.id !== input.id) {
        throw new Error(`Já existe outra organização com o documentNumber "${doc}".`);
      }
    }
    organization.updateBasicInfo({
      legalName: input.legalName,
      tradeName: input.tradeName,
      documentNumber: input.documentNumber,
    });
    const saved = await this.organizations.save(organization);
    return toOrganizationOutput(saved);
  }
}
