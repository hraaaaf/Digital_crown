import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const documentStudioSource = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);

const appSource = (file: string) => readFileSync(
  resolve(process.cwd(), 'src', file),
  'utf8',
);

const header = documentStudioSource('StudioHeader.tsx');
const content = documentStudioSource('DocumentHubContent.tsx');
const prescription = documentStudioSource('Forms/PrescriptionAgenticStudioV1.tsx');
const theme = appSource('index.css');

describe('Ordonnance Fidelity V3 U1 hierarchy', () => {
  it('makes Ordonnance the primary title while keeping patient, author and date visible', () => {
    expect(header).toContain('data-ordonnance-hierarchy-header');
    expect(header).toContain('data-ordonnance-hierarchy-title');
    expect(header).toContain("{compactOrdonnance ? documentLabel : 'Documents'}");
    expect(header).toContain("{compactOrdonnance ? 'Patient' : 'Patient actif'}");
    expect(header).toContain('id="document-studio-author"');
    expect(header).toContain('id="document-studio-date"');
    expect(header).toContain('min-h-11');
  });

  it('keeps the clinical workflow ahead of legal secondary metadata', () => {
    const clinicalWorkspace = content.indexOf('<PrescriptionAgenticStudio');
    const legalMetadata = content.indexOf('data-ordonnance-secondary-meta');
    expect(clinicalWorkspace).toBeGreaterThan(-1);
    expect(legalMetadata).toBeGreaterThan(-1);
    expect(clinicalWorkspace).toBeLessThan(legalMetadata);
  });

  it('orders blocked clinical guidance and safety before the prescription body', () => {
    const blockedIndex = prescription.indexOf('data-clinical-rule-status="blocked"');
    const safetyIndex = prescription.indexOf('data-safety-status="blocked"');
    const prescriptionBodyIndex = prescription.indexOf('<DrugRow');
    expect(blockedIndex).toBeGreaterThan(-1);
    expect(safetyIndex).toBeGreaterThan(-1);
    expect(prescriptionBodyIndex).toBeGreaterThan(-1);
    expect(blockedIndex).toBeLessThan(prescriptionBodyIndex);
    expect(safetyIndex).toBeLessThan(prescriptionBodyIndex);
  });

  it('inherits the active application theme instead of creating an Ordonnance palette', () => {
    for (const token of [
      '--primary:',
      '--secondary:',
      '--accent:',
      '--glass-bg:',
      '--glass-border:',
      '--card-bg:',
      '--text-main:',
      '--text-muted:',
      '--border-color:',
      '--input-bg:',
    ]) {
      expect(theme).toContain(token);
    }

    for (const surface of [header, content, prescription]) {
      expect(surface).not.toMatch(/#[0-9a-fA-F]{3,8}\b/);
      expect(surface).not.toContain("data-theme='dark'");
      expect(surface).not.toContain("data-theme='prestige'");
    }
  });
});