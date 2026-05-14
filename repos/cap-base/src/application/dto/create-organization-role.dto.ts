export type CreateOrganizationRoleInput = {
  code: string;
  name: string;
  description?: string;
};

export type OrganizationRoleOutput = {
  id: number;
  code: string;
  name: string;
  description?: string;
  isActive: boolean;
};
