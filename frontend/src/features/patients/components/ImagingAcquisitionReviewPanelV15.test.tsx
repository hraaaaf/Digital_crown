import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import {
  ImagingAcquisitionReviewPanelV15,
  type LabAcquisitionReview,
} from './ImagingAcquisitionReviewPanelV15';

const base: LabAcquisitionReview = {
  status: 'STAFF_REVIEW_REQUIRED',
  lab_only: true,
  clinical_receipt_authorized: false,
  challenge: 'synthetic-review-token-not-a-real-patient',
  capture: 'synthetic-capture-2026',
  capture_digest: 'a'.repeat(64),
  capture_size: 1234,
  patient_id: 42,
  nom: 'Test',
  prenom: 'Patiente',
  numero_dossier: 'SYN-42',
  date_naissance: '2000-03-04',
  expires_at: Math.floor(Date.now() / 1000) + 120,
  preview_url: '/isolated/lab/preview.png',
};

const fill = () => {
  fireEvent.change(screen.getByLabelText(/Ressaisir le numéro de dossier/), { target: { value: 'SYN-42' } });
  fireEvent.change(screen.getByLabelText(/Ressaisir la date de naissance/), { target: { value: '2000-03-04' } });
  fireEvent.click(screen.getByRole('checkbox'));
};

describe('ImagingAcquisitionReviewPanelV15 isolated LAB patient-safety UI', () => {
  it('stays fail-closed without BOTH identity checks and explicit staff action', async () => {
    const onConfirm = vi.fn().mockResolvedValue(undefined);
    render(<ImagingAcquisitionReviewPanelV15 review={base} previewUrl="/fixture.png"
      onConfirm={onConfirm} onCancel={vi.fn()} />);

    const submit = screen.getByRole('button', { name: /Confirmer la revue/ });
    expect(submit).toBeDisabled();
    expect(screen.getByText('SYN-42')).toBeInTheDocument();
    expect(screen.getByText('2000-03-04')).toBeInTheDocument();
    expect(screen.getByAltText(/Aperçu de la capture/)).toHaveAttribute('src', '/fixture.png');

    fireEvent.change(screen.getByLabelText(/Ressaisir le numéro de dossier/), { target: { value: 'WRONG' } });
    fireEvent.change(screen.getByLabelText(/Ressaisir la date de naissance/), { target: { value: '2000-03-04' } });
    fireEvent.click(screen.getByRole('checkbox'));
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Ressaisir le numéro de dossier/), { target: { value: 'SYN-42' } });
    expect(submit).toBeEnabled();
    fireEvent.click(submit);

    await waitFor(() => expect(onConfirm).toHaveBeenCalledTimes(1));
    expect(onConfirm).toHaveBeenCalledWith({
      challenge: base.challenge,
      selected_patient_id: 42,
      dossier: 'SYN-42',
      date_naissance: '2000-03-04',
      capture_digest: 'a'.repeat(64),
      explicit_confirmation: true,
    });
    expect(screen.getByRole('status')).toHaveTextContent(/laboratoire/i);
    expect(screen.queryByRole('button', { name: /Confirmer la revue/ })).toBeNull();
  });

  it('resets staff inputs when a DIFFERENT patient or media arrives', () => {
    const fn = vi.fn().mockResolvedValue(undefined);
    const view = render(<ImagingAcquisitionReviewPanelV15 review={base} previewUrl="/fixture.png"
      onConfirm={fn} onCancel={vi.fn()} />);
    fill();
    expect(screen.getByRole('button', { name: /Confirmer la revue/ })).toBeEnabled();

    view.rerender(<ImagingAcquisitionReviewPanelV15 review={{
      ...base, patient_id: 43, numero_dossier: 'SYN-43',
      capture_digest: 'b'.repeat(64), challenge: 'new-synthetic-challenge-123',
    }} previewUrl="/fixture2.png" onConfirm={fn} onCancel={vi.fn()} />);
    expect(screen.getByRole('button', { name: /Confirmer la revue/ })).toBeDisabled();
    expect((screen.getByLabelText(/Ressaisir le numéro de dossier/) as HTMLInputElement).value).toBe('');
    expect(screen.getByRole('checkbox')).not.toBeChecked();
  });

  it('disallows expired, untrusted or product-authorized LAB contexts', () => {
    const fn = vi.fn();
    const view = render(<ImagingAcquisitionReviewPanelV15 review={{
      ...base, expires_at: Math.floor(Date.now() / 1000) - 1,
    }} previewUrl="/fixture.png" onConfirm={fn} onCancel={vi.fn()} />);
    fill();
    expect(screen.getByRole('button', { name: /Confirmer la revue/ })).toBeDisabled();

    view.rerender(<ImagingAcquisitionReviewPanelV15 review={{
      ...base, lab_only: false,
    } as unknown as LabAcquisitionReview} previewUrl="/fixture.png" onConfirm={fn} onCancel={vi.fn()} />);
    expect(screen.getByRole('alert')).toHaveTextContent(/Capture indisponible/);
    expect(fn).not.toHaveBeenCalled();
  });

  it('does not signal success when the server rejects confirmation', async () => {
    const fn = vi.fn().mockRejectedValue(new Error('Patient name private server details'));
    render(<ImagingAcquisitionReviewPanelV15 review={base} previewUrl="/fixture.png"
      onConfirm={fn} onCancel={vi.fn()} />);
    fill();
    fireEvent.click(screen.getByRole('button', { name: /Confirmer la revue/ }));
    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent(/refusée/));
    expect(screen.queryByText(/Patient name private server details/)).toBeNull();
    expect(screen.queryByRole('status')).toBeNull();
  });
});
