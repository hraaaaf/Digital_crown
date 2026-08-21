import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';

const read = (relative: string) => readFileSync(new URL(relative, import.meta.url), 'utf8');

describe('patient indicators explainable source contracts', () => {
  it('removes automatic VIP language from patient markers', () => {
    const badge = read('./components/PatientScoreBadge.tsx');
    expect(badge).not.toMatch(/Platinum Elite|Gold Status|Bronze \(Vigilance\)|Excellence clinique|Engagement exemplaire/);
    expect(badge).toContain('Aucun historique RDV');
    expect(badge).toContain('Facturation indéterminée');
    expect(badge).toContain('Tag cabinet manuel');
  });

  it('makes the hover factual and responsive', () => {
    const hover = read('./components/PatientSummaryHoverCard.tsx');
    expect(hover).toContain('Repères du dossier');
    expect(hover).toContain('Repères & actions');
    expect(hover).toContain('Données du dossier • règles déterministes');
    expect(hover).not.toContain('data.intelligence_score');
    expect(hover).not.toContain('Alertes IA & Suggestion');
    expect(hover).not.toContain('Assistant Virtuel ODF');
    expect(hover).toContain('viewportWidth - padding * 2');
  });

  it('shows the NBA reason and removes the dead FlashSummary mount', () => {
    const details = read('./PatientDetailsInner.tsx');
    expect(details).toContain('res.data.nba.message');
    expect(details).not.toContain('<FlashSummary');
    expect(details).not.toContain("import { FlashSummary }");
  });

  it('renames the operational no-future-appointment marker', () => {
    const list = read('./PatientList.tsx');
    expect(list).toContain('Sans RDV futur');
    expect(list).not.toContain('> Fantôme<');
  });
});
