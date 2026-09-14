import { render, screen, waitFor, within } from '@testing-library/react';
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

const items = [
  { id: 1, patient_id: 7, asset_type: 'PHOTO', source_kind: 'UPLOAD', mime_type: 'image/png', timepoint: 'T0', created_at: '2026-09-01T10:00:00', thumbnail_asset_id: null },
  { id: 2, patient_id: 7, asset_type: 'RADIOGRAPH', source_kind: 'UPLOAD', mime_type: 'image/png', timepoint: 'T1', created_at: '2026-09-10T10:00:00', thumbnail_asset_id: null },
  { id: 3, patient_id: 7, asset_type: 'DOCUMENT', source_kind: 'UPLOAD', mime_type: 'application/pdf', timepoint: 'T2', created_at: '2026-09-12T10:00:00', thumbnail_asset_id: null },
];

describe('PatientMediaTimeline C5', () => {
  beforeEach(() => {
    vi.mocked(api.get).mockImplementation(async (url: string, config?: any) => {
      if (url === '/patients/7/assets') {
        const params = config?.params || {};
        const filtered = items.filter((item) => {
          if (params.asset_type && item.asset_type !== params.asset_type) return false;
          if (params.timepoint && item.timepoint !== params.timepoint) return false;
          return true;
        });
        return { data: { items: filtered, has_more: false } } as any;
      }
      return { data: new Blob(['x'], { type: 'image/png' }) } as any;
    });
    vi.stubGlobal('URL', { ...URL, createObjectURL: vi.fn(() => 'blob:test'), revokeObjectURL: vi.fn() });
  });

  it('filters the media rail by type and timepoint', async () => {
    const user = userEvent.setup();
    render(<PatientMediaTimeline patientId={7} />);

    await screen.findByText('3/3');
    await user.selectOptions(screen.getByLabelText('Filtrer par type'), 'RADIOGRAPH');
    expect(await screen.findByText('1/1')).toBeInTheDocument();
    const rail = screen.getByTestId('media-asset-rail');
    expect(within(rail).getByText('Radiographie')).toBeInTheDocument();
    expect(within(rail).queryByText('Photo')).not.toBeInTheDocument();
    expect(within(rail).queryByText('Document')).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText('Filtrer par repère'), 'T1');
    await waitFor(() => expect(screen.getByText('1/1')).toBeInTheDocument());
    expect(within(rail).getByText('Radiographie')).toBeInTheDocument();
  });

  it('opens a two-asset compare panel and can clear it', async () => {
    const user = userEvent.setup();
    render(<PatientMediaTimeline patientId={7} />);

    await screen.findByText('3/3');
    const compareButtons = screen.getAllByLabelText('Ajouter à la comparaison');
    await user.click(compareButtons[0]);
    await user.click(compareButtons[1]);

    expect(await screen.findByTestId('media-compare-panel')).toBeInTheDocument();
    expect(screen.getByText('T0 ↔ T1')).toBeInTheDocument();

    await user.click(screen.getByLabelText('Fermer la comparaison'));
    await waitFor(() => expect(screen.queryByTestId('media-compare-panel')).not.toBeInTheDocument());
  });
});
