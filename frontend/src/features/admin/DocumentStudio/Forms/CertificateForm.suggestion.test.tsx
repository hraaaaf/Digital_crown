import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({ api: { get: vi.fn() } }));

const props = {
  patientId: '42',
  certifType: '',
  setCertifType: vi.fn(),
  certifDays: 5,
  setCertifDays: vi.fn(),
  certifCustomMotif: '',
  setCertifCustomMotif: vi.fn(),
};

describe('CertificateForm contextual suggestion', () => {
  it('masque le signal faible par défaut qui n’apporte aucune information utile', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        confidence: 'low',
        type: 'Certificat de Présence',
        days: 1,
        reason: "Pas d'acte chirurgical récent détecté.",
      },
    } as never);

    render(<CertificateForm {...props} />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/prescriptions/certif-suggest/42'));
    expect(screen.queryByText(/Pas d'acte chirurgical récent détecté/i)).toBeNull();
    expect(props.setCertifType).not.toHaveBeenCalled();
    expect(props.setCertifDays).not.toHaveBeenCalled();
  });

  it('conserve un signal contextuel fort comme information non appliquée', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: {
        confidence: 'high',
        type: 'Repos Post-Opératoire',
        days: 3,
        reason: 'Suite à un acte chirurgical',
      },
    } as never);

    render(<CertificateForm {...props} />);
    expect(await screen.findByText(/Suite à un acte chirurgical/i)).toBeTruthy();
    expect(screen.getByText(/Suggestion non appliquée/i)).toBeTruthy();
    expect(props.setCertifType).not.toHaveBeenCalled();
    expect(props.setCertifDays).not.toHaveBeenCalled();
  });
});
