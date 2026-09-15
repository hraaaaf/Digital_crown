import type {
  PatientPharmacologyContext,
  PharmacologyArbitration,
} from './DentalPharmacologyArbiter';

const normalize = (value: string) => value
  .normalize('NFD')
  .replace(/[\u0300-\u036f]/g, '')
  .toUpperCase()
  .trim();

const realWeightKg = (ctx: PatientPharmacologyContext) =>
  typeof ctx.weightKg === 'number' && Number.isFinite(ctx.weightKg) && ctx.weightKg > 0
    ? ctx.weightKg
    : null;

const realAgeYears = (ctx: PatientPharmacologyContext) =>
  typeof ctx.ageYears === 'number' && Number.isFinite(ctx.ageYears) && ctx.ageYears >= 0
    ? ctx.ageYears
    : null;

function dailyUpperBoundMg(posology: string): number | null {
  const doseMatch = posology.match(/(\d+(?:[.,]\d+)?)\s*(?:[-–]\s*(\d+(?:[.,]\d+)?))?\s*mg\b/i);
  const frequencyMatch = posology.match(/(\d+)\s*fois\s+par\s+jour/i);
  if (!doseMatch || !frequencyMatch) return null;

  const low = Number(doseMatch[1].replace(',', '.'));
  const high = doseMatch[2] ? Number(doseMatch[2].replace(',', '.')) : low;
  const frequency = Number(frequencyMatch[1]);
  if (![low, high, frequency].every((value) => Number.isFinite(value) && value > 0)) return null;

  return Math.max(low, high) * frequency;
}

/**
 * Post-arbitration safety gate for weight-dependent hard ceilings.
 *
 * This is intentionally NOT a second dosing engine: it never creates a
 * replacement regimen. It only validates the already source-backed regimen
 * against a source-backed safety ceiling when a real patient weight exists.
 * If the ceiling is exceeded (or cannot be checked reliably), it fails closed
 * to practitioner review.
 */
export function applyMedicationWeightSafety(
  moleculeName: string,
  patient: PatientPharmacologyContext,
  arbitration: PharmacologyArbitration,
): PharmacologyArbitration {
  if (arbitration.status !== 'applicable' || !arbitration.regimen) return arbitration;

  const molecule = normalize(moleculeName);
  if (!molecule.includes('IBUPROFEN')) return arbitration;

  const ageYears = realAgeYears(patient);
  if (ageYears == null || ageYears >= 18) return arbitration;

  const weightKg = realWeightKg(patient);
  // SDCEP provides paediatric age-band regimens as well as the 30 mg/kg/day
  // maximum. Missing weight is never inferred; the existing age-band rule is
  // left unchanged until a real weight is available.
  if (weightKg == null) return arbitration;

  const proposedDailyUpperMg = dailyUpperBoundMg(arbitration.regimen.posology);
  if (proposedDailyUpperMg == null) {
    return {
      status: 'requires_review',
      regimen: null,
      messages: [
        'Sécurité pondérale ibuprofène : le schéma pédiatrique sourcé ne peut pas être vérifié automatiquement contre le plafond SDCEP de 30 mg/kg/j. Validation praticien requise.',
      ],
      evidenceIds: Array.from(new Set([...arbitration.evidenceIds, 'SDCEP_IBUPROFEN'])),
    };
  }

  const maxDailyMg = weightKg * 30;
  if (proposedDailyUpperMg > maxDailyMg) {
    const maxLabel = Number(maxDailyMg.toFixed(1));
    return {
      status: 'requires_review',
      regimen: null,
      messages: [
        `Sécurité pondérale ibuprofène : le schéma par tranche d’âge atteint jusqu’à ${proposedDailyUpperMg} mg/j, au-dessus du plafond SDCEP de 30 mg/kg/j pour ${weightKg} kg (${maxLabel} mg/j max). Aucun ajustement automatique : validation praticien requise.`,
      ],
      evidenceIds: Array.from(new Set([...arbitration.evidenceIds, 'SDCEP_IBUPROFEN'])),
    };
  }

  return arbitration;
}
