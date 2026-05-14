export const CAP_BASE_MODULE_NAME = "@cap/base";

export type { PrismaCapBaseRepositoriesClientLike } from "./composition/prisma-cap-base-repositories-client.js";
export { createCapBaseModule } from "./composition/create-cap-base-module.js";
export type { CapBaseModule, CapBaseRepositories, CapBaseUseCases } from "./composition/cap-base-module.js";
export { DEFAULT_CAP_BASE_ORGANIZATION_PERSISTENCE } from "./composition/cap-base-module.js";

export { Organization } from "./domain/entities/organization.entity.js";
export { OrganizationRole } from "./domain/entities/organization-role.entity.js";
export { OrganizationRoleAssignment } from "./domain/entities/organization-role-assignment.entity.js";
export { Cnpj } from "./domain/value-objects/cnpj.vo.js";
export { Email } from "./domain/value-objects/email.vo.js";
export { Phone } from "./domain/value-objects/phone.vo.js";

export type { ListOrganizationsParams, OrganizationsRepository } from "./domain/repositories/organizations.repository.js";
export type {
  ListOrganizationRolesParams,
  OrganizationRolesRepository,
} from "./domain/repositories/organization-roles.repository.js";
export type { OrganizationRoleAssignmentsRepository } from "./domain/repositories/organization-role-assignments.repository.js";

export type { CreateOrganizationInput, OrganizationOutput } from "./application/dto/create-organization.dto.js";
export type { UpdateOrganizationInput } from "./application/dto/update-organization.dto.js";
export type { ListOrganizationsInput } from "./application/dto/list-organizations.dto.js";
export type {
  CreateOrganizationRoleInput,
  OrganizationRoleOutput,
} from "./application/dto/create-organization-role.dto.js";
export type { UpdateOrganizationRoleInput } from "./application/dto/update-organization-role.dto.js";
export type { ListOrganizationRolesInput } from "./application/dto/list-organization-roles.dto.js";
export type {
  CreateOrganizationRoleAssignmentInput,
  OrganizationRoleAssignmentOutput,
} from "./application/dto/create-organization-role-assignment.dto.js";
export type { RevokeOrganizationRoleAssignmentInput } from "./application/dto/revoke-organization-role-assignment.dto.js";
export { toOrganizationOutput } from "./application/mappers/organization.mapper.js";
export { toOrganizationRoleOutput } from "./application/mappers/organization-role.mapper.js";
export { toOrganizationRoleAssignmentOutput } from "./application/mappers/organization-role-assignment.mapper.js";
export { CreateOrganizationUseCase } from "./application/use-cases/create-organization.use-case.js";
export { UpdateOrganizationUseCase } from "./application/use-cases/update-organization.use-case.js";
export { GetOrganizationUseCase } from "./application/use-cases/get-organization.use-case.js";
export { ListOrganizationsUseCase } from "./application/use-cases/list-organizations.use-case.js";
export { CreateOrganizationRoleUseCase } from "./application/use-cases/create-organization-role.use-case.js";
export { UpdateOrganizationRoleUseCase } from "./application/use-cases/update-organization-role.use-case.js";
export { GetOrganizationRoleUseCase } from "./application/use-cases/get-organization-role.use-case.js";
export { ListOrganizationRolesUseCase } from "./application/use-cases/list-organization-roles.use-case.js";
export { CreateOrganizationRoleAssignmentUseCase } from "./application/use-cases/create-organization-role-assignment.use-case.js";
export { RevokeOrganizationRoleAssignmentUseCase } from "./application/use-cases/revoke-organization-role-assignment.use-case.js";
export { ListOrganizationRoleAssignmentsByOrganizationUseCase } from "./application/use-cases/list-organization-role-assignments-by-organization.use-case.js";
export { ListOrganizationRoleAssignmentsByRoleUseCase } from "./application/use-cases/list-organization-role-assignments-by-role.use-case.js";
export { PrismaOrganizationsRepository } from "./infrastructure/prisma/prisma-organizations.repository.js";
export type {
  PrismaClientLike,
  PrismaOrganizationDelegate,
  PrismaOrganizationsPersistenceConfig,
} from "./infrastructure/prisma/prisma-organizations.repository.js";
export { PrismaOrganizationRolesRepository } from "./infrastructure/prisma/prisma-organization-roles.repository.js";
export type {
  PrismaOrganizationRoleDelegate,
  PrismaOrganizationRolesClientLike,
} from "./infrastructure/prisma/prisma-organization-roles.repository.js";
export { PrismaOrganizationRoleAssignmentsRepository } from "./infrastructure/prisma/prisma-organization-role-assignments.repository.js";
export type {
  PrismaOrganizationRoleAssignmentDelegate,
  PrismaOrganizationRoleAssignmentsClientLike,
} from "./infrastructure/prisma/prisma-organization-role-assignments.repository.js";
