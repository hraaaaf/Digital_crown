import type {
  PatientPharmacologyContext,
  PharmacologyArbitration,
  RegimenResult,
} from './DentalPharmacologyArbiter';

interface SupplementEvidence {
  id: string;
  title: string;
  url: string;
  reviewedAt: string;
}

export const PHARMACOLOGY_SUPPLEMENT_EVIDENCE: Record<string, SupplementEvidence> = {
  SDCEP_NYSTATIN: {
    id: 'SDCEP_NYSTATIN',
    title: 'Nystatin — candidosis',
    url: 'https://sdcepdentalprescribing.nhs.scot/guidance/fungal-infections/candidosis/nystatin/',
    reviewedAt: '2026-08-15',
  },
  SDCEP_ACICLOVIR_HSV: {
    id: 'SDCEP_ACICLOVIR_HSV',
    title: 'Aciclovir — severe herpes simplex / immunocompromised patients',
    url: 'https://sdcepdentalprescribing.nhs.scot/guidance/viral-infections/herpes-simplex/aciclovir/',
    reviewedAt: '2026-08-15',
  },
  SDCEP_HYDROCORTISONE_OROMUCOSAL: {
    id: 'SDCEP_HYDROCORTISONE_OROMUCOSAL',
    title: 'Hydrocortisone — oral ulceration / inflammation',
    url: 'https://sdcepdentalprescribing.nhs.scot/guidance/ulceration-inflammation/topical-corticosteroids/hydrocortisone/',
    reviewedAt: '2026-08-15',
  },
  SDCEP_FLUORIDE_2800: {
    id: 'SDCEP_FLUORIDE_2800',
    title: 'Sodium fluoride toothpaste 2800 ppm',
    url: 'https://sdcepdentalprescribing.nhs.scot/guidance/dental-caries/topical-fluoride-supplements/fluoride-toothpaste-2800-ppm/',
    reviewedAt: '2026-08-15',
  },
  SDCEP_FLUORIDE_5000: {
    id: 'SDCEP_FLUORIDE_5000',
    title: 'Sodium fluoride toothpaste 5000 ppm',
    url: 'https://sdcepdentalprescribing.nhs.scot/guidance/dry-mouth/topical-fluoride/fluoride-toothpaste-5000-ppm/',
    reviewedAt: '2026-08-15',
  },
  SDCEP_FLUORIDE_MOUTHWASH_005: {
    id: 'SDCEP_FLUORIDE_MOUTHWASH_005',
    title: 'Sodium fluoride mouthwash 0.05%',
    url: 'https://www.sdcepdentalprescribing.nhs.scot/guidance/dry-mouth/topical-fluoride/fluoride-mouthwash-005/',
    reviewedAt: '2026-08-15',
  },
};

const applicable = (regimen: RegimenResult): PharmacologyArbitration => ({
  status: 'applicable',
  regimen,
  messages: [],
  evidenceIds: regimen.evidenceIds,
});

const review = (message: string, evidenceIds: string[]): PharmacologyArbitration => ({
  status: 'requires_review',
  regimen: null,
  messages: [message],
  evidenceIds,
});

const noEvidence = (message: string, evidenceIds: string[]): PharmacologyArbitration => ({
  status: 'no_evidence',
  regimen: null,
  messages: [message],
  evidenceIds,
});

const age = (context: PatientPharmacologyContext): number | null =>
  typeof context.ageYears === 'number' && Number.isFinite(context.ageYears) && context.ageYears >= 0
    ? context.ageYears
    : null;

function nystatin(context: PatientPharmacologyContext): PharmacologyArbitration {
  const evidenceIds = ['SDCEP_NYSTATIN'];
  const a = age(context);
  if (a === null) return review('Âge patient requis avant proposition de nystatine.', evidenceIds);
  return applicable({
    molecule: 'NYSTATINE',
    dosage: '100000 UNITÉS/ML',
    posology: '1 ml après les repas 4 fois par jour pendant 7 jours',
    duration: '7 jours',
    form: 'SUSPENSION ORALE',
    evidenceIds,
    paediatric: a < 18,
  });
}

function aciclovir(context: PatientPharmacologyContext): PharmacologyArbitration {
  const evidenceIds = ['SDCEP_ACICLOVIR_HSV'];
  const a = age(context);
  if (a === null) return review('Âge patient requis avant proposition d’aciclovir.', evidenceIds);
  if (a < 0.5) return noEvidence('Aucun schéma SDCEP R1 encodé avant 6 mois.', evidenceIds);

  if (a < 2) {
    return applicable({
      molecule: 'ACICLOVIR',
      dosage: '100MG',
      posology: '100 mg 5 fois par jour pendant 5 jours',
      duration: '5 jours',
      form: 'COMPRIMÉS OU SUSPENSION ORALE',
      evidenceIds,
      paediatric: true,
    });
  }

  return applicable({
    molecule: 'ACICLOVIR',
    dosage: '200MG',
    posology: '200 mg 5 fois par jour pendant 5 jours',
    duration: '5 jours',
    form: 'COMPRIMÉS OU SUSPENSION ORALE',
    evidenceIds,
    paediatric: a < 18,
  });
}

