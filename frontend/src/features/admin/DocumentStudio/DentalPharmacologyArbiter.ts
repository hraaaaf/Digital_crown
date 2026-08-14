// Evidence-backed pharmacology arbitration for Document Studio.
//
// Safety principles:
// - molecule-first, never brand-first;
// - no inferred paediatric weight;
// - no automatic therapeutic substitution;
// - no regimen is returned unless an explicit source-backed rule matches;
// - conflicts / missing context fail closed to practitioner review.
//
// Primary dental source baseline (reviewed 2026-08-14):
// SDCEP Drug Prescribing for Dentistry, aligned with BNF 91 / BNFC 2025-2026.
// Bacterial infection guidance updated May/June 2026.
// WHO AWaRe is used for antimicrobial-stewardship classification/policy support,
// not as a replacement for local/national dental guidance.

export type EvidenceAuthority = 'SDCEP_BNF' | 'WHO_AWARE' | 'NATIONAL_REGULATOR';

export interface PharmacologyEvidence {
  id: string;
  authority: EvidenceAuthority;
  title: string;
  url: string;
  reviewedAt: string;
  note?: string;
}

export interface PatientPharmacologyContext {
  ageYears?: number | null;
  weightKg?: number | null;
  pregnancy?: boolean | null;
  breastfeeding?: boolean | null;
  renalImpairment?: boolean | null;
  hepaticImpairment?: boolean | null;
  anticoagulant?: string | null;
  antiplatelet?: string | null;
  allergies?: string[];
}

export interface RegimenResult {
  molecule: string;
  dosage: string;
  posology: string;
  duration?: string;
  form?: string;
  evidenceIds: string[];
  paediatric: boolean;
}

export type ArbitrationStatus =
  | 'applicable'
  | 'requires_weight'
  | 'requires_review'
  | 'not_recommended_for_context'
  | 'no_evidence';

export interface PharmacologyArbitration {
  status: ArbitrationStatus;
  regimen: RegimenResult | null;
  messages: string[];
  evidenceIds: string[];
}

export interface DentalAbscessContext {
  localMeasuresAttempted?: boolean;
  localMeasuresEffective?: boolean;
  spreadingInfection?: boolean;
  systemicInvolvement?: boolean;
  highRiskComplications?: boolean;
  severeInfection?: boolean;
  firstLineCompletedWithoutResponse?: boolean;
}

