import { describe, expect, it, vi } from 'vitest';
import type { PatientPairing } from './PatientCompanionStorage';

const sendRemoteCommand = vi.hoisted(() => vi.fn());
vi.mock('./PatientCompanionRemoteCommandTransport', () => ({
  sendRemoteCommand,
}));

import { sendMessageCommand } from './PatientCompanionMessageTransport';

const pairing = {
  accessToken: 'patient-token',
  pairedAt: '2026-09-22T10:00:00.000Z',
  context: {
    access_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    relationship_type: 'SELF',
    patient: { display_name: 'Aya Test' },
  },
} as PatientPairing;

describe('PatientCompanionMessageTransport', () => {
  it('reuses the certified remote command transport and messages endpoint', async () => {
    sendRemoteCommand.mockResolvedValueOnce({ status: 'ACCEPTED', result: { code: 'MESSAGE_STORED' } });
    const result = await sendMessageCommand(
      pairing,
      'message.send',
      { client_message_id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', body: 'Bonjour' },
      'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    );
    expect(result.status).toBe('ACCEPTED');
    expect(sendRemoteCommand).toHaveBeenCalledWith(
      pairing,
      'messages',
      'message.send',
      { client_message_id: 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb', body: 'Bonjour' },
      'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    );
  });

  it('does not reinterpret pending or rejected transport truth', async () => {
    sendRemoteCommand.mockRejectedValueOnce(Object.assign(new Error('pending'), { remotePending: true }));
    await expect(sendMessageCommand(pairing, 'message.sync', {})).rejects.toMatchObject({ remotePending: true });

    sendRemoteCommand.mockResolvedValueOnce({ status: 'REJECTED', result: { code: 'MESSAGE_RATE_LIMITED' } });
    await expect(sendMessageCommand(pairing, 'message.send', { client_message_id: 'd', body: 'x' }))
      .resolves.toEqual({ status: 'REJECTED', result: { code: 'MESSAGE_RATE_LIMITED' } });
  });
});
