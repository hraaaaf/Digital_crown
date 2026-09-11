import { describe, expect, it } from 'vitest';
import { deriveCalibrationUiState } from './cephaloCalibration';

describe('deriveCalibrationUiState', () => {
  it('keeps an unverified candidate fail-closed', () => {
    expect(deriveCalibrationUiState({
      isCalibrated: false,
      anglesData: { calibration_status: 'candidate_unverified', calibration_candidate: { axis_x_px: 40 } },
    })).toBe('CANDIDATE_UNVERIFIED');
  });

  it('distinguishes auto verified from clinician confirmed', () => {
    expect(deriveCalibrationUiState({
      isCalibrated: true,
      anglesData: { calibration_decision: { state: 'AUTO_VERIFIED' } },
      calibrationData: { method: 'AUTO_FIDUCIAL_PROFILE', state: 'AUTO_VERIFIED' },
    })).toBe('AUTO_VERIFIED');

    expect(deriveCalibrationUiState({
      isCalibrated: true,
      anglesData: { calibration_decision: { state: 'CLINICIAN_CONFIRMED' } },
      calibrationData: { method: 'AUTO_FIDUCIAL_PROFILE', state: 'CLINICIAN_CONFIRMED' },
    })).toBe('CLINICIAN_CONFIRMED');
  });

  it('keeps manual calibration distinct from auto confirmation', () => {
    expect(deriveCalibrationUiState({
      isCalibrated: true,
      anglesData: { calibration_status: 'verified' },
      calibrationData: { method: 'MANUAL_TWO_POINT' },
    })).toBe('MANUAL_TWO_POINT');
  });

  it('does not invent provenance for legacy calibrated analyses', () => {
    expect(deriveCalibrationUiState({ isCalibrated: true, anglesData: { calibration_status: 'verified' } }))
      .toBe('LEGACY_VERIFIED');
  });
});
