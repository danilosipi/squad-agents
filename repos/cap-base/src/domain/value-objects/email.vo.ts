const BASIC_EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * Value object para email (normalização + validação básica de formato).
 */
export class Email {
  private constructor(private readonly normalized: string) {}

  static create(raw: string): Email {
    const trimmed = raw.trim().toLowerCase();
    if (!trimmed) {
      throw new Error("Email não pode ser vazio.");
    }
    if (!BASIC_EMAIL.test(trimmed)) {
      throw new Error("Formato de email inválido.");
    }
    return new Email(trimmed);
  }

  get value(): string {
    return this.normalized;
  }
}
