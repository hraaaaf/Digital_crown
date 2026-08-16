import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const documentStudioDir = resolve(process.cwd(), 'src/features/admin/DocumentStudio');
const documentHubSource = readFileSync(resolve(documentStudioDir, '../DocumentHub.tsx'), 'utf8');
const studioHeaderSource = readFileSync(resolve(documentStudioDir, 'StudioHeader.tsx'), 'utf8');
const studioFooterSource = readFileSync(resolve(documentStudioDir, 'StudioFooter.tsx'), 'utf8');

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

  it('does not expose or type the uncertified ai-diagnostic executor in the Document Studio shell', () => {
    for (const source of [studioHeaderSource, studioFooterSource]) {
      expect(source).not.toContain('Lancer Analyse IA');
      expect(source).not.toContain('Régénérer Analyse');
      expect(source).not.toContain('onGenerateAI');
      expect(source).not.toContain("| 'ai'");
      expect(source).not.toContain("activeTab === 'ai'");
    }
  });
});