import type { DonneesEtape3, DivisionClasseII } from './cephaloTypes';

/**
 * Scientific-core safety boundary.
 *
 * This module previously converted cephalometric/clinical measurements into
 * extraction choices, appliance prescriptions and mechanics. That coupling is
 * intentionally disabled: measurement != diagnosis != indication != treatment.
 *
 * The helpers are kept temporarily because Step3Clinical still imports them.
 * They now fail closed until dentition/division are represented by explicit,
 * practitioner-validated clinical observations.
 */
export function deriveDentureFromAge(_ageStr: string | number): 'TEMPORAIRE' | 'MIXTE' | 'PERMANENTE' | '' {
  return '';
}

export function deriveDivision(_classeSquelettique: string, _surplombStr: string | number): DivisionClasseII {
  return null;
}

export interface OrthoExpertReport {
  /** Descriptive measurements only. Never a diagnosis, indication or plan. */
  rapportMarkdown: string;
}

const optionalNumber = (value: number | ''): number | null => {
  if (value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};

const displayNumber = (value: number | null, unit: string): string =>
  value === null ? 'non documenté' : `${value}${unit}`;

/**
 * Temporary compatibility adapter for the current Step 3 UI.
 *
 * IMPORTANT: this function is deliberately descriptive. It must not infer a
 * diagnosis, select extractions, name an appliance/device, prescribe mechanics,
 * request imaging, or generate a therapeutic strategy. Any future clinical
 * interpretation must come through the validated scientific core with explicit
 * provenance/applicability and practitioner validation.
 */
export function evaluateCase(data: DonneesEtape3, ddmTotale: number | null): OrthoExpertReport {
  const impa = optionalNumber(data.dentaire.impa);
  const iFrancfort = optionalNumber(data.dentaire.i_francfort);
  const surplomb = optionalNumber(data.dentaire.surplomb);
  const recouvrement = optionalNumber(data.dentaire.recouvrement);

  const rapportMarkdown = `
### Synthèse descriptive ODF

Cette synthèse reprend uniquement les données documentées. Elle ne constitue ni un diagnostic, ni une indication, ni une stratégie thérapeutique. L'interprétation et la décision restent au praticien.

- Classe squelettique documentée : ${data.classe_squelettique || 'non documentée'}
- Pattern vertical documenté : ${data.pattern_vertical || 'non documenté'}
- Profil documenté : ${data.profil || 'non documenté'}
- Surplomb : ${displayNumber(surplomb, ' mm')}
- Recouvrement : ${displayNumber(recouvrement, ' mm')}
- IMPA : ${displayNumber(impa, '°')}
- I/Francfort : ${displayNumber(iFrancfort, '°')}
- DDM globale calculée en amont : ${ddmTotale === null || !Number.isFinite(ddmTotale) ? 'non documentée' : `${ddmTotale.toFixed(1)} mm`}

**Décision thérapeutique : à documenter et valider par le praticien.**
`;

  return { rapportMarkdown };
}
