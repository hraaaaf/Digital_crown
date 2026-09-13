import type { DiagnosticTexts, DonneesEtape2 } from './cephaloTypes';

export const CLINICIAN_DIAGNOSTIC_ORIGIN = 'CLINICIAN_AUTHORED_V1' as const;

const DIAGNOSTIC_KEYS: (keyof DiagnosticTexts)[] = [
  'analyse_dentaire',
  'diagnostic_squelettique',
  'analyse_moulages',
  'synthese_diagnostique',
  'strategie_therapeutique',
];

const EMPTY_DIAGNOSTIC: DiagnosticTexts = {
  analyse_dentaire: '',
  diagnostic_squelettique: '',
  analyse_moulages: '',
  synthese_diagnostique: '',
  strategie_therapeutique: '',
};

export function serializeClinicianDiagnostic(diag: DiagnosticTexts): Record<string, string> {
  return {
    _origin: CLINICIAN_DIAGNOSTIC_ORIGIN,
    ...Object.fromEntries(DIAGNOSTIC_KEYS.map(key => [key, diag[key] || ''])),
  };
}

export function readClinicianDiagnostic(value: unknown): DiagnosticTexts | null {
  if (!value || typeof value !== 'object') return null;
  const candidate = value as Record<string, unknown>;
  if (candidate._origin !== CLINICIAN_DIAGNOSTIC_ORIGIN) return null;
  return DIAGNOSTIC_KEYS.reduce<DiagnosticTexts>((acc, key) => {
    acc[key] = typeof candidate[key] === 'string' ? candidate[key] as string : '';
    return acc;
  }, { ...EMPTY_DIAGNOSTIC });
}

export function sanitizeAnalysisReadPayload<T extends Record<string, any>>(payload: T): T {
  const markedClinician = readClinicianDiagnostic(payload.ai_diagnostic);
  const angles = payload.angles_data && typeof payload.angles_data === 'object'
    ? { ...payload.angles_data }
    : payload.angles_data;
  const hadLegacyNarrative = Boolean(angles?.ai_narrative);
  const hadUnattributedDiagnostic = Boolean(payload.ai_diagnostic) && !markedClinician;

  if (angles && typeof angles === 'object') {
    delete angles.ai_narrative;
    if (hadLegacyNarrative || hadUnattributedDiagnostic) {
      angles.__legacy_clinical_content = 'UNATTRIBUTED_LEGACY';
    }
  }

  return {
    ...payload,
    angles_data: angles,
    ai_diagnostic: markedClinician ? serializeClinicianDiagnostic(markedClinician) : null,
  } as T;
}

export function sanitizeAnalysisUploadPayload<T extends Record<string, any>>(payload: T): T {
  if (!payload.results || typeof payload.results !== 'object') return payload;
  const results = { ...payload.results };
  if (results.ai_narrative) {
    delete results.ai_narrative;
    results.__legacy_clinical_content = 'UNATTRIBUTED_LEGACY';
  }
  return { ...payload, results } as T;
}

const safeArray = (value: unknown): any[] => Array.isArray(value) ? value : [];

export interface ClinicalEvidenceSummary {
  scientificStatus: 'VERIFIED' | 'INCOMPLETE' | 'UNAVAILABLE';
  sourceCount: number;
  landmarkCount: number;
  constructionCount: number;
  measurementCount: number;
  r11: string;
  r12: string;
  r13: string;
  r14: string;
  hasLegacyClinicalContent: boolean;
}

export function summarizeClinicalEvidence(anglesData: Record<string, any> | null | undefined): ClinicalEvidenceSummary {
  const graph = anglesData?._evidence_graph_v1;
  const readPath = anglesData?.scientific_read_path;
  const hasGraph = Boolean(graph && typeof graph === 'object');
  const scientificStatus: ClinicalEvidenceSummary['scientificStatus'] =
    readPath?.active_chain === 'VERIFIED' ? 'VERIFIED' : hasGraph ? 'INCOMPLETE' : 'UNAVAILABLE';

  const sources = safeArray(graph?.sources);
  const landmarks = safeArray(graph?.landmarks);
  const constructions = safeArray(graph?.constructions);
  const measurements = safeArray(graph?.measurements);
  const findings = safeArray(graph?.findings);
  const diagnoses = safeArray(graph?.diagnoses);
  const problems = safeArray(graph?.problems);
  const objectives = safeArray(graph?.objectives);
  const options = safeArray(graph?.treatment_options);
  const finalPlans = safeArray(graph?.final_plans);

  const r11 = findings.length || diagnoses.length
    ? `${findings.length} constat(s) · ${diagnoses.length} diagnostic(s)`
    : 'Non matérialisé';
  const r12 = problems.length || objectives.length
    ? `${problems.length} problème(s) · ${objectives.length} objectif(s)`
    : 'Non matérialisé';
  const r13 = options.length ? `${options.length} option(s) tracée(s)` : 'Non matérialisé';
  const finalStatuses = [...new Set(finalPlans.map(item => item?.status).filter((item): item is string => typeof item === 'string'))];
  const r14 = finalPlans.length
    ? `${finalPlans.length} stratégie(s) · ${finalStatuses.join(', ') || 'statut non renseigné'}`
    : 'Aucune stratégie finale structurée validée';

  return {
    scientificStatus,
    sourceCount: sources.length,
    landmarkCount: Number.isFinite(readPath?.current_landmark_count) ? readPath.current_landmark_count : landmarks.length,
    constructionCount: Number.isFinite(readPath?.current_construction_count) ? readPath.current_construction_count : constructions.length,
    measurementCount: Number.isFinite(readPath?.current_measurement_count) ? readPath.current_measurement_count : measurements.length,
    r11,
    r12,
    r13,
    r14,
    hasLegacyClinicalContent: anglesData?.__legacy_clinical_content === 'UNATTRIBUTED_LEGACY',
  };
}

export function describeOcclusalState(etape2: DonneesEtape2): string {
  const { molaire_droite, molaire_gauche, canine_droite, canine_gauche } = etape2.occlusal;
  const arcade = etape2.type_arcade || 'Indéterminée';
  if (!molaire_droite && !molaire_gauche && !canine_droite && !canine_gauche && arcade === 'Indéterminée') {
    return '';
  }
  return [
    `Classe Molaire : D:${molaire_droite || '—'} / G:${molaire_gauche || '—'}`,
    `Classe Canine : D:${canine_droite || '—'} / G:${canine_gauche || '—'}`,
    `Forme d’arcade : ${arcade}`,
  ].join('\n');
}
