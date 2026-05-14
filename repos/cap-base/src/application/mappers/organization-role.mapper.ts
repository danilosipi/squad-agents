import type { OrganizationRole } from "../../domain/entities/organization-role.entity.js";
import type { OrganizationRoleOutput } from "../dto/create-organization-role.dto.js";

export function toOrganizationRoleOutput(role: OrganizationRole): OrganizationRoleOutput {
  return {
    id: role.id,
    code: role.code,
    name: role.name,
    description: role.description,
    isActive: role.isActive,
  };
}
