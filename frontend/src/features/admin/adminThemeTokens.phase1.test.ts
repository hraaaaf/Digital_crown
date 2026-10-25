/** Admin phase 1 — semantic appearance only; leave permission and printing gates intact. */
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const names = [
  'Settings/components/SharedUI.tsx',
  'Settings/tabs/BlockedPrintJobsReadOnly.tsx',
  'DocumentStudio/AccountingQuickActions.tsx',
] as const;
const read = (file: string) =>
  readFileSync(resolve(process.cwd(), 'src/features/admin', file), 'utf8');
const fixed = /(?:[\w-]+:)*(?:bg|text|border|ring|outline|shadow)-(?:slate|gray|blue|red|green|emerald|amber|orange|rose|indigo|yellow|purple|pink|white|black)(?:-\d{2,3})?(?:\/\d+)?\b|(?:bg|text|border)-\[#[a-f0-9]{3,8}\]/gi;

describe('Administration P1 semantic theme token safety', () => {
  it.each(names)('%s consumes semantic theme roles', file => {
    expect(read(file).match(fixed) ?? []).toEqual([]);
  });

  it('settings input fields and active tabs follow the selected theme', () => {
    const file = read('Settings/components/SharedUI.tsx');
    expect(file).toContain('bg-input-field');
    expect(file).toContain('text-text-main');
    expect(file).toContain('border-border-main');
    expect(file).toContain('bg-primary text-on-primary');
    expect(file).toContain('focus-visible:outline-primary');
    expect(file).toContain('bg-danger-surface');
    expect(file).toContain('border-danger-border');
    expect(file).not.toContain("color: active ? 'white'");
  });

  it('blocked print monitor stays owner-only and strictly read-only', () => {
    const file = read('Settings/tabs/BlockedPrintJobsReadOnly.tsx');
    expect(file).toContain('if (!ownerVerified) return null');
    expect(file).toContain("api.get<BlockedJobsResponse>('/admin/station-print-config/blocked-jobs')");
    expect(file).toContain("result.data.printingAvailable !== false");
    expect(file).toContain("result.data.retrySupported !== false");
    expect(file).not.toMatch(/api\.(?:post|put|patch|delete)\s*\(/);
    expect(file).toContain('bg-warning-surface');
    expect(file).toContain('border-warning-border');
    expect(file).toContain('text-warning');
    expect(file).toContain('ne pas réimprimer');
  });

  it('quick accounting actions preserve original callbacks and semantic action contrast', () => {
    const file = read('DocumentStudio/AccountingQuickActions.tsx');
    expect(file).toContain('onClick={() => onSelect(act)}');
    expect(file).toContain('onClick={onAddManual}');
    expect(file).toContain('aria-expanded={open}');
    expect(file).toContain('bg-primary');
    expect(file).toContain('text-on-primary');
    expect(file).toContain('border-border-main');
  });

  it('canonical semantic roles exist for all eight themes', () => {
    const css = readFileSync(resolve(process.cwd(), 'src/index.css'), 'utf8');
    for (const name of ['--color-primary:', '--color-on-primary:', '--color-card:',
                        '--color-input-field:', '--color-warning-surface:', '--color-danger-surface:']) {
      expect(css).toContain(name);
    }
    for (const theme of ['emerald','rose','ocean','graphite','prestige','dark','high-contrast']) {
      expect(css).toContain("[data-theme='" + theme + "']");
    }
  });
});
