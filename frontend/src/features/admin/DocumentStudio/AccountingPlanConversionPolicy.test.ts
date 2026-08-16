import { describe, expect, it, vi } from 'vitest';
import {
  convertPlanActsToQuoteItems,
  isPlanProposalQuoteEligible,
} from './AccountingPlanConversionPolicy';

describe('AccountingPlanConversionPolicy', () => {
  it('converts procedural plan acts without inventing prices', () => {
    vi.spyOn(Date, 'now').mockReturnValue(1000);
    const rows = convertPlanActsToQuoteItems([
      { suggested_act: 'Couronne zircone', fdi: 11, phase: 'PROTHETIQUE' },
      { act: 'Détartrage', phase: 'ASSAINISSEMENT' },
    ]);

    expect(rows).toEqual([
      {
        id: 1000,
        description: 'Couronne zircone',
        dent: '11',
        price: 0,
        toothNumbers: [11],
        category: 'PROTHETIQUE',
      },
      {
        id: 1001,
        description: 'Détartrage',
        dent: '0',
        price: 0,
        toothNumbers: [],
        category: 'ASSAINISSEMENT',
      },
    ]);
    vi.restoreAllMocks();
  });

  it('fails closed for medication, prescription, follow-up and education guidance', () => {
    const proposals = [
      { act: 'Prescription antalgique (Palier 2)' },
      { act: 'Antibiothérapie et antalgiques' },
      { act: 'Antibiothérapie et anti-inflammatoires stéroïdiens' },
      { act: 'Surveillance régulière de la vitalité pulpaire' },
      { act: "Enseignement à l'hygiène orale" },
      { act: 'Contention flexible et antibiothérapie prophylactique' },
    ];

    expect(proposals.every(act => !isPlanProposalQuoteEligible(act))).toBe(true);
    expect(convertPlanActsToQuoteItems(proposals)).toEqual([]);
  });

  it('keeps clearly procedural clinical acts eligible for practitioner pricing', () => {
    expect(isPlanProposalQuoteEligible({ act: 'Pulpectomie et parage canalaire' })).toBe(true);
    expect(isPlanProposalQuoteEligible({ act: 'Incision, drainage et lavage' })).toBe(true);
    expect(isPlanProposalQuoteEligible({ act: 'Application topique de vernis fluoré' })).toBe(true);
  });

  it('drops empty proposals', () => {
    expect(convertPlanActsToQuoteItems([{ act: '   ' }])).toEqual([]);
  });
});
