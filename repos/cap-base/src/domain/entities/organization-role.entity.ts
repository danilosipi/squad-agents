/**
 * Papel de organização no domínio fundacional (sem persistência).
 */
export class OrganizationRole {
  private constructor(
    public readonly id: number,
    private _code: string,
    private _name: string,
    private _description: string | undefined,
    private _isActive: boolean,
  ) {}

  static create(params: {
    id: number;
    code: string;
    name: string;
    description?: string;
    isActive?: boolean;
  }): OrganizationRole {
    // id === 0: aguardando primeira persistência (repositório atribui id definitivo em save).
    if (!Number.isInteger(params.id) || params.id < 0) {
      throw new Error("id inválido.");
    }
    const code = params.code.trim();
    if (!code) {
      throw new Error("code é obrigatório.");
    }
    const name = params.name.trim();
    if (!name) {
      throw new Error("name é obrigatório.");
    }
    const desc = params.description?.trim();
    return new OrganizationRole(
      params.id,
      code,
      name,
      desc ? desc : undefined,
      params.isActive ?? true,
    );
  }

  get code(): string {
    return this._code;
  }

  get name(): string {
    return this._name;
  }

  get description(): string | undefined {
    return this._description;
  }

  get isActive(): boolean {
    return this._isActive;
  }

  activate(): void {
    this._isActive = true;
  }

  deactivate(): void {
    this._isActive = false;
  }

  updateBasicInfo(params: { code?: string; name?: string; description?: string }): void {
    if (params.code !== undefined) {
      const next = params.code.trim();
      if (!next) {
        throw new Error("code não pode ser vazio.");
      }
      this._code = next;
    }
    if (params.name !== undefined) {
      const next = params.name.trim();
      if (!next) {
        throw new Error("name não pode ser vazio.");
      }
      this._name = next;
    }
    if (params.description !== undefined) {
      const d = params.description.trim();
      this._description = d ? d : undefined;
    }
  }
}
