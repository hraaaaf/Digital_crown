/** Patients phase 1 — semantic visual roles, zero backend/clinical mutation.
 * Existing neutral black modal backdrop is the only bounded, non-thematic
 * palette exception in these four components.
 */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const files = [
  'PatientDraftRouteGuard.tsx',
  'components/PatientRvgPanel.tsx',
  'components/PatientScoreBadge.tsx',
  'components/PatientSummaryHoverCard.tsx',
] as const;
const read = (file: string) =>
  readFileSync(resolve(process.cwd(), 'src/features/patients', file), 'utf8');
const fixed = /(?:[\w-]+:)*(?:bg|text|border|ring|outline|from|via|to|shadow)-(?:slate|gray|blue|red|indigo|orange|yellow|emerald|green|amber|rose|white|black|pink|purple|teal|cyan|zinc|sky)-\d{2,3}(?:\/\d+)?\b|(?:bg|text|border)-\[#(?:[a-f0-9]{3,8})\]/gi;

describe('Patients phase 1 semantic themes', () => {
  it.each(files)('%s contains no fixed UI palettes', file => {
    const content = read(file).replaceAll('bg-slate-950/70', '');
    expect(content.match(fixed) ?? []).toEqual([]);
  });

  it('draft exit retains true block/veto and explicitly contrasted danger action', () => {
    const file = read('PatientDraftRouteGuard.tsx');
    for (const contract of ['stayOnPatient', 'discardAndProceed', "blocker.state === 'blocked'",
                           "role=\"alertdialog\"", "aria-modal=\"true\"",
                           "resetPatientDocumentBoundary()", "stayButton.current?.focus()"]) {
      expect(file).toContain(contract);
    }
    expect(file).toContain('bg-card');
    expect(file).toContain('bg-danger-surface');
    expect(file).toContain('border-danger-border');
    expect(file).toContain('text-danger');
    expect(file).toContain('focus-visible:outline-primary');
    expect(file).toContain('bg-slate-950/70');
  });

  it('RVG never turns loading/error into a false empty state', () => {
    const file = read('components/PatientRvgPanel.tsx');
    expect(file).toContain("rvgService.listRVG(patientId)");
    expect(file).toContain("setError(true)");
    expect(file).toContain("if (loading)");
    expect(file).toContain("if (error)");
    expect(file).toContain("documents.length === 0");
    expect(file).toContain('text-danger');
    expect(file).toContain('bg-primary text-on-primary');
    expect(file).not.toContain('bg-[#003380]');
  });

  it('manual patient tags remain manual; billing statistics not recategorized', () => {
    const file = read('components/PatientScoreBadge.tsx');
    expect(file).toContain("Tag cabinet manuel.");
    expect(file).toContain("api.patch(\`/patients/\${patientId}/grade\`");
    expect(file).toContain('data.is_manual');
    expect(file).toContain('bg-info-surface');
    expect(file).toContain('border-info-border');
    expect(file).toContain('text-info');
  });

  it('dossier vigilance is not weakened by theme transition', () => {
    const file = read('components/PatientSummaryHoverCard.tsx');
    expect(file).toContain("data.patient_summary.alerts.join(', ')");
    expect(file).toContain('bg-danger-surface');
    expect(file).toContain('border-danger-border');
    expect(file).toContain('text-danger');
    expect(file).toContain("i.type === 'financial_risk'");
    expect(file).toContain('bg-warning-surface');
    expect(file).toContain('text-warning');
    expect(file).not.toContain('dark:bg-[#0f172a]');
  });

  it('all eight configured themes still expose the required roles', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
    for (const variable of [
      '--color-primary:', '--color-on-primary:', '--color-card:',
      '--color-danger-surface:', '--color-danger-border:',
      '--color-warning-surface:', '--color-info-surface:',
    ]) expect(css).toContain(variable);
    for (const name of ['emerald','rose','ocean','graphite','prestige','dark','high-contrast']) {
      expect(css).toContain("[data-theme='" + name + "']");
    }
  });
});
