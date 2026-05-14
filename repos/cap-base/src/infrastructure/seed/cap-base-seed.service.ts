import {
  INITIAL_ORGANIZATION_ROLES,
  INITIAL_ORGANIZATION_STATUSES,
  INITIAL_ORGANIZATION_TYPES,
  INITIAL_SYSTEM_PARAMETER_SCOPES,
  type SeedNamedReferenceRow,
  type SeedOrganizationRoleRow,
} from "./cap-base-seed-data.js";

export type SeedCounter = { created: number; updated: number; skipped: number };

export type CapBaseSeedResult = {
  organizationRoles: SeedCounter;
  organizationTypes: SeedCounter;
  organizationStatuses: SeedCounter;
  systemParameterScopes: SeedCounter;
};

type NamedRow = { id: number; name: string };

export type OrganizationRoleRow = {
  id: number;
  code: string;
  name: string;
  description: string | null;
  isActive: boolean;
};

export type OrganizationRoleDelegateLike = {
  findUnique(args: { where: { code: string } }): Promise<OrganizationRoleRow | null>;
  upsert(args: {
    where: { code: string };
    create: { code: string; name: string; description?: string | null; isActive: boolean };
    update: { name: string; description?: string | null; isActive: boolean };
  }): Promise<OrganizationRoleRow>;
};

export type NamedReferenceDelegateLike = {
  findFirst(args: { where: { name: string } }): Promise<NamedRow | null>;
  create(args: { data: { name: string } }): Promise<NamedRow>;
};

/**
 * Subconjunto mínimo do Prisma Client usado pelo seed (sem importar `@prisma/client`).
 */
export type CapBasePrismaSeedClientLike = {
  organizationRole: OrganizationRoleDelegateLike;
  organizationType: NamedReferenceDelegateLike;
  organizationStatus: NamedReferenceDelegateLike;
  systemParameterScope: NamedReferenceDelegateLike;
};

function emptyCounter(): SeedCounter {
  return { created: 0, updated: 0, skipped: 0 };
}

function roleContentMatches(existing: OrganizationRoleRow, row: SeedOrganizationRoleRow): boolean {
  return (
    existing.name === row.name &&
    (existing.description ?? null) === (row.description ?? null) &&
    existing.isActive === row.isActive
  );
}

export class CapBaseSeedService {
  constructor(private readonly client: CapBasePrismaSeedClientLike) {}

  async run(): Promise<CapBaseSeedResult> {
    const organizationRoles = await this.seedOrganizationRoles();
    const organizationTypes = await this.seedNamedReferences(
      this.client.organizationType,
      INITIAL_ORGANIZATION_TYPES,
    );
    const organizationStatuses = await this.seedNamedReferences(
      this.client.organizationStatus,
      INITIAL_ORGANIZATION_STATUSES,
    );
    const systemParameterScopes = await this.seedNamedReferences(
      this.client.systemParameterScope,
      INITIAL_SYSTEM_PARAMETER_SCOPES,
    );

    return {
      organizationRoles,
      organizationTypes,
      organizationStatuses,
      systemParameterScopes,
    };
  }

  private async seedOrganizationRoles(): Promise<SeedCounter> {
    const out = emptyCounter();
    for (const row of INITIAL_ORGANIZATION_ROLES) {
      const existing = await this.client.organizationRole.findUnique({ where: { code: row.code } });
      if (!existing) {
        await this.client.organizationRole.upsert({
          where: { code: row.code },
          create: {
            code: row.code,
            name: row.name,
            description: row.description,
            isActive: row.isActive,
          },
          update: {
            name: row.name,
            description: row.description,
            isActive: row.isActive,
          },
        });
        out.created += 1;
        continue;
      }
      if (roleContentMatches(existing, row)) {
        out.skipped += 1;
        continue;
      }
      await this.client.organizationRole.upsert({
        where: { code: row.code },
        create: {
          code: row.code,
          name: row.name,
          description: row.description,
          isActive: row.isActive,
        },
        update: {
          name: row.name,
          description: row.description,
          isActive: row.isActive,
        },
      });
      out.updated += 1;
    }
    return out;
  }

  private async seedNamedReferences(
    delegate: NamedReferenceDelegateLike,
    rows: readonly SeedNamedReferenceRow[],
  ): Promise<SeedCounter> {
    const out = emptyCounter();
    for (const row of rows) {
      const existing = await delegate.findFirst({ where: { name: row.name } });
      if (!existing) {
        await delegate.create({ data: { name: row.name } });
        out.created += 1;
      } else {
        out.skipped += 1;
      }
    }
    return out;
  }
}
