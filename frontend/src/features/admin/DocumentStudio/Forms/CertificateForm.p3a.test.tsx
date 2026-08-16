import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

describe('CertificateForm P3', () => {
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
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/prescriptions/certif-suggest/42'));

    expect(setCertifType).not.toHaveBeenCalled();
    expect(setCertifDays).not.toHaveBeenCalled();
    expect(screen.getByRole('status')).toHaveTextContent(/Aucun choix n’est appliqué automatiquement/i);
    expect(screen.getByText(/Validation du praticien requise/i)).toBeTruthy();
  });

  it('affiche Certificat médical comme dernier choix et ouvre une rédaction libre', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: null } as never);
    const setCertifType = vi.fn();

    const { rerender } = render(
      <CertificateForm
        patientId="42"
        certifType="Arrêt de travail"
        setCertifType={setCertifType}
        certifDays={2}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    const choices = screen.getAllByRole('button');
    expect(choices[choices.length - 1].textContent).toMatch(/Certificat médical/i);
    fireEvent.click(screen.getByRole('button', { name: /Certificat médical/i }));
    expect(setCertifType).toHaveBeenCalledWith('Certificat médical');

    rerender(
      <CertificateForm
        patientId="42"
        certifType="Certificat médical"
        setCertifType={setCertifType}
        certifDays={2}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif="Texte rédigé par le praticien"
        setCertifCustomMotif={vi.fn()}
      />,
    );

    expect((screen.getByRole('textbox', { name: /Contenu du certificat médical/i }) as HTMLTextAreaElement).value).toBe('Texte rédigé par le praticien');
    expect(screen.queryByLabelText(/Durée du repos/i)).toBeNull();
  });

  it('affiche un début du repos distinct uniquement pour un arrêt de travail', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({ data: null } as never);
    render(
      <CertificateForm
        patientId=""
        certifType="Arrêt de travail"
        setCertifType={vi.fn()}
        certifDays={3}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate="2026-08-17"
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );

    expect((screen.getByLabelText(/Début du repos/i) as HTMLInputElement).value).toBe('2026-08-17');
  });

});
