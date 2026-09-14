import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const src = (file: string) => readFileSync(resolve(process.cwd(), 'src/features/admin', file), 'utf8');
const documentHub = src('DocumentHub.tsx');
const documentHubContent = src('DocumentStudio/DocumentHubContent.tsx');
const generator = src('DocumentStudio/useDocumentGenerator.ts');
const studio = src('DocumentStudio/Forms/PrescriptionAgenticStudioV1.tsx');

describe('Prescription Intelligence V1 active clinical boundary', () => {
  it('does not call or retain the legacy smart suggestion path', () => {
    expect(documentHub).not.toContain('/prescriptions/smart-suggest/');
    expect(documentHub).not.toContain('setSmartSuggestion');
    expect(documentHub).toContain('smartSuggestion: null');
  });

  it('keeps legacy automatic prescription mechanisms outside the active V1 studio', () => {
    expect(studio).not.toContain('PrescriptionAgenticStudioLegacy');
    expect(studio).not.toContain('DEFAULT_MOROCCO_PRESETS');
    expect(studio).not.toContain('QUICK_PRESCRIPTIONS');
    expect(studio).toContain('data-clinical-rule-status="blocked"');
  });

  it('does not call the uncertified legacy safety engine from V1', () => {
    expect(studio).not.toContain("api.post('/prescriptions/safety/check'");
    expect(studio).toContain('data-safety-status="blocked"');
    expect(studio).toContain('Le moteur de sécurité legacy n’est pas une règle V1 certifiée');
  });

  it('never invents a medication form when V1 has none', () => {
    expect(documentHub).not.toContain("forme: m.forme || 'Sachets'");
    expect(documentHubContent).not.toContain("forme: 'Comprimés'");
    expect(generator).not.toContain("forme: d.forme || 'Sachets'");
    expect(generator).toContain('forme: d.forme,');
  });
});
