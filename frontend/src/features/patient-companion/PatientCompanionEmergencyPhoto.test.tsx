import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('./PatientCompanionEmergencyPhotoPrep', () => ({
  prepareEmergencyPhoto: vi.fn(async () => ({
    previewUrl: 'blob:pc07-preview',
    candidates: [{ imageB64: 'ZmFrZS1qcGVn', byteSize: 9, width: 640, height: 480 }],
  })),
}));

vi.mock('./PatientCompanionRemoteCommandTransport', () => ({
  sendRemoteCommand: vi.fn(),
}));

import { PatientCompanionEmergencyPhoto } from './PatientCompanionEmergencyPhoto';
import { sendRemoteCommand } from './PatientCompanionRemoteCommandTransport';

const pairing = {
  accessToken: 'pc07-token',
  context: {
    access_id: '6ca78b1a-2a5b-4a85-8d71-6f997833c1f5',
    relationship_type: 'SELF',
    patient: { display_name: 'Aya Test' },
  },
  pairedAt: '2026-09-21T08:00:00Z',
  remoteTransport: {
    signingKid: 'sig',
    encryptionKid: 'enc',
    cabinetSigningKid: 'cab-sig',
    cabinetEncryptionKid: 'cab-enc',
    cabinetSigningPublicJwk: {},
    cabinetEncryptionPublicJwk: {},
  },
} as any;

beforeEach(() => {
  vi.stubGlobal('crypto', { ...globalThis.crypto, randomUUID: vi.fn(() => '11111111-1111-4111-8111-111111111111') });
  Object.defineProperty(URL, 'revokeObjectURL', { value: vi.fn(), configurable: true });
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

async function choosePhoto() {
  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
  const file = new File(['fake'], 'emergency.jpg', { type: 'image/jpeg' });
  fireEvent.change(input, { target: { files: [file] } });
  expect(await screen.findByText('Envoyer au cabinet')).toBeInTheDocument();
}

describe('PatientCompanionEmergencyPhoto PC-07', () => {
  it('fails closed when secure transport is unavailable', () => {
    render(<PatientCompanionEmergencyPhoto pairing={pairing} enabled={false} />);
    expect(screen.getByText(/Reconnexion sécurisée au cabinet requise/i)).toBeInTheDocument();
    expect(screen.queryByText('Prendre ou choisir une photo')).not.toBeInTheDocument();
  });

  it('shows received only after authoritative ACK', async () => {
    vi.mocked(sendRemoteCommand).mockResolvedValue({
      status: 'ACCEPTED',
      result: { state: 'received', asset_id: 77 },
      messageId: '22222222-2222-4222-8222-222222222222',
      idempotencyKey: '11111111-1111-4111-8111-111111111111',
    });

    render(<PatientCompanionEmergencyPhoto pairing={pairing} enabled />);
    await choosePhoto();
    fireEvent.click(screen.getByText('Envoyer au cabinet'));

    expect(await screen.findByText('Photo reçue par le cabinet.')).toBeInTheDocument();
    expect(sendRemoteCommand).toHaveBeenCalledWith(
      pairing,
      'emergency-photo',
      'emergency_photo.submit',
      expect.objectContaining({ image_b64: 'ZmFrZS1qcGVn' }),
      '11111111-1111-4111-8111-111111111111',
    );
  });

  it('keeps pending truth and retries with the same idempotency key', async () => {
    const pending = Object.assign(new Error('ACK pending'), { remotePending: true });
    vi.mocked(sendRemoteCommand)
      .mockRejectedValueOnce(pending)
      .mockResolvedValueOnce({
        status: 'ACCEPTED',
        result: { state: 'received', asset_id: 77 },
        messageId: '33333333-3333-4333-8333-333333333333',
        idempotencyKey: '11111111-1111-4111-8111-111111111111',
      });

    render(<PatientCompanionEmergencyPhoto pairing={pairing} enabled />);
    await choosePhoto();
    fireEvent.click(screen.getByText('Envoyer au cabinet'));

    expect(await screen.findByText(/confirmation du cabinet encore en attente/i)).toBeInTheDocument();
    expect(screen.queryByText('Photo reçue par le cabinet.')).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Vérifier / réessayer'));
    expect(await screen.findByText('Photo reçue par le cabinet.')).toBeInTheDocument();

    expect(vi.mocked(sendRemoteCommand).mock.calls[0][4]).toBe('11111111-1111-4111-8111-111111111111');
    expect(vi.mocked(sendRemoteCommand).mock.calls[1][4]).toBe('11111111-1111-4111-8111-111111111111');
  });
});
