import { describe, expect, beforeAll, afterAll, beforeEach, it } from "vitest";
import { PrismaClient } from "@prisma/client";
import { PrismaOrganizationsRepository } from "../../src/infrastructure/prisma/prisma-organizations.repository.js";
import { PrismaOrganizationRolesRepository } from "../../src/infrastructure/prisma/prisma-organization-roles.repository.js";
import { PrismaOrganizationRoleAssignmentsRepository } from "../../src/infrastructure/prisma/prisma-organization-role-assignments.repository.js";
import { Organization } from "../../src/domain/entities/organization.entity.js";
import { OrganizationRole } from "../../src/domain/entities/organization-role.entity.js";
import { OrganizationRoleAssignment } from "../../src/domain/entities/organization-role-assignment.entity.js";
import {
  createCapBaseIntegrationPrismaClient,
  ensureOrganizationReferenceRows,
  getCapBaseIntegrationDatabaseUrl,
  resetCapBaseIntegrationTables,
  type IntegrationOrgPersistenceIds,
} from "./prisma-test-client.js";

const integrationUrl = getCapBaseIntegrationDatabaseUrl();

describe.skipIf(!integrationUrl)(
  "Prisma repositories (integração PostgreSQL — defina CAP_BASE_INTEGRATION_DATABASE_URL)",
  () => {
    let prisma: PrismaClient;
    let persistence: IntegrationOrgPersistenceIds;
    let orgRepo: PrismaOrganizationsRepository;
    let rolesRepo: PrismaOrganizationRolesRepository;
    let assignmentsRepo: PrismaOrganizationRoleAssignmentsRepository;

    beforeAll(async () => {
      prisma = createCapBaseIntegrationPrismaClient();
      await prisma.$connect();
    });

    afterAll(async () => {
      await prisma.$disconnect();
    });

    beforeEach(async () => {
      await resetCapBaseIntegrationTables(prisma);
      persistence = await ensureOrganizationReferenceRows(prisma);
      orgRepo = new PrismaOrganizationsRepository(prisma, {
        defaultTypeId: persistence.typeId,
        activeStatusId: persistence.activeStatusId,
        inactiveStatusId: persistence.inactiveStatusId,
      });
      rolesRepo = new PrismaOrganizationRolesRepository(prisma);
      assignmentsRepo = new PrismaOrganizationRoleAssignmentsRepository(prisma);
    });

    it("fluxo mínimo: role → organization → assignment → leituras → revogação persistida", async () => {
      const role = OrganizationRole.create({
        id: 0,
        code: "INT_TEST_ADMIN",
        name: "Administrador integração",
        description: "Criado pelo teste integrado",
      });
      const savedRole = await rolesRepo.save(role);
      expect(savedRole.id).toBeGreaterThan(0);

      const organization = Organization.create({
        id: 0,
        legalName: "Empresa Integração LTDA",
        tradeName: "Integração",
        documentNumber: "11222333000181",
      });
      const savedOrg = await orgRepo.save(organization);
      expect(savedOrg.id).toBeGreaterThan(0);

      const assignment = OrganizationRoleAssignment.create({
        id: 0,
        organizationId: savedOrg.id,
        roleId: savedRole.id,
      });
      const savedAssignment = await assignmentsRepo.save(assignment);
      expect(savedAssignment.id).toBeGreaterThan(0);
      expect(savedAssignment.isActive).toBe(true);

      const orgById = await orgRepo.findById(savedOrg.id);
      expect(orgById).not.toBeNull();
      expect(orgById!.documentNumber).toBe("11222333000181");

      const roleByCode = await rolesRepo.findByCode("INT_TEST_ADMIN");
      expect(roleByCode).not.toBeNull();
      expect(roleByCode!.id).toBe(savedRole.id);

      const byOrg = await assignmentsRepo.listByOrganizationId(savedOrg.id);
      expect(byOrg).toHaveLength(1);
      expect(byOrg[0]!.roleId).toBe(savedRole.id);

      const toRevoke = await assignmentsRepo.findById(savedAssignment.id);
      expect(toRevoke).not.toBeNull();
      toRevoke!.revoke();
      const afterRevoke = await assignmentsRepo.save(toRevoke!);
      expect(afterRevoke.isActive).toBe(false);
      expect(afterRevoke.revokedAt).toBeInstanceOf(Date);

      const fromDb = await prisma.organizationRoleAssignment.findUnique({
        where: { id: savedAssignment.id },
      });
      expect(fromDb?.isActive).toBe(false);
      expect(fromDb?.revokedAt).not.toBeNull();
    });
});
