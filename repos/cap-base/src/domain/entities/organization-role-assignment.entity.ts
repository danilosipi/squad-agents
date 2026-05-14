/**
 * Atribuição de papel a uma organização (domínio puro).
 */
export class OrganizationRoleAssignment {
  private constructor(
    public readonly id: number,
    public readonly organizationId: number,
    public readonly roleId: number,
    public readonly assignedAt: Date,
    private _revokedAt: Date | undefined,
    private _isActive: boolean,
  ) {}

  static create(params: {
    id: number;
    organizationId: number;
    roleId: number;
    assignedAt?: Date;
    revokedAt?: Date;
    isActive?: boolean;
  }): OrganizationRoleAssignment {
    // id === 0: aguardando primeira persistência (repositório atribui id definitivo em save).
    if (!Number.isInteger(params.id) || params.id < 0) {
      throw new Error("id inválido.");
    }
    if (!Number.isInteger(params.organizationId) || params.organizationId <= 0) {
      throw new Error("organizationId inválido.");
    }
    if (!Number.isInteger(params.roleId) || params.roleId <= 0) {
      throw new Error("roleId inválido.");
    }
    const assigned = params.assignedAt ?? new Date();
    let revoked = params.revokedAt;
    let active = params.isActive ?? true;
    if (active === false && revoked === undefined) {
      revoked = assigned;
    }
    if (revoked !== undefined && active) {
      active = false;
    }
    return new OrganizationRoleAssignment(
      params.id,
      params.organizationId,
      params.roleId,
      assigned,
      revoked,
      active,
    );
  }

  get revokedAt(): Date | undefined {
    return this._revokedAt;
  }

  get isActive(): boolean {
    return this._isActive;
  }

  revoke(): void {
    if (this._revokedAt !== undefined) {
      throw new Error("Atribuição já revogada.");
    }
    this._revokedAt = new Date();
    this._isActive = false;
  }

  reactivate(): void {
    if (this._isActive && this._revokedAt === undefined) {
      throw new Error("Atribuição já está ativa.");
    }
    this._revokedAt = undefined;
    this._isActive = true;
  }
}
