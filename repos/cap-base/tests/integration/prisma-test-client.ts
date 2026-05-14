import { PrismaClient } from "@prisma/client";

/**
 * URL dedicada a testes integrados (PostgreSQL).
 * Nunca use `DATABASE_URL` de produção aqui.
 */
export function getCapBaseIntegrationDatabaseUrl(): string | undefined {
  const url = process.env.CAP_BASE_INTEGRATION_DATABASE_URL?.trim();
  return url && url.length > 0 ? url : undefined;
}

export function createCapBaseIntegrationPrismaClient(): PrismaClient {
  const url = getCapBaseIntegrationDatabaseUrl();
  if (!url) {
    throw new Error("CAP_BASE_INTEGRATION_DATABASE_URL não definida.");
  }
  return new PrismaClient({
    datasources: {
      db: { url },
    },
    log: process.env.CAP_BASE_INTEGRATION_PRISMA_LOG === "1" ? ["query", "error"] : ["error"],
  });
}

/**
 * Remove dados de negócio usados pelos testes integrados (mantém tipos/status de referência).
 * Exige PostgreSQL com schema aplicado (`migrate dev` / `migrate deploy` ou `db push` apenas em base de teste).
 */
export async function resetCapBaseIntegrationTables(prisma: PrismaClient): Promise<void> {
  await prisma.$executeRawUnsafe(
    `TRUNCATE TABLE
      "OrganizationRoleAssignment",
      "UserOrganization",
      "Organization",
      "OrganizationRole"
    RESTART IDENTITY CASCADE`,
  );
}

export type IntegrationOrgPersistenceIds = {
  typeId: number;
  activeStatusId: number;
  inactiveStatusId: number;
};

/**
 * Garante linhas mínimas para FKs obrigatórios de `Organization` no schema CAP-BASE.
 */
export async function ensureOrganizationReferenceRows(
  prisma: PrismaClient,
): Promise<IntegrationOrgPersistenceIds> {
  const typeName = "__cap_base_integration_org_type__";
  let type = await prisma.organizationType.findFirst({ where: { name: typeName } });
  if (!type) {
    type = await prisma.organizationType.create({ data: { name: typeName } });
  }
  const activeName = "__cap_base_integration_status_active__";
  const inactiveName = "__cap_base_integration_status_inactive__";
  let active = await prisma.organizationStatus.findFirst({ where: { name: activeName } });
  if (!active) {
    active = await prisma.organizationStatus.create({ data: { name: activeName } });
  }
  let inactive = await prisma.organizationStatus.findFirst({ where: { name: inactiveName } });
  if (!inactive) {
    inactive = await prisma.organizationStatus.create({ data: { name: inactiveName } });
  }
  return { typeId: type.id, activeStatusId: active.id, inactiveStatusId: inactive.id };
}
