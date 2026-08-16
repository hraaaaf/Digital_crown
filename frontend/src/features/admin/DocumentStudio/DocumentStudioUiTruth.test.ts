import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const read = (relativePath: string) => readFileSync(new URL(relativePath, import.meta.url), 'utf8');

const activeShellSource = [
  read('./StudioHeader.tsx'),
  read('./StudioTabs.tsx'),
  read('./StudioFooter.tsx'),
  read('./LivePreview.tsx'),
].join('\n');

describe('Document Studio UI truth boundary', () => {
  it('does not advertise unsupported runtime or AI capability states', () => {
    expect(activeShellSource).not.toMatch(/Moteur Local Actif/i);
    expect(activeShellSource).not.toMatch(/Lancer Analyse IA/i);
    expect(activeShellSource).not.toMatch(/Régénérer Analyse/i);
    expect(activeShellSource).not.toMatch(/IA certifi[ée]e?/i);
  });

  it('keeps the uncertified clinical path explicitly unavailable', () => {
    expect(activeShellSource).toContain('Fonction clinique désactivée');
    expect(activeShellSource).toContain('validation scientifique dédiée');
  });
});
