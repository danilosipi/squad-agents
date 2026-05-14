import type { OrganizationsRepository } from "../domain/repositories/organizations.repository.js";
import type { OrganizationRolesRepository } from "../domain/repositories/organization-roles.repository.js";
import type { OrganizationRoleAssignmentsRepository } from "../domain/repositories/organization-role-assignments.repository.js";
import type { PrismaOrganizationsPersistenceConfig } from "../infrastructure/prisma/prisma-organizations.repository.js";
import type { CreateOrganizationUseCase } from "../application/use-cases/create-organization.use-case.js";
import type { UpdateOrganizationUseCase } from "../application/use-cases/update-organization.use-case.js";
import type { GetOrganizationUseCase } from "../application/use-cases/get-organization.use-case.js";
import type { ListOrganizationsUseCase } from "../application/use-cases/list-organizations.use-case.js";
import type { CreateOrganizationRoleUseCase } from "../application/use-cases/create-organization-role.use-case.js";
import type { UpdateOrganizationRoleUseCase } from "../application/use-cases/update-organization-role.use-case.js";
import type { GetOrganizationRoleUseCase } from "../application/use-cases/get-organization-role.use-case.js";
import type { ListOrganizationRolesUseCase } from "../application/use-cases/list-organization-roles.use-case.js";
import type { CreateOrganizationRoleAssignmentUseCase } from "../application/use-cases/create-organization-role-assignment.use-case.js";
import type { RevokeOrganizationRoleAssignmentUseCase } from "../application/use-cases/revoke-organization-role-assignment.use-case.js";
import type { ListOrganizationRoleAssignmentsByOrganizationUseCase } from "../application/use-cases/list-organization-role-assignments-by-organization.use-case.js";
import type { ListOrganizationRoleAssignmentsByRoleUseCase } from "../application/use-cases/list-organization-role-assignments-by-role.use-case.js";

export type CapBaseRepositories = {
  organizations: OrganizationsRepository;
  organizationRoles: OrganizationRolesRepository;
  organizationRoleAssignments: OrganizationRoleAssignmentsRepository;
};

export type CapBaseUseCases = {
  createOrganization: CreateOrganizationUseCase;
  updateOrganization: UpdateOrganizationUseCase;
  getOrganization: GetOrganizationUseCase;
  listOrganizations: ListOrganizationsUseCase;
  createOrganizationRole: CreateOrganizationRoleUseCase;
  updateOrganizationRole: UpdateOrganizationRoleUseCase;
  getOrganizationRole: GetOrganizationRoleUseCase;
  listOrganizationRoles: ListOrganizationRolesUseCase;
  createOrganizationRoleAssignment: CreateOrganizationRoleAssignmentUseCase;
  revokeOrganizationRoleAssignment: RevokeOrganizationRoleAssignmentUseCase;
  listOrganizationRoleAssignmentsByOrganization: ListOrganizationRoleAssignmentsByOrganizationUseCase;
  listOrganizationRoleAssignmentsByRole: ListOrganizationRoleAssignmentsByRoleUseCase;
};

export type CapBaseModule = {
  repositories: CapBaseRepositories;
  useCases: CapBaseUseCases;
};

/**
 * FKs padrão para `Organization` ao usar {@link createCapBaseModule} sem configuração extra.
 * Devem corresponder a linhas reais de `OrganizationType` / `OrganizationStatus` na base alvo.
 */
export const DEFAULT_CAP_BASE_ORGANIZATION_PERSISTENCE: PrismaOrganizationsPersistenceConfig = {
  defaultTypeId: 1,
  activeStatusId: 10,
  inactiveStatusId: 20,
};
