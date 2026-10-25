/** Accounting phase 1 — visual semantic-token migration, no financial writes. */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const files = ['AccountingHeader.tsx', 'AccountingTabs.tsx', 'UnpaidPanel.tsx'] as const;
const read = (file: string) => readFileSync(resolve(process.cwd(), 'src/features/accounting/components', file), 'utf8');
const fixed = /(?:[\w-]+:)*(?:bg|text|border|ring|outline|divide|shadow)-(?:slate|gray|blue|red|green|emerald|amber|orange|rose|indigo|yellow|purple|pink|white|black)(?:-\d{2,3})?(?:\/\d+)?\b|(?:bg|text|border)-\[#[a-f0-9]{3,8}\]/gi;

describe('Accounting P1 semantic theme token safety', () => {
  it.each(files)('%s has no hardcoded brand/status/UI palette', file => {
    const source = read(file);
    expect(source.match(fixed) ?? []).toEqual([]);
  });

  it('keeps export callbacks, disabled guards and on-primary text', () => {
    const source = read('AccountingHeader.tsx');
    expect(source).toContain('onClick={handleExportCsv}');
    expect(source).toContain('onClick={handleExport}');
    expect(source).toContain('disabled={exportingCsv || itemsCount === 0}');
    expect(source).toContain('disabled={exporting || itemsCount === 0}');
    expect(source.match(/bg-primary text-on-primary/g)?.length).toBeGreaterThanOrEqual(2);
    expect(source).toContain('bg-success-surface');
    expect(source).toContain('border-success-border');
    expect(source).toContain('text-success');
  });

  it('keeps the four original accounting tab identifiers and debt indicator', () => {
    const source = read('AccountingTabs.tsx');
    for (const id of ['history', 'treasury', 'insights', 'unpaid']) {
      expect(source).toContain("setActiveTab('" + id + "')");
    }
    expect(source).toContain('treasuryData.pending_count');
    expect(source).toContain('debtData.total_patients');
    expect(source).toContain('bg-info-surface');
    expect(source).toContain('bg-danger-surface');
  });

  it('does not change amounts, patient links or empty-state semantics', () => {
    const source = read('UnpaidPanel.tsx');
    for (const field of ['total_amount', 'total_billed', 'total_paid', 'remaining_due',
                         'total_patients', 'patient_id']) expect(source).toContain(field);
    expect(source).toContain('loadingDebts ? (');
    expect(source).toContain('!debtData || debtData.items.length === 0');
    expect(source).toContain('Aucun impayé');
    expect(source).toContain('href={\`/patients/\${item.patient_id}?tab=finances\`}');
    expect(source).toContain('bg-danger-surface');
    expect(source).toContain('text-danger');
  });

  it('inherits canonical semantic roles across eight configured themes', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
    for (const token of ['--color-primary:', '--color-on-primary:', '--color-card:',
                         '--color-background:', '--color-success-surface:', '--color-danger-surface:']) {
      expect(css).toContain(token);
    }
    for (const theme of ['emerald', 'rose', 'ocean', 'graphite', 'prestige', 'dark', 'high-contrast']) {
      expect(css).toContain("[data-theme='" + theme + "']");
    }
  });
});
