import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const documentStudioDir = resolve(process.cwd(), 'src/features/admin/DocumentStudio');
const hub = readFileSync(resolve(documentStudioDir, '../DocumentHub.tsx'), 'utf8');
const tabs = readFileSync(resolve(documentStudioDir, 'StudioTabs.tsx'), 'utf8');
const navigation = readFileSync(resolve(documentStudioDir, 'useDocumentHubNavigation.ts'), 'utf8');

describe('Document Studio P5 visible RBAC', () => {
  it('mirrors the backend document permission mapping in the Patient shell', () => {
    expect(hub).toContain("has('prescriptions')");
    expect(hub).toContain("tabs.push('ordonnance')");
    expect(hub).toContain("has('patients')");
    expect(hub).toContain("tabs.push('certificat')");
    expect(hub).toContain("has('accounting')");
    expect(hub).toContain("tabs.push('devis', 'honoraires', 'echeancier')");
    expect(hub).toContain("has('clinical')");
    expect(hub).toContain("tabs.push('libre')");
  });

  it('only renders allowed tabs and guards direct URL navigation', () => {
    expect(tabs).toContain("allowedTabs.includes('ordonnance')");
    expect(tabs).toContain("allowedTabs.includes('certificat')");
    expect(tabs).toContain("allowedTabs.includes('devis')");
    expect(tabs).toContain("allowedTabs.includes('honoraires')");
    expect(tabs).toContain("allowedTabs.includes('echeancier')");
    expect(tabs).toContain("allowedTabs.includes('libre')");
    expect(navigation).toContain('allowedTabs.includes(nextTab)');
    expect(navigation).toContain('const nextFallback = allowedTabs[0]');
  });

  it('does not expose the clinical treatment-plan surface inside Documents', () => {
    expect(tabs).not.toContain('tab-strategie');
    expect(tabs).not.toContain("activeTab === 'plan'");
    expect(hub).not.toContain('TreatmentPlanStudio');
  });
});
