import type { 
  Landmark, CVMStage, UIMode, StepId, SyncState, ImageFilters, VTOSettings 
} from './cephaloShared';

export interface DDMState {
  maxillaire: number | '';
  mandibulaire: number | '';
}

export interface DiagnosticTexts {
  squelettique: string;
  compensations_dentaires: string;
  plan_therapeutique: string;
}

export interface LocalState {
  landmarks: Landmark[];
  version: number;
}

// --- ÉTAPE 3 : PROTOCOLE COM ---
export type ClasseAngle = 'I' | 'II' | 'III';
export type DivisionClasseII = '1' | '2' | null;
export type TypeArcade = 'I' | 'II' | null;
export type PatternVertical = 'hypodivergent' | 'normodivergent' | 'hyperdivergent';
export type ProfilFacial = 'convexe' | 'droit' | 'concave';
export type SeveriteDDM = 'léger' | 'modéré' | 'sévère' | 'excès';

export interface AnalyseDentaire {
  surplomb: number | '';
  recouvrement: number | '';
  impa: number | '';
  i_francfort: number | '';
  inter_incisif: number | '';
}

export interface AnalyseOsseuse {
  angle_tweed: number | '';
  decalage_ab: number | '';
  situation_a: number | '';
  situation_b: number | '';
  profondeur_faciale: number | '';
}

export interface ExamenOcclusal {
  molaire_gauche: ClasseAngle;
  molaire_droite: ClasseAngle;
  canine_gauche: ClasseAngle;
  canine_droite: ClasseAngle;
}

export interface AnalyseEsthetique {
  ligne_e_ls: number | '';
  ligne_e_li: number | '';
}

export interface DonneesEtape3 {
  age: number | '';
  cvm: CVMStage | '';
  date_teles: string;
  dentaire: AnalyseDentaire;
  osseuse: AnalyseOsseuse;
  esthetique: AnalyseEsthetique;
  ddm_clinique: number | '';
  ddm_cephalo: number | '';
  division: DivisionClasseII;
  type_arcade: TypeArcade;
  classe_squelettique: string;
  pattern_vertical: PatternVertical | '';
  profil: ProfilFacial | '';
  severite_ddm: SeveriteDDM | '';
  subdivision: boolean;
}

export interface DonneesEtape2 {
  occlusal: ExamenOcclusal;
}

export interface PhotoUpload {
  id: string;
  type: 'radio' | 'moulage_max' | 'moulage_mand' | 'intra_face' | 'intra_profile' | 'extra_face' | 'extra_profile' | 'extra_sourire';
  file: File | null;
  preview: string | null;
  label: string;
}

