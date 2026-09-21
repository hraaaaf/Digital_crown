import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const { storage } = vi.hoisted(() => ({
  storage: {
    load: vi.fn(),
    saveEmergencyPhotoBytes: vi.fn(),
    readEmergencyPhotoBytes: vi.fn(),
    deleteEmergencyPhotoBytes: vi.fn(),
    saveEmergencyPhotoQueue: vi.fn(),
  },
}));

vi.mock('./PatientCompanionStorage', () => ({
  PatientCompanionStorage: storage,
}));

vi.mock('./PatientCompanionEmergencyPhotoPrep', () => ({
  prepareEmergencyPhoto: vi.fn(async () => ({
    previewUrl: 'blob:pc07-preview',
    bytes: new Uint8Array([1, 2, 3, 4]),
    byteSize: 4,
    width: 640,
    height: 480,
    mimeType: 'image/jpeg',
  })),
}));

vi.mock('./PatientCompanionEmergencyPhotoTransport', () => ({
  uploadEmergencyPhoto: vi.fn(),
}));

import { PatientCompanionEmergencyPhoto } from './PatientCompanionEmergencyPhoto';
import { uploadEmergencyPhoto } from './PatientCompanionEmergencyPhotoTransport';

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

const emptyVault = {
  version: 1,
  activeAccessId: pairing.context.access_id,
  pairings: [pairing],
  cache: {},
};

beforeEach(() => {
  vi.stubGlobal('crypto', {
    ...globalThis.crypto,
    randomUUID: vi.fn(() => '11111111-1111-4111-8111-111111111111'),
  });
  Object.defineProperty(URL, 'createObjectURL', {
    value: vi.fn(() => 'blob:restored'),
    configurable: true,
  });
  Object.defineProperty(URL, 'revokeObjectURL', { value: vi.fn(), configurable: true });
  storage.load.mockResolvedValue(emptyVault);
  storage.saveEmergencyPhotoBytes.mockResolvedValue(undefined);
  storage.readEmergencyPhotoBytes.mockResolvedValue(null);
  storage.deleteEmergencyPhotoBytes.mockResolvedValue(undefined);
  storage.saveEmergencyPhotoQueue.mockResolvedValue(emptyVault);
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

  it('persists local encrypted media before upload and shows received only after ACK', async () => {
    vi.mocked(uploadEmergencyPhoto).mockResolvedValue({
      status: 'ACCEPTED',
      result: { state: 'received' },
      messageId: '22222222-2222-4222-8222-222222222222',
      idempotencyKey: '33333333-3333-4333-8333-333333333333',
    } as any);

    render(<PatientCompanionEmergencyPhoto pairing={pairing} enabled />);
    await choosePhoto();

    expect(storage.saveEmergencyPhotoBytes).toHaveBeenCalledWith(
      pairing.context.access_id,
      '11111111-1111-4111-8111-111111111111',
      expect.any(Uint8Array),
    );

    fireEvent.click(screen.getByText('Envoyer au cabinet'));

    expect(await screen.findByText('Photo reçue par le cabinet.')).toBeInTheDocument();
    expect(uploadEmergencyPhoto).toHaveBeenCalledWith(
      pairing,
      '11111111-1111-4111-8111-111111111111',
      expect.any(Uint8Array),
      expect.any(String),
      expect.any(Function),
    );
    expect(storage.deleteEmergencyPhotoBytes).toHaveBeenCalledWith(
      '11111111-1111-4111-8111-111111111111',
    );
  });

  it('keeps pending truth and retries the same upload object', async () => {
    const pending = Object.assign(new Error('ACK pending'), { remotePending: true });
    vi.mocked(uploadEmergencyPhoto)
      .mockRejectedValueOnce(pending)
      .mockResolvedValueOnce({
        status: 'ACCEPTED',
        result: { state: 'received' },
      } as any);

    render(<PatientCompanionEmergencyPhoto pairing={pairing} enabled />);
    await choosePhoto();
    fireEvent.click(screen.getByText('Envoyer au cabinet'));

    expect(await screen.findByText(/aucune réception cabinet n’est encore confirmée/i)).toBeInTheDocument();
    expect(screen.queryByText('Photo reçue par le cabinet.')).not.toBeInTheDocument();

    fireEvent.click(screen.getByText('Reprendre l’envoi'));
    expect(await screen.findByText('Photo reçue par le cabinet.')).toBeInTheDocument();

    expect(vi.mocked(uploadEmergencyPhoto).mock.calls[0][1]).toBe('11111111-1111-4111-8111-111111111111');
    expect(vi.mocked(uploadEmergencyPhoto).mock.calls[1][1]).toBe('11111111-1111-4111-8111-111111111111');
  });

  it('restores a queued encrypted photo after reload without inventing receipt', async () => {
    storage.load.mockResolvedValue({
      ...emptyVault,
      cache: {
        [pairing.context.access_id]: {
          version: 1,
          accessId: pairing.context.access_id,
          syncedAt: '2026-09-21T08:00:00Z',
          appointments: [],
          shares: [],
          emergencyPhotos: [{
            uploadId: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
            state: 'remote_pending_ack',
            byteSize: 4,
            capturedAt: '2026-09-21T08:00:00Z',
            createdAt: '2026-09-21T08:00:00Z',
            updatedAt: '2026-09-21T08:01:00Z',
          }],
        },
      },
    });
    storage.readEmergencyPhotoBytes.mockResolvedValue(new Uint8Array([1, 2, 3, 4]));

    render(<PatientCompanionEmergencyPhoto pairing={pairing} enabled />);

    expect(await screen.findByText('Reprendre l’envoi')).toBeInTheDocument();
    expect(screen.queryByText('Photo reçue par le cabinet.')).not.toBeInTheDocument();
  });
});
