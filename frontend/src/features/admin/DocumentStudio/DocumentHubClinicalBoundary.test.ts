import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const documentHubSource = readFileSync(new URL('../DocumentHub.tsx', import.meta.url), 'utf8');
const studioFooterSource = readFileSync(new URL('./StudioFooter.tsx', import.meta.url), 'utf8');

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

  it('does not expose the uncertified ai-diagnostic executor in the Document Studio footer', () => {
    expect(studioFooterSource).not.toContain('Lancer Analyse IA');
    expect(studioFooterSource).not.toContain('Régénérer Analyse');
    expect(studioFooterSource).not.toContain('onClick={onGenerateAI}');
    expect(studioFooterSource).toContain('Fonction clinique désactivée');
  });
});
