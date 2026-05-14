import type { Organization } from "../entities/organization.entity.js";

export type ListOrganizationsParams = {
  search?: string;
  isActive?: boolean;
  limit?: number;
  offset?: number;
};

/**
 * Contrato de persistência para {@link Organization} (sem implementação).
 */
export interface OrganizationsRepository {
  findById(id: number): Promise<Organization | null>;
  findByDocumentNumber(documentNumber: string): Promise<Organization | null>;
  list(params?: ListOrganizationsParams): Promise<Organization[]>;
  save(organization: Organization): Promise<Organization>;
  delete(id: number): Promise<void>;
}
