import { describe, expect, it } from "vitest";
import { Cnpj } from "../../src/domain/value-objects/cnpj.vo.js";
import { Email } from "../../src/domain/value-objects/email.vo.js";
import { Phone } from "../../src/domain/value-objects/phone.vo.js";

describe("Cnpj", () => {
  it("aceita CNPJ válido (14 dígitos após normalização)", () => {
    const cnpj = Cnpj.create("12.345.678/0001-95");
    expect(cnpj.value).toBe("12345678000195");
  });

  it("rejeita CNPJ com menos de 14 dígitos", () => {
    expect(() => Cnpj.create("1234567800019")).toThrow(
      "CNPJ deve conter exatamente 14 dígitos numéricos.",
    );
  });
});

describe("Email", () => {
  it("normaliza email em minúsculas", () => {
    const email = Email.create("  Test@Example.COM  ");
    expect(email.value).toBe("test@example.com");
  });

  it("rejeita email inválido", () => {
    expect(() => Email.create("sem-arroba")).toThrow("Formato de email inválido.");
  });
});

describe("Phone", () => {
  it("mantém apenas dígitos após normalização", () => {
    const phone = Phone.create("(11) 98765-4321");
    expect(phone.value).toBe("11987654321");
  });

  it("rejeita telefone com tamanho fora do intervalo", () => {
    expect(() => Phone.create("123456789")).toThrow(
      "Telefone deve ter entre 10 e 15 dígitos numéricos após normalização.",
    );
  });
});
