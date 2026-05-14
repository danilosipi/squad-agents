export type CreateOrganizationInput = {
  legalName: string;
  tradeName?: string;
  documentNumber: string;
};

export type OrganizationOutput = {
  id: number;
  legalName: string;
  tradeName?: string;
  documentNumber: string;
  isActive: boolean;
  createdAt: Date;
  updatedAt?: Date;
};