export const PHARMACOLOGY_EVIDENCE: Record<string, PharmacologyEvidence> = {
  SDCEP_GUIDANCE: {
    id: 'SDCEP_GUIDANCE',
    authority: 'SDCEP_BNF',
    title: 'Drug Prescribing for Dentistry — Guidance',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/',
    reviewedAt: '2026-08-14',
    note: 'Current site states consistency with BNF 91 (March 2026) and BNFC 2025-2026.',
  },
  SDCEP_BACTERIAL_2026: {
    id: 'SDCEP_BACTERIAL_2026',
    authority: 'SDCEP_BNF',
    title: 'Bacterial infections — Drug Prescribing for Dentistry',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/',
    reviewedAt: '2026-08-14',
    note: 'Updated May 2026; review timing clarified June 2026.',
  },
  SDCEP_DENTAL_ABSCESS: {
    id: 'SDCEP_DENTAL_ABSCESS',
    authority: 'SDCEP_BNF',
    title: 'Dental abscess — Drug Prescribing for Dentistry',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_PEN_V: {
    id: 'SDCEP_PEN_V',
    authority: 'SDCEP_BNF',
    title: 'Phenoxymethylpenicillin — Dental abscess',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/first-line-antibiotics/phenoxymethylpenicillin/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_AMOXICILLIN: {
    id: 'SDCEP_AMOXICILLIN',
    authority: 'SDCEP_BNF',
    title: 'Amoxicillin — Dental abscess',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/first-line-antibiotics/amoxicillin/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_METRONIDAZOLE: {
    id: 'SDCEP_METRONIDAZOLE',
    authority: 'SDCEP_BNF',
    title: 'Metronidazole — Dental abscess',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/first-line-antibiotics/metronidazole/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_CLINDAMYCIN: {
    id: 'SDCEP_CLINDAMYCIN',
    authority: 'SDCEP_BNF',
    title: 'Clindamycin — Dental abscess second-line',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/second-line-antibiotics/clindamycin/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_CLARITHROMYCIN: {
    id: 'SDCEP_CLARITHROMYCIN',
    authority: 'SDCEP_BNF',
    title: 'Clarithromycin — Dental abscess second-line',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/bacterial-infections/dental-abscess/second-line-antibiotics/clarithromycin/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_PARACETAMOL: {
    id: 'SDCEP_PARACETAMOL',
    authority: 'SDCEP_BNF',
    title: 'Paracetamol — Odontogenic pain',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/odontogenic-pain/analgesics/paracetamol/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_IBUPROFEN: {
    id: 'SDCEP_IBUPROFEN',
    authority: 'SDCEP_BNF',
    title: 'Ibuprofen — Odontogenic pain',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/odontogenic-pain/analgesics/ibuprofen/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_MICONAZOLE: {
    id: 'SDCEP_MICONAZOLE',
    authority: 'SDCEP_BNF',
    title: 'Miconazole — Candidosis',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/fungal-infections/candidosis/miconazole/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_FLUCONAZOLE: {
    id: 'SDCEP_FLUCONAZOLE',
    authority: 'SDCEP_BNF',
    title: 'Fluconazole — Candidosis',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/fungal-infections/candidosis/fluconazole/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_CHLORHEXIDINE: {
    id: 'SDCEP_CHLORHEXIDINE',
    authority: 'SDCEP_BNF',
    title: 'Chlorhexidine mouthwash — Ulceration & inflammation',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/ulceration-inflammation/antimicrobial-mouthwashes/chlorhexidine-mouthwash/',
    reviewedAt: '2026-08-14',
  },
  SDCEP_BENZYDAMINE: {
    id: 'SDCEP_BENZYDAMINE',
    authority: 'SDCEP_BNF',
    title: 'Benzydamine mouthwash — Local analgesics',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/ulceration-inflammation/local-analgesics/benzydamine-mouthwash/',
    reviewedAt: '2026-08-14',
  },
  WHO_AWARE: {
    id: 'WHO_AWARE',
    authority: 'WHO_AWARE',
    title: 'WHO AWaRe antibiotic book',
    url: 'https://www.who.int/publications/i/item/9789240062382',
    reviewedAt: '2026-08-14',
    note: 'Stewardship support; does not replace local/national guidance.',
  },
};

const normalize = (value: string) => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toUpperCase()
  .trim();

const hasPenicillinImmediateAllergy = (ctx: PatientPharmacologyContext) => {
  const allergies = (ctx.allergies || []).map(normalize).join(' ');
  return allergies.includes('PENICILL') || allergies.includes('AMOXICILL') || allergies.includes('BETA LACTAM');
};

const age = (ctx: PatientPharmacologyContext) =>
  typeof ctx.ageYears === 'number' && Number.isFinite(ctx.ageYears) && ctx.ageYears >= 0
    ? ctx.ageYears
    : null;

const weight = (ctx: PatientPharmacologyContext) =>
  typeof ctx.weightKg === 'number' && Number.isFinite(ctx.weightKg) && ctx.weightKg > 0
    ? ctx.weightKg
    : null;

function applicable(regimen: RegimenResult): PharmacologyArbitration {
  return { status: 'applicable', regimen, messages: [], evidenceIds: regimen.evidenceIds };
}

function review(message: string, evidenceIds: string[] = []): PharmacologyArbitration {
  return { status: 'requires_review', regimen: null, messages: [message], evidenceIds };
}

function noEvidence(molecule: string): PharmacologyArbitration {
  return {
    status: 'no_evidence',
    regimen: null,
    messages: [`Aucune règle dentaire sourcée n'est enregistrée pour ${molecule}. Validation manuelle requise.`],
    evidenceIds: [],
  };
}

function paracetamol(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  const a = age(ctx);
  if (a == null) return review('Âge requis pour arbitrer la dose de paracétamol.', ['SDCEP_PARACETAMOL']);
  let dose = '';
  if (a < 0.5) return review('Règle SDCEP intégrée non applicable avant 6 mois.', ['SDCEP_PARACETAMOL']);
  if (a < 2) dose = '120MG';
  else if (a < 4) dose = '180MG';
  else if (a < 6) dose = '240MG';
  else if (a < 8) dose = '240-250MG';
  else if (a < 10) dose = '360-375MG';
  else if (a < 12) dose = '480-500MG';
  else if (a < 16) dose = '480-750MG';
  else if (a < 18) dose = '500MG-1G';
  else dose = '1G';
  return applicable({
    molecule: 'PARACETAMOL', dosage: dose,
    posology: a >= 18 ? '1 g, 4 fois par jour' : `${dose}, 4 fois par jour (max. 4 prises/24 h)`,
    duration: 'jusqu’à 5 jours pour douleur odontogène/post-opératoire',
    form: a >= 18 ? 'COMPRIMÉS' : 'FORME ADAPTÉE À L’ÂGE',
    evidenceIds: ['SDCEP_PARACETAMOL'], paediatric: a < 18,
  });
}

function ibuprofen(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  const a = age(ctx);
  if (ctx.pregnancy) return review('Grossesse : arbitrage AINS requis avant proposition.', ['SDCEP_IBUPROFEN']);
  if (ctx.antiplatelet && normalize(ctx.antiplatelet).includes('ASPIR')) {
    return review('Ibuprofène non proposé automatiquement chez un patient sous aspirine faible dose.', ['SDCEP_IBUPROFEN']);
  }
  if (a == null) return review('Âge requis pour arbitrer la dose d’ibuprofène.', ['SDCEP_IBUPROFEN']);
  if (a < 0.5) return review('Règle SDCEP intégrée non applicable avant 6 mois.', ['SDCEP_IBUPROFEN']);
  let dosage = '';
  let posology = '';
  if (a < 1) { dosage = '50MG'; posology = '50 mg 4 fois par jour, de préférence après nourriture'; }
  else if (a < 4) { dosage = '100MG'; posology = '100 mg 3 fois par jour, de préférence après nourriture'; }
  else if (a < 7) { dosage = '150MG'; posology = '150 mg 3 fois par jour, de préférence après nourriture'; }
  else if (a < 10) { dosage = '200MG'; posology = '200 mg 3 fois par jour, de préférence après nourriture'; }
  else if (a < 12) { dosage = '300MG'; posology = '300 mg 3 fois par jour, de préférence après nourriture'; }
  else if (a < 18) { dosage = '300-400MG'; posology = '300–400 mg 4 fois par jour, de préférence après nourriture'; }
  else { dosage = '400MG'; posology = '400 mg 4 fois par jour, de préférence après nourriture'; }
  return applicable({ molecule: 'IBUPROFENE', dosage, posology, duration: 'jusqu’à 5 jours', form: 'FORME ADAPTÉE À L’ÂGE', evidenceIds: ['SDCEP_IBUPROFEN'], paediatric: a < 18 });
}

function phenoxymethylpenicillin(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  if (hasPenicillinImmediateAllergy(ctx)) return { status: 'not_recommended_for_context', regimen: null, messages: ['Allergie immédiate aux pénicillines : ne pas proposer automatiquement.'], evidenceIds: ['SDCEP_PEN_V'] };
  const a = age(ctx);
  if (a == null) return review('Âge requis pour arbitrer la phénoxyméthylpénicilline.', ['SDCEP_PEN_V']);
  let dose = '';
  if (a < 0.5) return review('Règle SDCEP intégrée non applicable avant 6 mois.', ['SDCEP_PEN_V']);
  if (a < 1) dose = '62.5MG';
  else if (a < 6) dose = '125MG';
  else if (a < 12) dose = '250MG';
  else dose = '500MG';
  return applicable({ molecule: 'PHENOXYMETHYLPENICILLINE', dosage: dose, posology: `${dose} 4 fois par jour`, duration: '3–5 jours; revue idéalement à 3 jours', form: 'COMPRIMÉS OU SOLUTION ORALE', evidenceIds: ['SDCEP_PEN_V', 'SDCEP_DENTAL_ABSCESS'], paediatric: a < 18 });
}

function amoxicillin(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  if (hasPenicillinImmediateAllergy(ctx)) return { status: 'not_recommended_for_context', regimen: null, messages: ['Allergie immédiate aux pénicillines : ne pas proposer automatiquement.'], evidenceIds: ['SDCEP_AMOXICILLIN'] };
  const a = age(ctx);
  if (a == null) return review('Âge requis pour arbitrer l’amoxicilline.', ['SDCEP_AMOXICILLIN']);
  if (a < 0.5) return review('Règle SDCEP intégrée non applicable avant 6 mois.', ['SDCEP_AMOXICILLIN']);
  let dose = '';
  if (a < 1) dose = '125MG';
  else if (a < 5) dose = '250MG';
  else dose = '500MG';
  return applicable({ molecule: 'AMOXICILLINE', dosage: dose, posology: `${dose} 3 fois par jour`, duration: '3–5 jours; revue idéalement à 3 jours', form: 'GÉLULES OU SUSPENSION ORALE', evidenceIds: ['SDCEP_AMOXICILLIN', 'SDCEP_DENTAL_ABSCESS'], paediatric: a < 18 });
}

function metronidazole(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  if (ctx.anticoagulant && normalize(ctx.anticoagulant).includes('WARFAR')) {
    return { status: 'not_recommended_for_context', regimen: null, messages: ['Warfarine : le guide SDCEP indique de ne pas prescrire automatiquement le métronidazole.'], evidenceIds: ['SDCEP_METRONIDAZOLE'] };
  }
  const a = age(ctx);
  if (a == null) return review('Âge requis pour arbitrer le métronidazole.', ['SDCEP_METRONIDAZOLE']);
  if (a < 1) return review('Règle SDCEP d’abcès dentaire intégrée non applicable avant 1 an.', ['SDCEP_METRONIDAZOLE']);
  let dose = '';
  let frequency = '';
  if (a < 3) { dose = '50MG'; frequency = '3 fois par jour'; }
  else if (a < 7) { dose = '100MG'; frequency = '2 fois par jour'; }
  else if (a < 10) { dose = '100MG'; frequency = '3 fois par jour'; }
  else if (a < 18) { dose = '200MG'; frequency = '3 fois par jour'; }
  else { dose = '400MG'; frequency = '3 fois par jour'; }
  return applicable({ molecule: 'METRONIDAZOLE', dosage: dose, posology: `${dose} ${frequency}`, duration: '3–5 jours; revue idéalement à 3 jours', form: 'COMPRIMÉS OU SUSPENSION ORALE', evidenceIds: ['SDCEP_METRONIDAZOLE', 'SDCEP_DENTAL_ABSCESS'], paediatric: a < 18 });
}

function clindamycin(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  const a = age(ctx);
  if (a == null) return review('Âge requis pour arbitrer la clindamycine.', ['SDCEP_CLINDAMYCIN']);
  if (a < 12) return { status: 'not_recommended_for_context', regimen: null, messages: ['Le schéma dentaire SDCEP intégré ne couvre pas les moins de 12 ans.'], evidenceIds: ['SDCEP_CLINDAMYCIN'] };
  return applicable({ molecule: 'CLINDAMYCINE', dosage: '300MG', posology: '300 mg 4 fois par jour, avalé avec de l’eau', duration: '5 jours; seconde ligne seulement après réévaluation', form: 'GÉLULES', evidenceIds: ['SDCEP_CLINDAMYCIN'], paediatric: a < 18 });
}

function clarithromycin(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  const a = age(ctx);
  if (a == null) return review('Âge requis pour arbitrer la clarithromycine.', ['SDCEP_CLARITHROMYCIN']);
  if (a >= 18) return applicable({ molecule: 'CLARITHROMYCINE', dosage: '500MG', posology: '500 mg 2 fois par jour', duration: '5 jours; seconde ligne seulement après réévaluation', form: 'COMPRIMÉS', evidenceIds: ['SDCEP_CLARITHROMYCIN'], paediatric: false });
  if (a >= 12) return applicable({ molecule: 'CLARITHROMYCINE', dosage: '250-500MG', posology: '250–500 mg 2 fois par jour', duration: '5 jours; seconde ligne seulement après réévaluation', form: 'COMPRIMÉS', evidenceIds: ['SDCEP_CLARITHROMYCIN'], paediatric: true });
  if (a < 1) return review('Le schéma SDCEP intégré commence à 1 an.', ['SDCEP_CLARITHROMYCIN']);
  const w = weight(ctx);
  if (w == null) return { status: 'requires_weight', regimen: null, messages: ['Poids réel requis pour la clarithromycine entre 1 et 11 ans.'], evidenceIds: ['SDCEP_CLARITHROMYCIN'] };
  let dose: string | null = null;
  if (w >= 8 && w <= 11) dose = '62.5MG';
  else if (w >= 12 && w <= 19) dose = '125MG';
  else if (w >= 20 && w <= 29) dose = '187.5MG';
  else if (w >= 30 && w <= 40) dose = '250MG';
  if (!dose) return review('Poids hors bandes SDCEP intégrées (8–40 kg) : validation manuelle requise.', ['SDCEP_CLARITHROMYCIN']);
  return applicable({ molecule: 'CLARITHROMYCINE', dosage: dose, posology: `${dose} 2 fois par jour`, duration: '5 jours; seconde ligne seulement après réévaluation', form: 'COMPRIMÉS OU SUSPENSION ORALE', evidenceIds: ['SDCEP_CLARITHROMYCIN'], paediatric: true });
}

function miconazole(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  const a = age(ctx);
  if (ctx.anticoagulant && normalize(ctx.anticoagulant).includes('WARFAR')) return { status: 'not_recommended_for_context', regimen: null, messages: ['Warfarine : miconazole non proposé automatiquement.'], evidenceIds: ['SDCEP_MICONAZOLE'] };
  if (a == null) return review('Âge requis pour arbitrer le miconazole.', ['SDCEP_MICONAZOLE']);
  if (a < 2) return { status: 'not_recommended_for_context', regimen: null, messages: ['Le schéma SDCEP intégré est prévu à partir de 2 ans.'], evidenceIds: ['SDCEP_MICONAZOLE'] };
  return applicable({ molecule: 'MICONAZOLE', dosage: '20MG/G', posology: 'Appliquer une quantité de la taille d’un petit pois après les repas, 4 fois par jour', duration: '7 jours', form: 'GEL OROMUCOSAL', evidenceIds: ['SDCEP_MICONAZOLE'], paediatric: a < 18 });
}

function fluconazole(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  if (ctx.anticoagulant && normalize(ctx.anticoagulant).includes('WARFAR')) return { status: 'not_recommended_for_context', regimen: null, messages: ['Warfarine : fluconazole non proposé automatiquement.'], evidenceIds: ['SDCEP_FLUCONAZOLE'] };
  const a = age(ctx);
  if (a == null) return review('Âge requis pour arbitrer le fluconazole.', ['SDCEP_FLUCONAZOLE']);
  if (a < 0.5) return { status: 'not_recommended_for_context', regimen: null, messages: ['Le schéma SDCEP intégré commence à 6 mois.'], evidenceIds: ['SDCEP_FLUCONAZOLE'] };
  if (a < 12) {
    const w = weight(ctx);
    if (w == null) return { status: 'requires_weight', regimen: null, messages: ['Poids réel requis pour le fluconazole de 6 mois à 11 ans.'], evidenceIds: ['SDCEP_FLUCONAZOLE'] };
    return applicable({ molecule: 'FLUCONAZOLE', dosage: '50MG/5ML OU 50MG', posology: `Jour 1 : ${Math.min(400, Math.round(w * 6))} mg; puis ${Math.min(200, Math.round(w * 3))} mg une fois par jour`, duration: '7 jours', form: 'SUSPENSION ORALE OU GÉLULES', evidenceIds: ['SDCEP_FLUCONAZOLE'], paediatric: true });
  }
  return applicable({ molecule: 'FLUCONAZOLE', dosage: '50MG', posology: 'Jour 1 : 200 mg une fois; puis 100 mg une fois par jour', duration: '7 jours', form: 'GÉLULES', evidenceIds: ['SDCEP_FLUCONAZOLE'], paediatric: a < 18 });
}

function chlorhexidine(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  const a = age(ctx);
  return applicable({ molecule: 'CHLORHEXIDINE', dosage: '0.2%', posology: 'Rincer la bouche pendant 1 minute avec 10 ml, 2 fois par jour', form: 'BAIN DE BOUCHE', evidenceIds: ['SDCEP_CHLORHEXIDINE'], paediatric: a != null ? a < 18 : false });
}

function benzydamine(ctx: PatientPharmacologyContext): PharmacologyArbitration {
  const a = age(ctx);
  if (a == null) return review('Âge requis pour arbitrer le bain de bouche à la benzydamine.', ['SDCEP_BENZYDAMINE']);
  if (a <= 12) return { status: 'not_recommended_for_context', regimen: null, messages: ['Bain de bouche à la benzydamine non recommandé par la règle SDCEP intégrée chez les ≤12 ans.'], evidenceIds: ['SDCEP_BENZYDAMINE'] };
  return applicable({ molecule: 'BENZYDAMINE', dosage: '0.15%', posology: 'Rincer ou gargariser avec 15 ml toutes les 1 h 30 si nécessaire', form: 'BAIN DE BOUCHE', evidenceIds: ['SDCEP_BENZYDAMINE'], paediatric: a < 18 });
}

export function arbitrateMedication(
  moleculeName: string,
  ctx: PatientPharmacologyContext,
): PharmacologyArbitration {
  const name = normalize(moleculeName);
  if (!name) return noEvidence('médicament vide');

  if (name.includes('PHENOXYMETHYLPENICILLINE') || name === 'PENICILLINE V') return phenoxymethylpenicillin(ctx);
  if (name.includes('AMOXICILLINE') && !name.includes('CLAVUL')) return amoxicillin(ctx);
  if (name.includes('AMOXICILLINE') && name.includes('CLAVUL')) {
    return {
      status: 'requires_review',
      regimen: null,
      messages: ['Co-amoxiclav : molécule réelle, mais retirée des recommandations SDCEP 2026 de seconde ligne pour l’abcès dentaire. Aucun schéma dentaire automatique R1.'],
      evidenceIds: ['SDCEP_BACTERIAL_2026'],
    };
  }
  if (name.includes('METRONIDAZOLE')) return metronidazole(ctx);
  if (name.includes('CLINDAMYCINE')) return clindamycin(ctx);
  if (name.includes('CLARITHROMYCINE')) return clarithromycin(ctx);
  if (name.includes('PARACETAMOL')) return paracetamol(ctx);
  if (name.includes('IBUPROFENE')) return ibuprofen(ctx);
  if (name.includes('MICONAZOLE')) return miconazole(ctx);
  if (name.includes('FLUCONAZOLE')) return fluconazole(ctx);
  if (name.includes('CHLORHEXIDINE')) return chlorhexidine(ctx);
  if (name.includes('BENZYDAMINE')) return benzydamine(ctx);

  return noEvidence(moleculeName);
}

export function arbitrateDentalAbscessAntibioticIndication(
  context: DentalAbscessContext,
): PharmacologyArbitration {
  const evidenceIds = ['SDCEP_DENTAL_ABSCESS', 'SDCEP_BACTERIAL_2026', 'WHO_AWARE'];
  if (context.spreadingInfection || context.systemicInvolvement || context.highRiskComplications) {
    return { status: 'applicable', regimen: null, messages: ['Antibiotique potentiellement indiqué en complément des mesures locales; choix de molécule à arbitrer séparément. Revue idéalement à 3 jours.'], evidenceIds };
  }
  if (context.localMeasuresAttempted && context.localMeasuresEffective) {
    return { status: 'not_recommended_for_context', regimen: null, messages: ['Mesures locales efficaces sans diffusion/signes systémiques : ne pas proposer automatiquement d’antibiotique.'], evidenceIds };
  }
  if (context.firstLineCompletedWithoutResponse) {
    return { status: 'requires_review', regimen: null, messages: ['Échec de première ligne : revoir diagnostic, observance et contrôle de source; seconde ligne seulement après réévaluation/référence spécialisée.'], evidenceIds };
  }
  return { status: 'requires_review', regimen: null, messages: ['Contexte infectieux insuffisant : aucune antibiothérapie automatique.'], evidenceIds };
}
