import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const source = (file: string) => readFileSync(
  resolve(process.cwd(), 'src/features/admin/DocumentStudio', file),
  'utf8',
);
const header = source('StudioHeader.tsx');
const tabs = source('StudioTabs.tsx');
const footer = source('StudioFooter.tsx');

describe('Document Studio T2-E product polish', () => {
  it('keeps patient identity and current document visible in the shell header', () => {
    expect(header).toContain('Patient actif');
    expect(header).toContain('DOCUMENT_STUDIO_LABELS[activeTab]');
    expect(header).toContain('truncate font-black');
  });

  it('keeps canonical tabs usable in dark mode without changing product vocabulary', () => {
    expect(tabs).toContain('dark:bg-slate-900/80');
    expect(tabs).toContain('DOCUMENT_STUDIO_LABELS.plan');
    expect(tabs).toContain('aria-pressed={active}');
  });

  it('preserves a clear total / preview / archive / print hierarchy', () => {
    expect(footer).toContain('Total document');
    expect(footer).toContain('Aperçu');
    expect(footer).toContain('Enregistrer');
    expect(footer).toContain('Imprimer');
    expect(footer).toContain('dark:bg-slate-950/85');
  });
});