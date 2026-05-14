import type {
  ListOrganizationRolesParams,
  OrganizationRolesRepository,
} from "../../src/domain/repositories/organization-roles.repository.js";
import { OrganizationRole } from "../../src/domain/entities/organization-role.entity.js";

/**
 * Repositório em memória para testes (sem Prisma).
 */
export class InMemoryOrganizationRolesRepository implements OrganizationRolesRepository {
  private readonly items: OrganizationRole[] = [];
  private nextId = 1;

  async findById(id: number): Promise<OrganizationRole | null> {
    return this.items.find((r) => r.id === id) ?? null;
  }

  async findByCode(code: string): Promise<OrganizationRole | null> {
    const c = code.trim();
    return this.items.find((r) => r.code.trim() === c) ?? null;
  }

  async list(params?: ListOrganizationRolesParams): Promise<OrganizationRole[]> {
    let result = [...this.items].sort((a, b) => a.id - b.id);
    if (params?.isActive !== undefined) {
      result = result.filter((r) => r.isActive === params.isActive);
    }
    const search = params?.search?.trim();
    if (search) {
      const q = search.toLowerCase();
      result = result.filter((r) => {
        const code = r.code.toLowerCase();
        const name = r.name.toLowerCase();
        const desc = r.description?.toLowerCase() ?? "";
        return code.includes(q) || name.includes(q) || desc.includes(q);
      });
    }
    const offset = params?.offset ?? 0;
    const limit = params?.limit;
    if (limit !== undefined && limit >= 0) {
      return result.slice(offset, offset + limit);
    }
    return result.slice(offset);
  }

  async save(role: OrganizationRole): Promise<OrganizationRole> {
    if (role.id === 0) {
      const id = this.nextId++;
      const saved = OrganizationRole.create({
        id,
        code: role.code,
        name: role.name,
        description: role.description,
        isActive: role.isActive,
      });
      this.items.push(saved);
      return saved;
    }
    const idx = this.items.findIndex((r) => r.id === role.id);
    if (idx === -1) {
      this.items.push(role);
      return role;
    }
    this.items[idx] = role;
    return role;
  }
}
