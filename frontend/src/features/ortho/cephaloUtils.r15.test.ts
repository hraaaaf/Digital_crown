import { describe, expect, it } from 'vitest';
import { buildPayload, computeStep3Data } from './cephaloUtils';
import { CLINICIAN_DIAGNOSTIC_ORIGIN } from './cephaloClinicalEvidence';

const diag = {
  analyse_dentaire: 'dentaire',
  diagnostic_squelettique: 'squelette',
  analyse_moulages: 'moulages',
  synthese_diagnostique: 'synthèse',
  strategie_therapeutique: 'plan praticien',
};

describe('R15 payload provenance', () => {
  it('marks every newly saved clinician note set as CLINICIAN_AUTHORED_V1', () => {
    const payload = buildPayload([], null, null, null, diag, {});
    expect(payload.ai_diagnostic._origin).toBe(CLINICIAN_DIAGNOSTIC_ORIGIN);
    expect(payload.ai_diagnostic.synthese_diagnostique).toBe('synthèse');
    expect(payload.ai_diagnostic.strategie_therapeutique).toBe('plan praticien');
  });

  it('never rebuilds an editable mould note from automatic occlusal data', () => {
    const computed = computeStep3Data([], 15, 'M', null, {
      occlusal: {
        molaire_gauche: 'I', molaire_droite: 'II',
        canine_gauche: 'I', canine_droite: 'I',
      },
      type_arcade: 'U',
    });
    expect(computed.analyse_moulages_auto).toBe('');
  });
});
