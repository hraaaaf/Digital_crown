/** P2ter++: clinical fields belong to one study, never a patient-wide fallback. */
import type { DDMState, DiagnosticTexts, DonneesEtape2, DonneesEtape3 } from './cephaloTypes';

export interface StudyClinicalContext {
  ddm: DDMState;
  diag: DiagnosticTexts;
  etape2Data: DonneesEtape2;
  etape3Data: DonneesEtape3;
}

export function emptyStudyClinicalContext(): StudyClinicalContext {
  return {
    ddm: { maxillaire: '', mandibulaire: '' },
    diag: {
      analyse_dentaire: '', diagnostic_squelettique: '', analyse_moulages: '',
      synthese_diagnostique: '', strategie_therapeutique: '',
    },
    etape2Data: {
      occlusal: { molaire_gauche: '', molaire_droite: '', canine_gauche: '', canine_droite: '' },
      type_arcade: null,
    },
    etape3Data: {
      age: '', cvm: '', date_teles: new Date().toISOString().split('T')[0],
      dentaire: { surplomb: '', recouvrement: '', impa: '', i_francfort: '', inter_incisif: '' },
      osseuse: { angle_tweed: '', decalage_ab: '', situation_a: '', situation_b: '', profondeur_faciale: '', sna: '', snb: '', anb: '' },
      esthetique: { ligne_e_ls: '', ligne_e_li: '', angle_nasolabial: '' },
      ddm_clinique: '', ddm_cephalo: '', division: null, classe_squelettique: '',
      pattern_vertical: '', profil: '', severite_ddm: '', subdivision: false, analyse_moulages_auto: '',
      selectedAnalysis: 'COM', denture_type: '', preference_technique: '',
    },
  };
}

const text = (v: unknown): string => typeof v === 'string' ? v : '';
const num = (v: unknown): number | '' => typeof v === 'number' && Number.isFinite(v) ? v : '';
const angle = (v: unknown): 'I' | 'II' | 'III' | '' =>
  v === 'I' || v === 'II' || v === 'III' ? v : '';

export function hydrateStudyClinicalContext(angles: unknown): StudyClinicalContext {
  const fresh = emptyStudyClinicalContext();
  if (!angles || typeof angles !== 'object') return fresh;
  const a = angles as Record<string, unknown>;
  const diagnostic = a.ai_diagnostic && typeof a.ai_diagnostic === 'object'
    ? a.ai_diagnostic as Record<string, unknown>
    : a.ai_narrative && typeof a.ai_narrative === 'object'
      ? a.ai_narrative as Record<string, unknown> : {};
  const clinical = a.clinical_data && typeof a.clinical_data === 'object'
    ? a.clinical_data as Record<string, unknown> : {};
  fresh.diag = {
    analyse_dentaire: text(diagnostic.analyse_dentaire),
    diagnostic_squelettique: text(diagnostic.diagnostic_squelettique),
    analyse_moulages: text(diagnostic.analyse_moulages),
    synthese_diagnostique: text(diagnostic.synthese_diagnostique),
    strategie_therapeutique: text(diagnostic.strategie_therapeutique) || text(clinical.plan_traitement),
  };
  const ddmOf = (key: string): number | '' => {
    const raw = clinical[key];
    return raw && typeof raw === 'object' ? num((raw as Record<string, unknown>).calcul_ddm) : '';
  };
  fresh.ddm = { maxillaire: ddmOf('ddm_maxillaire'), mandibulaire: ddmOf('ddm_mandibulaire') };
  fresh.etape2Data = {
    occlusal: {
      molaire_gauche: angle(clinical.classe_molaire_gauche),
      molaire_droite: angle(clinical.classe_molaire_droite),
      canine_gauche: angle(clinical.classe_canine_gauche),
      canine_droite: angle(clinical.classe_canine_droite),
    },
    type_arcade: clinical.forme_arcade === 'U' || clinical.forme_arcade === 'V'
      || clinical.forme_arcade === 'CARREE' ? clinical.forme_arcade : null,
  };
  if (typeof clinical.age === 'number' && Number.isFinite(clinical.age)) fresh.etape3Data.age = clinical.age;
  if (clinical.denture_type === 'TEMPORAIRE' || clinical.denture_type === 'MIXTE'
      || clinical.denture_type === 'PERMANENTE') fresh.etape3Data.denture_type = clinical.denture_type;
  if (clinical.preference_technique === 'DAMON' || clinical.preference_technique === 'CLASSIC'
      || clinical.preference_technique === 'ALIGNEURS') fresh.etape3Data.preference_technique = clinical.preference_technique;
  return fresh;
}
