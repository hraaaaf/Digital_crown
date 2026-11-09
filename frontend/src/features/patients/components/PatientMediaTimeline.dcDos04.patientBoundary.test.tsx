import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../../services/api';
import { PatientMediaTimeline } from './PatientMediaTimeline';

vi.mock('../../../services/api', () => ({ api: { get: vi.fn(), post: vi.fn() } }));

const media = (id: number, patientId: number, timepoint: 'T0' | 'T1') => ({
  id, patient_id: patientId, asset_type: 'RADIOGRAPH', source_kind: 'UPLOAD',
  mime_type: 'image/png', timepoint, created_at: '2026-11-09T00:00:00',
  thumbnail_asset_id: null,
});

beforeEach(() => {
  vi.clearAllMocks();
  vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:synthetic-test'), revokeObjectURL: vi.fn() });
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url === '/patients/7/assets') return {
      data: { items: [media(71, 7, 'T0'), media(72, 7, 'T1')], has_more: false },
    } as never;
    if (url === '/patients/8/assets') return {
      data: { items: [media(81, 8, 'T0'), media(82, 8, 'T1')], has_more: false },
    } as never;
    return { data: new Blob(['synthetic'], { type: 'image/png' }) } as never;
  });
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

describe('DC-DOS-04 patient-bound T0/T1 two-viewer regression (synthetic)', () => {
  it('unmounts the old patient compare and modal immediately on patient switch', async () => {
    const view = render(<PatientMediaTimeline patientId={7} readOnly />);
    await waitFor(() => expect(document.querySelectorAll('[data-clinical-asset-id="71"]').length).toBeGreaterThan(0));
    const rail = screen.getByTestId('media-asset-rail');
    const compare = within(rail).getAllByRole('button', { name: 'Ajouter à la comparaison' });
    fireEvent.click(compare[0]);
    fireEvent.click(compare[1]);
    expect(screen.getByTestId('media-compare-panel')).toBeTruthy();
    fireEvent.click(within(rail).getByRole('button', { name: 'Ouvrir Radiographie T0' }));
    await waitFor(() => expect(screen.getByRole('dialog', { name: 'Visionneuse média clinique' })).toBeTruthy());

    view.rerender(<PatientMediaTimeline patientId={8} readOnly />);
    expect(screen.queryByRole('dialog', { name: 'Visionneuse média clinique' })).toBeNull();
    expect(screen.queryByTestId('media-compare-panel')).toBeNull();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:synthetic-test');
    expect(document.querySelector('[data-clinical-asset-id="71"]')).toBeNull();
    expect(document.querySelector('[data-clinical-asset-id="72"]')).toBeNull();
    await waitFor(() => expect(document.querySelectorAll('[data-clinical-asset-id="81"]').length).toBeGreaterThan(0));
    expect(screen.getByTestId('patient-media-timeline').getAttribute('data-clinical-patient-id')).toBe('8');
    expect(screen.queryByRole('button', { name: 'Importer' })).toBeNull();
    expect(api.get).toHaveBeenCalledWith('/patients/8/assets', expect.anything());
  });
});




describe('DC-DOS-04 late network result quarantine (synthetic)', () => {
  it('never reattaches an old patient response to the next patient viewport', async () => {
    let resolveOld!: (value: any) => void;
    const oldResponse = new Promise((resolve) => { resolveOld = resolve; });
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url === '/patients/7/assets') return oldResponse as never;
      if (url === '/patients/8/assets') return Promise.resolve({
        data: { items: [media(81, 8, 'T0'), media(82, 8, 'T1')], has_more: false },
      }) as never;
      return Promise.resolve({ data: new Blob(['synthetic'], { type: 'image/png' }) }) as never;
    });

    const view = render(<PatientMediaTimeline patientId={7} readOnly />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/7/assets', expect.anything()));
    view.rerender(<PatientMediaTimeline patientId={8} readOnly />);
    await waitFor(() => expect(document.querySelector('[data-clinical-asset-id="81"]')).toBeTruthy());

    resolveOld({ data: { items: [media(71, 7, 'T0'), media(72, 7, 'T1')], has_more: false } });
    await waitFor(() => expect(screen.getByTestId('patient-media-timeline').getAttribute('data-clinical-patient-id')).toBe('8'));
    expect(document.querySelector('[data-clinical-asset-id="71"]')).toBeNull();
    expect(document.querySelector('[data-clinical-asset-id="72"]')).toBeNull();
  });
});


describe('DC-DOS-04 tenant/user scope collision guard (synthetic)', () => {
  it('drops old modal when a different cabinet uses the same numeric patient ID', async () => {
    const view = render(<PatientMediaTimeline patientId={7} scopeKey="user-100-cabinet-900" readOnly />);
    await waitFor(() => expect(document.querySelector('[data-clinical-asset-id="71"]')).toBeTruthy());
    fireEvent.click(within(screen.getByTestId('media-asset-rail')).getByRole('button', { name: 'Ouvrir Radiographie T0' }));
    await waitFor(() => expect(screen.getByRole('dialog', { name: /Visionneuse/ })).toBeTruthy());
    view.rerender(<PatientMediaTimeline patientId={7} scopeKey="user-200-cabinet-901" readOnly />);
    expect(screen.queryByRole('dialog', { name: /Visionneuse/ })).toBeNull();
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:synthetic-test');
  });
});
