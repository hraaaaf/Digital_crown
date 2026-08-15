import { describe, expect, it } from 'vitest';

import {
  shouldSkipInvalidCertificatePreview,
} from './useDocumentGenerator';
import {
  CERTIFICATE_TYPE_FREE,
  CERTIFICATE_TYPE_WORK_STOP,
} from './CertificatePolicy';

const baseParams = {
  patientId: '1',
  patientDetails: null,
  activeTab: 'certificat',
  drugs: [],
  certifType: CERTIFICATE_TYPE_FREE,
  certifDays: 1,
  certifStartDate: '2026-08-15',
  certifCustomMotif: '',
  items: [],
  paymentMode: 'Espèces',
  libreTitle: '',
  libreContent: '',
  libreCustomPatient: '',
  libreCustomDate: '',
  libreHideHeader: false,
  librePageSize: 'A5',
  libreAlignment: 'justify',
  docDate: '2026-08-15',
  selectedTeethFromOdontogram: [],
  smartSuggestion: null,
  installments: [],
} as any;

describe('P3 certificate automatic preview guard', () => {
  it('skips an incomplete free-certificate preview instead of calling the backend', () => {
    expect(shouldSkipInvalidCertificatePreview(baseParams)).toBe(true);
  });

  it('allows preview once the practitioner has authored the free content', () => {
    expect(
      shouldSkipInvalidCertificatePreview({
        ...baseParams,
        certifCustomMotif: 'Constat rédigé par le praticien.',
      }),
    ).toBe(false);
  });

  it('skips an invalid work-stop preview with a zero duration', () => {
    expect(
      shouldSkipInvalidCertificatePreview({
        ...baseParams,
        certifType: CERTIFICATE_TYPE_WORK_STOP,
        certifCustomMotif: '',
        certifDays: 0,
      }),
    ).toBe(true);
  });

  it('allows a valid work-stop preview', () => {
    expect(
      shouldSkipInvalidCertificatePreview({
        ...baseParams,
        certifType: CERTIFICATE_TYPE_WORK_STOP,
        certifCustomMotif: '',
        certifDays: 3,
        certifStartDate: '2026-08-15',
      }),
    ).toBe(false);
  });

  it('does not apply the certificate preview guard to other document tabs', () => {
    expect(
      shouldSkipInvalidCertificatePreview({
        ...baseParams,
        activeTab: 'libre',
      }),
    ).toBe(false);
  });
});
