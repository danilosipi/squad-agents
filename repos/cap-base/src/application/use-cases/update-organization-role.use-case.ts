import type { OrganizationRolesRepository } from "../../domain/repositories/organization-roles.repository.js";
import type { UpdateOrganizationRoleInput } from "../dto/update-organization-role.dto.js";
import type { OrganizationRoleOutput } from "../dto/create-organization-role.dto.js";
import { toOrganizationRoleOutput } from "../mappers/organization-role.mapper.js";

export class UpdateOrganizationRoleUseCase {
  constructor(private readonly roles: OrganizationRolesRepository) {}

  async execute(input: UpdateOrganizationRoleInput): Promise<OrganizationRoleOutput> {
    const role = await this.roles.findById(input.id);
    if (!role) {
      throw new Error(`Papel organizacional com id ${input.id} não encontrado.`);
    }
    if (input.code !== undefined) {
      const code = input.code.trim();
      if (!code) {
        throw new Error("code não pode ser vazio.");
      }
      const other = await this.roles.findByCode(code);
      if (other && other.id !== input.id) {
        throw new Error(`Já existe outro papel organizacional com o code "${code}".`);
      }
    }
    role.updateBasicInfo({
      code: input.code,
      name: input.name,
      description: input.description,
    });
    const saved = await this.roles.save(role);
    return toOrganizationRoleOutput(saved);
  }
}
