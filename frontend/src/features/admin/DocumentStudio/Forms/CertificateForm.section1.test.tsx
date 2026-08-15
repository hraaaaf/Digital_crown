import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { CertificateForm } from './CertificateForm';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({ api: { get: vi.fn().mockRejectedValue(new Error('offline test')) } }));

const baseProps = {
  patientId: '',
  certifDays: 5,
  setCertifDays: vi.fn(),
  certifCustomMotif: '',
  setCertifCustomMotif: vi.fn(),
};

describe('CertificateForm section 1', () => {
  it('présente le type de certificat comme choix explicite et masque la durée tant qu’il manque', () => {
    render(<CertificateForm {...baseProps} certifType="" setCertifType={vi.fn()} />);
    expect(screen.getByText('Type de certificat')).toBeTruthy();
    expect(screen.queryByText('Durée du repos')).toBeNull();
  });

  it('expose le choix comme bouton explicite non-submit', () => {
    const setCertifType = vi.fn();
    render(<CertificateForm {...baseProps} certifType="" setCertifType={setCertifType} />);
    const button = screen.getByRole('button', { name: /Arrêt de travail/i });
    expect(button.getAttribute('type')).toBe('button');
    fireEvent.click(button);
    expect(setCertifType).toHaveBeenCalledWith('Arrêt de travail');
  });

  it('affiche les erreurs de type et de motif libre sur leurs contrôles', () => {
    const { rerender } = render(
      <CertificateForm
        {...baseProps}
        certifType=""
        setCertifType={vi.fn()}
        validationErrors={[{ field: 'certifType', message: 'Le type de certificat est requis.' }]}
      />,
    );
    expect(screen.getByRole('alert').textContent).toMatch(/type de certificat est requis/i);

    rerender(
      <CertificateForm
        {...baseProps}
        certifType="Autre"
        setCertifType={vi.fn()}
        validationErrors={[{ field: 'certifCustomMotif', message: 'Le motif personnalisé est requis.' }]}
      />,
    );
    const input = screen.getByPlaceholderText(/motif personnalisé/i);
    expect(input.getAttribute('aria-invalid')).toBe('true');
    expect(screen.getByText(/motif personnalisé est requis/i)).toBeTruthy();
  });

  it('ne demande aucune durée pour un certificat de présence', () => {
    render(<CertificateForm {...baseProps} certifType="Certificat de Présence" setCertifType={vi.fn()} />);
    expect(screen.queryByText('Durée du repos')).toBeNull();
  });
});
