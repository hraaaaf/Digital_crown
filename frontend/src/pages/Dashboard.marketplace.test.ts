import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";
const source = fs.readFileSync(path.resolve(__dirname, "Dashboard.tsx"), "utf8");
describe("Dashboard D3 marketplace", () => {
  it("keeps a compact business-facing marketplace entry", () => {
    expect(source).toContain('to="/approvisionnement"');
    expect(source).toContain('Commander les consommables et fournitures du cabinet');
  });
  it("does not expose internal implementation rationale", () => {
    expect(source).not.toContain('Pourquoi ici');
    expect(source).not.toContain('frontend only');
    expect(source).not.toContain('perimetre metier coherent');
  });
});
