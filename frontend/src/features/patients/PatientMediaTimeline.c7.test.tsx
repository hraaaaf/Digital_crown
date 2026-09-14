import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { api } from '../../services/api';
import { PatientMediaTimeline } from './components/PatientMediaTimeline';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const asset = (id: number, assetType = 'PHOTO', timepoint = 'T0') => ({
  id,
  patient_id: 7,
  asset_type: assetType,
  source_kind: 'UPLOAD',
  mime_type: 'image/png',
  timepoint,
  created_at: `2026-09-${String(Math.min(id, 28)).padStart(2, '0')}T10:00:00`,
  thumbnail_asset_id: null,
});

describe('PatientMediaTimeline C7', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockImplementation(async (url: string, config?: any) => {
      if (url !== '/patients/7/assets') return { data: new Blob(['x'], { type: 'image/png' }) } as any;
      const params = config?.params || {};
      if (params.q === 'radio') {
        return { data: { items: [asset(301, 'RADIOGRAPH', 'T2')], has_more: false } } as any;
      }
      if (params.offset === 2) {
        return { data: { items: [asset(3, 'DOCUMENT', 'T2')], has_more: false } } as any;
      }
      return { data: { items: [asset(1), asset(2, 'RADIOGRAPH', 'T1')], has_more: true } } as any;
    });
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:test'), revokeObjectURL: vi.fn() });
  });

  it('loads the next bounded page instead of silently stopping at the first page', async () => {
    const user = userEvent.setup();
    render(<PatientMediaTimeline patientId={7} />);

    await screen.findByText('2/2');
    const loadMore = screen.getByRole('button', { name: 'Charger plus de médias' });
    await user.click(loadMore);

    await screen.findByText('3/3');
    expect(api.get).toHaveBeenCalledWith('/patients/7/assets', expect.objectContaining({
      params: expect.objectContaining({ limit: 200, offset: 2 }),
    }));
  });

  it('pushes search to the server so a match beyond the first page is discoverable', async () => {
    const user = userEvent.setup();
    render(<PatientMediaTimeline patientId={7} />);
    await screen.findByText('2/2');

    await user.type(screen.getByLabelText('Rechercher un média'), 'radio');

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/patients/7/assets', expect.objectContaining({
      params: expect.objectContaining({ q: 'radio', offset: 0 }),
    })), { timeout: 1500 });
    expect(await screen.findByText('1/1')).toBeInTheDocument();
    expect(screen.getByText('Radiographie')).toBeInTheDocument();
  });
});
