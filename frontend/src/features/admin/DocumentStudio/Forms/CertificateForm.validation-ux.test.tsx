import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { CERTIFICATE_TYPE_FREE, CERTIFICATE_TYPE_WORK_STOP } from '../CertificatePolicy';

vi.mock('../../../../services/api', () => ({
  api: { get: vi.fn().mockRejectedValue(new Error('offline test')) },
}));

const baseProps = {
  patientId: '',
  certifType: CERTIFICATE_TYPE_FREE,
  setCertifType: vi.fn(),
  certifDays: 3,
  setCertifDays: vi.fn(),
  docDate: '2026-08-15',
  certifStartDate: '2026-08-15',
  setCertifStartDate: vi.fn(),
  setCertifCustomMotif: vi.fn(),
};

describe('CertificateForm validation UX', () => {
  it('rend explicite le contenu libre requis sans inventer de texte', () => {
    render(<CertificateForm {...baseProps} certifCustomMotif="" />);

    const textarea = screen.getByLabelText(/Contenu du certificat médical/i);
    expect(textarea.getAttribute('aria-required')).toBe('true');
    expect(textarea.getAttribute('aria-invalid')).toBe('true');
    expect(screen.getByText(/Contenu requis avant génération/i)).toBeTruthy();
    expect(screen.getByText(/ne complète jamais ce texte/i)).toBeTruthy();
  });

  it('retire l’état invalide dès que le praticien a rédigé son contenu', () => {
    render(<CertificateForm {...baseProps} certifCustomMotif="Constat clinique rédigé par le praticien." />);

    const textarea = screen.getByLabelText(/Contenu du certificat médical/i);
    expect(textarea.getAttribute('aria-invalid')).toBe('false');
    expect(screen.getByText(/Ce texte est repris tel quel/i)).toBeTruthy();
  });

  it('affiche clairement qu’aucune nature n’est sélectionnée sur un nouveau certificat', () => {
    render(<CertificateForm {...baseProps} certifType="" certifDays={0} certifCustomMotif="" />);

    expect(screen.getByText(/Aucun type sélectionné/i)).toBeTruthy();
    expect(screen.queryByLabelText(/Durée du repos en jours/i)).toBeNull();
  });

  it('affiche une durée réellement vide et invalide après choix explicite Arrêt de travail', () => {
    render(
      <CertificateForm
        {...baseProps}
        certifType={CERTIFICATE_TYPE_WORK_STOP}
        certifDays={0}
        certifCustomMotif=""
      />,
    );

    const duration = screen.getByLabelText(/Durée du repos en jours/i) as HTMLInputElement;
    expect(duration.value).toBe('');
    expect(duration.getAttribute('aria-required')).toBe('true');
    expect(duration.getAttribute('aria-invalid')).toBe('true');
    expect(screen.getByText(/Non définie/i)).toBeTruthy();
    expect(screen.getByText(/Aucune durée n’est préremplie/i)).toBeTruthy();
  });

  it('rend la durée valide uniquement après saisie du praticien', () => {
    render(
      <CertificateForm
        {...baseProps}
        certifType={CERTIFICATE_TYPE_WORK_STOP}
        certifDays={3}
        certifCustomMotif=""
      />,
    );

    const duration = screen.getByLabelText(/Durée du repos en jours/i) as HTMLInputElement;
    expect(duration.value).toBe('3');
    expect(duration.getAttribute('aria-invalid')).toBe('false');
  });

  it('n’affiche plus une promesse générique de certificat sécurisé', () => {
    render(<CertificateForm {...baseProps} certifCustomMotif="Texte validé." />);

    expect(screen.getByText(/Validation du praticien requise/i)).toBeTruthy();
    expect(screen.queryByText(/Certificat Médical SÉCURISÉ/i)).toBeNull();
  });
});
