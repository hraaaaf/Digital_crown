import { describe, expect, it } from 'vitest';
import {
  CLINICIAN_DIAGNOSTIC_ORIGIN,
  describeOcclusalState,
  readClinicianDiagnostic,
  sanitizeAnalysisReadPayload,
  sanitizeAnalysisUploadPayload,
  serializeClinicianDiagnostic,
  summarizeClinicalEvidence,
} from './cephaloClinicalEvidence';

const diag = {
  analyse_dentaire: 'dentaire',
  diagnostic_squelettique: 'squelette',
  analyse_moulages: 'moulages',
  synthese_diagnostique: 'synthèse',
  strategie_therapeutique: 'plan praticien',
};

describe('R15 clinician provenance', () => {
  it('rejects unmarked legacy diagnostic content for editable clinician fields', () => {
    expect(readClinicianDiagnostic(diag)).toBeNull();
  });

  it('serializes and reloads clinician-authored content with an explicit origin', () => {
    const serialized = serializeClinicianDiagnostic(diag);
    expect(serialized._origin).toBe(CLINICIAN_DIAGNOSTIC_ORIGIN);
    expect(readClinicianDiagnostic(serialized)).toEqual(diag);
  });

  it('removes ambiguous history narratives while preserving marked clinician content', () => {
    const legacy = sanitizeAnalysisReadPayload({
      ai_diagnostic: diag,
      angles_data: { ai_narrative: { diagnostic_squelettique: 'machine' }, metrics: {} },
    });
    expect(legacy.ai_diagnostic).toBeNull();
    expect(legacy.angles_data.ai_narrative).toBeUndefined();
    expect(legacy.angles_data.__legacy_clinical_content).toBe('UNATTRIBUTED_LEGACY');

    const marked = sanitizeAnalysisReadPayload({
      ai_diagnostic: serializeClinicianDiagnostic(diag),
      angles_data: { metrics: {} },
    });
    expect(readClinicianDiagnostic(marked.ai_diagnostic)).toEqual(diag);
    expect(marked.angles_data.__legacy_clinical_content).toBeUndefined();
  });

  it('removes fresh automated narrative before the store can promote it', () => {
    const payload = sanitizeAnalysisUploadPayload({
      results: { ai_narrative: { synthese_diagnostique: 'machine' }, metrics: {} },
    });
    expect(payload.results.ai_narrative).toBeUndefined();
    expect(payload.results.__legacy_clinical_content).toBe('UNATTRIBUTED_LEGACY');
  });
});

describe('R15 evidence summary', () => {
  it('reports a verified scientific chain and honest non-materialized R11-R14 states', () => {
    const summary = summarizeClinicalEvidence({
      scientific_read_path: {
        active_chain: 'VERIFIED',
        current_landmark_count: 12,
        current_construction_count: 7,
        current_measurement_count: 7,
      },
      _evidence_graph_v1: {
        sources: [{}, {}], landmarks: [{}], constructions: [{}], measurements: [{}],
        findings: [], diagnoses: [], problems: [], objectives: [], treatment_options: [], final_plans: [],
      },
    });
    expect(summary.scientificStatus).toBe('VERIFIED');
    expect(summary.sourceCount).toBe(2);
    expect(summary.landmarkCount).toBe(12);
    expect(summary.constructionCount).toBe(7);
    expect(summary.measurementCount).toBe(7);
    expect(summary.r11).toBe('Non matérialisé');
    expect(summary.r12).toBe('Non matérialisé');
    expect(summary.r13).toBe('Non matérialisé');
    expect(summary.r14).toBe('Aucune stratégie finale structurée validée');
  });

  it('reflects real structured objects without extrapolating them', () => {
    const summary = summarizeClinicalEvidence({
      _evidence_graph_v1: {
        sources: [], landmarks: [], constructions: [], measurements: [],
        findings: [{ finding_id: 'f1' }], diagnoses: [{ diagnosis_id: 'd1' }],
        problems: [{ problem_id: 'p1' }], objectives: [{ objective_id: 'o1' }],
        treatment_options: [{ option_id: 't1' }, { option_id: 't2' }],
        final_plans: [{ final_plan_id: 'fp1', status: 'VALIDATED' }],
      },
    });
    expect(summary.scientificStatus).toBe('INCOMPLETE');
    expect(summary.r11).toBe('1 constat(s) · 1 diagnostic(s)');
    expect(summary.r12).toBe('1 problème(s) · 1 objectif(s)');
    expect(summary.r13).toBe('2 option(s) tracée(s)');
    expect(summary.r14).toBe('1 stratégie(s) · VALIDATED');
  });

  it('reports no evidence when no graph exists', () => {
    expect(summarizeClinicalEvidence({}).scientificStatus).toBe('UNAVAILABLE');
  });
});

describe('R15 occlusal description', () => {
  it('keeps automatic occlusal description read-only and separate from clinician notes', () => {
    const text = describeOcclusalState({
      occlusal: { molaire_droite: 'I', molaire_gauche: 'II', canine_droite: 'I', canine_gauche: 'I' },
      type_arcade: 'U',
    });
    expect(text).toContain('Classe Molaire');
    expect(text).toContain('Forme d’arcade : U');
  });
});
