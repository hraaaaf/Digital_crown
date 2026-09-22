import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';

const source = fs.readFileSync(
  path.resolve(__dirname, 'PatientCompanionMessagingPanel.tsx'),
  'utf8',
);

describe('PatientCompanionMessagingPanel truth contract', () => {
  it('keeps the same client message id when retrying the unchanged staff intent', () => {
    expect(source).toContain("const [sendIntent, setSendIntent]");
    expect(source).toContain("sendIntent?.body === text");
    expect(source).toContain("client_message_id: intent.clientMessageId");
    expect(source).toContain("if (sendIntent && sendIntent.body !== value.trim()) setSendIntent(null)");
  });

  it('uses evidence-based delivery labels only', () => {
    expect(source).toContain("'Envoyé depuis le cabinet'");
    expect(source).toContain("'Reçu sur l’appareil'");
    expect(source).toContain("'Lu'");
    // Staff-side messages use recipient-relative "Lu"; the patient-side contract
    // separately requires "Lu par le cabinet" where that perspective is meaningful.
    expect(source).not.toContain("'Livré'");
    expect(source).not.toContain("'En ligne'");
  });

  it('keeps access identity explicit and attachments out of scope', () => {
    expect(source).toContain('Accès destinataire');
    expect(source).toContain('selectedLabel');
    expect(source).not.toContain('type="file"');
  });
});
