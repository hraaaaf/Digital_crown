import { describe, expect, it } from 'vitest';

import {
  buildQuoteTransferPayload,
  canTransferPractitionerActs,
  getCompanionOrientation,
  normalizePractitionerAct,
} from './DiagnosticCompanionPolicy';
import { convertPlanActsToQuoteItems } from './AccountingPlanConversionPolicy';

const practitionerActs = [
  { id: '1', phase: 'INITIALE', act: '  Détartrage   complet  ' },
];

describe('DiagnosticCompanionPolicy', () => {
  it('normalizes practitioner text without inventing content', () => {
    expect(normalizePractitionerAct('  Détartrage   complet  ')).toBe('Détartrage complet');
  });

  it('does not transfer without explicit practitioner confirmation', () => {
    expect(canTransferPractitionerActs(practitionerActs, false)).toBe(false);
    expect(buildQuoteTransferPayload(practitionerActs, false)).toEqual([]);
  });

  it('transfers only confirmed practitioner-entered acts', () => {
    const payload = buildQuoteTransferPayload(practitionerActs, true);
    expect(payload).toEqual([
      { suggested_act: 'Détartrage complet', fdi: 'Global', phase: 'INITIALE' },
    ]);
  });

  it('does not expose an autonomous diagnosis in orientation copy', () => {
    const orientation = getCompanionOrientation('PAIN');
    const text = `${orientation.title} ${orientation.checklist.join(' ')}`.toLowerCase();
    expect(text).not.toContain('diagnostic établi');
    expect(text).not.toContain('amoxicill');
    expect(text).not.toContain('clindamyc');
  });

  it('keeps eligible practitioner acts financially neutral in Devis', () => {
    const quoteItems = convertPlanActsToQuoteItems(buildQuoteTransferPayload(practitionerActs, true));
    expect(quoteItems).toHaveLength(1);
    expect(quoteItems[0].description).toBe('Détartrage complet');
    expect(Number(quoteItems[0].price)).toBe(0);
  });

  it('filters medication instructions before Devis', () => {
    const quoteItems = convertPlanActsToQuoteItems([
      { suggested_act: 'Amoxicilline 1 g pendant 7 jours', fdi: 'Global', phase: 'INITIALE' },
    ]);
    expect(quoteItems).toEqual([]);
  });

  it('filters mixed clinical act plus medication wording fail-closed', () => {
    const quoteItems = convertPlanActsToQuoteItems([
      { suggested_act: 'Détartrage + antibiothérapie', fdi: 'Global', phase: 'INITIALE' },
    ]);
    expect(quoteItems).toEqual([]);
  });
});
