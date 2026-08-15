import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { CERTIFICATE_TYPE_FREE } from '../CertificatePolicy';

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

  it('n’affiche plus une promesse générique de certificat sécurisé', () => {
    render(<CertificateForm {...baseProps} certifCustomMotif="Texte validé." />);

    expect(screen.getByText(/Validation du praticien requise/i)).toBeTruthy();
    expect(screen.queryByText(/Certificat Médical SÉCURISÉ/i)).toBeNull();
  });
});
