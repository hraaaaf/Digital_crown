import { describe, expect, it } from 'vitest';
import { arbitrateForMorocco } from './MoroccoPharmacologyPolicy';

describe('Morocco-first pharmacology gate', () => {
  it('blocks automatic proposal when Moroccan AMM is not verified', () => {
    const result = arbitrateForMorocco({
      molecule: 'AMOXICILLINE',
      ammVerified: false,
      moroccoRegimenEvidenceIds: [],
      internationalSupportEvidenceIds: ['SDCEP_AMOXICILLIN'],
    });
    expect(result.status).toBe('morocco_amm_unverified');
    expect(result.mayAutoProposeRegimen).toBe(false);
  });

  it('keeps foreign guidance as review-only when Morocco regimen guidance is missing', () => {
    const result = arbitrateForMorocco({
      molecule: 'AMOXICILLINE',
      ammVerified: true,
      ammEvidenceId: 'MOROCCO_AMM',
      moroccoRegimenEvidenceIds: [],
      internationalSupportEvidenceIds: ['SDCEP_AMOXICILLIN'],
    });
    expect(result.status).toBe('morocco_guideline_gap');
    expect(result.mayAutoProposeRegimen).toBe(false);
    expect(result.evidenceIds).toContain('MOROCCO_AMM');
    expect(result.evidenceIds).toContain('SDCEP_AMOXICILLIN');
  });

  it('fails closed on a Morocco/international evidence conflict', () => {
    const result = arbitrateForMorocco({
      molecule: 'EXAMPLE',
      ammVerified: true,
      ammEvidenceId: 'MOROCCO_AMM',
      moroccoRegimenEvidenceIds: ['MOROCCO_RULE'],
      internationalSupportEvidenceIds: ['FOREIGN_RULE'],
      conflict: 'Local rule differs from foreign guidance',
    });
    expect(result.status).toBe('morocco_conflict');
    expect(result.mayAutoProposeRegimen).toBe(false);
  });

  it('allows automatic proposal only when Morocco AMM and Morocco regimen evidence are both present', () => {
    const result = arbitrateForMorocco({
      molecule: 'PARACETAMOL',
      ammVerified: true,
      ammEvidenceId: 'MOROCCO_AMM',
      moroccoRegimenEvidenceIds: ['MOROCCO_PARACETAMOL'],
      internationalSupportEvidenceIds: ['SDCEP_PARACETAMOL'],
    });
    expect(result.status).toBe('morocco_verified');
    expect(result.mayAutoProposeRegimen).toBe(true);
    expect(result.evidenceIds).toEqual(['MOROCCO_AMM', 'MOROCCO_PARACETAMOL']);
  });
});
