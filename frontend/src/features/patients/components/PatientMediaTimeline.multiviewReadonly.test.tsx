import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../../services/api';
import { PatientMediaTimeline } from './PatientMediaTimeline';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.get).mockResolvedValue({ data: { items: [], has_more: false } } as never);
});
afterEach(() => cleanup());

describe('07.1.A clinical media R-mode contract (synthetic)', () => {
  it('removes every upload input and write affordance from MultiView R mode', async () => {
    render(<PatientMediaTimeline patientId={17} readOnly />);
    await waitFor(() => expect(vi.mocked(api.get)).toHaveBeenCalled());
    expect(screen.queryByRole('button', { name: 'Importer' })).toBeNull();
    expect(document.querySelector('[aria-label="Import média clinique"]')).toBeNull();
    expect(document.querySelector('input[type="file"]')).toBeNull();
    expect(vi.mocked(api.post)).not.toHaveBeenCalled();
  });

  it('locks a split Photos view to real PHOTO assets in request and client filtering',async()=>{
    const assets=[
      {id:11,patient_id:17,asset_type:'PHOTO',source_kind:'UPLOAD',created_at:'2026-10-26T09:00:00',timepoint:'T0'},
      {id:12,patient_id:17,asset_type:'RADIOGRAPH',source_kind:'UPLOAD',created_at:'2026-10-26T09:00:00',timepoint:'T1'},
    ];
    vi.mocked(api.get).mockResolvedValue({data:{items:assets,has_more:false}} as never);
    render(<PatientMediaTimeline patientId={17} readOnly fixedAssetType="PHOTO"/>);
    await waitFor(()=>expect(vi.mocked(api.get)).toHaveBeenCalledWith('/patients/17/assets',{
      params:expect.objectContaining({asset_type:'PHOTO'}),
    }));
    const filter=screen.getByRole('combobox',{name:'Filtrer par type'}) as HTMLSelectElement;
    expect(filter.value).toBe('PHOTO');
    expect(filter.disabled).toBe(true);
    expect(screen.queryByText('Radiographie')).toBeNull();
    expect(document.querySelector('input[type="file"]')).toBeNull();
    expect(vi.mocked(api.post)).not.toHaveBeenCalled();
  });

  it('preserves the original upload control outside the read-only MultiView', async () => {
    render(<PatientMediaTimeline patientId={17} />);
    await waitFor(() => expect(vi.mocked(api.get)).toHaveBeenCalled());
    expect(screen.getByRole('button', { name: 'Importer' })).toBeTruthy();
    expect(document.querySelector('[aria-label="Import média clinique"]')).toBeTruthy();
    expect(vi.mocked(api.post)).not.toHaveBeenCalled();
  });
});
