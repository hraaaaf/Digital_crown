import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../../services/api';
import { ImagingAcquisitionProductReviewV15 } from './ImagingAcquisitionProductReviewV15';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn(), delete: vi.fn() },
}));
const get = vi.mocked(api.get);
const post = vi.mocked(api.post);
const del = vi.mocked(api.delete);

const capture = { id: 17, digest: 'a'.repeat(64), size: 80, mime: 'image/png', category: 'PHOTO' };
const inventory = {
  schema_version: 'dc06-product-unassigned-v1',
  state: 'UNASSIGNED_INVENTORY_READ_ONLY',
  clinical_receipt_authorized: false,
  patient_assigned: false,
  read_only: true,
  captures: [capture],
};
const review = {
  schema_version: 'dc06-product-review-v1',
  status: 'STAFF_REVIEW_REQUIRED',
  clinical_receipt_authorized: false,
  review_id: 'syntheticReviewId123456789012345',
  challenge: 'syntheticChallengeValue1234567890',
  capture_id: 17,
  capture_digest: capture.digest,
  capture_size: capture.size,
  patient_id: 42, nom: 'Test', prenom: 'Patiente',
  numero_dossier: 'LAB-42', date_naissance: '2000-03-04',
  expires_at: Math.floor(Date.now() / 1000) + 90,
  preview_url: '/imaging/acquisition/review/syntheticReviewId123456789012345/preview',
};
const accepted = {
  status: 'STAFF_REVIEW_VERIFIED_TRANSIENT_ONLY',
  clinical_receipt_authorized: false, patient_assigned: false,
  media_published: false,
};
const confirm = '/imaging/acquisition/review/' + review.review_id + '/confirm';

beforeEach(() => {
  vi.resetAllMocks();
  vi.stubGlobal('crypto', { subtle: {
    digest: vi.fn().mockResolvedValue(new Uint8Array(32).fill(0xaa).buffer),
  } });
  Object.defineProperty(URL, 'createObjectURL', {
    configurable: true, value: vi.fn().mockReturnValue('blob:product-verified-capture'),
  });
  Object.defineProperty(URL, 'revokeObjectURL', {
    configurable: true, value: vi.fn(),
  });
  get.mockImplementation(async (url) => {
    if (url === '/imaging/acquisition/unassigned')
      return { data: inventory } as never;
    if (url === review.preview_url)
      return { data: new Uint8Array(80).buffer, headers: { 'content-type': 'image/png' } } as never;
    throw new Error('unexpected endpoint');
  });
  post.mockImplementation(async (url) => {
    if (url === '/imaging/acquisition/review') return { data: review } as never;
    if (url === confirm) return { data: accepted } as never;
    throw new Error('unexpected POST');
  });
  del.mockResolvedValue({ status: 204 } as never);
});
afterEach(() => vi.unstubAllGlobals());

