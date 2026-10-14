import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const storageMocks = vi.hoisted(() => ({
  load: vi.fn(), savePairing: vi.fn(), setActive: vi.fn(),
  clear: vi.fn(), saveWallet: vi.fn(),
}));

vi.mock('./PatientCompanionStorage', () => ({ PatientCompanionStorage: storageMocks }));
vi.mock('html5-qrcode', () => ({
  Html5QrcodeSupportedFormats: { QR_CODE: 0 },
  Html5QrcodeScanner: class { render() {} clear() { return Promise.resolve(); } },
}));
vi.mock('./PatientCompanionStationDocuments', () => ({
  PatientCompanionStationDocuments: ({
    sessionId, pairing, onClose,
  }: {
    sessionId: string;
    pairing: { context: { access_id: string } };
    onClose: (revoked: boolean) => void;
  }) => (
    <section data-testid="station-claim-documents">
      Retrait Station {sessionId} pour {pairing.context.access_id}
      <button type="button" onClick={() => onClose(true)}>Révoquer le retrait</button>
    </section>
  ),
}));

import { PatientCompanionApp } from './PatientCompanionApp';

const pairing = {
  accessToken: 'device-scoped-token',
  context: { access_id: 'ctx-A', relationship_type: 'SELF', patient: { display_name: 'Patient Test' } },
  pairedAt: '2026-10-12T18:00:00Z',
};
const vault = {
  version: 1, activeAccessId: 'ctx-A', pairings: [pairing],
  cache: { 'ctx-A': {
    version: 1, accessId: 'ctx-A', appointments: [], secureMessages: [],
    shares: [{ share_id: 'wallet-share-1', resource_type: 'document', title: 'Partage du coffre' }],
  } },
};

beforeEach(() => {
  for (const value of Object.values(storageMocks)) value.mockReset();
  storageMocks.load.mockResolvedValue(vault);
  vi.stubGlobal('fetch', vi.fn());
  vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined);
  window.history.replaceState({}, '', '/companion');
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('LOT04 × Pocket patient — separate Station authorization from wallet share IDs', () => {
  it('mounts Station documents only after an actual claim response and in the Pocket Documents tab', async () => {
    window.history.replaceState({}, '', '/companion?stationSession=one-time-station-token');
    vi.mocked(fetch).mockResolvedValue({
      ok: true, json: async () => ({ sessionId: 'verified-station-session' }),
    } as Response);
    render(<PatientCompanionApp />);
    expect(await screen.findByTestId('station-claim-documents')).toHaveTextContent('verified-station-session pour ctx-A');
    expect(screen.getByText('Partage du coffre')).toBeInTheDocument();
    expect(window.location.search).toBe('');
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/workstation/patient-session/claim'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ Authorization: 'Bearer device-scoped-token' }),
        body: JSON.stringify({ token: 'one-time-station-token', accessId: 'ctx-A' }),
      }),
    );
    expect(JSON.stringify(vi.mocked(fetch).mock.calls)).not.toContain('wallet-share-1');

    fireEvent.click(screen.getByRole('button', { name: 'Aujourd’hui' }));
    expect(screen.queryByTestId('station-claim-documents')).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Documents' }));
    expect(screen.getByTestId('station-claim-documents')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Révoquer le retrait' }));
    expect(screen.queryByTestId('station-claim-documents')).not.toBeInTheDocument();
  });

  it('never mounts the Station document module for wallet-only documents or missing server session ID', async () => {
    render(<PatientCompanionApp />);
    await screen.findByText('Patient Test');
    fireEvent.click(screen.getByRole('button', { name: 'Documents' }));
    expect(screen.getByText('Partage du coffre')).toBeInTheDocument();
    expect(screen.queryByTestId('station-claim-documents')).not.toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('fails closed when Station claim returns no canonical session identity', async () => {
    window.history.replaceState({}, '', '/companion?stationSession=opaque-token');
    vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({ ok: true }) } as Response);
    render(<PatientCompanionApp />);
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: 'Documents' }));
    expect(screen.getByText('Partage du coffre')).toBeInTheDocument();
    expect(screen.queryByTestId('station-claim-documents')).not.toBeInTheDocument();
  });
});
