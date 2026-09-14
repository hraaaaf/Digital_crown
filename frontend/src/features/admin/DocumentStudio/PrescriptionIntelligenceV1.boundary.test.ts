import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const src = (file: string) => readFileSync(resolve(process.cwd(), 'src/features/admin', file), 'utf8');
const documentHub = src('DocumentHub.tsx');
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
});
