import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const storageMocks = vi.hoisted(() => ({
  load: vi.fn(),
  savePairing: vi.fn(),
  setActive: vi.fn(),
  clear: vi.fn(),
}));

vi.mock('./PatientCompanionStorage', () => ({
  PatientCompanionStorage: storageMocks,
}));

vi.mock('html5-qrcode', () => ({
  Html5QrcodeSupportedFormats: { QR_CODE: 0 },
  Html5QrcodeScanner: class {
    render() {}
    clear() { return Promise.resolve(); }
  },
}));

import { PatientCompanionApp } from './PatientCompanionApp';

const emptyState = { version: 1, activeAccessId: null, pairings: [], cache: {} };

beforeEach(() => {
  storageMocks.load.mockReset();
  storageMocks.savePairing.mockReset();
  storageMocks.setActive.mockReset();
  storageMocks.clear.mockReset();
  storageMocks.load.mockResolvedValue(emptyState);
  vi.stubGlobal('fetch', vi.fn());
  window.history.replaceState({}, '', '/companion');
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('PatientCompanionApp PC-00 local-first', () => {
  it('starts from QR/manual pairing with no Firebase credential field', async () => {
    render(<PatientCompanionApp />);
    expect(await screen.findByText('Appairer ce téléphone')).toBeInTheDocument();
    expect(screen.getByText('Scanner le QR')).toBeInTheDocument();
    expect(screen.getByLabelText('Code manuel')).toBeInTheDocument();
    expect(screen.queryByText(/Firebase/i)).not.toBeInTheDocument();
  });

  it('pairs by one-time code and persists the returned context in the encrypted vault', async () => {
    const context = {
      access_id: 'opaque-access',
      relationship_type: 'SELF',
      patient: { display_name: 'Aya Test', prenom: 'Aya', nom: 'Test' },
    };
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: async () => ({ access_token: 'device-session', context, paired_at: '2026-09-19T18:00:00Z' }),
    } as Response);
    storageMocks.savePairing.mockResolvedValue({
      version: 1,
      activeAccessId: 'opaque-access',
      pairings: [{ accessToken: 'device-session', context, pairedAt: '2026-09-19T18:00:00Z' }],
      cache: {},
    });

    render(<PatientCompanionApp />);
    await screen.findByText('Appairer ce téléphone');
    fireEvent.change(screen.getByLabelText('Code manuel'), { target: { value: 'ABCD-EFGH-JKLM' } });
    fireEvent.click(screen.getByText('Appairer avec le code'));

    await waitFor(() => expect(storageMocks.savePairing).toHaveBeenCalledTimes(1));
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/patient-companion/pair'),
      expect.objectContaining({ method: 'POST' }),
    );
    expect(await screen.findByText('Aya Test')).toBeInTheDocument();
  });

  it('opens the locally stored patient space without contacting the cabinet', async () => {
    const context = {
      access_id: 'local-access',
      relationship_type: 'PARENT',
      patient: { display_name: 'Yazan Test' },
    };
    storageMocks.load.mockResolvedValue({
      version: 1,
      activeAccessId: 'local-access',
      pairings: [{ accessToken: 'encrypted-at-rest', context, pairedAt: '2026-09-19T18:00:00Z' }],
      cache: {},
    });

    render(<PatientCompanionApp />);

    expect(await screen.findByText('Yazan Test')).toBeInTheDocument();
    expect(screen.getByText(/Coffre local actif/i)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });
  it('forces an explicit context choice when several patient contexts are stored', async () => {
    storageMocks.load.mockResolvedValue({
      version: 1,
      activeAccessId: 'a1',
      pairings: [
        { accessToken: 't1', context: { access_id: 'a1', relationship_type: 'SELF', patient: { display_name: 'Aya Test' } }, pairedAt: '2026-09-19T18:00:00Z' },
        { accessToken: 't2', context: { access_id: 'a2', relationship_type: 'PARENT', patient: { display_name: 'Yazan Test' } }, pairedAt: '2026-09-19T18:01:00Z' },
      ],
      cache: {},
    });
    storageMocks.setActive.mockResolvedValue({
      version: 1,
      activeAccessId: 'a2',
      pairings: [
        { accessToken: 't1', context: { access_id: 'a1', relationship_type: 'SELF', patient: { display_name: 'Aya Test' } }, pairedAt: '2026-09-19T18:00:00Z' },
        { accessToken: 't2', context: { access_id: 'a2', relationship_type: 'PARENT', patient: { display_name: 'Yazan Test' } }, pairedAt: '2026-09-19T18:01:00Z' },
      ],
      cache: {},
    });

    render(<PatientCompanionApp />);

    expect(await screen.findByText('Choisir un dossier')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Yazan Test'));
    await waitFor(() => expect(storageMocks.setActive).toHaveBeenCalledWith('a2'));
    expect(await screen.findByText('Mon espace')).toBeInTheDocument();
  });

});
