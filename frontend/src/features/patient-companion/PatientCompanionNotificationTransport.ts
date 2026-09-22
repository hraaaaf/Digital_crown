import type { PatientPairing } from './PatientCompanionStorage';
import { sendRemoteCommand, type RemoteCommandResult } from './PatientCompanionRemoteCommandTransport';

export type NotificationOperation =
  | 'notification.read'
  | 'notification.snooze'
  | 'notification.preferences';

export type NotificationCommandResult = RemoteCommandResult;

export async function sendNotificationCommand(
  pairing: PatientPairing,
  operation: NotificationOperation,
  payload: Record<string, unknown>,
  idempotencyKey: string = crypto.randomUUID(),
): Promise<NotificationCommandResult> {
  return sendRemoteCommand(pairing, 'notifications', operation, payload, idempotencyKey);
}

export const PatientCompanionNotificationTransport = { sendNotificationCommand };
