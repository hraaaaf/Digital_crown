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
const preview = source('DocumentHubPreview.tsx');

describe('Document Studio T2-E product polish', () => {
  it('keeps patient identity and current document visible in the shell header', () => {
    expect(header).toContain('Patient actif');
    expect(header).toContain('DOCUMENT_STUDIO_LABELS[activeTab]');
    expect(header).toContain('truncate font-black');
  });

  it('keeps current canonical document tabs usable in dark mode', () => {
    expect(tabs).toContain('dark:bg-slate-900/80');
    expect(tabs).toContain('DOCUMENT_STUDIO_LABELS.ordonnance');
    expect(tabs).toContain('DOCUMENT_STUDIO_LABELS.certificat');
    expect(tabs).toContain('DOCUMENT_STUDIO_LABELS.libre');
    expect(tabs).not.toContain('DOCUMENT_STUDIO_LABELS.plan');
    expect(tabs).toContain('aria-pressed={active}');
  });

  it('preserves a clear total / preview / archive / print hierarchy', () => {
    expect(footer).toContain('Total document');
    expect(footer).toContain('Aperçu');
    expect(footer).toContain('Enregistrer');
    expect(footer).toContain('Imprimer');
    expect(footer).toContain('dark:bg-slate-950/85');
  });

  it('closes the open preview with Escape and unregisters the keyboard handler', () => {
    expect(preview).toContain("event.key !== 'Escape'");
    expect(preview).toContain('onClose();');
    expect(preview).toContain("window.addEventListener('keydown', handleKeyDown)");
    expect(preview).toContain("window.removeEventListener('keydown', handleKeyDown)");
  });
});
