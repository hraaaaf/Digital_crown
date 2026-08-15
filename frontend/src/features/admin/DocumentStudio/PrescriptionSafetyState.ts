export type PrescriptionSafetyStatus = 'unchecked' | 'checking' | 'verified' | 'error';

export interface PrescriptionSafetyWarning {
  type?: string;
  severity?: string;
  drug?: string;
  antecedent?: string;
  message: string;
}

export interface PrescriptionSafetyViewState {
  label: string;
  tone: 'neutral' | 'progress' | 'success' | 'warning' | 'error';
  verified: boolean;
}

export function prescriptionSafetyFingerprint(
  patientId: string,
  drugNames: string[],
): string {
  const normalized = drugNames
    .map(name => name.trim().toUpperCase())
    .filter(Boolean)
    .sort();

  return `${patientId.trim()}::${normalized.join('|')}`;
}

export function derivePrescriptionSafetyViewState(
  status: PrescriptionSafetyStatus,
  warnings: PrescriptionSafetyWarning[],
): PrescriptionSafetyViewState {
  if (status === 'checking') {
    return { label: 'Vérification…', tone: 'progress', verified: false };
  }
  if (status === 'error') {
    return { label: 'Vérification impossible', tone: 'error', verified: false };
  }
  if (status === 'verified') {
    if (warnings.length > 0) {
      return {
        label: `${warnings.length} alerte${warnings.length > 1 ? 's' : ''}`,
        tone: 'warning',
        verified: true,
      };
    }
    return { label: 'Sécurité vérifiée', tone: 'success', verified: true };
  }
  return { label: 'Sécurité non vérifiée', tone: 'neutral', verified: false };
}
