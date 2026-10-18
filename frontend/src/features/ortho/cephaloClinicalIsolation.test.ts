import { describe, it, expect } from 'vitest';
import { emptyStudyClinicalContext, hydrateStudyClinicalContext } from './cephaloClinicalIsolation';
import { useOrthoStore } from './stores/useOrthoStore';
import { buildPayload } from './cephaloUtils';

describe('P2ter++ clinical isolation A -> B (synthetic sentinel)', () => {
  it('never falls back to diagnosis, treatment plan, occlusion or DDM from A when B omits fields', () => {
    const a = hydrateStudyClinicalContext({
      ai_diagnostic: {
        synthese_diagnostique: 'SENTINEL_A_DIAGNOSIS',
        strategie_therapeutique: 'SENTINEL_A_TREATMENT',
      },
      clinical_data: {
        ddm_maxillaire: { calcul_ddm: 14 },
        classe_molaire_gauche: 'III',
        preference_technique: 'DAMON',
      },
    });
    const b = hydrateStudyClinicalContext({
      ai_diagnostic: { diagnostic_squelettique: 'STUDY_B_ONLY' },
      clinical_data: {},
    });
    expect(a.diag.strategie_therapeutique).toBe('SENTINEL_A_TREATMENT');
    expect(b.diag.strategie_therapeutique).toBe('');
    expect(b.diag.synthese_diagnostique).toBe('');
    expect(b.ddm.maxillaire).toBe('');
    expect(b.etape2Data.occlusal.molaire_gauche).toBe('');
    expect(b.etape3Data.preference_technique).toBe('');
    expect(b.diag.diagnostic_squelettique).toBe('STUDY_B_ONLY');

    const persistedB = buildPayload(
      [], null, null, null, b.diag, {}, null, b.etape2Data, b.etape3Data,
    );
    expect(JSON.stringify(persistedB)).not.toContain('SENTINEL_A');
    expect(persistedB.clinical_data.plan_traitement).toBe('');
  });

  it('invalidates every clinical field as soon as study changes, before async B hydration', () => {
    const s = useOrthoStore.getState();
    s.setPatientInfo(77291, 'T2 synthetic');
    s.setAnalysisId(12301);
    s.setDiag({ ...emptyStudyClinicalContext().diag, strategie_therapeutique: 'SENTINEL_A' });
    s.setDdm({ maxillaire: 22, mandibulaire: 10 });
    s.setEtape3Data({ ...emptyStudyClinicalContext().etape3Data, preference_technique: 'DAMON' });
    s.setAnalysisId(undefined);
    expect(useOrthoStore.getState().diag.strategie_therapeutique).toBe('');
    expect(useOrthoStore.getState().analysisId).toBeUndefined();
    s.setAnalysisId(12302);
    expect(useOrthoStore.getState().ddm.maxillaire).toBe('');
    expect(useOrthoStore.getState().etape3Data.preference_technique).toBe('');
    s.setDiag(hydrateStudyClinicalContext({ ai_diagnostic: { synthese_diagnostique: 'B' } }).diag);
    expect(JSON.stringify(useOrthoStore.getState().diag)).not.toContain('SENTINEL_A');
  });

  it('never rehydrates legacy per-patient treatment data into another study', () => {
    localStorage.setItem('digitalcrown_etape3_77292', JSON.stringify({
      preference_technique: 'DAMON', strategie_therapeutique: 'SENTINEL_A',
    }));
    useOrthoStore.getState().setPatientInfo(77292, 'T2 different synthetic patient');
    useOrthoStore.getState().setAnalysisId(12303);
    const state = useOrthoStore.getState();
    expect(state.etape3Data.preference_technique).toBe('');
    expect(JSON.stringify(state.diag)).not.toContain('SENTINEL_A');
    expect(JSON.stringify(state.etape3Data)).not.toContain('SENTINEL_A');
  });
});
