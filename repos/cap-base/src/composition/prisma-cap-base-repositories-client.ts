import type { PrismaClientLike } from "../infrastructure/prisma/prisma-organizations.repository.js";
import type { PrismaOrganizationRolesClientLike } from "../infrastructure/prisma/prisma-organization-roles.repository.js";
import type { PrismaOrganizationRoleAssignmentsClientLike } from "../infrastructure/prisma/prisma-organization-role-assignments.repository.js";

/** Cliente Prisma mínimo para os três repositórios CAP-BASE expostos no composition root. */
export type PrismaCapBaseRepositoriesClientLike = PrismaClientLike &
  PrismaOrganizationRolesClientLike &
  PrismaOrganizationRoleAssignmentsClientLike;
