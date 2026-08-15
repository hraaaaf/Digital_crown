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

export function evaluateDiagnosisWithoutAutomaticSubstitution(params: SafeDiagnosisInput) {
  // Deliberately keep the legacy diagnostic rule evaluation separated from the
  // free-text medical history so that it cannot rewrite a therapeutic protocol.
  const result = evaluateDiagnosis({ ...params, medicalHistory: '' });
  const history = params.medicalHistory.toLowerCase();

  const hasPenicillinSignal = containsAny(history, [
    'pénicilline', 'penicilline', 'clamoxyl', 'amoxicilline',
  ]);
  const hasAinsSignal = containsAny(history, [
    'ains', 'ibuprofène', 'ibuprofene', 'anti-inflammatoire',
  ]);

  const protocolText = result.protocol.join(' ').toLowerCase();
  const warnings = [...result.warnings];

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

  return { ...result, warnings };
}
