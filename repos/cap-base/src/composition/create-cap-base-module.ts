import { PrismaOrganizationsRepository } from "../infrastructure/prisma/prisma-organizations.repository.js";
import { PrismaOrganizationRolesRepository } from "../infrastructure/prisma/prisma-organization-roles.repository.js";
import { PrismaOrganizationRoleAssignmentsRepository } from "../infrastructure/prisma/prisma-organization-role-assignments.repository.js";
import { CreateOrganizationUseCase } from "../application/use-cases/create-organization.use-case.js";
import { UpdateOrganizationUseCase } from "../application/use-cases/update-organization.use-case.js";
import { GetOrganizationUseCase } from "../application/use-cases/get-organization.use-case.js";
import { ListOrganizationsUseCase } from "../application/use-cases/list-organizations.use-case.js";
import { CreateOrganizationRoleUseCase } from "../application/use-cases/create-organization-role.use-case.js";
import { UpdateOrganizationRoleUseCase } from "../application/use-cases/update-organization-role.use-case.js";
import { GetOrganizationRoleUseCase } from "../application/use-cases/get-organization-role.use-case.js";
import { ListOrganizationRolesUseCase } from "../application/use-cases/list-organization-roles.use-case.js";
import { CreateOrganizationRoleAssignmentUseCase } from "../application/use-cases/create-organization-role-assignment.use-case.js";
import { RevokeOrganizationRoleAssignmentUseCase } from "../application/use-cases/revoke-organization-role-assignment.use-case.js";
import { ListOrganizationRoleAssignmentsByOrganizationUseCase } from "../application/use-cases/list-organization-role-assignments-by-organization.use-case.js";
import { ListOrganizationRoleAssignmentsByRoleUseCase } from "../application/use-cases/list-organization-role-assignments-by-role.use-case.js";
import type { PrismaCapBaseRepositoriesClientLike } from "./prisma-cap-base-repositories-client.js";
import { DEFAULT_CAP_BASE_ORGANIZATION_PERSISTENCE, type CapBaseModule } from "./cap-base-module.js";

/**
 * Composition root: monta repositórios Prisma e casos de uso a partir de um cliente Prisma-like.
 * Não instancia `PrismaClient` — o caller fornece o client (real ou fake).
 */
export function createCapBaseModule(client: PrismaCapBaseRepositoriesClientLike): CapBaseModule {
  const organizations = new PrismaOrganizationsRepository(client, DEFAULT_CAP_BASE_ORGANIZATION_PERSISTENCE);
  const organizationRoles = new PrismaOrganizationRolesRepository(client);
  const organizationRoleAssignments = new PrismaOrganizationRoleAssignmentsRepository(client);

  return {
    repositories: {
      organizations,
      organizationRoles,
      organizationRoleAssignments,
    },
    useCases: {
      createOrganization: new CreateOrganizationUseCase(organizations),
      updateOrganization: new UpdateOrganizationUseCase(organizations),
      getOrganization: new GetOrganizationUseCase(organizations),
      listOrganizations: new ListOrganizationsUseCase(organizations),
      createOrganizationRole: new CreateOrganizationRoleUseCase(organizationRoles),
      updateOrganizationRole: new UpdateOrganizationRoleUseCase(organizationRoles),
      getOrganizationRole: new GetOrganizationRoleUseCase(organizationRoles),
      listOrganizationRoles: new ListOrganizationRolesUseCase(organizationRoles),
      createOrganizationRoleAssignment: new CreateOrganizationRoleAssignmentUseCase(
        organizationRoleAssignments,
        organizations,
        organizationRoles,
      ),
      revokeOrganizationRoleAssignment: new RevokeOrganizationRoleAssignmentUseCase(organizationRoleAssignments),
      listOrganizationRoleAssignmentsByOrganization: new ListOrganizationRoleAssignmentsByOrganizationUseCase(
        organizationRoleAssignments,
      ),
      listOrganizationRoleAssignmentsByRole: new ListOrganizationRoleAssignmentsByRoleUseCase(
        organizationRoleAssignments,
      ),
    },
  };
}
