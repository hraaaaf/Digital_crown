/**
 * UI-only nomenclature for clinician-led review. Generated from
 * docs/audits/CEPHALO_J1B1_S3_38_LANDMARK_TERMINOLOGY.json (J1.B1-S3).
 * The 38 model-channel labels are NOT validated automatic anatomy. No coordinates,
 * persistence, clinical decision, measurements, or inference exist in this module.
 * The two occlusal points below are UI constructions, NOT SRPose38 channels.
 */

export const CEPHALO_38_REVIEW_TERMS = [
  { index: 0, id: "S", fr: "Selle turcique", en: "Sella", aliases: ["Sella turcica","S"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 1, id: "N", fr: "Nasion", en: "Nasion", aliases: ["Na","N"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 2, id: "Or", fr: "Orbitale", en: "Orbitale", aliases: ["Or","Bord orbitaire inférieur"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 3, id: "Po", fr: "Porion anatomique", en: "Anatomical porion", aliases: ["Po","Porion"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 4, id: "A", fr: "Point A (subspinale)", en: "Subspinale / A-point", aliases: ["A-point","Subspinale"], sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 5, id: "B", fr: "Point B (supramentale)", en: "Supramentale / B-point", aliases: ["B-point","Supramentale"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 6, id: "Pog", fr: "Pogonion osseux", en: "Bony pogonion", aliases: ["Pg","Pog"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 7, id: "Me", fr: "Menton osseux", en: "Bony menton", aliases: ["Me"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 8, id: "Gn", fr: "Gnathion osseux", en: "Bony gnathion", aliases: ["Gn"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 9, id: "Go", fr: "Gonion / angle mandibulaire", en: "Gonion", aliases: ["Go","Gonion"], sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 10, id: "L1_incisal", fr: "Bord incisif de l’incisive mandibulaire", en: "Lower central incisor incisal edge", aliases: ["L1 tip","Ii","LIE"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 11, id: "U1_incisal", fr: "Bord incisif de l’incisive maxillaire", en: "Upper central incisor incisal edge", aliases: ["U1 tip","Is","UIE"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 12, id: "Ls_soft", fr: "Labrale supérieur (lèvre supérieure)", en: "Labrale superius / upper lip", aliases: ["Ls","Upper lip"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 13, id: "Li_soft", fr: "Labrale inférieur (lèvre inférieure)", en: "Labrale inferius / lower lip", aliases: ["Li","Lower lip"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 14, id: "Sn_soft", fr: "Subnasale", en: "Subnasale", aliases: ["Sn","Soft-tissue subnasale"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 15, id: "Pog_soft", fr: "Pogonion cutané", en: "Soft-tissue pogonion", aliases: ["Pog’","Pg'","Pos"], sourceEvidence: "AUTHOR_PAPER_POS16_ONLY" },
  { index: 16, id: "PNS", fr: "Épine nasale postérieure", en: "Posterior nasal spine", aliases: ["PNS"], sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 17, id: "ANS", fr: "Épine nasale antérieure", en: "Anterior nasal spine", aliases: ["ANS"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 18, id: "Ar", fr: "Articulare", en: "Articulare", aliases: ["Ar"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 19, id: "D_point", fr: "Point D (centre de la symphyse)", en: "Point D (center of mandibular symphysis)", aliases: ["D"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 20, id: "U1_apex", fr: "Apex de l’incisive maxillaire", en: "Upper central incisor root apex", aliases: ["U1A","UIA"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 21, id: "L1_apex", fr: "Apex de l’incisive mandibulaire", en: "Lower central incisor root apex", aliases: ["L1A","LIA"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 22, id: "Cm", fr: "Columelle nasale", en: "Columella", aliases: ["Cm"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 23, id: "Ptm", fr: "Fente ptérygomaxillaire", en: "Pterygomaxillary fissure", aliases: ["Ptm","PTM"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 24, id: "Co", fr: "Condylion", en: "Condylion", aliases: ["Co","Cd"], sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 25, id: "Prn", fr: "Pronasale / pointe du nez", en: "Pronasale", aliases: ["Prn","Pn"], sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 26, id: "Ba", fr: "Basion", en: "Basion", aliases: ["Ba"], sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 27, id: "PT_point", fr: "Point ptérygoïdien (Pt de Ricketts)", en: "Ricketts pterygoid point (Pt)", aliases: ["Pt","PT"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 28, id: "Bo", fr: "Point de Bolton", en: "Bolton point", aliases: ["Bo","Bolton"], sourceEvidence: "AUTHOR_PAPER_EXPLICIT" },
  { index: 29, id: "Ls2", fr: "Point additionnel lèvre supérieure (UL′)", en: "Additional upper lip point UL-prime", aliases: ["UL′","UL'"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 30, id: "Li2", fr: "Point additionnel lèvre inférieure (LL′)", en: "Additional lower lip point LL-prime", aliases: ["LL′","LL'"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 31, id: "Gn_soft", fr: "Gnathion cutané", en: "Soft-tissue gnathion", aliases: ["Gn′","Gns","Gs"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 32, id: "Me_soft", fr: "Menton cutané", en: "Soft-tissue menton", aliases: ["Me′","Mes"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 33, id: "G_soft", fr: "Glabelle cutanée", en: "Soft-tissue glabella", aliases: ["G′","Glabella"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 34, id: "N_soft", fr: "Nasion cutané", en: "Soft-tissue nasion", aliases: ["N′","Ns"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 35, id: "C_point", fr: "Point cervical", en: "Cervical point", aliases: ["C","Neck-throat point"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 36, id: "U6", fr: "Repère de la première molaire maxillaire", en: "Upper first molar landmark", aliases: ["U6","Upper molar"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
  { index: 37, id: "L6", fr: "Repère de la première molaire mandibulaire", en: "Lower first molar landmark", aliases: ["L6","Lower molar"], sourceEvidence: "NO_DIRECT_NUMBERED_AUTHOR_EVIDENCE" },
] as const;

export const CEPHALO_OCCLUSAL_REVIEW_TERMS = [
  { id: "Occ_Ant", fr: "Repère antérieur du plan occlusal (construction à définir)", en: "Occlusal plane anterior point (construction not source-verified)" },
  { id: "Occ_Post", fr: "Repère postérieur du plan occlusal (construction à définir)", en: "Occlusal plane posterior point (construction not source-verified)" },
] as const;

export type CephaloReviewTerm = (typeof CEPHALO_38_REVIEW_TERMS)[number];
