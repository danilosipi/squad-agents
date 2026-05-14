import type { OrganizationRoleAssignmentsRepository } from "../../src/domain/repositories/organization-role-assignments.repository.js";
import { OrganizationRoleAssignment } from "../../src/domain/entities/organization-role-assignment.entity.js";

/**
 * Repositório em memória para testes (sem Prisma).
 */
export class InMemoryOrganizationRoleAssignmentsRepository implements OrganizationRoleAssignmentsRepository {
  private readonly items: OrganizationRoleAssignment[] = [];
  private nextId = 1;

  async findById(id: number): Promise<OrganizationRoleAssignment | null> {
    return this.items.find((a) => a.id === id) ?? null;
  }

  async listByOrganizationId(organizationId: number): Promise<OrganizationRoleAssignment[]> {
    return this.items
      .filter((a) => a.organizationId === organizationId)
      .sort((a, b) => a.id - b.id);
  }

  async listByRoleId(roleId: number): Promise<OrganizationRoleAssignment[]> {
    return this.items.filter((a) => a.roleId === roleId).sort((a, b) => a.id - b.id);
  }

  async save(assignment: OrganizationRoleAssignment): Promise<OrganizationRoleAssignment> {
    if (assignment.id === 0) {
      const id = this.nextId++;
      const saved = OrganizationRoleAssignment.create({
        id,
        organizationId: assignment.organizationId,
        roleId: assignment.roleId,
        assignedAt: assignment.assignedAt,
        revokedAt: assignment.revokedAt,
        isActive: assignment.isActive,
      });
      this.items.push(saved);
      return saved;
    }
    const idx = this.items.findIndex((a) => a.id === assignment.id);
    if (idx === -1) {
      this.items.push(assignment);
      return assignment;
    }
    this.items[idx] = assignment;
    return assignment;
  }
}