describe('LOT06 B06-2 actual product review (no clinical publication)', () => {
  it('never opens preview or proposes a patient when native bridge is not connected', async () => {
    get.mockResolvedValueOnce({ data: {
      ...inventory, state: 'NATIVE_IPC_NOT_CONNECTED', captures: [],
    }} as never);
    render(<ImagingAcquisitionProductReviewV15 patientId={42} />);
    await waitFor(() => expect(get).toHaveBeenCalledTimes(1));
    expect(screen.queryByRole('button')).toBeNull();
    expect(post).not.toHaveBeenCalled();
    expect(screen.queryByRole('img')).toBeNull();
  });

  it('requires an explicit selection and verified image, two typed IDs and checkbox', async () => {
    render(<ImagingAcquisitionProductReviewV15 patientId={42} />);
    const examine = await screen.findByRole('button', { name: /Examiner cette capture/ });
    expect(post).not.toHaveBeenCalled();
    fireEvent.click(examine);
    await waitFor(() => expect(post).toHaveBeenCalledWith('/imaging/acquisition/review', {
      selected_patient_id: 42, capture_id: 17, capture_digest: capture.digest,
    }));
    const button = await screen.findByRole('button', { name: /Confirmer la revue temporaire/ });
    expect(button).toBeDisabled();
    await waitFor(() => expect(get).toHaveBeenCalledWith(
      review.preview_url,
      { responseType: 'arraybuffer', headers: { 'X-DC-Review-Challenge': review.challenge } },
    ));
    const img = await screen.findByRole('img', { name: /Aperçu sécurisé/ });
    expect(button).toBeDisabled();
    fireEvent.load(img);
    expect(button).toBeDisabled();
    fireEvent.change(screen.getByLabelText(/Ressaisir le numéro de dossier/), {
      target: { value: 'LAB-42' },
    });
    fireEvent.change(screen.getByLabelText(/Ressaisir la date de naissance/), {
      target: { value: '2000-03-04' },
    });
    expect(button).toBeDisabled();
    fireEvent.click(screen.getByRole('checkbox'));
    expect(button).toBeEnabled();
    fireEvent.click(button);
    await waitFor(() => expect(post).toHaveBeenCalledWith(confirm, {
      challenge: review.challenge, selected_patient_id: 42,
      dossier: 'LAB-42', date_naissance: '2000-03-04',
      capture_digest: capture.digest, explicit_confirmation: true,
    }));
    expect(await screen.findByRole('status')).toHaveTextContent(/Aucun média publié/i);
    expect(screen.queryByRole('img')).toBeNull();
    expect(post).toHaveBeenCalledTimes(2);
  });

  it('denies malformed, wrong patient, expired or remote preview context', async () => {
    post.mockResolvedValueOnce({ data: { ...review, patient_id: 43 } } as never);
    const ui = render(<ImagingAcquisitionProductReviewV15 patientId={42} />);
    fireEvent.click(await screen.findByRole('button', { name: /Examiner/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/refusée/);
    expect(screen.queryByRole('img')).toBeNull();
    ui.unmount();

    post.mockResolvedValueOnce({ data: {
      ...review, preview_url: 'https://external.invalid/media.png',
    } } as never);
    render(<ImagingAcquisitionProductReviewV15 patientId={42} />);
    fireEvent.click(await screen.findByRole('button', { name: /Examiner/ }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/refusée/);
    expect(get).not.toHaveBeenCalledWith('https://external.invalid/media.png', expect.anything());
  });

  it('does not confirm a wrong SHA preview, and reset on patient route changes', async () => {
    vi.stubGlobal('crypto', { subtle: {
      digest: vi.fn().mockResolvedValue(new Uint8Array(32).fill(0x00).buffer),
    } });
    const ui = render(<ImagingAcquisitionProductReviewV15 patientId={42} />);
    fireEvent.click(await screen.findByRole('button', { name: /Examiner/ }));
    await waitFor(() => expect(get).toHaveBeenCalledWith(review.preview_url, expect.anything()));
    expect(screen.queryByRole('img')).toBeNull();
    expect(await screen.findByRole('button', { name: /Confirmer la revue temporaire/ })).toBeDisabled();
    expect(post).toHaveBeenCalledTimes(1);
    ui.rerender(<ImagingAcquisitionProductReviewV15 patientId={43} />);
    await waitFor(() => expect(screen.queryByRole('button', { name: /Confirmer la revue temporaire/ })).toBeNull());
  });

  it('cancel explicitly revokes this review and never creates a receipt', async () => {
    render(<ImagingAcquisitionProductReviewV15 patientId={42} />);
    fireEvent.click(await screen.findByRole('button', { name: /Examiner/ }));
    const cancel = await screen.findByRole('button', { name: 'Annuler' });
    fireEvent.click(cancel);
    await waitFor(() => expect(del).toHaveBeenCalledWith(
      '/imaging/acquisition/review/' + review.review_id,
      { headers: { 'X-DC-Review-Challenge': review.challenge } },
    ));
    expect(screen.queryByRole('img')).toBeNull();
    expect(post).toHaveBeenCalledTimes(1);
  });
});
