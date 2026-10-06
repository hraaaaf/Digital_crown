import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { api } from '../../../../services/api';

let mockUser: any = { role: 'DENTISTE', employer_id: null, permissions: { prescriptions: true } };

vi.mock('../../../../stores/useAuthStore', () => ({
  useAuthStore: (selector: any) => selector({ user: mockUser }),
}));

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
  },
}));

describe('CertificateForm P3', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUser = { role: 'DENTISTE', employer_id: null, permissions: { prescriptions: true } };
  });
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
    expect(screen.getByRole('status').textContent).toMatch(/Aucun choix n’est appliqué automatiquement/i);
    expect(screen.getByText(/Validation du praticien requise/i)).toBeTruthy();
  });

  it('ne charge pas la suggestion clinique sans permission prescriptions', async () => {
    mockUser = { role: 'SECRETAIRE', employer_id: 7, permissions: { prescriptions: false } };
    render(
      <CertificateForm
        patientId="42"
        certifType="Certificat de Présence"
        setCertifType={vi.fn()}
        certifDays={1}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif=""
        setCertifCustomMotif={vi.fn()}
      />,
    );
    await waitFor(() => expect(api.get).not.toHaveBeenCalled());
  });

  it('ignore une réponse tardive de suggestion après changement de patient', async () => {
    let resolveFirst: (value: any) => void = () => undefined;
    const first = new Promise(resolve => { resolveFirst = resolve; });
    vi.mocked(api.get)
      .mockImplementationOnce(() => first as never)
      .mockResolvedValueOnce({ data: { confidence: 'low', type: 'Certificat de Présence', days: 0, reason: 'Patient 2' } } as never);

    const props = {
      certifType: 'Certificat de Présence',
      setCertifType: vi.fn(),
      certifDays: 1,
      setCertifDays: vi.fn(),
      docDate: '2026-08-15',
      certifStartDate: '',
      setCertifStartDate: vi.fn(),
      certifCustomMotif: '',
      setCertifCustomMotif: vi.fn(),
    };

    const { rerender } = render(<CertificateForm patientId="1" {...props} />);
    rerender(<CertificateForm patientId="2" {...props} />);

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/prescriptions/certif-suggest/2'));
    resolveFirst({ data: { confidence: 'high', type: 'Arrêt de travail', days: 30, reason: 'Patient 1' } });
    await new Promise(resolve => setTimeout(resolve, 0));

    expect(screen.queryByText(/Patient 1/i)).toBeNull();
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

  it('nettoie un ancien brouillon HTML dès l’ouverture du certificat médical libre', async () => {
    const setCertifCustomMotif = vi.fn();
    render(
      <CertificateForm
        patientId=""
        certifType="Certificat médical"
        setCertifType={vi.fn()}
        certifDays={0}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif="<p>Texte <strong>important</strong><br>Deuxième ligne</p>"
        setCertifCustomMotif={setCertifCustomMotif}
      />,
    );

    await waitFor(() => {
      expect(setCertifCustomMotif).toHaveBeenCalledWith('Texte important\nDeuxième ligne');
    });
  });

  it('retire un ancien code de mise en page au lieu de l’exposer dans le certificat médical', async () => {
    const setCertifCustomMotif = vi.fn();
    render(
      <CertificateForm
        patientId=""
        certifType="Certificat médical"
        setCertifType={vi.fn()}
        certifDays={0}
        setCertifDays={vi.fn()}
        docDate="2026-08-15"
        certifStartDate=""
        setCertifStartDate={vi.fn()}
        certifCustomMotif="<div><b>Patient : {{ patient.nom }}</b></div>"
        setCertifCustomMotif={setCertifCustomMotif}
      />,
    );

    await waitFor(() => {
      expect(setCertifCustomMotif).toHaveBeenCalledWith('Patient :');
    });
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
