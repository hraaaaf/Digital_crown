import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { BlockedPrintJobsReadOnly } from './BlockedPrintJobsReadOnly';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({ api: { get: vi.fn(), post: vi.fn(), put: vi.fn() } }));
const success = {
  status: 'review_only', printingAvailable: false, retrySupported: false,
  total: 1, jobs: [{
    reference: '123abc789def', status: 'uncertain',
    updatedAt: '2026-10-13T10:00:00+00:00', investigations: 2,
  }],
};

beforeEach(() => {
  vi.resetAllMocks();
  vi.mocked(api.get).mockResolvedValue({ data: success } as never);
});
afterEach(() => cleanup());

describe('LOT04.8 Cabinet blocked print status — READ ONLY', () => {
  it('never requests data or renders for delegated/non-owner settings', () => {
    const { container } = render(<BlockedPrintJobsReadOnly ownerVerified={false} />);
    expect(container.firstChild).toBeNull();
    expect(api.get).not.toHaveBeenCalled();
  });

  it('shows safe opaque references and investigation without a retry or document action', async () => {
    const { container } = render(<BlockedPrintJobsReadOnly ownerVerified />);
    expect(await screen.findByText(/Réf. 123abc789def/)).toBeInTheDocument();
    expect(screen.getByText('À vérifier — ne pas réimprimer')).toBeInTheDocument();
    expect(screen.getByText(/Constat\(s\) d’investigation : 2/)).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/admin/station-print-config/blocked-jobs');
    expect(container.querySelectorAll('button')).toHaveLength(1); // refresh only
    expect(screen.getByRole('button', { name: 'Actualiser les états' })).toBeInTheDocument();
    expect(container.querySelector('a, form, iframe, object, embed, input[type=file]')).toBeNull();
    expect(container.querySelector('[data-print-job-status="uncertain"]')).toBeInTheDocument();
    expect(container.innerHTML).not.toMatch(/patientName|patientId|pdfBytes|printerId|retry-print|\/print-job\/dispatch/i);
    expect(api.post).not.toHaveBeenCalled();
    expect(api.put).not.toHaveBeenCalled();
  });

  it('refresh is read-only and clears previous rows on API failure', async () => {
    const { container } = render(<BlockedPrintJobsReadOnly ownerVerified />);
    expect(await screen.findByText(/Réf. 123abc789def/)).toBeInTheDocument();
    vi.mocked(api.get).mockRejectedValueOnce(new Error('server unavailable'));
    fireEvent.click(screen.getByRole('button', { name: 'Actualiser les états' }));
    expect(await screen.findByText(/États indisponibles/)).toBeInTheDocument();
    expect(container.querySelector('[data-print-job-status]')).toBeNull();
    expect(api.get).toHaveBeenCalledTimes(2);
    expect(api.post).not.toHaveBeenCalled();
  });

  it('empty list explains no blocked jobs instead of saying printed', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { ...success, total: 0, jobs: [] },
    } as never);
    render(<BlockedPrintJobsReadOnly ownerVerified />);
    expect(await screen.findByText('Aucune impression bloquée répertoriée.')).toBeInTheDocument();
    expect(screen.queryByText(/Livré|Terminé|Imprimé/)).toBeNull();
  });

  it('fails closed on server accidentally returning enabled printing', async () => {
    vi.mocked(api.get).mockResolvedValueOnce({
      data: { ...success, printingAvailable: true, retrySupported: true },
    } as never);
    render(<BlockedPrintJobsReadOnly ownerVerified />);
    expect(await screen.findByText(/États indisponibles/)).toBeInTheDocument();
    expect(screen.queryByText('Réf. 123abc789def')).toBeNull();
  });
});
