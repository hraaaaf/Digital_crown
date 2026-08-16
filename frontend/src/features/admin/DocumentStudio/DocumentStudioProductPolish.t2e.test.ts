import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const header = readFileSync(new URL('./StudioHeader.tsx', import.meta.url), 'utf8');
const tabs = readFileSync(new URL('./StudioTabs.tsx', import.meta.url), 'utf8');
const footer = readFileSync(new URL('./StudioFooter.tsx', import.meta.url), 'utf8');

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
