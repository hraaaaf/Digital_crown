import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { OrthoMediaRecordPanel, ORTHO_PHOTO_SLOTS } from './OrthoMediaRecordPanel';

const { get, post } = vi.hoisted(() => ({ get: vi.fn(), post: vi.fn() }));

vi.mock('../../../services/api', () => ({
  api: { get, post },
}));

vi.mock('react-hot-toast', () => ({
  default: { success: vi.fn(), error: vi.fn() },
}));

const P = {
  bgPanel: '#fff', bgCard: '#fff', bgInput: '#fff', border: '#ddd', text: '#111',
  textMuted: '#666', textDim: '#999', accent: '#0b57d0', accentSuccess: '#16804a',
};

const emptyRecord = {
  schema_version: 'ORTHO_MEDIA_RECORD_V1',
  patient_id: 7,
  timepoint: 'T0',
  photo_slots: ORTHO_PHOTO_SLOTS.map(([slot_id]) => ({ slot_id, state: 'EMPTY', asset: null })),
  photo_complete: false,
  model_hooks: [
    { hook_id: 'MAXILLARY_ARCH', accepted_formats: ['STL', 'PLY', 'OBJ'], state: 'VALIDATOR_NOT_IMPLEMENTED', measurement_authority: 'NONE' },
    { hook_id: 'MANDIBULAR_ARCH', accepted_formats: ['STL', 'PLY', 'OBJ'], state: 'VALIDATOR_NOT_IMPLEMENTED', measurement_authority: 'NONE' },
    { hook_id: 'OCCLUSION_RELATION', accepted_formats: ['STL', 'PLY', 'OBJ'], state: 'VALIDATOR_NOT_IMPLEMENTED', measurement_authority: 'NONE' },
  ],
};

describe('OrthoMediaRecordPanel LOT07-F', () => {
  beforeEach(() => {
    get.mockReset();
    post.mockReset();
    get.mockResolvedValue({ data: emptyRecord });
    post.mockResolvedValue({ data: {} });
  });

  it('renders the canonical 3 extraoral + 5 intraoral slots and fail-closed model hooks', async () => {
    render(<OrthoMediaRecordPanel patientId={7} P={P} />);
    await screen.findByText(/8 vues standardisées/i);
    expect(document.querySelectorAll('[data-ortho-photo-slot]')).toHaveLength(8);
    expect(document.querySelectorAll('[data-ortho-model-hook]')).toHaveLength(3);
    expect(screen.getAllByText(/Import désactivé jusqu'au validateur 3D/i)).toHaveLength(3);
    expect(screen.getByLabelText('Importer Profil')).toHaveAttribute('accept', 'image/jpeg,image/png,image/webp');
    expect(screen.getByLabelText('Importer Occlusal mandibulaire')).toBeInTheDocument();
    expect(document.querySelector('[data-ortho-model-hook] input[type=file]')).toBeNull();
    expect(get).toHaveBeenCalledWith('/patients/7/ortho-media-record', { params: { timepoint: 'T0' } });
  });

  it('uploads a photo only through the canonical patient record endpoint with explicit timepoint/acquisition', async () => {
    render(<OrthoMediaRecordPanel patientId={7} P={P} />);
    await screen.findByText(/8 vues standardisées/i);
    const input = document.querySelector('[data-ortho-photo-slot="EXTRA_PROFILE"] input[type=file]') as HTMLInputElement;
    const file = new File(['photo'], 'profile.png', { type: 'image/png' });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => expect(post).toHaveBeenCalledTimes(1));
    const [url, body] = post.mock.calls[0];
    expect(url).toBe('/patients/7/ortho-media-record/photos/EXTRA_PROFILE');
    expect(body).toBeInstanceOf(FormData);
    expect((body as FormData).get('timepoint')).toBe('T0');
    expect(typeof (body as FormData).get('acquired_at')).toBe('string');
    expect((body as FormData).get('file')).toBe(file);
  });

  it('keeps the newest timepoint response authoritative when requests resolve out of order', async () => {
    let resolveT0: (value: any) => void = () => undefined;
    let resolveT1: (value: any) => void = () => undefined;
    const t0 = new Promise(resolve => { resolveT0 = resolve; });
    const t1 = new Promise(resolve => { resolveT1 = resolve; });
    get.mockImplementation((_url: string, config: any) => config.params.timepoint === 'T0' ? t0 : t1);
    render(<OrthoMediaRecordPanel patientId={7} P={P} />);
    fireEvent.change(screen.getByLabelText('Temps orthodontique'), { target: { value: 'T1' } });
    resolveT1({ data: { ...emptyRecord, timepoint: 'T1' } });
    await screen.findByText(/0\/8/);
    resolveT0({ data: { ...emptyRecord, photo_slots: emptyRecord.photo_slots.map((slot: any) => ({ ...slot, state: 'FILLED' })), photo_complete: true } });
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(screen.getByText(/0\/8/)).toBeInTheDocument();
  });

  it('fails closed when acquisition time is empty instead of posting invalid provenance', async () => {
    render(<OrthoMediaRecordPanel patientId={7} P={P} />);
    await screen.findByText(/8 vues/i);
    fireEvent.change(screen.getByLabelText('Date de prise de vue'), { target: { value: '' } });
    const input = document.querySelector('[data-ortho-photo-slot="EXTRA_PROFILE"] input[type=file]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(['photo'], 'profile.png', { type: 'image/png' })] } });
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(post).not.toHaveBeenCalled();
  });

  it('does not use browser localStorage as a clinical record', async () => {
    const getItem = vi.spyOn(Storage.prototype, 'getItem');
    const setItem = vi.spyOn(Storage.prototype, 'setItem');
    render(<OrthoMediaRecordPanel patientId={7} P={P} />);
    await screen.findByText(/8 vues standardisées/i);
    expect(getItem).not.toHaveBeenCalled();
    expect(setItem).not.toHaveBeenCalled();
  });
});
