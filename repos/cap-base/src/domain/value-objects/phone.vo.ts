const MIN_DIGITS = 10;
const MAX_DIGITS = 15;

/**
 * Value object para telefone (somente dígitos; tamanho mínimo/máximo básico).
 */
export class Phone {
  private constructor(private readonly digits: string) {}

  static create(raw: string): Phone {
    const normalized = raw.replace(/\D/g, "");
    if (normalized.length < MIN_DIGITS || normalized.length > MAX_DIGITS) {
      throw new Error(
        `Telefone deve ter entre ${MIN_DIGITS} e ${MAX_DIGITS} dígitos numéricos após normalização.`,
      );
    }
    return new Phone(normalized);
  }

  get value(): string {
    return this.digits;
  }
}
