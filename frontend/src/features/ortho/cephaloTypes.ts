import type { 
  Landmark, CVMStage
} from './cephaloShared';

export interface DDMState {
  maxillaire: number | '';
  mandibulaire: number | '';
}

export interface DiagnosticTexts {
  analyse_dentaire: string;
  diagnostic_squelettique: string;
  analyse_moulages: string;
  synthese_diagnostique: string;
  strategie_therapeutique: string;
}

export interface LocalState {
  landmarks: Landmark[];
  version: number;
}

// --- ÉTAPE 3 : PROTOCOLE COM ---
export type ClasseAngle = 'I' | 'II' | 'III';
export type DivisionClasseII = '1' | '2' | '' | null;
export type TypeArcade = 'U' | 'V' | 'CARREE' | '' | null;
export type PatternVertical = 'hypodivergent' | 'normodivergent' | 'hyperdivergent';
export type ProfilFacial = 'convexe' | 'droit' | 'concave';
export type SeveriteDDM = 'léger' | 'modéré' | 'sévère' | 'excès';

export interface AnalyseDentaire {
  surplomb: number | '';
  recouvrement: number | '';
  impa: number | '';
  i_francfort: number | '';
  inter_incisif: number | '';
  i_na_angle?: number | '';
  i_na_mm?: number | '';
  i_nb_angle?: number | '';
  i_nb_mm?: number | '';
  fmia?: number | '';
}


export interface AnalyseOsseuse {
  angle_tweed: number | '';
  decalage_ab: number | '';
  situation_a: number | '';
  situation_b: number | '';
  profondeur_faciale: number | '';
  sna: number | '';
  snb: number | '';
  anb: number | '';
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
  angle_nasolabial: number | '';
}

export interface AnalyseWitsMcNamara {
  wits_appraisal?: number | '';
  longueur_maxillaire?: number | '';
  longueur_mandibulaire?: number | '';
  differentiel_max_mand?: number | '';
  etage_inferieur_face?: number | '';
}

export interface DonneesPanoramique {
  dds_incluses?: boolean;
  perte_osseuse?: boolean;
  asymetrie_condylienne?: boolean;
  resorption_radiculaire?: boolean;
}

export interface DonneesEtape3 {
  age: number | '';
  cvm: CVMStage | '';
  date_teles: string;
  dentaire: AnalyseDentaire;
  osseuse: AnalyseOsseuse;
  esthetique: AnalyseEsthetique;
  wits_mcnamara?: AnalyseWitsMcNamara;
  panoramique?: DonneesPanoramique;
  ddm_clinique: number | '';
  ddm_cephalo: number | '';
  division: DivisionClasseII;
  classe_squelettique: string;
  pattern_vertical: PatternVertical | '';
  profil: ProfilFacial | '';
  severite_ddm: SeveriteDDM | '';
  subdivision: boolean;
  analyse_moulages_auto: string;
  selectedAnalysis: 'COM' | 'STEINER' | 'TWEED' | 'MCNAMARA' | 'WITS' | 'ALL';
  denture_type: 'TEMPORAIRE' | 'MIXTE' | 'PERMANENTE' | '';
  preference_technique: 'DAMON' | 'CLASSIC' | 'ALIGNEURS' | '';
}

export interface DonneesEtape2 {
  occlusal: ExamenOcclusal;
  type_arcade: TypeArcade;
}

export interface PhotoUpload {
  id: string;
  type: 'radio' | 'moulage_max' | 'moulage_mand' | 'intra_face' | 'intra_profile' | 'extra_face' | 'extra_profile' | 'extra_sourire';
  file: File | null;
  preview: string | null;
  label: string;
}

