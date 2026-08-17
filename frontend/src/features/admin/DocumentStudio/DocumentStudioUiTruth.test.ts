import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const documentStudioDir = resolve(process.cwd(), 'src/features/admin/DocumentStudio');
const read = (file: string) => readFileSync(resolve(documentStudioDir, file), 'utf8');

const activeShellSource = [
  read('StudioHeader.tsx'),
  read('StudioTabs.tsx'),
  read('StudioFooter.tsx'),
  read('LivePreview.tsx'),
].join('\n');

describe('Document Studio UI truth boundary', () => {
  it('does not advertise unsupported runtime or AI capability states', () => {
    expect(activeShellSource).not.toMatch(/Moteur Local Actif/i);
    expect(activeShellSource).not.toMatch(/Lancer Analyse IA/i);
    expect(activeShellSource).not.toMatch(/Régénérer Analyse/i);
    expect(activeShellSource).not.toMatch(/IA certifi[ée]e?/i);
  });

  it('removes the uncertified clinical route instead of exposing a ghost disabled state', () => {
    expect(activeShellSource).not.toContain("| 'ai'");
    expect(activeShellSource).not.toContain("activeTab === 'ai'");
    expect(activeShellSource).not.toContain('Fonction clinique désactivée');
    expect(activeShellSource).not.toContain('validation scientifique dédiée');
  });
});