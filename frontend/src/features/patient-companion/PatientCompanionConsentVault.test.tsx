import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { PatientCompanionConsentVault } from './PatientCompanionConsentVault';
import { PatientCompanionConsentTransport } from './PatientCompanionConsentTransport';

vi.mock('../mobile/Dashboard/components/SignaturePad', () => ({
  SignaturePad: ({ onSave }: { onSave: (value: string) => void }) => (
    <button type="button" onClick={() => onSave('data:image/png;base64,c2lnbmF0dXJl')}>Mock signature</button>
  ),
}));

vi.mock('./PatientCompanionConsentTransport', () => ({
  PatientCompanionConsentTransport: {
    sendConsentCommand: vi.fn(),
  },
}));

const pairing = {
  accessToken: 'token',
  context: {
    access_id: 'opaque-access',
    relationship_type: 'SELF',
    patient: { display_name: 'Aya Test' },
  },
  pairedAt: '2026-09-20T18:00:00Z',
};

const pendingItem = {
  consent_id: '11111111-1111-4111-8111-111111111111',
  share_id: '22222222-2222-4222-8222-222222222222',
  title: 'Consentement traitement',
  document_type: 'DOCUMENT_LIBRE',
  document_version: 3,
  state: 'PENDING',
  created_at: '2026-09-20T18:00:00Z',
  qualified_electronic_signature: false,
};

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn());
  vi.stubGlobal('open', vi.fn());
  Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:pc04') });
  Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('PatientCompanionConsentVault PC-04', () => {
  it('does not contact the cabinet before explicit online sync', () => {
    render(<PatientCompanionConsentVault pairing={pairing} enabled={false} />);
    expect(screen.getByText(/Synchronisez votre espace/i)).toBeInTheDocument();
    expect(fetch).not.toHaveBeenCalled();
  });

  it('requires reading the exact document before signature and marks signed only after ACK', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [pendingItem] }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          items: [{ ...pendingItem, state: 'SIGNED', signed_at: '2026-09-20T18:10:00Z', evidence_ref: 'evidence-1' }],
        }),
      } as Response);

    vi.mocked(PatientCompanionConsentTransport.sendConsentCommand).mockResolvedValue({
      status: 'ACCEPTED',
      result: {
        code: 'CONSENT_SIGNED',
        status: 'SIGNED',
        qualified_electronic_signature: false,
      },
      messageId: 'm',
      idempotencyKey: 'i',
    });

    render(<PatientCompanionConsentVault pairing={pairing} enabled />);
    expect(await screen.findByText('Consentement traitement')).toBeInTheDocument();
    expect(screen.queryByText('Mock signature')).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Lire le document'));
    expect(await screen.findByText('Mock signature')).toBeInTheDocument();
    expect(window.open).toHaveBeenCalledWith('blob:pc04', '_blank', 'noopener,noreferrer');

    fireEvent.click(screen.getByText('Mock signature'));
    await waitFor(() => expect(PatientCompanionConsentTransport.sendConsentCommand).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/Signature enregistrée par le cabinet/i)).toBeInTheDocument();
    expect(screen.getByText('Signature enregistrée')).toBeInTheDocument();
  });

  it('never claims signed while remote ACK is pending', async () => {
    vi.mocked(fetch)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ items: [pendingItem] }),
      } as Response)
      .mockResolvedValueOnce({
        ok: true,
        blob: async () => new Blob(['%PDF-1.4'], { type: 'application/pdf' }),
      } as Response);

    const pending = Object.assign(new Error('pending'), { remotePending: true });
    vi.mocked(PatientCompanionConsentTransport.sendConsentCommand).mockRejectedValue(pending);

    render(<PatientCompanionConsentVault pairing={pairing} enabled />);
    expect(await screen.findByText('Consentement traitement')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Lire le document'));
    fireEvent.click(await screen.findByText('Mock signature'));

    expect(await screen.findByText(/confirmation cabinet encore en attente/i)).toBeInTheDocument();
    expect(screen.getByText('À signer')).toBeInTheDocument();
    expect(screen.queryByText('Signature enregistrée')).not.toBeInTheDocument();
  });
});
