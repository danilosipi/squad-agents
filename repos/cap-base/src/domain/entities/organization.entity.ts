/**
 * Organização fundacional do CAP (domínio puro; sem persistência).
 */
export class Organization {
  private constructor(
    public readonly id: number,
    private _legalName: string,
    private _tradeName: string | undefined,
    private _documentNumber: string,
    private _isActive: boolean,
    public readonly createdAt: Date,
    private _updatedAt: Date | undefined,
  ) {}

  static create(params: {
    id: number;
    legalName: string;
    tradeName?: string;
    documentNumber: string;
    isActive?: boolean;
    createdAt?: Date;
    updatedAt?: Date;
  }): Organization {
    // id === 0: aguardando primeira persistência (repositório atribui id definitivo em save).
    if (!Number.isInteger(params.id) || params.id < 0) {
      throw new Error("id inválido.");
    }
    const legal = params.legalName.trim();
    if (!legal) {
      throw new Error("legalName é obrigatório.");
    }
    const doc = params.documentNumber.trim();
    if (!doc) {
      throw new Error("documentNumber é obrigatório.");
    }
    const trade = params.tradeName?.trim();
    return new Organization(
      params.id,
      legal,
      trade ? trade : undefined,
      doc,
      params.isActive ?? true,
      params.createdAt ?? new Date(),
      params.updatedAt,
    );
  }

  get legalName(): string {
    return this._legalName;
  }

  get tradeName(): string | undefined {
    return this._tradeName;
  }

  get documentNumber(): string {
    return this._documentNumber;
  }

  get isActive(): boolean {
    return this._isActive;
  }

  get updatedAt(): Date | undefined {
    return this._updatedAt;
  }

  activate(): void {
    this._isActive = true;
    this._updatedAt = new Date();
  }

  deactivate(): void {
    this._isActive = false;
    this._updatedAt = new Date();
  }

  updateBasicInfo(params: {
    legalName?: string;
    tradeName?: string | null;
    documentNumber?: string;
  }): void {
    if (params.legalName !== undefined) {
      const next = params.legalName.trim();
      if (!next) {
        throw new Error("legalName não pode ser vazio.");
      }
      this._legalName = next;
    }
    if (params.tradeName !== undefined) {
      if (params.tradeName === null) {
        this._tradeName = undefined;
      } else {
        const t = params.tradeName.trim();
        this._tradeName = t ? t : undefined;
      }
    }
    if (params.documentNumber !== undefined) {
      const d = params.documentNumber.trim();
      if (!d) {
        throw new Error("documentNumber não pode ser vazio.");
      }
      this._documentNumber = d;
    }
    this._updatedAt = new Date();
  }
}
