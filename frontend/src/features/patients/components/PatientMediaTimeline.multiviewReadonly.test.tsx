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
    expect(screen.queryByLabelText('Import média clinique')).toBeNull();
    expect(document.querySelector('input[type="file"]')).toBeNull();
    expect(vi.mocked(api.post)).not.toHaveBeenCalled();
  });

  it('preserves the original upload control outside the read-only MultiView', async () => {
    render(<PatientMediaTimeline patientId={17} />);
    await waitFor(() => expect(vi.mocked(api.get)).toHaveBeenCalled());
    expect(screen.getByRole('button', { name: 'Importer' })).toBeTruthy();
    expect(screen.getByLabelText('Import média clinique')).toBeTruthy();
    expect(vi.mocked(api.post)).not.toHaveBeenCalled();
  });
});
