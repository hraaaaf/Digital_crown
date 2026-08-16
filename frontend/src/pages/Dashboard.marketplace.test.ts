import { describe, expect, it } from "vitest";
import fs from "node:fs";
import path from "node:path";

const dashboardSource = fs.readFileSync(path.resolve(__dirname, "Dashboard.tsx"), "utf8");
const marketplaceSource = fs.readFileSync(
  path.resolve(__dirname, "../features/dashboard/components/MarketplaceCard.tsx"),
  "utf8",
);

describe("Dashboard D3 marketplace", () => {
  it("keeps a compact business-facing marketplace entry", () => {
    expect(dashboardSource).toContain("<MarketplaceCard");
    expect(marketplaceSource).toContain('to="/approvisionnement"');
    expect(marketplaceSource).toContain('Commander les consommables et fournitures du cabinet');
  });

  it("does not expose internal implementation rationale", () => {
    const source = `${dashboardSource}\n${marketplaceSource}`;
    expect(source).not.toContain('Pourquoi ici');
    expect(source).not.toContain('frontend only');
    expect(source).not.toContain('perimetre metier coherent');
  });
});
