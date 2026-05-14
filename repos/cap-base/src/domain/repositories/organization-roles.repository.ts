import type { OrganizationRole } from "../entities/organization-role.entity.js";

export type ListOrganizationRolesParams = {
  search?: string;
  isActive?: boolean;
  limit?: number;
  offset?: number;
};

/**
 * Contrato de persistência para {@link OrganizationRole} (sem implementação).
 */
export interface OrganizationRolesRepository {
  findById(id: number): Promise<OrganizationRole | null>;
  findByCode(code: string): Promise<OrganizationRole | null>;
  list(params?: ListOrganizationRolesParams): Promise<OrganizationRole[]>;
  save(role: OrganizationRole): Promise<OrganizationRole>;
}
