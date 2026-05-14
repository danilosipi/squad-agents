import type { Organization } from "../../domain/entities/organization.entity.js";
import type { OrganizationOutput } from "../dto/create-organization.dto.js";

export function toOrganizationOutput(organization: Organization): OrganizationOutput {
  return {
    id: organization.id,
    legalName: organization.legalName,
    tradeName: organization.tradeName,
    documentNumber: organization.documentNumber,
    isActive: organization.isActive,
    createdAt: organization.createdAt,
    updatedAt: organization.updatedAt,
  };
}
