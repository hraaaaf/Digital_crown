export type CalibrationUiState =
  | 'UNCALIBRATED'
  | 'CANDIDATE_UNVERIFIED'
  | 'AUTO_VERIFIED'
  | 'CLINICIAN_CONFIRMED'
  | 'MANUAL_TWO_POINT'
  | 'LEGACY_VERIFIED';

interface CalibrationStateInput {
  isCalibrated: boolean;
  anglesData?: Record<string, any> | null;
  calibrationData?: Record<string, any> | null;
}

export function deriveCalibrationUiState({
  isCalibrated,
  anglesData,
  calibrationData,
}: CalibrationStateInput): CalibrationUiState {
  const decisionState = String(anglesData?.calibration_decision?.state || '').toUpperCase();
  const status = String(anglesData?.calibration_status || '').toLowerCase();
  const persistedState = String(calibrationData?.state || '').toUpperCase();
  const method = String(calibrationData?.method || '').toUpperCase();

  if (persistedState === 'CLINICIAN_CONFIRMED' || decisionState === 'CLINICIAN_CONFIRMED' || status === 'clinician_confirmed') {
    return 'CLINICIAN_CONFIRMED';
  }
  if (persistedState === 'AUTO_VERIFIED' || decisionState === 'AUTO_VERIFIED' || status === 'auto_verified' || method === 'AUTO_FIDUCIAL_PROFILE') {
    return 'AUTO_VERIFIED';
  }
  if (method === 'MANUAL_TWO_POINT') {
    return 'MANUAL_TWO_POINT';
  }
  if (status === 'candidate_unverified' || decisionState === 'CANDIDATE_UNVERIFIED' || Boolean(anglesData?.calibration_candidate)) {
    return 'CANDIDATE_UNVERIFIED';
  }
  if (isCalibrated) {
    return 'LEGACY_VERIFIED';
  }
  return 'UNCALIBRATED';
}

export function calibrationUiLabel(state: CalibrationUiState): string {
  switch (state) {
    case 'CANDIDATE_UNVERIFIED':
      return 'Réglette à vérifier';
    case 'AUTO_VERIFIED':
      return 'Auto-vérifiée';
    case 'CLINICIAN_CONFIRMED':
      return 'Confirmée praticien';
    case 'MANUAL_TWO_POINT':
      return 'Calibration manuelle';
    case 'LEGACY_VERIFIED':
      return 'Calibration vérifiée';
    default:
      return 'Échelle non vérifiée';
  }
}

export function calibrationUiTone(state: CalibrationUiState): 'amber' | 'emerald' | 'indigo' {
  if (state === 'AUTO_VERIFIED' || state === 'CLINICIAN_CONFIRMED') return 'emerald';
  if (state === 'MANUAL_TWO_POINT' || state === 'LEGACY_VERIFIED') return 'indigo';
  return 'amber';
}
