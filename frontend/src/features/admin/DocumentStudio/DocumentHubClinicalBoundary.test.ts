import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const documentHubSource = readFileSync(new URL('../DocumentHub.tsx', import.meta.url), 'utf8');

describe('DocumentHub clinical inference boundary', () => {
  it('does not derive treatment, imaging or medication advice from free-text antecedents or financial labels', () => {
    expect(documentHubSource).not.toContain('antecedents_medicaux');
    expect(documentHubSource).not.toContain('ghost-comp-');
    expect(documentHubSource).not.toContain('Couverture antibiotique stricte recommandée');
    expect(documentHubSource).not.toContain('Radiographies contre-indiquées');
    expect(documentHubSource).not.toContain('Générer Protocole');
  });

  it('keeps prescription safety outside the shared financial/document hub', () => {
    expect(documentHubSource).not.toContain("api.post('/prescriptions/safety/check'");
  });
});