function hydrocortisoneOromucosal(context: PatientPharmacologyContext): PharmacologyArbitration {
  const evidenceIds = ['SDCEP_HYDROCORTISONE_OROMUCOSAL'];
  const a = age(context);
  if (a === null) return review('Âge patient requis avant proposition d’hydrocortisone oromuqueuse.', evidenceIds);
  if (a < 12) return review('Hydrocortisone oromuqueuse avant 12 ans : uniquement sur avis médical selon SDCEP.', evidenceIds);
  return applicable({
    molecule: 'HYDROCORTISONE',
    dosage: '2.5MG',
    posology: '1 comprimé à laisser fondre au contact de la lésion 4 fois par jour',
    form: 'COMPRIMÉS OROMUQUEUX',
    evidenceIds,
    paediatric: a < 18,
  });
}

function sodiumFluoride2800(context: PatientPharmacologyContext): PharmacologyArbitration {
  const evidenceIds = ['SDCEP_FLUORIDE_2800'];
  const a = age(context);
  if (a === null) return review('Âge patient requis avant proposition de dentifrice fluoré 2800 ppm.', evidenceIds);
  if (a < 10) return review('Dentifrice fluoré 2800 ppm non indiqué avant 10 ans selon SDCEP (risque d’ingestion/intoxication).', evidenceIds);
  return applicable({
    molecule: 'FLUORURE DE SODIUM',
    dosage: '0.619% (2800 PPM)',
    posology: 'Brosser 1 minute après les repas avec 1 cm de dentifrice, recracher, 2 fois par jour',
    form: 'DENTIFRICE',
    evidenceIds,
    paediatric: a < 18,
  });
}

function sodiumFluoride5000(context: PatientPharmacologyContext): PharmacologyArbitration {
  const evidenceIds = ['SDCEP_FLUORIDE_5000'];
  const a = age(context);
  if (a === null) return review('Âge patient requis avant proposition de dentifrice fluoré 5000 ppm.', evidenceIds);
  if (a < 16) return review('Dentifrice fluoré 5000 ppm non indiqué avant 16 ans selon SDCEP (risque d’ingestion/intoxication).', evidenceIds);
  return applicable({
    molecule: 'FLUORURE DE SODIUM',
    dosage: '1.1% (5000 PPM)',
    posology: 'Brosser 3 minutes après les repas avec 2 cm de dentifrice, recracher, 3 fois par jour',
    form: 'DENTIFRICE',
    evidenceIds,
    paediatric: a < 18,
  });
}

function sodiumFluorideMouthwash005(context: PatientPharmacologyContext): PharmacologyArbitration {
  const evidenceIds = ['SDCEP_FLUORIDE_MOUTHWASH_005'];
  const a = age(context);
  if (a === null) return review('Âge patient requis avant proposition de bain de bouche fluoré 0,05%.', evidenceIds);
  if (a < 6) return review('Bain de bouche fluoré 0,05% non indiqué avant 6 ans selon SDCEP (risque d’ingestion/intoxication).', evidenceIds);
  return applicable({
    molecule: 'FLUORURE DE SODIUM',
    dosage: '0.05%',
    posology: 'Rincer avec 10 ml pendant 1 minute puis recracher, 1 fois par jour, de préférence à distance du brossage',
    form: 'BAIN DE BOUCHE',
    evidenceIds,
    paediatric: a < 18,
  });
}

/**
 * Supplements the core arbiter with additional source-backed dental medicines.
 * Returns null when the molecule/presentation is not owned by this supplement.
 *
 * Fluoride is presentation-specific: a generic "fluorure de sodium" name is
 * intentionally insufficient because 2800 ppm, 5000 ppm and 0.05% mouthwash
 * have different age thresholds and instructions.
 */
export function arbitrateMedicationSupplement(
  moleculeName: string,
  context: PatientPharmacologyContext,
): PharmacologyArbitration | null {
  const name = (moleculeName || '').trim().toUpperCase();
  if (!name) return null;

  if (name.includes('NYSTATIN')) return nystatin(context);
  if (name.includes('ACICLOVIR') || name.includes('ACYCLOVIR')) return aciclovir(context);
  if (name.includes('HYDROCORTISONE')) return hydrocortisoneOromucosal(context);

  if (name.includes('FLUORURE DE SODIUM') || name.includes('SODIUM FLUORIDE')) {
    if (name.includes('5000')) return sodiumFluoride5000(context);
    if (name.includes('2800')) return sodiumFluoride2800(context);
    if (name.includes('0.05') || name.includes('0,05')) return sodiumFluorideMouthwash005(context);
    return review('Présentation fluorée insuffisamment précisée : 2800 ppm, 5000 ppm ou bain de bouche 0,05% requis.', [
      'SDCEP_FLUORIDE_2800',
      'SDCEP_FLUORIDE_5000',
      'SDCEP_FLUORIDE_MOUTHWASH_005',
    ]);
  }

  return null;
}
