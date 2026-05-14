/**
 * Dados fundacionais do CAP-BASE para seed idempotente (referência estática).
 * Chaves naturais: `OrganizationRole.code`; `name` nas tabelas de referência só com `name`.
 */

export type SeedOrganizationRoleRow = {
  code: string;
  name: string;
  description: string | null;
  isActive: boolean;
};

export type SeedNamedReferenceRow = {
  /** Valor canónico persistido em `name` (ex.: LEGAL_ENTITY). */
  name: string;
};

/** Papéis de organização no ecossistema de capitalização. */
export const INITIAL_ORGANIZATION_ROLES: readonly SeedOrganizationRoleRow[] = [
  {
    code: "CAPITALIZATION_COMPANY",
    name: "Empresa de capitalização",
    description: "Instituição autorizada a operar planos de capitalização.",
    isActive: true,
  },
  {
    code: "PROMOTER_COMPANY",
    name: "Empresa promotora",
    description: "Organização que promove a constituição ou comercialização de grupos/planos.",
    isActive: true,
  },
  {
    code: "DISTRIBUTOR",
    name: "Distribuidora",
    description: "Canal de distribuição de produtos de capitalização.",
    isActive: true,
  },
  {
    code: "BROKER",
    name: "Corretora",
    description: "Intermediária na colocação ou gestão de relações comerciais.",
    isActive: true,
  },
  {
    code: "SERVICE_PROVIDER",
    name: "Prestador de serviço",
    description: "Fornecedor de serviços de suporte ao ecossistema (não necessariamente distribuidor).",
    isActive: true,
  },
  {
    code: "BENEFICENT_ENTITY",
    name: "Entidade beneficente",
    description: "Entidade sem fins lucrativos ou fins sociais elegíveis em sorteios/doações.",
    isActive: true,
  },
];

/** Tipos de organização (campo `name` no schema; chave natural = texto canónico). */
export const INITIAL_ORGANIZATION_TYPES: readonly SeedNamedReferenceRow[] = [
  { name: "LEGAL_ENTITY" },
  { name: "INDIVIDUAL" },
];

/** Estados de organização referenciados por `Organization.statusId`. */
export const INITIAL_ORGANIZATION_STATUSES: readonly SeedNamedReferenceRow[] = [
  { name: "ACTIVE" },
  { name: "INACTIVE" },
];

/** Alias do requisito da fase (`INITIAL_STATUSES`) — mesmo conteúdo que `INITIAL_ORGANIZATION_STATUSES`. */
export const INITIAL_STATUSES: readonly SeedNamedReferenceRow[] = INITIAL_ORGANIZATION_STATUSES;

/** Escopos de parâmetro de sistema para `SystemParameter.scopeId`. */
export const INITIAL_SYSTEM_PARAMETER_SCOPES: readonly SeedNamedReferenceRow[] = [
  { name: "GLOBAL" },
  { name: "ORGANIZATION" },
];
