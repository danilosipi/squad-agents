import { describe, expect, it } from "vitest";
import { Organization } from "../../src/domain/entities/organization.entity.js";

describe("Organization", () => {
  it("cria organização válida", () => {
    const org = Organization.create({
      id: 1,
      legalName: "  ACME LTDA  ",
      tradeName: "  ACME  ",
      documentNumber: "  12345678000195  ",
    });
    expect(org.id).toBe(1);
    expect(org.legalName).toBe("ACME LTDA");
    expect(org.tradeName).toBe("ACME");
    expect(org.documentNumber).toBe("12345678000195");
    expect(org.isActive).toBe(true);
  });

  it("activate() define isActive true e atualiza updatedAt", () => {
    const org = Organization.create({
      id: 1,
      legalName: "X",
      documentNumber: "1",
      isActive: false,
    });
    const before = org.updatedAt;
    org.activate();
    expect(org.isActive).toBe(true);
    expect(org.updatedAt).toBeDefined();
    expect(org.updatedAt!.getTime()).toBeGreaterThanOrEqual(before?.getTime() ?? 0);
  });

  it("deactivate() define isActive false", () => {
    const org = Organization.create({
      id: 1,
      legalName: "X",
      documentNumber: "1",
      isActive: true,
    });
    org.deactivate();
    expect(org.isActive).toBe(false);
  });

  it("updateBasicInfo() atualiza campos informados", () => {
    const org = Organization.create({
      id: 1,
      legalName: "Old Legal",
      tradeName: "Old Trade",
      documentNumber: "111",
    });
    org.updateBasicInfo({
      legalName: "New Legal",
      tradeName: null,
      documentNumber: "222",
    });
    expect(org.legalName).toBe("New Legal");
    expect(org.tradeName).toBeUndefined();
    expect(org.documentNumber).toBe("222");
  });
});
