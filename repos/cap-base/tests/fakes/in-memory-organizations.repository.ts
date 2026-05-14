import type {
  ListOrganizationsParams,
  OrganizationsRepository,
} from "../../src/domain/repositories/organizations.repository.js";
import { Organization } from "../../src/domain/entities/organization.entity.js";

/**
 * Repositório em memória para testes (sem Prisma).
 */
export class InMemoryOrganizationsRepository implements OrganizationsRepository {
  private readonly items: Organization[] = [];
  private nextId = 1;

  async findById(id: number): Promise<Organization | null> {
    return this.items.find((o) => o.id === id) ?? null;
  }

  async findByDocumentNumber(documentNumber: string): Promise<Organization | null> {
    const doc = documentNumber.trim();
    return this.items.find((o) => o.documentNumber.trim() === doc) ?? null;
  }

  async list(params?: ListOrganizationsParams): Promise<Organization[]> {
    let result = [...this.items];
    if (params?.isActive !== undefined) {
      result = result.filter((o) => o.isActive === params.isActive);
    }
    if (params?.search !== undefined && params.search.trim() !== "") {
      const q = params.search.trim().toLowerCase();
      result = result.filter((o) => {
        const legal = o.legalName.toLowerCase();
        const trade = o.tradeName?.toLowerCase() ?? "";
        const document = o.documentNumber.toLowerCase();
        return legal.includes(q) || trade.includes(q) || document.includes(q);
      });
    }
    const offset = params?.offset ?? 0;
    const limit = params?.limit;
    if (limit !== undefined && limit >= 0) {
      return result.slice(offset, offset + limit);
    }
    return result.slice(offset);
  }

  async save(organization: Organization): Promise<Organization> {
    if (organization.id === 0) {
      const id = this.nextId++;
      const saved = Organization.create({
        id,
        legalName: organization.legalName,
        tradeName: organization.tradeName,
        documentNumber: organization.documentNumber,
        isActive: organization.isActive,
        createdAt: organization.createdAt,
        updatedAt: organization.updatedAt,
      });
      this.items.push(saved);
      return saved;
    }
    const idx = this.items.findIndex((o) => o.id === organization.id);
    if (idx === -1) {
      this.items.push(organization);
      return organization;
    }
    this.items[idx] = organization;
    return organization;
  }

  async delete(id: number): Promise<void> {
    const idx = this.items.findIndex((o) => o.id === id);
    if (idx !== -1) {
      this.items.splice(idx, 1);
    }
  }
}
