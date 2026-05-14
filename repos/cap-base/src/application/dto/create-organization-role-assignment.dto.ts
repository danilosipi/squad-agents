export type CreateOrganizationRoleAssignmentInput = {
  organizationId: number;
  roleId: number;
};

export type OrganizationRoleAssignmentOutput = {
  id: number;
  organizationId: number;
  roleId: number;
  assignedAt: Date;
  revokedAt?: Date;
  isActive: boolean;
};
