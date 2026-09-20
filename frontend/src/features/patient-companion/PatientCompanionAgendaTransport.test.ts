import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { PatientPairing } from './PatientCompanionStorage';

const mocks = vi.hoisted(() => ({
  signAndEncrypt: vi.fn(),
  decryptAndVerify: vi.fn(),
}));

vi.mock('../../services/api', () => ({ API_BASE: 'http://cabinet.test' }));
vi.mock('./PatientCompanionRemoteCrypto', () => ({
  PatientCompanionRemoteCrypto: {
    signAndEncrypt: mocks.signAndEncrypt,
    decryptAndVerify: mocks.decryptAndVerify,
  },
}));

import { sendAgendaCommand } from './PatientCompanionAgendaTransport';

const pairing: PatientPairing = {
  accessToken: 'patient-token',
  pairedAt: '2026-09-20T10:00:00.000Z',
  expiresAt: '2030-01-01T00:00:00.000Z',
  context: {
    access_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    relationship_type: 'SELF',
    patient: { display_name: 'Aya Test' },
  },
  remoteTransport: {
    version: 1,
    keysetId: 'keyset',
    signingKid: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb',
    encryptionKid: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    cabinetSigningKid: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
    cabinetSigningPublicJwk: {},
    cabinetEncryptionKid: 'eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee',
    cabinetEncryptionPublicJwk: {},
  },
};

describe('PatientCompanionAgendaTransport', () => {
  let sent: Record<string, unknown>;

  beforeEach(() => {
    sent = {};
    mocks.signAndEncrypt.mockReset();
    mocks.decryptAndVerify.mockReset();
    mocks.signAndEncrypt.mockImplementation(async (payload: Record<string, unknown>) => {
      sent = payload;
      return 'opaque-command';
    });
    vi.stubGlobal('fetch', vi.fn(async () => ({
      ok: true,
      status: 200,
      json: async () => ({ blob: 'opaque-ack' }),
    })));
  });

  it('returns ACCEPTED only after a matching verified cabinet ACK', async () => {
    mocks.decryptAndVerify.mockImplementation(async () => {
      const now = new Date();
      return {
        protocol_version: 'dc-pc-remote-v1',
        message_id: 'ffffffff-ffff-4fff-8fff-ffffffffffff',
        access_id: pairing.context.access_id,
        sent_at: now.toISOString(),
        expires_at: new Date(now.getTime() + 5 * 60_000).toISOString(),
        idempotency_key: '11111111-1111-4111-8111-111111111111',
        operation: 'command.result',
        payload: {
          request_message_id: sent.message_id,
          request_operation: 'agenda.create',
          status: 'ACCEPTED',
          result: { state: 'confirmed' },
        },
      };
    });

    const result = await sendAgendaCommand(
      pairing,
      'agenda.create',
      { slot_ref: '22222222-2222-4222-8222-222222222222' },
      '11111111-1111-4111-8111-111111111111',
    );

    expect(result.status).toBe('ACCEPTED');
    expect(result.result).toEqual({ state: 'confirmed' });
    expect(mocks.signAndEncrypt).toHaveBeenCalledOnce();
    expect(mocks.decryptAndVerify).toHaveBeenCalledWith('opaque-ack', pairing.remoteTransport);
  });

  it('rejects a cryptographically verified ACK bound to another request', async () => {
    mocks.decryptAndVerify.mockImplementation(async () => {
      const now = new Date();
      return {
        protocol_version: 'dc-pc-remote-v1',
        message_id: 'ffffffff-ffff-4fff-8fff-ffffffffffff',
        access_id: pairing.context.access_id,
        sent_at: now.toISOString(),
        expires_at: new Date(now.getTime() + 5 * 60_000).toISOString(),
        idempotency_key: '11111111-1111-4111-8111-111111111111',
        operation: 'command.result',
        payload: {
          request_message_id: '33333333-3333-4333-8333-333333333333',
          request_operation: 'agenda.create',
          status: 'ACCEPTED',
          result: { state: 'confirmed' },
        },
      };
    });

    await expect(sendAgendaCommand(
      pairing,
      'agenda.create',
      { slot_ref: '22222222-2222-4222-8222-222222222222' },
      '11111111-1111-4111-8111-111111111111',
    )).rejects.toThrow('Résultat ACK Patient Companion invalide');
  });
});
