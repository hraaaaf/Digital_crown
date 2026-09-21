import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PatientCompanionFinance } from './PatientCompanionFinance';

const pairing = {
  accessToken: 'pc06-token',
  context: {
    access_id: 'pc06-access',
    relationship_type: 'SELF',
    patient: { display_name: 'Aya Test' },
  },
  pairedAt: '2026-09-21T08:00:00Z',
};

const payload = {
  summary: { billed: 1800, collected: 600, remaining_due: 1200 },
  payments: [{ id: 1, amount: 600, method: 'CARTE', paid_at: '2026-09-20T10:00:00Z', source: 'acte' }],
  schedules: [{
    id: 3,
    title: 'Traitement orthodontique',
    total_amount: 1200,
    items: [{ id: 5, label: 'Versement 1', amount: 600, due_date: '2026-10-01T00:00:00Z', paid_date: null, status: 'EN_ATTENTE' }],
  }],
  invoices: [{
    share_id: 'share-1',
    document_id: 9,
    title: "Note d'honoraires septembre",
    amount: 1800,
    issued_at: '2026-09-01T00:00:00Z',
    download_path: '/api/patient-companion/contexts/pc06-access/finance/invoices/share-1/download',
  }],
  online_payment: { available: false },
};

beforeEach(() => vi.stubGlobal('fetch', vi.fn()));
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('PatientCompanionFinance PC-06', () => {
  it('does not fetch finance while cabinet access is disabled', () => {
    render(<PatientCompanionFinance pairing={pairing} enabled={false} />);
    expect(screen.getByText(/Reconnexion au cabinet requise/i)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('renders authoritative read data without a payment CTA', async () => {
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => payload } as Response);

    render(<PatientCompanionFinance pairing={pairing} enabled />);

    expect(await screen.findByText('Traitement orthodontique')).toBeInTheDocument();
    expect(screen.getByText('Carte')).toBeInTheDocument();
    expect(screen.getByText("Note d'honoraires septembre")).toBeInTheDocument();
    expect(screen.getByText(/Paiement en ligne non activé/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /payer/i })).not.toBeInTheDocument();
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/patient-companion/contexts/pc06-access/finance'),
      expect.objectContaining({ headers: { Authorization: 'Bearer pc06-token' }, cache: 'no-store' }),
    );
  });

  it('removes prior finance values when refresh fails', async () => {
    vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => payload } as Response);
    const view = render(<PatientCompanionFinance pairing={pairing} enabled />);
    expect(await screen.findByText('Traitement orthodontique')).toBeInTheDocument();

    vi.mocked(fetch).mockRejectedValueOnce(new Error('offline'));
    view.rerender(<PatientCompanionFinance pairing={{ ...pairing, accessToken: 'rotated-token' }} enabled />);

    expect(await screen.findByText(/Impossible d’actualiser/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText('Traitement orthodontique')).not.toBeInTheDocument());
  });
});
