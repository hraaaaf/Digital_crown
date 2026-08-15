import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

describe('CertificateForm P3-A', () => {
  it('n’applique jamais automatiquement type ou durée depuis une suggestion haute confiance', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        confidence: 'high',
        type: 'Arrêt de travail',
        days: 3,
        reason: 'Contexte chirurgical détecté',
      },
    } as never);

    const setCertifType = vi.fn();
    const setCertifDays = vi.fn();

    render(
      <CertificateForm
        patientId="42"
        certifType="Certificat de Présence"
        setCertifType={setCertifType}
        certifDays={1}
        setCertifDays={setCertifDays}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/prescriptions/certif-suggest/42'));

    expect(setCertifType).not.toHaveBeenCalled();
    expect(setCertifDays).not.toHaveBeenCalled();
    expect(screen.getByText(/Suggestion non appliquée/i)).toBeTruthy();
    expect(screen.getByText(/valider.*praticien/i)).toBeTruthy();
  });
});
