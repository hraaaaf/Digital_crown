import type {
  DentalAbscessContext,
  PatientPharmacologyContext,
  PharmacologyArbitration,
} from './DentalPharmacologyArbiter';

const normalize = (value: string) => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toUpperCase()
  .trim();

const realAgeYears = (ctx: PatientPharmacologyContext) =>
  typeof ctx.ageYears === 'number' && Number.isFinite(ctx.ageYears) && ctx.ageYears >= 0
    ? ctx.ageYears
    : null;

const realWeightKg = (ctx: PatientPharmacologyContext) =>
  typeof ctx.weightKg === 'number' && Number.isFinite(ctx.weightKg) && ctx.weightKg > 0
    ? ctx.weightKg
    : null;

const evidenceIds = (arbitration: PharmacologyArbitration) =>
  Array.from(new Set([...arbitration.evidenceIds, 'SDCEP_AMOXICILLIN', 'SDCEP_DENTAL_ABSCESS']));

/**
 * Safety gate for an explicitly documented severe dental infection.
 *
 * This gate is deliberately conservative:
 * - it never infers severity from free text;
 * - it never invents a paediatric weight;
 * - for 6 months to 11 years it exposes the source-backed ceiling
 *   (up to 30 mg/kg per dose, max 1 g, three times daily) but does not choose
 *   a replacement dose automatically;
 * - from 12 years onward, severe-infection guidance is not auto-adopted here
 *   because SDCEP age-based escalation and product SmPC weight bands can diverge
 *   in lower-weight adolescents. Practitioner review remains mandatory.
 */
export function applyAmoxicillinSevereDentalAbscessSafety(
  moleculeName: string,
  patient: PatientPharmacologyContext,
  dentalAbscessContext: DentalAbscessContext | null | undefined,
  arbitration: PharmacologyArbitration,
): PharmacologyArbitration {
  if (dentalAbscessContext?.severeInfection !== true) return arbitration;
  if (arbitration.status !== 'applicable' || !arbitration.regimen) return arbitration;

  const molecule = normalize(moleculeName);
  if (!molecule.includes('AMOXICILLINE') || molecule.includes('CLAVUL')) return arbitration;

  const ageYears = realAgeYears(patient);
  const ids = evidenceIds(arbitration);

  if (ageYears == null) {
    return {
      status: 'requires_review',
      regimen: null,
      messages: ['Infection dentaire sévère explicitement signalée : âge réel requis avant adaptation de l’amoxicilline.'],
      evidenceIds: ids,
    };
  }

  if (ageYears < 0.5) {
    return {
      status: 'requires_review',
      regimen: null,
      messages: ['Infection dentaire sévère : la règle SDCEP intégrée pour cette adaptation commence à 6 mois. Validation praticien requise.'],
      evidenceIds: ids,
    };
  }

  if (ageYears < 12) {
    const weightKg = realWeightKg(patient);
    if (weightKg == null) {
      return {
        status: 'requires_weight',
        regimen: null,
        messages: ['Infection dentaire sévère entre 6 mois et 11 ans : poids réel requis. Aucun poids n’est inféré.'],
        evidenceIds: ids,
      };
    }

    const maxSingleDoseMg = Math.min(1000, weightKg * 30);
    const maxLabel = Number(maxSingleDoseMg.toFixed(1));
    return {
      status: 'requires_review',
      regimen: null,
      messages: [
        `Infection dentaire sévère explicitement signalée : SDCEP autorise une augmentation jusqu’à 30 mg/kg par prise, maximum 1 g, 3 fois par jour chez les 6 mois–11 ans. Pour ${weightKg} kg, le plafond est ${maxLabel} mg par prise. Aucun choix de dose automatique : validation praticien requise.`,
      ],
      evidenceIds: ids,
    };
  }

  const weightKg = realWeightKg(patient);
  if (ageYears < 18 && weightKg == null) {
    return {
      status: 'requires_weight',
      regimen: null,
      messages: [
        'Infection dentaire sévère chez un adolescent : poids réel requis pour confronter la règle SDCEP d’escalade et le SmPC pondéral avant toute proposition.',
      ],
      evidenceIds: ids,
    };
  }

  return {
    status: 'requires_review',
    regimen: null,
    messages: [
      'Infection dentaire sévère explicitement signalée : une augmentation d’amoxicilline peut être indiquée, mais aucune dose sévère n’est auto-sélectionnée dans ce gate. Validation praticien requise après confrontation des recommandations dentaires et du SmPC de la présentation.',
    ],
    evidenceIds: ids,
  };
}
