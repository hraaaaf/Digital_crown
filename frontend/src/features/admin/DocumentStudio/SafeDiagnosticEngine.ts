import { evaluateDiagnosis } from './DiagnosticEngine';

export interface SafeDiagnosisInput {
  motif: string;
  vitality: string;
  percussion: string;
  palpation: string;
  radiology: string;
  lesionDuration: string;
  medicalHistory: string;
}

const containsAny = (text: string, values: string[]) => values.some(value => text.includes(value));

const LEGACY_FALLBACK_TITLE = 'Consultation Standard';
const LEGACY_FALLBACK_DESCRIPTION = 'Examen clinique normal. Aucun traitement urgent requis.';

export function evaluateDiagnosisWithoutAutomaticSubstitution(params: SafeDiagnosisInput) {
  // Deliberately keep the legacy diagnostic rule evaluation separated from the
  // free-text medical history so that it cannot rewrite a therapeutic protocol.
  const legacyResult = evaluateDiagnosis({ ...params, medicalHistory: '' });

  // Fail closed: the legacy engine used to manufacture a reassuring diagnosis,
  // paracetamol and scaling when no rule matched. A no-match is uncertainty,
  // not evidence of a normal examination or an indication for treatment.
  const isLegacyFallback =
    legacyResult.title === LEGACY_FALLBACK_TITLE &&
    legacyResult.description === LEGACY_FALLBACK_DESCRIPTION;

  if (isLegacyFallback) {
    return {
      title: 'Données insuffisantes / règle non couverte',
      description: 'Aucune règle diagnostique validée ne correspond aux données saisies. Poursuivre l’évaluation clinique avant toute proposition thérapeutique.',
      protocol: [],
      treatmentPlan: [],
      warnings: ['Aucune proposition diagnostique ou thérapeutique générée : validation du praticien requise.'],
    };
  }

  const history = params.medicalHistory.toLowerCase();

  const hasPenicillinSignal = containsAny(history, [
    'pénicilline', 'penicilline', 'clamoxyl', 'amoxicilline',
  ]);
  const hasAinsSignal = containsAny(history, [
    'ains', 'ibuprofène', 'ibuprofene', 'anti-inflammatoire',
  ]);

  const protocolText = legacyResult.protocol.join(' ').toLowerCase();
  const warnings = [...legacyResult.warnings];

  if (hasPenicillinSignal && protocolText.includes('amoxicilline')) {
    warnings.push(
      '⚠️ Signal d’allergie à la pénicilline détecté dans les antécédents. Aucune substitution thérapeutique automatique : validation du praticien requise.',
    );
  }

  if (hasAinsSignal && protocolText.includes('ains')) {
    warnings.push(
      '⚠️ Signal d’allergie aux AINS détecté dans les antécédents. Aucune substitution thérapeutique automatique : validation du praticien requise.',
    );
  }

  return { ...legacyResult, warnings };
}
