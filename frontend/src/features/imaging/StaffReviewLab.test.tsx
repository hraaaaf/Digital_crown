import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { StaffReviewLab } from './StaffReviewLab';
import type { LabReviewClient, LabReviewInput, LabApproveInput } from './StaffReviewLab';

const CAPTURE = {
  device: 'fixture-connector-1',
  capture: 'capture-synthetic-0001',
  modality: 'Photo test',
  claimedSha256: 'a'.repeat(64),
  receivedAtLabel: 'Instant fictif',
};
const TARGETS = [
  { patientId: 101, label: 'FICTIF A', appointments: [{ id: 201, label: 'RDV A' }] },
  { patientId: 102, label: 'FICTIF B', appointments: [{ id: 202, label: 'RDV B' }] },
];

function harness(options: { override?: Partial<LabReviewClient> } = {}) {
  const review = vi.fn(async (input: LabReviewInput) => ({
    status: 'STAFF_REVIEW_REQUIRED',
    review_challenge: 'server-test-nonce',
    expires_at: Math.floor(Date.now() / 1000) + 300,
    patient_id: input.patient_id,
    appointment_id: input.appointment_id,
    server_confirmed: false as const,
  }));
  const approve = vi.fn(async (_input: LabApproveInput) => ({
    status: 'APPROVED', server_confirmed: false as const,
  }));
  const client = { review, approve, ...options.override } as LabReviewClient;
  const view = render(
    <StaffReviewLab capture={CAPTURE} targets={TARGETS}
      workstationId="fixture-workstation" client={client} />,
  );
  return { review, approve, view };
}
const patientSelect = () => screen.getByLabelText(/Patient · choix obligatoire/) as HTMLSelectElement;
const appointmentSelect = () => screen.getByLabelText(/Rendez-vous · facultatif/) as HTMLSelectElement;
const reviewButton = () => screen.getByRole('button', { name: 'Vérifier le lien patient' });
const confirmButton = () => screen.getByRole('button', { name: 'Confirmer ce patient' });

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

describe('LOT06-B desktop lab: real UI events / no false server receipt', () => {
  it('never auto-selects a patient or sends approval before a real click', async () => {
    const { review, approve } = harness();
    expect(patientSelect().value).toBe('');
    expect(reviewButton().hasAttribute('disabled')).toBe(true);
    expect(review).not.toHaveBeenCalled();
    expect(approve).not.toHaveBeenCalled();
    fireEvent.change(patientSelect(), { target: { value: '101' } });
    fireEvent.change(appointmentSelect(), { target: { value: '201' } });
    fireEvent.click(reviewButton());
    await screen.findByRole('button', { name: 'Confirmer ce patient' });
    expect(review).toHaveBeenCalledWith({
      workstation_id: 'fixture-workstation', device: CAPTURE.device,
      capture: CAPTURE.capture, patient_id: 101, appointment_id: 201,
    });
    expect(approve).not.toHaveBeenCalled();
    fireEvent.click(confirmButton());
    await screen.findByText(/Association approuvée dans le LAB/);
    expect(approve).toHaveBeenCalledTimes(1);
    expect(approve).toHaveBeenCalledWith(expect.objectContaining({
      patient_id: 101, appointment_id: 201, explicit_staff_action: true,
      review_challenge: 'server-test-nonce',
    }));
    expect(screen.queryByText(/reçu clinique non confirmés/i)).not.toBeNull();
    expect(screen.queryByRole('button', { name: 'Confirmer ce patient' })).toBeNull();
  });

  it('blocks patient-only capture without a reason and never pretends it is server-audited', async () => {
    const { review, approve } = harness();
    fireEvent.change(patientSelect(), { target: { value: '102' } });
    expect(reviewButton().hasAttribute('disabled')).toBe(true);
    expect(screen.getByText(/son audit serveur reste à implémenter/i)).toBeTruthy();
    fireEvent.change(screen.getByLabelText(/Justification · obligatoire/), {
      target: { value: 'Consultation non programmée' },
    });
    fireEvent.click(reviewButton());
    await screen.findByRole('button', { name: 'Confirmer ce patient' });
    expect(review).toHaveBeenCalledWith(expect.objectContaining({
      patient_id: 102, appointment_id: null,
    }));
    expect(approve).not.toHaveBeenCalled();
  });

  it('invalidates review challenge on cancel or patient change', async () => {
    const { approve } = harness();
    fireEvent.change(patientSelect(), { target: { value: '101' } });
    fireEvent.change(appointmentSelect(), { target: { value: '201' } });
    fireEvent.click(reviewButton());
    await screen.findByRole('button', { name: 'Confirmer ce patient' });
    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(screen.queryByRole('button', { name: 'Confirmer ce patient' })).toBeNull();
    fireEvent.change(patientSelect(), { target: { value: '102' } });
    expect(approve).not.toHaveBeenCalled();
    expect(reviewButton().hasAttribute('disabled')).toBe(true);
  });

  it('fails closed on mismatched server review response', async () => {
    const invalidReview = vi.fn(async (input: LabReviewInput) => ({
      status: 'STAFF_REVIEW_REQUIRED',
      review_challenge: 'unbound',
      expires_at: Math.floor(Date.now() / 1000) + 300,
      patient_id: input.patient_id + 1,
      appointment_id: input.appointment_id,
      server_confirmed: false as const,
    }));
    const { approve } = harness({ override: { review: invalidReview } });
    fireEvent.change(patientSelect(), { target: { value: '101' } });
    fireEvent.change(appointmentSelect(), { target: { value: '201' } });
    fireEvent.click(reviewButton());
    await screen.findByRole('alert');
    expect(approve).not.toHaveBeenCalled();
    expect(screen.queryByRole('button', { name: 'Confirmer ce patient' })).toBeNull();
  });

  it('requires new review after server approval rejection', async () => {
    const rejectedApprove = vi.fn(async (_input: LabApproveInput): Promise<never> => {
      throw new Error('STAFF_REVIEW_EXPIRED');
    });
    const { approve } = harness({ override: { approve: rejectedApprove } });
    fireEvent.change(patientSelect(), { target: { value: '101' } });
    fireEvent.change(appointmentSelect(), { target: { value: '201' } });
    fireEvent.click(reviewButton());
    await screen.findByRole('button', { name: 'Confirmer ce patient' });
    fireEvent.click(confirmButton());
    await screen.findByRole('alert');
    expect(approve).not.toHaveBeenCalled();
    expect(rejectedApprove).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('button', { name: 'Confirmer ce patient' })).toBeNull();
  });
});
