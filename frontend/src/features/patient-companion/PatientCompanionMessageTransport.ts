import type { PatientPairing } from './PatientCompanionStorage';
import { sendRemoteCommand, type RemoteCommandResult } from './PatientCompanionRemoteCommandTransport';

export type MessageOperation =
  | 'message.send'
  | 'message.sync'
  | 'message.received'
  | 'message.read';

export type MessageCommandResult = RemoteCommandResult;

export async function sendMessageCommand(
  pairing: PatientPairing,
  operation: MessageOperation,
  payload: Record<string, unknown>,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<MessageCommandResult> {
  return sendRemoteCommand(pairing, 'messages', operation, payload, idempotencyKey);
}

export const PatientCompanionMessageTransport = { sendMessageCommand };
