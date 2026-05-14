import { describe, expect, it } from "vitest";
import { CreateOrganizationUseCase } from "../../src/application/use-cases/create-organization.use-case.js";
import { CreateOrganizationRoleUseCase } from "../../src/application/use-cases/create-organization-role.use-case.js";
import { CreateOrganizationRoleAssignmentUseCase } from "../../src/application/use-cases/create-organization-role-assignment.use-case.js";
import { RevokeOrganizationRoleAssignmentUseCase } from "../../src/application/use-cases/revoke-organization-role-assignment.use-case.js";
import { ListOrganizationRoleAssignmentsByOrganizationUseCase } from "../../src/application/use-cases/list-organization-role-assignments-by-organization.use-case.js";
import { ListOrganizationRoleAssignmentsByRoleUseCase } from "../../src/application/use-cases/list-organization-role-assignments-by-role.use-case.js";
import { InMemoryOrganizationsRepository } from "../fakes/in-memory-organizations.repository.js";
import { InMemoryOrganizationRolesRepository } from "../fakes/in-memory-organization-roles.repository.js";
import { InMemoryOrganizationRoleAssignmentsRepository } from "../fakes/in-memory-organization-role-assignments.repository.js";

describe("OrganizationRoleAssignment use cases", () => {
  async function seedOrgAndRole() {
    const orgRepo = new InMemoryOrganizationsRepository();
    const roleRepo = new InMemoryOrganizationRolesRepository();
    const assignmentRepo = new InMemoryOrganizationRoleAssignmentsRepository();
    const createOrg = new CreateOrganizationUseCase(orgRepo);
    const createRole = new CreateOrganizationRoleUseCase(roleRepo);
    const org = await createOrg.execute({
      legalName: "ACME",
      documentNumber: "12345678000195",
    });
    const role = await createRole.execute({ code: "R1", name: "Papel 1" });
    return { orgRepo, roleRepo, assignmentRepo, org, role };
  }

  it("CreateOrganizationRoleAssignmentUseCase cria vínculo", async () => {
    const { orgRepo, roleRepo, assignmentRepo, org, role } = await seedOrgAndRole();
    const useCase = new CreateOrganizationRoleAssignmentUseCase(assignmentRepo, orgRepo, roleRepo);
    const out = await useCase.execute({ organizationId: org.id, roleId: role.id });
    expect(out.id).toBeGreaterThan(0);
    expect(out.organizationId).toBe(org.id);
    expect(out.roleId).toBe(role.id);
    expect(out.isActive).toBe(true);
    expect(out.assignedAt).toBeInstanceOf(Date);
  });

  it("CreateOrganizationRoleAssignmentUseCase falha se organization não existir", async () => {
    const orgRepo = new InMemoryOrganizationsRepository();
    const roleRepo = new InMemoryOrganizationRolesRepository();
    const assignmentRepo = new InMemoryOrganizationRoleAssignmentsRepository();
    const createRole = new CreateOrganizationRoleUseCase(roleRepo);
    const role = await createRole.execute({ code: "ORF", name: "Só papel" });
    const useCase = new CreateOrganizationRoleAssignmentUseCase(assignmentRepo, orgRepo, roleRepo);
    await expect(useCase.execute({ organizationId: 404, roleId: role.id })).rejects.toThrow(
      "Organização com id 404 não encontrada.",
    );
  });

  it("CreateOrganizationRoleAssignmentUseCase falha se role não existir", async () => {
    const orgRepo = new InMemoryOrganizationsRepository();
    const roleRepo = new InMemoryOrganizationRolesRepository();
    const assignmentRepo = new InMemoryOrganizationRoleAssignmentsRepository();
    const createOrg = new CreateOrganizationUseCase(orgRepo);
    const org = await createOrg.execute({
      legalName: "Só org",
      documentNumber: "98765432000187",
    });
    const useCase = new CreateOrganizationRoleAssignmentUseCase(assignmentRepo, orgRepo, roleRepo);
    await expect(useCase.execute({ organizationId: org.id, roleId: 999 })).rejects.toThrow(
      "Papel organizacional com id 999 não encontrado.",
    );
  });

  it("CreateOrganizationRoleAssignmentUseCase bloqueia vínculo ativo duplicado", async () => {
    const { orgRepo, roleRepo, assignmentRepo, org, role } = await seedOrgAndRole();
    const useCase = new CreateOrganizationRoleAssignmentUseCase(assignmentRepo, orgRepo, roleRepo);
    await useCase.execute({ organizationId: org.id, roleId: role.id });
    await expect(useCase.execute({ organizationId: org.id, roleId: role.id })).rejects.toThrow(
      `Já existe vínculo ativo entre a organização ${org.id} e o papel ${role.id}.`,
    );
  });

  it("RevokeOrganizationRoleAssignmentUseCase revoga vínculo", async () => {
    const { orgRepo, roleRepo, assignmentRepo, org, role } = await seedOrgAndRole();
    const createAssignment = new CreateOrganizationRoleAssignmentUseCase(assignmentRepo, orgRepo, roleRepo);
    const created = await createAssignment.execute({ organizationId: org.id, roleId: role.id });
    const revoke = new RevokeOrganizationRoleAssignmentUseCase(assignmentRepo);
    const out = await revoke.execute({ id: created.id });
    expect(out.isActive).toBe(false);
    expect(out.revokedAt).toBeInstanceOf(Date);
  });

  it("RevokeOrganizationRoleAssignmentUseCase falha para id inexistente", async () => {
    const assignmentRepo = new InMemoryOrganizationRoleAssignmentsRepository();
    const revoke = new RevokeOrganizationRoleAssignmentUseCase(assignmentRepo);
    await expect(revoke.execute({ id: 777 })).rejects.toThrow("Atribuição de papel com id 777 não encontrada.");
  });

  it("ListOrganizationRoleAssignmentsByOrganizationUseCase lista por organização", async () => {
    const { orgRepo, roleRepo, assignmentRepo, org, role } = await seedOrgAndRole();
    const createAssignment = new CreateOrganizationRoleAssignmentUseCase(assignmentRepo, orgRepo, roleRepo);
    const role2 = await new CreateOrganizationRoleUseCase(roleRepo).execute({ code: "R2", name: "Papel 2" });
    await createAssignment.execute({ organizationId: org.id, roleId: role.id });
    await createAssignment.execute({ organizationId: org.id, roleId: role2.id });
    const list = new ListOrganizationRoleAssignmentsByOrganizationUseCase(assignmentRepo);
    const out = await list.execute(org.id);
    expect(out).toHaveLength(2);
    expect(out.map((a) => a.roleId).sort()).toEqual([role.id, role2.id].sort());
  });

  it("ListOrganizationRoleAssignmentsByRoleUseCase lista por papel", async () => {
    const orgRepo = new InMemoryOrganizationsRepository();
    const roleRepo = new InMemoryOrganizationRolesRepository();
    const assignmentRepo = new InMemoryOrganizationRoleAssignmentsRepository();
    const createOrg = new CreateOrganizationUseCase(orgRepo);
    const createRole = new CreateOrganizationRoleUseCase(roleRepo);
    const createAssignment = new CreateOrganizationRoleAssignmentUseCase(assignmentRepo, orgRepo, roleRepo);
    const org1 = await createOrg.execute({ legalName: "O1", documentNumber: "11111111000191" });
    const org2 = await createOrg.execute({ legalName: "O2", documentNumber: "22222222000172" });
    const role = await createRole.execute({ code: "SHARED", name: "Compartilhado" });
    await createAssignment.execute({ organizationId: org1.id, roleId: role.id });
    await createAssignment.execute({ organizationId: org2.id, roleId: role.id });
    const list = new ListOrganizationRoleAssignmentsByRoleUseCase(assignmentRepo);
    const out = await list.execute(role.id);
    expect(out).toHaveLength(2);
    expect(out.map((a) => a.organizationId).sort((a, b) => a - b)).toEqual([org1.id, org2.id].sort((a, b) => a - b));
  });
});
