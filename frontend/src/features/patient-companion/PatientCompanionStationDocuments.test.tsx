import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { PatientPairing } from './PatientCompanionStorage';
import { PatientCompanionStationDocuments } from './PatientCompanionStationDocuments';

const pairing = {
  accessToken: 'phone-private-token',
  context: { access_id: '00000000-0000-0000-0000-000000000101' },
} as PatientPairing;

describe('04.5 — Patient Companion private-phone withdrawal', () => {
  const originalCreate = URL.createObjectURL;
  const originalRevoke = URL.revokeObjectURL;
  const originalFetch = globalThis.fetch;
  beforeEach(() => {
    URL.createObjectURL = vi.fn(() => 'blob:phone-pdf');
    URL.revokeObjectURL = vi.fn();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    globalThis.fetch = originalFetch;
    URL.createObjectURL = originalCreate;
    URL.revokeObjectURL = originalRevoke;
  });

  it('uses paired patient access for discovery and downloads on personal phone only', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ documents: [{ documentId: 42, kind: 'care_sheet' }] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: { get: (key: string) => key === 'content-type' ? 'application/pdf' : null },
        blob: async () => new Blob(['%PDF-1.4\\n'], { type: 'application/pdf' }),
      });
    globalThis.fetch = fetchMock as typeof fetch;
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    render(<PatientCompanionStationDocuments sessionId="session-1" pairing={pairing} onClose={vi.fn()} />);
    const button = await screen.findByRole('button', { name: 'Télécharger ma feuille de soins' });
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/api/patient-companion/station-session/session-1/documents?accessId='),
      expect.objectContaining({ headers: { Authorization: 'Bearer phone-private-token' }, cache: 'no-store' }),
    );
    fireEvent.click(button);
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(String(fetchMock.mock.calls[1][0])).toContain('/documents/care-sheet/42?accessId=');
    await waitFor(() => expect(click).toHaveBeenCalledTimes(1));
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/votre téléphone peut conserver le fichier/i)).toBeInTheDocument();
  });

  it('04.5 downloads a staff-verified presence receipt only on the paired phone', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ documents: [{ documentId: 71, kind: 'presence_receipt' }] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        headers: { get: (name: string) => name === 'content-type' ? 'application/pdf' : null },
        blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
      });
    globalThis.fetch = fetchMock as typeof fetch;
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    render(<PatientCompanionStationDocuments sessionId="session-1" pairing={pairing} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Télécharger mon justificatif de présence' }));
    await waitFor(() => expect(click).toHaveBeenCalledTimes(1));
    expect(fetchMock.mock.calls[1][0]).toContain('/documents/presence-receipt/71?accessId=');
    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
  });

  it('never creates a PDF when the patient context or session is rejected', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ documents: [{ documentId: 42, kind: 'care_sheet' }] }),
      })
      .mockResolvedValueOnce({ ok: false, status: 404, headers: { get: () => null } });
    globalThis.fetch = fetchMock as typeof fetch;
    render(<PatientCompanionStationDocuments sessionId="session-1" pairing={pairing} onClose={vi.fn()} />);
    fireEvent.click(await screen.findByRole('button', { name: 'Télécharger ma feuille de soins' }));
    expect(await screen.findByRole('alert')).toHaveTextContent(/Téléchargement refusé/i);
    expect(URL.createObjectURL).not.toHaveBeenCalled();
  });

  it('04.6 revokes the server-side patient session when closing on the phone', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ documents: [] }) })
      .mockResolvedValueOnce({ ok: true, status: 204 });
    globalThis.fetch = fetchMock as typeof fetch;
    const onClose = vi.fn();
    render(<PatientCompanionStationDocuments sessionId="session-1" pairing={pairing} onClose={onClose} />);
    await screen.findByText('Aucun document disponible pour cette session.');
    fireEvent.click(screen.getByRole('button', { name: 'Terminer et effacer ma session' }));
    await waitFor(() => expect(onClose).toHaveBeenCalledWith(true));
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining('/station-session/session-1/purge?accessId='),
      expect.objectContaining({ method: 'POST', headers: { Authorization: 'Bearer phone-private-token' }, cache: 'no-store' }),
    );
  });

  it('04.6 hides the phone document UI even when server revocation fails offline', async () => {
    globalThis.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ documents: [] }) })
      .mockRejectedValueOnce(new Error('network unavailable')) as typeof fetch;
    const onClose = vi.fn();
    render(<PatientCompanionStationDocuments sessionId="session-1" pairing={pairing} onClose={onClose} />);
    await screen.findByText('Aucun document disponible pour cette session.');
    fireEvent.click(screen.getByRole('button', { name: 'Terminer et effacer ma session' }));
    await waitFor(() => expect(onClose).toHaveBeenCalledWith(false));
  });

  it('shows no document controls when the private phone session has expired', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({ ok: false, status: 404 }) as typeof fetch;
    render(<PatientCompanionStationDocuments sessionId="expired" pairing={pairing} onClose={vi.fn()} />);
    expect(await screen.findByRole('alert')).toHaveTextContent(/Session expirée ou indisponible/i);
    expect(screen.queryByRole('button', { name: 'Télécharger ma feuille de soins' })).not.toBeInTheDocument();
  });
});
