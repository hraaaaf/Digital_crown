/**
 * UI-only nomenclature for clinician-led review. Generated from
 * docs/audits/CEPHALO_J1B1_S3_38_LANDMARK_TERMINOLOGY.json (J1.B1-S3).
 * The 38 model-channel labels are NOT validated automatic anatomy. No coordinates,
 * persistence, clinical decision, measurements, or inference exist in this module.
 * The two occlusal points below are UI constructions, NOT SRPose38 channels.
 */

export const CEPHALO_38_REVIEW_TERMS = [
  { index: 0, id: "S", fr: "Selle turcique", en: "Sella", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 1, id: "N", fr: "Nasion", en: "Nasion", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 2, id: "Or", fr: "Orbitale", en: "Orbitale", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 3, id: "Po", fr: "Porion anatomique", en: "Anatomical porion", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 4, id: "A", fr: "Point A (subspinale)", en: "Subspinale / A-point", sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 5, id: "B", fr: "Point B (supramentale)", en: "Supramentale / B-point", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 6, id: "Pog", fr: "Pogonion osseux", en: "Bony pogonion", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 7, id: "Me", fr: "Menton osseux", en: "Bony menton", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 8, id: "Gn", fr: "Gnathion osseux", en: "Bony gnathion", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 9, id: "Go", fr: "Gonion / angle mandibulaire", en: "Gonion", sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 10, id: "L1_incisal", fr: "Bord incisif de l’incisive mandibulaire", en: "Lower central incisor incisal edge", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 11, id: "U1_incisal", fr: "Bord incisif de l’incisive maxillaire", en: "Upper central incisor incisal edge", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 12, id: "Ls_soft", fr: "Labrale supérieur (lèvre supérieure)", en: "Labrale superius / upper lip", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 13, id: "Li_soft", fr: "Labrale inférieur (lèvre inférieure)", en: "Labrale inferius / lower lip", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 14, id: "Sn_soft", fr: "Subnasale", en: "Subnasale", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 15, id: "Pog_soft", fr: "Pogonion cutané", en: "Soft-tissue pogonion", sourceEvidence: "AUTHOR_PAPER_POS16_ONLY" },
  { index: 16, id: "PNS", fr: "Épine nasale postérieure", en: "Posterior nasal spine", sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 17, id: "ANS", fr: "Épine nasale antérieure", en: "Anterior nasal spine", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 18, id: "Ar", fr: "Articulare", en: "Articulare", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 19, id: "D_point", fr: "Point D (centre de la symphyse)", en: "Point D (center of mandibular symphysis)", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 20, id: "U1_apex", fr: "Apex de l’incisive maxillaire", en: "Upper central incisor root apex", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 21, id: "L1_apex", fr: "Apex de l’incisive mandibulaire", en: "Lower central incisor root apex", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 22, id: "Cm", fr: "Columelle nasale", en: "Columella", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 23, id: "Ptm", fr: "Fente ptérygomaxillaire", en: "Pterygomaxillary fissure", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 24, id: "Co", fr: "Condylion", en: "Condylion", sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 25, id: "Prn", fr: "Pronasale / pointe du nez", en: "Pronasale", sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 26, id: "Ba", fr: "Basion", en: "Basion", sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 27, id: "PT_point", fr: "Point ptérygoïdien (Pt de Ricketts)", en: "Ricketts pterygoid point (Pt)", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 28, id: "Bo", fr: "Point de Bolton", en: "Bolton point", sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 29, id: "Ls2", fr: "Point additionnel lèvre supérieure (UL′)", en: "Additional upper lip point UL-prime", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 30, id: "Li2", fr: "Point additionnel lèvre inférieure (LL′)", en: "Additional lower lip point LL-prime", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 31, id: "Gn_soft", fr: "Gnathion cutané", en: "Soft-tissue gnathion", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 32, id: "Me_soft", fr: "Menton cutané", en: "Soft-tissue menton", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 33, id: "G_soft", fr: "Glabelle cutanée", en: "Soft-tissue glabella", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 34, id: "N_soft", fr: "Nasion cutané", en: "Soft-tissue nasion", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 35, id: "C_point", fr: "Point cervical", en: "Cervical point", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 36, id: "U6", fr: "Repère de la première molaire maxillaire", en: "Upper first molar landmark", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 37, id: "L6", fr: "Repère de la première molaire mandibulaire", en: "Lower first molar landmark", sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
] as const;

export const CEPHALO_OCCLUSAL_REVIEW_TERMS = [
  { id: "Occ_Ant", fr: "Repère antérieur du plan occlusal (construction à définir)", en: "Occlusal plane anterior point (construction not source-verified)" },
  { id: "Occ_Post", fr: "Repère postérieur du plan occlusal (construction à définir)", en: "Occlusal plane posterior point (construction not source-verified)" },
] as const;

export type CephaloReviewTerm = (typeof CEPHALO_38_REVIEW_TERMS)[number];
