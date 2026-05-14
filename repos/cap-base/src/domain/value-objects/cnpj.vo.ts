/**
 * Value object para CNPJ (apenas normalização e tamanho; sem dígitos verificadores).
 */
export class Cnpj {
  private constructor(private readonly digits: string) {}

  static create(raw: string): Cnpj {
    const normalized = raw.replace(/\D/g, "");
    if (normalized.length !== 14) {
      throw new Error("CNPJ deve conter exatamente 14 dígitos numéricos.");
    }
    return new Cnpj(normalized);
  }

  get value(): string {
    return this.digits;
  }

  /** Formato XX.XXX.XXX/XXXX-XX */
  get formatted(): string {
    const d = this.digits;
    return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12, 14)}`;
  }
}
