import type { OrganizationRolesRepository } from "../../domain/repositories/organization-roles.repository.js";
import { OrganizationRole } from "../../domain/entities/organization-role.entity.js";
import type { CreateOrganizationRoleInput, OrganizationRoleOutput } from "../dto/create-organization-role.dto.js";
import { toOrganizationRoleOutput } from "../mappers/organization-role.mapper.js";

export class CreateOrganizationRoleUseCase {
  constructor(private readonly roles: OrganizationRolesRepository) {}

  async execute(input: CreateOrganizationRoleInput): Promise<OrganizationRoleOutput> {
    const code = input.code.trim();
    if (!code) {
      throw new Error("code é obrigatório.");
    }
    const name = input.name.trim();
    if (!name) {
      throw new Error("name é obrigatório.");
    }
    const existing = await this.roles.findByCode(code);
    if (existing) {
      throw new Error(`Já existe papel organizacional com o code "${code}".`);
    }
    const role = OrganizationRole.create({
      id: 0,
      code,
      name,
      description: input.description,
    });
    const saved = await this.roles.save(role);
    return toOrganizationRoleOutput(saved);
  }
}
