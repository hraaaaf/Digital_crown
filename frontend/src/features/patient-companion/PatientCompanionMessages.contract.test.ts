import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const source = fs.readFileSync(path.resolve(__dirname, 'PatientCompanionMessages.tsx'), 'utf8');

describe('PatientCompanionMessages truth contract', () => {
  it('keeps offline composition available while preserving non-confirmation wording', () => {
    expect(source).toContain('const canSend = bytes > 0 && bytes <= MAX_BODY_BYTES && !busy;');
    expect(source).toContain("if (!transportReady || !enabled)");
    expect(source).toContain('Message chiffré enregistré sur cet appareil · non envoyé.');
  });

  it('uses evidence-based labels and no realtime presence claims', () => {
    expect(source).toContain('Lu par le cabinet');
    expect(source).toContain('Reçu par le cabinet');
    expect(source).toContain('Reçu sur cet appareil');
    expect(source).toContain('Conversation asynchrone chiffrée');
    expect(source).not.toContain('En ligne');
    expect(source).not.toContain('écrit…');
  });

  it('keeps attachments out of the PC-08 initial slice', () => {
    expect(source).not.toContain('type="file"');
    expect(source).not.toContain('accept="image');
  });
});
