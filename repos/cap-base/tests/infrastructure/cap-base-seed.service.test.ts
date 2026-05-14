import { describe, expect, it } from "vitest";
import { INITIAL_ORGANIZATION_ROLES } from "../../src/infrastructure/seed/cap-base-seed-data.js";
import {
  CapBaseSeedService,
  type CapBasePrismaSeedClientLike,
  type OrganizationRoleRow,
} from "../../src/infrastructure/seed/cap-base-seed.service.js";

type NamedRow = { id: number; name: string };

function createFakeSeedClient(): CapBasePrismaSeedClientLike {
  const organizationRoles: OrganizationRoleRow[] = [];
  let roleNextId = 1;

  const organizationTypes: NamedRow[] = [];
  const organizationStatuses: NamedRow[] = [];
  const systemParameterScopes: NamedRow[] = [];
  let namedNextId = 1;

  function makeNamedDelegate(store: NamedRow[]) {
    return {
      async findFirst(args: { where: { name: string } }): Promise<NamedRow | null> {
        const n = args.where.name;
        return store.find((r) => r.name === n) ?? null;
      },
      async create(args: { data: { name: string } }): Promise<NamedRow> {
        const row: NamedRow = { id: namedNextId++, name: args.data.name };
        store.push(row);
        return row;
      },
    };
  }

  return {
    organizationRole: {
      async findUnique(args: { where: { code: string } }): Promise<OrganizationRoleRow | null> {
        const c = args.where.code;
        return organizationRoles.find((r) => r.code === c) ?? null;
      },
      async upsert(args: {
        where: { code: string };
        create: { code: string; name: string; description?: string | null; isActive: boolean };
        update: { name: string; description?: string | null; isActive: boolean };
      }): Promise<OrganizationRoleRow> {
        const idx = organizationRoles.findIndex((r) => r.code === args.where.code);
        if (idx === -1) {
          const row: OrganizationRoleRow = {
            id: roleNextId++,
            code: args.create.code,
            name: args.create.name,
            description: args.create.description ?? null,
            isActive: args.create.isActive,
          };
          organizationRoles.push(row);
          return row;
        }
        const prev = organizationRoles[idx]!;
        const row: OrganizationRoleRow = {
          ...prev,
          name: args.update.name,
          description: args.update.description ?? null,
          isActive: args.update.isActive,
        };
        organizationRoles[idx] = row;
        return row;
      },
    },
    organizationType: makeNamedDelegate(organizationTypes),
    organizationStatus: makeNamedDelegate(organizationStatuses),
    systemParameterScope: makeNamedDelegate(systemParameterScopes),
  };
}

describe("CapBaseSeedService", () => {
  it("cria papéis iniciais quando não existem", async () => {
    const prisma = createFakeSeedClient();
    const sut = new CapBaseSeedService(prisma);
    const result = await sut.run();
    expect(result.organizationRoles.created).toBe(INITIAL_ORGANIZATION_ROLES.length);
    expect(result.organizationRoles.updated).toBe(0);
    expect(result.organizationRoles.skipped).toBe(0);
    expect(result.organizationTypes.created).toBe(2);
    expect(result.organizationStatuses.created).toBe(2);
    expect(result.systemParameterScopes.created).toBe(2);
  });

  it("não duplica papéis ao rodar duas vezes e incrementa skipped", async () => {
    const prisma = createFakeSeedClient();
    const sut = new CapBaseSeedService(prisma);
    const first = await sut.run();
    const second = await sut.run();
    expect(first.organizationRoles.created).toBe(INITIAL_ORGANIZATION_ROLES.length);
    expect(second.organizationRoles.created).toBe(0);
    expect(second.organizationRoles.skipped).toBe(INITIAL_ORGANIZATION_ROLES.length);
    expect(second.organizationRoles.updated).toBe(0);
  });

  it("atualiza nome/descrição quando o código já existe e o conteúdo diverge", async () => {
    const prisma = createFakeSeedClient();
    const sut = new CapBaseSeedService(prisma);
    await sut.run();
    const broker = await prisma.organizationRole.findUnique({ where: { code: "BROKER" } });
    expect(broker).not.toBeNull();
    broker!.name = "Nome antigo";
    broker!.description = "desc antiga";

    const second = await sut.run();
    expect(second.organizationRoles.updated).toBeGreaterThanOrEqual(1);
    const fixed = await prisma.organizationRole.findUnique({ where: { code: "BROKER" } });
    expect(fixed).toMatchObject({
      name: "Corretora",
      description: "Intermediária na colocação ou gestão de relações comerciais.",
    });
  });

  it("retorna contadores coerentes para referências nomeadas na segunda execução", async () => {
    const prisma = createFakeSeedClient();
    const sut = new CapBaseSeedService(prisma);
    await sut.run();
    const second = await sut.run();
    expect(second.organizationTypes.skipped).toBe(2);
    expect(second.organizationTypes.created).toBe(0);
    expect(second.organizationStatuses.skipped).toBe(2);
    expect(second.systemParameterScopes.skipped).toBe(2);
  });
});
